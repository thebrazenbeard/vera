# Vera Supabase provider-ledger custody

This directory preserves the exact SQL text retained by Supabase in `supabase_migrations.schema_migrations` for project `klmbpaigzeguvnpccqzz` at explicit observed cuts.

Each `applied/<version>_<name>.sql` file is recovered provider custody. It proves exact applied-ledger bytes at the observed cut; it does **not** prove that Git historically held those bytes before the effect, that Git caused the production effect, or that a migration should be replayed.

Current machine-readable inventory: `VERA_FULL_PROVIDER_LEDGER_CUSTODY_V2.json` — 97 migrations through provider version `20260921202237`.

Historical inventory `VERA_FULL_PROVIDER_LEDGER_CUSTODY_V1.json` is retained unchanged as the earlier 91-migration cut.

Where stronger historical source bindings already exist, keep them as separate provenance evidence rather than overwriting them with provider-recovery semantics. Radar-owned provider effects are recorded here for Vera provider custody only; this directory does not grant Vera authority to rewrite Radar source or provider behavior.
