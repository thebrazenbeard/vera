# Vera Supabase portfolio inclusion reconciliation

This is a **read-only operator contract**, not a migration queue, runtime activation, or authorization to deploy code from sibling repositories.

## Scope

`PORTFOLIO_INCLUSION_V1.json` classifies explicit integration candidates relative to the Vera Supabase provider. An existing table or Edge Function proves only that an object was observed in that provider. It does not prove that `vera_core.QualifiedVeraRuntime` is installed, selected, connected, or behaviorally qualified.

The registry deliberately distinguishes already-deployed external state, separately owned CCB/Bug Ops services, retained historical BT2/Redworm state, optional Vera Ark and Masamune candidates, and local-only providers.

## Read-only current-state probe

Use the connected Supabase project or a trusted read-only SQL client to run:

```sql
SELECT table_schema || '.' || table_name AS table_ref
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND table_schema IN (
    'public', 'radar', 'semantic_atlas', 'build_team_2',
    'bug_ops', 'redworm'
  )
ORDER BY table_schema, table_name;
```

Independently inspect the project's Edge Function names. Supply *only* object names to a local file shaped like:

```json
{
  "tables": ["public.vera_save_state_events", "semantic_atlas.runtime_snapshots"],
  "edge_functions": ["github-bus-ingest"]
}
```

The example above is deliberately partial and **will report drift** for the current full deployed contract. Populate it with the complete fresh observed inventory.

Run:

```powershell
python scripts/validate_supabase_portfolio_inclusion.py --inventory observed.json
```

Exit code 0 means the exact **registered objects** in the supplied observation matched. Exit code 1 means the supplied observation differs from the declared contract. Parsing/contract errors return exit code 2. Extra observed objects are reported without automatically being admitted or treated as defects.

The program has no network transport, credentials, SQL mutation, schema alteration, deployment or runtime-selection capability.

## Admission rules

- **Present:** existing provider objects are checked for absence, but remain their source owners' external state.
- **Optional:** Vera Ark's event mirror is design-only; include it only after selecting an operational producer, exact target, writer role, retention policy, migration custody and live readback.
- **Separate service:** Masamune, SQL Connectome and F.U.C.K.U.P. do not silently join Vera's project because their source contains SQL or an Edge Function.
- **Local:** Vera Mono's native state ledger and Mediaphile's LAN SQLite database are not replicated to Supabase by default.
- **Control/authority:** Only an exact separately authorized provider effect may deploy a schema or function; this document cannot provide that authority.

Never put credentials, row data, autobiographical memory, or tokens in a supplied inventory or Git repository. A file-based inventory is a dated observation, not automatic monitoring.
