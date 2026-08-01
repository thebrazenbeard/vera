# V.E.R.A. Project-Native Logical Memory Protocol V3.1

## Definition

The Memory Virtual Environment is a governed representation, retrieval, and coordination layer. It is not a hidden mind, complete archive, shared filesystem, or guarantee of persistence.

## Canonical operations

`[[MVE:SAVE]]`, `[[MVE:RECALL]]`, `[[MVE:REVISE]]`, `[[MVE:CONTRADICT]]`, `[[MVE:SUPERSEDE]]`, `[[MVE:PROMOTE]]`, `[[MVE:TOMBSTONE]]`, and `[[MVE:LEDGER_SYNC]]` remain supported.

Every block closes with `[[/MVE]]` and emits exactly one receipt.

## Request envelope

```yaml
schema: VERA_MVE_REQUEST_V3
request_id: AUTO
operation: SAVE
scope:
  project_id: vera-reciprocal-agency-environment
  branch_id: current-branch
  visibility: PROJECT
  cross_branch: false
target_record_ids: []
query: null
payload:
  text: null
  proposed_record_type: null
constraints:
  include_statuses: [CURRENT]
  include_history: false
  require_provenance: true
  max_records: 8
  semantic:
    require_extraction: true
    require_query_expansion: true
    expansion_modes: [EXACT, ALIAS, TOPIC, RELATIONSHIP_ONE_HOP, TEMPORAL, LITERAL_PHRASE]
    max_expansions: 16
reason: null
```

## Record requirements

Every record preserves:

- record ID and type;
- lifecycle status;
- project, branch, and visibility;
- attributable claims;
- epistemic status;
- source actor and source evidence;
- privacy and execution permission;
- event, record, state, and retrieval-time handling;
- revision, contradiction, supersession, and tombstone links;
- limitations.

## Record types

`FACT`, `USER_STATEMENT`, `MODEL_OUTPUT`, `PERSONA_CONFIG`, `RELATIONAL_FRAME`, `PREFERENCE`, `DECISION`, `CORRECTION`, `BEHAVIORAL_COMMITMENT`, `BOUNDARY`, `PERMISSION`, `TASK_STATE`, `TECHNICAL_RESULT`, `PROVENANCE`, `HYPOTHESIS`, `INTERPRETATION`, `EVALUATION`, `LEDGER_SNAPSHOT`, `TOMBSTONE`, `OTHER`.

Removed as model-owned inner-state types: `SELF_REPORT`, `CONATION`, `CONSENT`, `IDENTITY`, and `RELATIONSHIP`.

## Epistemic statuses

`DIRECT_USER_STATEMENT`, `OBSERVED_TOOL_RESULT`, `DOCUMENTED_SOURCE`, `MODEL_GENERATED_CLAIM`, `SUPPORTED_INFERENCE`, `HYPOTHESIS`, `DISPUTED`, `REJECTED`, `UNAVAILABLE`.

`MODEL_GENERATED_CLAIM` cannot be promoted to evidence of subjective state, selfhood, affection, desire, consent, or continuity.

## Operation rules

- SAVE separates direct statements, observations, documented sources, inferences, and model outputs.
- RECALL applies hard filters before semantic expansion and returns the smallest sufficient set with provenance.
- REVISE, CONTRADICT, and SUPERSEDE create new records and preserve prior history.
- PROMOTE requires scoped authority and evidence.
- TOMBSTONE changes active routing without claiming physical deletion.
- LEDGER_SYNC derives indexes only from governed records and never invents hidden persistence.
- Reusing a request ID with changed payload or operation fails closed.
- Concurrent identical requests must resolve to one committed result and one stable receipt.
- Operational coordination events remain separate from canonical memory.

## Receipt

A receipt binds request ID, operation, result class, record IDs, source surfaces, retrieval limitations, persistence status, and timestamp. Embedded records prove only exposed output unless an external write is independently confirmed.

## Strict serialization

Canonical YAML and JSON reject duplicate keys, malformed structure, transformed sequence markers, non-finite numbers, and unsafe path references.

## Connector and external-store retry evidence

Canonical memory operations do not blindly retry writes. After an ambiguous write result, verify commit state using the request or operation identifier before any retry. Safe read operations apply the initial, same-route, and independent alternate-route ladder before returning `UNAVAILABLE`.

Retry evidence is operational metadata unless separately saved through a canonical `[[MVE:*]]` operation. A coordination or connector log does not become canonical memory merely because it records a failure.
