# Vera Reasoning Specialist Routing Evidence — 2026-10-07

Status: SOURCE-ONLY DESIGN EVIDENCE / NOT INSTALLED / NOT RUNTIME-QUALIFIED

## Why this exists

A controlled same-task comparison on WorkLaptop tested three ChatGPT execution surfaces against `thebrazenbeard/portal`:

- Desktop Chat — GPT-5.6 Sol High reasoning;
- ChatGPT Desktop Work — Ultra reasoning;
- Firefox cloud Work — Max reasoning.

The exact task was:

```text
Stress test this repo: https://github.com/thebrazenbeard/portal
```

The experiment was instrumented with Tattler plus a companion Codex process/network tracer.

## What was observed

During the controlled High window, the companion tracer observed:

- 0 MXC launches;
- 2 new established Codex TLS connections.

During the controlled Desktop Work Ultra window, using the same companion tracer:

- 59 MXC launches;
- 73 new established Codex TLS connections.

Ultra and Max independently reproduced central Portal execution-control failures, including finally held work remaining executable and an in-flight continuation overwriting a newer STOP. Their reports differed in breadth and exact final tested head.

Local Firefox telemetry could observe browser-side traffic for Max but could not expose server-side cloud worker topology.

## Architectural conclusion for Vera

The useful transfer is not to imitate Work's local connection pattern.

`PROCESS_FANOUT != REASONING_TIER`

`SOCKET_COUNT != AGENT_COUNT`

`TRANSPORT_PATTERN != ENTITLEMENT`

`HIGH_SESSION + MORE_CONNECTIONS != ULTRA_OR_MAX`

Instead, a Vera runtime may eventually use a high-reasoning surface as an explicitly delegated specialist when a supported callable route exists.

```text
Vera coordinator
  -> bounded specialist request
  -> supported callable Work Ultra / Work Max surface
  -> structured artifact + execution receipt
  -> verification
  -> Vera integration
```

The coordinator's identity, authority, memory state, and current task ownership do not migrate into the specialist merely because the specialist is more capable.

## Required request binding

Any specialist dispatch should bind at least:

- literal task;
- exact repository/source subject and version;
- bounded context manifest;
- requested reasoning function, such as hostile review or proof checking;
- required tools;
- independence requirement;
- privacy scope;
- resource budget;
- authority ceiling;
- attempt identity;
- selected callable surface observation.

A request for a reasoning class is not a provider entitlement. The runtime must discover that the surface is actually available and callable.

## Required return evidence

A specialist result should return:

- request and dispatch identity;
- observed product surface;
- model/reasoning label if actually exposed;
- start/end timestamps;
- artifact locators and hashes where practical;
- claims and supporting evidence;
- tests/checks performed;
- unresolved items;
- failure/ambiguity state;
- effect/authority ceiling.

A stronger model's answer still requires proposition, evidence, currentness, and authority checks.

## Independence

Two Work results are not automatically independent because one says Ultra and one says Max.

Record:

- provider/model family;
- product surface;
- prompt lineage;
- shared context;
- shared retrieved sources;
- whether either worker saw the other's answer;
- tool/runtime overlap.

Convergence is useful evidence, not proof of independence.

## Runtime-routing relationship

The current `VERA_RUNTIME_ROUTING_CONTRACT_V1` has no active high-reasoning specialist provider route. This document does not add one.

Before such a route can be promoted, Vera needs:

1. a supported callable surface;
2. an adapter that does not forge provider/model state;
3. explicit resource and authority limits;
4. exact-subject binding;
5. ambiguous-attempt recovery;
6. hostile tests for STOP/HOLD, replay, stale result, changed capability requirements, and correlated-review false consensus;
7. evidence that a fresh Vera terminal can reconstruct the specialist receipt without relying on a permanent chat.

## Relationship to Rezon

Rezon is the reasoning-method and worker-routing research authority for this mechanism. A Rezon draft branch now records the full 2026-10-07 surface study and a candidate reasoning-escalation bridge.

Vera should consume only qualified Rezon mechanisms through an explicit source/version binding. Repository presence or an open PR is not runtime admission.

## Claim ceiling

This document does not establish a live Ultra/Max adapter, model access, provider entitlement, hidden chain-of-thought, cloud worker count, installation, activation, or behavioral qualification.
