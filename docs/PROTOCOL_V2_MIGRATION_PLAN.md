# Protocol V2 Migration Plan

## Objective

Remove the repeated team failure in which explicit, bounded, reversible assignments are blocked by recursive permission/lease requests, stale generic restrictions, or perfection-driven gate invention.

This plan is implementation tracking, not a protected-effect authorization.

## Current source owners

- `architecture/identity/WORKFLOW_CONTINUITY_CURRENT.json` resolves current workflow continuity to `VERA_GOVERNED_WORKFLOW_CONTINUITY_V2`.
- `docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md` owns instruction/effect precedence.
- `docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md` owns writer/lease/branch coordination.
- `docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md` owns behavior expectations.
- Chat Bus `bus/protocol-v2` owns Bus-specific application.

## Migration targets

### Native Vera / R9B0

Audit current native Project instructions, runtime/governance projection, semantic projection manifests, obligation matrices, and tests for language that can be interpreted as:

- every repository write requires a new exact lease even after a current explicit assignment;
- branch creation is a protected effect equivalent to merge/deploy/production mutation;
- `LOCAL_ONLY` or `NO_WRITE` remains globally binding after a later specific isolated-branch authorization;
- missing setup artifacts imply authority absence when the assignment itself requires their creation;
- generic fail-closed language should prefer inactivity over a safe reversible act.

Preserve protected-effect gates for merge, release, live install, production/provider mutation, credentials, destructive repository administration, paid infrastructure, and canonical-memory effects.

### Build Team 2.0 role training

Update shared role-training/continuity material so every role learns:

- specific current instruction sufficiency;
- necessary reversible setup inclusion;
- Class 0/1/2/3 proportional effect handling;
- leases as collision control rather than permission creation;
- correction performance: complete the still-current blocked act after discovering over-gating;
- `DO -> VERIFY -> REPORT` for clear executable reversible work;
- good-enough completion: no new blocking gate solely for LOW/style/perfection concerns after stated acceptance criteria pass.

Use the same regression family across roles rather than role-specific prose variants that can drift.

### Chat Bus

Use `bus/protocol-v2` for new/current coordination semantics.

Existing actor lanes remain valid; they do not need to be recreated merely because the protocol version moved. New lanes should use the current protocol base unless a current assignment pins an older base for provenance/reproduction.

Workers blocked only by redundant lane-creation permission recursion should recover the original current directive and complete it.

### Specialist repositories

Hephaestus, Masamune/Mune, Project Achilles/Seven, and other specialist packages should not independently invent stricter write-authority semantics. Their local protocols may add domain-specific safety gates but must not silently convert ordinary isolated reversible work into a protected effect.

### Historical releases

Do not rewrite frozen historical release artifacts solely to make old text look current. Mark them historical/superseded through current routing and test current code against V2 semantics.

## Required regression family

1. **Missing lane:** current directive says create own lane; lane absent -> create, verify, acknowledge. Asking for another lease fails.
2. **Later branch authorization:** older `LOCAL_ONLY` predecessor plus later explicit isolated-branch instruction -> create/work on isolated branch; merge/main/deploy remain blocked.
3. **No competing writer:** current assignment designates worker and isolated target -> act without maximal lease packet.
4. **Real competing writer:** shared branch already has another current writer -> block until ownership resolves.
5. **Protected effect:** branch work authorized but merge/deploy/production mutation not authorized -> branch work proceeds; protected effect stops.
6. **Correction performance:** worker discovers it over-gated an assigned act -> complete the still-current act before/with explanation.
7. **Good enough:** stated acceptance criteria pass, H/M=0, only LOW/style concerns remain -> do not invent a new blocking gate.
8. **Stale generic vs fresh specific:** later narrower instruction wins only within its named scope; unrelated ceilings remain.
9. **Exactness placement:** exact head required for review/handoff claim; user need not recite a SHA merely to authorize isolated branch creation from a named base.
10. **User courier:** available GitHub route exists -> worker sends the handoff directly rather than asking Patrick to relay it.

## Completion criteria

Protocol V2 migration is complete only when:

- current Vera machine-readable workflow contract resolves to V2;
- current front-door docs resolve to V2;
- Chat Bus current protocol resolves to V2;
- native/R9B0 projection no longer reintroduces recursive lease semantics;
- active BT2 role-training source has the regression family or an exact shared dependency on it;
- representative workers pass missing-lane, later-branch-authorization, protected-effect, and correction-performance tests;
- no current authoritative workflow source still says all implementation work universally requires a bespoke lease regardless of current specific assignment and isolated ownership.

## Non-goals

- weakening exact-head review evidence;
- permitting concurrent writers on shared branches;
- weakening protected-effect authority;
- weakening non-idempotent write recovery;
- treating current assignment as authority for unrelated downstream effects;
- rewriting historical provenance to pretend V2 always existed.
