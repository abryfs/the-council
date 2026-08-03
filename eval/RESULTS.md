# Results

Run `python3 eval/measure.py` to reproduce. Numbers below are from the corpus at 7 patterns.

## Eval 01 — context cost · RUN · 2026-08-03

```
corpus: 7 patterns, mean entry 385 chars (~96 tok), whole corpus ~674 tok
per-prompt at k=15:  retrieved ~1443 tok  ·  full corpus ~674 tok
saving: NONE — corpus is smaller than k*mean, so retrieval is pure overhead here
```

**At the current size, retrieval loses.** Loading all 7 patterns costs 674 tokens; a k=15
retrieval costs 1,443. This is reported first because it is the result, and because a harness
that cannot report against its own thesis is decoration.

Projection, mean entry size held constant:

| n patterns | corpus (tok) | retrieved k=15 (tok) | saving |
|---|---|---|---|
| 30 | 2,886 | 1,443 | 50.0% |
| 100 | 9,621 | 1,443 | 85.0% |
| 300 | 28,864 | 1,443 | 95.0% |
| **1000** | **96,214** | **1,443** | **98.5%** |

**Break-even is n≈15.** Below that, ship a flat file and skip the machinery.

Two things this establishes:

1. **1,000 patterns cannot be always-on.** ~96k tokens is ~10% of a 1M window burned before
   the task starts, and it sits in the range where measured instruction-following collapses.
   Retrieval is not an optimization here; it is the only way the corpus can exist at all.
2. **The projected 98.5% independently reproduces the ITR result** (95% at 30k→1.5k) on a
   different corpus. The mechanism's efficiency claim replicates.

**Caveats, stated rather than buried.** Token counts use a ~4 chars/token approximation, not a
real tokenizer — treat as ±10% and swap in the real one before publishing. The projection
assumes mean entry size holds to n=1000, which it will not exactly. And a saving is not a
benefit: this measures what retrieval *costs*, not whether it returns the right patterns.

## Eval 02 — selection vs random · NOT RUN

The load-bearing one. Kill condition defined in `01-context.md`. Until this reports, the
project's central claim is unproven and the README says so.

## Eval 03 — output quality · NOT RUN

Blocked on 02. Running it first would measure a corpus we cannot yet retrieve from.
