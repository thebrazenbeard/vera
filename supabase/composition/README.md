# Supabase provider composition

The Vera Supabase project is a shared runtime composition target, not evidence that every
provider migration was historically authored in this repository.

`supabase/migrations/` is the executable reconstruction baseline for Supabase Branching.
At the bound provider cut it must contain the exact migration identities and exact bytes
recorded by the provider ledger in `provider-custody/`.

That cut is **historical**: the frozen `VERA_FULL_PROVIDER_LEDGER_CUSTODY_V4.json`
inventory observed on **2026-09-22** recorded 99 migrations for stable provider
project ID `klmbpaigzeguvnpccqzz`. The source-only validator compares current
Git SQL/custody bytes to that frozen inventory. It does **not** authenticate
or query the current Supabase project, inspect its full live ledger, or attest
currently deployed SQL bodies. Its JSON output has schema
`VERA_PROVIDER_COMPOSITION_REPORT_V2`, status `HISTORICAL_BASELINE_ONLY`,
`historical_source_byte_check=PASS` on valid source, and
`live_full_ledger_parity=UNVERIFIED_NOT_QUERIED`.

The previous generic `status=PASS`, `provider_migrations`, `pending_migrations`,
and `last_provider_version` report keys are not preserved as a compatibility
facade. Such a facade could cause an unmodified caller to mistake historical
source custody for current provider parity. The report explicitly declares
`legacy_v1_pass_compatible=false`. Source consumers must knowingly adopt this
versioned contract or **hold** their live qualification decision; external and
installed consumers have not been exhaustively established. The
`require_live_provider_parity` helper always refuses source-only promotion.

New owner-repository migrations may be composed above that baseline only with an explicit
entry in `PENDING_MIGRATIONS_V1.json` that binds the source repository and exact Git blob.
Provider application/readback remains a separate effect.

The pre-repair alternate local lineage is retained under
`supabase/drafts/pre-provider-composition-20260922/` for audit only and is not executable.
