#!/usr/bin/env python3
"""council-render — reads the cache on stdin's session_id, prints <=2 revealed rows.

Separate file on purpose: this used to be a heredoc inside council-statusline.sh,
which meant two stdin redirects on one command. The last redirect won, python
received the session JSON as its program, and 2>/dev/null swallowed the error.
The feature was silently dead. A script that reads stdin cannot also BE stdin.
"""
import hashlib, json, os, sys, time

cache_dir, ttl = sys.argv[1], int(sys.argv[2])
try:
    ev = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

sid = str(ev.get("session_id") or "")[:64]
if not sid:
    sys.exit(0)

path = os.path.join(cache_dir, f"council-{hashlib.sha1(sid.encode()).hexdigest()[:16]}.json")
try:
    with open(path) as f:
        d = json.load(f)
except Exception:
    sys.exit(0)

# Stale passages are worse than none — they describe a task you already finished.
if time.time() - float(d.get("ts", 0)) > ttl:
    sys.exit(0)

passages = (d.get("passages") or [])[:2]
if not passages:
    sys.exit(0)

# Width comes from the env Claude Code sets; tput cannot see the terminal here.
try:
    cols = max(40, int(os.environ.get("COLUMNS", "100")))
except ValueError:
    cols = 100

# ── the reveal ───────────────────────────────────────────────────────────────
# The status line re-runs constantly, so successive renders are animation frames
# for free. A passage surfaces character by character from the moment it was
# written: ~22 chars/sec, so a full line settles in about four seconds. The
# leading edge is brighter than the settled text, which reads as the sentence
# being written rather than pasted. Once whole, it simply stays.
elapsed = max(0.0, time.time() - float(d.get("ts", 0)))
FADE_IN = 0.55            # the name breathes in before any body text moves
CPS     = 22.0

RESET   = "\033[0m"
SETTLED = "\033[38;5;240m"   # deliberately below the status line above it
EDGE    = "\033[38;5;173m"   # the character currently being written
GHOST   = "\033[38;5;236m"   # not yet arrived — barely there by design
CLAY    = "\033[38;5;137m"
MARK    = {"block": CLAY + "▲", "warn": SETTLED + "▲", "note": SETTLED + "\u00b7"}

def veil(name, t):
    """The name arrives as a whole, but dim, and warms as it settles."""
    if t < 0.18:  return GHOST + name + RESET
    if t < FADE_IN: return "\033[38;5;238m" + name + RESET
    return SETTLED + name + RESET

for p in passages:
    name = str(p.get("name", ""))[:40]
    mech = " ".join(str(p.get("mechanism", "")).split())
    mark = MARK.get(p.get("severity"), MARK["note"]) + RESET

    budget = cols - len(name) - 8
    if budget < 20:
        mech = ""
    elif len(mech) > budget:
        mech = mech[: budget - 1].rsplit(" ", 1)[0] + "\u2026"

    if not mech:
        print(f"{mark} {veil(name, elapsed)}")
        continue

    shown = int(max(0.0, elapsed - FADE_IN) * CPS)
    if shown >= len(mech):
        print(f"{mark} {veil(name, elapsed)}{SETTLED} \u2014 {mech}{RESET}")
    else:
        body = mech[:shown]
        edge = mech[shown] if shown < len(mech) else ""
        # a thin ghost of what is still coming, so the line does not jump width
        rest = "".join(" " if (c == " " or i % 2) else "\u00b7"
                       for i, c in enumerate(mech[shown + 1:]))[:34]
        print(f"{mark} {veil(name, elapsed)}{SETTLED} \u2014 {body}"
              f"{EDGE}{edge}{GHOST}{rest}{RESET}")
