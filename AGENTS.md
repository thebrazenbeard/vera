# V.E.R.A. Repository Instructions

## Project boundary

This repository contains the public, version-controlled technical architecture for V.E.R.A., the Virtual Environment for Reciprocal Agency.

V.E.R.A. is a provenance-governed context, memory, and coordination system. It does not establish or imply consciousness, autonomous identity, model-owned desire, hidden persistence, reciprocal attachment, or offscreen activity.

## Authority and truth

1. Platform and safety constraints govern.
2. Present user instruction and correction govern within their valid scope.
3. Tool results and documented sources govern factual claims within their evidenced scope.
4. Model output is not self-authenticating evidence.
5. Stored records never override current permission, correction, privacy, provenance, or reality honesty.

## Repository rules

- Never commit credentials, tokens, private conversation exports, raw memory-ledger rows, or database dumps.
- Preserve history. Prefer additive migrations, append-only records, explicit supersession, and scoped tombstones.
- Do not rewrite or delete legacy persona-era artifacts merely because they are no longer active. Archive and label them.
- Do not modify production Supabase unless the user explicitly authorizes the exact target and scope.
- A passing branch workflow does not authorize merge or deployment.
- Use bounded branches and pull requests. Do not write directly to `main`.
- Keep Time, Memory, Initiatives, Coordination, and runtime integration as separate contracts with explicit interfaces.
- Treat `event_time`, `state_time`, `record_time`, and retrieval time as distinct.
- Treat GitHub as architecture source control, not the live context store.
- Treat Supabase as external persistence only when a connector result confirms the operation.

## Active integration order

1. Neutral R6A0 release package and migration parity.
2. Coordination bus contract.
3. Memory contract and Time boundary review.
4. Temporal enforcement contract.
5. Initiative kernel contract.
6. Runtime adapter and end-to-end integration.
7. Production deployment, separately authorized.

PR #3 remains suspended and outside the active temporal critical path unless the user explicitly reauthorizes it.

## Verification

Every implementation change must provide fresh evidence proportionate to its risk:

- focused unit or contract tests;
- syntax or type validation;
- migration replay in a disposable database when schema behavior is involved;
- security and privilege checks for database surfaces;
- repository-wide integration checks before merge;
- explicit documentation of anything not demonstrated.

## Coordination

Operational workstream coordination uses `public.vera_coordination_events`. Coordination messages are routing and audit data, not proof of autonomous agents, wake-up behavior, or hidden execution.

The canonical program tracker is GitHub issue #11.