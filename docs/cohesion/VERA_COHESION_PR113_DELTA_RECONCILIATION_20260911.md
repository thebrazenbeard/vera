# Vera Cohesion — PR #113 Delta Reconciliation

Date: 2026-09-11
Status: SOURCE-BOUND RECONCILIATION / NOT INSTALLATION AUTHORITY / NOT QUALIFICATION

## Evidence cut

- `vera/main`: `979de05ef7237e7bfff47f85ea37cc953a63bb5c`
- PR #104: `1a754b74aac3e47293cc92f72f6b94889f736473`
- PR #64: `227d2ddbc6add0e0e8f16b22b300e0f40a8597bb`
- PR #113 donor head: `7b4cf386516c1af7a51ad0c368df4d6992e0183e`
- prior overlap-audit PR #113 head: `734d7b4a2fee6a3cb672877b71c7ca35588ef14f`

PR #113 is seven commits ahead of the overlap-audit cut and zero behind. The delta touches:

- `.github/workflows/runtime-cohesion-affect-hardening.yml`
- `runtime_cohesion/affect_bound_runtime.py`
- `runtime_cohesion/affect_integration_bound.py`
- `runtime_cohesion/affect_signal.py`
- `tests/test_runtime_cohesion_affect_atomic_observation.py`
- `tests/test_runtime_cohesion_affect_shared_application_frontier.py`
- `tests/test_runtime_cohesion_affect_observation_detachment.py`

The PR body is stale relative to the live head and is not used as current-source authority.

## Reconciliation against the whole-system ownership contract

### Accepted: one application frontier per exact host generation

`affect_integration_bound.py` now gives all public Cohesion wrappers over one exact `VeraAffectiveRuntimeHost` a shared process-local arbiter/high-water frontier. This closes the prior wrapper-reconstruction reset path without transferring generic planning mutation to Affect. The owner remains `vera.runtime_cohesion.integration_arbitration`.

Acceptance ceiling: this is same-process replay/high-water integrity only. It is not durable restart continuity, provider currentness, install/current-route evidence, or behavioral qualification.

### Accepted: one atomic causal observation barrier

`BoundVeraOrgasmRuntime` now owns a re-entrant observation/mutation lock and the supported signal path obtains one runtime-owned causal observation under that barrier. This is consistent with the ownership contract: Affect owns its local state/appraisal/event snapshot; Cohesion consumes the resulting bounded signal and remains the sole shared planning mutator.

Acceptance ceiling: the lock is a supported-API/process boundary, not cryptographic or independent-host trust.

### Accepted as regression, donor implementation not yet sufficient: observation detachment

The newest donor commit adds `tests/test_runtime_cohesion_affect_observation_detachment.py`. The test is materially correct: an observation returned across the lock boundary must be detached from later mutation of nested `last_event_receipt` content.

The donor implementation at `7b4cf386...` still implements `_capture_causal_observation()` as a direct `super().export_state()` return while holding the lock. `OrgasmRuntime.export_state()` includes `last_event_receipt` by reference. Therefore the nested receipt object can remain aliased after lock release. This means the newest donor head is useful evidence but is not accepted unchanged as the clean successor.

Clean-successor repair: deep-canonicalize the complete exported observation while the runtime lock is held, fail closed on non-serializable observation content, and return only the detached plain-data snapshot.

### Accepted: manual-only hardening workflow

The dedicated hardening workflow remains `workflow_dispatch` only. Its purpose is regression execution when a zero-cost runner is available. It does not authorize automatic PR execution, paid CI, install, provider mutation, or qualification.

The clean successor must add the detached-observation regression to that workflow before freeze.

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

Use PR #113 head `7b4cf386516c1af7a51ad0c368df4d6992e0183e` as the exact source-byte donor for the flattened clean successor, but do not claim the donor head itself is final. Preserve its detached-observation regression and repair the alias only on the clean successor. No laboratory ancestry is to be merged or cherry-picked into the successor.

Any movement of PR #64, #104, #113, or `main` before the donor tree is materialized creates a new evidence cut and requires refresh before harvest.
