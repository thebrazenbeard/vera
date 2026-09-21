# Vera Whole-System Repair V1

Status: **OPEN REPAIR PROGRAM / VERA-SIDE EVIDENCE LANE**

Command: `VERA::WHOLE_SYSTEM_REPAIR::EXECUTE_TO_VERIFIED_CLOSURE_V1`

This branch is Vera's current isolated repair/evidence lane, restacked on
`vera/main@0e9d298b4c9ae9f1ae3a5d1fae29c74a9eeeba52`.

It is **not** the shared integrated closure ledger. BV owns that ledger in
`thebrazenbeard/vera-control-plane` PR #100. Vera sends RESULT / BLOCKER /
REVIEW evidence to BV for integration.

The predecessor Vera repair lane / PR #155 is historical-only because
`vera/main` moved materially during the repair run. Its evidence is preserved,
but it is not the current repair subject.

## Exact source cut

- `thebrazenbeard/vera/main@0e9d298b4c9ae9f1ae3a5d1fae29c74a9eeeba52`
- `thebrazenbeard/vera-control-plane/main@386ef60b7cd3911c07227ccf0e9563ace1f4731c`
- Bus topology binding `f90d52e66d655e9c3cfac63cb529914ac51d3a88`
- Vera provider `klmbpaigzeguvnpccqzz`: ACTIVE_HEALTHY, 89 applied migrations
- VCP provider `fawkirqroyniueeqspif`: ACTIVE_HEALTHY, 4 applied migrations

## Worker partition

Vera owns the Vera repository, Vera Supabase custody/security/reproducibility,
live-Vera Project/source/runtime evidence, and Vera currentness/effect-governance
reconciliation.

BV owns VCP source/provider repair and the integrated closure ledger.

## Rezon hostile review

The opposition method is sourced from
`thebrazenbeard/rezon@estate/rezon-canonical-baseline-v1-20260920`,
especially `docs/ADVERSARIAL_COLLABORATION.md` and
`docs/EVALUATION_AND_FALSIFICATION.md`.

This in-chat reviewer is not independent corroboration.

## Critical live-currentness blocker

The current ChatGPT runtime does not expose an artifact-level receipt proving
which exact release-bound Vera control artifact is installed and governing this
runtime.

Project-available evidence includes both native V2 interface/currentness files
and R10A0 files whose own status says source candidate / not installed / not
runtime-qualified.

Therefore the installed release remains `UNKNOWN`.

## Vera Supabase custody progress

`repair/provider-custody/VERA_SUPABASE_RADAR_CUSTODY_V1.json` binds the first
production custody slice:

- all eight Radar provider migrations were compared to the Git-held Bus source;
- seven are exact byte-for-byte matches;
- `20260902204759_radar_live_message_projection_v1` is not byte-identical,
  but its executable SQL is equal after stripping line comments and normalizing
  whitespace;
- exact originally applied Git bytes for that one migration remain unrecovered.

This does not yet establish complete Vera-provider reproducibility.

## Completion rule

This lane cannot support `WHOLE_SYSTEM_VERIFIED` until the integrated BV
ledger satisfies Patrick's full definition of done. PR creation, review, source
repair, and provider-history reconstruction are intermediate states only.
