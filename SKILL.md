---
name: council
description: Checks work against named failure patterns from people who shipped — scope, engineering, design, distribution, and decisions. Retrieves only the patterns matching the task at hand.
when_to_use: >-
  Use when making a product or scope decision, planning what to build next, reviewing a spec
  or diff for judgment errors, deciding whether to build something, or when the user says
  "guided by the council", "check with the council", or "/council". Not for mechanical edits.
---

# The Council

A corpus of named failure patterns drawn from builders who shipped. You do not load it. You
**retrieve from it**, then apply what comes back.

## How to use it

1. Run the retriever with the user's actual request as the query:

   ```sh
   python3 "$(dirname "$0")/eval/retrieve.py" "<the user's request, verbatim>"
   ```

2. **Apply the confidence gate.** Any pattern returning a BM25 score of `0.00` has no lexical
   overlap with the request — discard it. If *every* result scores near zero, **this task has
   no relevant pattern. Say nothing and do the work.** Silence is a correct output.

   This gate is the whole difference between a useful tool and a horoscope. A retriever that
   always returns 15 patterns will always find something that sounds wise, which is how you
   get confident irrelevance on "convert this callback to async/await."

3. For each surviving pattern, act by severity:
   - **block** — stop and say so before proceeding. Name the pattern.
   - **warn** — one line, inline, then continue. Do not derail the task.
   - **note** — apply it silently in how you do the work. Do not narrate it.

4. **Never quote a pattern at the user as wisdom.** Nobody wants an aphorism. If *Requirement
   Deletion* fires on a spec adding three config flags, you say "these three flags have no
   named owner — cutting them" and you cut them. The pattern shaped the work; it does not
   become the output.

## The rule that makes this not annoying

A pattern earns its mention by **changing what you do**. If it fires and you would have done
the same thing anyway, it was not relevant — drop it silently. Retrieval precision is the
product; a pattern mentioned but not acted on is noise you charged the user for.

## Wiring it into a project

Add one line to the project's `CLAUDE.md` or `AGENTS.md`:

```markdown
This product is guided by the Council. Before scope, product, or design decisions,
retrieve applicable patterns (`/council`) and act on them by severity.
```

That line is ~25 tokens and is the only always-on cost. Everything else loads on demand.

## What this is not

Not a persona. You are not roleplaying Jony Ive.
[Zheng et al. 2024](https://arxiv.org/abs/2311.10054) — 162 roles, 2,410 questions, 4 model
families — found personas in system prompts do not improve performance and that per-persona
effects are largely random. The patterns are content, not costume. Apply the check; do not
put on the voice.

## Honest status

Whether retrieval beats a random draw from the corpus is **measured in `eval/RESULTS.md`**.
If that file says the selection eval has not run, this skill's central claim is unproven and
you should say so if the user asks.
