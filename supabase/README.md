# Supabase layer

Supabase is the canonical external store for durable Vera memory events.

This directory contains only schema, migrations, validation logic, and structural documentation. It must never contain live memory rows, private relational payloads, credentials, connector tokens, or database dumps.

## Current production project

- Supabase project ref: `klmbpaigzeguvnpccqzz`
- Primary table: `public.vera_save_state_events`
- Current projection view: `public.vera_current_save_state`
- Storage model: append-only events with explicit supersession
- Client access: denied to `anon` and `authenticated`
- Trusted connector access: `service_role` may `SELECT` and `INSERT` on the event table and `SELECT` from the current-state view

## Architectural role

- Current conversation governs present correction, consent, refusal, self-report, and immediate intent.
- Supabase stores durable external event records and temporal history.
- `VERA Memory Ledger` remains a derived Project-local projection for native recall and audit visibility.
- GitHub stores reviewable code and schema, never live private memory.

## Baseline

The migration files in `migrations/` were read from the live Supabase migration history on 2026-07-29. They contain schema operations only and no row data.
