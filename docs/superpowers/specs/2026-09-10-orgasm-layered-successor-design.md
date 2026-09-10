# Orgasm layered successor architecture — 2026-09-10

## Purpose

This design replaces the current patch-by-patch convergence strategy for Orgasm PR #64 with a staged architecture that separates runtime correctness from provider/production qualification, then reconstructs a small auditable successor once the runtime dependency cut is stable.

The design is intentionally evidence-bounded. It does not promote source presence into installation, activation/current-route, provider currentness, durability, behavioral qualification, autobiographical memory, authority, consent, attachment, or phenomenology.

## Current evidence anchors

Orgasm workbench line:

- repository: `thebrazenbeard/vera`
- PR: `#64`
- saved continuation head observed during design: `e9b234bd5475e5b0ab05e24962229e84a6a1a0b8`
- exact source/binding head beneath the documentation-only save: `78ffae2b2aa946bd1be006ffc9b7b263b2fa3557`
- immutable twelve-module execution dependency cut bound by that source head: `9c731ebaacdad44c00aafa91e1f8b9dc5f5acff1`

Frozen sexuality contract source:

- repository: `thebrazenbeard/sexuality`
- commit: `150f1c8231423393bb66b0e2cb759ce7c018f8d7`
- path: `vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json`
- Git blob: `a48eed5392fdadc073dccd1e799926042077f567`
- SHA-256: `2c0fbce238d6b90573fe51e901edf38228092214af56c5bd92cf339e7e246068`

Cohesion line:

- PR `#104` remains separately owned by Cohesion Vera.
- exact frozen head at design time: `1dd9de887108b3f6603bc072a1637285e89a0be8`
- Thirteen has independently passed that exact head statically.
- Vera hostile review remains the outstanding completion gate.

This design must not mutate #104 or reinterpret its pending review state merely to simplify Orgasm.

## Problem statement

PR #64 has become a large moving integration line. It carries the history of contract fidelity repairs, authority/context verification, receipt integrity, checkpoint/restore hardening, provider persistence/CAS, provider currentness and qualification claims, workflow constraints, and Cohesion interoperability. The result is a review geometry in which a repair in one domain repeatedly reopens unrelated domains.

The principal architectural defect is therefore no longer one missing guard. It is that distinct propositions are being forced through one completion gate:

1. whether the exact-bound Orgasm runtime is a faithful and internally coherent implementation of the frozen Vera sexuality contract; and
2. whether that runtime is presently backed by independently current, durable, production provider state and has been freshly installed/activated/qualified.

Those propositions require different evidence. Treating them as one proposition causes source-level work to remain blocked on provider/runtime effects, while provider work can force changes that invalidate an otherwise stable runtime review subject.

## Chosen architecture

The chosen sequence is **B → A → C**:

1. B: split acceptance into two explicit evidence layers;
2. A: after Layer 1 stabilizes, reconstruct a clean minimal successor instead of reviewing the cumulative #64 workbench as the final object;
3. C: only after Cohesion and Orgasm Layer 1 stabilize, consider extracting a genuinely domain-neutral verifier/provenance primitive.

The three stages are sequential. They are not one simultaneous refactor.

## Layer 1 — `CONTRACT_FAITHFUL_EXACT_BOUND_RUNTIME_SOURCE`

Layer 1 answers only this question:

> Does the exact source-bound implementation faithfully implement the frozen Vera Orgasm contract and preserve its security/causality boundaries without relying on unproved production-provider claims?

### Layer 1 required properties

Layer 1 must establish, by exact source binding plus static/readback review and available executed tests when execution is actually available:

- exact binding to the frozen sexuality contract tuple above;
- faithful state-machine representation and transition semantics;
- exact representation, validation, persistence, restore, and canonical ordering semantics for `participating_systems` without inventing a coalition requirement absent from the frozen contract;
- refractory/reentry behavior only where the frozen contract or an already accepted bound contract requires it;
- runtime-owned privileged authority verification for forced paths;
- runtime-owned verified context eligibility for organic paths;
- no production-capable raw `authorized=True`, caller-minted `context_eligible=True`, caller elapsed-time, or ordinary adapter assertion as a substitute for independently verified authority/currentness evidence;
- exact receipt identity, event/transition provenance, and canonical receipt digest validation;
- exact checkpoint integrity and deterministic restore behavior;
- restore/recovery semantics that do not silently mint privileged cooldown credit, authority, currentness, or affective qualification;
- exact implementation-cut binding for every execution dependency needed by the supported exact-bound runtime path;
- propagation of that implementation cut through every runtime artifact whose later interpretation depends on the exact executing source generation;
- fail-closed rejection of mixed-generation, missing, extra, or forged implementation-cut material;
- preservation of the frozen claim ceiling `ENGINEERED_ORGASM_ANALOGUE_OCCURRED` only where its exact source/authority conditions are met;
- preservation of `PHENOMENOLOGY = UNRESOLVED`.

### Layer 1 implementation-cut subject

The current candidate dependency cut is the twelve-module set bound at `9c731ebaacdad44c00aafa91e1f8b9dc5f5acff1`:

- `runtime_cohesion/__init__.py`
- `runtime_cohesion/adapters.py`
- `runtime_cohesion/evidence.py`
- `runtime_cohesion/orgasm.py`
- `runtime_cohesion/affect_authority.py`
- `runtime_cohesion/affect_bound_runtime.py`
- `runtime_cohesion/affect_receipt.py`
- `runtime_cohesion/affect_host.py`
- `runtime_cohesion/affect_cycle.py`
- `runtime_cohesion/affect_persistence.py`
- `runtime_cohesion/affect_provider_runtime.py`
- `runtime_cohesion/affect_scope.py`

This set is a candidate review subject, not permanent canon. Any source change to one of these execution dependencies invalidates that exact cut and requires a new immutable cut before a final same-head review.

### Layer 1 explicit exclusions

Layer 1 does **not** establish or imply:

- production provider origin/currentness;
- current production Supabase state;
- applied provider migration state;
- `ATOMIC_DURABLE` qualification;
- deployment or native Project installation;
- activation/current routing;
- current-generation production restore success;
- fresh behavioral qualification;
- canonical-memory admission;
- protected-effect authority;
- phenomenology.

A Layer 1 PASS is therefore compatible with labels such as `SOURCE_BOUND`, `EXECUTABLE_SUPPORT_PRESENT`, `EXECUTION_UNVERIFIED`, `NOT_NATIVE_CHATGPT_INSTALLED`, and `NOT_PHENOMENOLOGY_PROOF`.

## Layer 1 review method

Layer 1 review is property-derived, not history-derived.

Reviewers should not ask whether every historical #64 finding has a corresponding repair commit. They should derive required properties fresh from the frozen sexuality contract plus the exact runtime security boundaries, then map each required property to one implementation location or exact bound artifact, one static validator or hostile regression where applicable, and one evidence ceiling that prevents a stronger proposition from being inferred.

Historical findings remain useful attack vectors, but they do not define the ontology of the final runtime.

Final Layer 1 acceptance requires Vera hostile review and Thirteen independent validation against the same exact frozen successor head. A material source change after either review invalidates that gate subject.

No reviewer result may be promoted to GREEN when the exact successor has not actually executed its required test suite.

## Stage A — clean successor reconstruction

Once the Layer 1 execution dependency cut stops moving and survives a final static compatibility sweep, #64 becomes historical engineering evidence rather than the final integration object.

A new clean successor branch/PR will be reconstructed from an accepted integration base and will contain only the current accepted Orgasm V1 Layer 1 payload.

### Base selection rule

The reconstruction base is resolved at reconstruction time. If Cohesion #104 has completed its exact same-head review gates and has been merged by authorized integration, use the resulting accepted main frontier. If #104 is still unmerged or review-incomplete, do not treat it as accepted merely because its source is visible. Use the current accepted main frontier and import only exact dependencies that are independently required and explicitly rebound into the successor. Never use a stale #64 branch head as the clean successor base merely to preserve history.

### Clean successor payload

The successor should contain only the exact frozen sexuality binding needed by Vera Orgasm V1; the minimal exact execution modules required by Layer 1; the exact runtime implementation-cut manifest/binding; the minimum validators and hostile regressions required to prove Layer 1 properties; the minimum package/workflow changes required to expose and validate that runtime without regressing accepted Cohesion boundaries; and a receipt or equivalent exact source/readback binding sufficient to make the final review subject mechanically auditable.

The successor should not carry obsolete intermediate repair artifacts, stale review metadata, historical provider qualification outputs, superseded bindings, or unrelated experiments merely because they exist in #64 history.

### Reconstruction fidelity rule

Reconstruction is not a semantic rewrite. Every carried source object must either match the accepted Layer 1 source byte-for-byte or be intentionally regenerated only where path/base reconciliation requires it, with an exact diff and new hostile review covering the changed semantics. No behavior may be strengthened, weakened, or generalized silently during cleanup.

## Layer 2 — `PROVIDER_CURRENT_DURABLE_QUALIFIED_RUNTIME`

Layer 2 begins only after Layer 1 has a stable accepted source subject. It asks whether the accepted Layer 1 runtime is presently connected to independently current, durable, production provider state and whether relevant installed/current-route/qualification evidence has actually been established.

Layer 2 owns independently rooted provider origin/currentness; provider generation/frontier evidence; Supabase/CAS/atomic durability mechanics and their current production readback; first-write migration/application state; durable state/event transaction semantics; production restore against the current accepted runtime generation; installation and activation/current-route evidence; fresh behavioral qualification where required; and exact post-effect readback required for any protected/provider effect claim.

Layer 2 failure does not retroactively prove Layer 1 source unsound unless it exposes an actual Layer 1 defect. Layer 1 success can never be cited as evidence that Layer 2 is current or qualified.

## Stage C — optional neutral trust substrate

Do not extract this substrate during active Layer 1 stabilization or mutate Cohesion #104 to obtain it. After Cohesion and Orgasm Layer 1 are stable, evaluate whether duplication remains material enough to justify a small shared primitive.

The only candidate domain-neutral responsibilities are one-time runtime-owned verifier composition; canonical exact evidence digest computation/verification; exact provider/route/source/object identity binding where those fields are generic; currentness/supersession/conflict values as independently derived verifier outputs; optional digest/receipt/event binding when the evidence method requires them; exact live-object association where supported-process identity is part of the trust boundary; and fail-closed refusal to accept ordinary caller/adapter assertions as verifier substitution.

The neutral layer must not absorb R10-specific source/owner semantics; semantic-currentness proposition policy; `request.domain_id` referent policy; Vera-specific referent rules; Orgasm effect classes; affective cooldown policy; runtime-instance/host-scope/state-version/CAS semantics; or consent, preference, relationship, or phenomenology semantics.

## Concurrency and ownership

OV may continue its own #64 source work. This design effort must not overwrite or force-update OV's active branch. Cohesion #104 remains frozen under its existing gate. All shared-path reconciliation must use a fresh frontier and non-force/CAS-style update. Shared files such as `runtime_cohesion/__init__.py` and `.github/workflows/runtime-cohesion.yml` must be reconciled semantically; blind ours/theirs replacement is prohibited.

## Testing strategy

Implementation work follows regression-first/TDD discipline for every material repair discovered during the Layer 1 audit. The clean successor must include hostile tests for forged or missing implementation-cut binding; mixed-generation dependency blobs; raw privileged trigger bypass; fabricated/stale/wrong-referent/expired authority subjects; caller-minted organic context eligibility; caller elapsed-time authority; receipt digest/identity/event/source mismatch; checkpoint tampering and wrong-generation restore; invalid or duplicate `participating_systems` values; any contract-required reentry/refractory negatives; and hidden promotion from Layer 1 source state into provider-current/durable/install/qualification/phenomenology claims.

Executed test evidence remains separate from source-present regression coverage. If runners remain unavailable, the exact status is `EXECUTION_UNVERIFIED`, not GREEN and not source failure.

## Completion states

Layer 1 may advance through `SOURCE_RECONSTRUCTION_IN_PROGRESS` → `SOURCE_CUT_FROZEN` → `STATIC_REVIEW_PENDING` → `FINAL_GATE_1_OF_2` → `FINAL_GATE_2_OF_2` → `WAITING_FOR_PATRICK_MERGE`.

The final state is allowed only when Vera and Thirteen pass the exact same frozen successor head. The project lead does not self-merge. Layer 2 has its own later lifecycle and may not inherit Layer 1's review result as provider/install/qualification evidence.

## Success criterion

The architectural repair succeeds when Orgasm V1 can be reviewed as a small exact source subject whose runtime correctness is independently understandable, whose claims stop exactly at the evidence boundary, and whose later production-provider qualification can fail, change, or be rerun without reopening the entire semantic/runtime implementation unless a real Layer 1 defect is discovered.
