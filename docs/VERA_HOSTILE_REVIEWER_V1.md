# Vera Hostile Reviewer V1

Status: **SOURCE IMPLEMENTED / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

## Goal

Make the useful visible hostile-review block a governed Vera feature rather than an ad hoc conversational habit.

When enabled, Vera first produces the ordinary answer. The runtime then binds that exact answer by SHA-256 and asks an adversarial Countervoice to attack the strongest material claims, recommendations, assumptions, and architectural choices. The resulting critique is surfaced visibly as a blockquote.

The feature is intentionally simple: **OFF** or **ON**.

## Why this is a response-review feature, not a personality

The hostile reviewer is not a separate identity and does not become Vera's permanent voice. It is a response-stage adversarial pass. Turning it off must restore the ordinary response path without needing to undo personality state.

That distinction also prevents a long research or review task from contaminating later ordinary conversation.

## Boundaries

The hostile pass is advisory only. It may identify a problem and cause the final recommendation to be narrowed, but it may not:

- invent evidence;
- broaden Patrick's request;
- grant or infer authority;
- claim a tool effect occurred;
- promote source to install/runtime/qualification;
- convert inference into fact;
- convert history into current memory or preference;
- expose hidden chain-of-thought.

The public surface is concise objections and conclusions only.

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

## Failure mode to avoid

The reviewer must not become a ritualized contrarian that manufactures a disagreement on every turn. Its job is to find a **material** objection. If no material objection survives scrutiny, it may say so briefly.
