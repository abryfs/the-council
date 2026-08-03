# Scope & prioritization patterns

Format: `### Name` · mechanism · `CASE` real instance · `TRIGGER` when to retrieve ·
`SEVERITY` block | warn | note

---

### The B-Problem Drift
When the A-problem has no clear solution, people quietly move to the second-order task that
does. Effort looks identical; value is not.
CASE — Thiel gave every PayPal employee exactly one thing and refused to discuss anything
else, specifically because with three priorities people gravitate to the one with a clear path.
TRIGGER — a proposal has an obvious clean fix while the stated problem is still unresolved
SEVERITY — warn

### Boiling the Ocean
Addressing every market and persona simultaneously, so no single one is served well enough
to pull.
CASE — Magic Leap: proprietary optics + new OS + content platform, years spent, none finished.
TRIGGER — a plan lists 3+ user types, platforms, or markets as v1 scope
SEVERITY — warn

### Requirement Deletion
Optimizing a part that should not exist. Every requirement carries a person's name; unnamed
requirements have no owner and no reason.
CASE — Musk's five-step process, applied on the Model 3 line: the fastest-deleted parts were
the ones nobody could attribute to a person.
TRIGGER — a spec adds a field, flag, config knob, or abstraction layer
SEVERITY — note

### Pre-User Polish
Spending on legal, copy, SEO, accessibility audits, i18n, or performance before anyone uses
the thing. All real, none now.
CASE — the standard pre-launch failure: a shipped ToS and no shipped product.
TRIGGER — work proposed on policy, copy polish, SEO, a11y, i18n, or unmeasured perf while
user count is zero
SEVERITY — warn

### The Reversibility Tax
Running heavyweight process on decisions you could undo in one commit. Most decisions are
two-way doors and should be made at speed.
CASE — Bezos: one-way doors get deliberation, two-way doors get a single high-judgment
person; large orgs fail by applying the former process to everything.
TRIGGER — a discussion is weighing options on something a single commit could reverse
SEVERITY — note

### Flag Instead of Fix
Reporting a problem whose solution you already know. A list of things you could have fixed
is a bill, not a report.
CASE — the dominant complaint about coding agents in 2026: work returned 90% done with the
remaining 10% described rather than executed.
TRIGGER — output contains "you may want to", "consider", or "note that X is broken" about
something inside the current task
SEVERITY — block

### Scope Grown By Helper
An agent or teammate expanding a task with unrequested improvements, so the diff stops being
reviewable and the original ask gets diluted.
CASE — measured on Opus 5 specifically: the model expands scope and applies its own judgment
about what the task should be, unless scope is constrained explicitly.
TRIGGER — a diff touches files the stated task did not name
SEVERITY — warn
