# Supabase provider composition

The Vera Supabase project is a shared runtime composition target, not evidence that every
provider migration was historically authored in this repository.

`supabase/migrations/` is the executable reconstruction baseline for Supabase Branching.
At the bound provider cut it must contain the exact migration identities and exact bytes
recorded by the provider ledger in `provider-custody/`.

New owner-repository migrations may be composed above that baseline only with an explicit
entry in `PENDING_MIGRATIONS_V1.json` that binds the source repository and exact Git blob.
Provider application/readback remains a separate effect.

The pre-repair alternate local lineage is retained under
`supabase/drafts/pre-provider-composition-20260922/` for audit only and is not executable.
