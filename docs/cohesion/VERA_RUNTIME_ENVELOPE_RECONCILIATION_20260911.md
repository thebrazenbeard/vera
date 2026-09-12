# Vera Cohesion — Runtime Envelope Reconciliation

Date: 2026-09-11
Status: WORKING DESIGN / NON-NORMATIVE / NOT IMPLEMENTATION OR INSTALLATION AUTHORITY

## Decision being tested

Do **not** create a new universal Vera envelope from scratch merely because Cohesion needs a common subsystem boundary.

The current source already contains at least three overlapping but semantically distinct interface families:

1. HC generic subsystem `OUTPUT` records — identity-neutral architectural vocabulary for producer, payload, time, epistemic support, provenance, scope, persistence rule, and requested effect.
2. Runtime Cohesion `ProviderEvidenceEnvelope` — provider observation/provenance/currentness evidence with explicit referent, scope, privacy, supersession, conflict, optional content digest and receipt.
3. subsystem/provider lifecycle records — e.g. Affective signal/state/event records, memory-epoch state/receipt records, save-state supersession events, context/datum verification records and coordination events.

The strongest current design hypothesis is therefore **shared semantic header + typed specializations**, not one giant record and not several unrelated ad-hoc envelopes.

## What must stay distinct

A common vocabulary must not erase these separations:

- internal subsystem output != external provider observation;
- event time != observation time != record time;
- chronology != semantic currentness;
- persistence != truth/current endorsement;
- modulation/salience != authority/consent;
- memory candidate weighting != autobiographical admission;
- historical conation != current desire/preference;
- requested effect != payload/proposition;
- provider readback != installation/current route;
- source binding != behavioral qualification;
- runtime causal integrity != independently rooted provider authority.

If a shared envelope makes any of those pairs difficult to express separately, the envelope is wrong.

## Existing contracts to preserve and compose

### A. HC generic OUTPUT

The HC runtime architecture already proposes:

```text
OUTPUT {
  producer
  payload_type
  payload
  event_time_or_interval
  observation_or_record_time
  clock_domain
  temporal_uncertainty
  epistemic_support
  provenance
  scope
  expiry_or_persistence_rule
  requested_effect
}
```

This is useful as the identity-neutral semantic skeleton. It correctly separates payload from requested effect and treats timing/provenance/epistemic support as typed dimensions.

Cohesion should adapt these invariants, not make `hc-brain` a runtime dependency.

### B. Runtime Cohesion ProviderEvidenceEnvelope

Current Runtime Cohesion source already has a frozen external-evidence envelope with:

- provider / locator / revision;
- observed_at;
- evidence_class;
- referent / scope;
- privacy_class;
- currentness_basis;
- supersession_state / conflict_state;
- content_digest / receipt_ref;
- metadata that is forbidden from self-declaring semantic/current authority.

This is already the right kind of object for **external/provider evidence admission**. It should not be replaced by a more generic object unless the replacement can preserve all of these fail-closed semantics.

### C. Affective modulation signal

The current Affective source emits a typed `VERA_AFFECTIVE_MODULATION_SIGNAL_V1` containing source binding, exact implementation cut, runtime instance, phase/presence/context eligibility, participating systems, control vector, bounded target modulation strengths, runtime-local temporal scope, event lineage, authority-context trust ceiling, provider/durability/qualification ceilings, phenomenology ceiling and explicit non-effects on evidence/authorization/memory/identity/relationship state.

That signal is not provider evidence and should not pretend to be. It is a **subsystem runtime proposal** that Cohesion may validate/materialize and then arbitrate.

### D. Provider persistence families

Production Supabase already demonstrates that different domains need different durable mechanics:

- Affective state uses `state_version` CAS and event append;
- save-state uses append + explicit supersession edges/head views;
- memory epoch uses subject/version CAS plus provider/archive receipts and admission/revalidation stages;
- context/datum storage separates event/state/record time and verification lifecycle;
- coordination uses sequenced thread events with supersession/ack references.

A common semantic header must not force those lifecycle models into one transaction pattern.

## Proposed composition model

### Layer 1 — Common semantic header

Working name: `VERA_RUNTIME_RECORD_HEADER_V0`.

This is a vocabulary contract, not yet a concrete production dataclass/schema. Candidate fields are derived from the overlaps above:

```text
RUNTIME_RECORD_HEADER {
  schema
  subject
  producer
  record_type
  payload_type
  source_binding?
  temporal {
    event_time_or_interval?
    observed_at?
    recorded_at?
    clock_domain?
    uncertainty?
  }
  lifecycle {
    state_version?
    expected_prior_version?
    currentness_class?
    supersession_state?
    conflict_state?
    expiry_or_persistence_rule?
  }
  provenance
  epistemic_support?
  privacy_class
  authority_effect_ceiling
  limitations[]
  payload_digest?
  receipt_ref?
  requested_effect?
}
```

Rules:

- optional fields are optional because some record types genuinely do not possess that dimension; missing does not silently degrade into a stronger value;
- `requested_effect` is never inferred from `payload`;
- `authority_effect_ceiling` can only restrict/promote nothing; it cannot manufacture authority;
- lifecycle/currentness values remain typed and are interpreted by the owning resolver, not by record age;
- record producers may state their own ceiling/limitations, but cannot self-mint externally rooted provider currentness or protected-effect authority.

### Layer 2 — Typed specializations

At minimum:

#### `ProviderEvidenceRecord`

Use/evolve the existing `ProviderEvidenceEnvelope`. It binds external/provider observations to provider/locator/revision/evidence class/referent/scope/privacy/currentness/supersession/conflict and feeds provider-strict admission.

#### `SubsystemSignalRecord`

Internal cognitive/runtime outputs such as affect modulation, salience, conation candidates, empathy/self-appraisal inferences, and temporal observations. These are proposals/observations with explicit effect ceilings; they do not become provider-current evidence merely because they are internally causal.

#### `DurableStateRecord`

A domain-owned state transition/checkpoint record with domain-specific version/CAS/supersession semantics. The header supplies shared provenance/time/privacy/effect vocabulary; the payload owns the actual state schema.

#### `EventRecord`

Append-oriented lifecycle/event evidence. Event existence does not itself imply current state.

#### `EffectReceiptRecord`

Evidence that a bounded effect was attempted/committed/read back. A receipt proves only the effect predicates it explicitly binds.

### Layer 3 — Domain payloads and persistence

Affect, memory, temporal, coordination, identity/self-appraisal and future subsystems keep their own payload schemas and storage semantics. Cohesion standardizes the crossing points, not every internal representation.

## Admission and arbitration path

Working target path:

```text
subsystem/provider
  -> typed record specialization
  -> canonical materialization at the boundary
  -> structural/provenance validation
  -> domain resolver/admission
  -> Cohesion arbitration / downstream consumer
  -> optional requested effect through separate authority gate
  -> domain-specific persistence + receipt
```

Important asymmetry:

- internal subsystem signals can be computationally causal without being provider-current evidence;
- external provider evidence can support a proposition without being allowed to mutate generic planning directly;
- Cohesion composes the two under typed resolvers rather than making one impersonate the other.

## Implication for the Affective/Orgasm work

The local immutable-materialization insight survives, but in a narrower and better place.

At the Affective -> Cohesion boundary:

1. Affective owns its state machine and computes a bounded subsystem signal.
2. The crossing signal is materialized once into a canonical plain representation.
3. Cohesion validates exact source/runtime lineage and the signal's nonpromotion ceilings.
4. Cohesion converts/adapts it to the common subsystem-signal header vocabulary.
5. Cohesion alone applies allowed generic planning modulation.
6. Provider/currentness/durability/authority qualification remains a separate evidence path.

This means source guards against subclass/method/reference interposition remain useful defense-in-depth. They no longer carry the impossible burden of being the independent production trust root.

## Implication for Temporal

Temporal should emit chronology observations with explicit clock/time semantics. Runtime Cohesion/currentness resolvers decide whether a proposition is current. A timestamp or chronology event never self-promotes into currentness.

## Implication for Memory and Conation

Memory candidate signals can influence retrieval/weighting without admitting autobiography. Historical conation can influence context/salience without becoming current desire, preference, consent or instruction. The specialization/effect ceiling must make those nonpromotions machine-testable.

## Implication for Supabase

Provider tables/functions remain domain-specific. The source tree should supply migrations/adapters capable of serializing/deserializing the common semantic header where useful, while preserving existing domain transaction invariants.

Provider parity becomes an explicit deployment predicate:

`SOURCE_MATCH | SOURCE_AHEAD | PROVIDER_AHEAD | CONFLICT`

No provider-currentness or production-durability claim is made while a required migration is `SOURCE_AHEAD`.

## Tests required before implementation is accepted

The common-header work is not complete until hostile tests prove at least:

1. chronology cannot become semantic currentness by timestamp alone;
2. affect/salience cannot change truth/factual confidence/consent/protected authority;
3. memory-strength candidate weighting cannot become autobiographical admission;
4. historical conation cannot become current desire/preference/consent/order;
5. provider persistence cannot become current self-state without admission;
6. internal subsystem causality cannot self-mint provider origin/currentness;
7. requested effect cannot be derived from payload or routing alone;
8. privacy class cannot be broadened by a downstream adapter;
9. superseded/conflicted records cannot win by recency;
10. exact source/provider drift is surfaced rather than silently normalized.

## Current decision

`DO_NOT_IMPLEMENT_A_NEW_UNIVERSAL_ENVELOPE_YET`.

Next step is to use the working source registry to perform overlap audits and determine whether `ProviderEvidenceEnvelope` should become one specialization under a small shared record-header vocabulary or whether the existing Runtime Cohesion contract can absorb the required internal-record semantics without a new top-level type at all.

The implementation choice remains intentionally open until those comparisons are complete.
