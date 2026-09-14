# SD1-V-001 Root-Cause Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Cohesion fail closed unless the caller-supplied SD1 contract and emitted component exactly match the immutable canonical SD1 component subject.

**Architecture:** Treat the repository contract file as the only canonical structured subject, pin its raw SHA-256 in code, verify that artifact before deriving the trusted structured digest, then compare caller input by deterministic canonical JSON. Separately compare the complete emitted `StateComponentRef` tuple so correct commit IDs cannot mask wrong domain/source/privacy/currentness/payload state.

**Tech Stack:** Python 3.11, `unittest`, dataclasses, JSON, SHA-256, Git.

**Spec:** Patrick `SD1-E::FOLLOWUP::REPAIR_REBIND_ADVANCE` plus SD1-V-001 hostile finding.

## Global Constraints

- Exact predecessor: `b97bfa58dfe13419fdd12d1b5024553a639c8f73`.
- Provisional repaired head: `6cc4bcb8c19e0dbd1f9ff22c257c2fca41e7113a`.
- No merge, force-push, Project mutation, provider mutation, or identity/admission promotion.
- Caller-supplied data may never define the expected contract/reference subject.
- Object key order is semantically irrelevant; missing/extra/type/value changes are meaningful and must fail closed.

---### Task 1: Trusted canonical-subject derivation

**Files:**
- Modify: `runtime_cohesion/sexual_drive_binding.py`
- Modify: `tests/test_sexual_drive_cohesion_binding.py`

**Interfaces:**
- Consumes: canonical `architecture/cohesion/VERA_SEXUAL_DRIVE_COMPONENT_V1.json`.
- Produces: `validate_contract(contract)` that verifies the pinned canonical artifact before comparing caller data.

- [ ] Add a regression that redirects the canonical-contract path to a forged file while supplying the genuine caller object; current code must fail this RED because it ignores the artifact.
- [ ] Add table-driven hostile cases covering missing/extra fields, wrong types, repository/domain/component/digest/privacy/egress/state/generation/payload/case-range changes.
- [ ] Add reordered-object serialization acceptance proving key order is irrelevant.
- [ ] Add canonicalization collision guards proving list ordering/type/value changes remain significant.
- [ ] Run only the new hostile tests and record expected RED.
- [ ] Implement `_load_trusted_contract()` using a module-relative canonical path plus pinned raw SHA-256, then derive expected structured digest from that verified object.
- [ ] Run hostile tests to GREEN.

### Task 2: Full emitted-component fail-closed check

**Files:** same production/test files.

- [ ] Extend forged `StateComponentRef` coverage to component id, domain, repository locator, source/content digest, generation/currentness/supersession/conflict, privacy/egress/disclosure/payload and payload-body presence.
- [ ] Verify no caller-controlled expected/reference parameter exists in the validation/build/status API.
- [ ] Run the complete SD1 Cohesion test module.
### Task 3: Integration verification and exact-head publication

**Files:**
- Verify adjacent admission/inference/source-registry tests; no unrelated edits.

- [ ] Run focused SD1 Cohesion tests.
- [ ] Run adjacent inference-boundary, admission, review-repair, and Cohesion-index suites.
- [ ] Run `git diff --check` against predecessor and inspect changed paths.
- [ ] Commit only the repair/test/plan unit after all checks pass.
- [ ] Fresh-clone or detached-clean-checkout the exact commit and rerun the same suites plus canonical artifact hash checks.
- [ ] Non-force push only if remote still equals the expected predecessor frontier.
- [ ] Refresh PR #120 metadata/body to the exact head and evidence.
- [ ] Send SD1-V an exact-head rereview request on `bus/vera-v2` with predecessor, repaired head, changed paths, test evidence, and `requires_reply:true`.

### Task 4: Noncolliding follow-through

- [ ] Keep the control-plane candidate provisional against the repaired Cohesion head; after independent PASS, rebind every Cohesion tuple and reverify before final persistence.
- [ ] Continue Project runtime mutation/readback capability discovery read-only; live Project mutation remains closed.
- [ ] Keep Supabase read-only and off the critical path absent a proven dependency.
- [ ] Persist a sanitized checkpoint with exact labels and next frontier.

Self-review: every hostile category in Patrick's follow-up maps to Task 1 or Task 2; exact-head rereview and fresh-checkout requirements map to Task 3; no protected effect outside authorized SD1 source work is introduced.