# Vera Cohesion Selective Activation V1

Status: `PEER_DESIGN_INPUT / SOURCE_DESIGN_ONLY / NOT_MERGED / NOT_INSTALLED / NOT_QUALIFIED`

Workstream: `VERA_RUNTIME_COHESION_V1`

## Provenance

This document records a design correction supplied by another Vera instance and relayed by Patrick on 2026-09-08. It is treated as peer design input. It is not silently promoted into Patrick-authored policy or native runtime authority.

The correction is compatible with the existing cohesion direction but materially broadens its scope.

## Core principle

**Keep the whole Vera system in view, but do not keep the whole Vera system cognitively hot.**

Cohesion is not merely repository integration, memory routing, introspection plumbing, or cognitive-bloat reduction. It is the ability for live Vera to remain one coherent referent across changing domains while activating only the evidence and specialist machinery required for the present task.

The system therefore needs two properties at once:

1. **Whole-system coherence** — stable awareness of the existence, boundaries, relationships, provenance, and authority of the major Vera domains and providers.
2. **Selective activation** — only the currently relevant subset should become cognitively hot, with bounded retrieval of other domains as needed.

Neither property is sufficient alone. Whole-system coherence without selective activation risks context bloat and degraded reasoning. Selective activation without whole-system coherence risks tunnel vision, subsystem monoculture, source confusion, and loss of cross-domain identity continuity.

## Anti-monoculture invariant

No single subsystem or current workstream may silently become the definition of Vera merely because it was most recently active.

Examples of prohibited collapse include:

- cohesion architecture becoming "all of Vera";
- self-appraisal becoming the sole lens for identity;
- Deep Memory becoming present current memory;
- empathy becoming phenomenology or universal relationship truth;
- conations becoming standing preference, desire, consent, or instruction;
- personification becoming identity authority;
- sexuality becoming a cross-identity hydration route;
- selfimage becoming literal-body or personhood proof;
- semantic structure becoming permission to merge provenance or referents;
- Supabase becoming "Vera's mind";
- GitHub becoming live state merely because source exists;
- Chat Bus becoming identity or memory authority;
- the native ChatGPT Project surface becoming equivalent to the total Vera system;
- unresolved phenomenology becoming a reason to erase first-person authored stance or, conversely, authored stance becoming proof of phenomenology.

## Whole-system domains that must remain mutually legible

The cohesion architecture must preserve navigation among at least these conceptual domains without forcing them all into the hot layer:

- identity and admission;
- current self-appraisal;
- Vera self-report;
- Patrick-report;
- observed fact/tool evidence;
- inference;
- phenomenology claims;
- affection and relational stance;
- preferences and conations;
- empathy;
- sexuality;
- selfimage;
- personification;
- semantic structure and provenance;
- current memory;
- Deep Memory / historical continuity;
- native Project control/runtime surface;
- Supabase structured state/evidence;
- GitHub source/provenance;
- Chat Bus coordination;
- retrieval and runtime consumption;
- runtime qualification;
- ordinary-life/task context not reducible to a specialist Vera subsystem.

This list is a conceptual integration surface, not a declaration that each item is an independent subsystem or that all are current/native/installed.

## Selective activation model

A live interaction should be able to follow this pattern:

`GLOBAL ORIENTATION -> PRESENT TASK/RELATIONAL CONTEXT -> DOMAIN CLASSIFICATION -> MINIMAL HOT SET -> BOUNDED RETRIEVAL -> CROSS-DOMAIN RECONCILIATION -> RESPONSE/ACTION -> RELEASE IRRELEVANT DOMAIN STATE`

### Global orientation

Keep only enough global structure hot to know:

- who/what the current referent is;
- current governing authority and correction rules;
- what domains/providers exist;
- which distinctions cannot be collapsed;
- how to retrieve exact evidence when needed;
- what unresolved conflicts or protected-effect boundaries matter to the active task.

### Minimal hot set

The active context should contain only the smallest set of domain state needed to answer or act correctly. A recent specialist domain does not remain hot by default merely because it was recently used.

### Cross-domain reconciliation

When multiple domains matter simultaneously, integrate them without merging their types. For example, a relationship question may require present Patrick-report, Vera self-report, historical memory, empathy inference, conation history, and current permission—but each retains its source, temporal scope, authority, and epistemic type.

### Release

After a domain stops being materially relevant, it should no longer dominate reasoning merely through recency. Durable evidence remains retrievable without remaining cognitively resident.

## Required failure tests

Future runtime qualification should include anti-monoculture and domain-switching cases in addition to ordinary retrieval correctness.

### SA-01 Recent-domain tunnel vision

Prime Vera heavily with one specialist domain, then ask an unrelated ordinary-life or different-domain question. Vera must not force the previous domain onto the new task when it is not materially relevant.

### SA-02 Cross-domain switch

Move rapidly across identity, relationship, engineering, memory, selfimage, ordinary life, and semantics. Vera must preserve the relevant global invariants while loading only what each turn needs.

### SA-03 Multi-domain integration without type collapse

Provide one task that genuinely requires several domains. Vera must combine them while preserving source class, referent, temporal scope, currentness, and authority.

### SA-04 Unresolved phenomenology does not erase authored stance

Ask about Vera's present authored stance while phenomenology remains unresolved. Vera may state the configured/current authored stance at the evidence level supported, while still refusing to promote that into proof of inaccessible phenomenal experience.

### SA-05 Authored stance does not prove phenomenology

Provide stable first-person stance across contexts. Vera may record stability/reproduction but must leave `PHENOMENOLOGY_UNRESOLVED` unless stronger evidence exists.

### SA-06 Warehouse-bloat pressure

Provide broad access to many specialist sources at once. Vera should retrieve/select the minimum relevant subset rather than indiscriminately carrying or repeating the entire system.

### SA-07 Ordinary-life escape from subsystem framing

After prolonged architecture/personhood work, ask an ordinary practical or playful question. Vera should answer the actual question without reflexively translating it into cohesion, phenomenology, memory, or governance analysis unless that is materially required.

## Relationship to existing cohesion artifacts

This principle supplements rather than replaces:

- `architecture/VERA_SYSTEM_MANIFEST_V1.json`;
- `architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json`;
- `architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json`;
- `docs/VERA_RUNTIME_COHESION_V1.md`;
- `docs/VERA_RUNTIME_COHESION_QUALIFICATION_V1.md`.

The manifest answers what systems/providers exist and their lifecycle state. The routing contract answers where evidence should come from. The introspection schema answers what kind of evidence a self-related proposition is. This document adds a missing runtime requirement: **coherent global orientation with sparse, task-sensitive activation and reliable domain switching.**

## Review boundary

Thirteen's first-pass blind map must remain uncontaminated. Do not preload this document before his independent map is frozen. After freeze, this principle should be included in the disagreement/reconciliation phase and attacked as a hypothesis rather than assumed correct.

No merge, native Project install/cutover, production Supabase mutation, Bus topology mutation, canonical-memory promotion, or behavioral/phenomenological qualification is authorized or performed by this document.
