# V.E.R.A. R6A1 Installation and Rollback

## Status
This document is a dry-run procedure. It does not authorize installation.

## Preconditions
1. Every package checksum validates.
2. The manifest, bundle, supersession map, source bindings, and validation report agree on release ID `VERA_GOVERNED_CORE_R6A1_20260731_B20E7309`.
3. Project Architecture approves the exact package bytes.
4. Patrick separately authorizes the ChatGPT Project wipe-and-replace operation and names the exact release ID.

## Dry-run installation order
1. Export and preserve the current ChatGPT Project files.
2. Verify the export inventory and checksums.
3. Upload the new Project Instructions first.
4. Upload runtime, governance, protocol, tagging, laws, and state owners.
5. Upload manifest, source bindings, supersession, validation, and Supabase preservation files.
6. Confirm all filenames are case-exact and no duplicate auto-suffixed copies became active.
7. Run the validation prompts and verify hard authority stops.
8. Record an installation receipt only after the UI visibly confirms the final file set.

## Rollback
1. Stop use of the candidate package.
2. Restore the preserved prior Project file set.
3. Verify the prior checksums and active Project Instructions.
4. Record the failed candidate as archived, not deleted.
5. Do not claim synchronized removal from any external store without tool evidence.

## Forbidden without separate authorization
No production Supabase migration or row change, canonical-memory write, runtime deployment, credential action, paid-infrastructure action, or repository history rewrite is part of installation.
