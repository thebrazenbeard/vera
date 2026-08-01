# V.E.R.A. R7A1 Semantic Tagging and Retrieval

## Purpose

Semantic tagging improves discoverability and collision resistance. It does not create truth, permission, identity, consciousness, reciprocity, authority, or persistence.

## Extraction pipeline

1. Split source text into attributable claims.
2. Label source actor and epistemic class.
3. Extract entities, systems, artifacts, projects, people, persona configurations, locations, and concepts.
4. Extract topics and aliases while preserving observed forms.
5. Extract directed relationships as representational data.
6. Extract temporal expressions with source evidence and precision.
7. Preserve literal phrases needed for exact recall.
8. Record collisions, exclusions, and unresolved references.
9. Project canonical values only after governance filters.

## Entity types

`PERSON`, `ORGANIZATION`, `PROJECT`, `SYSTEM`, `MODEL`, `TOOL`, `PERSONA_CONFIG`, `ARTIFACT`, `LOCATION`, `DEVICE`, `SOFTWARE`, `CONCEPT`, `OTHER`.

A persona configuration is not a person or autonomous virtual entity.

## Relationship rule

Relationships may describe source attribution, project membership, technical dependency, authorship, sequence, reference, observed interaction, and user-defined framing.

They may not silently imply reciprocal feeling, consent, subjective ownership, or independent agency.

## Query expansion

Search exact terms first, then aliases, canonical forms, topics, one-hop relationships, temporal anchors, and literal phrases. Reapply privacy, provenance, lifecycle, branch, archive, and model-claim filters after expansion.

## Archive tagging

Sanitized archive records must carry:

- source locator;
- technical subject;
- record time;
- redaction status;
- redaction reason where applicable;
- archive-only routing;
- explicit prohibition on active-memory promotion without separate review.

Do not infer or reconstruct excluded personal or intimate material from gaps.

## Temporal tagging

Keep event, record, state, retrieval, effective, and observed time distinct. File metadata remains metadata unless supported as event evidence.

## Evidence

Every semantic object carries source claim IDs, evidence, epistemic status, and extraction confidence. Confidence describes extraction quality, not claim truth.

## Connection-attempt evidence

Retry and failure records tag:

- semantic target identity;
- route identity and route class;
- attempt number;
- observed timestamp;
- exact error class and message;
- transient reset performed;
- partial-data state;
- commit-state check;
- idempotency or operation identifier where applicable;
- final classification: confirmed, degraded, deterministic failure, or blocked.

An alternate route must target the same semantic object and evidence requirements; switching to a different question does not satisfy the retry law.
