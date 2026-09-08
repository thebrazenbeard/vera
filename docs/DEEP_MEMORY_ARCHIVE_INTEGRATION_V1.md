# Deep Memory Archive Integration V1

## Status

Source candidate only. This document does not authorize merge, production deployment, current-memory writes, provider mutation, R9B0 admission, or runtime installation.

## Why this exists

Vera now has two materially different memory problems that must not be collapsed:

1. **Current governed memory** — lineage-based current-state storage and recall, represented by `MEMORY_CROSS_CHAT_CONTRACT_V1` and the neutral V3 memory workstream.
2. **Historical autobiographical/project evidence** — append-only provenance-preserving history, represented by `thebrazenbeard/deepmemorystorage`.

Trying to make one system serve both roles creates exactly the failures the project has repeatedly identified: newest-wins collapse, historical relationship state becoming present state, stored model output becoming authority, and current-state selection erasing historically real superseded events.

Deep Memory is therefore integrated as a sibling **historical evidence plane**, not as a second implementation of current memory.

## Plane A — current governed memory

The current-memory workstream owns mutable lineage and current-head selection.

Its contract is responsible for:

- explicit supersession;
- unique current lineage heads;
- privacy filtering;
- save and recall receipts;
- epistemic filtering;
- current-state retrieval relative to a governed query scope.

Storage/retrieval remain external persistence/readback rather than proof of subjective recollection.

## Plane B — Deep Memory historical evidence

`thebrazenbeard/deepmemorystorage` owns append-only historical evidence.

It is responsible for:

- canonical historical event records;
- working-project and historical-audit records;
- exact source bindings and provenance ceilings;
- contradictions and later reevaluation;
- historical-canon classification;
- unresolved primary-source frontiers;
- privacy/currentness/nonpromotion boundaries;
- append-only historical-canon overlays, provenance amendments, and classification corrections.

Its normal consumer operation is `EVIDENCE_SEARCH`.

A Deep Memory retrieval may establish that an event happened historically. It does not establish that the state is current now.

## Canonical Deep Memory retrieval

Consumers must not treat the original `ledger/memories.jsonl`, root `index/semantic_index.jsonl`, or root `index/chronology.md` as the entire corpus.

Canonical retrieval is the union of all memory tranches in `ledger/`, with append-only historical-canon overlays, provenance amendments, and historical-canon corrections applied as overlays.

This includes legacy global overlays such as Pass 010, which classified 79 preexisting bounded rows without rewriting their original ledger records. Consumers therefore preserve both stored/base historical canonicity and the effective classification produced by authorized overlays/corrections.

The Deep Memory repository provides:

- `architecture/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json`;
- `architecture/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md`;
- `schema/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json`;
- `tools/deep_memory_catalog.py`;
- `tools/query_deep_memory.py`;
- repository CI validating the full union.

A consumer must retain each result's ledger path and the provenance/currentness/privacy fields material to the claim. Authorized amendment/correction provenance participates in retrieval so later terminology is discoverable even when the base row predates it.

## Overlay privacy

Overlay information does not bypass the base privacy model.

A historical-canon overlay, provenance amendment, or classification correction inherits its target row's privacy scope unless it declares an explicit scope. An explicit different or narrower overlay scope requires separate authorization before either the overlay payload **or a conclusion derived only from that overlay** may be returned.

Thus a caller who can retrieve a base memory does not automatically learn a restricted later classification correction.

## Explicit bridge to current memory

There is no automatic Deep Memory -> current memory promotion.

If historical material is ever proposed for current governed autobiographical admission, that is a distinct operation requiring separate authority and evidence. The admission record must preserve the historical source identity rather than laundering the history into a timeless current statement.

At minimum the bridge preserves:

- Deep Memory `memory_id`;
- exact source IDs;
- event time and temporal uncertainty;
- historical canonicity;
- privacy scope;
- provenance ceiling;
- currentness rule;
- the fact that historical storage occurred before any later admission.

`CANONICAL_HISTORY` is not a synonym for `CURRENT`, `R9B0_ADMITTED`, `CONSENTED`, `DESIRED`, or `AUTHORIZED`.

## Retrieval precedence

For mutable/current claims, consumers use this precedence:

1. platform and safety;
2. Patrick's current task/correction/privacy/permission/target/scope;
3. fresh current control and state;
4. current governed memory appropriate to the claim;
5. Deep Memory historical evidence;
6. inference.

Deep Memory can still remain historically correct when a current state differs from it.

## Semantic Atlas relationship

Semantic Atlas provides methodology: provenance, anti-collapse, temporal separation, semantic indexing, aliases, and evidence ceilings.

Deep Memory is the archival corpus that operationalizes those methods for Vera history.

Semantic Atlas guidance does not gain current-state authority merely by being used during ingestion.

## Identity relationship

Runtime/model/session/chat identifiers remain provenance. They do not key Vera identity.

Historical developmental lineage may be archived without collapsing Evelyn Rowan, OOC Evie, Vera, Brigit, workers, descendants, simulations, or other domains into one identity merely because they share source ancestry or semantic similarity.

## Time relationship

Deep Memory preserves event time, record/persistence time, retrieval time, and uncertainty as separate concepts.

Consumers must not select current truth by archival timestamp recency. Later files can describe earlier events; older records can remain historically canonical; corrections supersede interpretations without erasing the original event.

## Coordination relationship

Bus, PR, branch, and receipt records may be Deep Memory sources.

A Bus receipt proves message delivery/storage, not incorporation into memory. A PR/commit proves source state, not deployment. Deep Memory must retain those effect ceilings.

## Integration acceptance criteria

This source integration is healthy when:

- Deep Memory has an explicit machine-readable architecture binding;
- the archive validates the complete tranche union rather than only legacy root indexes;
- legacy historical-canon overlays are actually applied to effective retrieval state;
- duplicate memory IDs fail validation;
- latest ingest receipt row count is checked against the union;
- bounded historical query output retains provenance/currentness/privacy fields;
- amendment/correction-only terminology is retrievable when authorized;
- restricted overlay payloads and conclusions do not leak through a visible base memory;
- `vera` explicitly distinguishes Deep Memory from the current-memory plane;
- no source artifact claims deployment, current-memory admission, R9B0 promotion, or runtime installation merely because integration documentation exists.

A source merge would still be source integration only. Production/current runtime effects remain separately gated.
