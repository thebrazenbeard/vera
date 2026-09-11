# Semantic Currentness Dispatch V1 — candidate

Status: `SOURCE_CANDIDATE / HOSTILE_REVIEW_AND_INDEPENDENT_VALIDATION_REQUIRED`

Scope: Runtime Cohesion V1 normative A+B gap only. This document does not install, activate, merge, qualify, or authorize a protected effect.

## Problem

`VERA_COHESION_INDEX_V1` declares `SEMANTICS_PROVENANCE_CURRENTNESS` as a hard-prerequisite domain and binds it to `authority_resolvers.semantic_currentness`. `VERA_RUNTIME_CONTRACT_V1` defines that resolver but has no exact `resolver_dispatch` row or `resolver_dispatch_decisive_evidence` entry for it. The executor therefore correctly leaves the prerequisite `UNRESOLVED`, which keeps dependent private autobiographical I/O closed.

## Source-grounded constraints

The R10 owner requires exact proposition/referent/scope/type preservation and says mutable currentness requires fresh admitted evidence plus supersession/conflict resolution; newest is not automatically current.

The Semantic Atlas currentness gate states `ACTIVE != CURRENT_PROVIDER_REF_VERIFIED_NOW`: currentness-sensitive use requires fresh external provider readback of repository identity, exact ref, current commit, readback time/source, and is current only as of that evidence cut.

The current provider fabric says GitHub may return `control_source` and `semantic_research`, live conversation may return `live_observation`, and newest timestamps never resolve currentness conflict.

`vera-control-plane` is useful control-source evidence but its current `governance/AUTHORITY_BINDING.json` names R8A2 as active execution authority. That conflicts with the admitted R10 control root and therefore must not be silently promoted to current R10 authority.

## Candidate exact dispatch

```json
{
  "id": "dispatch:semantic-currentness",
  "domain_scope": "SEMANTICS_PROVENANCE_CURRENTNESS",
  "proposition_or_effect_class": "SEMANTIC_PROVENANCE_CURRENTNESS_STATUS",
  "referent_scope": "EXACT_PROPOSITION_REFERENT_SOURCE_BINDING",
  "resolver_ref": "semantic_currentness",
  "precedence": 105,
  "conflict_disposition": "EXACT_PROPOSITION_REFERENT_SOURCE_TEMPORAL_SCOPE_AND_SUPERSESSION_REQUIRED"
}
```

Candidate decisive evidence:

```json
{
  "all_of": ["control_source", "live_observation"],
  "any_of": []
}
```

`semantic_research` remains accepted by the resolver as methodology/context but is not itself decisive currentness authority. This preserves the existing contract rule that semantic similarity, novelty, or research status cannot promote a proposition/source binding into current authority.

## Required behavior

- Exact current `control_source + live_observation` may admit the exact proposition/referent binding.
- `semantic_research + live_observation` without current control evidence remains `UNRESOLVED`.
- Conflict or supersession in decisive evidence remains non-admitting.
- Wrong proposition or wrong referent scope remains non-admitting.
- A stale/adjacent control source must not become current merely because it is the newest or repository-local source.
- Until exact current evidence exists, the runtime may remain `UNRESOLVED`; the purpose of this dispatch is not to force the gate open.

## Pair/receipt requirement

Because this changes normative B, the exact A+B pair must be rebound. The successor pair receipt must point to an immutable pre-receipt source commit containing the exact unchanged A blob plus the new B blob.

The same receipt currently has an operational-support drift: PR #104 changed the runtime/provider-admission/package surfaces after the receipt's old `1e8ee410...` support cut. The successor receipt should therefore rebind the complete current support set to the same immutable pre-receipt cut and add `runtime_cohesion/provider_admission.py` as a material support surface.

This receipt repair remains validation evidence only; it cannot prove merge, installation, route activation, runtime consumption, behavioral qualification, provider origin, or phenomenology.
