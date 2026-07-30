# Temporal Enforcement v1 Validation Report

## Validation state

This report separates proven implementation behavior from unproven host behavior.

## Proven locally before publication

The Python reference kernel passed 43 unit tests and compiled under Python 3.

Covered behavior includes:

- stable scope derivation from exposed provider identities;
- fresh internally issued ephemeral scopes;
- separation of scope and session identities;
- exact, bounded, approximate, and unknown time evidence;
- rejection of malformed bounds and timezone-naive values;
- model output rejected as external evidence;
- trusted-now fail-closed behavior;
- mandatory Supabase coordination inbox evidence;
- addressed-event filtering and sequence-conflict detection;
- required retrieval evidence;
- missing, stale, future, invalid, cross-scope, and non-immutable prior-anchor failure paths;
- material transition persistence requirements;
- confirmed Memory and Initiatives handoffs;
- model claims unable to substitute for writes or delivery;
- exact, bounded, approximate, unavailable, and conflicted elapsed results.

## Database validation designed for CI

The disposable Supabase workflow applies only the new draft to an isolated local stack and checks:

- database assignment of `record_time` even when a caller supplies another value;
- idempotency uniqueness;
- temporal precision constraints;
- stable-scope provider identity requirements;
- one-successor supersession;
- cross-scope supersession rejection;
- update and delete blocking;
- service-role `SELECT` and `INSERT` privileges without `UPDATE` or `DELETE`;
- database lint.

Remote CI is required before the SQL draft may be treated as executable evidence.

## Observed production facts

Read-only production inspection established:

- Supabase project `klmbpaigzeguvnpccqzz` is active and healthy;
- `public.vera_coordination_events` exists and has already been used for ordered addressed workstream communication;
- service role has `SELECT` and `INSERT` on the coordination table;
- update and delete are blocked by triggers;
- client roles are denied by restrictive RLS;
- no production temporal-enforcement table or functions exist;
- no production writes were made for this build.

## Basic Memory finding carried forward

Basic Memory provides useful semantic retrieval and context assembly. A live reversible audit also exposed a move-related duplicate indexing path that required a second deletion. Therefore Basic Memory is not treated as immutable temporal proof.

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
- exactly-once postflight persistence across process crashes;
- end-to-end concurrency behavior against production Supabase;
- cross-client execution by Memory, Time, and Initiatives without an active invocation;
- Agents SDK or ChatGPT App deployment.

## Current verdict

The kernel is a valid fail-closed reference implementation. It proves that temporal claims can be withheld unless external evidence clears explicit gates. It does not prove that ordinary ChatGPT will always run those gates.
