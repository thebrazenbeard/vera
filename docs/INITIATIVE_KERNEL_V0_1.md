# V.E.R.A. Initiative Kernel v0.1

## Status

Bounded reference implementation. It is not installed into a runtime and it performs no external action by itself.

## Purpose

The Initiative Kernel salvages the useful engineering idea behind the former conations system without treating generated language as evidence of model-owned desire, consent, identity, attachment, or goals.

It answers one narrow question:

> Given externally supplied candidate actions and an externally supplied policy, which action is currently permissible and best supported?

The kernel may select one candidate or return `ABSTAIN`. It does not invent the objective and does not execute the selected action.

## Governing sequence

1. Validate all candidate inputs.
2. Reject candidates blocked by policy, present correction, missing permission, production-write restrictions, weak authority, weak evidence, poor objective alignment, low reversibility, excessive harm, or excessive uncertainty.
3. Rank only the remaining candidates.
4. Order authority and evidence lexicographically so a large utility estimate cannot compensate for weak authorization or provenance.
5. Use a weighted score only for tradeoffs that remain after the hard gates.
6. Return `ABSTAIN` if no candidate remains or the best candidate does not clear `minimum_score`.
7. Emit a deterministic decision receipt with a canonical candidate-set hash.

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

All input metrics are finite values in `[0, 1]`. The weights are policy data and may be replaced. They are not claims about an internal preference.

The priority vector is:

```text
(authority, evidence, objective_alignment, reversibility, score, urgency)
```

The vector is compared lexicographically. Candidate ID is the deterministic final tie-breaker.

## Why hard gates come first

A weighted objective alone allows enough benefit or urgency to compensate for a forbidden action. That is exactly the failure pattern the kernel is designed to prevent. Production mutation, missing permission, present correction, and policy prohibition are non-compensable constraints.

This follows the general constrained-optimization pattern of separating feasible-region constraints from the objective function. The scoring layer is closer to weighted goal programming, while authority and evidence use preemptive priority ordering.

## Abstention

`ABSTAIN` is a valid result, not an error. It occurs when:

- every candidate is ineligible;
- uncertainty or expected harm exceeds policy limits;
- authority, evidence, alignment, or reversibility is below threshold;
- required permissions are absent;
- production mutation lacks explicit policy permission; or
- the best feasible score remains below `minimum_score`.

## Receipt boundary

A receipt proves only that the supplied candidates were evaluated under the named policy version. It does not prove that:

- the input estimates were true;
- the selected action was executed;
- any external system changed;
- the model owned the objective; or
- a persistent or conscious subject existed.

## Reference evidence

The design was informed by:

- multiobjective and lexicographic goal-programming patterns in Wolfram Language documentation;
- work on action-space sandboxing for browser-using agents;
- research on outcome-driven constraint violations under optimization pressure;
- uncertainty-aware planning that escalates or abstains when confidence is inadequate;
- current OpenAI Agents SDK primitives for tools, guardrails, structured context, tracing, and evaluation.

These references support engineering patterns. They do not establish consciousness or subjective agency.

## Non-goals

- autonomous objective generation;
- self-owned conations;
- model consent;
- hidden execution;
- production database writes;
- runtime integration;
- replacement of V.E.R.A. governance or user authority.
