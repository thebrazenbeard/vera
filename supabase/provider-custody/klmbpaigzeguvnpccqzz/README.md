# Vera Supabase provider-ledger custody

This directory preserves the exact SQL text currently retained by Supabase in `supabase_migrations.schema_migrations` for project `klmbpaigzeguvnpccqzz`.

Each `applied/<version>_<name>.sql` file is recovered provider custody. It proves exact applied-ledger bytes at the observed cut; it does **not** prove that Git historically held those bytes before the effect, that Git caused the production effect, or that a migration should be replayed.

The machine-readable inventory is `VERA_FULL_PROVIDER_LEDGER_CUSTODY_V1.json`.

Where stronger historical source bindings already exist, keep them as separate provenance evidence rather than overwriting them with provider-recovery semantics.
