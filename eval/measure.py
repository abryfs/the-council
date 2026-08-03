#!/usr/bin/env python3
"""Eval 01 — deterministic context-cost measurement. No model calls, no judges.

Token estimate uses ~4 chars/token (English). Treat as +/-10%; swap a real
tokenizer in before publishing any number from this.
"""
import glob
import os
import re

CHARS_PER_TOKEN = 4.0
K = 15  # patterns retrieved per prompt

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(root, "patterns", "*.md")))

entries = []
for f in files:
    body = open(f).read()
    # entries are '### Name' blocks
    for block in re.split(r"^### ", body, flags=re.M)[1:]:
        entries.append(block.strip())

if not entries:
    raise SystemExit("no patterns found under patterns/*.md")

sizes = [len(e) for e in entries]
n = len(entries)
mean_chars = sum(sizes) / n
corpus_chars = sum(sizes)


def tok(chars):
    return round(chars / CHARS_PER_TOKEN)


print(f"corpus: {n} patterns across {len(files)} shard(s)")
print(f"  mean entry      {mean_chars:6.0f} chars  ~{tok(mean_chars):5d} tok")
print(f"  largest entry   {max(sizes):6d} chars  ~{tok(max(sizes)):5d} tok")
print(f"  whole corpus    {corpus_chars:6d} chars  ~{tok(corpus_chars):5d} tok")
print()

retrieved = mean_chars * K
print(f"per-prompt cost at k={K}")
print(f"  retrieved       {retrieved:6.0f} chars  ~{tok(retrieved):5d} tok")
print(f"  full corpus     {corpus_chars:6d} chars  ~{tok(corpus_chars):5d} tok")
if corpus_chars > retrieved:
    print(f"  saving          {100 * (1 - retrieved / corpus_chars):5.1f}%   (at n={n})")
else:
    print(f"  saving           none — corpus smaller than k*mean; retrieval is pure overhead here")
print()

print("projection (mean entry size held constant)")
print(f"  {'n':>6}  {'corpus tok':>11}  {'retrieved tok':>13}  {'saving':>7}")
for N in (30, 100, 300, 1000):
    c = mean_chars * N
    print(f"  {N:>6}  {tok(c):>11}  {tok(retrieved):>13}  {100 * (1 - retrieved / c):>6.1f}%")
print()
print("NOTE: saving is real and deterministic. It says nothing about whether the")
print("      retrieved 15 are the RIGHT 15 — that is eval 02, which is not yet run.")
