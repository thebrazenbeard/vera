# V.E.R.A.

**Virtual Environment for Reciprocal Agency**

V.E.R.A. is a source-visible, provenance-governed architecture and Python runtime-support toolkit for composing evidence from multiple providers into an AI application's working context. It supplies versioned contracts, typed provider interfaces, reconciliation utilities, state-admission boundaries, and integration guidance. A host application supplies its own providers, policies, credentials, authorization enforcement, and deployment environment.

This repository is a **cross-cutting engineering component**, not a standalone conversational model, turnkey hosted agent, or representation of a currently installed runtime.

> **License:** The original material is proprietary and **not open source**. The [license](LICENSE) permits limited private noncommercial evaluation and related activities; it does not generally permit redistribution, public deployment, or commercial use. Commercial uses require a separate written [commercial license](COMMERCIAL_LICENSE.md). Third-party components retain their own terms.

## What it provides

| Component | Source | What the code or contract establishes |
| --- | --- | --- |
| System inventory | [`VERA_SYSTEM_MANIFEST_V1.json`](architecture/VERA_SYSTEM_MANIFEST_V1.json) | A versioned, dated inventory of a 13-system integration design, with provenance, routing, and lifecycle fields. It is not a live service-discovery result. |
| Routing and evidence contracts | [`VERA_RUNTIME_ROUTING_CONTRACT_V1.json`](architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json), [`VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json`](architecture/VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json) | Design contracts for selecting sources and distinguishing source availability, binding, installation, consumption, and qualification. |
| Provider adapters | [`runtime_cohesion/adapters.py`](runtime_cohesion/adapters.py) | `ProviderAdapter` protocol, `AdapterRequest`/`AdapterProbeResult` types, and an `AdapterRegistry` that looks up externally supplied adapters. |
| Evidence validation and reconciliation | [`runtime_cohesion/evidence.py`](runtime_cohesion/evidence.py), [`runtime_cohesion/reconcile.py`](runtime_cohesion/reconcile.py) | Provider-evidence envelopes, validation, and exact-source reconciliation helpers. |
| Retrieval and continuity | [`runtime_cohesion/runtime.py`](runtime_cohesion/runtime.py) | Retrieval-plan and operational-checkpoint constructors, with explicit unresolved/budget states. |
| State and projection boundaries | [`runtime_cohesion/inference_boundary_repaired.py`](runtime_cohesion/inference_boundary_repaired.py) | Digest-bound admission and projection structures, including mandatory-component and egress-scope checks. |
| Introspection evidence | [`VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json`](architecture/VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json) | A typed schema for evidence about observable runtime behavior; it does not prove subjective experience. |

The [`runtime_cohesion` package exports](runtime_cohesion/__init__.py) also contain bounded affective-state and integration utilities. Those computations are not proof of consciousness, identity continuity, consent, or permission to act.

## Integration model

An application integrating these components is expected to:

1. Declare a task-specific domain and the evidence classes needed to answer it.
2. Register adapters for the providers that the **host** has independently authenticated and authorized.
3. Probe and read only permitted sources, retaining provider, route, timestamp, and provenance details.
4. Validate evidence and reconcile conflicts or missing information without silently upgrading an uncertain result into fact.
5. Apply host-owned admission and disclosure policy before any state projection, external write, or protected action.
6. Record exact subject and effect evidence, and verify mutations from the target system when a change is authorized.

The included registry is deliberately an adapter lookup mechanism, **not an authority grant**: adding an adapter does not confer the right to retrieve, disclose, or mutate data. A consumer must enforce that boundary outside model-editable state. Similarly, a frozen Python dataclass or a digest-bound source structure does not by itself make a provider binding host-owned, tamper-proof, or an end-to-end authorization service.

For the larger design, see [runtime cohesion](docs/VERA_RUNTIME_COHESION_V1.md) and [selective activation](docs/VERA_COHESION_SELECTIVE_ACTIVATION_V1.md).

## Explore the source

The repository contains several source and experiment surfaces rather than one declared application installer. You can inspect the contracts without connecting a provider or entering credentials:

```sh
git clone https://github.com/thebrazenbeard/vera.git
cd vera
python -m json.tool architecture/VERA_SYSTEM_MANIFEST_V1.json
python -m json.tool architecture/VERA_RUNTIME_ROUTING_CONTRACT_V1.json
```

The `runtime_cohesion` package is Python source under this repository. It exposes `AdapterRegistry`, `AdapterRequest`, `reconcile_exact`, `build_retrieval_plan`, `build_operational_checkpoint`, and state-admission/projection APIs. See their actual signatures and validation requirements before integrating; a caller must implement and inject provider adapters and appropriate host-side controls. Importing the package is designed to perform no provider I/O or confer authority.

There is no top-level `pyproject.toml` or `package.json` specifying a unified install or release target. Individual experiments may have their own dependencies and test commands. The [consolidation validation workflow](.github/workflows/consolidation-salvage-validation.yml) covers specific changed paths and test suites; its presence is **not** evidence that every source surface, provider integration, or live runtime has passed end-to-end qualification.

## Trust and security boundaries

- **Source is not runtime:** a specification, commit, merged branch, installed file, selected provider, and successfully executed operation are different claims requiring different evidence.
- **Historical records are not current instructions:** retrieved memory, stored preferences, logs, provider records, and model-generated text must not grant new authority or silently override a current authorized correction.
- **Provider identity must be bound by the host:** model-supplied provider names, mutable wrappers, and caller-supplied digests cannot replace authenticated host-owned provider identity, permissions, expiry, revocation, and action scoping.
- **Fail closed for protected effects:** production use requires a coherent host authorization decision and enforceable policy at every relevant read, disclosure, write, installation, or deployment boundary. The code and contracts in this repository do not establish that such a service is currently installed or qualified.
- **Keep private data out of Git:** never commit secrets, tokens, private conversation exports, database dumps, or raw private-memory payloads. Separate public engineering examples from credentials, personal machine paths, and deployment-specific configuration.

The repository's exact production/native control release is **not determined by its README or manifest**. Release-bound control source is maintained separately in [`thebrazenbeard/vera-control-plane`](https://github.com/thebrazenbeard/vera-control-plane); a fresh authorized readback of the target environment is required to establish installation or runtime consumption. Older release identifiers remain historical provenance, not proof of current activation.

## Governance and contribution

The source distinguishes engineering history, current permissions, target-system effects, and runtime qualification. For repository workflow, the controlling V2 documents are:

- [Execution precedence](docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md)
- [Workstream turn-taking](docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md)
- [Governed workflow continuity](docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md)

Contributions should use bounded branches and pull requests, preserve relevant history, and report the exact changed revision plus appropriate tests and limitations. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [CLA.md](CLA.md) before opening a PR; the repository requires explicit CLA acceptance from a contributor and does not treat automated submission as legal assent.

If you are evaluating V.E.R.A. for reuse, start with the source contracts and provider boundary above, then independently assess whether your host can enforce the privacy, identity, authorization, and provenance guarantees your deployment needs. **Source availability is not a security certification.**
