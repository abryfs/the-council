# Why it failed, mechanistically — and what the mechanism says to build

The [results](eval/RESULTS.md) are three nulls. This file is the account of *why*, at the level
of attention heads and training frequency rather than behaviour, and the design rules that fall
out of it.

The short version: **the corpus had a small norm.**

---

## 1. Agreeing context is invisible to a behavioural eval

Retrieved text and parametric memory are **separate additive write-paths, not a merge.**

Some attention heads write value vectors that raise the logit of the *memorized* answer; others
raise the logit of the token present *in context*. The output is the argmax over their sum.
These are separable enough that scaling one identified memory head's value vector by α = −0.7
flips in-context-answer rate to 86.2%, by modifying **0.00001% of parameters**
([arXiv:2310.15910](https://arxiv.org/abs/2310.15910); replicated by Ortu et al. ACL 2024 and
PH3, [arXiv:2402.18154](https://arxiv.org/abs/2402.18154)).

When the retrieved text **agrees** with the prior, both families push the same token. Two
positive contributions to a token already at argmax move the logit margin and cannot move the
decision. A behavioural eval samples the argmax.

> An agreeing corpus is not weakly visible to a behavioural eval. It is **invisible**.

Three further mechanisms each independently predict a zero result:

**The circuit was off the critical path.** Retrieval heads are <5% of heads and implement
token-level copy-paste. Ablate them and long-context retrieval collapses — *but tasks relying on
parametric knowledge degrade minimally*
([arXiv:2404.15574](https://arxiv.org/abs/2404.15574)). 67% recall delivered text into a circuit
that wasn't load-bearing for what was measured.

**Deference falls as prior confidence rises.** Adherence to conflicting context declines roughly
linearly with the model's unconditioned probability on its own answer, average slope −0.23
across six domains (ClashEval, [arXiv:2404.10198](https://arxiv.org/abs/2404.10198)). Parametric
strength is log-linear in pretraining duplication count
([arXiv:2211.08411](https://arxiv.org/abs/2211.08411)). Canonical builder advice sits at the far
right of that axis — exactly where the adherence curve floors.

**ICL is a low-norm modulation.** In-context learning compresses demonstrations into a task
vector θ(S) that modulates the forward pass
([arXiv:2310.15916](https://arxiv.org/abs/2310.15916)). A corpus specifying a function the model
already computes yields θ(S) ≈ θ_default.

**The corpus is not even neutral.** Partially-consistent evidence triggers confirmation rather
than neutrality ([ICLR 2024, arXiv:2305.13300](https://arxiv.org/abs/2305.13300)), raising the
prior-confidence term that gates *every future* context update. An agreeing corpus makes the
model marginally **harder** to correct with the next document.

---

## 2. What a corpus must be to produce lift

Four properties, each measurable **before** building anything.

| Property | Test |
|---|---|
| **Low pretraining frequency** | Target the <10² supporting-document regime — private, post-cutoff, org-specific |
| **High surprisal under the base model** | Measure logprobs. If the model would generate it, it carries zero bits |
| **Literal strings that must appear** | Induction heads copy *tokens*, not concepts — identifiers, flags, exact paths, version numbers |
| **Arbitrary, not derivable** | Could a competent person reconstruct it from first principles plus the visible artifact? If yes, the prior has it |

**The screening procedure**, which this project should have run first: for each candidate claim,
sample the base model unprompted on the eliciting situation n ≥ 20. **Anything it produces >80%
of the time is dead weight.** It can only move a margin you never observe.

### The same repo demonstrates both classes

These are the right shape — arbitrary, unrecoverable, low-frequency, full of literal strings:

- `gbrain config set` writes the DB plane and is a silent no-op for `embedding_model`; that field is file-plane.
- `gbrain sync` runs `git pull` in the target working tree by default. Always pass `--no-pull`.
- `api/` is a separate Go module whose Docker build context is `api/` only, so importing root-module `internal/embed` compiles locally with a `replace` and fails the image build.
- `internal/place.Centroids()` filters `p.Depth == DepthLeaf`, so non-leaf nodes carry no anchor vector.

These are not — derivable, high-frequency, at the confidence ceiling:

- Coordination must be a byproduct, never an act.
- A false interrupt is unrecoverable; a missed one is invisible.
- Solve at the layer all paths flow through.

Both sets are load-bearing for the humans. Only the first set can move a model.

---

## 3. Where a rule goes, and why

Assignment falls out of three facts: what is prefix-cacheable, what is conditional, and where
attention lands.

| Layer | Holds | Mechanism |
|---|---|---|
| **System prompt / output style** | **Dispositions only** | Cached prefix, visible to every token, lands on the Assistant-persona representation that character training targets. A checklist of situational imperatives here gets generalized into character |
| **CLAUDE.md + imports** | Only what is true **every** turn and unrecoverable | Same cache region. Cached ≠ free: still occupies the softmax denominator, still counts toward constraint count, still pays the length tax. Target 5–10k chars |
| **Skills** | **Everything conditional** | Progressive disclosure — only name+description preload. Just-in-time retrieval into the recency window *at the moment the rule applies*, so the rule never has to win an n-way softmax against the whole context |
| **Hooks** | Filtering, and event-local context | The only layer that is **both** late-position and conditional. `updatedToolOutput` removes tokens from the window entirely |
| **Turn-boundary recap** | One consolidated restatement | Attention on the system-prompt span is flat within a generation and **drops sharply between turns** (COLM 2024) |
| **Verifiers** | Anything that must hold | Converts a ~0.85 Bernoulli into a 1.0. The only layer that does |

**An instruction to "ignore irrelevant output" spends attention budget. A hook that deletes the
output spends none.**

---

## 4. The instruction budget is multiplicative, not a shared pool

ManyIFEval ([arXiv:2509.21051](https://arxiv.org/abs/2509.21051)): GPT-4o instruction-level
accuracy 0.94 at n=1 → 0.85 at n=10. **Prompt-level — all constraints satisfied — 0.94 → 0.21.**
Note 0.85¹⁰ = 0.197. A naive product-of-independent-Bernoulli estimator predicts prompt-level
accuracy within 0.02–0.05; instruction count alone predicts within ~10% (Pearson r = 0.994).
Claude 3.5 Sonnet: 0.95 → 0.48.

> The model does not trade constraints off against each other. It independently coin-flips each
> one, slightly worse. **Clarity per constraint is a weak lever. Count is the strong one.**

Ten separately-crystal-clear constraints do not beat five vague ones.

Two further costs, separable from count:

- **Raw length.** FLenQA holds task content fixed and pads with irrelevant text: ~0.92 → ~0.68 mean accuracy from 250 to 3000 tokens, well below the technical window limit ([arXiv:2402.14848](https://arxiv.org/abs/2402.14848)).
- **Distractors.** A *single* competing near-answer measurably degrades performance, four compound it, and models do consistently better on **shuffled** haystacks than coherent ones. Semantically adjacent neighbours inflate the local softmax denominator around the target.

That last one names the worst possible configuration: **a superseded claim sitting immediately
beside the rule that supersedes it, in the most coherent possible arrangement.** An annotated-in-
place correction block is exactly that.

---

## 5. Levers, ranked

1. **Delete superseded text rather than annotating it.**
2. **Reduce in-scope constraint count; split into passes.** 0.85¹⁰ = 0.21 → 0.85⁵ = 0.44.
3. **Convert unverified constraints to verifiers.** 0.85 → 1.0.
4. **Move conditional rules from auto-load to skills and hooks.**
5. **Position: load-bearing constraint at the start, restated at the end.** 22pp between best and worst placement (Liu, TACL 2024: 75.8% / 53.8% / 63.2%), and it holds in base models.
6. **Rewrite prohibitions as positive recipes with named substitutes.** Negation is computed correctly around layer 14 then overwritten by late-layer shortcut heads promoting the named concept; ablating those recovers +17.3pp / +20.7pp, ~15pp average across six models (ICML 2026). Naming the forbidden thing primes it.
7. **Gate thinking on task class.** +12.3pp math, +14.2pp symbolic, +6.9pp logic, **<1pp on everything else** across 1,218 comparisons ([arXiv:2409.12183](https://arxiv.org/abs/2409.12183)).
8. **Many-shot (50+) to override a prior.** The only prompt-level lever that beats a pretraining prior. The transition is around 50 shots, not 3.

**Measurably zero:** persona/role prompting. Temperature for single-sample accuracy. Escalation
formatting — "IMPORTANT!!! ALWAYS" pushes into a measured over-focus regime where instruction
dominance is bought with context blindness.

---

## 6. How to evaluate, given all of the above

This project's evals were well-executed and pointed at the wrong quantity. The corrections:

- **Build the item set from decisions where the base model is 40–60% split on repeated sampling.** A saturated base rate has no headroom; 12/12 has a 95% Wilson interval of [0.76, 1.00], so the maximum detectable improvement was ~24pp.
- **Report Δ on the base-model-failure residual**, not on the whole eval.
- **Always run a paired no-corpus arm.** Without it, a trap-set result cannot distinguish "the corpus defended" from "the base model was never going to fall for it."
- **Power it for the effect you expect.** 1 of 5 decisive pairs at p=0.969 is a non-result, not a null result.
- **Never trust the reasoning trace as ground truth.** Claude 3.7 Sonnet mentioned a hint it demonstrably used 25% of the time; on reward-hacking environments, <2%. Attribution graphs show cases with zero circuit correspondence between stated reasoning and computation.

---

## Confidence

**Established:** the memory-head/in-context-head separation and its ablation result; ClashEval's
prior-confidence slope; Kandpal's frequency curve; ManyIFEval's multiplicative shape; Liu's
position result; Sprague's thinking-by-task-class result; the persona null.

**Contested or single-source:** the banned-phrase priming measurement (single-author preprint,
though it converges with the ICML 2026 late-layer-shortcut result); attention-sink explanations
for any specific model; the duplicate-anchor entropy trade-off (formal analysis, no empirical
measurement).

**Extrapolated here, not measured:** that "constraints in scope on this turn" rather than
"constraints in context" is the right n; that the FLenQA curve extends past 3000 tokens.
