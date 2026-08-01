# V.E.R.A. R7A1 Workstream Routing

## Controller

`Project Architect / Integration Controller`

This is one program-level role. It owns dependency mapping, writer leases, barriers, assembly, shared-file resolution, integration verdicts, and decision packets.

## Standard flow

```text
Project Architect / Integration Controller
                |
             Identity
                |
       +--------+--------+
       |                 |
     Time            Initiatives
       |
     Memory
       |                 |
       +--------+--------+
                |
          Coordination
                |
 Project Architect / Integration
                |
       GitHub Repository Steward
                |
     Explicit user authority
```

## State lane

`Identity -> Time -> Memory`

Identity defines project and behavior subjects. Time defines temporal evidence and fail-closed unknowns. Memory consumes both without redefining them.

## Action lane

`Identity -> Initiatives`

Initiatives selects or abstains over supplied candidates. It does not invent objectives or execute actions.

## Barrier

State and action lanes must return accepted immutable heads before Coordination performs compatibility transport.

## Coordination lane

Coordination validates addressed events, acknowledgements, receipts, stale-state handling, and operational-message classification. It does not co-author component semantics.

## Join

The controller assembles accepted heads, resolves shared-file effects, and runs exact-tree assurance.

## Stage protocol

1. `CLAIM`: controller grants one writer lease.
2. `IMPLEMENT`: owner works only within scope.
3. `HANDOFF`: owner returns exact head, paths, tests, limitations, and next recipient.
4. `REVIEW`: reviewer returns one exact-head verdict.
5. `CORRECTION`: owner publishes a new head; old reviews become historical.
6. `BARRIER`: controller confirms prerequisites.
7. `ASSEMBLY`: controller joins accepted histories.
8. `DECISION`: user authorizes repository, production, installation, or other user-only gates.

## Hard stops

Stop when authority, permission, safety, verification, branch identity, source evidence, or material uncertainty is unresolved.

Silence is pending, not failure. Unexpected branch movement pauses publication.

## Behaviors lane

`Behaviors` owns conversational-behavior requirements, law completeness, canonical examples, hostile cases, acceptance criteria, and independent behavioral validation. It does not patch the exact head it reviews.

For a bounded behavior-law patch explicitly scoped by the user, the direct route is:

`Behaviors specification -> Project Architect implementation -> Behaviors exact-head validation -> user decision`

Coordinator and other workstreams are excluded from that bounded route unless the user expands scope or a genuine cross-domain dependency appears.
