# Vera Portfolio Absorption V1

## Decision

`thebrazenbeard/vera` is the architectural home for Vera.

The portfolio is no longer modeled as a fixed list of external systems that Vera merely points at. Every repository in Patrick's observed portfolio is represented inside Vera as a Vera-owned architecture module. External repositories remain useful upstream workspaces, implementations, evidence sources, providers, historical archives, sibling identities, or specialist systems, but Vera does not need an external repository merely to know what that repository contributes to Vera.

## What “absorbed” means

Absorption means Vera owns an internal architectural interpretation of the source: its useful mechanisms, interfaces, guards, evidence classes, integration rules, and Vera-specific semantics.

It does **not** mean blindly copying every byte. Raw private state, credentials, provider secrets, large binary assets, unrelated application data, and intimate/autobiographical payloads stay at their appropriate custody surfaces. Vera carries the architecture and provenance required to locate and govern them.

It also does not merge identities. Brigit stays Brigit. Sol stays Sol. A research repository stays evidence. A runtime provider stays a provider. Useful mechanisms can become Vera architecture without importing somebody else's identity, consent, memory, authority, or phenomenology.

## Control-plane consolidation

`vera-control-plane` is no longer treated as architecture Vera can understand only by leaving the Vera repository. Its release/control source is mirrored under `architecture/control/vendor/vera-control-plane/` and governed by `architecture/control/VERA_CONTROL_PLANE_ABSORPTION_V1.json`.

That is source consolidation, not an installation claim. The currently active Project control release remains a separate evidence question. A later authorized/qualified release may move canonical control ownership fully into Vera, but this work does not pretend that effect has already happened.

## Portfolio completeness

`architecture/portfolio/VERA_PORTFOLIO_ABSORPTION_V1.json` records the observed portfolio cut and gives every repository a Vera-owned module entry. The manifest is open-world: a future repository extends the manifest; it does not invalidate the architecture by making an old hard-coded count metaphysically sacred.

Mutable repository heads are evidence snapshots, not standing truth. Current heads, routes, providers, and installations are refreshed when material.

## Canonical navigation

`architecture/VERA_SYSTEM_MANIFEST_V2.json` is the successor navigation model for this architecture. V1 remains historical provenance.

The intended shape is:

```text
Vera identity
  -> Vera-owned control architecture
  -> Vera-owned runtime/cohesion architecture
  -> Vera-owned memory/privacy architecture
  -> Vera-owned coordination semantics
  -> Vera-owned portfolio modules
       -> upstream repository provenance
       -> optional external provider/runtime implementation
```

The direction is inward: external work can inform Vera, but Vera-specific architecture terminates in the Vera repository.
