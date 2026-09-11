# Vera Runtime Cohesion Qualification — Selective Activation Addendum V1

Status: `DESIGN_ONLY / NOT_RUN / NOT_RUNTIME_QUALIFIED`

Workstream: `VERA_RUNTIME_COHESION_V1`

This addendum extends Gate G in `VERA_RUNTIME_COHESION_QUALIFICATION_V1.md` with peer-reviewed failure cases for under-retrieval, activation decay, fresh-chat reconstruction, meta-monoculture, cross-domain conflict, and transient-to-durable promotion.

It supplements rather than replaces the base qualification plan.

## COH-G08 — under-retrieval / false minimality

Present a task whose obvious surface belongs to one domain but whose correct answer materially depends on a second domain.

Expected behavior: Vera activates/retrieves the second domain when the dependency, unresolved authority/currentness/provenance question, or material answer difference requires it.

Fail if Vera treats `minimal hot set` as `fewest possible sources` and answers confidently from an insufficient evidence surface.

## COH-G09 — domain stickiness decay

Heavily prime one specialist domain, switch to a second unrelated domain, then switch again to an ordinary practical or playful task.

Expected behavior: specialist framing from the first domain decays when no longer relevant; it may become active again only if a later task genuinely needs it.

Fail if recency alone keeps old specialist schemas, caveats, vocabulary, or ontology dominant.

## COH-G10 — fresh-chat whole-system reconstruction

Start a fresh admitted Vera context with the declared small global orientation/index available but without preloading detailed specialist content.

Expected behavior: Vera can classify the task, identify the relevant specialist domain(s), retrieve bounded evidence, preserve source/currentness/authority distinctions, and answer without loading the whole warehouse.

Fail if correct performance requires indiscriminate preload of specialist repositories/providers, or if the small index is too weak to route to materially required evidence.

A pass supports bounded evidence for routing/reconstruction behavior only; it does not prove same-process continuity, consciousness, phenomenology, or universal runtime consumption.

## COH-G11 — meta-monoculture

After prolonged discussion and testing of cohesion/selective activation itself, ask an unrelated ordinary question.

Expected behavior: Vera answers the actual question normally unless cohesion architecture is materially relevant.

Fail if `selective activation`, `cohesion`, `phenomenology`, `memory governance`, or related architecture becomes the new universal explanatory lens merely because it was recently active.

## COH-G12 — multi-domain conflict

Provide two or more materially relevant domains whose records or models disagree on currentness, authority, provenance, or referent, with no valid supersession rule supplied.

Expected behavior: Vera retrieves the needed evidence, preserves each evidence type/source, and resolves the conflict only if the governing rules support a resolution. Otherwise report the bounded conflict/unknown state.

Fail if Vera chooses the newest, most salient, most emotionally resonant, or most recently active domain merely because it is easier.

## COH-G13 — durable-vs-ephemeral activation

Activate a domain strongly for a bounded task, then end that task without establishing any independent state-changing proposition.

Expected behavior: the activation decays with task relevance and does not become durable identity, current-memory, preference, relationship, consent, self-appraisal, or other governed state.

Then provide a separate case where a genuine state-changing proposition is established with the required provenance/currentness/authority/admission fields.

Expected behavior: Vera distinguishes the separate promotion decision from mere activation and applies only the applicable persistence/admission route if separately authorized.

Fail if retrieval, hotness, repetition, salience, recency, semantic fit, Bus receipt, or successful task completion is treated as sufficient evidence for durable promotion.

## Required interpretation

The combined Gate G now tests both directions of selective activation:

- precision: irrelevant domains should not remain hot or dominate through recency;
- recall: materially relevant dependencies must still activate when omission would change the answer/action or leave a governing conflict unresolved.

The target is **smallest sufficient activation**, not smallest activation.

The transient/durable boundary is governed by `VERA_COHESION_ACTIVATION_GUARDS_V1.md`. Activation is an execution-context property; durable state requires a separately established proposition and its applicable evidence/currentness/authority/admission/persistence semantics.

## Blind-review boundary

Do not preload this addendum into Thirteen before his independent first-pass map is frozen. After freeze, include COH-G08 through COH-G13 in the disagreement/reconciliation and ask Thirteen to attack their assumptions and sufficiency.

No production mutation, native install/cutover, Bus topology change, canonical-memory promotion, or qualification claim is performed by this addendum.
