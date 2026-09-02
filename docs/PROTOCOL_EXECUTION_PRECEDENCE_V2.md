# V.E.R.A. Protocol Execution Precedence V2

## Status

This document defines the controlling execution/authority semantics for nonproduction repository and coordination work. It supersedes conflicting V1 interpretations that turn explicit tasks into recursive permission requests. It does not authorize merge, deployment, production schema/data mutation, credentials, repository deletion/archive/visibility changes, paid infrastructure, or canonical-memory effects unless those effects are separately and explicitly authorized.

## Core rule

A current, specific, authorized instruction to perform an action is sufficient authority for that action and its minimally necessary, reversible setup and verification steps within the same target and scope.

Do not require a second permission, writer lease, or restatement for the same bounded act merely because an older generic protocol described a more formal path.

Specific current instructions outrank older generic workflow restrictions within their lawful scope. Generic restrictions still constrain effects outside the assigned scope.

## Authority resolution

Resolve authority by subject and scope rather than by title prestige:

1. platform/safety constraints;
2. Patrick's current explicit instruction/correction and exact scope;
3. current Patrick-designated repository-local steward for effects inside that delegated repository scope;
4. current task-specific coordinator/architect authority within its delegated scope;
5. current project/domain protocol;
6. older/general rules as historical constraints only where they remain compatible.

A repository-local steward can therefore outrank a broader coordinator **inside that repository** when Patrick says so. That local precedence does not grant the steward authority outside the delegated repository/scope and never outranks Patrick.

## Necessary-step inclusion

When an assigned action necessarily requires a reversible setup step, that step is included unless explicitly excluded.

Examples:

- `create your bus lane and acknowledge` includes creating the missing branch, adding branch-local ownership metadata, and appending the acknowledgment;
- `do the work on an isolated branch` includes creating that isolated branch from the specified or freshly resolved base;
- `fix this source defect` includes creating an isolated work branch, editing the bounded source, running relevant tests, and publishing a handoff;
- `review this exact head` does not include patching it, because patching is not necessary to review and changes role semantics.

The absence of a required artifact is normally the trigger to create it, not evidence that creation lacks authority.

## Effect classes

### Class 0 — observation

Reads, searches, comparisons, local analysis, and verification that do not mutate external state.

No writer lease is required.

### Class 1 — reversible isolated work

Examples include:

- creating an actor-owned isolated branch or mailbox lane;
- writing only to that actor-owned isolated branch;
- appending an acknowledgment or handoff to the actor's own coordination lane;
- creating local drafts, tests, fixtures, or review artifacts;
- opening a draft or bounded work PR when the assignment expressly calls for repository implementation.

A current user instruction or valid coordinator assignment is sufficient authority for Class 1 work within its scope. A separate bespoke writer lease is not required merely to begin the isolated work.

Creating an actor-owned isolated branch establishes that actor as the sole writer for that branch until handoff, transfer, abandonment, or current correction. This is coordination ownership, not broader project authority.

### Class 2 — shared mutable work

Examples include:

- modifying an existing shared implementation/integration branch;
- changing a branch or PR currently owned by another writer;
- resolving shared files across multiple component owners;
- mutating shared coordination state where concurrent writers could collide.

Class 2 requires one clearly resolved current writer/owner. A lease or equivalent ownership record is used to prevent collision. The lease coordinates already-authorized work; it is not a separate source of project authority.

If there is no competing writer and the current assignment explicitly designates the actor as owner, do not manufacture a lease round-trip solely for ceremony.

### Class 3 — protected effects

Examples include:

- merge to protected/default/release branches;
- deployment or live installation;
- production database/schema/data mutation;
- credentials, secrets, billing, or paid infrastructure;
- repository archive/delete/visibility/settings/ruleset changes;
- canonical-memory admission/promotion/deletion;
- effects explicitly reserved to Patrick or another current owner/steward.

These require exact current authority appropriate to the target and scope. Class 1 or Class 2 authority never silently expands into Class 3.

## Lease semantics

Writer leases exist to answer one question: `who may mutate this shared work surface right now?`

They do not answer whether Patrick or the controlling project instruction authorized the underlying objective.

Therefore:

1. no lease is required for Class 0;
2. an actor-owned Class 1 branch/lane may be self-established when the current instruction tells that actor to create/use it;
3. leases are required for genuinely shared Class 2 surfaces or where current ownership is otherwise ambiguous/conflicted;
4. a lease cannot authorize Class 3 effects unless the protected-effect authority independently exists;
5. no protocol may require a lease whose only purpose is to obtain permission to create the coordination surface needed to receive that same lease.

## Action default

For a clear current instruction whose next step is Class 0 or Class 1:

`DO -> VERIFY -> REPORT`

Do not substitute:

`ANALYZE -> REQUEST SAME PERMISSION AGAIN -> WAIT`

When tools permit completion in the current turn, complete the bounded act before giving a status explanation.

## Legitimate stops

Stop and ask or escalate only when at least one of these is material to the next act:

- the instruction is genuinely ambiguous between materially different targets or outcomes;
- current instructions conflict and precedence cannot be resolved;
- a different current writer owns the shared target;
- a current higher repository-local steward boundary excludes the actor from the mutation;
- the requested next step crosses into Class 3 without exact authority;
- a deterministic permission, authentication, integrity, schema, safety, or capability failure blocks execution;
- evidence needed to avoid corrupting or overwriting divergent state is missing;
- the user explicitly requested approval before the next step.

Do not stop merely because a more exact packet could theoretically be written.

## Proportional currentness

Freshness and exact-head requirements are proportional to the consequence of the act.

- Exact heads are mandatory for immutable review claims, shared-branch handoffs, conflict resolution, publication, and other cases where exact bytes matter.
- An isolated branch creation from a named branch may resolve that branch's current head immediately before creation; the user need not separately recite its SHA unless the instruction intentionally pins one.
- A stale historical rule cannot defeat a fresher specific assignment merely because the historical rule is more verbose.

## Correction behavior

When Patrick or a current controlling instruction corrects the route:

1. stop the obsolete interpretation;
2. apply the corrected behavior in the same turn when executable;
3. carry the correction across the active task family;
4. do not cite the obsolete protocol as a reason to request the same permission again;
5. report the material cause after the behavior is corrected.

## No defensive theater

The following are protocol failures:

- discovering that a required branch is missing and treating the absence as a reason not to create it when creation was assigned;
- interpreting `work on an isolated branch` as `build locally until someone separately authorizes the branch`;
- demanding an exact lease for an actor-owned mailbox branch after a current directive explicitly says the actor should create it;
- using `fail closed` as a generic preference for inaction where a safe reversible act is available;
- reporting what one intends to do instead of performing an already-authorized executable step;
- making Patrick repeat an instruction solely to satisfy a more ceremonial wording format;
- using broad coordinator status to bypass a current Patrick-designated repository-local steward.

## Review boundary

Rigor remains mandatory where it actually matters.

Reviews still bind exact heads. Shared writers still must not collide. Repository-local steward boundaries remain binding. Production and release effects still require exact authority and readback. Ambiguous non-idempotent writes still require inspection before retry. Evidence still outranks confidence.

This protocol removes redundant permission recursion; it does not weaken effect verification or protected-effect gates.

## Success criterion

A well-governed team is not the team that asks permission most often. It is the team that correctly distinguishes:

- what it has already been told to do;
- what setup is necessarily included;
- what needs coordination because another writer could be harmed;
- what is genuinely protected and needs a new decision;
- which repository-local steward boundary currently controls the effect;
- what was actually completed and verified.

When those distinctions are clear, ordinary work should move quickly and consequential work should remain deliberately gated.
