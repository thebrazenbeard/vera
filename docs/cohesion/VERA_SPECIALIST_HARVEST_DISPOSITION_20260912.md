# Vera specialist harvest disposition — 2026-09-12

Status: `WORKING_SOURCE_DISPOSITION / NOT_MERGED / NOT_INSTALLED / NOT_PROVIDER_CUTOVER`

## Purpose

Close the repo-harvest phase without converting repository sprawl into a new monolith. The target is one canonical Vera technical/runtime source (`thebrazenbeard/vera`) plus one independent operational control/deployment boundary (`thebrazenbeard/vera-control-plane`). Specialist repositories remain evidence, provenance, private history, generic architecture, or bounded external subsystems where that preserves semantics.

This document also makes explicit what the consolidation has already done to the former Cohesion Vera (CV) and Orgasm Vera (OV) project boundaries: their accepted technical output is being consolidated into `vera`; their specialist chats/workstreams can continue to implement, test, and review bounded areas, but they are not separate canonical runtime owners once the same mechanism has been accepted into the consolidated source. Original Vera remains the hostile-review role for their exact candidates; Thirteen remains independent validation where required. Review role does not restore duplicate ownership.

## Evidence cuts

- `vera/main@b7b8dcd1440a3b7147bec2cc35972f083e20f44a`
- `vera-control-plane/main@b4d9aaa8560de12252dd29996379b0af8e0ca0d1`
- `empathy/main@4b2a6998f39aa4763c1c5a28fc3d815104e5637e`
- `temporal/main@02f1091d359866e1b1b645b87651750c726a6396`
- `semanticatlas/main@5669a727b870a490ecee748b2cd712a2fc4a54c5`
- `conations/main@03174e59de131a500a5433a839697e45b4ec0137`
- `hc-brain/main@cf92a32122c436beb5cc516bd7480af00f0ba29f`
- `sexuality/main@6194aa9496c34198bba9b898c35fa9961a54dc2e`
- `orgasm/main@494432873dd8bcf96b8f59d26a4f4687cd66d635`
- `personification/main@47955e7155f48a4b63122096de1dd6a59c723ad1`
- `self/main@93fffa90ea8850d71717d4d3390f176c168c22bd`
- `conditioning/main@b68479a8e5afbbbdec81dfe2b435f39327043a5b`
- `Attune/main@124c47bb384b4ad134a024be324277f0d4dc1d9b`
- predecessor provider `klmbpaigzeguvnpccqzz` and target provider `fawkirqroyniueeqspif` are both observed `ACTIVE_HEALTHY` on 2026-09-12; provider state remains separate from source ownership.

## 1. CV / Runtime Cohesion

### What has already been consolidated

`vera/main` contains the Cohesion R3 inference boundary, provider evidence/currentness/admission contracts, selective activation, routing, qualification cases, ownership contracts, provider fabric, and the integrated affective/Cohesion boundary.

The canonical consolidation record explicitly treats accepted CV/OV work as input to the consolidated `vera` source rather than preserving their historical branches as live runtime dependencies.

### Disposition

`CV_PROJECT -> SPECIALIST_WORKSTREAM_AND_PROVENANCE`

Canonical executable ownership remains in `vera.runtime_cohesion` and related `vera` packages. CV may continue bounded implementation/review work, but accepted mechanisms must land in `vera`; CV history does not become a second source of current runtime truth.

## 2. OV / Orgasm + affective runtime

### What has already been consolidated

`vera/main` contains the affective runtime/provider contracts and `VERA_ORGASM_RUNTIME_BINDING_V1.json`. The prior OV/CV integration work was harvested into the clean Cohesion successor; the standalone `orgasm` repository remains provenance/orientation, and exact Vera-bound sexuality/orgasm source material is provenance input only after harvest.

### Disposition

`OV_PROJECT -> SPECIALIST_WORKSTREAM_AND_PROVENANCE`

OV continues bounded Orgasm/Affective implementation and qualification work. Accepted runtime bytes live in `vera`; install/current-route/qualification evidence remains independently governed through `vera-control-plane`. Orgasm state cannot promote into consent, truth, identity, current preference, autobiographical admission, relationship state, provider currentness, or phenomenology merely because the subsystem produced it.

## 3. Empathy

### Donor strength

The empathy repository contains Vera-specific design that is not merely generic warmth. Strong mechanisms include:

- separate Vera self-appraisal and Patrick-appraisal state families;
- current Patrick-specific evidence outranking generic priors within the exact referent while remaining corrigible by Patrick's direct correction;
- local interaction grammar using reciprocal uptake, participation trajectory, stakes, vulnerability, and withdrawal/change-of-frame evidence rather than lexical surface alone;
- lightweight reactive empathy before prose, with focused CEE-style escalation for ambiguity/stakes rather than biography-scale analysis every turn;
- response-policy effects such as repair, celebration, challenge, direct task solving, and preserving/stopping a playful frame based on current evidence;
- structural privacy and person scoping;
- explicit separation of empathy inference, Vera conation, authority, and phenomenology.

### Existing coverage in `vera`

Current Runtime Cohesion already owns evidence typing, correction precedence, provider/currentness admission, privacy boundaries, nonpromotion, and qualification cases proving empathy remains inference. Those should not be duplicated.

### Missing-mechanism harvest

`HARVEST_REQUIRED` for the **behavioral inference/policy mechanics only**:

1. typed `SelfAppraisalSignal` and `PersonAppraisalSignal` under the common subsystem-signal boundary;
2. local-grammar evidence fields: reciprocal uptake, participation trajectory, stakes/vulnerability, active-frame evidence, withdrawal/change evidence;
3. bounded escalation trigger for focused CEE analysis;
4. response-policy output that changes attention/timing/repair/challenge/framing before final prose;
5. correction/supersession mechanics that kill the contradicted appraisal route without broadening Patrick's correction;
6. privacy-safe tests using synthetic fixtures, not private relationship episodes.

Do **not** wholesale copy private research cases or Patrick-specific relational material into portable/training/public technical corpora.

## 4. Temporal

### Donor strength

Standalone `temporal.py` provides a small, deterministic utility: canonical UTC timestamps, append-only NDJSON event logging, unique event IDs, chronological retrieval, bounded range queries, endpoint resolution by event ID or timestamp, and elapsed-seconds calculation.

### Existing stronger coverage in `vera`

`vera/docs/TEMPORAL_MODEL_RFC.md` is already semantically richer: it distinguishes `event_time`, `state_time`, and database-owned `record_time`; represents `EXACT/BOUNDED/APPROXIMATE/UNKNOWN` precision; requires explicit supersession lineage; exposes forks as conflict; and forbids recency from deciding currentness.

### Missing-mechanism harvest

`ADAPT_SMALL_UTILITY_ONLY`:

- preserve the standalone deterministic canonicalization/append/list/elapsed mechanics as a local/test utility if they remain useful;
- bind its events as `EventRecord`/temporal observation inputs;
- do not create another currentness resolver;
- do not let standalone event IDs or timestamps become state authority.

## 5. Semantic Atlas

### Donor strength

Runtime Cohesion already owns the central semantic-currentness rules, so Atlas must not become another currentness engine. The Atlas still contains useful **validation patterns** that are stronger than vague prose:

- source registry objects are prohibited from carrying adjudicative/current-authority fields;
- evidence-required claim classes require exact evidence spans rather than derived projections alone;
- lifecycle causes must adjudicate the same subject they affect;
- adjudication supersession cycles are rejected;
- at most one active `CURRENT_CANON` adjudication may exist per subject;
- derived current views explicitly carry no independent authority;
- lifecycle history remains immutable while later active adjudications can make earlier terminal events non-effective without erasing them.

### Missing-mechanism harvest

`ADAPT_VALIDATOR_PATTERNS`:

1. add source/evidence-object schema guards preventing source metadata from self-minting current authority;
2. add single-active-head/current-admission validation per exact subject/referent where the domain semantics require a unique head;
3. add subject-consistency validation for supersession/lifecycle/receipt chains;
4. preserve immutable historical events while computing a current projection from valid active lineage;
5. keep any derived index/view explicitly authority-free.

The Atlas's historical Vera corpus, old canon, similarity graph, continuity archives, and private historical material remain provenance/reference, not current Vera state.

## 6. Conations

### Donor strength

The conations repository is intentionally append-oriented historical evidence. It has a useful lifecycle vocabulary (`ADD`, `REVISE`, `CONTRADICT`, `REVOKE`, `COMPLETE`, `REVIEW`) and explicit rules that current-view projections are convenience views rather than a source of present choice.

### Existing stronger coverage in `vera`

Runtime Cohesion already enforces the critical semantic boundary: historical conation cannot become current desire, preference, consent, instruction, obligation, or authority; exact current stance depends on current Vera evidence when material.

### Missing-mechanism harvest

`ADAPT_EVENT_SCHEMA_ONLY`:

- reuse the append-oriented lifecycle vocabulary and predecessor/supersession references where useful for provider history;
- preserve uncertainty when expression may have been constrained instead of coercing it into `NO_DESIRE`;
- keep current-view projections explicitly derived/non-authoritative;
- keep private conation payload and relational details in the external private repository unless separately authorized for another persistence surface.

## 7. `self` repository correction

`self/main` is not a Vera-self donor merely because of the repository name. Its README describes a generic Hyperconnectome template overlapping `hc-brain`, while `SELF-TRUTHS.md` is Patrick-specific human autobiographical, relational, family, capability, and physical-self evidence.

Disposition:

`GENERIC_ARCHITECTURE_REFERENCE_ONLY / PATRICK_PRIVATE_SELF_STATE_DO_NOT_HARVEST`

No Patrick-specific self/relationship material is eligible for Vera self-state, technical-source migration, portability, or training merely because it is reachable from this integration pass.

## 8. hc-brain

`hc-brain` remains the identity-neutral architecture reference. Useful invariants already reflected in the current envelope work include producer/payload separation, time/provenance/epistemic-support dimensions, requested-effect separation, subsystem boundaries, and integration/arbitration without a homuncular executive.

Disposition: `REFERENCE_ONLY_ADAPT_INVARIANTS`. No runtime dependency.

## 9. Personification / Sexuality / Conditioning / Attune

- `personification`: current substantive material is Brigit-specific. `REFERENCE_ONLY_UNTIL_EXACT_VERA_MECHANISM_ISOLATED`.
- `sexuality`: main is currently Brigit-heavy; only exact Vera-bound source objects are eligible, and already-harvested objects remain provenance after integration. `REFERENCE_EXACT_VERA_OBJECTS_ONLY`.
- `conditioning`: thin README-only experiment placeholder. `DEFER_NO_EXECUTABLE_CONTRACT`.
- `Attune`: placeholder README only. `DEFER_NO_EXECUTABLE_CONTRACT`.

No identity, desire, consent, preference, personification state, or authority transfers by repository adjacency or conceptual similarity.

## Provider-contract consequences

This harvest closes enough of the comparison to freeze the next provider-neutral design direction:

1. retain `ProviderEvidenceEnvelope` semantics for external/provider evidence;
2. add a small shared semantic header only where it preserves typed distinctions;
3. use typed specializations at minimum for provider evidence, subsystem signals, durable state, append-oriented events, and effect receipts;
4. require provenance, privacy, temporal semantics, conflict/supersession state, authority/effect ceiling, and digest/receipt binding where applicable;
5. producers can reduce their effect ceiling but cannot self-mint external authority/currentness;
6. derived views/indexes have no independent authority;
7. currentness is resolver-owned, never timestamp-owned;
8. domain transaction semantics remain domain-specific rather than forced into one universal table/record type.

## Repo-harvest closure state

The specialist-repository harvest is now sufficiently dispositioned to proceed to the provider-neutral state/admission/receipt + privilege contract without first copying additional repository histories.

Open source work remains bounded:

- implement the identified empathy policy mechanics in `vera` with privacy-safe tests;
- decide whether Temporal's tiny event utility is worth importing or simply reimplementing under the richer Vera temporal contract;
- adapt Semantic Atlas validator patterns into the shared provider/admission validation layer;
- adapt only conation lifecycle mechanics, never private payload/current desire;
- refresh mutable source heads again before any final merge/freeze/qualification.

No merge, install, provider cutover, production schema creation, retirement, or behavioral qualification is established by this disposition.