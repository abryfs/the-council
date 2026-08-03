# the-council

**A measured negative result about builder-pattern corpora for coding agents.**

The premise: give an AI coding agent a corpus of named failure patterns drawn from people who
shipped — Thiel, Brooks, Rams, Graham, Grove — retrieve only the handful relevant to each
prompt, and the agent gives better advice.

We built it and measured it three ways. **The retrieval works. The corpus does not help — and
the final experiment shows there is no headroom for it to help in.**

This repo is the method, the data, and the null. It is a work in progress, and the code is a
research harness rather than a product.

---

## Results

| Claim | Verdict |
|---|---|
| Retrieval cuts context vs loading the corpus | **yes** — 86% at n=107, 98.5% projected at n=1,000 |
| A lexical (BM25) gate can tell "nothing applies" | **no** — three designs, all failed |
| A semantic gate can | **yes** — separated all 5 controls unprompted |
| Retrieval beats a random draw | **yes, weakly** — 0.107 vs 0.057 prec@15, CI [+0.05, +1.45] |
| An agent scanning a compact index beats BM25 | **yes** — recall 27% → 67%, 26/26 precision, no dependencies |
| **Patterns improve output quality** | **NO** — 1 of 5 decisive pairs, sign test p=0.969 |
| **Patterns enforce a selection the model makes unreliably** | **NO** — 12/12 vs 12/12, +0 points (ceiling) |
| **Any headroom exists at all** | **NO** — adversarially built cases, base model fails 2/18 (11%) |

Full numbers, limitations, and a false null that nearly shipped:
**[`eval/RESULTS.md`](eval/RESULTS.md)**.

## Why it fails

**The corpus is made of the model's defaults.** Canonical startup wisdom is canonical because
it saturates training data. A corpus of it can only agree with what the model was going to say.

Measured directly: across three prompts and four independent runs each, the base model with
**no corpus at all** made the prescribed move **12 times out of 12**. It told the founder to
hand-install for five teams on a call. It demanded a flamegraph before conceding a rewrite. It
named work-already-spent as a fact about the past that doesn't earn rent. Every time, unprompted.

Injecting the pattern that says those things adds nothing. This is a **content** problem, and
no amount of retrieval or gating work fixes it.

## What does work, and is reusable

The pipeline is validated even though its payload isn't:

```
prompt → agent scans a compact index (name · severity · trigger) → ≤8 candidates
       → semantic gate: the calling agent keeps ≤4, often 0
       → act by severity
```

- **67% candidate recall**, against 27% for BM25. The failure was semantic, not lexical — nothing connects *"we have 4 users, two of them are me and my cofounder"* to *Skipping The Unscalable* by shared vocabulary.
- **26/26 precision** on what the gate kept, judged by independent blind graders who never saw the gate.
- **Zero noise, and correct silence** on all five mechanical control prompts.
- **No embeddings, no vector DB, no API key.** The gate is free because the calling agent is already in context. The index costs ~57 tokens per pattern, which caps the corpus near 150; above that you need embeddings.

If you have a corpus the model *cannot* already know, this machinery is here.

## Method

A negative result is worth exactly as much as its method, so:

- **20 prompts authored blind to the corpus**, by an agent explicitly forbidden from seeing it, including unmarked mechanical controls.
- **Analysis scripts written before results arrived** (`eval/score.py`, `eval/score2.py`), so the framing could not be tuned to the outcome.
- **Blind arms**, labels shuffled per prompt, the mapping held outside the graders' reach.
- **Pairwise judging in both orders**, with an AB/BA disagreement counted as an abstention rather than a vote. The order-flip rate was 44%, which is why this matters.
- **Ceiling effects and nulls reported at the same volume as wins.**
- **Predictions logged before each run.** Three were made. All three were wrong, and all three were optimistic in the direction the author wanted.

`eval/RESULTS.md` also documents a harness bug that produced a clean-looking false null — 9/9
ties at 100% order agreement — because a key mismatch fed every judge the string `undefined`.
The judges reported it correctly in their reasoning; the tally alone looked like unusually
rigorous evidence. It was caught by reading the reasoning instead of the count.

## What would be worth testing

**Patterns that contradict the model's default** — *"ship the ugly version"*, *"don't add the
abstraction even though it's cleaner"* — was the strongest counter-argument, and eval 05 was
built specifically to test it. Agents constructed adversarial cases from patterns chosen for
contradicting defaults, with the wrong answer made attractive. The base model failed **2 times
out of 18**. There was no headroom to measure, so no treatment arm ran. That direction is now
closed, not open.

**What remains is knowledge the model cannot have** — your own product's recorded failures and
their outcomes. *"Neon scale-to-zero suspends on query inactivity and pgxpool's health check
sends nothing"* is worth retrieving forever. *"Don't boil the ocean"* never was. That is a
private corpus, not a public one, and nothing here tests it.

Any future test needs prompts where the base model demonstrably **fails**, or it reproduces
this result.

## Not encoded in another language, and why

An early idea was storing the corpus in a non-English language to save tokens. It is backwards.
Tokenizers are English-centric and English is the cheapest per unit of meaning — Simplified
Chinese runs ~1.13× English, Polish and Hindi ~1.42×
([Frontiers, 2025](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1538165/full)).
LLaMA 3.2 gets 4.9 chars per token on English against 3.6–3.8 on Spanish and French. Encoding
elsewhere costs more tokens *and* degrades instruction-following. Recorded so nobody retries it.

## Not a persona pack

[Zheng et al., EMNLP Findings 2024](https://arxiv.org/abs/2311.10054) — 162 roles, 2,410
questions, 4 model families — found that personas in system prompts do not improve performance,
and that per-persona effects are largely random. "Think like Jony Ive" is a costume. What Ive
articulated is a check you can run against a diff. The patterns here are content, not voice.

## Reproduce

```sh
python3 eval/measure.py                      # context cost
python3 eval/retrieve.py "your prompt here"  # BM25 baseline retrieval
python3 eval/score.py                        # eval 02 — unblind and score
python3 eval/score2.py                       # eval 02b
```

`corpus.json` holds 107 patterns across product/scope, engineering, design, distribution, and
decisions. Each carries a named mechanism, a real cited case, a retrieval trigger, and a severity.

## Prior art worth reading

[obra/superpowers](https://github.com/obra/superpowers) is the one credible project in this
space, and it earned that by publishing results that went against its own changes. This repo
tries to hold the same bar.

## License

MIT — see [LICENSE](LICENSE).
