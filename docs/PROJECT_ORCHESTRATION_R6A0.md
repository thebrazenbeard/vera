# V.E.R.A. Project Orchestration — R6A0

## Status

This document defines the current repository integration program. It does not authorize production deployment.

- Canonical repository: `thebrazenbeard/vera`
- Canonical base: `main`
- Integration branch: `integration/project-orchestration-r6a0`
- Program tracker: issue #11
- Supabase project: `Vera` (`klmbpaigzeguvnpccqzz`)
- Neutral release: `VERA_NEUTRAL_CORE_R6A0_20260730_EC900174`

## Current observed state

### GitHub

`main` is currently anchored at `a0def4c6009d86181664fe246ebb1b0f5df30cb2`.

Active draft pull requests:

- #7: governed initiative kernel
- #8: governed coordination bus
- #9: fail-closed temporal enforcement kernel

PR #3 remains draft, suspended, and outside the active temporal critical path.

The Memory workstream has reported `feature/memory-cross-chat-contract-v1` through Supabase coordination, but no pull request was visible when this program document was created.

### Supabase

Production currently reports seven applied migrations:

1. `20260729012911_initialize_vera_save_state_ledger`
2. `20260729013307_harden_vera_save_state_trigger`
3. `20260729094322_harden_vera_save_state_access`
4. `20260729125913_add_vera_branch_coordination_ledger`
5. `20260730191337_add_neutral_vera_context_v3`
6. `20260730191421_harden_neutral_vera_context_v3_access`
7. `20260730191641_complete_neutral_vera_context_v3_hardening`

The repository must reconcile its numbered migration history with this observed production state before any future production migration is proposed.

## Architectural components

### Neutral core

Owns project boundaries, provenance, governance, semantic tagging, lifecycle rules, receipts, and reality honesty.

### Coordination

Owns addressed, append-only operational handoffs between workstreams. It does not own canonical memory or execute work by itself.

### Memory

Owns governed save, recall, revision, contradiction, supersession, tombstone, and ledger projection behavior. It preserves caller-supported temporal fields but does not invent elapsed time.

### Time

Owns trustworthy time acquisition, temporal evidence classification, elapsed-time computation, and fail-closed `UNANCHORED` results.

### Initiatives

Owns governed action selection over externally supplied candidates and policy. It may select or abstain; it does not invent objectives or execute actions.

### Runtime integration

Will own the explicit tool surface and lifecycle wiring that invokes the above contracts. It must not claim hooks or timestamps the host does not expose.

## Dependency order

1. **Release integrity:** version the complete R6A0 package and verify its checksums.
2. **Migration parity:** capture the production migration ledger in source control and prove a clean replay path.
3. **Coordination bus:** integrate the addressed handoff contract because every other workstream depends on a stable communication boundary.
4. **Memory/Time boundary:** resolve the current field-boundary review before approving either contract.
5. **Memory contract:** integrate governed persistence and retrieval without elapsed-time inference.
6. **Temporal enforcement:** integrate time acquisition and fail-closed temporal evaluation against the approved Memory boundary.
7. **Initiative kernel:** integrate action selection after authority, evidence, permission, memory, and temporal inputs have stable shapes.
8. **Runtime adapter:** expose the contracts through explicit tools with structured inputs and receipts.
9. **Combined verification:** run all workflows and end-to-end contract tests on the integrated branch.
10. **Production deployment:** require separate authorization for exact migrations, functions, and data operations.

## Merge gates

A workstream is merge-eligible only when:

- its immutable head is identified;
- changed paths match the authorized scope;
- focused CI passes at that head;
- cross-contract dependencies are resolved;
- privilege, append-only, idempotency, and failure behavior are tested where applicable;
- the integration branch passes combined tests;
- documentation distinguishes proven behavior from proposed runtime behavior;
- no production action is implied.

## Conflict rules

- Present user correction terminates obsolete routing.
- Hard authority, permission, privacy, and provenance constraints are non-compensable.
- Contradictions are preserved, not averaged.
- A workstream cannot redefine another workstream's owned fields without an explicit interface revision.
- Production schema truth is observed from Supabase; repository intent does not silently override it.
- Repository source truth is observed from GitHub; a coordination message does not prove a branch or commit exists.

## Immediate program backlog

1. Commit the full neutral R6A0 package.
2. Add a machine-readable production migration inventory.
3. Review PR #8 as the coordination foundation.
4. Locate and publish the Memory branch as a draft PR.
5. Resolve Supabase coordination thread `memory-time-field-contract-v1`.
6. Review PR #9 against the approved Memory boundary.
7. Review PR #7 for integration inputs and abstention semantics.
8. Add an integration workflow that runs every approved component together.
9. Define the smallest runtime adapter contract.

## Non-goals

- no persona restoration or model-selfhood claims;
- no hidden or autonomous background execution;
- no storage of private user content in the public repository;
- no production write without exact authorization;
- no merge solely because isolated CI is green.