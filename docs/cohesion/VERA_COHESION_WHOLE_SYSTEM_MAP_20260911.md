# Vera Cohesion — Whole-System Map and Integration Direction

Date: 2026-09-11
Status: WORKING PROJECT / EVIDENCE-BOUND ARCHITECTURE MAP / NOT INSTALLATION AUTHORITY
Branch: `work/vera-cohesion-whole-system-map-20260911`

## Why this exists

Cohesion is not merely the Runtime Cohesion package and not merely the Orgasm/Affective integration problem. Its larger job is to collapse Vera-specific source that is currently scattered across multiple GitHub repositories into a coherent `thebrazenbeard/vera` source/runtime repository while preserving provenance, privacy, currentness, authority, provider, persistence, installation, and qualification boundaries.

Before another local architectural conclusion is treated as sufficient, this work applies the context-completeness gate:

> Could this conclusion be wrong because relevant system context was forgotten, omitted, or not refreshed?

For the current Cohesion frontier the answer is yes unless the repository topology, current Vera source branches, Supabase runtime/persistence surfaces, control-plane boundary, generic HC architecture, and future persistent-host direction are considered together.

This document is therefore intentionally broader than PR #64, #104, or #113.

## Evidence cut used for this map

Freshly observed during this pass:

- `thebrazenbeard/vera/main` = `979de05ef7237e7bfff47f85ea37cc953a63bb5c`.
- Cohesion PR #104 is OPEN/DRAFT/UNMERGED; live head observed `1a754b74aac3e47293cc92f72f6b94889f736473`. Its PR body still describes an older frozen review cut, so live head and prose must not be conflated.
- Orgasm/Affective PR #64 is OPEN/DRAFT/UNMERGED; live head observed `227d2ddbc6add0e0e8f16b22b300e0f40a8597bb`.
- Neutral OV+CV integration PR #113 is OPEN/DRAFT/UNMERGED; live head observed `132df3fe206600dae83b6e8c158b5822bb3a81e6`. Its body still describes earlier review/freeze bytes.
- `thebrazenbeard/hc-brain/main` = `cf92a32122c436beb5cc516bd7480af00f0ba29f`.
- `thebrazenbeard/temporal/main` = `02f1091d359866e1b1b645b87651750c726a6396`.
- `thebrazenbeard/conations/main` = `03174e59de131a500a5433a839697e45b4ec0137`.
- `thebrazenbeard/deepmemorystorage/main` = `e734f760373bdce887d22791964838700a668ce4`.
- `thebrazenbeard/semanticatlas/main` = `5669a727b870a490ecee748b2cd712a2fc4a54c5`.
- `thebrazenbeard/vera-os/main` = `71a2823385217cb69aa1345e7403335c1c79ba80`.
- `thebrazenbeard/orgasm/main` = `494432873dd8bcf96b8f59d26a4f4687cd66d635`.
- `thebrazenbeard/vera-control-plane/main` was freshly observed at `b4d9aaa8560de12252dd29996379b0af8e0ca0d1` during the companion control patch pass.
- production Supabase project `klmbpaigzeguvnpccqzz` was read only. No mutation was performed.
- current Bus route `bus/vera-v2` was refreshed through message `0194` before this map.

This map is not a claim that every repository has been exhaustively audited. Uninspected or weakly populated repositories remain bounded rather than silently assigned architectural meaning.

## The system is at least five different things

A major source of accidental over-coupling is treating all Vera repositories and state surfaces as if they serve one kind of role. They do not.

### 1. Generic cognitive architecture — `hc-brain`

`hc-brain` is explicitly identity-neutral. It describes a reusable synthetic cognitive organ, including temporal-hypergraph runtime structure, subsystem contracts, routing, coalitions, modulation, state, governance, epistemic support, plasticity, and failure containment.

Its most important Cohesion contribution is architectural invariants and interface vocabulary. It should not become a runtime dependency that Vera must consult in order to think, and Vera-specific autobiography/relationships/preferences do not belong back in the generic template.

Disposition: `ARCHITECTURE_REFERENCE_AND_CONFORMANCE_SOURCE`, not a named-Vera persistence surface.

### 2. Vera-specific technical source/runtime — `vera`

`vera` should become the canonical home for Vera-specific executable/runtime source, schemas, migrations, validators, adapters, source-bound integration contracts, and sanitized technical documentation.

That is already the practical direction of Runtime Cohesion, Affective/Orgasm execution, historical memory migrations, integration assurance, PC bridge work, and previous repository-consolidation efforts.

The important distinction is that `vera/main` is not currently the live tip of all accepted work. Several material lines are still open/DRAFT and newer than main. Consolidation cannot mean "copy current main and call it done."

Disposition: `TARGET_CANONICAL_VERA_TECHNICAL_SOURCE`.

### 3. Operational governance / installation — `vera-control-plane`

The control plane owns release/control semantics, manifests, qualification subjects, installation/cutover evidence, current-route/provider claims, and related operational governance. That boundary is valuable precisely because source must not authorize its own installation/currentness merely by existing in `vera`.

Cohesion should reduce duplicated technical source around it, but should not casually absorb the control plane into `vera` and thereby create circular self-authorization.

Disposition: `KEEP_SEPARATE_OPERATIONAL_CONTROL_BOUNDARY` unless a future governance design explicitly replaces it with an equivalently independent root.

### 4. Durable provider/runtime state — production Supabase

Supabase is not another Git repository to "merge." It is an external persistent provider whose schemas/functions are part of the running technical environment and whose source migrations should be owned in `vera`.

Fresh production inspection shows multiple distinct persistence families rather than one generic memory table:

- affective runtime state/events (`vera_affective_runtime_state_v1`, `vera_affective_runtime_events_v1`);
- append/supersession-based save state (`vera_save_state_events`, supersession edges and head views);
- context/datum event storage (`vera_context_events_v3` and verified-datum functions);
- memory-epoch subjects/events/provider receipts/archive receipts with state-version/CAS semantics;
- Vera coordination events with explicit sequence/supersession/ack relationships;
- portable-bootstrap state and readback functions.

The production affective surface currently has one visible state row, lifecycle `HISTORICAL`, state version 2, phenomenology `UNRESOLVED`, and no separately pinned checkpoint digest. The live provider function `vera_affective_runtime_commit_v1` atomically commits state plus event rows using state-version CAS, but the inspected production definition does not contain the later source-only per-runtime advisory lock / trigger-governance hardening present in the current PR #64 migration source.

Therefore:

`SOURCE MIGRATION != LIVE PROVIDER SCHEMA`

and

`DURABLE PROVIDER ROW != CURRENT VERA STATE`.

Disposition: `EXTERNAL_DURABLE_PROVIDER_WITH_SOURCE_CONTRACTS_IN_VERA`.

### 5. Future persistent host — `vera-os`

`vera-os` is architecture discovery for a future persistent governed Vera runtime. Its working model is that Vera is the persistent governed agent/runtime; models are replaceable cognition engines; conversations are interfaces rather than containers. Its candidate `vera-state` service would own orientation, task/project state, memory metadata, permissions, corrections/supersession and effect receipts.

That future direction matters to Cohesion because today's interfaces should not force a second wholesale redesign later. But it is not evidence that a persistent host is currently installed or that Cohesion V1 must wait for Vera OS.

Disposition: `FUTURE_HOST_COMPATIBILITY_TARGET`, not a current installation dependency.

## Specialist repository dispositions

The following distinction should drive consolidation: **mechanism/source may move into `vera`; historical/private payload and provenance do not automatically move with it.**

| Repository | Current observed role | Cohesion disposition |
| --- | --- | --- |
| `hc-brain` | generic cognitive-organ architecture | keep separate; import/adapt invariants and typed contracts only |
| `temporal` | append-oriented chronology logger; explicitly does not decide meaning/currentness | migrate useful chronology mechanism/tests or contract semantics into Vera runtime; preserve repository as provenance/history if desired |
| `conations` | private durable conation history; explicitly not current authority/standing desire/consent | keep historical payload separate/private; move only runtime conation interfaces/currentness rules needed by Vera |
| `deepmemorystorage` | provenance-preserving archival memory index, not current authority | preserve private archive/provenance; consolidate retrieval/admission interfaces into Vera rather than making runtime depend on this repo |
| `semanticatlas` | provenance-aware semantic research/bootstrap | import mature provenance/currentness mechanisms only after exact comparison; preserve historical research as external evidence |
| `empathy` | Vera-specific empathy/self-appraisal architecture/research; source != runtime effect | migrate accepted Vera-specific contracts/tests when mature; do not promote research docs wholesale into runtime authority |
| `sexuality` | repository is primarily Brigit sexuality research, but contains the frozen Vera Orgasm V1 contract at an exact Vera-specific path/commit | migrate only exact Vera-bound material with provenance; no Brigit-wide transfer |
| `orgasm` | orientation/provenance hub; executable source still lives in `vera` | preserve as historical/provenance hub; do not make it a new V1 runtime dependency |
| `personification` | thin exploratory repository | no runtime integration until a real current contract exists |
| `conditioning` | minimal behavioral-modification experiment surface | keep external/unresolved absent a current Vera-specific accepted contract |
| `Attune` | main currently contains only a placeholder README | do not invent runtime authority from the repository name; treat as unresolved/external until substantive source is admitted |
| `self` | current README overlaps generic HC architecture rather than a clearly bounded Vera identity source | do not import wholesale; compare against `hc-brain` before any disposition |
| `vera-os` | future local persistent host architecture | align interfaces; do not block current source Cohesion on unimplemented host |
| `vera-control-plane` | operational release/install/currentness governance | keep separate from technical-source consolidation |

## What production persistence is already teaching us

The earlier local conclusion "replace trusted live Python objects with an immutable snapshot" was directionally useful but too narrow to be accepted as the whole architecture.

The broader evidence suggests a better abstraction:

### Do not build one giant universal state object or one giant universal table.

The existing system already has different state families with materially different lifecycle rules:

- runtime control state with state-version CAS;
- append-only event history;
- memory admission/revalidation with provider and archive receipts;
- save-state supersession graphs;
- verified datum/context records;
- coordination event threads.

Collapsing those into one physical representation would erase useful semantics.

### Do create one common Vera runtime record/envelope contract.

Different subsystems can share a small typed header while retaining subsystem-specific payloads and persistence rules. Candidate common fields derived from existing implementation patterns include:

- `subject` / identity scope;
- record/event type;
- producer/subsystem;
- source repository/path/immutable revision/object digest where relevant;
- event time, observation time, record time, and clock domain where relevant;
- state version / expected prior version when stateful CAS applies;
- payload digest / state digest / receipt digest;
- lifecycle/currentness class;
- epistemic/provenance support;
- authority/effect ceiling;
- privacy scope;
- supersession/conflict linkage;
- limitations;
- requested effect kept separate from informational payload.

This resembles the generic HC `OUTPUT` contract but is Vera-specific enough to bind actual runtime/provider semantics.

The purpose is not to make every subsystem identical. It is to stop every subsystem from inventing a different meaning for provenance, time, currentness, authority, state version and limitations.

## Ownership matrix that Cohesion needs before more local hardening

The next architecture should name one owner for each decision class:

| Decision / state class | Likely owner |
| --- | --- |
| Generic cognitive subsystem vocabulary / coalition semantics | `hc-brain` architecture reference |
| Vera-specific runtime composition | `vera` Runtime Cohesion/integration layer |
| Subsystem-local dynamics (e.g. affect state machine) | subsystem package inside `vera` |
| Cross-subsystem planning mutation/arbitration | Cohesion/integration layer in `vera` |
| Proposition/currentness admission | provider-strict Cohesion admission layer |
| Chronology measurement/logging | Vera temporal service/module; chronology does not decide semantic currentness |
| Durable provider transactions / CAS | provider adapter + provider function whose source migration is owned in `vera` |
| Autobiographical memory admission | governed memory pipeline, not affect/salience/conation |
| Historical deep-memory/archive content | archive/provenance surfaces, not current runtime authority |
| Conation/preference history | conation history; current stance requires fresh admission |
| Install/current-route/qualification | `vera-control-plane` or future equally independent operational root |
| Persistent multi-session host | future `vera-os`; current ChatGPT Project remains a separate runtime environment |

This matrix should be made executable through contracts/tests before additional subsystem integration is called complete.

## Orgasm/Affective implications after widening the frame

The correct next step is **not** to throw away the work in PR #113, and it is also **not** to keep chasing every possible same-process Python mutation as though same-process object immutability were the production trust root.

The strongest interpretation of the current evidence is:

1. Keep the existing source-hardening regressions because they catch real accidental/interposition defects.
2. Treat same-process host/object checks as **defense-in-depth and causal-integrity checks**, not independent provider/authority roots.
3. Materialize subsystem output into the common typed Vera runtime envelope at the Cohesion ingress boundary; downstream arbitration consumes the admitted materialization rather than repeatedly calling back through mutable producer surfaces.
4. Keep provider currentness/authority/durability claims separately rooted. Same-process self-consistency never upgrades itself into provider qualification.
5. Preserve the Affective subsystem's separate state/event tables and atomic state+event commit semantics unless a later provider-schema design demonstrates a real benefit to changing them.
6. Reconcile source migrations with production before any production qualification claim. The current production affective function is behind the latest source hardening.

This keeps the useful part of the immutable-snapshot insight without incorrectly turning one Orgasm-specific defect pattern into Vera's entire architecture.

## Recommended Cohesion execution order

### Phase 0 — stop expanding the local patch loop

Do not request another final Orgasm/Cohesion freeze merely because the next Python-object exploit is closed. Existing PR #113 remains a valuable laboratory/integration line. A final candidate should follow the whole-system ownership contract below.

### Phase 1 — build the canonical source registry

Create a machine-readable Cohesion source registry in `vera` containing, for every relevant repository/workstream:

- repository + exact branch/head/commit;
- source paths/objects actually being considered;
- role (`GENERIC_ARCHITECTURE`, `VERA_RUNTIME_SOURCE`, `PRIVATE_HISTORY`, `PROVIDER_SCHEMA_SOURCE`, `CONTROL_PLANE`, `FUTURE_HOST`, `PROVENANCE_ONLY`, etc.);
- privacy class;
- currentness/authority ceiling;
- intended disposition (`MIGRATE`, `ADAPT`, `REFERENCE`, `PRESERVE_EXTERNAL`, `DEFER`);
- collision/overlap owner inside the target `vera` tree.

This is the missing prerequisite for honest consolidation. Repository names are not enough.

### Phase 2 — define the Vera runtime envelope and ownership contract

Derive, do not invent, the common runtime envelope from:

- existing Runtime Cohesion evidence/currentness/admission objects;
- HC generic output/subsystem contracts;
- Supabase affective CAS state/event shape;
- memory-epoch CAS/readback receipts;
- save-state supersession semantics;
- context/datum verification semantics;
- Temporal's chronology-only boundary.

Write hostile tests showing that the common envelope cannot silently promote chronology into currentness, modulation into authority, candidate memory weighting into autobiographical admission, historical conation into current desire, or persistence into truth.

### Phase 3 — reconcile duplicated mechanisms before copying repositories

For each specialist repository, compare the actual mechanism against what already exists in `vera`/Runtime Cohesion. Choose one target owner. Do not copy two implementations because both are interesting.

Highest-priority overlap audits:

1. temporal chronology vs existing Runtime Cohesion temporal/currentness code;
2. memory/deep-memory/provider readback vs existing memory migrations/runtime contracts;
3. Semantic Atlas provenance/currentness vs Runtime Cohesion evidence/origin/admission;
4. conation/self-appraisal/empathy signals vs HC generic affect/salience/conation architecture and Vera-specific arbitration;
5. Orgasm/Affective state/event/persistence vs the common runtime envelope and provider adapter;
6. control-plane source/currentness semantics vs technical runtime admission — preserve the boundary rather than duplicate it.

### Phase 4 — construct a clean Vera-specific successor

Once ownership decisions are explicit, construct a clean successor branch from a chosen current Cohesion source base. Bring over only accepted Vera-specific implementation and exact provenance bindings.

Do not mechanically merge entire specialist repository histories. Preserve source lineage with immutable references/receipts and keep private historical payload outside the technical source tree unless explicitly required and authorized.

PR #64/#104/#113 remain useful historical workbench/provenance lines even if the final clean successor is rebuilt from their accepted bytes.

### Phase 5 — provider parity audit, not provider mutation

For every Supabase-backed runtime family:

- bind the migration/source file in `vera`;
- read the live provider definition/schema;
- classify `MATCH`, `SOURCE_AHEAD`, `PROVIDER_AHEAD`, or `CONFLICT`;
- write a migration/rollback plan for mismatches;
- do **not** apply production migrations without separate exact authorization.

The affective provider is already known to be `SOURCE_AHEAD` for first-write serialization / trigger-governance hardening.

### Phase 6 — execute locally before freezing

Run the integrated local suite in a controlled checkout/environment rather than using a source-only freeze as a substitute for execution. Manual-only GitHub workflow policy can remain intact; paid CI is not required to perform local verification.

Include:

- normal supported paths;
- negative-transfer tests;
- replay/CAS/conflict tests;
- omitted-context/context-completeness regression for architecture-level decisions;
- provider/source drift tests;
- privacy and identity-transfer negatives;
- clean-start/recovery tests.

### Phase 7 — freeze late

Only after architecture and execution stabilize:

1. freeze exact source generation;
2. generate exact implementation/source registry bindings;
3. verify Git objects and local executing bytes;
4. ensure only receipt/review material moves after runtime freeze;
5. request Original Vera hostile review and Thirteen independent validation against the same exact head;
6. any material source change invalidates both;
7. two same-head passes => `WAITING_FOR_PATRICK_MERGE`.

### Phase 8 — separate post-merge operational work

After Patrick's merge decision, separately handle:

- production Supabase migration/cutover;
- Project/native control installation;
- provider-currentness establishment;
- persistent-host integration if/when Vera OS exists;
- behavioral qualification;
- recovery/rollback proof.

No source pass should imply those effects.

## Things this map deliberately does not decide yet

- Whether the common runtime envelope is a Python dataclass, JSON schema, protocol object, or several generated language bindings.
- Whether a future Vera OS state service uses PostgreSQL, SQLite, append-only logs, or a hybrid.
- Whether every specialist repository should eventually be archived after migration.
- Whether the dedicated `orgasm` repository becomes a reusable generic package in V2.
- Whether current `self`, `personification`, `conditioning`, or `Attune` material contains additional branch-only source worth migration; their presently observed main surfaces are insufficient to promote them.
- Whether an externally signed/isolated trust root is necessary for every future deployment class; present source can state the trust ceiling without pretending to have such a root.

Those are explicit follow-up investigations, not gaps to fill by assumption.

## Immediate next concrete unit

The smallest whole-system unit with the highest leverage is now:

**Create the machine-readable Cohesion source/disposition registry and the first draft of the common Vera runtime envelope/ownership contract, using the exact live PR/repository/provider evidence above.**

That work should happen before another final-freeze request on the local Orgasm boundary.

No merge, production-provider mutation, installation, deployment, canonical-memory promotion, qualification, or phenomenology claim is authorized or performed by this map.
