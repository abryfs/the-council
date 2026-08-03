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

## Eval 02 — selection vs random · RUN · 2026-08-03 · **passes, weakly**

20 prompts authored blind to the corpus · 107 patterns · k=15 · three arms, labels shuffled
per prompt, graders never told which arm they held · analysis script written before the
grades came back.

| arm | precision@15 | relevant / 15 |
|---|---|---|
| random | 0.057 | 0.8 |
| **bm25** | **0.107** | **1.6** |
| oracle (LLM, full corpus) | 0.263 | 4.0 |

```
bm25 - random: +0.75 patterns/prompt   95% paired bootstrap CI [+0.05, +1.45]
VERDICT: BEATS RANDOM
oracle - bm25: +2.35                   95% CI [+1.55, +3.20]
```

**The kill condition does not fire. Retrieval beats random. But read the lower bound: +0.05.**
This is a marginal pass, not a strong one, and the absolute numbers are worse news than the
comparison: at k=15 the retriever delivers **1.6 useful patterns and 13.4 irrelevant ones**,
for 3,060 tokens. 89% of what it returns is noise.

The ceiling is also low. Even hand-picked selection with the whole corpus visible scores
**0.263** — so at k=15, three quarters of a *perfect* selection is still noise by a strict
grader's standard. That is a fact about the corpus-to-prompt matching problem, not about BM25.

**Self-assessment inflation, measured in passing.** The oracle rated its own picks at 6.7/15
relevant. Blind graders rated the same picks at 4.0/15. It over-rated itself by 68%. Anything
in this repo that self-scores should be assumed to do the same.

### Post-hoc: k=15 is the real mistake

**Declared post-hoc** — the primary comparison above was pre-registered; this curve was
computed after seeing the result and is therefore weaker evidence.

| k | prec@k | relevant found | tokens/prompt |
|---|---|---|---|
| 1 | 0.250 | 0.25 | 204 |
| 3 | 0.200 | 0.60 | 612 |
| 5 | 0.150 | 0.75 | 1,020 |
| 15 | 0.107 | 1.60 | 3,060 |

The ranking is real: BM25's 32 relevant hits land at median rank 6, with 15 of 32 in the top 5.
Precision more than doubles from k=15 to k=1. **k=15 was chosen by analogy with ITR and is
wrong here** — it buys 1 extra relevant pattern for 2,448 extra tokens.

### Controls

The five mechanical prompts (regex, async/await, postgres index, timezone, vite build) drew
0.4/15 relevant for bm25 and 0.8/15 for oracle. Near-zero, as they should be. But note *why*:
strict grading, not gating. The system still **retrieved and would still have shown** 15
patterns for "why is this regex not matching."

### Limitations

n=20 is a pilot, not a publication. One grader per set — no inter-rater reliability. Graders
are LLMs, and LLM judges carry known position and self-preference biases; arm order was
shuffled per prompt to blunt position bias, which is a mitigation and not a fix. One retriever
(pure lexical, no embeddings, no reranker) — the weakest reasonable floor by design.

### What this changes

1. **Default k drops from 15 to 3–5.** Better precision, ~5× cheaper.
2. **The semantic gate is now required, not optional.** Eval 01b showed lexical scoring cannot
   gate; the oracle showed a semantic judge can. Combining them — BM25 to rank, one cheap
   semantic call to gate and cut — is the only configuration the evidence supports.
3. **The honest pitch is "roughly twice random, from a very low base," not "it works."**

## Eval 02b — k=4 + semantic gate · RUN · 2026-08-03 · **large win, one real loss**

BM25 retrieves 8 candidates; a semantic gate (an agent, given only the prompt and the 8) keeps
≤4 or none. Scored against the v1 blind graders' relevance judgments — those graders saw these
exact patterns, judged them blind, and were run **before the gate existed**. No circularity:
the gate never saw the grades, the graders never saw the gate.

| metric | v1 (k=15, no gate) | v2 (k≤4, gated) |
|---|---|---|
| precision | 0.107 | **1.000** (12/12) |
| signal — relevant shown/prompt | 1.60 | **0.60** |
| noise — irrelevant shown/prompt | 13.40 | **0.00** |
| silence on control prompts | 0/5 | **5/5** |
| tokens/prompt | 3,060 | **122** |

**Every pattern the gate kept was independently judged relevant.** Noise went to zero, the
five mechanical prompts got silence, and cost fell 25×.

**The loss is real and must not be buried: signal dropped from 1.60 to 0.60.** The gate
returned nothing on 13 of 20 prompts, including several where the oracle found 6–12 applicable
patterns. You are shown less useful material than before.

### Root cause: candidate recall is 27%, and it is the retriever

The obvious reading — "the gate over-rejects" — is wrong, and the diagnostic says so:

```
Of the patterns graders judged relevant, how many appear in BM25's top-8?
  23 / 84 = 27%      (0% on 7 of 20 prompts)
```

On p04 (*"we have 4 users, two of them are me and my cofounder"*) the graders found 12 relevant
patterns and **BM25 surfaced none of them**. The gate returned empty and gave the correct
reason unprompted: *"the relevant advice (go do unscalable things with users) is not among
these eight."* It rejected accurately. It was never shown the right candidates.

**The bottleneck is lexical retrieval recall, not gate precision.** A smarter gate cannot fix
this, and raising k only buys noise — eval 02 already showed precision falling as k rises.
The fix is a semantic retriever at the candidate stage: embeddings, or an LLM pass over
pattern names. That is the next experiment and the only one worth running.

### Limitations

n=12 kept patterns is a very small sample for a 100% figure — read it as "no false positives
observed in 12," not as a precision guarantee. Single gate agent, no inter-rater check on the
gate itself. Ground truth is the union of v1 graders' relevance marks, so it inherits their
strictness and their LLM-judge biases.

## Eval 03 — output quality · NOT RUN

Blocked on shipping the k=3–5 + semantic-gate configuration. Running it against the current
k=15 setup would measure a configuration the evidence says not to use.
