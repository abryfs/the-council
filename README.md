# the-council

**A retrieval-loaded corpus of builder patterns for coding agents.** Not a persona pack. Not
a rules file. A library of named failure patterns from people who shipped, where only the
handful that actually apply to your prompt ever enter context — and usually none do.

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

## The open risk, and where it landed

**The selector was always the whole product.** The persona paper's sharpest finding is that
*manual* selection of the right principle helped significantly while *automatic* selection
performed **no better than random** — and a corpus with a random selector is strictly worse
than no corpus, because you pay context for noise.

That risk has now been measured rather than argued. Selection does beat random (weakly), and
the two-stage pipeline drives precision to 1.000 with zero noise. But recall came out at 27%,
so the failure mode moved rather than disappeared: the tool no longer says wrong things, it
says nothing far too often. See **Measured so far**.

This is stated up front because every comparable repo ships vibes, and the one credible
project in this space ([obra/superpowers](https://github.com/obra/superpowers)) earned that by
publishing results that went against its own changes.

## Measured so far

| Claim | Status |
|---|---|
| Retrieval cuts context vs loading the corpus | **yes** — 86% at n=107, 98.5% projected at n=1,000 |
| A lexical confidence gate can tell "nothing applies" | **no** — three designs, all failed (eval 01b) |
| A semantic gate can | **yes** — oracle separated all 5 controls unprompted |
| Retrieval picks relevant patterns better than random | **yes, weakly** — 0.107 vs 0.057 prec@15, CI [+0.05, +1.45] |
| k=4 + semantic gate beats the k=15 baseline | **yes, decisively** — precision 0.107 → 1.000, noise 13.4 → 0.0, cost 25× lower |
| ...without losing useful signal | **no** — signal fell 1.60 → 0.60/prompt |
| Lexical retrieval can find the relevant patterns at all | **no** — candidate recall 27%; replaced |
| An agent scanning a compact index can | **yes** — recall 67%, end-to-end 26/26 precision at 1.30 signal, no dependencies |
| Patterns improve output quality vs no corpus | **NO** — 1/5 decisive pairs, sign test p=0.969. Kill condition fired. |
| Corpus scales to 1,000 without precision collapse | **moot** — not scaling a corpus that shows no benefit |

**The honest one-line summary: what it shows you is now trustworthy, and it shows you too
little.** The shipped pipeline (BM25 → 8 candidates → semantic gate → ≤4) surfaced 12 patterns
across 20 prompts and blind graders judged **all 12 relevant**, with zero noise, silence on
every mechanical prompt, and 122 tokens per prompt against 3,060 before. But it stayed silent
on 13 of 20 prompts, and the diagnosis is that **lexical candidate recall is 27%** — the right
patterns are usually not in the top 8 at all. The gate is good; the retriever is the
bottleneck. Full numbers, limitations, and three negative results in
[`eval/RESULTS.md`](eval/RESULTS.md).

Nothing moves from "not yet run" to a claim in this README without the numbers next to it,
including negative ones.

## Build order

1. ~~30 patterns~~ → **107 patterns, 5 domains.** Done.
2. ~~Selection eval~~ → beats random; two-stage gate reaches 1.000 precision. Done.
3. **Fix candidate recall (27%). ← current.** Semantic retrieval at the candidate stage.
   Nothing downstream is worth measuring until the right patterns reach the gate.
4. Quality eval, blind-graded, three arms (none / full corpus / retrieved+gated).
5. Only then scale the corpus toward 1,000.

## Not English-encoded, and why

An early idea was storing the corpus in another language to save tokens. It is backwards:
tokenizers are English-centric, and English is the cheapest per unit of meaning. Simplified
Chinese runs ~1.13× English; Polish and Hindi ~1.42×
([Frontiers, 2025](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1538165/full)).
LLaMA 3.2 gets 4.9 chars/token on English vs 3.6–3.8 on Spanish/French. Encoding elsewhere
costs more tokens *and* degrades instruction-following. Recorded so nobody retries it.

## License

MIT.
