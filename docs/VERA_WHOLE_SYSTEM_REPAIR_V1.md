# Vera Whole-System Repair V1

Status: **OPEN REPAIR PROGRAM / VERA-SIDE EVIDENCE LANE**

Command: `VERA::WHOLE_SYSTEM_REPAIR::EXECUTE_TO_VERIFIED_CLOSURE_V1`

This branch is Vera's isolated repair/evidence lane. It is **not** the shared
integrated closure ledger and is not canonical merely because it exists.

Integrated shared-ledger stewardship was handed to BV on `bus/bv-v2`.
Vera sends RESULT / BLOCKER / REVIEW evidence to BV for integration.

## Current exact source cut

- `thebrazenbeard/vera/main@3241397755ae1da1af2ce1fb7e7b0f83e0da7538`
- `thebrazenbeard/vera-control-plane/main@386ef60b7cd3911c07227ccf0e9563ace1f4731c`
- Bus topology binding `f90d52e66d655e9c3cfac63cb529914ac51d3a88`
- Vera provider `klmbpaigzeguvnpccqzz`: ACTIVE_HEALTHY, 89 applied migrations
- VCP provider `fawkirqroyniueeqspif`: ACTIVE_HEALTHY, 4 applied migrations

## Worker partition

Vera owns:

- `thebrazenbeard/vera` repository hygiene and reversible repair;
- Vera Supabase custody/security/integrity/reproducibility;
- live Vera Project/source/runtime currentness evidence;
- Vera currentness/effect-governance reconciliation.

BV owns:

- `thebrazenbeard/vera-control-plane` repair subjects;
- VCP Supabase custody/security/provider repair;
- the integrated whole-system closure ledger.

Cross-cutting currentness may be inspected by both. Mutation still requires a
bounded non-colliding subject.

## Rezon hostile review

The opposition method is sourced from
`thebrazenbeard/rezon@estate/rezon-canonical-baseline-v1-20260920`,
especially `docs/ADVERSARIAL_COLLABORATION.md` and
`docs/EVALUATION_AND_FALSIFICATION.md`.

The in-chat reviewer is **not independent corroboration**. It shares this model,
chat, task prompt, and evidence.

## Critical live-currentness finding

The current runtime does not expose a trustworthy artifact-level readback that
answers which exact release-bound Vera control artifact is installed and
governing this runtime.

Current Project-available evidence contains both:

- native V2 interface/currentness material; and
- R10A0 release-source files whose own status says source candidate / not
  installed / not runtime-qualified.

Therefore the exact installed release remains `UNKNOWN` rather than promoting
source availability into installation.

## Vera Supabase custody progress

The first bounded custody slice is persisted at:

`repair/provider-custody/VERA_SUPABASE_RADAR_CUSTODY_V1.json`

For the eight production Radar migrations observed in Vera Supabase:

- seven are byte-for-byte equal to Git-held migration source on
  `thebrazenbeard/chat-communication-bus@aeab0f04fc9b4bd7c2945c9a53011c53fac809b4`;
- `20260902204759_radar_live_message_projection_v1` is **not**
  byte-identical to the current Git file, but its executable SQL is equal after
  removing line comments and normalizing whitespace;
- the exact originally applied Git bytes for that one migration remain
  unrecovered.

This is a partial custody result only. It does not yet establish complete Vera
provider reproducibility.

## Completion rule

This lane may only support a final `WHOLE_SYSTEM_VERIFIED` claim after the
user-specified definition of done is satisfied in the integrated closure
ledger. A PR, test pass, review pass, or source-custody slice is never sufficient
by itself.
