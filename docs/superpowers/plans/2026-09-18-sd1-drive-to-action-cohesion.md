# SD1 Drive-to-Action Cohesion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans task-by-task.

**Goal:** Rebind Cohesion to Sexuality `4e4f70a3433e267f3b769b2c1a676babf5cd4000`, carry the drive-to-action/activation-evidence contract, and separate immutable consumer binding from producer-owned currentness.

**Spec:** `thebrazenbeard/sexuality@4e4f70a3433e267f3b769b2c1a676babf5cd4000:docs/superpowers/specs/2026-09-18-sd1-drive-to-action-runtime-bridge-design.md`

## Exact upstream tuple
- semantic owner blob: `b5aab6974b1a044de7f6ab4db3163eb9dfff01fd`
- semantic owner Git-content SHA-256: `762594a288d7edcb3e1b5c2b1a4bcbe081256e33fcdbbef4c0db37a65c36b7d5`
- regression blob: `818ea76e1ee416d727b7818ff1309f24a8046e40`
- manifest blob: `97b31f59562380eb2ecf24e45b6ce2e092794dd3`
- manifest Git-content SHA-256: `17435cc38e6ee61a8344fa79fa4ca370592f91790af2222f6a7bfb2031162efc`
- causal blob unchanged: `db6d1ae4e579695396c56b1708a7828ddc3ffa05`
- authority blob unchanged: `da08345a3bff11ffb653270abb6ad4b3a1c0541d`

## Global constraints
- Cohesion remains a validator/binder, not a sexual-response generator.
- Drive-to-action semantics are source-bound but response generation stays outside `runtime_cohesion/sexual_drive_binding.py`.
- Frozen artifact integrity and producer currentness are separate propositions.
- Consumer binding must never redefine Sexuality producer currentness.
- Preserve exact-type/primitive-type/canonical-structured-digest hostile boundary.
- No install/current-route/causal/phenomenal/identity claim.
## Task 1 — RED producer-currentness split

Modify `tests/test_sexual_drive_cohesion_binding.py` first.

Add tests requiring a top-level `producer_currentness` object with:
- `provider=thebrazenbeard/sexuality`
- `observed_head=4e4f70a3433e267f3b769b2c1a676babf5cd4000`
- `status=CURRENT`
- `frozen_input_status=FROZEN_INPUT_VALID`
- policy stating consumer binding cannot redefine provider currentness.

Add a regression that changes only the producer observation to a newer synthetic head/status `SUPERSEDED`: canonical frozen component integrity must still validate as its own immutable input subject, while producer currentness no longer reports CURRENT.

Run the focused Cohesion test and confirm RED.

Implement the minimal contract/binder representation. Remove currentness-shaped meaning from the frozen component projection: `currentness_basis` must describe frozen input identity, while producer currentness lives separately.

Rerun focused + adjacent suite and commit `repair: separate SD1 producer currentness from frozen binding`.
## Task 2 — RED/GREEN exact upstream rebind

Update tests first to require Sexuality head `4e4f70a3433e267f3b769b2c1a676babf5cd4000`, manifest blob `97b31f59562380eb2ecf24e45b6ce2e092794dd3`, semantic blob `b5aab6974b1a044de7f6ab4db3163eb9dfff01fd`, and source bridge semantics:
- `TURN_LOCAL_DRIVE_APPRAISAL`
- `REQUIRED_ON_ELIGIBLE_TURNS`
- `CURRENT_TURN_PATH_PARTICIPATION_REQUIRED`
- generic affection does not satisfy sexual candidate reachability.

Run focused tests and confirm RED.

Rebind `architecture/cohesion/VERA_SEXUAL_DRIVE_COMPONENT_V1.json`, registry/index exact object fields, and the canonical structured digest in `runtime_cohesion/sexual_drive_binding.py`. Preserve `NOT_RESPONSE_GENERATOR`.

Run:
- `py -3.11 -m unittest -q tests.test_sexual_drive_cohesion_binding tests.test_inference_boundary tests.test_inference_boundary_review_repairs tests.test_runtime_cohesion_admission tests.test_vera_cohesion_index_v1`
- py_compile on affected Python files
- `git diff --check`

Commit `bind: rebind Cohesion to SD1 drive-to-action successor`.

## Task 3 — Exact-head freeze
Verify from a detached exact-head checkout, capture component Git blob + raw Git-content SHA-256 + canonical structured SHA-256, refresh PR #120 body, and request fresh hostile rereview. Prior exact-head PASS does not transfer.
