# VERA behavior evaluation: portable public handoff V1

This JSON handoff is a **source-only, HOLD-by-default import contract** for
`model-training`, `labyrinth`, and other authorized consumers. It is anchored
to the **bytes** of the canonical VERA behavior profile v1.0.1, not to model
identity, private history, or an installed runtime.

Import `architecture/identity/VERA_BEHAVIOR_EVAL_HANDOFF_V1.json` and verify it
with `python -m scripts.validate_behavior_eval_handoff` (Python standard library
only). A consumer must reject a changed profile hash, unexpected schema,
dimensions, controls, admission state, or unknown fields. A downstream copy
must retain this binding or explicitly version a replacement.

The ten `dimensions[].id` values map one-to-one to the profile's intended
evaluation dimensions. They are **dimensions, not a public test bank or scoring
rubric**. The public file deliberately contains no prompts, examples, case IDs,
answers, user conversations, weights, or private evaluator artifacts.

## Eight dialogue families are not ten behavior dimensions

The supplemental `architecture/identity/VERA_DIALOGUE_FAMILY_CROSSWALK_V1.json`
records a **design hypothesis**, pinned to `model-training` Draft #349 at
`f5917287` (blob `9eebdaab`), about which of its eight fictional dialogue
scenario families might exercise some of these ten behavior dimensions. The
families are curriculum organizations, not evaluator dimensions or measured
model qualities; this is a many-to-many interpretation, not an identity or
score conversion. `pragmatic_help` deliberately has no direct dimension
hypothesis. `voice_recognizability` and `cross_runtime_consistency` have no
direct family hypothesis at all. Both require distinct owner-approved tests.

This source-only crosswalk does not establish voice fidelity, conversation
quality, continuity, model improvement, held-out independence, or runtime
identity. In particular, an assistant can mimic a few fictional responses
without recognizing its runtime or retaining a consistent voice. A consumer
must not treat a family count, mapping, or public example as a held-out PASS.
Changes to the external family set or pinned Vera profile require a new
reviewed mapping version; the local verifier only checks the pinned source
contract, not the present external repo or any model execution.

The verifier also compares JSON values recursively by **type**: numeric zero
cannot impersonate a mandatory `false` approval or evaluation gate, even
though those values compare equal in Python.

## A real behavioral comparison requires separate authority and evidence

1. Obtain Patrick's explicit approval for the proposed behavior-only cases,
   allowed data use, evaluation authority, and model-run resources. Keep
   private examples and gold answers in owner-approved isolated custody.
2. Have an independent evaluator certify train/held-out disjointness and
   perform blinded, paired candidate-vs-unmodified-base scoring. Neural
   training-improvement claims require the five-arm comparator from
   `model-training` #329: candidate, frozen untrained base, sham update,
   shuffled-label and corrupted-label controls on the same held-out cases.
   A training-free weight-compilation claim instead requires zero-patch,
   sham-patch and random-patch controls; label corruptions are inapplicable.
3. Bind each arm to real model/base/adapter-or-compiled-artifact, tokenizer
   (or witnessed non-applicability), runtime, behavior-profile and generation-
   configuration provenance. A source hash cannot prove weights were loaded.
4. Keep case-level responses and gold outside public Git. Publish only an
   owner-approved, privacy-screened independent receipt. That receipt needs
   its own authenticated authority/readback; this handoff cannot attest it.

The verifier **intentionally cannot turn this JSON into `PASS`**, even if a
caller edits `admission` or inserts fabricated scores. The source contract
supports consumer integration tests but never represents trained capability,
effective persona binding, learning improvement, or physical Qwen inference.
