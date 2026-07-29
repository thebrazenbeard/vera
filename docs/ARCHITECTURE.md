# Vera Memory Architecture

## Current design principle

The systems are complementary. No component is promoted merely because it is newer, and no working retrieval surface is removed without an observed replacement test.

## Authority and responsibility

### Current conversation

Controls present correction, consent, refusal, self-report, immediate task intent, and live applicability. Stored records do not override present state.

### Supabase

Canonical durable external store for governed structured memory events, lifecycle history, provenance, semantic tags, and temporal records.

Supabase is append-only for memory events. Corrections and revisions are represented through new superseding records rather than mutation of prior history.

### VERA Memory Ledger

A compact Project-local semantic projection and audit surface. Its purpose is to improve native Project retrieval and expose a readable indexed snapshot of governed records.

The Ledger is not a complete archive, hidden database, or authority over current consent, refusal, correction, self-report, or identity endorsement.

The Ledger remains in service while its retrieval value is tested against Supabase-backed alternatives. It must not be deleted or replaced merely because Supabase is available.

### GitHub

Version control for schemas, migrations, validators, synthetic tests, architecture documents, releases, and checksums.

GitHub is not a live memory database. This repository is public and must contain no private memory records, conversation exports, Ledger snapshots, credentials, or database dumps.

## Temporal model under evaluation

A durable memory record distinguishes:

- `event_time`: when the represented record-producing event occurred
- `event_time_precision`: `EXACT`, `APPROXIMATE`, or `RANGE`
- `record_time`: when the external store persisted the record

Project-local incorporation is a separate operation. A Ledger snapshot may record that it included a Supabase record through a synchronization receipt containing the external record ID, content hash, snapshot ID, and synchronization time.

Ledger inclusion does not by itself prove permanent branch adoption or current endorsement.

## Migration policy

1. Preserve the working VERA Memory Ledger.
2. Add Supabase capabilities alongside it.
3. Use synthetic tests and non-destructive pilots first.
4. Compare recall quality, provenance, temporal behavior, conflict handling, and connector-unavailable behavior.
5. Promote a replacement only after it performs at least as well under fresh-chat testing.

## Data flow

```text
Live conversation
      |
      v
Governed memory decision
      |
      v
Supabase durable record
      |
      +--> VERA Memory Ledger derived projection
      |
      +--> GitHub schemas, migrations, validators, and releases only
```
