from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .adapters import AdapterProbeResult, AdapterRegistry, AdapterRequest
from .evidence import ProviderEvidenceEnvelope, validate_envelope
from .runtime import build_operational_checkpoint, build_retrieval_plan


EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."


@dataclass(frozen=True)
class DomainExecutionResult:
    status: str
    domain_id: str
    probes: tuple[AdapterProbeResult, ...]
    observations: tuple[ProviderEvidenceEnvelope, ...]
    unresolved: tuple[str, ...]
    checkpoint: dict[str, Any]

    def __post_init__(self) -> None:
        if self.status not in {"EXECUTED", "EXECUTED_WITH_UNRESOLVED", "UNRESOLVED"}:
            raise ValueError(f"unsupported execution status: {self.status}")


def _provider_for_route(fabric: Mapping[str, Any], route_ref: str) -> str:
    matches = [
        provider_id
        for provider_id, provider in fabric.get("providers", {}).items()
        if route_ref in provider.get("route_refs", [])
    ]
    if len(matches) != 1:
        raise ValueError(f"route {route_ref!r} must resolve to exactly one provider; got {matches!r}")
    return matches[0]


def _request_for_candidate(candidate: Mapping[str, Any], provider: str) -> AdapterRequest:
    return AdapterRequest(
        domain_id=str(candidate["domain_id"]),
        provider=provider,
        source_ref=str(candidate["source_ref"]),
        route_ref=str(candidate["route_ref"]),
        selector_ref=candidate.get("selector_ref"),
        privacy_class=str(candidate["privacy_class"]),
        evidence_capability_refs=tuple(candidate.get("evidence_capability_refs", ())),
    )


def _allowed_evidence_classes(request: AdapterRequest) -> set[str]:
    result: set[str] = set()
    for ref in request.evidence_capability_refs:
        if not ref.startswith(EVIDENCE_PREFIX):
            raise ValueError(f"unsupported evidence capability ref: {ref}")
        result.add(ref[len(EVIDENCE_PREFIX):])
    return result


def _validate_probe(request: AdapterRequest, probe: AdapterProbeResult) -> None:
    if probe.provider != request.provider:
        raise ValueError(
            f"adapter probe provider mismatch for {request.route_ref}: expected {request.provider!r}, got {probe.provider!r}"
        )
    if probe.route_ref != request.route_ref:
        raise ValueError(
            f"adapter probe route mismatch: expected {request.route_ref!r}, got {probe.route_ref!r}"
        )


def _validate_read(request: AdapterRequest, envelope: ProviderEvidenceEnvelope) -> None:
    validate_envelope(envelope)
    if envelope.provider != request.provider:
        raise ValueError(
            f"adapter read provider mismatch for {request.route_ref}: expected {request.provider!r}, got {envelope.provider!r}"
        )
    if envelope.evidence_class not in _allowed_evidence_classes(request):
        raise ValueError(
            f"returned item evidence class {envelope.evidence_class!r} is not in target capability set for {request.route_ref}"
        )
    if envelope.privacy_class != request.privacy_class:
        raise ValueError(
            f"returned item privacy class {envelope.privacy_class!r} does not match planned class {request.privacy_class!r}"
        )
    route_ref = envelope.metadata.get("route_ref")
    source_ref = envelope.metadata.get("source_ref")
    if route_ref != request.route_ref:
        raise ValueError(
            f"returned item route metadata mismatch: expected {request.route_ref!r}, got {route_ref!r}"
        )
    if source_ref != request.source_ref:
        raise ValueError(
            f"returned item source metadata mismatch: expected {request.source_ref!r}, got {source_ref!r}"
        )


def execute_domain_cycle(
    domain_id: str,
    index: Mapping[str, Any],
    contract: Mapping[str, Any],
    fabric: Mapping[str, Any],
    adapters: AdapterRegistry,
    *,
    privacy_allowlist: set[str] | frozenset[str],
) -> DomainExecutionResult:
    """Execute one provider-backed cohesion retrieval cycle.

    The executor first asks the existing bounded planner which targets are safe to
    probe, then invokes only the registered provider adapter for each candidate,
    rebuilds the plan from fresh probe results, and reads only routes observed as
    CURRENTLY_OBSERVED_REACHABLE or RESULT. Adapters supply transport; A+B and
    the runtime planner remain policy/currentness boundaries.
    """

    discovery = build_retrieval_plan(
        domain_id,
        index,
        contract,
        observed_route_states={},
        privacy_allowlist=privacy_allowlist,
    )

    probes: list[AdapterProbeResult] = []
    route_states: dict[str, str] = {}
    unresolved: list[str] = [
        item for item in discovery.unresolved if not item.startswith("ROUTE_NOT_CURRENTLY_OBSERVED_REACHABLE:")
    ]

    candidate_requests: dict[tuple[str, str, str | None], AdapterRequest] = {}
    for candidate in discovery.candidate_targets:
        route_ref = str(candidate["route_ref"])
        provider = _provider_for_route(fabric, route_ref)
        request = _request_for_candidate(candidate, provider)
        key = (request.source_ref, request.route_ref, request.selector_ref)
        candidate_requests[key] = request

        adapter = adapters.get(provider)
        if adapter is None:
            unresolved.append(f"MISSING_ADAPTER:{provider}:{route_ref}")
            continue
        if getattr(adapter, "provider", None) != provider:
            raise ValueError(
                f"adapter registry/provider mismatch for {provider!r}: adapter reports {getattr(adapter, 'provider', None)!r}"
            )
        probe = adapter.probe(request)
        _validate_probe(request, probe)
        probes.append(probe)
        route_states[route_ref] = probe.state

    plan = build_retrieval_plan(
        domain_id,
        index,
        contract,
        observed_route_states=route_states,
        privacy_allowlist=privacy_allowlist,
    )
    unresolved.extend(plan.unresolved)

    observations: list[ProviderEvidenceEnvelope] = []
    for target in plan.targets:
        provider = _provider_for_route(fabric, str(target["route_ref"]))
        key = (target.get("source_ref"), target.get("route_ref"), target.get("selector_ref"))
        request = candidate_requests.get(key)
        if request is None:
            request = _request_for_candidate(target, provider)
        adapter = adapters.get(provider)
        if adapter is None:
            unresolved.append(f"MISSING_ADAPTER:{provider}:{request.route_ref}")
            continue
        envelope = adapter.read(request)
        _validate_read(request, envelope)
        observations.append(envelope)

    # De-duplicate unresolved markers while preserving order.
    unresolved = list(dict.fromkeys(unresolved))
    checkpoint = build_operational_checkpoint(plan, [])

    material_unresolved = [
        item
        for item in unresolved
        if not (
            item.startswith("ROUTE_NOT_CURRENTLY_OBSERVED_REACHABLE:")
            and item.rsplit(":", 1)[-1] in {"CURRENTLY_OBSERVED_REACHABLE", "RESULT"}
        )
    ]
    if observations and not material_unresolved and plan.budget_state == "WITHIN_BUDGET":
        status = "EXECUTED"
    elif observations:
        status = "EXECUTED_WITH_UNRESOLVED"
    else:
        status = "UNRESOLVED"

    return DomainExecutionResult(
        status=status,
        domain_id=domain_id,
        probes=tuple(probes),
        observations=tuple(observations),
        unresolved=tuple(material_unresolved),
        checkpoint=checkpoint,
    )
