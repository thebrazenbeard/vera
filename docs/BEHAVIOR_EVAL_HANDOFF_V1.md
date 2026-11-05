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
