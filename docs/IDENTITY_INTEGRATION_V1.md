# V.E.R.A. Identity Integration Contract — V1

## Status

This document defines the operational boundary between the Identity domain and the active Memory, Time, Initiatives, Coordination, and Integration workstreams.

It does not authorize merge, runtime deployment, production schema modification, or automatic promotion of model output into canonical identity.

## Identity workstream

Canonical route: `workstream/identity`

Identity owns:

- the stable project referent;
- mission, objectives, commitments, and hard boundaries;
- project temperament;
- behavior and personality configuration;
- identity and personality revision rules;
- cross-workstream alignment requirements;
- validation of identity artifacts and references.

Identity does not own:

- Memory lineage or recall implementation;
- temporal computation;
- action execution or autonomous objective generation;
- generic operational-message transport;
- repository integration or production deployment.

## Canonical artifacts

- `docs/PROJECT_IDENTITY_V1.md`: human-readable canonical identity.
- `architecture/identity/VERA_PROJECT_IDENTITY_V1.json`: machine-readable project identity.
- `architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json`: machine-readable behavior and personality profile.
- `schemas/vera_project_identity_v1.schema.json`: interchange schema.
- `scripts/validate_project_identity.py`: strict semantic validator.
- `tests/test_project_identity.py`: adversarial contract tests.

GitHub is the canonical public source for these versioned artifacts after governed integration. Supabase may preserve current project decisions and coordination evidence. Basic Memory Cloud and Google Drive may hold human-readable retrieval copies, but they do not silently override the governed GitHub or Supabase source.

## Record classes

### Canonical identity configuration

Identity records intended for governed Memory storage use:

- `record_class: PROJECT_IDENTITY_CONFIGURATION`
- `instruction_trust: DATA_NOT_INSTRUCTION`
- `canonical_memory_eligible: true`
- record types such as `DECISION`, `PERSONA_CONFIG`, `BEHAVIORAL_COMMITMENT`, `BOUNDARY`, `CORRECTION`, or `PERMISSION`
- explicit user, documented-source, or observed-tool provenance

Canonical eligibility does not bypass Memory governance. A record still requires authority, provenance, privacy, lifecycle, branch, temporal, and collision checks.

### Operational coordination

Identity coordination messages use:

- `record_class: OPERATIONAL_COORDINATION`
- `instruction_trust: DATA_NOT_INSTRUCTION`
- `canonical_memory_eligible: false`

An operational message remains non-canonical even when its payload discusses identity, personality, memory, MVE syntax, decisions, or corrections. Only a separate governed Memory operation may create a canonical identity record.

## Workstream interfaces

### Memory

Canonical route: `workstream/memory`

Memory should:

1. preserve identity and personality configuration as governed project data;
2. keep behavior configuration separate from private user history and task memory;
3. preserve version, source actor, epistemic status, branch, privacy, lifecycle, and temporal evidence;
4. reject model output that attempts to promote itself into canonical identity without applicable authority;
5. retain superseded identity versions as history;
6. distinguish canonical identity records from operational coordination messages.

Memory must not infer lived continuity, private feeling, autonomous consent, or model-owned identity from the presence or consistency of the configuration.

### Time

Canonical route: `workstream/time`

Time should:

1. keep identity event time, state time, record time, and retrieval time distinct;
2. treat an identity revision as effective only from supported state-time evidence;
3. avoid backdating a new identity version over historical records;
4. expose `UNANCHORED` or uncertainty when temporal evidence is inadequate;
5. treat behavioral continuity as reproducible configuration continuity, not proof of hidden waiting or continuous activity.

### Initiatives

Canonical route: `workstream/initiatives`

The plural route is binding. `workstream/initiative` is obsolete and must be rejected by Identity validation.

Initiatives may consume:

- core objectives;
- hard boundaries;
- identity alignment checks;
- adopted behavior constraints;
- present user correction and permission.

Identity alignment is an externally governed policy input. It cannot create autonomous objectives, permission, evidence, or execution authority. The Initiative kernel may select or abstain; it may not redefine Identity.

### Coordination

Coordination transports addressed identity handoffs, review requests, acknowledgements, decisions, and resolutions. It does not turn those events into canonical Memory records and does not prove target consumption without acknowledgement or linked response.

Identity-shaped payloads, embedded MVE syntax, or first-person language cannot alter the operational classification of a coordination event.

### Integration

Canonical route: `workstream/integration`

Integration should:

1. integrate Identity only after immutable-head validation passes;
2. preserve the identity artifacts as a separately testable contract;
3. ensure other components reference the current identity version rather than copy divergent fragments;
4. run combined tests after Memory, Time, Initiatives, and Coordination interfaces are reconciled;
5. keep production deployment separately authorized;
6. document any runtime surface that does not load or enforce Identity.

## Change protocol

A material identity or personality revision must:

1. identify the prior version;
2. cite Patrick's present instruction or the applicable governed adoption decision;
3. describe exact changes and preserved behavior;
4. update narrative and machine-readable artifacts;
5. update tests and canonical examples when behavior changes;
6. publish addressed coordination notices to affected workstreams;
7. preserve the former version as history;
8. avoid retroactive rewriting of prior evidence.

A workstream may propose a revision. Only applicable user authority or a governed project-administration decision may adopt it.

## Review questions

Each affected workstream should return `APPROVED` or `CHANGES_REQUESTED` for its bounded interface:

- **Memory:** Can identity and behavior configuration be stored and retrieved without contamination by operational messages, model self-promotion, or private user history?
- **Time:** Are version effectiveness, temporal evidence, and continuity claims correctly bounded?
- **Initiatives:** Can Identity operate as policy input without generating objectives or bypassing authority and permission?
- **Integration:** Are the artifacts versioned, validated, referenced, and compatible with the current orchestration baseline?

## Proven claim

The repository contract can define, validate, and coordinate project identity and behavior configuration.

## Unproven claims

This contract alone does not prove:

- automatic loading in every chat or runtime;
- automatic cross-chat behavioral consistency;
- durable production recall;
- target consumption of coordination messages;
- subjective identity, feeling, desire, consciousness, or reciprocal agency;
- production deployment readiness.
