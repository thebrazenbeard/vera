# V.E.R.A. Workstream Turn-Taking Protocol V2

## Status

Current nonproduction workstream coordination protocol.

This V2 supersedes V1 for current routing, ownership, lease, and execution semantics. V1 remains historical evidence only where it conflicts with this file or `PROTOCOL_EXECUTION_PRECEDENCE_V2.md`.

GitHub is the sole work-bearing coordination surface. Slack and legacy Supabase coordination records may be historical evidence but are not current workflow authority.

This protocol does not by itself authorize protected effects such as merge to protected/default/release branches, deployment, production provider mutation, credentials, repository archive/delete/visibility/settings changes, paid infrastructure, or canonical-memory effects.

## Purpose

Keep work moving while preventing actual collisions and consequential unauthorized effects.

The protocol is deliberately asymmetric:

- ordinary reversible work should be easy to start and easy to verify;
- shared mutable work should have one resolved writer;
- repository-local stewardship must be respected where Patrick has designated it;
- protected effects should remain deliberately gated.

The system must not make all categories equally difficult.

## Instruction precedence

A current specific instruction or assignment controls its bounded target over older generic workflow rules.

When Patrick or a current coordinator says to perform a reversible repository act, that instruction includes the minimally necessary reversible setup and verification needed to perform it unless explicitly excluded.

Do not demand the same permission again in a more ceremonial format.

A current Patrick-designated repository-local steward outranks broader project roles for mutations inside the delegated repository scope. Patrick remains final authority. Stewardship is scoped, not global.

## Work classes

### 0 — Observe

Read, search, compare, inspect, reason, test locally, and verify without external mutation.

No writer lease.

### 1 — Isolated owner work

Actor-owned branches, actor-owned Chat Bus lanes, local or branch-local drafts/tests, append-only acknowledgments/handoffs, and other reversible work that cannot collide with another writer because the actor owns the surface.

A current assignment is sufficient authority. If the actor-owned branch does not exist and the assignment says to use or create it, the actor creates it from the specified or freshly resolved base and thereby establishes sole-writer ownership for that lane.

No separate lease round-trip is required.

### 2 — Shared mutable work

Existing shared implementation/integration branches, shared PR surfaces, cross-component files, or any target with a plausible concurrent writer.

Resolve one current writer before mutation. A lease or equivalent GitHub ownership record exists to prevent collision.

If the assignment itself clearly designates one writer and no conflicting writer exists, that designation is sufficient; do not create a second permission ceremony merely to restate it.

### 3 — Protected effect

Merge, release, deployment, live install, production data/schema mutation, credentials, paid infrastructure, repository archive/delete/visibility/settings/ruleset changes, canonical-memory effects, and any effect explicitly reserved to Patrick or another owner/steward.

Requires separate exact current authority appropriate to the effect unless Patrick has already expressly granted that exact effect in the current task.

## Repository-local stewardship

Repository-local stewardship answers a different question from writer ownership: `who has delegated repository authority here?`

A broad coordinator may be the current project integrator and still lack mutation authority in a repository where Patrick has installed a higher local steward. In that case:

- the coordinator must not mutate around the steward;
- writer leases cannot be used to bypass the steward;
- reads remain allowed unless Patrick restricts them;
- the steward's local precedence does not expand into unrelated repositories or providers;
- Patrick can change the designation at any time.

## Ownership semantics

Ownership answers `who writes this mutable surface right now?` It does not manufacture authority for the objective and does not bypass a repository-local steward.

For an actor-owned Class-1 branch, ownership begins when that actor creates or validly claims the branch under a current assignment and ends on handoff, transfer, abandonment, supersession, or correction.

For Class-2 shared work, ownership must be explicit enough to exclude concurrent writers. The exact form may be a GitHub assignment, issue comment, branch-local ownership record, or lease packet where the complexity genuinely warrants one.

Do not require a maximal packet when a simpler unambiguous ownership record answers the collision question.

## Standard operating loop

For an executable current assignment:

1. **ORIENT** — read the current GitHub assignment, target state, and any applicable repository-local steward boundary needed for the next act.
2. **ACT** — perform the next authorized reversible step.
3. **VERIFY** — read back the effect or run the relevant check.
4. **CONTINUE** — if the next bounded step is still clearly inside scope, do it.
5. **HANDOFF/REPORT** — publish the result, exact head where material, limitations, and next dependency.

Do not split `ORIENT`, `ACT`, and `REPORT` across multiple conversational turns when the tools allow one complete bounded cycle.

## Branch creation

Branch creation is not a protected effect by default.

When an instruction says to work on, create, or own an isolated branch/lane:

- if it exists, verify ownership/currentness and use it;
- if it is absent, create it from the named base;
- if no exact base SHA was specified, freshly resolve the named base immediately before creation;
- if branch creation fails deterministically, report the actual tool/auth/conflict failure;
- do not treat absence itself as a blocker;
- do not create it if a current higher repository-local steward boundary excludes that mutation.

Creating a branch does not authorize merge, deployment, production mutation, or writes to another actor's branch.

## Reviews

Independent reviews remain exact-head operations.

A reviewer may inspect and return a bounded verdict for the exact head. The reviewer does not patch the reviewed head unless current instructions explicitly change the role from reviewer to writer and any applicable repository-local steward boundary permits it.

A later commit makes the prior exact-head review historical. This exactness rule applies to review claims; it is not a reason to block unrelated Class-1 setup work.

## Handoffs

A useful handoff contains only what downstream work actually needs, normally:

- work item / assignment identity;
- repository + branch;
- exact final head when repository bytes matter;
- what materially changed;
- verification/test result;
- unresolved blocker or limitation;
- next recipient or dependency.

Do not require a large ritual packet where those facts are already unambiguous.

## Corrections

A current correction changes behavior before explanation.

If an actor discovers that it improperly stopped for redundant permission:

1. re-evaluate the original instruction under V2;
2. if the act is executable Class 0/1, still current, and inside any steward boundary, perform it;
3. verify it;
4. report the correction and cause;
5. propagate the corrected interpretation to the active task family.

Do not merely apologize and leave the original task undone.

## Legitimate blockers

Stop only for a blocker that matters to the next act, such as:

- materially ambiguous target/outcome;
- conflicting current instructions;
- competing current writer on a shared target;
- current repository-local steward boundary excluding the mutation;
- missing protected-effect authority;
- deterministic authentication/authorization/tool/schema/integrity/safety failure;
- divergent/ambiguous non-idempotent effect requiring inspection;
- failed verification that makes continuation unsafe;
- explicit instruction to wait for approval.

`A stricter packet could exist` is not a blocker.

## Anti-patterns

The following are failures under V2:

- `branch absent -> therefore I cannot create the branch` when creation was assigned;
- `isolated branch requested -> stay local until a second Git permission arrives`;
- `current coordinator assigned me -> ask coordinator to assign me again with more fields`;
- `safe reversible step available -> fail closed because uncertainty exists somewhere else in the project`;
- `I know the next action and can perform it -> report what I would do instead`;
- `new specific instruction conflicts with an older generic restraint -> follow the older generic restraint without resolving precedence`;
- `Patrick must relay a handoff that GitHub can carry directly`;
- `I am the global coordinator -> therefore I may bypass the current repository-local steward`.

## Exactness where it belongs

Exact commit heads, byte hashes, immutable reviews, test receipts, and readback remain mandatory when a claim depends on exact repository/provider state.

Exactness is evidence discipline. It must not be transformed into redundant permission discipline.

## Reality boundary

This protocol governs observable work coordination and tool use. It does not imply hidden execution, continuous activity, consciousness, subjective continuity, or autonomous authority.
