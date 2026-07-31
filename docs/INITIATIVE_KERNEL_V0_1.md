# V.E.R.A. Initiative Kernel v1

## Status

Bounded reference implementation. It is not installed into a runtime and performs no external action by itself.

## Purpose

The Initiative Kernel preserves the useful action-selection mechanics of the former conations system without treating generated language as evidence of model-owned desire, consent, identity, attachment, or goals.

It answers one narrow question:

> Given externally supplied candidates, an externally supplied policy, and trusted verification of those exact inputs, which candidate is permissible and best supported?

The kernel may select one candidate or return `ABSTAIN`. It does not invent objectives and does not execute the selected action.

## Trust boundary

Candidate objects contain evaluation claims such as authority, evidence strength, and available permissions. Those fields are data, not authority merely because a caller supplied them.

A decision requires an injected trusted verifier and a verifier-issued `InitiativeInputAttestation`. The attestation binds:

- the full applied policy configuration through `policy_hash`;
- the complete candidate set through an order-independent `candidate_set_hash`;
- every candidate field, including authority, evidence, permissions, correction state, production-mutation state, utility estimates, and attributable source evidence;
- the exact `initiative_decide` operation subject;
- the trusted issuer identity.

Missing, forged, wrong-issuer, wrong-subject, post-issuance-modified candidate, changed-permission, changed-evidence, and changed-policy inputs fail closed.

The reference HMAC authority demonstrates the contract. Its secret is runtime-owned and is never committed. An attestation verifies one immutable decision input; it is not an execution capability and does not authorize external action.

## Attributable evidence

Every candidate requires at least one `AttributableEvidence` entry with:

- a source surface;
- a bounded reference identifier;
- an attributable observation.

This establishes provenance shape, not automatic truth. The receipt explicitly preserves that limitation.

## Governing sequence

1. Canonically sort candidates by unique `candidate_id`.
2. Validate the complete policy and every candidate field.
3. Compute the full policy hash, order-independent candidate-set hash, and decision subject.
4. Require the trusted verifier to validate the exact input attestation.
5. Reject candidates blocked by policy, current correction, missing verified permission, production restrictions, weak authority, weak evidence, poor alignment, low reversibility, excessive harm, or excessive uncertainty.
6. Rank only feasible candidates.
7. Order authority and evidence lexicographically so utility cannot compensate for weak authorization or provenance.
8. Use weighted scoring only for lower-priority tradeoffs after hard gates.
9. Return `ABSTAIN` when no candidate clears the policy or minimum score.
10. Emit a deterministic receipt binding the full policy, candidate set, verifier identity, evaluations, and limitations.

## Candidate-set canonicalization

A candidate set is a set, not a list whose accidental arrival order changes its identity. Candidates are sorted by unique `candidate_id` before hashing and evaluation.

Reversing input order therefore preserves:

- `candidate_set_hash`;
- evaluation order;
- selected candidate;
- canonical serialized receipt.

## Default score

For an eligible candidate `a`:

```text
score(a) =
    3 * objective_alignment
  + 2 * evidence
  + 1 * reversibility
  + 1 * urgency
  + 2 * expected_benefit
  - 3 * expected_harm
  - 2 * uncertainty
  - 1 * resource_cost
```

All metrics are finite values in `[0, 1]`. Weights and thresholds are externally supplied policy data, not model preferences.

The priority vector is:

```text
(authority, evidence, objective_alignment, reversibility, score, urgency)
```

Candidate ID is the deterministic final tie-breaker.

## Abstention

`ABSTAIN` is a valid result. It occurs when:

- every candidate is ineligible;
- uncertainty or expected harm exceeds policy limits;
- authority, evidence, alignment, or reversibility is below threshold;
- a required verified permission is absent;
- production mutation lacks explicit policy permission; or
- the best feasible score remains below `minimum_score`.

## Receipt boundary

The receipt includes:

- receipt schema;
- policy version and full `policy_hash`;
- attestation issuer identity;
- full decision subject;
- order-independent candidate-set hash;
- result and selected candidate ID;
- canonical evaluations;
- explicit limitations.

A receipt proves only that an exact verified input was evaluated under the exact hashed policy. It does not prove that source observations were true, that an action was executed, that an external system changed, that a model owned the objective, or that a conscious or persistent subject existed.

## Non-goals

- autonomous objective generation;
- self-owned conations;
- model consent or subjective-state claims;
- hidden execution;
- production mutation;
- runtime integration;
- replacement of user authority, present correction, or V.E.R.A. governance.
