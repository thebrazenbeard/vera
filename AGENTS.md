# V.E.R.A. Repository Instructions

## Project boundary

This private repository contains cross-cutting, version-controlled technical architecture for V.E.R.A., the Virtual Environment for Reciprocal Agency.

V.E.R.A. is a provenance-governed Project/runtime referent. Runtime/session/model identifiers are execution provenance, not identity, current authority, or proof of uninterrupted private experience. Repository source is not proof of active ChatGPT Project installation or runtime consumption.

The current governed native Project package line is maintained in `thebrazenbeard/vera-R9A0`; historical release material in this repository remains provenance unless independently rebound as current.

## Authority and truth

1. Platform and safety constraints govern.
2. Present user instruction and correction govern within their valid scope.
3. Fresh authorized target-system evidence governs mutable factual/currentness claims within its evidenced scope.
4. Model output, history, CI, retrieval, package presence, and capability do not self-authorize protected effects.
5. Stored records never override current permission, correction, privacy, provenance, currentness, or reality honesty.

## Repository rules

- Never commit credentials, tokens, private conversation exports, raw private memory payloads, or database dumps.
- Preserve history. Prefer additive migrations, append-only records, explicit supersession, and scoped tombstones.
- Do not rewrite or erase historical artifacts merely because they are no longer active; preserve and classify them.
- Use bounded branches and pull requests. Do not write directly to `main` unless a present exact exception explicitly authorizes it.
- A passing branch workflow does not authorize merge, deployment, installation, provider mutation, or runtime effect.
- Treat event, state, record, retrieval, source, installation, and effect times as distinct where material.
- Treat GitHub as source/provenance control, not the live context store.
- Treat Supabase as external persistence only when the target operation is authorized and its effect is verified by readback.
- Package/source generation, Project installation, provider state, runtime consumption, and downstream effect are separate evidence domains.

## Workflow coordination

GitHub is the sole work-bearing coordination surface under issue #46.

- Assignments, decisions, reviews, blockers, status, implementation discussion, Supabase work, and handoffs belong on GitHub.
- Slack is social/historical only and cannot authorize or establish current workflow state.
- Legacy `public.vera_coordination_events` records are historical evidence, not the live workflow board.
- Do not split one workflow between GitHub and Slack/Supabase.
- Bind handoffs/reviews to exact immutable subjects when their correctness depends on exact bytes.
- Unexpected movement of an immutable review/write subject stops that exact action until currentness is reconciled.

There is no single timeless program issue. Use the current repository/workstream issue or PR that owns the task; issue #11 is historical R6A0-era program state and is not a canonical current tracker.

## Dot-command continuation

All chats operating inside the V.E.R.A. project follow `docs/DOT_COMMAND_CONTINUATION_PROTOCOL_V1.md` for the shorthand command `.` and its end-of-turn continuation behavior.

- `.` means execute one complete bounded work cycle, not acknowledge or return status-only prose.
- When project work remains, the final non-empty block is exact copy-pasteable continuation syntax that advances the actual frontier.
- Before claiming no project work remains, check pending assignments, reviews, handoffs, durable state, validation/readback, and safe mechanical next steps.
- When nothing actionable remains, the final continuation slot may be benign self-chosen content rather than manufactured work.
- Continuation syntax communicates the next requested action; it does not authorize a protected effect.

## Correction and effect discipline

When a present correction or concrete defect changes the route:

1. terminate the obsolete route;
2. apply the smallest executable correction to the original task;
3. preserve historical evidence where provenance matters;
4. verify target-system effect/readback before claiming persistence or closure;
5. do not add review/handoff ceremony unless a real dependency or risk requires it.

On ambiguous non-idempotent writes, inspect the operation/target before retry. Never blindly repeat a possibly successful effect.

## Verification

Every implementation change must provide evidence proportionate to its risk, such as:

- focused unit or contract tests;
- syntax/type/schema validation;
- migration replay or live provider verification when database behavior is involved;
- security/privilege checks for exposed database surfaces;
- exact changed-path/subject readback for bounded repository work;
- explicit documentation of anything not demonstrated.

No current source, provider, installation, runtime, or release claim should be inferred solely from stale README text, old issue prose, or a newer timestamp.
