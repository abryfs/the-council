#!/usr/bin/env python3
"""Eval 02b scoring. Written BEFORE the v2 grades came back.

v1 compared three arms at fixed k=15. v2 compares at k<=4, and the gated arm
returns a VARIABLE count including zero -- so precision alone is not enough.
The metrics that matter for a shipped tool are declared here, in advance:

  precision      relevant / shown          (undefined when nothing is shown)
  signal         relevant shown per prompt (what the user gains)
  noise          irrelevant shown per prompt (what the user pays)
  silence        fraction of prompts where the arm correctly showed nothing
"""
import json
import os
from collections import defaultdict

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(root, "eval")

key = json.load(open(os.path.join(E, "blind_key2.json")))
grades = json.load(open(os.path.join(E, "grades2.json")))
shown = json.load(open(os.path.join(E, "arms2.json")))
oracle = json.load(open(os.path.join(E, "oracle.json")))
CONTROLS = {p for p, o in oracle.items() if o["relevant"] <= 3}

ARMS = ["gated", "random4", "oracle4"]
stat = {a: defaultdict(float) for a in ARMS}
rows = []

for g in grades:
    pid = g["id"]
    if pid not in key:
        continue
    row = {"id": pid, "ctrl": pid in CONTROLS}
    for s in g["sets"]:
        arm = key[pid][s["label"]]
        n_shown = len(shown[pid][arm])
        n_rel = s["relevant_count"]
        row[arm] = (n_rel, n_shown)
        stat[arm]["rel"] += n_rel
        stat[arm]["shown"] += n_shown
        stat[arm]["noise"] += n_shown - n_rel
        stat[arm]["n"] += 1
        if n_shown == 0:
            stat[arm]["silent"] += 1
            if pid in CONTROLS:
                stat[arm]["silent_on_ctrl"] += 1
    rows.append(row)

n = len(rows)
nc = len([r for r in rows if r["ctrl"]])

print(f"n = {n} prompts ({nc} controls) · gated k<=4 · random4/oracle4 k=4\n")
print(f"{'id':5} {'ctrl':>5}  " + "  ".join(f"{a:>14}" for a in ARMS))
for r in sorted(rows, key=lambda x: x["id"]):
    cells = []
    for a in ARMS:
        rel, sh = r.get(a, (0, 0))
        cells.append(f"{rel}/{sh}".rjust(14))
    print(f"{r['id']:5} {'yes' if r['ctrl'] else '':>5}  " + "  ".join(cells))

print(f"\n{'arm':9} {'precision':>10} {'signal':>8} {'noise':>8} {'silence':>9}")
for a in ARMS:
    s = stat[a]
    prec = s["rel"] / s["shown"] if s["shown"] else float("nan")
    print(f"{a:9} {prec:>10.3f} {s['rel']/n:>8.2f} {s['noise']/n:>8.2f} {s['silent']/n:>8.0%}")

print("\nvs the v1 baseline (bm25 @ k=15): precision 0.107 · signal 1.60 · noise 13.40 · silence 0%")

g = stat["gated"]
print(f"\ngated arm:")
print(f"  showed nothing on {int(g['silent'])}/{n} prompts "
      f"({int(g['silent_on_ctrl'])}/{nc} of the controls)")
print(f"  tokens/prompt ~{round(g['shown']/n*204)} (v1 k=15 was ~3060)")
if nc:
    print(f"  control silence rate: {g['silent_on_ctrl']/nc:.0%}  "
          f"(this is the anti-horoscope metric; v1 was 0%)")
