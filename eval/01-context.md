# Eval 01 — context cost of retrieval vs loading the corpus

**Question:** how many tokens does a retrieved subset cost against loading the whole corpus?

**Why this one first:** it is deterministic. No judges, no variance, no model calls. If the
saving is not large it does not matter whether selection works, so this gates everything else.

**Method:** measure the corpus, measure a k=15 retrieved subset, project both to N=1000
patterns. Token estimate uses the standard ~4 chars/token English approximation; treat it as
±10%, and swap in a real tokenizer before publishing any number.

**Run:** `python3 eval/measure.py`

**Status:** run. See `RESULTS.md`.

---

# Eval 02 — does selection beat random? (NOT YET RUN)

**Question:** for a given prompt, does the retriever return patterns a blind human/judge rates
as relevant, more often than a random draw from the corpus?

**Why this is the load-bearing one.** [Zheng et al. 2024](https://arxiv.org/abs/2311.10054)
found that manual selection of the right principle helped significantly while *automatic*
selection was "no better than random." If that reproduces here, the corpus is a liability:
you pay context for noise. **This eval can kill the project, and is supposed to be able to.**

**Method:**
1. 40 realistic founder/product/engineering prompts, written before the patterns are indexed.
2. Three arms per prompt, k=15: `retrieved` · `random` · `oracle` (hand-picked).
3. A grader sees the prompt and one unlabelled set. Rates each pattern relevant / not.
4. Arms are shuffled and unlabelled. The grader never learns which arm it holds.
5. Report precision@15 per arm, plus the retrieved-vs-random gap with a CI.

**Kill condition:** if `retrieved` is not clearly above `random`, stop. Do not scale to 1000.

**Do not:** let the same model that wrote the patterns grade relevance in the same session.
Measured: a reviewer given the artifact plus its production history scores no better than
plain self-review.

---

# Eval 03 — does it improve output? (NOT YET RUN, blocked on 02)

**Question:** does a retrieved pattern set produce better output than no corpus?

**Method:** Anthropic's shipped A/B protocol — collect realistic prompts, run each in a
**fresh session** with the skill available and again with it disabled, compare. Fresh matters:
leftover authoring context masks gaps.

**Arms:** `none` · `full corpus loaded` · `retrieved k=15`. The middle arm is not filler — it
tests whether retrieval beats brute force, which is the entire architectural bet.

**Grading:** blind, anchored rubric with per-band descriptions (holistic 0–10 clusters at 7–9
regardless of quality). Judges get the output and the rubric — never the prompt's arm label,
never the corpus.

**Report negatives.** A null result published is worth more than a win asserted.
