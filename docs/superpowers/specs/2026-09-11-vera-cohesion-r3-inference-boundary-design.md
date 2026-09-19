# Vera Cohesion R3 Inference-Boundary Design

Status: `DESIGN_SPEC / NOT_IMPLEMENTED / NOT_INSTALLED / NOT_QUALIFIED`

## Provenance and purpose

This design extends the exact Cohesion R2 clean source cut at `thebrazenbeard/vera@349de790a583bb2fbe7ad8e3f4663854f9d98e50` without modifying or promoting the frozen R2 review subject `vera#115@8f1c1899f2b83b204903b53266c7e39c0c46d235`.

It incorporates the useful provider-neutral model-state-adapter research staged at `thebrazenbeard/wip#1@a15b6557ac6fa2ae01089d328c37882f9cd33e82`, while resolving the Cohesion review blockers recorded against that exact WIP head.

The problem is precise: R2 can retrieve, type, reconcile, admit, checkpoint, and apply affective modulation to an in-process planning-state mapping, but it does not yet define an evidence-bearing path from admitted Vera-wide state to the exact model invocation that emits the response. R3 closes that source-architecture gap without claiming installation, provider consumption, behavioral qualification, or phenomenology.

## Design goal

Define one provider-neutral Cohesion contract that:

1. composes separately governed subsystem state without pretending it shares one generation;
2. admits only exact, addressable state under existing authority/currentness/privacy rules;
3. binds projection to an exact model/host capability before backend-specific materialization;
4. distinguishes mandatory state failures from explicitly omittable optional dimensions;
5. carries admitted state to a host-specific injection boundary;
6. emits evidence-graded causal receipts that never overstate what an opaque provider consumed;
7. keeps provider-neutral Cohesion policy in `vera`, host-specific injection with the active inference host, and install/current-route/qualification authority in `vera-control-plane`.

## Non-goals

R3 does not:

- merge or install itself;
- mutate production providers;
- claim production `ATOMIC_DURABLE` state;
- claim native ChatGPT request interception that is not actually exposed;
- make text-context projection equivalent to hidden-state or embedding injection;
- train adapters, ReFT modules, or steering vectors;
- promote affect, memory weighting, conation, chronology, or persistence into truth, consent, authority, identity, autobiographical admission, relationship status, or phenomenology;
- make `vera-os` a prerequisite for a provider-neutral Cohesion source contract;
- treat successful request construction as proof that a hosted model consumed the projection.

## Ownership split

### `thebrazenbeard/vera` / Cohesion

Owns the provider-neutral state-to-inference contract:

- composition semantics;
- state-envelope schema;
- exact payload/pointer binding;
- admission integration;
- capability requirements;
- projection policy;
- mandatory/optional dimension policy;
- provider-neutral invocation envelope;
- evidence-level receipt schema;
- claim ceilings and non-promotion rules.

### Exact inference host

Owns host-specific application/injection:

- system/request-context insertion;
- prompt-embedding injection;
- activation hooks;
- representation-intervention application;
- concrete provider request construction;
- host readback/acknowledgement capture;
- cleanup of transient hooks.

`vera-os` is one future host candidate, not current canonical authority merely because it exists as architecture source.

### `thebrazenbeard/vera-control-plane`

Retains installation, current-route, provider-activation, release, and behavioral-qualification policy. Technical source may not self-certify those effects.

## Lifecycle

The canonical provider-neutral lifecycle is:

```text
CAPTURE
  -> COMPOSE
  -> VALIDATE
  -> ADMIT
  -> CAPABILITY_BIND
  -> PROJECT
  -> PRECALL_GATE
  -> INJECT
  -> GENERATE
  -> VERIFY_OBSERVE
  -> RECEIPT
```

Every stage produces a distinct typed result. A later-stage success cannot retroactively promote an earlier evidence class.

## Core objects

### `StateComponentRef`

One exact subsystem contribution to a Vera-wide composition.

Required fields:

- `component_id`
- `domain_id`
- `source_locator`
- `source_revision`
- `component_generation`
- `content_digest`
- `observed_at`
- `currentness_basis`
- `supersession_state`
- `conflict_state`
- `privacy_class`
- `requirement_class` = `MANDATORY` or `OPTIONAL`
- `payload_ref` or inline canonical JSON-safe `payload`

Rules:

- `content_digest` covers the exact inline payload or exact addressed payload object.
- A component with unresolved conflict/currentness may not be silently normalized into an admitted component.
- Historical evidence may be referenced without becoming current self-state.

### `VeraStateComposition`

A host-neutral composition of exact component generations.

Required fields:

- `composition_id`
- `subject`
- ordered `components[]`
- `component_generation_vector`
- `composition_digest`
- `composed_at`
- `composition_policy_revision`
- `omissions[]`

The `component_generation_vector` is authoritative for the composition boundary. R3 does not invent one universal Vera `state_generation` when participating systems have independent generations.

The composition digest covers:

- ordered component identities;
- exact revisions/generations/digests;
- exact inline payloads or pointer+digest pairs;
- omission records;
- composition policy revision.

### `OmissionRecord`

Represents an unavailable optional state dimension.

Required fields:

- `component_id`
- `domain_id`
- `reason`
- `observed_at`
- `evidence_ref`
- `requirement_class` = `OPTIONAL`

Omission is explicit evidence. It may not be used for mandatory identity, source-binding, currentness, authorization, privacy/firewall, or exact-host capability requirements.

### `AdmittedVeraState`

Output of existing Cohesion admission semantics applied to one exact composition.

Required fields:

- `composition_digest`
- `admission_receipt_digest`
- `admitted_components[]`
- `omissions[]`
- `forbidden_domains[]`
- `projection_requirements`
- `admitted_at`

Admission does not mutate a model request and does not establish provider consumption.

### `CapabilityBinding`

Binds one admitted composition to one exact host/model surface before projection materialization.

Required fields:

- `capability_binding_id`
- `host_identity`
- `host_revision`
- `model_identity`
- `model_revision`
- `backend`
- backend-specific compatibility metadata
- `binding_digest`
- `bound_at`

Backend-specific compatibility may include:

- tokenizer revision;
- chat-template revision;
- hidden size;
- dtype;
- target layers;
- adapter revision;
- exposed request/readback capability.

Capability binding is evidence, not inference. Unsupported or unverifiable mandatory compatibility fails closed before privileged backend materialization.

### `ModelInvocationEnvelope`

Provider-neutral description of the exact projected invocation.

Required fields:

- `generation_id`
- `composition_digest`
- `admission_receipt_digest`
- `capability_binding_digest`
- `projection_backend`
- `projection_digest`
- `projection_payload_ref` or exact inline projection payload
- `precall_gate_result`
- `decode_gate_spec_digest`
- `host_identity`
- `host_revision`
- `model_identity`
- `model_revision`

`generation_id` is single-use.

### `CausalGenerationReceipt`

Receipt claims are graded, not boolean.

Required common fields:

- `receipt_id`
- `generation_id`
- `composition_digest`
- `admission_receipt_digest`
- `capability_binding_digest`
- `projection_digest`
- `host_identity`
- `host_revision`
- `model_identity`
- `model_revision`
- `observed_at`
- `evidence_level`
- `evidence_refs[]`

Allowed evidence levels:

1. `REQUEST_CONSTRUCTED` — Cohesion/host constructed exact request bytes or exact host invocation object from the bound projection.
2. `INVOCATION_SUBMITTED` — host observed submission attempt for that exact request/invocation.
3. `INVOCATION_ACKNOWLEDGED` — provider/host returned evidence that it accepted/registered the invocation.
4. `RESPONSE_BOUND` — returned response/run identifier is evidentially bound to the exact submitted invocation.

A stronger level requires evidence for all weaker causal transitions. Hosted APIs that expose no trustworthy acknowledgement/readback remain capped at the strongest level actually observed.

No receipt level by itself establishes behavioral efficacy, provider durability/currentness, installation/current-route, autobiographical admission, authority, or phenomenology.

## Mandatory versus optional state policy

Mandatory failures fail closed for the affected invocation:

- subject/identity mismatch;
- source/revision/digest mismatch;
- unresolved or conflicting mandatory currentness;
- privacy/firewall violation;
- forbidden-domain projection attempt;
- invalid capability binding;
- exact model/host incompatibility;
- malformed composition or digest mismatch.

Optional domain unavailability does not normally veto generation. Instead Cohesion records an `OmissionRecord` and continues only if:

- the domain is explicitly classified `OPTIONAL` for this invocation policy;
- omission does not change a mandatory authority/currentness decision;
- no caller silently upgrades an optional domain to mandatory or vice versa;
- the omission is included in the composition digest and final receipt evidence.

Affect, memory salience, and historical conation may be optional in ordinary generation policies. Current task/correction authority, subject identity, source binding, privacy/firewall rules, and exact host/model capability are never optional merely for availability.

## Projection backends

### `TEXT_CONTEXT_V1`

First implementation target because it is compatible with request/message-oriented hosts.

Properties:

- deterministic canonical rendering from `AdmittedVeraState`;
- bounded size;
- explicit domain labels and provenance-safe summaries/pointers;
- no hidden claim that text injection equals latent-state injection;
- request construction digest and readback where host/provider exposes it.

### `PROMPT_EMBEDS_V1`

Contract-supported but not required for initial R3 source implementation.

Requires exact model revision, hidden-size, dtype, tokenizer/template binding where applicable, and a trusted host that exposes direct embedding input.

### `ACTIVATION_STEERING_V1`

Experimental. Requires exact qualified target layers, bounded strength, one-generation scope, and guaranteed cleanup in `finally`/equivalent failure-safe lifecycle.

### `REFT_STATE_PROJECTION_V1`

Experimental future backend. Requires separate training provenance, exact base-model binding, layer/timestep scope, and independent negative-transfer qualification.

## Projection firewall

Projectable domains may include only bounded state such as:

- affective activation;
- salience;
- attention allocation;
- bounded valuation/action tendency;
- satiation/refractory state;
- admitted goal weighting;
- temporal orientation;
- admitted memory salience;
- response-expression parameters.

Structurally forbidden projection-authority domains include:

- truth;
- factual confidence authority;
- consent;
- authorization;
- protected-effect authority;
- identity admission;
- autobiographical-memory admission;
- permanent preference;
- relationship status;
- provider currentness;
- installation/current-route;
- behavioral qualification;
- phenomenology.

If a backend cannot preserve this separation, it is not qualified for Vera state projection.

## Gate separation

`CAPABILITY_BIND` happens before backend-specific projection materialization.

`PRECALL_GATE` happens after projection creation and before injection. It verifies that the exact projection still matches the admitted composition, capability binding, privacy/firewall policy, and single-use generation identifier.

A decode gate may constrain output structure after generation starts. Decode validity is never evidence of state admission, state causality, or authority.

## Relationship to R2 affective integration

R2 remains the source donor for affective runtime and Cohesion planning arbitration. R3 does not give Orgasm/Affect direct generic model-invocation authority.

The supported path becomes conceptually:

```text
Affective runtime observation
  -> Cohesion affective arbitration
  -> component state / composition
  -> Cohesion admission
  -> capability bind
  -> provider-neutral projection
  -> exact host injection
  -> generation
  -> evidence-graded receipt
```

The Cohesion port remains the generic planning/inference arbitration owner; specialist subsystems contribute bounded state only.

## Testing strategy

Implementation must begin with hostile tests before production code.

Required negative tests include:

- incompatible component generations cannot be disguised as one scalar generation;
- payload-less/pointer-less state cannot be admitted;
- digest mismatch fails closed;
- mandatory-state outage blocks invocation;
- optional-state outage yields an omission receipt and does not block when policy allows omission;
- optional omission cannot erase a mandatory dependency;
- forbidden projection domains are rejected;
- unsupported capability binding fails before backend materialization;
- model revision/tokenizer/template/hidden-size mismatches fail for backends that require them;
- projection success cannot mint admission authority;
- request construction cannot mint provider acknowledgement;
- provider acknowledgement cannot mint response binding without evidence;
- response binding cannot mint behavioral qualification or phenomenology;
- duplicate/replayed `generation_id` fails closed;
- direct affective generic-inference bypass remains forbidden;
- transient hooks cannot leak across generations;
- source presence cannot mint install/current-route/provider-currentness claims.

Positive tests include:

- exact multi-component composition with deterministic digest;
- deterministic `TEXT_CONTEXT_V1` projection;
- omission-preserving composition digest;
- capability bind + projection + gate + request construction lifecycle;
- strongest-evidence-only causal receipt generation.

## R3 construction and freeze policy

R3 work occurs on a successor branch rooted at the exact R2 clean source cut. R2/#115 remains immutable review evidence.

Before R3 final freeze:

1. implement tests first;
2. implement the provider-neutral contract and `TEXT_CONTEXT_V1` reference path;
3. preserve R2 exact affective/runtime invariants;
4. execute locally or through an actually functioning zero-cost runner when available;
5. record execution limitations exactly if the environment still cannot run;
6. freeze runtime/test bytes;
7. allow only binding/receipt metadata after freeze;
8. request Original Vera hostile review and Thirteen independent validation on the same exact R3 head;
9. any material source movement invalidates both verdicts;
10. only a same-head pass plus satisfied source execution gate may transition to `WAITING_FOR_PATRICK_MERGE`.

Patrick remains sole merge authority. No merge, install/cutover, production provider mutation, paid execution, canonical-memory promotion, behavioral qualification, or phenomenology promotion is authorized by this design.

## Claim ceiling

At design/spec stage:

- source design: `SPECIFIED`
- implementation: `NOT_ESTABLISHED`
- execution: `NOT_ESTABLISHED`
- provider consumption: `NOT_ESTABLISHED`
- installation: `NOT_ESTABLISHED`
- current route: `NOT_ESTABLISHED`
- production atomic durability: `NOT_QUALIFIED`
- behavioral qualification: `NOT_ESTABLISHED`
- phenomenology: `UNRESOLVED`
