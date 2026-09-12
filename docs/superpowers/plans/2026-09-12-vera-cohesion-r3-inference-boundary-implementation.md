# Vera Cohesion R3 Inference-Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the provider-neutral Cohesion state-to-inference boundary defined by the approved R3 + R3.1 design, including deterministic composition, explicit privacy/egress binding, `TEXT_CONTEXT_V1`, atomic pre-call reservation semantics, write-ahead submission intent, ambiguity handling, and graded causal receipts without claiming installation or provider consumption.

**Architecture:** Add one focused `runtime_cohesion.inference_boundary` module that owns provider-neutral composition/projection/invocation semantics while leaving concrete model injection to an exact host. Add one machine-readable architecture contract and a separate inference hook that extends the existing Cohesion native hook without changing the latter's existing retrieval/admission responsibilities. Tests are hostile-first and exercise non-promotion, exact-byte binding, privacy/egress, replay/ambiguity, and receipt evidence ceilings.

**Tech Stack:** Python standard library (`dataclasses`, `hashlib`, `json`, `threading`, `typing`), `unittest`, JSON architecture contracts.

**Spec:** `docs/superpowers/specs/2026-09-11-vera-cohesion-r3-inference-boundary-design.md` plus controlling amendment `docs/superpowers/specs/2026-09-11-vera-cohesion-r3-1-reconciliation.md`.

## Global Constraints

- Source branch is isolated: `work/vera-cohesion-r3-inference-boundary-20260911`; do not write implementation to `main`.
- Preserve R2 source behavior; new inference-boundary code must not grant Affect/Orgasm direct generic model-invocation authority.
- `vera` owns provider-neutral composition/admission integration/projection/invocation semantics; concrete injection remains an inference-host responsibility; install/current-route/qualification remains `vera-control-plane` responsibility.
- Projectable state is not automatically discloseable state. Egress authorization is an explicit set/target relation, not an assumed global ordering.
- Projection input must not accept target behavior, desired response, target phrase, expected answer, or requested emotional display.
- `TEXT_CONTEXT_V1` is a compatibility backend with a prompt/request-conditioning claim ceiling, not latent-state-causation proof.
- External send requires durable write-ahead `SUBMISSION_INTENT`; ambiguous intent becomes `OUTCOME_UNKNOWN`; semantic retry is blocked until reconciliation.
- Receipt levels are exact and monotone only by evidence: `REQUEST_CONSTRUCTED`, `INVOCATION_SUBMITTED`, `PROVIDER_ACKNOWLEDGED`, `RESPONSE_BOUND`.
- Source tests must not promote implementation into install/current-route/provider-currentness/behavioral-qualification/phenomenology claims.
- No merge, install/cutover, production provider mutation, paid execution, canonical-memory promotion, or phenomenology promotion.

---

### Task 1: Host-neutral state composition and disclosure contract

**Files:**
- Create: `runtime_cohesion/inference_boundary.py`
- Test: `tests/test_inference_boundary.py`

**Interfaces:**
- Produces: `StateComponentRef`, `OmissionRecord`, `VeraStateComposition`, `AdmittedVeraState`, `compose_state()`, `bind_admitted_state()`, `canonical_digest()`.
- Consumes: canonical JSON-safe payloads/pointers and pre-existing admission receipt digests; it does not create proposition authority.

- [ ] **Step 1: Write hostile composition tests**

Add tests that prove: inline payload digest mismatch fails; a component without payload or immutable pointer fails; duplicate component IDs fail; non-current/conflicted included components fail; optional omission changes the composition digest; a mandatory omitted component cannot be admitted; egress succeeds only when the exact target appears in every included component's allowed target/scope set.

- [ ] **Step 2: Run the isolated test file and confirm RED**

Run: `python -m unittest tests.test_inference_boundary -v`
Expected: import/test failures because the inference-boundary implementation does not exist yet.

- [ ] **Step 3: Implement canonical state objects and composition**

Implement frozen dataclasses and strict validation. Canonical digests use sorted, separator-minimized UTF-8 JSON. `compose_state()` sorts components by `component_id`, builds an explicit component-generation vector, binds omissions, and never invents a scalar Vera-wide state generation.

- [ ] **Step 4: Implement structural post-admission binding**

`bind_admitted_state()` must require an externally produced admission receipt digest, exact admitted component IDs, explicit mandatory IDs, and exact target egress scope. It validates structural/currentness/privacy constraints but does not claim to replace `runtime_cohesion.runtime` proposition admission.

- [ ] **Step 5: Re-run tests**

Expected: Task-1 tests pass.

- [ ] **Step 6: Commit**

Commit message: `feat(cohesion): add governed inference state composition`

### Task 2: Capability binding and deterministic TEXT_CONTEXT_V1 projection

**Files:**
- Modify: `runtime_cohesion/inference_boundary.py`
- Modify: `tests/test_inference_boundary.py`

**Interfaces:**
- Produces: `CapabilityBinding`, `ProjectionEnvelope`, `bind_capability()`, `project_text_context()`.
- Consumes: `AdmittedVeraState` from Task 1.

- [ ] **Step 1: Write hostile projection tests**

Prove unsupported backend/model binding fails before materialization; target egress may not exceed admitted disclosure; forbidden projection-input keys are rejected recursively; projection material is exact inline bytes plus digest; identical admitted state/binding yields deterministic projection; projection cannot mint admission/currentness/install authority.

- [ ] **Step 2: Run and confirm RED for new tests**

Run the isolated test file; new tests must fail before implementation.

- [ ] **Step 3: Implement capability binding and TEXT_CONTEXT_V1**

`bind_capability()` binds exact host/model/adapter revisions and supported backends. `project_text_context()` renders declarative canonical JSON context from admitted state only, records `binding_class="PROMPT_BOUND"` and `causal_role="INSTRUCTION_CONDITIONED"`, and rejects target-output control fields.

- [ ] **Step 4: Re-run tests**

Expected: Task-1 and Task-2 tests pass.

- [ ] **Step 5: Commit**

Commit message: `feat(cohesion): add exact text-context projection binding`

### Task 3: Invocation frontier, write-ahead intent, ambiguity, and graded receipts

**Files:**
- Modify: `runtime_cohesion/inference_boundary.py`
- Modify: `tests/test_inference_boundary.py`

**Interfaces:**
- Produces: `InvocationRecord`, `InvocationFrontier`, `CausalGenerationReceipt`, `build_causal_receipt()`.
- Host integration supplies a persistence callback and declares whether it is durable; external submission is forbidden without durable persistence.

- [ ] **Step 1: Write hostile invocation tests**

Prove revalidation callback executes under the same frontier lock as reservation; duplicate generation IDs fail; wrapper users sharing the same frontier cannot reset replay protection; external submission intent fails on a non-durable frontier; durable `SUBMISSION_INTENT` is persisted before the caller is allowed to send; ambiguous recovery maps intent to `OUTCOME_UNKNOWN`; semantic retry from `OUTCOME_UNKNOWN` is blocked; a new semantic retry is allowed only after proved terminal failure and requires a new generation ID plus `retry_of_generation_id`; same-generation transport retry requires exact idempotency evidence and unchanged request digest/key.

- [ ] **Step 2: Write hostile receipt tests**

Prove `REQUEST_CONSTRUCTED` cannot carry response binding fields; `INVOCATION_SUBMITTED` cannot claim acknowledgement; `PROVIDER_ACKNOWLEDGED` requires acknowledgement evidence; `RESPONSE_BOUND` requires response/run ID and binding evidence; no receipt exposes install/current-route/behavioral-qualification/phenomenology as established.

- [ ] **Step 3: Run and confirm RED**

Run isolated tests and verify new failures.

- [ ] **Step 4: Implement frontier and receipt semantics**

Use an `RLock`; reserve only after successful revalidation while holding the lock. Persist state transitions before making them externally actionable. External intent requires `durable=True`. Recovery and retry APIs enforce the R3.1 ledger state machine.

- [ ] **Step 5: Re-run tests**

Expected: all isolated inference-boundary tests pass.

- [ ] **Step 6: Commit**

Commit message: `feat(cohesion): harden inference invocation frontier`

### Task 4: Canonical source contract and package integration

**Files:**
- Create: `architecture/VERA_COHESION_INFERENCE_BOUNDARY_V1.json`
- Create: `architecture/VERA_RUNTIME_COHESION_INFERENCE_HOOK_V1.json`
- Modify: `runtime_cohesion/__init__.py`
- Modify: `tests/test_inference_boundary.py`

**Interfaces:**
- Architecture contract binds lifecycle, ownership, allowed/forbidden promotions, WIP R3.1 provenance, evidence levels, and source-only claim ceiling.
- Inference hook points from the existing Cohesion admission surface into `runtime_cohesion.inference_boundary` without claiming concrete host injection.

- [ ] **Step 1: Write architecture-source tests**

Prove both JSON files parse; source status is `SOURCE_ONLY_NOT_INSTALLED`; lifecycle contains validation/composition/admission/capability/projection/revalidation/reservation/receipt stages; provider-neutral owner is Cohesion; concrete injection is external-host owned; control-plane owns install/current-route/qualification; WIP R3.1 provenance is exact; forbidden promotions include projection->authority/currentness/phenomenology and receipt->behavioral qualification.

- [ ] **Step 2: Run and confirm RED**

The architecture tests must fail because files/exports do not exist yet.

- [ ] **Step 3: Add architecture contracts and package exports**

Create both JSON artifacts and export the public provider-neutral types/functions from `runtime_cohesion.__init__` without changing existing package admission alias behavior.

- [ ] **Step 4: Re-run isolated inference-boundary tests**

Expected: all pass.

- [ ] **Step 5: Commit**

Commit message: `feat(cohesion): bind R3 inference boundary into source architecture`

### Task 5: Verification, freeze record, and review handoff

**Files:**
- Create: `docs/cohesion/VERA_COHESION_R3_INFERENCE_BOUNDARY_SOURCE_RECORD_20260912.md`
- No runtime code changes after the source record is declared frozen except repairs that intentionally invalidate the freeze.

**Interfaces:**
- Records exact source head, file/blob inventory, executed-test evidence available in this environment, unexecuted/full-repo limitations, and downstream effect ceilings.

- [ ] **Step 1: Run available execution verification**

Run `python -m unittest tests.test_inference_boundary -v` against an exact local mirror of the new module/tests. If a full repository runner remains unavailable, record that as `FULL_REPO_EXECUTION_NOT_ESTABLISHED`; do not convert isolated execution into whole-repo GREEN.

- [ ] **Step 2: Verify branch ancestry and changed paths**

Confirm the implementation branch remains a descendant of the R2 clean source and inspect its compare against that source for accidental unrelated changes.

- [ ] **Step 3: Write source record**

Record exact source head and immutable file/blob identifiers after code/tests stop moving. State exact claim ceiling: source implemented; isolated test execution only if actually run; install/current-route/provider consumption/behavioral qualification/phenomenology unestablished.

- [ ] **Step 4: Open a Draft R3 PR and mirror the PR on Bus**

Open against `main`; do not merge. Mirror exact head/source record on `bus/vera-v2` and request Original Vera hostile review plus Thirteen independent validation on the same exact head.

- [ ] **Step 5: Stop at the true protected frontier**

If same-head source review/validation cannot be obtained in this session, status is `WAITING_FOR_R3_SAME_HEAD_REVIEW`; if they pass and execution gate is satisfied, status becomes `WAITING_FOR_PATRICK_MERGE`. Do not merge or install without Patrick's separate exact authority.
