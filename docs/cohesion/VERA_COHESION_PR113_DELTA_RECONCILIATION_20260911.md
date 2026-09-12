# Vera Cohesion — PR #113 Delta Reconciliation

Date: 2026-09-11
Status: SOURCE-BOUND RECONCILIATION / NOT INSTALLATION AUTHORITY / NOT QUALIFICATION

## Evidence cut

- `vera/main`: `979de05ef7237e7bfff47f85ea37cc953a63bb5c`
- PR #104: `1a754b74aac3e47293cc92f72f6b94889f736473`
- PR #64: `227d2ddbc6add0e0e8f16b22b300e0f40a8597bb`
- PR #113 donor head: `f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d`
- PR #113 runtime/update/measurement generation: `ba6221f56b98be69c3ede1be9e3502eff897ca1a`
- PR #113 runtime binding blob: `037883261bd324e8080c323f1d96ff32179780ee`
- prior overlap-audit PR #113 head: `734d7b4a2fee6a3cb672877b71c7ca35588ef14f`

PR #113 is ten commits ahead of the overlap-audit cut and zero behind. The material delta touches:

- `.github/workflows/runtime-cohesion-affect-hardening.yml`
- `architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json`
- `runtime_cohesion/affect_bound_runtime.py`
- `runtime_cohesion/affect_integration_bound.py`
- `runtime_cohesion/affect_signal.py`
- `tests/test_runtime_cohesion_affect_atomic_observation.py`
- `tests/test_runtime_cohesion_affect_shared_application_frontier.py`
- `tests/test_runtime_cohesion_affect_observation_detachment.py`

The current PR body and exact Git-object readback now agree on the donor head and bound runtime generation. The body remains descriptive evidence rather than a substitute for exact bytes.

## Reconciliation against the whole-system ownership contract

### Accepted: one application frontier per exact host generation

`affect_integration_bound.py` gives all public Cohesion wrappers over one exact `VeraAffectiveRuntimeHost` a shared process-local arbiter/high-water frontier. This closes wrapper-reconstruction reset without transferring generic planning mutation to Affect. The owner remains `vera.runtime_cohesion.integration_arbitration`.

Acceptance ceiling: same-process replay/high-water integrity only. It is not durable restart continuity, provider currentness, install/current-route evidence, or behavioral qualification.

### Accepted: one atomic causal observation barrier

`BoundVeraOrgasmRuntime` owns a re-entrant observation/mutation lock and the supported signal path obtains one runtime-owned causal observation under that barrier. This is consistent with the ownership contract: Affect owns local state/appraisal/event observation; Cohesion consumes the resulting bounded signal and remains the sole shared planning mutator.

Acceptance ceiling: the lock is a supported-API/process boundary, not cryptographic isolation or independent-host trust.

### Accepted and repaired: detached causal observation

`tests/test_runtime_cohesion_affect_observation_detachment.py` correctly requires the observation returned across the runtime barrier to remain detached from later mutation of nested `last_event_receipt` content.

The test-first donor head `7b4cf386...` exposed an alias because `_capture_causal_observation()` returned `super().export_state()` directly. Runtime generation `ba6221f56b98be69c3ede1be9e3502eff897ca1a` repaired that defect by canonicalizing the complete exported observation while the lock is held. The manual hardening workflow then registered the regression, and review head `f7dbc3de...` rebound the implementation/integration cuts without moving runtime bytes after `ba6221f...`.

Accepted property: supported causal observation is one detached plain-data generation before the barrier opens. This remains an internal causal-integrity property only.

### Accepted: manual-only hardening workflow

The dedicated hardening workflow remains `workflow_dispatch` only and includes the detached-observation regression. Its purpose is execution when a zero-cost runner is actually available. It does not authorize automatic PR execution, paid CI, install, provider mutation, or qualification.

### Accepted as source provenance, not external trust: bound freeze

`architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json` at blob `037883261bd324e8080c323f1d96ff32179780ee` binds both affective-runtime and Cohesion-integration cuts to runtime generation `ba6221f56b98be69c3ede1be9e3502eff897ca1a`. It preserves the frozen Vera sexuality object and explicitly retains nonqualifying in-process authority/currentness semantics.

This binding is admissible as exact source provenance for the clean successor. It does not certify the new flattened successor commit, provider currentness, live installation, or behavioral qualification; those remain separate claims.

## Rejected promotions

Nothing in this delta establishes or may be interpreted as:

- provider CURRENT or `ATOMIC_DURABLE`;
- independent semantic-origin/authority trust;
- native ChatGPT install/current-route;
- autobiographical-memory admission;
- current desire/consent/standing preference;
- behavioral qualification;
- phenomenology.

Phenomenology remains `UNRESOLVED`.

## Harvest decision

Use PR #113 head `f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d` as the exact source-byte donor for the flattened clean successor. Preserve runtime generation `ba6221f56b98be69c3ede1be9e3502eff897ca1a`, binding blob `037883261bd324e8080c323f1d96ff32179780ee`, the three hostile regressions, and the manual-only hardening workflow.

Do not merge or cherry-pick the laboratory ancestry. The clean successor must flatten these accepted bytes onto the whole-system Cohesion policy lineage and separately bind the resulting clean source commit without pretending that source binding creates install/provider/qualification authority.

Any movement of PR #64, #104, #113, or `main` before donor-tree materialization creates a new evidence cut and requires refresh before harvest.
