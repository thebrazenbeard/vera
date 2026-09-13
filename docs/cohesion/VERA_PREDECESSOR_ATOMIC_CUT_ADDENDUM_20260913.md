# Predecessor atomic-cut addendum — 2026-09-13

Status: `ATOMIC_STATEMENT_READBACK / NO_PROVIDER_MUTATION`.

At `2026-09-13T03:23:54.997914Z`, one SQL statement recomputed all nine migration-table counts/digests, the receipt-sequence state, and the 298-object classification. The nine table counts/digests exactly matched `architecture/VERA_PREDECESSOR_MIGRATION_CARGO_SNAPSHOT_20260912.json` from `vera@d56666c558da24587dc3d11f39b0f177971cb5e3` (blob `39311906abf8536a0ddb0baff21d996e28e9255f`).

Table digest preimage is now explicit: SHA-256 over UTF-8 bytes of `jsonb_agg(to_jsonb(row) ORDER BY <declared_primary_key>)::text`; an empty table uses literal `[]`.

The same statement returned classification count `298`, unknown count `0`, and classification SHA-256 `05c9deb50dff86b63c3afde0aec5ee477a2fea855b8c1e097f67c62d6422c48a`. Its preimage format is UTF-8 lines `schema|object_class|identity|disposition`, ordered by `schema_name,object_class,identity`, joined with LF.

The full 298-line classification preimage was observed in the same read but is not yet persisted in source, so that hostile-review item remains open. Sequence state was included in the same statement but remains PostgreSQL non-MVCC sequence state.
