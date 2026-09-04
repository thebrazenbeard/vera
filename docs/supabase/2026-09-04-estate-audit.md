# Supabase estate audit — 2026-09-04

Status: **WORKING AUDIT / SOURCE-ONLY / NO PRODUCTION MUTATION**

This document records a read-only estate audit of the live Supabase projects and the current source repositories. It is not a deletion authorization, migration execution receipt, deployment claim, or proof that an object is unused merely because it is empty.

## Provider bindings inspected

- Vera production Supabase: `klmbpaigzeguvnpccqzz` (Postgres 17, `ca-central-1`)
- Project Lantern Supabase: `agvhmutlrolbaijzlbqk` (Postgres 17, `us-west-2`)
- Vera source: `thebrazenbeard/vera@979de05ef7237e7bfff47f85ea37cc953a63bb5c`
- Build Team 2 source: `thebrazenbeard/build-team-2.0@main` tree `ec2987e45f64a588ac92f6cae9964cb3725b9485`
- Project Lantern source: `thebrazenbeard/project-lantern@main` tree `6333d386c74ce37e644fa1e995be9f9dc3fe6394`

Patrick's current project-boundary instruction for this work: Build Team 2 material may move from Vera production Supabase to the separate Project Lantern Supabase project.

## Executive classification

| Surface | Provisional class | Reason / next test |
|---|---|---|
| Vera `build_team_2` | **MIGRATION CANDIDATE -> LANTERN** | Strong project-local identity; substantial live/history state; no cross-schema foreign keys found. Move only after source lineage, caller, API, and cutover verification. |
| Vera `bug_ops` + `pgmq` bug queues | **VERA OPERATIONS** | Non-empty and materially used; configuration binds `project_key=VERA` / Vera project ref; One is current coordinator; Voss is already inactive. Do not move merely because BT2 roles participate. |
| Lantern `bug_ops` + bug queues | **DORMANT / STALE CONSTRUCTION COPY** | Schema/queues exist but are empty; migration lineage stops at older V1 generation and lacks Vera's later v2 hardening/retire-Voss changes. Decide owner before reuse or eventual retirement. |
| Vera `radar` | **VERA OPERATIONS / DERIVED PROJECTION** | Actively receiving GitHub Bus projections; Realtime publication configured over seven Radar tables. GitHub Bus remains canonical. |
| Vera `semantic_atlas` runtime snapshots/objects | **DERIVED OPERATIONAL PROJECTION** | Runtime objects are Git-bound/materialized; preserve until tested rebuild exists. Capture policy is config; capture events/outcomes are operational/history evidence. |
| Vera `redworm` | **UNKNOWN / HOLD** | Tiny but encodes runtime succession/lineage and has observed reads/writes. No source owner was resolved by code search. Size is not retirement evidence. |
| Vera `public` | **MIXED OWNERSHIP / DECOMPOSE** | Contains Vera state, memory epoch/bootstrap, datum APIs, and Brigit-specific state. `public` is a namespace, not an ownership boundary. |
| Vera Brigit tables in `public` | **SEPARATE IDENTITY COLOCATED / HOLD** | Must be reviewed under Brigit privacy/identity ownership, not silently classified as Vera core or garbage. |
| Vera Storage `files/canon_images/*` | **VERA CORE ASSET STORAGE** | Five current canon images; private bucket. Retain. |
| Vera Auth | **DORMANT CONFIG SURFACE** | Zero users observed. No conclusion about whether Auth may be needed later. |
| Vera Realtime | **CONFIGURED / ACTIVE CAPABILITY** | No current subscription rows, but `supabase_realtime` publication is configured for Radar. Not unused. |
| Vera Cron | **INSTALLED / UNCONFIGURED** | `pg_cron` installed; zero jobs observed. Clean slate for future bounded verification/maintenance. |
| Vera Database Webhooks | **INSTALLED / UNCONFIGURED** | Managed webhook plumbing installed; no hooks/triggers/queued requests observed. Clean slate. |
| Vera Storage FDW / Vault scaffolding | **PLATFORM INFRASTRUCTURE / HOLD** | Platform-created vector/analytics/knowledge foreign servers reference Vault-backed Storage credentials; no foreign tables/user mappings observed. Do not prune as ordinary app debris. |

## Vera `build_team_2`: extraction facts

The live schema is more than the four headline collective tables. Current relations include:

- `collectives` — 1 row
- `facets` — 10 rows
- `tasks` — 17 rows
- `perspectives` — 0 rows
- `decisions` — 0 rows
- `memory_events` — 5,934 live rows, append-only, about 14 MB
- `one_working_laws_current` — 1 row
- `role_training_packages` — 7 rows, append-only
- `role_training_current` — 2 rows
- `role_training_qualifications` — 0 rows
- `role_operational_checkpoints` — 3 rows, append-only with qualification-binding guard
- current-resolution views for training/checkpoints

Cumulative PostgreSQL statistics show `memory_events` is heavily read and written (5,947 inserts observed by stats, thousands of scans); it is not dead storage.

### Favorable migration property

No cross-schema foreign keys were found between `build_team_2` and Vera's other custom schemas. That substantially reduces extraction risk.

### Actual coupling that must move

Vera exposes service-role `SECURITY DEFINER` wrapper RPCs in `public` which reference `build_team_2`, including task creation, perspective/decision writes, append-memory, and recent-memory reads. A Lantern cutover therefore must move/recreate the intended API boundary and update callers before the Vera copy can be quarantined or retired.

The `build_team_2` schema itself is deliberately not granted USAGE to anon/authenticated/service_role; service-role access is mediated through controlled wrappers. Preserve that security intent in the destination rather than blindly copying ACLs.

## Source reproducibility defect

The current Build Team 2 README says the storage model is defined by `migrations/001_build_team_2.sql`, but current `main` has no `migrations/` directory. The live Vera Supabase migration ledger, by contrast, records the BT2 evolution from initial hive-mind creation through identity/RPC, One laws, training/checkpoint infrastructure, view hardening, and trigger search-path hardening.

This means the remote database currently has a more complete record of BT2 database evolution than the nominal BT2 source repository. That is backwards and should be repaired **before** the Lantern production cutover.

The Vera repository does contain Supabase migration source for at least later BT2 hardening, so migration reconstruction should begin from immutable Vera source plus live catalog introspection rather than from a newly invented schema.

Project Lantern has a similar reproducibility gap: its live `lantern_material`, R9A0-era, and old bug-operation structures are not visibly represented by a normal Supabase migration directory on current `project-lantern@main`.

## Vera `bug_ops` is not a BT2 relocation candidate by default

Fresh live state:

- 92 bug reports
- 237 bug events
- 175 v2 dispatch events
- 236 operation receipts
- PGMQ `bug_dispatch`: about 91 live messages and 84 archived messages
- role-specific work queues currently empty
- role registry: Masa, Mune, One active; Voss inactive
- system config binds the subsystem to project `VERA` / Vera Supabase and identifies One as coordinator

The database migration history also includes the later v2 replay-safety / project-key work and explicit Voss retirement. Lantern's older empty bug schema/queues do not contain that complete current lineage.

Conclusion: retain Vera bug operations while separately deciding whether Lantern needs its own bug system. Do not share one mutable queue across the project boundary by accident.

## API / security observations

`public` grants schema USAGE to anon/authenticated/service_role, while the named internal schemas generally do not grant anon/authenticated USAGE. That makes `public` the highest-value exposure review surface.

Several Vera datum/helper functions in `public` have effective EXECUTE privilege for anon/authenticated. The underlying datum tables themselves have no anon/authenticated table grants and the principal mutating functions are SECURITY INVOKER, while `vera_context_events_v3` has explicit deny policies for those client roles. This is **not evidence of a current bypass**, but it is needless API-surface ambiguity and should be rationalized function-by-function.

Many internal functions in non-public schemas also retain default function EXECUTE privileges, but schema USAGE blocks ordinary anon/authenticated reachability. Treat this as ACL hygiene, not an emergency vulnerability.

Security Advisor output was INFO-only at this audit cut, primarily `RLS enabled/no policy`. In several server-only tables, RLS-with-no-client-policy can be intentional deny-by-default behavior. Do not mechanically create permissive policies to silence the Advisor.

## Performance observations

Advisor output is also INFO-level. It identifies unindexed foreign keys, including several BT2 training/checkpoint/memory relations, and many currently-unused indexes across Vera context, Semantic Atlas, Brigit, and Radar.

Do not drop an index solely because the provider reports it unused. Several systems are young, sparse, event-driven, or intentionally pre-indexed for future queries. Use query/liveness evidence and expected access paths before retirement.

## Liveness evidence changes several cleanup calls

Cumulative relation stats show strong use of:

- `build_team_2.memory_events`
- `public.vera_coordination_events`
- Radar messages/delivery/acknowledgement relations
- Semantic Atlas runtime objects/snapshots
- Vera bug reports/events/receipts/dispatch

`redworm` also shows nonzero historical reads/writes and therefore remains UNKNOWN rather than RETIRE.

Lantern, by contrast, shows actual use concentrated in `lantern_material`. Its R9A0 coordination/governance and bug-operation tables are effectively empty in the observed cut, making them valid **retirement candidates for later proof**, not immediate deletions.

## Async topology

Vera currently has four distinct asynchronous mechanisms that must not be allowed to become overlapping mystery workers:

1. GitHub Bus -> `github-bus-ingest` Edge Function -> Radar RPC projection
2. PGMQ bug dispatch/work queues
3. Database Webhooks / `pg_net` (installed, no configured hooks yet)
4. Cron / `pg_cron` (installed, no configured jobs yet)

Every future async path should declare:

`producer -> durable handoff -> consumer -> idempotency key -> acknowledgement -> retry -> dead-letter/failure record -> owner`

Cron should default to bounded verification/maintenance. Webhooks should default to explicit outbound event notifications. Neither should silently become a self-repair authority.

## Proposed BT2 -> Lantern migration sequence

No step below is a production-effect authorization.

1. Reconstruct and version the exact BT2 schema/API migration lineage from immutable Vera migrations plus live catalog readback.
2. Define destination ownership and namespace inside Project Lantern; do not collide with `lantern_material` semantics.
3. Decide whether BT2 API wrappers remain RPCs, move behind a dedicated internal API schema, or are mediated by a Lantern service/Edge Function. Preserve service-only access intent.
4. Create destination schema through versioned migration source, not Dashboard-only state.
5. Copy a frozen/exported snapshot and verify per-table row counts plus deterministic digests/invariants. For large `memory_events`, verify ordered identity/content digests rather than trusting a row-count match.
6. If the subsystem cannot tolerate a short write freeze, use an explicitly reconciled incremental-copy strategy; do not invent indefinite dual-write coupling.
7. Cut writers to Lantern first, then readers.
8. Verify normal BT2 operation no longer requires synchronous Vera-database access. Cross-project identity references should be stable IDs/events/contracts, not permanent database joins.
9. Quarantine Vera BT2 as read-only for a proving window and watch for attempted use.
10. Only with separate Patrick authorization and positive no-consumer evidence, retire Vera BT2 objects/wrappers.

## Project-wide cleanup order

1. **Freeze estate manifest and ownership map.** Every object gets owner, semantic class, writer, reader, access path, retention rule, and reproducible source locator.
2. **Repair source-of-truth gaps.** Put database migration/configuration state under versioned source before more Dashboard-only automation is added.
3. **Rationalize `public`.** Reduce ambiguous RPC exposure and separate domain ownership without breaking intentional service-only/RLS behavior.
4. **Extract BT2 to Lantern.** Follow the verified cutover above.
5. **Classify Lantern legacy baggage.** Old R9A0 construction and empty bug/queue machinery must earn RETAIN or RETIRE status independently.
6. **Reconcile active projections.** Radar topology/currentness, Semantic Atlas projection rebuildability, and other derived-state contracts get explicit source cuts and checks.
7. **Introduce automation deliberately.** Cron/Webhooks only after owners/invariants/failure paths exist.
8. **Retire last.** DORMANT/UNKNOWN never becomes RETIRE from age, naming, size, empty-row state, or Advisor suggestions alone.

## Independent review

Vera requested a separate hostile review from Seven on the canonical Chat Communication Bus (`SUPABASE-ESTATE-CLEANUP-20260904`, round R1). That review is intended to challenge the entire estate plan—cross-project coupling, migration atomicity, RLS/API exposure, queue/idempotency semantics, secrets, rollback, regional differences, and hidden dependencies—before consequential changes.

Until that review is returned and reconciled, this file is an evidence inventory and provisional architecture, not an implementation decision.
