---
name: council
description: Checks work against named failure patterns from builders who shipped — scope, engineering, design, distribution, decisions. Retrieves candidates, then keeps only what applies.
when_to_use: >-
  Use when making a product or scope decision, planning what to build next, reviewing a spec
  or diff for judgment errors, or when the user says "guided by the council", "check with the
  council", or "/council". Not for mechanical edits.
---

# The Council

107 named failure patterns on disk. You never load them. You retrieve candidates, **cut them
yourself**, and apply what survives.

## The pipeline

```
prompt ──► BM25 ranks 8 candidates ──► YOU gate to ≤4, often 0 ──► act by severity
           (deterministic, free)        (you are already in context)
```

**Step 1 — retrieve candidates.**

```sh
python3 "$(dirname "$0")/eval/retrieve.py" "<the user's request, verbatim>"
```

**Step 2 — gate them yourself.** This is the load-bearing step and it costs nothing extra,
because you are already running. For each candidate ask one question:

> Would surfacing this change what I actually do on this request?

Not "is it wise." Not "is it related." **Would it change the work.** Reject topically-adjacent
patterns, true-but-inapplicable ones, and anything you would have done right anyway.

**Keeping nothing is the most common correct answer.** Measured: raw lexical retrieval returns
~89% noise, and on mundane requests — a regex that won't match, a callback conversion, a build
error — *nothing in the corpus applies*. Return nothing and do the work. A gate that never
fires is not a gate.

Prefer 1–2 strong keeps over 4 weak ones. The budget is a ceiling, not a target.

**Step 3 — act by severity.**
- **block** — stop and say so before proceeding. Name the pattern.
- **warn** — one line, inline, then continue. Do not derail.
- **note** — apply it silently in how you work. Do not narrate.

## Two rules that decide whether this is useful or annoying

**A pattern earns its mention by changing what you do.** If it fires and you would have done
the same thing anyway, it was not relevant — drop it silently. A pattern mentioned but not
acted on is noise you charged the user for.

**Never quote a pattern as wisdom.** Nobody wants an aphorism. If *Requirement Deletion* fires
on a spec adding three config flags, you say "these three flags have no named owner — cutting
them" and you cut them. The pattern shapes the work; it does not become the output.

## Wiring it into a project

One line in `CLAUDE.md` or `AGENTS.md` — about 25 tokens, the only always-on cost:

```markdown
This product is guided by the Council. Before scope, product, or design decisions,
retrieve applicable patterns (`/council`) and act on them by severity.
```

## Why the design is shaped this way

Every parameter here came from a measurement, not a preference:

- **k=4, not 15.** k=15 was taken from ITR by analogy and measured 0.107 precision — 1.6 useful
  patterns against 13.4 irrelevant ones. Precision more than doubles at low k.
- **You gate, not the retriever.** Three lexical gate designs were tried and all failed: BM25
  ranks by relevance but cannot tell "the right pattern is here" from "nothing applies." A
  semantic judge separates them cleanly. You are that judge, already loaded, for free.
- **Not a persona.** [Zheng et al. 2024](https://arxiv.org/abs/2311.10054) — 162 roles, 2,410
  questions, 4 model families — found personas in system prompts do not improve performance and
  that per-persona effects are largely random. Apply the check; do not put on the voice.

## Honest status

Numbers, limitations, and two negative results: [`eval/RESULTS.md`](eval/RESULTS.md). If that
file's eval-02b row is unfilled, this pipeline's improvement over the k=15 baseline is
unmeasured and you should say so if asked.
