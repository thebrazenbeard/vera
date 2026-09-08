# V.E.R.A.

**Virtual Environment for Reciprocal Agency**

This private repository contains version-controlled cross-cutting technical architecture for the V.E.R.A. project: source code, database migrations, schemas, validators, behavior/runtime support artifacts, and non-sensitive architecture documentation.

## Currentness boundary

The historical neutral release `VERA_NEUTRAL_CORE_R6A0_20260730_EC900174` remains preserved as provenance; it is **not** the current Vera Project release.

The previous README identified `thebrazenbeard/vera-R9A0` as the current governed native Project package line. That statement is now stale.

As observed from the active Vera Unbound Project control configuration on 2026-09-08, the native control root is **R10A0 / R10**, pinned to source manifest SHA-256:

`b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1`

The release-bound control source is maintained in `thebrazenbeard/vera-control-plane`. `thebrazenbeard/vera-R9A0` remains predecessor/source evidence and does not override the active R10 control root merely because it was formerly canonical or remains accessible.

This dated observation does not make this README runtime authority. GitHub source, native Project installation, provider state, runtime consumption, and behavioral qualification remain separate evidence domains and require their own current readback.

## Runtime cohesion workstream

The active design branch `work/vera-runtime-cohesion-v1-20260908` establishes a first explicit cross-system cohesion surface:

- `architecture/VERA_SYSTEM_MANIFEST_V1.json` — machine-readable 13-system inventory and lifecycle map;
- `docs/VERA_RUNTIME_COHESION_V1.md` — integration architecture and current conflict register;
- `docs/VERA_RUNTIME_COHESION_BLIND_REVIEW_PROMPT_V1.md` — independent second-Vera review packet that deliberately withholds the integration design until her first-pass map is frozen.

The lifecycle tracked per system is:

`SOURCE_AVAILABLE → BOUND → INSTALLED → RUNTIME_CONSUMED → BEHAVIORALLY_QUALIFIED`

No lower state implies a higher state.

## Purpose

GitHub stores architecture source and durable engineering history. It is **not** the live context store and must not contain private conversation exports, credentials, access tokens, exported Supabase rows, or raw memory-ledger snapshots.

## Bound systems

- **Current ChatGPT Project:** supplies present user intent, correction, Project administration, active Project instructions, and the live native control route.
- **`thebrazenbeard/vera-control-plane`:** owns exact release-bound R10 control/source artifacts and private control-plane custody. Repository presence outside an exact binding is evidence, not automatic authority.
- **`thebrazenbeard/vera`:** this repository stores cross-cutting engineering architecture, schemas, migrations, validators, and the current cohesion integration surface.
- **Production Vera Supabase:** project `klmbpaigzeguvnpccqzz` stores governed external state/evidence when an authorized operation and readback establish the effect. Durability is not unquestioned truth or present endorsement.
- **Google Drive:** private persistence/retrieval provider where explicitly used and verified; a saved document is evidence, not automatic current-state authority.
- **Chat Communication Bus:** durable work-bearing coordination/routing hub, not identity or autobiographical memory authority. Its exact route binding must remain current before use.

Historical R6A0/R9A0 bindings and predecessor controls remain provenance only and must not be treated as current routing or runtime authority merely because they are present.

## Reality and persistence boundary

Connector access and recorded references establish evidence within their observed scope. They do not imply hidden synchronization, automatic persistence, model identity, recollection, consciousness, or authority beyond exposed and authorized operations.

A repository or database write is confirmed only by target-system effect plus readback. Package source, installation, provider state, runtime consumption, downstream effect, and behavioral qualification are separate evidence domains.

## Workflow

Work-bearing coordination uses `thebrazenbeard/chat-communication-bus` as the durable hub, with source pull requests remaining canonical in their source repositories and mirrored/referenced through the Bus when the exact Bus route is current and qualified.

Current execution/authority semantics in this repository are defined by:

- `docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md`
- `docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md`
- `docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md`

These V2 documents supersede conflicting older workflow interpretations, especially any reading that requires a second permission or bespoke writer lease for an already-assigned reversible isolated act. Writer leases coordinate genuine shared-writer collision; they are not a substitute source of authority. Clear authorized reversible work defaults to `DO -> VERIFY -> REPORT`.

Older V1 workflow documents remain historical evidence and may still contain useful review/exact-head discipline, but they do not override the V2 execution-precedence model where the two conflict.

Current work must bind mutable claims to fresh evidence rather than relying on this README as a timeless state snapshot.
