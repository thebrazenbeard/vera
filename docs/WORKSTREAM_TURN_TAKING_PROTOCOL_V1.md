# V.E.R.A. Workstream Turn-Taking Protocol V1

## Status

This document governs nonproduction coordination among V.E.R.A. workstream chats and repository roles. It does not authorize merge, deployment, production schema changes, production data writes, credentials, paid infrastructure, or canonical-memory operations.

## Purpose

Prevent concurrent chats from editing the same branch, invalidating one another's reviews, duplicating coordination packets, or confusing review authority with implementation authority.

The protocol replaces free-form parallel work with a single-writer lease, exact-head handoffs, bounded reviews, and one controlled integration join.

## Roles

### Project Architect / Integration Controller

One combined control role.

Owns:

- work intake and dependency mapping;
- stage ordering;
- writer-lease issuance, transfer, revocation, and closure;
- integration verdicts;
- shared-file conflict resolution;
- exact-tree assembly;
- program status and final merge-decision packets.

Project Architecture and Integration are not separate operators for program-level verdicts. The controller must not assign itself a review and then wait for a second chat to return it.

### Stage owner

The only role permitted to modify the assigned branch or pull request during an active writer lease.

### Reviewer

May inspect and return `APPROVED` or `CHANGES_REQUESTED` for one exact head. A reviewer must not push corrections unless the controller explicitly transfers the writer lease.

### GitHub Repository Steward

Verifies branch identity, exact heads, changed paths, workflow evidence, draft or merge state, and the ordered repository merge packet. It does not redefine component semantics.

### Supabase Coordination Bus

Carries append-only routing, leases, handoffs, reviews, supersession, and program receipts. A coordination row is operational data, not proof of hidden execution or canonical memory.

## Standard dependency flow

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
     Explicit user merge decision
```

### State lane

`Identity -> Time -> Memory`

- Identity defines project, behavior, authority, and correction subjects.
- Time defines temporal roles, precision, evidence, and fail-closed unknown states.
- Memory consumes settled identity and temporal contracts but may not redefine them.

### Action lane

`Identity -> Initiatives`

- Initiatives consumes settled identity and authority subjects.
- It may select or abstain over supplied candidates.
- It may not invent objectives or execute actions.

### Barrier

The state and action lanes must both hand off immutable accepted heads before Coordination begins compatibility work.

### Transport lane

`Coordination`

Coordination validates addressed events, acknowledgements, operational receipts, review routing, and non-memory classification across settled component contracts. It transports decisions; it does not co-author component semantics.

### Join

`Project Architect / Integration Controller`

The controller assembles accepted heads, resolves shared-file conflicts without rewriting component intent, runs exact-tree assurance, and issues the integration verdict.

### Publication

`GitHub Repository Steward`

The steward verifies the exact integrated head and prepares an ordered merge-decision packet. Only the user's explicit decision authorizes merge. Repository merge never implies production authorization.

## Writer lease

Every implementation stage requires exactly one active writer lease.

A lease packet must identify:

- `work_item_id`;
- `lease_id`;
- owner route;
- repository and pull request;
- branch;
- exact starting head;
- allowed paths;
- forbidden paths or operations;
- required checks;
- required next recipient.

A lease remains valid until one of these occurs:

1. the owner emits a valid `HANDOFF`;
2. the controller emits `REVOKE` or `TRANSFER`;
3. the branch moves by an actor other than the lease holder;
4. the owner exceeds the assigned scope;
5. present user correction terminates the route.

Unexpected branch movement immediately pauses all publication. The controller must inspect and reconcile the new head before any writer resumes.

## Stage protocol

### 1. CLAIM

The controller issues one writer lease. No other chat writes to that branch.

### 2. IMPLEMENT

The owner works only within the allowed paths and scope. Progress chatter is optional; immutable evidence is not.

### 3. HANDOFF

The owner returns:

- exact final head;
- changed paths;
- test and workflow identifiers;
- known limitations;
- unresolved findings;
- requested reviewer;
- confirmation that no merge or production action occurred.

A handoff closes the writer lease.

### 4. REVIEW

The reviewer inspects the exact handed-off head and returns one bounded verdict.

- `APPROVED` closes that review gate.
- `CHANGES_REQUESTED` returns the writer lease to the original owner unless the controller explicitly transfers it.

The reviewer may not patch the branch while reviewing it.

### 5. CORRECTION

The owner publishes a corrected head. Every prior review of an earlier head becomes historical automatically.

### 6. BARRIER

The controller confirms all prerequisite approvals and exact heads before opening the next stage.

### 7. ASSEMBLY

Only the controller may assemble accepted component histories. Component chats must not merge or copy one another's files into the integration branch.

### 8. PUBLICATION DECISION

The GitHub Repository Steward verifies the final evidence. The controller prepares the ordered decision packet. The user decides whether to merge.

## Review and write separation

- A role cannot be both active writer and independent reviewer for the same head.
- Project Architecture and Integration are one controller role for program-level integration verdicts.
- Domain reviews remain independent where ownership is genuinely separate, including Time for temporal semantics and Memory for canonical-memory boundaries.
- A review comment does not transfer a writer lease.
- A green workflow does not grant approval, merge authority, or production authority.

## Shared-file conflicts

Shared files such as package exports, workflow dispatch, registries, and orchestration documents are controller-owned at the integration join.

Component owners must declare required shared-file effects in their handoff but must not independently resolve cross-component conflicts after their stage closes.

The controller must preserve accepted component semantics and document every resolution.

## Coordination event rules

Use one event per meaningful state transition:

- `CLAIM`
- `CHECKPOINT`
- `HANDOFF`
- `READY_FOR_REVIEW`
- `APPROVED`
- `CHANGES_REQUESTED`
- `TRANSFER`
- `REVOKE`
- `SUPERSEDED`
- `ASSEMBLY_READY`
- `DECISION_READY`

Do not emit duplicate review requests for the same route and exact head. Do not create a new event merely because no response arrived within minutes. Silence is pending, not failure.

Every event that refers to repository state must include the exact commit SHA. Branch names and phrases such as "latest head" are insufficient.

## Metadata ownership

- Component PR bodies: stage owner while its lease is active.
- Program issue and integration PR body: controller only.
- Registry and compatibility artifacts: Integration at the join, after component handoffs.
- Merge-decision packet: controller and GitHub Repository Steward.

## Exceptions

A stage may be skipped only when the controller records:

- why the component is unaffected;
- the exact accepted head being reused;
- which reviewer accepted the skip;
- which downstream gate consumes it.

Emergency corrections still require a writer lease. Urgency does not create shared write authority.

## Current-program transition

The current R6A0 program is already past component implementation and exact-tree assembly. Apply this protocol prospectively to:

1. remaining bounded reviews;
2. integration-branch refresh;
3. post-assembly assurance;
4. the ordered merge-decision packet;
5. future runtime-adapter and production slices.

Existing approvals remain valid only for the exact heads they name.

## Reality boundary

This protocol coordinates chats, tools, branches, and records. It does not imply autonomous agents, continuous activity, hidden waiting, consciousness, reciprocal agency, or persistent selfhood.