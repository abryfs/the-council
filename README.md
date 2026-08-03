# the-council

**A retrieval-loaded corpus of builder patterns for coding agents.** Not a persona pack. Not
a rules file. A library of named failure patterns from people who shipped, where only the
~15 relevant to your prompt ever enter context.

> Working title. Rename before publishing.

---

## The claim, and what backs it

Most agent "rules" repos ship one big always-on file. That fails for a measured reason: the
perfect-response rate at N=40 simultaneous instructions is 0.09–0.31, and effectively zero by
N=80. A thousand one-liners in context is not a strong prompt — it is noise that buries the
six rules you care about.

The alternative is retrieval. [Instruction-Tool Retrieval (arXiv:2602.17046)](https://arxiv.org/html/2602.17046v1)
measured this architecture against a monolithic-prompt baseline:

| | Monolithic | Retrieved | Δ |
|---|---|---|---|
| Per-step context tokens | 30,000 | 1,500 | **−95%** |
| Tool routing accuracy | 62% | 82% | **+32% rel.** |
| Cost per episode | $2.90 | $0.86 | **−70%** |

That is the mechanism this repo implements. It is *not* evidence that builder patterns
improve output — see **Open risk** below, which is the honest part.

## Why patterns, not personas

We tried the persona framing first and dropped it on evidence.
[Zheng et al., EMNLP Findings 2024 (arXiv:2311.10054)](https://arxiv.org/abs/2311.10054) —
162 roles, 2,410 questions, 4 model families — found that **adding a persona to a system
prompt does not improve performance**, and that per-persona effects are "largely random."

"Think like Jony Ive" is a costume. What Ive actually *articulated* — that you subtract until
removing one more thing breaks it — is a check you can run against a diff. Same people, same
wisdom, falsifiable form:

```
### Requirement Deletion
Optimizing a part that should not exist. Every requirement carries a name, and if
it carries no name it has no owner and no reason.
CASE — Musk's five-step process; the fastest-deleted parts on the Model 3 line
were ones nobody could attribute to a person.
TRIGGER — a spec adds a field, flag, config knob, or abstraction layer
SEVERITY — warn
```

Name · mechanism · real case · trigger · severity. Grep-able, testable, citable.

## Open risk — read this before believing anything

**The selector is the whole product, and it is unproven.** The persona paper's sharpest
finding is that *manual* selection of the right principle helped significantly, while
*automatic* selection performed **no better than random**. A corpus of 1,000 patterns with a
random selector is strictly worse than no corpus: you pay context for noise.

So the question this repo has to answer is not "do builder patterns help?" It is:

> **Can we retrieve the right ~15 patterns out of 1,000 for a given prompt, better than chance?**

Until `eval/` reports a number on that, this is a hypothesis with good citations. It is
stated here rather than buried because every comparable repo ships vibes, and the one
credible project in this space ([obra/superpowers](https://github.com/obra/superpowers))
earned that by publishing results that went against its own changes.

## Measured so far

| Claim | Status |
|---|---|
| Retrieval cuts context vs loading the corpus | **measured locally** — see `eval/RESULTS.md` |
| Retrieval picks relevant patterns better than random | **not yet run** — `eval/02-selection.md` |
| Patterns improve output quality vs no corpus | **not yet run** — `eval/03-quality.md` |
| Corpus scales to 1,000 without precision collapse | **not yet run** — blocked on the above |

Nothing moves from "not yet run" to a claim in this README without the numbers next to it,
including negative ones.

## Build order

1. 30 patterns, 3 domains. **← current**
2. Selection eval. If retrieval is not beating random, stop — 1,000 patterns would be 1,000 wasted entries.
3. Quality eval, blind-graded, three arms (none / full corpus / retrieved).
4. Only then scale the corpus.

## Not English-encoded, and why

An early idea was storing the corpus in another language to save tokens. It is backwards:
tokenizers are English-centric, and English is the cheapest per unit of meaning. Simplified
Chinese runs ~1.13× English; Polish and Hindi ~1.42×
([Frontiers, 2025](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1538165/full)).
LLaMA 3.2 gets 4.9 chars/token on English vs 3.6–3.8 on Spanish/French. Encoding elsewhere
costs more tokens *and* degrades instruction-following. Recorded so nobody retries it.

## License

MIT.
