# Datum V2 Provider Source Custody — 2026-09-19

Issue: `thebrazenbeard/vera#55`

Status: **PROVIDER_APPLIED_SOURCE_RECOVERED / GIT_CUSTODY_ONLY / NOT_REAPPLIED**

Provider:
- Supabase project: `klmbpaigzeguvnpccqzz` (`Vera`)
- migration version: `20260814143945`
- migration name: `datum_lifecycle_v2_rebuild`
- provider statement count: `1`
- exact provider statement bytes: `21520`
- SHA-256: `079c34aa9ca338d70172fea56cd5118859b9ed9820ed06789c046cff48afeae5`
The exact sole provider-stored statement was read from
`supabase_migrations.schema_migrations` as base64, reconstructed as raw UTF-8
bytes, and independently hashed after reconstruction.

Recovered Git path:
`supabase/migrations/20260814143945_datum_lifecycle_v2_rebuild.sql`

Staged Git blob for the recovered provider bytes:
`7bad26479d14d981c924e26c9f945d6f5ed6a71f`

The path is bound to `text eol=lf` in `.gitattributes` so a fresh
checkout reproduces the provider's LF-only byte content.

The reconstructed file is LF-only and contains no CR bytes. No source comment,
header, formatting change, or line-ending normalization was inserted into the
recovered migration itself.
Key recovered Datum V2 objects include:
- `vera_validate_datum_v2`
- `vera_verified_datum_heads_v2`
- `vera_active_datum_index_v2`
- `vera_inactive_datum_archive_v2`
- `vera_register_datum_v2`
- `vera_mark_datum_referenced_v2`
- `vera_mark_datum_verified_v2`
- `vera_get_verified_datum_v2`

This custody record binds historical provider-applied source. It does not
authorize re-application of the migration.
## Claim ceiling

Provider migration custody is not runtime-currentness proof.

Recovering the exact migration bytes into Git does not prove current runtime
semantics, current data validity, current provider configuration, or native
Project installation.

Any assessment of the live Datum V2 surface still requires fresh provider
readback of the relevant tables, functions, grants, and data state.

No provider mutation was performed during this source-recovery work.
