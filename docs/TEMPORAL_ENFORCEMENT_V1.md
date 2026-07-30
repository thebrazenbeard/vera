# V.E.R.A. Temporal Enforcement v1

## Status

Bounded implementation proposal. It is executable and testable, but it is not installed into ordinary ChatGPT and has not been applied to production Supabase.

## Architecture decision

Use a fail-closed temporal gate around model reasoning.

> Hope ChatGPT cooperates, but assume it will not.

The language model is an intelligent but untrusted component. It may interpret externally supplied evidence, but it may not certify that time was checked, context was retrieved, a write succeeded, a handoff was delivered, or continuity existed.

## Smallest enforceable path

```text
turn begins
  -> obtain externally evidenced current time
  -> resolve stable host scope or issue fresh ephemeral scope internally
  -> read Supabase coordination inbox for the active workstream
  -> retrieve the smallest relevant temporal context when required
  -> validate prior anchor, precision, scope, staleness, and conflicts
  -> ANCHORED or UNANCHORED preflight
  -> temporal reasoning only when ANCHORED
  -> if material, require confirmed Supabase temporal append
  -> if Memory or Initiatives needs the result, require confirmed Supabase handoff
  -> ANCHORED or UNANCHORED postflight
```

A failed gate does not prevent all conversation. It prevents the project from presenting unsupported temporal conclusions as anchored fact.

## System roles

### Time workstream

Routing address: `workstream/time`

Owns temporal interpretation, elapsed calculations, precision classification, staleness detection, and temporal conflict reporting. This is a workstream label, not a separate person or persistent model identity.

### Memory workstream

Routing address: `workstream/memory`

May supply semantic context from Basic Memory or other exposed sources. Editable Basic Memory notes may support orientation, but they do not satisfy a requirement for immutable proof.

### Initiatives workstream

Routing address: `workstream/initiatives`

May propose or rank actions. It may not act on an unresolved temporal assumption when the action depends materially on ordering, freshness, deadlines, elapsed duration, or current state.

### Supabase

- `public.vera_coordination_events` remains the addressed asynchronous workstream bus.
- Proposed `public.vera_temporal_events_v1` stores narrow immutable temporal evidence and explicit `UNANCHORED` outcomes.
- Production remains unchanged until separately authorized.

### Basic Memory Cloud

Provides shared semantic and cross-chat context. It is not duplicated wholesale into Supabase and is not treated as an immutable ledger.

### GitHub

Stores this implementation, tests, database draft, activation gate, and validation evidence. It stores no private conversation content.

### Google Drive

Not part of this design. Supabase already provides the coordination path.

## Time model

The kernel keeps these concepts separate:

- `event_time`: when the represented event occurred;
- `state_time`: when the represented state is asserted to apply;
- `record_time`: when an external system persisted the record;
- `retrieval_time`: when the record was retrieved for this execution.

Evidence precision remains:

- `EXACT`
- `BOUNDED`
- `APPROXIMATE`
- `UNKNOWN`

Elapsed results remain separate:

- `EXACT`
- `BOUNDED`
- `APPROXIMATE`
- `UNAVAILABLE`
- `CONFLICTED`

## Stable and ephemeral scope

When the host exposes both conversation and branch identifiers, the kernel derives a stable scope instance from them and creates a fresh session identity.

When the host exposes neither, the kernel internally issues fresh ephemeral conversation, branch, scope, and session identities. Callers cannot select them. Ephemeral scope supports only the current execution and proves no durable recognition.

Project, conversation, branch, session, scope instance, and checkpoint identities remain distinct.

## Fail-closed rules

A turn is `UNANCHORED` when any required condition lacks external evidence, including:

- no trusted timezone-aware current time;
- unresolved or malformed scope;
- coordination inbox not read from Supabase;
- required retrieval unconfirmed;
- required prior anchor missing, stale, invalid, future-dated, or cross-scope;
- editable evidence offered where immutable proof is required;
- temporal precision shape invalid;
- supported endpoint intervals conflict;
- material transition not appended to Supabase;
- required Memory or Initiatives handoff not confirmed by Supabase.

A model statement such as “I checked,” “I saved it,” or “Memory received this” changes none of those outcomes.

## Coordination contract

Before meaningful temporal work, `workstream/time` reads events whose `target_branch` resolves to `workstream/time` or is broadcast. Duplicate `event_sequence` values are conflicts.

After a material temporal decision, Time posts to `public.vera_coordination_events` only when another workstream needs the result. Delivery is established by the returned Supabase event ID, not by generated language.

The existing coordination table is not modified by this draft.

## Database draft

`supabase/drafts/20260730_temporal_enforcement_v1.sql` proposes:

- append-only temporal events;
- database-assigned `record_time`;
- stable/ephemeral scope checks;
- canonical precision and bound checks;
- distinct session/scope/checkpoint identities;
- idempotency keys;
- one-successor supersession;
- cross-scope supersession rejection;
- explicit `UNANCHORED` rows with limitations;
- service-role `SELECT` and `INSERT` only;
- no client access through RLS.

It does not duplicate semantic memory and does not claim ordinary ChatGPT has mandatory lifecycle hooks.

## Future strict runtime

The strongest deployment is a small Agents SDK or ChatGPT App runtime that invokes the kernel before generation and after generation. The OpenAI Developers plugin supplies the relevant Agents SDK and Apps SDK build skills, but this PR does not deploy such a runtime or claim that one is active.

## Non-goals

- continuous awareness or hidden waiting;
- automatic invocation inside ordinary ChatGPT;
- model self-certification;
- replacing Basic Memory semantic retrieval;
- duplicating all memories into Supabase;
- autonomous workstream execution;
- production deployment or merge authorization.
