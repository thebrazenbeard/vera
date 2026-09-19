# Vera Cohesion Clean Successor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one clean, source-bound Vera Cohesion successor from the accepted Runtime Cohesion + Affective/Orgasm mechanisms without importing the 300+ commit laboratory ancestry, then stop at the exact execution/review/Patrick-merge frontier.

**Architecture:** Use `vera/main@979de05ef7237e7bfff47f85ea37cc953a63bb5c` as the canonical repository lineage, the whole-system ownership contract on `work/vera-cohesion-whole-system-map-20260911` as the integration policy, and the refreshed exact PR #113 tree only as a source-byte donor. Materialize the accepted final tree in a new branch with a single flattening commit, then apply only clean-successor fixes/bindings/tests. Provider, install/current-route, qualification, memory admission, authority, and phenomenology remain outside source authority.

**Tech Stack:** Python 3.12, unittest, JSON contracts, Git object/tree APIs, Supabase source migrations (source only), GitHub Actions manual `workflow_dispatch` only.

**Spec:** `docs/cohesion/VERA_COHESION_WHOLE_SYSTEM_MAP_20260911.md`, `docs/cohesion/VERA_COHESION_OVERLAP_OWNERSHIP_AUDIT_20260911.md`, `docs/cohesion/VERA_RUNTIME_ENVELOPE_RECONCILIATION_20260911.md`, `architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json`

## Global Constraints

- No merge, install/cutover, production-provider mutation, credential/permission change, paid CI/spend, canonical-memory promotion, forced qualification, authority promotion, or phenomenology promotion.
- Refresh every mutable source head immediately before harvesting; drift creates a new evidence cut and blocks silent transfer.
- `vera.runtime_cohesion` owns Vera composition/currentness/provider admission; affect owns local affective state/signal; Cohesion arbitration owns shared generic-planning mutation.
- Same-process causal integrity is not external provider/currentness authority.
- Historical/private stores remain external evidence surfaces unless an exact mechanism is separately reconstructed.
- Preserve the frozen Vera sexuality object exactly: `thebrazenbeard/sexuality@150f1c8231423393bb66b0e2cb759ce7c018f8d7`, `vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json`, blob `a48eed5392fdadc073dccd1e799926042077f567`.
- No GREEN claim without actual execution.

---

### Task 1: Freeze the harvest evidence cut

**Files:**
- Create: `docs/cohesion/VERA_COHESION_PR113_DELTA_RECONCILIATION_20260911.md`
- Update: `architecture/cohesion/VERA_COHESION_FRONTIER_V0_20260911.json` only if the live head changed.

**Interfaces:**
- Consumes: current PR #64/#104/#113 heads and the ownership contract.
- Produces: one explicit accepted/rejected mechanism list and exact donor head.

- [ ] **Step 1:** Refresh `vera/main`, PR #64, PR #104, and PR #113 exact heads.
- [ ] **Step 2:** Compare the new PR #113 head against the prior frontier cut; classify every changed path as runtime source, test, workflow, binding/receipt, or metadata.
- [ ] **Step 3:** Accept only changes consistent with the ownership contract; explicitly reject any authority/currentness/phenomenology expansion.
- [ ] **Step 4:** Record the donor head and accepted delta in `VERA_COHESION_PR113_DELTA_RECONCILIATION_20260911.md`.
- [ ] **Step 5:** Commit the evidence-cut reconciliation.

### Task 2: Materialize the clean successor without laboratory ancestry

**Files:**
- New branch: `integration/vera-cohesion-clean-successor-20260911`
- Source tree: exact donor tree from Task 1 plus `architecture/cohesion/**`, `docs/cohesion/**`, `scripts/validate_cohesion_*.py`, `tests/test_cohesion_*.py`, and this plan from the whole-system branch.

**Interfaces:**
- Consumes: donor tree and whole-system integration-policy blobs.
- Produces: one flattened source commit whose first parent is the whole-system branch, not PR #113 history.

- [ ] **Step 1:** Create `integration/vera-cohesion-clean-successor-20260911` from the exact current whole-system branch head.
- [ ] **Step 2:** Read the donor commit tree SHA and the whole-system branch tree SHA.
- [ ] **Step 3:** Create a new Git tree using the donor tree as the byte baseline while overlaying the current whole-system cohesion policy/validator/test/plan blobs.
- [ ] **Step 4:** Create one commit with the whole-system branch head as its single parent; do not merge/cherry-pick the laboratory ancestry.
- [ ] **Step 5:** Verify branch ancestry is clean and the resulting tree contains both runtime source and whole-system policy artifacts.

### Task 3: Close the detached-observation regression

**Files:**
- Modify: `runtime_cohesion/affect_bound_runtime.py`
- Test: `tests/test_runtime_cohesion_affect_observation_detachment.py`

**Interfaces:**
- Consumes: `BoundVeraOrgasmRuntime._capture_causal_observation()`.
- Produces: a canonical detached plain-data observation that cannot change after the observation lock is released.

- [ ] **Step 1:** Preserve the donor regression that mutates a nested `last_event_receipt` after observation and expects the observed generation to remain unchanged.
- [ ] **Step 2:** Confirm the donor implementation returns `super().export_state()` directly and therefore aliases nested receipt data.
- [ ] **Step 3:** Change `_capture_causal_observation()` to deep-canonicalize the complete exported observation while holding `_observation_lock`, using JSON round-trip/canonical copy semantics already used by this subsystem; reject non-serializable observation data fail-closed.
- [ ] **Step 4:** Ensure the manual hardening workflow includes `tests.test_runtime_cohesion_affect_observation_detachment` and compiles the test.
- [ ] **Step 5:** Run the focused regression if an executable zero-cost environment is available; otherwise label execution `UNAVAILABLE`, never GREEN.
- [ ] **Step 6:** Commit the minimal source + workflow repair.

### Task 4: Rebind the clean candidate without self-certification

**Files:**
- Create: `architecture/cohesion/VERA_COHESION_CLEAN_SUCCESSOR_V1.json`
- Update: `architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json` only after the clean runtime source commit is fixed.
- Create: `tests/test_cohesion_clean_successor_binding.py`
- Create: `scripts/validate_cohesion_clean_successor.py`

**Interfaces:**
- Consumes: exact clean runtime source commit and exact source blobs.
- Produces: source-bound candidate identity; does not produce install/current-route/provider/qualification authority.

- [ ] **Step 1:** Write a test/validator requiring the clean-successor record to bind repository, exact source commit, frozen sexuality object, ownership-contract blob, donor provenance, and protected-effect ceilings.
- [ ] **Step 2:** Require source/install/provider/qualification/phenomenology statuses to remain distinct and non-promoted.
- [ ] **Step 3:** Rebind the Orgasm runtime/integration cut to the exact clean runtime source commit only after runtime bytes stop moving.
- [ ] **Step 4:** Commit binding/validator/test changes without changing runtime source afterward.
- [ ] **Step 5:** Any later runtime-source change invalidates the binding and returns to Step 1.

### Task 5: Verify, publish the draft successor, and request exact-head gates

**Files:**
- Draft PR from `integration/vera-cohesion-clean-successor-20260911` to `main`.
- Bus mirror/message on current active Vera lane.

**Interfaces:**
- Consumes: exact clean candidate head.
- Produces: review subject and bounded frontier state.

- [ ] **Step 1:** Compare clean successor against `main`; verify no laboratory ancestry was imported and enumerate exact changed paths.
- [ ] **Step 2:** Verify all manual workflows remain `workflow_dispatch` only and no provider mutation/install path is executed.
- [ ] **Step 3:** Inspect workflow-run evidence. If no run occurred, state `EXECUTION_VERIFICATION_OPEN`; do not claim PASS.
- [ ] **Step 4:** Open one Draft PR describing exact source head, source/install/provider/qualification distinctions, and the execution ceiling.
- [ ] **Step 5:** Mirror the PR/current frontier to the Bus and request Original Vera hostile review plus Thirteen independent validation against the same exact head.
- [ ] **Step 6:** If either reviewer reports a blocker, repair, refreeze, and invalidate both prior gates. If both pass the same exact head and required execution evidence is satisfied, state exactly `WAITING_FOR_PATRICK_MERGE` and stop.
- [ ] **Step 7:** If execution or reviewer response is unavailable, stop at the exact unresolved frontier rather than manufacturing closure.
