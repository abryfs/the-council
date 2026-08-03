#!/usr/bin/env python3
"""Deterministic BM25 retriever over the pattern corpus.

Deliberately the WEAKEST reasonable retriever: pure lexical, no embeddings, no
reranker. ITR used dense + BM25 + cross-encoder. If this floor beats random, a
real hybrid does better; if this floor loses, that is informative too.

Fields are weighted because `trigger` is authored as the retrieval key.
"""
import json
import math
import os
import random
import re
from collections import Counter

FIELD_WEIGHTS = {"trigger": 3, "name": 2, "mechanism": 1}
K1, B = 1.5, 0.75

STOP = set("""a an the and or but if then than that this these those is are was were be been being
of to in on at by for with from as it its into about over under not no nor so such can could
should would will just do does did doing done have has had i you we they he she them us our your
my me his her their what which who whom when where why how all any both each few more most other
some only own same too very s t don now up out off again further once here there""".split())

_word = re.compile(r"[a-z0-9]+")

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def toks(text):
    return [w for w in _word.findall(text.lower()) if w not in STOP and len(w) > 2]


def load_corpus(path=None):
    path = path or os.path.join(root, "corpus.json")
    with open(path) as f:
        return json.load(f)


def build_index(corpus):
    """Returns (docs, df, avgdl). docs[i] = Counter of weighted term freqs."""
    docs = []
    for p in corpus:
        c = Counter()
        for field, w in FIELD_WEIGHTS.items():
            for t in toks(p.get(field, "")):
                c[t] += w
        docs.append(c)
    df = Counter()
    for c in docs:
        for t in c:
            df[t] += 1
    avgdl = sum(sum(c.values()) for c in docs) / max(len(docs), 1)
    return docs, df, avgdl


def bm25(query, corpus, docs, df, avgdl, k=15):
    N = len(corpus)
    q = toks(query)
    scored = []
    for i, c in enumerate(docs):
        dl = sum(c.values())
        s = 0.0
        for t in q:
            if t not in c:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            tf = c[t]
            s += idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / avgdl))
        scored.append((s, i))
    # deterministic: ties break by index, never by dict order
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [i for s, i in scored[:k]], [s for s, i in scored[:k]]


def random_draw(corpus, k=15, seed=0):
    rng = random.Random(seed)
    return rng.sample(range(len(corpus)), min(k, len(corpus)))


if __name__ == "__main__":
    import sys

    corpus = load_corpus()
    docs, df, avgdl = build_index(corpus)
    query = " ".join(sys.argv[1:]) or "should we build the team plan before launch"
    idx, scores = bm25(query, corpus, docs, df, avgdl, k=10)
    print(f"corpus: {len(corpus)} patterns\nquery: {query!r}\n")
    for rank, (i, s) in enumerate(zip(idx, scores), 1):
        flag = "" if s > 0 else "   <- zero score (no lexical overlap)"
        print(f"{rank:2d}. [{s:6.2f}] {corpus[i]['name']:<32} ({corpus[i]['severity']}){flag}")
