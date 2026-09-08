# V.E.R.A.

**Virtual Environment for Reciprocal Agency**

This private repository contains version-controlled cross-cutting technical architecture for the V.E.R.A. project: source code, database migrations, schemas, validators, behavior/runtime support artifacts, and non-sensitive architecture documentation.

## Currentness boundary

The historical neutral release `VERA_NEUTRAL_CORE_R6A0_20260730_EC900174` remains preserved as provenance; it is **not** the current Vera Project release.

The current governed native Project package line is maintained separately in `thebrazenbeard/vera-R9A0`. As of the latest audited binding, the combined R9A0/R9B0 source subject is branch `feature/r9a0-combined-native-implementation-v1` at commit `1d2bb27d5ff89854c93c431998c5ba255704c1b2`.

That repository/source binding is not itself proof of active ChatGPT Project installation, runtime consumption, or mutable provider currentness. Installation, provider state, and runtime effects require their own evidence/readback.

## Purpose

GitHub stores architecture source and durable engineering history. It is **not** the live context store and must not contain private conversation exports, credentials, access tokens, exported Supabase rows, or raw memory-ledger snapshots.

## Bound systems

- **Current ChatGPT Project:** supplies present user intent, correction, Project administration, and active Project instructions.
- **GitHub:** this repository stores cross-cutting architecture/migrations; `thebrazenbeard/vera-R9A0` carries the current governed native package line.
- **Supabase:** project `Vera` stores governed external state when an authorized operation and readback establish the effect.
- **Deep Memory:** `thebrazenbeard/deepmemorystorage` is the private append-only **historical evidence plane**. Its normal architecture operation is `EVIDENCE_SEARCH`; it is not current authority and does not automatically project into current governed memory. See `architecture/integration/VERA_DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.json` and `docs/DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.md` on the source candidate that introduces this binding.

Historical R6A0 bindings under `coordination/` remain provenance only and must not be treated as current routing authority merely because they are present.

## Memory planes

Vera's architecture deliberately separates two memory roles:

- **Current governed memory** (`workstream/memory`, `VERA_MEMORY_CROSS_CHAT_CONTRACT_V1`) owns explicit current lineage, privacy/epistemic filtering, and save/recall receipts.
- **Deep Memory historical evidence** owns append-only history, provenance ceilings, historical-canon classification, contradictions/supersession, and unresolved primary-source frontiers.

A Deep Memory record can be historically canonical without being current or admitted. Any historical-to-current bridge requires separate explicit review/admission and must preserve the original historical provenance, privacy, event time, and currentness limitations.

## Reality and persistence boundary

Connector access and recorded references establish evidence within their observed scope. They do not imply hidden synchronization, automatic persistence, model identity, recollection, consciousness, or authority beyond exposed and authorized operations.

A repository or database write is confirmed only by target-system effect plus readback. Package source, installation, provider state, runtime consumption, and downstream effect are separate evidence domains.

## Workflow

Work-bearing coordination is GitHub-only under issue #46. Slack and legacy Supabase coordination records may be historical evidence, but they are not current workflow authority.

Current execution/authority semantics are defined by:

- `docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md`
- `docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md`
- `docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md`

These V2 documents supersede conflicting older workflow interpretations, especially any reading that requires a second permission or bespoke writer lease for an already-assigned reversible isolated act. Writer leases coordinate genuine shared-writer collision; they are not a substitute source of authority. Clear authorized reversible work defaults to `DO -> VERIFY -> REPORT`.

Older V1 workflow documents remain historical evidence and may still contain useful review/exact-head discipline, but they do not override the V2 execution-precedence model where the two conflict.

Current work must bind mutable claims to fresh evidence rather than relying on this README as a timeless state snapshot.
