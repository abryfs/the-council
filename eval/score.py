#!/usr/bin/env python3
"""Unblind the grading and compute precision@15 per arm.

Written BEFORE the grades came back, so the analysis is not tuned to the result.
"""
import json
import os
import sys
from collections import defaultdict

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(root, "eval")

key = json.load(open(os.path.join(E, "blind_key.json")))
oracle = json.load(open(os.path.join(E, "oracle.json")))
grades = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(E, "grades.json")))

K = 15
CONTROLS = {p for p, o in oracle.items() if o["relevant"] <= 3}

per_arm = defaultdict(list)
per_arm_ctrl = defaultdict(list)
rows = []

for g in grades:
    pid = g["id"]
    if pid not in key:
        continue
    row = {"id": pid}
    for s in g["sets"]:
        arm = key[pid][s["label"]]
        n = s["relevant_count"]
        row[arm] = n
        per_arm[arm].append(n)
        (per_arm_ctrl if pid in CONTROLS else per_arm)[arm + "_ctrl" if pid in CONTROLS else arm]
        if pid in CONTROLS:
            per_arm_ctrl[arm].append(n)
    rows.append(row)

ARMS = ["bm25", "random", "oracle"]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def boot_ci(a, b, n=10000, seed=7):
    """Paired bootstrap on the per-prompt difference a-b."""
    import random

    rng = random.Random(seed)
    d = [x - y for x, y in zip(a, b)]
    ms = []
    for _ in range(n):
        s = [d[rng.randrange(len(d))] for _ in range(len(d))]
        ms.append(sum(s) / len(s))
    ms.sort()
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


print(f"n = {len(rows)} prompts · k = {K} · controls (oracle<=3 relevant): {sorted(CONTROLS)}\n")
print(f"{'id':5} {'bm25':>6} {'random':>7} {'oracle':>7}   {'ctrl':>4}")
for r in sorted(rows, key=lambda x: x["id"]):
    c = "yes" if r["id"] in CONTROLS else ""
    print(f"{r['id']:5} {r.get('bm25',0):>6} {r.get('random',0):>7} {r.get('oracle',0):>7}   {c:>4}")

print(f"\n{'arm':8} {'prec@15':>8} {'relevant/15':>12}")
for a in ARMS:
    m = mean(per_arm[a])
    print(f"{a:8} {m/K:>8.3f} {m:>9.1f}/15")

paired = {a: [r.get(a, 0) for r in rows] for a in ARMS}
lo, hi = boot_ci(paired["bm25"], paired["random"])
print(f"\nbm25 - random: {mean(paired['bm25']) - mean(paired['random']):+.2f} patterns/prompt")
print(f"  95% paired bootstrap CI: [{lo:+.2f}, {hi:+.2f}]")
print(f"  VERDICT: {'BEATS RANDOM' if lo > 0 else 'NOT DISTINGUISHABLE FROM RANDOM'}")

lo2, hi2 = boot_ci(paired["oracle"], paired["bm25"])
print(f"\noracle - bm25: {mean(paired['oracle']) - mean(paired['bm25']):+.2f}  CI [{lo2:+.2f}, {hi2:+.2f}]")
print("  (headroom a better retriever could capture)")

if CONTROLS:
    print(f"\ncontrol prompts only (n={len(CONTROLS)}) — should be near zero for a system that knows when to shut up:")
    for a in ARMS:
        print(f"  {a:8} {mean(per_arm_ctrl[a]):.1f}/15 relevant")
