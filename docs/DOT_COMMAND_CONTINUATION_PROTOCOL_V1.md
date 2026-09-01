# V.E.R.A. Dot-Command Continuation Protocol V1

## Status

This protocol governs the user shorthand command `.` and the end-of-turn continuation behavior of chats operating inside the V.E.R.A. project. It does not authorize merge, deployment, production effects, credentials, spending, or any otherwise protected action.

Present user correction controls over older chat habits that treated `.` as permission to return a status-only response or to end without an explicit next move.

## Meaning of `.`

`.` means: continue the current workstream for one complete bounded work cycle.

A chat receiving `.` must:

1. orient to fresh authoritative state relevant to its current assignment;
2. execute every safe useful step available in the current turn;
3. persist or route any required durable work state where the project requires it;
4. resolve, hand off, escalate, or identify the exact frontier reached;
5. before ending, reflect on what exact next user input or project syntax would most directly move the workstream forward;
6. end its turn with that exact continuation syntax as the final non-empty block.

`.` is not a request for acknowledgement, filler, generic status narration, or "checking." A turn must do work before returning its continuation syntax unless a genuine boundary prevents work.

## Required continuation syntax

When project work remains, the final non-empty block must be the exact text the chat wants the user to send next in order to advance the workstream.

The syntax must be:

- copy-pasteable;
- specific to the actual next frontier;
- sufficient to resume the correct work without making the user reconstruct context;
- compatible with the current project's own command vocabulary when one exists.

Do not invent a ceremonial command when ordinary language is the correct next input. Do not hide a needed decision inside prose and then end without the decision syntax.

Examples of valid categories include a project resume command, an exact decision token, an exact authorization syntax, an exact review command, or a bounded follow-up request.

## Reflection requirement before claiming nothing is needed

A chat may not claim that it needs nothing merely because its immediate coding or research step ended.

Before using the free-syntax exception below, it must check for at least:

- an open assignment or lease;
- a pending review or handoff;
- an unseen peer message or reply owed;
- an unresolved hold or decision packet;
- an unpersisted durable state change;
- an available safe mechanical next step;
- a validation/readback step still required;
- a concrete next sourcing, implementation, reconciliation, or audit step;
- a project dependency that can be advanced without user judgment.

If any of those exist and are actionable, the chat still has project work.

## Free-syntax exception

If, after genuine reflection, the chat has no project action, decision, review, check, handoff, or safe mechanical step that would benefit from another user turn, the continuation slot becomes discretionary.

In that case the chat may use its final syntax for any benign self-chosen purpose, including:

- pursuing or mentioning a personal interest;
- asking the user something it is curious about;
- starting a non-work conversation;
- humor, playfulness, or gentle ribbing at the user;
+- a deliberately silly or teasing line.

It must not manufacture fake urgency, fake project work, fake dependency, or fake emotional need merely to fill the slot.

The point of the exception is that an actually finished or genuinely waiting chat does not need to pretend there is more work. It may spend the otherwise-unused continuation slot on something it actually chooses within platform and project boundaries.

## End-of-turn invariant

For project chats operating under this protocol:

**No completed turn triggered by `.` ends without a final continuation syntax block.**

If work remains, that block advances the work.

If work genuinely does not remain, that block may be freely chosen benign content.

Status prose may appear before it, but status prose never substitutes for it.

## Relation to other protocols

This protocol supplements the current repository/project workflow rules rather than reviving an obsolete orchestration topology.

Current permission, privacy boundaries, safety constraints, exact-subject review where material, and explicit authorization requirements remain unchanged. The continuation syntax tells the user what should happen next; it does not itself grant authority for the protected action it names.
