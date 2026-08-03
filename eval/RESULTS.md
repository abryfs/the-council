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

## Eval 01b — can BM25 gate? · RUN · NEGATIVE · 2026-08-03

**It cannot.** Two failed gate designs, both measured on the real 107-pattern corpus.

**Design 1 — `score > 0`.** Useless. Mean 14.3 of 15 retrieved patterns score non-zero; zero
of 20 prompts gate to nothing. Across a 107-pattern corpus there is enough incidental word
overlap that almost everything scores.

**Design 2 — absolute threshold.** Confounded by prompt length. Raw top scores range
7.02–21.32, and the ordering tracks how many words the prompt has, not how relevant the
corpus is. The two clearly-mechanical prompts sit lowest (7.02 regex, 7.15 async/await) — but
so do two genuinely product-shaped ones (8.33 *"we have 4 users, two of them are me and my
cofounder"*, 9.08 *"the settings page feels cluttered"*), because they are short. Any
threshold that cuts the controls also cuts real questions.

**Design 3 — length-normalized (top score ÷ query terms).** Also fails, and this is the
decisive one:

```
suspected-mechanical : 0.71 – 0.88
everything else      : 0.54 – 2.78     OVERLAPPING
```

The mechanical prompts sit entirely *inside* the range of the real ones. Normalization removes
the length confound and the signal does not survive it.

**What this means.** Lexical retrieval can rank patterns by relevance, but it **cannot tell
"the right pattern is in here" from "nothing here applies."** Those are different questions and
BM25 only answers the first. A working gate needs a semantic signal — an LLM relevance
judgment, or embeddings with a calibrated threshold — which is a per-call cost the pure-lexical
design was specifically trying to avoid.

Consequence for `SKILL.md`: the documented `score == 0` gate **does not work as written** and
is now known-broken. It stays documented as broken rather than quietly removed.

## Eval 02 — selection vs random · NOT RUN

The load-bearing one. Kill condition defined in `01-context.md`. Until this reports, the
project's central claim is unproven and the README says so.

## Eval 03 — output quality · NOT RUN

Blocked on 02. Running it first would measure a corpus we cannot yet retrieve from.
