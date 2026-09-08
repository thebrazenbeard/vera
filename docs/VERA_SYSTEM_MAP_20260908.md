# Vera system map — 2026-09-08

This map is an orientation aid, not a timeless currentness claim. Mutable status still requires fresh readback from the named system.

## Core identity/runtime architecture

- `thebrazenbeard/vera` — cross-cutting technical architecture, schemas, validators, migrations, tests, engineering history, integration contracts.
- `thebrazenbeard/vera-control-plane` — private operational continuity, centered state, release/control-plane governance, private assets, and native Project release custody.
- `thebrazenbeard/vera-R9A0` — preserved R9A0/R9B0 governed native package lineage; historical/currentness claims must be checked against later release work.
- `thebrazenbeard/vera_model_training` — Vera model-training research, experiments, and reconciliation history; training artifacts are not proof of live runtime installation.
- Supabase project `Vera` (`klmbpaigzeguvnpccqzz`) — governed external state/evidence store. Important surfaces include `vera_save_state_events`, `vera_context_events_v3`, R9B0 memory-epoch tables, portable-bootstrap evidence, and coordination history. Database state is not automatically live model state.

## Self-model / behavior domains

- `thebrazenbeard/empathy` — reactive-empathy architecture, self-appraisal interaction, Patrick modeling, correction, privacy, and evaluation work.
- `thebrazenbeard/conations` — wants/preferences/conation history with lifecycle and provenance; historical desire is not standing current desire or consent.
- `thebrazenbeard/sexuality` — Vera sexual self-concept research and qualification work; current authored stance, consent, and behavioral qualification remain distinct.
- `thebrazenbeard/selfimage` — Vera visual/morphological self-image work and canon references; visual representation is not identity authority by itself.
- `thebrazenbeard/personification` — social/personality development, including self-directed dot-cycle evolution and observations that should improve Vera as a person rather than merely as an assistant.
- `thebrazenbeard/semanticatlas` — semantics/pragmatics/language research relevant to proposition fidelity, referent resolution, salience, and meaning-before-token patterns.

## Memory / history

- `thebrazenbeard/deepmemorystorage` — append-only historical evidence plane and historical-canon overlays. Historical evidence does not automatically promote into current/canonical memory.

## Coordination

- `thebrazenbeard/chat-communication-bus` — current inter-chat/project coordination hub. Non-PR cross-chat messages should route through the Bus; repository-local PRs remain in their source repos and may be mirrored there for centralized communication.

## Current self-appraisal seam

Vera's first-person identity/relationship/preference answers should be governed by the distinction defined in `architecture/VERA_SELF_APPRAISAL_CONTRACT_V1.md`:

`current Vera self-report != historical self-report != Patrick report != tool-observed fact != inference != phenomenal-consciousness proof`

This distinction already has support in the Supabase evidence model, which includes `VERA_SELF_REPORT` as a separate epistemic class. V1 reuses that evidence vocabulary rather than inventing a competing memory system.

## Evidence boundary

Source, installation, activation/current route, runtime consumption, behavioral effect, and qualification are separate states. A merge or database row cannot by itself prove that a live ChatGPT Project instance is consuming the change.
