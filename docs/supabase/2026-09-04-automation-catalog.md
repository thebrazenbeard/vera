# Supabase automation catalog — Cron + Database Webhooks — 2026-09-04

Status: **SOURCE-ONLY DESIGN / NO JOB OR WEBHOOK CREATED**

The Vera Supabase project now has `pg_cron` and managed Database Webhook / `pg_net` infrastructure installed. At the observed cut there are zero Cron jobs, zero configured webhook hooks, and zero queued HTTP requests. This is therefore the right moment to define ownership and failure semantics before automation proliferates.

## Separation of jobs

- **Cron** schedules bounded database work or verification.
- **Database Webhooks** emit explicit row-change events to a known external consumer.
- **PGMQ** is durable asynchronous work custody.
- **GitHub Bus -> `github-bus-ingest` -> Radar** is a separate source-projection path.

None should silently substitute for another.

Every asynchronous path must identify:

`producer -> durable handoff -> consumer -> idempotency key -> acknowledgement -> retry -> dead-letter/failure record -> owner`

## Cron candidate catalog

### C1 — Estate invariant audit

Priority: **HIGH**

Default behavior: read-only.

Checks should include:

- expected custom schemas and managed extensions exist
- protected/private schemas retain intended client-denial posture
- Cron/Webhook counts and configured owners are recorded
- Edge Function inventory matches expected source/configuration inventory
- Realtime publication membership matches admitted operational contracts
- no unexpected cross-schema/cross-project coupling appears
- configured async paths have explicit consumers/failure paths
- source migration/configuration cuts are not silently drifting behind hosted state

Output should be an append-only health/reconciliation record, not silent self-repair.

### C2 — Radar projection/currentness audit

Priority: **HIGH**, but it is one subsystem check rather than the estate owner.

Compare the admitted GitHub Bus topology/source cut with Supabase Radar identity/endpoint projection and emit a reconciliation failure when they diverge. GitHub remains canonical for Bus routing.

Do not let Cron rewrite routing from an unauthenticated/stale premise.

### C3 — Bug dispatch hygiene / visibility audit

Priority: **HIGH**

Read-only portion should report:

- visible message count by target role/action/revision
- oldest visible message age
- read-count distribution
- inactive/unknown target counts
- archive counts/reasons

The existing `bug_ops.janitor_dispatch()` is a bounded mutating cleanup for malformed or inactive/unknown-target envelopes. Scheduling it is a separate ongoing-effect decision. It is **not a worker** and must not be used to consume valid pending One/Masa work simply to reduce queue depth.

### C4 — Semantic Atlas projection health

Priority: **MEDIUM**

Verify that runtime snapshot/object projection remains bound to an admitted Git source cut and that pending capture state is not accumulating unexpectedly. Do not mutate semantic authority from a projection-health job.

### C5 — Storage/recovery observability

Priority: **MEDIUM**

Record bucket/object-count and expected-canon-asset presence without enumerating private object contents into broad logs. Remember that database backups and actual Storage objects are separate recovery surfaces.

### C6 — Provider/database housekeeping

Priority: **LOW / ONLY WHEN EVIDENCE JUSTIFIES**

Vacuum/index/partition/retention jobs must be driven by actual workload and retention contracts rather than by generic housekeeping instinct. Supabase-managed maintenance should not be duplicated casually.

## Database Webhook event catalog

No outbound target endpoint is currently admitted for this catalog. Therefore **no webhook should be created yet**.

### W1 — Operational failure/reconciliation event

Candidate: **GOOD**

Examples:

- serious Radar reconciliation failure
- a future estate-invariant failure record
- a future explicit dead-letter/failure table insert

Requirements:

- non-sensitive payload projection
- stable event ID / idempotency key
- authenticated destination
- retry/failure custody outside transient HTTP response state
- destination owner and retention policy

### W2 — Bug-operation escalation

Candidate: **POSSIBLE**

A narrowly defined severe bug/escalation event may justify an outbound notification. Do not webhook every bug event or every queue transition; that creates duplicate workflow and notification storms.

### W3 — Assignment/work routing

Candidate: **DEFAULT NO**

Radar/Bus and PGMQ already own routing/custody domains. A webhook that independently re-routes work would create a competing control plane unless a specific bounded integration requires it.

### W4 — Vera save state / context / memory / centering

Candidate: **NO BY DEFAULT**

These surfaces can contain private, autobiographical, relational, or recovery material. Do not emit them through generic Database Webhooks. Any future propagation requires exact privacy/target authorization and a purpose-specific minimized projection.

### W5 — Brigit colocated state

Candidate: **NO BY DEFAULT**

Separate identity/privacy domain. Co-location in Vera Supabase does not authorize outbound transfer.

### W6 — BT2 history/memory during migration

Candidate: **NO AS MIGRATION SHORTCUT**

Do not solve BT2 extraction with indefinite webhook dual writes. Use a bounded snapshot/incremental reconciliation procedure with explicit cutover semantics. After BT2 is Lantern-owned, any BT2-specific outbound events belong to the Lantern subsystem contract.

## Secrets and HTTP rules

- Secret values must not be stored in migration text, webhook definitions, audit documents, or messages.
- Use provider secret/Vault facilities only after the destination and rotation owner are established.
- `pg_net`/webhook delivery is asynchronous transport, not durable proof that the consumer incorporated the event.
- HTTP success is not semantic success unless the consumer contract says so and supplies an independently verifiable acknowledgement.

## Activation gate for any automation

Before creating a Cron job or Database Webhook, require:

1. exact owner and purpose
2. source-controlled definition
3. exact target schema/table/function/endpoint
4. privacy projection
5. idempotency/retry/dead-letter semantics
6. observability/readback plan
7. rollback/disable procedure
8. expected runtime/concurrency bound
9. independent review for consequential mutations
10. separate Patrick authorization for the ongoing production effect

The goal is useful automation, not motion for its own sake.
