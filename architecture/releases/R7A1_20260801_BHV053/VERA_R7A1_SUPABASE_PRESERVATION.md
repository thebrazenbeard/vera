# V.E.R.A. R7A1 Supabase Preservation Plan

## Status

Supabase project `klmbpaigzeguvnpccqzz` remains external project infrastructure.

Patch evidence was read from the append-only coordination ledger:

- sequence 1028: base Behaviors law specification;
- sequence 1033: retry and alternate-route amendment;
- sequence 1034: Project Architect implementation start.

These rows are operational evidence, not hidden execution or canonical memory.

## Preserve

- append-only coordination and bootstrap registry history;
- prior R7A0 durable binding and read-back confirmation as historical evidence;
- exact sequence, acknowledgement, supersession, branch, source, and temporal fields;
- legacy rows without promoting them into active truth.

## Production boundary

This release applies no production schema change, row rewrite, deletion, migration, function deployment, credential action, or service configuration. A fresh initialization after installation may create a new governed bootstrap claim and binding only under the exact initialization command and existing registry rules.

## Retry discipline

Read-only Supabase failures use the safe retry ladder. Ambiguous writes require commit-state and operation-identity verification before retry. Deterministic authorization, schema, or integrity failures are not retried as transient connection failures.
