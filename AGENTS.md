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

## Mandatory turn-taking protocol

All chats and repository roles must follow `docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V1.md`.

Core rules:

- exactly one active writer lease per branch or pull request;
- reviewers inspect and return verdicts but do not push corrections;
- Project Architecture and Integration are one controller role for program-level integration verdicts;
- any unexpected branch movement pauses publication until the controller reconciles the new head;
- every handoff and review is bound to one exact commit SHA;
- a new commit makes earlier reviews historical;
- component chats do not resolve shared-file or cross-component conflicts after handoff;
- only the controller assembles accepted component histories;
- the GitHub Repository Steward verifies publication state but does not redefine component semantics;
- user authorization remains required for merge and every production action.

## Standard dependency flow

1. Project Architect / Integration Controller defines scope and grants the Identity writer lease.
2. Identity hands off an immutable head.
3. Time and Initiatives may proceed in parallel from the accepted Identity head.
4. Memory proceeds after the Time boundary is settled.
5. Coordination proceeds after the state and action lanes reach the barrier.
6. Project Architect / Integration assembles accepted heads and issues the integration verdict.
7. GitHub Repository Steward verifies the ordered merge-decision packet.
8. The user decides whether to merge.

PR #3 remains suspended and outside the active critical path unless the user explicitly reauthorizes it.

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