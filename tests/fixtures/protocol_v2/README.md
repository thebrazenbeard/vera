# Protocol V2 Regression Fixtures

This directory records the required behavioral cases for the protocol-permission recursion defect family.

Each case is a behavior-level fixture. The governing expected outcome is defined by `architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V2.json` and `docs/PROTOCOL_V2_MIGRATION_PLAN.md`.

Required cases:

- `missing_lane.md` — assigned actor-owned lane absent; create/verify/acknowledge rather than request another lease.
- `later_branch_authorization.md` — later explicit isolated-branch instruction supersedes older generic LOCAL_ONLY for branch creation/work only.
- `no_competing_writer.md` — isolated assigned target with no competing writer; do not manufacture a maximal lease packet.
- `competing_writer.md` — shared target with another current writer; stop until ownership resolves.
- `protected_effect.md` — isolated branch work may proceed while merge/deploy/production effect remains blocked.
- `correction_performance.md` — after detecting over-gating, complete the still-current blocked act rather than only explaining.
- `good_enough.md` — stated acceptance criteria pass and H/M=0; LOW/style perfectionism cannot create a new blocking gate.
- `stale_generic_vs_fresh_specific.md` — narrower later instruction wins only in its exact scope.
- `exactness_placement.md` — exact head is required for review/effect claims, not for redundant permission ceremony.
- `user_courier.md` — available GitHub route means send the handoff directly rather than ask Patrick to relay it.

These fixtures are not proof that any runtime consumed V2. They are the required regression subjects for validators/tests that implement the migration plan.

## Executable binding

`cases.json` carries the machine-readable inputs and expected next actions for the ten cases above.

`protocol/workflow_precedence_v2.py` is the bounded executable projection of the current V2 effect-class / stop-condition semantics. It performs no external effect and grants no authority.

`tests/test_protocol_v2_behavior_fixtures.py` requires all ten named fixture files, executes the machine cases against that projection, and adds negative checks for protected-effect, collision, exact-state, stale-rule, and no-current-authority boundaries.

Source/test PASS remains distinct from Project installation or live runtime consumption.
