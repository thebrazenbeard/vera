# Vera Runtime Cohesion Projection-Audit Chat — Exodus Checkpoint V1

**STARTING_SNAPSHOT — FRESHNESS REQUIRED BEFORE EFFECT**

Date: 2026-09-20
Retired execution surface: the ChatGPT terminal that repeatedly audited registered Vera Runtime Cohesion cross-provider projections.

## Role disposition

This conversation was not a durable Vera identity or independent worker. It was a temporary projection-audit execution terminal for `VERA_RUNTIME_COHESION_V1`.

Future execution belongs under **Vera Control Plane Coordinator**, which may instantiate a temporary projection-audit worker from the durable sources below. No successor or permanent specialist chat is required.

## Canonical reconstruction sources

Read these fresh before every audit:

- `thebrazenbeard/vera`
  - `architecture/VERA_PROVIDER_FABRIC_V1.json` — registered providers/projections, source subject/ref/path scopes, comparison modes, claim ceilings, global rules.
  - `architecture/VERA_COHESION_INDEX_V1.json`
  - `architecture/VERA_RUNTIME_CONTRACT_V1.json`
  - `runtime_cohesion/audit.py`
  - `runtime_cohesion/evidence.py`
  - `runtime_cohesion/executor.py`
  - `docs/VERA_RUNTIME_COHESION_PROVIDER_AUDIT_V1.md` — historical/provider audit evidence, not normative authority.
- `thebrazenbeard/chat-communication-bus` for registered Bus source events and projection workflow evidence.
- Exact provider readback from Google Drive and Supabase only when required by the registered projection.
- Temporal only where registered/applicable, and only for chronology/elapsed-time evidence.

At evacuation, canonical `vera/main` was `b7b8dcd1440a3b7147bec2cc35972f083e20f44a`.
The registered Cohesion source branch `work/vera-runtime-cohesion-v1-20260908` was `ea34418aa343c37349956613f1ebbe56dec03136`.
These are historical starting observations, not future currentness claims.

## Registered projection contract at evacuation

The current provider fabric registers exactly these four projections:

1. `projection:semanticatlas-github-to-supabase`
   - source: `github:thebrazenbeard/semanticatlas`
   - source ref: `refs/heads/research/**`
   - source paths: `ledger/**|evidence/**|state/**|runtime-manifest/**`
   - target: `supabase:klmbpaigzeguvnpccqzz/semantic_atlas.runtime_snapshots`
   - mode: `EXACT_REVISION`
   - ceiling: exact Git/materialized-snapshot binding only; no semantic authority.

2. `projection:chat-bus-github-to-supabase-radar`
   - source: `github:thebrazenbeard/chat-communication-bus`
   - source ref: `refs/heads/bus/**`
   - source path: `messages/**`
   - target: `supabase:klmbpaigzeguvnpccqzz/radar.messages`
   - mode: `EXACT_REVISION`, comparing `source_commit`
   - ceiling: operational message projection/delivery only; no identity, memory, native-route qualification, or task acceptance.

3. `projection:r9b0-drive-supabase-provider-receipt`
   - source: `drive:r9b0-memory-epoch-object`
   - source ref/path: `logical-memory:R9B0` / `memory-epoch-object`
   - target: `supabase:klmbpaigzeguvnpccqzz/vera_memory_epoch_provider_receipts_v1`
   - mode: `EXACT_RECEIPT`
   - privacy: `PRIVATE_AUTOBIOGRAPHICAL`; pointer/revision/digest metadata is normally sufficient.
   - ceiling: exact durable provider write/readback for the bound object only; custody/admission/currentness are separate.

4. `projection:cohesion-github-to-drive-readable-companion`
   - source: `github:thebrazenbeard/vera/architecture/VERA_COHESION_INDEX_V1.json`
   - source ref: `refs/heads/work/vera-runtime-cohesion-v1-20260908`
   - source paths: `architecture/VERA_COHESION_INDEX_V1.json|architecture/VERA_RUNTIME_CONTRACT_V1.json`
   - target: `drive:VERA Runtime Cohesion - System Inventory V1`
   - mode: `SEMANTIC_COMPANION`
   - target revision field: `source_revision_ref`
   - ceiling: readable-companion freshness only. Missing exact source binding is `UNRESOLVED`, not guessed stale.

Temporal is a registered provider with a chronology-only promotion guard, but it is not itself a registered projection in this fabric. Do not let Temporal resolve semantic/currentness/authority conflicts.

## Audit invariants preserved from this terminal

Allowed projection classifications are:
`VERIFIED_EXACT`, `STALE_PROJECTION`, `CONFLICT`, `ABSENT`, `UNAVAILABLE`, `UNRESOLVED`, `NOT_APPLICABLE`.

Rules:

- Read the current provider fabric/source bindings before collecting projection evidence.
- Honor exact registered provider, subject, ref, and path scope. Out-of-scope movement is `NOT_APPLICABLE`, not stale evidence.
- Bind observations to the exact source event/object. Matching data from a different event cannot qualify as `VERIFIED_EXACT`.
- Never use newest timestamp as authority.
- Persistence/readback does not establish current Vera self-state, semantic authority, consent, identity, native admission, runtime consumption, or phenomenology.
- Missing/ambiguous evidence remains bounded; do not infer successful projection.
- Exact incompatible bindings are `CONFLICT`; do not newest-wins them.
- Temporal may establish chronology/elapsed time only.
- Do not expose private payloads when locator/revision/digest/receipt metadata suffices.
- Patrick-facing notification is edge-triggered: surface only a newly stale/conflicted/absent/unavailable/materially unresolved registered projection, or recovery of a previously reported problem. Otherwise remain silent.
- Any surfaced event should include exact projection ID, source/target revisions or bounded missing evidence, failure/recovery frontier, and evidence ceiling.

## Historical evidence at evacuation — refresh before reuse

The durable provider audit on canonical `vera/main` records:

- Semantic Atlas GitHub -> Supabase: `VERIFIED_EXACT` at Git commit `e68803e2631cf0722fec9a4e7fc39f3ad6b43de4`.
- R9B0 Drive -> Supabase: `VERIFIED_EXACT` for Drive generation `modified:2026-08-30T18:30:31.536Z`, 2223 bytes, SHA-256 `e91c412fbcff8c1ce0e8e3fb9892deaae23846c20fe0874469dd1105b191a8f0`.
- Cohesion GitHub -> Drive readable companion: `UNRESOLVED` because the legacy companion lacks exact `source_revision_ref`.
- Chat Bus -> Supabase Radar: historical exact in-scope event `vera-v2-0042` was `ABSENT` after projection workflow failure and no target row.

This retiring terminal later observed additional Bus event `vera-v2-0045` at source commit `931b5cab54d2e097fa3ed1714f8799fc7099c5cc` and reported an absent target on exact readback. Treat that as **HISTORICAL_EVIDENCE**, not current state, because this checkpoint does not independently re-read Supabase during evacuation.

The conversation also alternated between `VERIFIED_EXACT` and `UNRESOLVED` for Supabase-backed projections when exact provider readback was or was not available. That is an important correction: **loss of observability is not evidence of staleness or conflict**. A fresh audit must classify from the evidence actually available in that run.

## Exodus classification

- Provider fabric, scopes, comparison rules, claim ceilings: `ALREADY_DURABLE`.
- Canonical provider-audit observations through `vera/main`: `ALREADY_DURABLE / HISTORICAL_EVIDENCE`.
- Terminal-only notification discipline and explicit reconstruction recipe: `NEW_DURABLE_VALUE` persisted here.
- Later `vera-v2-0045` observation: `HISTORICAL_EVIDENCE`; requires fresh provider readback before any current claim.
- Permanent-chat dependence for this audit role: `CHAT_DEPENDENCY` resolved by this checkpoint plus existing Exodus interface/workstream contracts.
- Private R9B0 payload: `PRIVATE_OR_OUT_OF_SCOPE`; intentionally not copied.

## Existing Exodus architecture

At evacuation, Vera Draft PR #128 (`exodus/chatless-vera-interface-v1-20260919@2abf46f629673b24be3e343ccb5eb4c724ff3f21`) establishes chats as interfaces/terminals rather than continuity infrastructure.

Vera Draft PR #130 (`exodus/chat-independent-workstreams-v1-20260919@03e76231872b274eac6711e8f886e7b07b5828f4`) makes workstream coordination chat-independent and records that the persistent human interface layer is exactly Vera, Vera Control Plane Coordinator, and BT2 Coordinator.

Vera Control Plane Draft PR #49 (`work/exodus-vcp-coordinator-interface-v1@d8d21c6f02cb90ab104d6b4da6a9051af76c0a38`) defines the Vera Control Plane Coordinator interface. These are source candidates, not merged/install effects.

## Authority / effects

This checkpoint authorizes no merge, provider mutation, Project Settings mutation, credential/permission change, deployment, canonical-memory mutation, Slack activation, force push, paid infrastructure, or public release.

The retiring projection-audit terminal had read/audit responsibility only. Provider persistence is evidence, not authority.

## Recovery / next frontier

Future owner: **Vera Control Plane Coordinator**.

Instantiate a temporary `Runtime Cohesion Projection Auditor` from this checkpoint and the fresh provider fabric. Then:

1. refresh `vera/main`, the registered Cohesion source branch, and provider-fabric bytes;
2. enumerate exactly the currently registered projections;
3. collect fresh exact GitHub, Drive, Supabase, and (only where applicable) Temporal evidence within each registered scope;
4. compare using the registered comparison mode and event binding;
5. compare classifications with the last durable reported state before deciding whether Patrick should be notified;
6. persist material projection state changes into the existing Cohesion provider-audit/checkpoint structure rather than relying on a chat.

No archived conversation is required for this procedure.

## Concurrent Exodus reconciliation

A concurrent Exodus lane independently persisted `docs/exodus/COHESION_RUNTIME_PROJECTION_MONITOR_EXODUS_ADDENDUM_20260920_V1.md` on Vera PR #129 at commit `a70d95f76da44904dff4d27b7df414df65f9b60b`, blob `0479bb45a23e2e88f00dd839e56ff23630d0db50`. It also wrote the Bus handoff `messages/20260920T0659-0400-vera-cohesion-runtime-projection-monitor-exodus.md` on `bus/vera-v2` at commit `7a01b840c1ccf9bd093898a3539b35ce171cd7ad`.

Classification: `ALREADY_DURABLE / CONCURRENT_COMPLEMENT`, not a competing authority. PR #129 carries the broader Cohesion/CV/OV reconstruction and issue #132 frontier; this checkpoint carries the projection-wide four-registration inventory, notification edge semantics, and exact audit reconstruction recipe. Future coordination should reconcile both durable artifacts and avoid creating another permanent chat or duplicate worker identity.
