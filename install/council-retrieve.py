#!/usr/bin/env python3
"""council-retrieve — pick <=2 passages for the human status line.

Runs as a Stop hook. Reads the tail of the session transcript, scores it against
the council corpus with BM25, and writes the winners to a per-session cache that
the status line reads. Never speaks to the model; never touches the network.

Design constraints, each of which is a failure this guards against:

  * The status line re-runs constantly, so it must not compute. This does the
    work once per turn and leaves a file; the status line only reads.
  * Hooks must never block. Pure stdlib, no network, no LLM, hard-capped work.
  * An always-populated status line becomes wallpaper in a day. Passages are
    written only when the winner CHANGES, and a repeat is suppressed for
    REPEAT_COOLDOWN.
  * Low recall is fine here and high precision is not optional. A passage that
    is merely topical is worse than silence, so SCORE_FLOOR is deliberately high
    and the common case is writing nothing.
  * Any error at all -> exit 0 with no cache write. Silence is always correct.

Disable: touch ~/.claude/council-muted   (or set COUNCIL_DISABLE=1)
"""
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter

CORPUS = os.path.expanduser("~/dev/the-council/corpus.json")
CACHE_DIR = os.environ.get("TMPDIR", "/tmp")
MUTE_FILE = os.path.expanduser("~/.claude/council-muted")

MAX_PASSAGES = 2
SCORE_FLOOR = 9.0          # tuned high: silence beats a topical near-miss
MARGIN_FLOOR = 0.45        # 2nd passage must be >=45% of the 1st, or show one
TAIL_CHARS = 6000          # how much recent transcript to consider
TAIL_BYTES = 400_000               # seek to the end; long sessions must still fire
REPEAT_COOLDOWN = 45 * 60  # don't re-show the same passage within 45 min
CACHE_TTL = 90 * 60        # a passage older than this is stale; show nothing

K1, B = 1.5, 0.75
STOP = set("""a an the and or but if then than that this these those is are was were be been being
of to in on at by for with from as it its into about over under not no nor so such can could
should would will just do does did doing done have has had i you we they he she them us our your
my me his her their what which who whom when where why how all any both each few more most other
some only own same too very s t don now up out off again further once here there let need want
make made get got go going know think see look use used using like also well back even still way
one two first new old good great best right thing things something anything everything""".split())
_word = re.compile(r"[a-z0-9]+")


def toks(text):
    return [w for w in _word.findall(text.lower()) if w not in STOP and len(w) > 2]


def read_tail(path):
    """Last TAIL_CHARS of human+assistant text from a transcript jsonl.

    Seeks to the end rather than refusing large files: a long session is
    exactly when this is most useful, and an early size guard silently
    disabled the feature on every real transcript.
    """
    out = []
    try:
        size = os.path.getsize(path)
        with open(path, errors="ignore") as f:
            if size > TAIL_BYTES:
                f.seek(size - TAIL_BYTES)
                f.readline()          # discard the partial first line
            for line in f:
                if '"text"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                msg = d.get("message") or {}
                content = msg.get("content")
                if isinstance(content, str):
                    out.append(content)
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            out.append(c.get("text", ""))
    except OSError:
        return ""
    return "\n".join(out)[-TAIL_CHARS:]


def score(query, corpus):
    docs, df = [], Counter()
    for p in corpus:
        c = Counter()
        for field, w in (("trigger", 3), ("name", 2), ("mechanism", 1)):
            for t in toks(p.get(field, "")):
                c[t] += w
        docs.append(c)
        for t in c:
            df[t] += 1
    if not docs:
        return []
    import math
    avgdl = sum(sum(c.values()) for c in docs) / len(docs)
    N = len(docs)
    q = toks(query)
    scored = []
    for i, c in enumerate(docs):
        dl = sum(c.values()) or 1
        s = 0.0
        for t in q:
            if t not in c:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            tf = c[t]
            s += idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / avgdl))
        scored.append((s, i))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored


def main():
    if os.path.exists(MUTE_FILE) or os.environ.get("COUNCIL_DISABLE"):
        return
    raw = sys.stdin.read()
    if not raw.strip():
        return
    ev = json.loads(raw)
    sid = str(ev.get("session_id") or "")[:64]
    tpath = ev.get("transcript_path") or ""
    if not sid or not tpath or not os.path.exists(CORPUS):
        return

    cache = os.path.join(CACHE_DIR, f"council-{hashlib.sha1(sid.encode()).hexdigest()[:16]}.json")
    prev = {}
    try:
        with open(cache) as f:
            prev = json.load(f)
    except Exception:
        prev = {}

    tail = read_tail(tpath)
    if len(tail) < 200:
        return

    with open(CORPUS) as f:
        corpus = json.load(f)

    ranked = score(tail, corpus)
    if not ranked or ranked[0][0] < SCORE_FLOOR:
        return   # nothing clears the bar -> leave the previous state alone

    top = ranked[0][0]
    picks = [i for s, i in ranked[:MAX_PASSAGES] if s >= SCORE_FLOOR and s >= top * MARGIN_FLOOR]

    now = time.time()
    recent = {k: v for k, v in (prev.get("recent") or {}).items() if now - v < REPEAT_COOLDOWN}
    fresh = [i for i in picks if corpus[i]["name"] not in recent]
    if not fresh:
        return   # everything we'd show was shown recently -> stay quiet

    out = {
        "ts": now,
        "passages": [
            {"name": corpus[i]["name"], "severity": corpus[i]["severity"],
             # voice = one line of direct counsel. Falls back to mechanism for
             # any pattern that has not been given one yet.
             "voice": corpus[i].get("voice", ""),
             "mechanism": corpus[i]["mechanism"]}
            for i in fresh
        ],
        "recent": {**recent, **{corpus[i]["name"]: now for i in fresh}},
    }
    tmp = cache + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f)
    os.replace(tmp, cache)   # atomic: the status line never reads a half-written file


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass   # a status-line nicety must never fail a turn
    sys.exit(0)
