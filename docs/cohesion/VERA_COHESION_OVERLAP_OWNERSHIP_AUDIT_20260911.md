# Vera Cohesion — Overlap and Ownership Audit

Date: 2026-09-11
Status: WORKING PROJECT / SOURCE-BOUND ARCHITECTURE AUDIT / NOT INSTALLATION AUTHORITY

## Purpose

Cohesion must consolidate Vera-specific technical mechanisms into `thebrazenbeard/vera` without preserving accidental repository boundaries as duplicate runtime owners.

This audit applies the context-completeness gate before the clean successor is constructed:

> Could an ownership decision be wrong because a relevant existing implementation, provider lifecycle, authority boundary, private-history surface, or superseding source was omitted?

The current answer is bounded by the exact source cuts listed below. Mutable heads must be refreshed again before migration or final freeze.

## Evidence cut

- `thebrazenbeard/vera/main@979de05ef7237e7bfff47f85ea37cc953a63bb5c`
- Cohesion PR #104 live head `1a754b74aac3e47293cc92f72f6b94889f736473`
- Affective/Orgasm PR #64 live head `227d2ddbc6add0e0e8f16b22b300e0f40a8597bb`
- OV+CV integration laboratory PR #113 live head `734d7b4a2fee6a3cb672877b71c7ca35588ef14f`
- `thebrazenbeard/hc-brain/main@cf92a32122c436beb5cc516bd7480af00f0ba29f`
- `thebrazenbeard/temporal/main@02f1091d359866e1b1b645b87651750c726a6396`
- `thebrazenbeard/conations/main@03174e59de131a500a5433a839697e45b4ec0137`
- `thebrazenbeard/deepmemorystorage/main@e734f760373bdce887d22791964838700a668ce4`
- `thebrazenbeard/semanticatlas/main@5669a727b870a490ecee748b2cd712a2fc4a54c5`
- `thebrazenbeard/empathy/main@4b2a6998f39aa4763c1c5a28fc3d815104e5637e`
- `thebrazenbeard/vera-os/main@71a2823385217cb69aa1345e7403335c1c79ba80`
- `thebrazenbeard/orgasm/main@494432873dd8bcf96b8f59d26a4f4687cd66d635`
- production Supabase project `klmbpaigzeguvnpccqzz`, read-only evidence cut from 2026-09-11

The owner names below are **target ownership decisions**, not claims that every named module already exists on `vera/main` or is installed in a live runtime.

## 1. Temporal chronology vs semantic currentness

### Existing overlap

The standalone Temporal repository is deliberately small: it records event chronology, sorts events, and computes elapsed time. Its own contract says that a logged event does not automatically become memory, current state, identity, preference, consent, authority, or truth.

`vera/docs/TEMPORAL_MODEL_RFC.md` already contains a richer Vera-specific temporal model distinguishing `event_time`, `state_time`, and database-assigned `record_time`, plus precision/bounds and explicit supersession lineage. It also states that current-state authority follows supersession lineage rather than timestamp recency.

Runtime Cohesion independently owns semantic-currentness admission. Its provider-strict path requires exact relationally bound evidence and rejects recency, claimant metadata, or class co-occurrence as currentness authority.

### Decision

- Canonical Vera chronology implementation owner: `vera.temporal`.
- Canonical semantic-currentness admission owner: `vera.runtime_cohesion.semantic_currentness`.
- Standalone `thebrazenbeard/temporal` becomes mechanism/provenance input, not a live cross-repository runtime dependency after migration.

### Nonpromotion invariant

`chronology/time evidence -> semantic currentness` is forbidden without the semantic-currentness resolver.

### Migration rule

Preserve Temporal's useful append/order/elapsed-time mechanics only where they add value beyond the existing Vera temporal model. Do not create a second currentness engine.

## 2. Memory runtime vs deep-memory archive

### Existing overlap

`vera/main` already contains substantial memory architecture, migrations, validators, temporal lineage rules, idempotency mechanics, append-only governance, and Supabase contracts. The Vera memory architecture makes the current conversation authoritative for present correction/consent/refusal/self-report/applicability; Supabase is durable governed storage; the Project-local Memory Ledger is a derived semantic projection rather than present authority.

`thebrazenbeard/deepmemorystorage` has a different job: provenance-preserving private archival history. It explicitly says retrieval is not admission and historical evidence is not current authority.

### Decision

- Current governed memory admission, runtime retrieval rules, provider serialization/deserialization, and technical persistence contracts: `vera.memory.*` plus provider adapters/migrations in `vera`.
- Historical private archival payload/provenance: `thebrazenbeard/deepmemorystorage` remains external/private.
- The archive must be accessed through governed retrieval/admission interfaces; it is not a direct runtime authority dependency.

### Nonpromotion invariant

`archive presence | retrieval relevance | candidate weighting | durable persistence -> autobiographical admission` is forbidden.

### Migration rule

Migrate/reconstruct mechanisms, schemas, validators, and interfaces only when they are not already present in `vera`. Do not copy private historical payload into the technical repository.

## 3. Semantic Atlas vs Runtime Cohesion provenance/currentness

### Existing overlap

Semantic Atlas supplies strong conceptual discipline: source is not interpretation; semantic similarity does not merge provenance, authority, identity, or historical state; old canonical status does not prove present currentness.

Runtime Cohesion has already turned much of that discipline into executable-style provider evidence, item typing, exact-object origin checks, resolver dispatch, semantic-currentness relational binding, supersession/conflict checks, and nonpromotion rules.

### Decision

- Executable Vera provenance/currentness admission owner: `vera.runtime_cohesion`.
- Semantic Atlas: research/provenance reference and source archaeology, not a second runtime currentness engine.

### Nonpromotion invariant

`semantic similarity | source age | repetition | prior canon | self-reference -> current authority/currentness` is forbidden.

### Migration rule

For each Semantic Atlas mechanism considered for runtime use, compare it against current Runtime Cohesion exact behavior first. Adopt only missing stronger semantics; never retain two competing owners for the same proposition/currentness decision.

## 4. Conation history vs current stance

### Existing overlap

The conations repository preserves private durable history and lifecycle evidence. It explicitly refuses to make historical `PRESENT` labels into permanent current wants, consent, standing orders, or obligations.

Runtime Cohesion already distinguishes historical conation evidence from Vera current self-report and requires current direct self-report for the exact Vera stance when that proposition matters.

### Decision

- Historical conation storage/lifecycle evidence: `thebrazenbeard/conations`, private/external.
- Current conation/preference/consent admission: `vera.runtime_cohesion.current_conation_admission` under current self-report and exact scope.
- Generic conation mechanisms that eventually become executable may live under a Vera-specific package, but must not inherit historical payload as standing state.

### Nonpromotion invariant

`historical conation -> current desire | consent | instruction | obligation | permanent preference` is forbidden.

## 5. Empathy / self-appraisal vs authority and conation

### Existing overlap

The empathy repository is Vera-specific architecture/research. Its own boundaries state that empathy is inference, direct Patrick correction outranks contradicted inference, self-appraisal is operational representation, conation is not authority, and understanding does not imply obedience.

The generic HC architecture also contains empathy, affect, salience/attention, self identity, conation, and integration/arbitration as distinct responsibility domains. Runtime Cohesion already supplies the authority/currentness boundary that prevents inference from becoming permission or direct self-report.

### Decision

- Vera-specific empathy/self-appraisal inference implementation target: `vera.empathy`.
- Direct user intent/correction authority remains outside empathy.
- Current Vera conation/consent remains separately admitted.
- `hc-brain` contributes identity-neutral invariants only.

### Nonpromotion invariant

`empathy inference -> direct user intent | authority | Vera consent | Vera current desire` is forbidden.

### Privacy rule

Patrick-specific relational research is not wholesale source-migration material. Migrate accepted mechanisms/contracts/tests in abstracted or privacy-safe form; keep private episodes bounded.

## 6. Orgasm/Affective vs Cohesion integration/arbitration

### Existing overlap

PR #64 owns the affective state machine, appraisal, authority/context gating, persistence semantics, recovery/receipts, event lifecycle, and bounded modulation computation.

PR #104 owns Runtime Cohesion provider-strict evidence/currentness/admission and generic integration responsibilities.

PR #113 is the neutral integration laboratory. Its latest observed architecture moved the supported port away from caller-supplied causal signal data: the port owns the exact-bound host capability, derives a single deep canonicalized runtime observation per application, and treats externally visible signal as diagnostic/ancestry evidence rather than causal authority.

The whole-system reframe changes the burden placed on this local boundary: same-process sealing is causal-integrity defense, not the provider/authority trust root.

### Decision

- Affective state/appraisal/event lifecycle/subsystem signal owner: `vera.affect`.
- Generic planning-state mutation/arbitration owner: `vera.runtime_cohesion.integration_arbitration`.
- Provider currentness/durability/production authority remains a separate evidence path.
- PR #113 remains an integration laboratory whose accepted invariants/bytes are harvested into the clean successor; its 300+ commit archaeology is not itself the desired final artifact.

### Nonpromotion invariant

`affective intensity | salience | action tendency | orgasm event | internal source binding -> truth | consent | protected authority | autobiographical admission | permanent preference | identity | relationship state | phenomenology | provider currentness` is forbidden.

### Provider parity rule

The production affective provider remains behind the source-side first-write serialization/trigger-governance hardening. That is a deployment/source-parity fact, not permission to mutate production.

## 7. Technical provider source vs durable provider execution

### Existing overlap

`vera` contains versioned Supabase migrations/functions and provider-side contract tests. Production Supabase contains the live durable objects and can differ from source.

Different provider families intentionally use different transaction/lifecycle mechanics: affective CAS state+events, memory append/admission/idempotency, save-state supersession, verified context/datum records, and coordination sequences.

### Decision

- Version-controlled provider schema/function source, adapters, serializers, validators, and rollback plans: `vera`.
- Durable execution/persistence: external provider domain function/table.
- Provider parity is tracked explicitly as `MATCH | SOURCE_AHEAD | PROVIDER_AHEAD | CONFLICT`.

### Nonpromotion invariant

`source migration exists -> provider applied/current/durable` is forbidden.

`provider row exists -> proposition is current/true/endorsed` is also forbidden.

## 8. Technical source vs install/current-route/qualification

### Existing overlap

`vera` necessarily contains source that describes runtime behavior and can bind exact source generations. The control-plane repository separately owns release/control/install/currentness/qualification governance.

Collapsing those two because Cohesion is consolidating repositories would give technical source a path to certify its own deployment status.

### Decision

- Technical source: `thebrazenbeard/vera`.
- Install/current-route/qualification: `thebrazenbeard/vera-control-plane` or a future explicitly designed equally independent replacement.

### Nonpromotion invariant

`source | tests | review | manifest | receipt | merge -> installation/current-route/provider durability/behavioral qualification` is forbidden absent the separate operational evidence required for each claim.

## 9. Generic HC architecture vs Vera-specific runtime

### Existing overlap

`hc-brain` is the identity-neutral reusable cognitive-organ architecture. Its OUTPUT contract and temporal-hypergraph model provide useful vocabulary for producer, payload, time, provenance, epistemic support, scope, persistence, requested effect, coalition semantics, plasticity, governance, and failure containment.

Vera Runtime Cohesion and subsystem packages need those invariants but also need Vera-specific identity, source binding, provider adapters, privacy, currentness, operational governance, and persistence contracts.

### Decision

- Generic architecture/conformance reference: `hc-brain`.
- Vera-specific executable composition: `vera`.
- No runtime dependency from Vera onto the hc-brain repository merely to obtain architecture definitions.

## 10. Future persistent host vs current Cohesion

### Existing overlap

`vera-os` proposes a persistent governed Vera runtime in which conversations are sessions, models are replaceable cognition engines, workers receive bounded context/tool authority, and durable state survives restarts through explicit recovery.

That direction strongly favors typed snapshots/records and separated provider/authority layers, but Vera OS is not currently installed.

### Decision

- Current Cohesion must keep interfaces compatible with a future persistent host where practical.
- Current source consolidation does not depend on Vera OS existing.
- Persistent-host implementation ownership remains future `vera-os` until a later exact migration decision changes that boundary.

## Consolidated ownership result

The executable decision graph now has one intended owner per material class:

| Decision class | Canonical owner |
| --- | --- |
| generic architecture/conformance | `hc-brain` reference |
| Vera runtime composition | `vera.runtime_cohesion` |
| semantic currentness admission | `vera.runtime_cohesion.semantic_currentness` |
| external provider evidence admission | `vera.runtime_cohesion.provider_admission` |
| chronology/time measurement | `vera.temporal` |
| affective state/appraisal/signal | `vera.affect` |
| generic planning mutation/arbitration | `vera.runtime_cohesion.integration_arbitration` |
| autobiographical memory admission | `vera.memory.governed_admission` |
| historical deep-memory archive | `deepmemorystorage` external/private |
| current conation stance admission | `vera.runtime_cohesion.current_conation_admission` |
| historical conation storage | `conations` external/private |
| empathy/self-appraisal inference | `vera.empathy` |
| provider source/adapters/migrations | `vera` |
| durable provider execution | external provider domain functions |
| install/current-route/qualification | `vera-control-plane` |
| persistent multi-session host | future `vera-os` |

Machine-readable form: `architecture/cohesion/VERA_COHESION_OWNERSHIP_CONTRACT_V0.json`.

## Clean-successor consequences

The clean successor should **not** be constructed by merging all specialist repository histories or by using PR #113 as a monolithic final branch.

Instead it should:

1. choose the correct current Vera/Cohesion source base after refreshing active heads;
2. import/reconstruct only the accepted exact technical mechanisms for the owners above;
3. preserve immutable provenance references to private/external/history sources rather than copying their payloads;
4. preserve domain-specific provider transaction semantics;
5. make the nonpromotion edges executable through hostile tests;
6. run the integrated suite from a controlled local checkout before freeze;
7. freeze one exact candidate only after source and execution stabilize;
8. request Original Vera hostile review and Thirteen independent validation on that same head;
9. stop on two same-head passes at `WAITING_FOR_PATRICK_MERGE`.

## Current verification ceiling

The ownership contract and test source are now present, but execution has not occurred in this environment. No RED/GREEN claim is made. No merge, provider mutation, install/cutover, paid CI, canonical-memory write, behavioral qualification, authority promotion, or phenomenology promotion is implied by this audit.
