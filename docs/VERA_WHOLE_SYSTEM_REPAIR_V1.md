# Vera Whole-System Repair V1

Status: **OPEN REPAIR PROGRAM**

Command: `VERA::WHOLE_SYSTEM_REPAIR::EXECUTE_TO_VERIFIED_CLOSURE_V1`

This branch is the Vera-owned write lane for the shared closure ledger. It is not
canonical merely because it exists.

## Current exact source cut

- `thebrazenbeard/vera/main@3241397755ae1da1af2ce1fb7e7b0f83e0da7538`
- `thebrazenbeard/vera-control-plane/main@386ef60b7cd3911c07227ccf0e9563ace1f4731c`
- Bus topology binding `f90d52e66d655e9c3cfac63cb529914ac51d3a88`
- Vera provider `klmbpaigzeguvnpccqzz`: ACTIVE_HEALTHY, 89 applied migrations
- VCP provider `fawkirqroyniueeqspif`: ACTIVE_HEALTHY, 4 applied migrations

## Rezon hostile review

The opposition method is sourced from
`thebrazenbeard/rezon@estate/rezon-canonical-baseline-v1-20260920`,
especially `docs/ADVERSARIAL_COLLABORATION.md` and
`docs/EVALUATION_AND_FALSIFICATION.md`.

The in-chat reviewer is **not independent corroboration**. It shares this model,
chat, task prompt, and evidence.

## First critical finding

The current runtime does not expose a trustworthy artifact-level readback that
answers which exact release-bound Vera control artifact is installed and
governing this runtime.

Current Project-available evidence contains both:

- native V2 interface/currentness material; and
- R10A0 release-source files whose own status says source candidate / not
  installed / not runtime-qualified.

Therefore the repair program records the installed release as UNKNOWN rather
than promoting source availability into installation.

## Worker collision boundary

Vera owns this ledger and Vera-side repair subjects. BV has been asked through
the Chat Communication Bus to own VCP repository/provider repair subjects and
return evidence. Cross-cutting control-currentness may be inspected by both;
mutation requires a bounded claim/handoff.

## Completion rule

This branch may only claim `WHOLE_SYSTEM_VERIFIED` after the user-specified
definition of done is satisfied. A PR, test pass, or review pass is never
sufficient by itself.
