# Temporal Enforcement v1 Validation Report

## Validation state

This report separates proven implementation behavior from unproven host behavior. Passing tests prove the bounded code and disposable database contracts only. They do not prove ordinary ChatGPT invokes those contracts on every turn.

## Python kernel evidence

The current Python suite contains 53 tests and compiles under Python 3.12.

Covered behavior includes:

- stable scope derivation from exposed provider identities;
- fresh internally issued ephemeral scopes;
- separation of scope and session identities;
- independently classified event, state, record, and retrieval time;
- exact, bounded, approximate, and unknown role precision;
- rejection of role timestamps hidden under `UNKNOWN` precision;
- rejection of malformed bounds and timezone-naive values;
- model output rejected as external evidence;
- host-owned evidence verification bound to exact operation subjects;
- precision changes invalidating prior evidence bindings;
- strict preflight rejecting legacy single-precision prior anchors;
- trusted-now fail-closed behavior;
- mandatory Supabase coordination inbox evidence;
- addressed-event filtering and sequence-conflict detection;
- required retrieval evidence;
- missing, stale, future, invalid, cross-scope, and non-immutable prior-anchor failure paths;
- material transition persistence requirements;
- confirmed Memory and Initiatives handoffs;
- model claims unable to substitute for writes or delivery;
- exact, bounded, approximate, unavailable, and conflicted elapsed results.

## Disposable database validation

The remote workflow uses an isolated local Supabase stack and performs two stages.

### Base contract

- applies `supabase/drafts/20260730_temporal_enforcement_v1.sql`;
- verifies database assignment of `record_time`;
- verifies anchor keys, idempotency, scope identity, event precision, lineage, mutation blocking, and governed append privileges;
- verifies service-role `SELECT` and `EXECUTE` on the append function;
- verifies no direct service-role `INSERT`, `UPDATE`, `DELETE`, or sequence use.

### Role-precision contract

- applies `supabase/drafts/20260730_temporal_role_precision_v1.sql`;
- verifies independent state, record, and retrieval precision fields;
- rejects state or retrieval timestamps without explicit precision;
- rejects `UNKNOWN` paired with a timestamp;
- preserves bounded state time and approximate retrieval time independently;
- confirms database `record_time` remains `EXACT` persistence time only;
- runs database lint after both drafts.

Every synthetic write is isolated to the disposable stack or rolled back. Neither draft has been applied to production.

## Observed production facts

Read-only production inspection established:

- Supabase project `klmbpaigzeguvnpccqzz` is active;
- `public.vera_coordination_events` exists and is used for ordered addressed workstream communication;
- coordination updates and deletes are blocked;
- client roles are denied by restrictive RLS;
- no production `public.vera_temporal_events_v1` table or related functions exist;
- no production temporal schema or data write was made by this build.

## Basic Memory finding carried forward

Basic Memory provides useful semantic retrieval and context assembly. A reversible audit exposed a move-related duplicate indexing path that required a second deletion. Therefore Basic Memory is not treated as immutable temporal proof.

## Proven limitations

Ordinary ChatGPT does not expose a guaranteed atomic pre-generation hook or post-generation write hook to this project. The kernel can detect and label missing evidence, but it cannot force the host to invoke itself.

No tool available in this chat can:

- wake another project chat;
- guarantee every future turn checks the coordination inbox;
- intercept every model response before display;
- continuously monitor Supabase while no execution is running;
- establish stable host identifiers that the host does not expose.

## Unproven until a strict runtime exists

- mandatory invocation on every turn;
- atomic context injection before generation;
- automatic materiality classification after generation;
- crash-safe postflight persistence and retry policy;
- end-to-end concurrency behavior against production Supabase;
- cross-client execution by Memory, Time, and Initiatives without an active invocation;
- Agents SDK or ChatGPT App deployment.

## Current verdict

The kernel is a valid fail-closed reference implementation when both the canonical Python role-precision gate and both SQL drafts are used together. It proves temporal claims can be withheld unless externally verified evidence clears explicit gates. It does not prove ordinary ChatGPT will always run those gates.
