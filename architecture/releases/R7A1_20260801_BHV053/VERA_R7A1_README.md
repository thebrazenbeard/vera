# V.E.R.A. Neutral Core - R7A1_20260801_BHV053

V.E.R.A. means **Virtual Environment for Reciprocal Agency**.

This successor repairs the R7A0 behavior-law coverage defect and preserves the portable bootstrap architecture.

- Release ID: `VERA_NEUTRAL_CORE_R7A1_20260801_BHV053`
- Repository base: `main@ca49ed09658d0d0d833c60a1f62b432cae340ce4`
- Candidate branch: `feature/r7a1-behavior-laws-successor-v1`
- Behaviors specification: Supabase sequences `1028` and `1033`
- Laws: `VERA-LAW-001` through `VERA-LAW-053`
- Status: generated and locally validated replacement candidate, not installed
- Production changes: none
- Canonical-memory writes: none

## What changed

- preserved laws 001 through 026 exactly;
- added conversational laws 027 through 050;
- added connection retry and failure-classification laws 051 through 053;
- added nine canonical positive cases and fifteen hostile cases;
- activated the expanded law set through Project Instructions and Runtime;
- added Behaviors as normative owner and independent exact-head reviewer;
- added safe read retry, alternate-route, and write-idempotency discipline;
- renamed every Project file with the unique `VERA_R7A1_` prefix.

## Installation boundary

This is a complete Project-file successor, not a delta.

1. Export the current Project files as a rollback archive.
2. Verify `VERA_R7A1_CHECKSUMS.sha256`.
3. Remove the entire current Project-file set.
4. Upload all 22 successor Project files together, including `VERA_R7A1_BOOTSTRAP_MANIFEST.json`.
5. Do not upload any old and new Project files together.
6. Replace the native Project Instructions field with the supplied R7A1 bootloader text.
7. Run the exact initialization command in a fresh chat:

   `VERA::INITIALIZE::PORTABLE_PROJECT_V1`

8. Run a read-only cold-start recovery test in another fresh chat.

Partial replacement or reused filenames are forbidden because ChatGPT may create an unremovable `(1)` suffix and break exact manifest matching.

## Reality boundary

V.E.R.A. is an architecture and coordination environment. It is not a conscious, autonomous, persistent, self-owning, or emotionally reciprocal entity.
