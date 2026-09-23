# Vera Hostile Reviewer V1

Status: **SOURCE IMPLEMENTED / TYPED PROPOSITION REVIEW / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

## Goal

Make the useful visible hostile-review block a governed Vera feature rather than an ad hoc conversational habit.

When enabled, Vera first produces the ordinary answer. The runtime then binds:

1. the exact primary-answer bytes by SHA-256; and
2. the exact typed literal proposition by a canonical SHA-256 envelope.

The adversarial pass attacks that literal proposition without silently replacing it with a stronger, weaker, narrower, or different proposition.

## Typed proposition contract

The review input binds:

- `literal_proposition`
- `proposition_type`
- `referent`
- `scope`
- `success_criteria`
- `known_evidence`
- `protected_assumptions`

The literal proposition is marked unproven and attacked as stated.

Changing the proposition type, referent, scope, evidence, criteria, or protected assumptions changes the proposition digest.

## Review sequence

The governed sequence is:

1. bind the exact typed proposition;
2. bind the exact primary answer;
3. attack the literal proposition;
4. return one typed verdict:
   - `LITERAL_SURVIVES`
   - `LITERAL_FAILS`
   - `UNRESOLVED`
5. if the literal proposition survives, support that result rather than manufacturing opposition;
6. infer an underlying objective or propose a stronger route only after literal failure, unless Patrick explicitly requested a stronger route.

This prevents both benevolent proposition substitution and performative contrarianism.

## Typed result contract

The reviewer returns a `HostileReviewDecision`, not an opaque critique string.

Typed externally shareable fields include:

- `literal_verdict`
- `counterexamples`
- `unsupported_assumptions`
- `scope_failures`
- `alternative_explanations`
- `surviving_claim`
- `inferred_objective`
- `stronger_route`
- `confidence`
- `unresolved`

The decision must echo both the primary-answer digest and the proposition digest. Digest mismatch fails closed.

A `LITERAL_SURVIVES` decision may contain zero objections. That is an expected successful hostile-review outcome.

A `LITERAL_FAILS` decision must contain actual failure evidence: a counterexample, unsupported assumption, or scope failure.

A stronger route requires an inferred objective and is not permitted after literal survival unless the caller explicitly requested stronger-route exploration.

## Why this is a response-review feature, not a personality

The hostile reviewer is not a separate identity and does not become Vera's permanent voice. It is a response-stage adversarial method.

Turning it off restores the ordinary response path without needing to undo personality state.

The reviewer must not disagree merely to look independent.

## Boundaries

The hostile pass is advisory only. It may identify a problem and cause the final recommendation to be narrowed, but it may not:

- invent evidence;
- broaden Patrick's request;
- silently substitute proposition type, referent, or scope;
- grant or infer authority;
- claim a tool effect occurred;
- promote source to install/runtime/qualification;
- convert inference into fact;
- convert history into current memory or preference;
- create identity, consent, or desire state;
- expose hidden chain-of-thought.

The public surface is typed, concise, externally shareable review output only.

## Cross-chat toggle

The runtime module accepts a control object with:

- `mode = OFF | ON`
- `scope = VERA_PROJECT_ALL_CHATS | CHAT_LOCAL`
- presentation and objection-budget settings.

A durable **all-chat** effect requires the current Vera Project/runtime to consume a current control-plane object. Repository source alone does not establish that installation.

The corresponding private control source belongs in `thebrazenbeard/vera-control-plane`.

## Eligibility

With the global switch ON, the review pass should run on substantive turns: recommendations, architecture, interpretation, causal reasoning, plans, and decision support.

It should not spam greetings, simple acknowledgements, or trivial mechanical confirmations.

## Failure modes explicitly tested

The focused regression surface covers:

- exact primary-answer substitution;
- typed proposition substitution;
- proposition-type/referent/scope drift;
- performative opposition;
- stronger-claim promotion after literal survival;
- stronger-route ordering;
- literal-failure claims without actual failure evidence;
- opaque/free-text reviewer output;
- objection-budget overflow;
- clean literal-survives/no-objection behavior.

## Claim ceiling

This source implementation establishes deterministic typed request/result mechanics only.

It does **not** establish:

- native ChatGPT Project installation;
- all-chat activation;
- model/provider selection;
- current runtime consumption;
- behavioral qualification;
- authority;
- memory admission;
- identity or phenomenology.
