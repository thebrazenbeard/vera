from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Any, Mapping

from .adapters import AdapterProbeResult, AdapterRegistry, AdapterRequest
from .audit import AUDIT_STATUSES, ProjectionAuditResult, audit_registered_projections
from .evidence import ProviderEvidenceEnvelope, validate_envelope
from .runtime import build_operational_checkpoint, build_retrieval_plan


EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."
RETRIEVABLE_PROBE_STATES = {"CURRENTLY_OBSERVED_REACHABLE", "RESULT"}
_EVENT_SELECTOR_TOKENS = {"$source_ref", "$source_path", "$source_revision"}


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


@dataclass(frozen=True)
class ProjectionExecutionResult:
    status: str
    projection_id: str
    probes: tuple[AdapterProbeResult, ...]
    source_observation: ProviderEvidenceEnvelope | None
    target_observation: ProviderEvidenceEnvelope | None
    audit: ProjectionAuditResult | None
    unresolved: tuple[str, ...]
    checkpoint: dict[str, Any]

    def __post_init__(self) -> None:
        if self.status not in AUDIT_STATUSES:
            raise ValueError(f"unsupported projection execution status: {self.status}")
        if not self.projection_id:
            raise ValueError("projection_id must be non-empty")


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


def _checkpoint_with_unresolved(checkpoint: Mapping[str, Any], unresolved: list[str]) -> dict[str, Any]:
    result = dict(checkpoint)
    pointer = dict(result.get("minimum_necessary_payload_or_pointer", {}))
    pointer["unresolved"] = list(dict.fromkeys(unresolved))
    result["minimum_necessary_payload_or_pointer"] = pointer
    return result


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
        if envelope is None:
            unresolved.append(f"ABSENT_ITEM:{provider}:{request.route_ref}:{request.source_ref}")
            continue
        _validate_read(request, envelope)
        observations.append(envelope)

    unresolved = list(dict.fromkeys(unresolved))
    checkpoint = _checkpoint_with_unresolved(build_operational_checkpoint(plan, []), unresolved)

    material_unresolved = [
        item
        for item in unresolved
        if not (
            item.startswith("ROUTE_NOT_CURRENTLY_OBSERVED_REACHABLE:")
            and item.rsplit(":", 1)[-1] in RETRIEVABLE_PROBE_STATES
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


def _matches_pattern(value: str, pattern_expression: str) -> bool:
    patterns = [part.strip() for part in pattern_expression.split("|") if part.strip()]
    return any(fnmatchcase(value, pattern) for pattern in patterns)


def _projection_by_id(fabric: Mapping[str, Any], projection_id: str) -> Mapping[str, Any]:
    rows = [row for row in fabric.get("projections", []) if row.get("id") == projection_id]
    if len(rows) != 1:
        raise ValueError(f"projection {projection_id!r} must resolve exactly once; got {len(rows)}")
    return rows[0]


def _resolve_event_selector(
    projection: Mapping[str, Any],
    *,
    role: str,
    event_ref: str,
    event_path: str,
    source_revision: str | None,
) -> tuple[tuple[str, str], ...]:
    raw = projection.get(f"{role}_event_selector")
    if raw is None:
        return ()
    if not isinstance(raw, Mapping):
        raise ValueError(f"projection {projection.get('id')!r} {role}_event_selector must be a mapping")

    values = {
        "$source_ref": event_ref,
        "$source_path": event_path,
        "$source_revision": source_revision,
    }
    resolved: list[tuple[str, str]] = []
    for field_name, template in raw.items():
        if not isinstance(field_name, str) or not field_name:
            raise ValueError("event selector field names must be non-empty strings")
        if not isinstance(template, str) or not template:
            raise ValueError(f"event selector value for {field_name!r} must be a non-empty string")
        if template.startswith("$") and template not in _EVENT_SELECTOR_TOKENS:
            raise ValueError(f"unsupported event selector token: {template}")
        value = values.get(template, template)
        if value is None:
            raise ValueError(f"event selector token {template!r} is unavailable before source readback")
        resolved.append((field_name, value))
    return tuple(sorted(resolved))


def _projection_request(
    projection: Mapping[str, Any],
    fabric: Mapping[str, Any],
    *,
    role: str,
    event_ref: str,
    event_path: str,
    source_revision: str | None = None,
) -> AdapterRequest:
    if role not in {"source", "target"}:
        raise ValueError(f"unsupported projection role: {role}")
    provider = str(projection[f"{role}_provider"])
    route_ref = str(projection[f"{role}_route_ref"])
    evidence_class = str(projection[f"{role}_evidence_class"])
    resolved_provider = _provider_for_route(fabric, route_ref)
    if resolved_provider != provider:
        raise ValueError(
            f"projection {projection.get('id')!r} {role} route/provider mismatch: {route_ref!r} resolves to {resolved_provider!r}, not {provider!r}"
        )
    provider_row = fabric.get("providers", {}).get(provider, {})
    if evidence_class not in provider_row.get("evidence_capability_refs", []):
        raise ValueError(
            f"projection {projection.get('id')!r} {role} evidence class {evidence_class!r} is not supported by provider {provider!r}"
        )
    return AdapterRequest(
        domain_id=f"PROJECTION_AUDIT:{projection['id']}",
        provider=provider,
        source_ref=str(projection[f"{role}_subject"]),
        route_ref=route_ref,
        selector_ref=None,
        privacy_class=str(projection["privacy_class"]),
        evidence_capability_refs=(f"{EVIDENCE_PREFIX}{evidence_class}",),
        event_ref=event_ref,
        event_path=event_path,
        event_selector=_resolve_event_selector(
            projection,
            role=role,
            event_ref=event_ref,
            event_path=event_path,
            source_revision=source_revision,
        ),
    )


def _event_binding_issue(
    request: AdapterRequest,
    envelope: ProviderEvidenceEnvelope,
) -> tuple[str, str] | None:
    if request.event_ref is None:
        return None
    observed_ref = envelope.metadata.get("projection_event_ref")
    observed_path = envelope.metadata.get("projection_event_path")
    if not isinstance(observed_ref, str) or not observed_ref or not isinstance(observed_path, str) or not observed_path:
        return (
            "UNRESOLVED",
            f"EVENT_BINDING_MISSING:{request.provider}:{request.route_ref}:{request.event_ref}:{request.event_path}",
        )
    if observed_ref != request.event_ref or observed_path != request.event_path:
        return (
            "CONFLICT",
            f"EVENT_BINDING_MISMATCH:{request.provider}:{request.route_ref}:requested={request.event_ref}@{request.event_path}:observed={observed_ref}@{observed_path}",
        )
    return None


def _projection_checkpoint(
    projection_id: str,
    status: str,
    source_ref: str,
    source_path: str,
    source: ProviderEvidenceEnvelope | None,
    target: ProviderEvidenceEnvelope | None,
    unresolved: tuple[str, ...],
    audit: ProjectionAuditResult | None,
) -> dict[str, Any]:
    return {
        "referent": projection_id,
        "scope": "DURABLE_OPERATIONAL_STATE",
        "provenance": "VERA_RUNTIME_COHESION_V1",
        "purpose": "CROSS_PROVIDER_PROJECTION_RECONCILIATION",
        "sensitivity_or_privacy_class": "POINTER_ONLY",
        "minimum_necessary_payload_or_pointer": {
            "projection_id": projection_id,
            "source_ref": source_ref,
            "source_path": source_path,
            "status": status,
            "source_revision": source.revision if source is not None else None,
            "target_revision": target.revision if target is not None else None,
            "escalation_frontier": audit.escalation_frontier if audit is not None else None,
            "unresolved": list(unresolved),
        },
        "destination_eligibility": "REQUIRES_ELIGIBLE_DURABLE_PROVIDER",
        "retention_or_expiry": "UNTIL_RECONCILED_RECOVERED_EXPIRED_OR_SUPERSEDED",
        "supersession_semantics": "EXPLICIT_SUCCESSOR_OR_RECOVERY_REQUIRED; NEWEST_TIMESTAMP_DOES_NOT_SUPERSEDE",
        "non_promotion_flag": True,
    }


def _projection_result(
    projection_id: str,
    status: str,
    probes: list[AdapterProbeResult],
    source_ref: str,
    source_path: str,
    source: ProviderEvidenceEnvelope | None = None,
    target: ProviderEvidenceEnvelope | None = None,
    audit: ProjectionAuditResult | None = None,
    unresolved: tuple[str, ...] = (),
) -> ProjectionExecutionResult:
    return ProjectionExecutionResult(
        status=status,
        projection_id=projection_id,
        probes=tuple(probes),
        source_observation=source,
        target_observation=target,
        audit=audit,
        unresolved=unresolved,
        checkpoint=_projection_checkpoint(
            projection_id,
            status,
            source_ref,
            source_path,
            source,
            target,
            unresolved,
            audit,
        ),
    )


def execute_projection_cycle(
    projection_id: str,
    fabric: Mapping[str, Any],
    adapters: AdapterRegistry,
    *,
    source_ref: str,
    source_path: str,
    privacy_allowlist: set[str] | frozenset[str],
) -> ProjectionExecutionResult:
    """Probe, read, event-bind, and reconcile one registered projection.

    Scope and privacy gates run before provider I/O. The exact caller event ref
    and path cross the adapter boundary. A provider observation must independently
    bind that same event before revision/digest reconciliation may run. Collection
    targets receive their registered provider-native event selector. Matching
    revisions for a different event never qualify as VERIFIED_EXACT.
    """

    projection = _projection_by_id(fabric, projection_id)
    privacy_class = str(projection.get("privacy_class", ""))
    probes: list[AdapterProbeResult] = []

    if not _matches_pattern(source_ref, str(projection.get("source_ref_pattern", ""))) or not _matches_pattern(
        source_path, str(projection.get("source_path_pattern", ""))
    ):
        return _projection_result(
            projection_id,
            "NOT_APPLICABLE",
            probes,
            source_ref,
            source_path,
        )

    if privacy_class not in privacy_allowlist and "*" not in privacy_allowlist:
        return _projection_result(
            projection_id,
            "UNRESOLVED",
            probes,
            source_ref,
            source_path,
            unresolved=(f"PRIVACY_NOT_ELIGIBLE:{projection_id}:{privacy_class}",),
        )

    source_request = _projection_request(
        projection,
        fabric,
        role="source",
        event_ref=source_ref,
        event_path=source_path,
    )

    source_adapter = adapters.get(source_request.provider)
    if source_adapter is None:
        return _projection_result(
            projection_id,
            "UNRESOLVED",
            probes,
            source_ref,
            source_path,
            unresolved=(f"MISSING_ADAPTER:{source_request.provider}:{source_request.route_ref}",),
        )
    if getattr(source_adapter, "provider", None) != source_request.provider:
        raise ValueError("source adapter registry/provider mismatch")
    source_probe = source_adapter.probe(source_request)
    _validate_probe(source_request, source_probe)
    probes.append(source_probe)
    if source_probe.state == "UNAVAILABLE":
        return _projection_result(
            projection_id,
            "UNAVAILABLE",
            probes,
            source_ref,
            source_path,
            unresolved=(f"SOURCE_ROUTE_UNAVAILABLE:{source_request.route_ref}",),
        )
    if source_probe.state not in RETRIEVABLE_PROBE_STATES:
        return _projection_result(
            projection_id,
            "UNRESOLVED",
            probes,
            source_ref,
            source_path,
            unresolved=(f"SOURCE_ROUTE_NOT_CURRENTLY_REACHABLE:{source_request.route_ref}:{source_probe.state}",),
        )

    source_observation = source_adapter.read(source_request)
    if source_observation is None:
        return _projection_result(
            projection_id,
            "ABSENT",
            probes,
            source_ref,
            source_path,
            unresolved=(f"SOURCE_OBJECT_ABSENT:{source_request.source_ref}",),
        )
    _validate_read(source_request, source_observation)
    binding_issue = _event_binding_issue(source_request, source_observation)
    if binding_issue is not None:
        status, reason = binding_issue
        return _projection_result(
            projection_id,
            status,
            probes,
            source_ref,
            source_path,
            source=source_observation,
            unresolved=(reason,),
        )

    target_request = _projection_request(
        projection,
        fabric,
        role="target",
        event_ref=source_ref,
        event_path=source_path,
        source_revision=source_observation.revision,
    )
    target_adapter = adapters.get(target_request.provider)
    if target_adapter is None:
        return _projection_result(
            projection_id,
            "UNRESOLVED",
            probes,
            source_ref,
            source_path,
            source=source_observation,
            unresolved=(f"MISSING_ADAPTER:{target_request.provider}:{target_request.route_ref}",),
        )
    if getattr(target_adapter, "provider", None) != target_request.provider:
        raise ValueError("target adapter registry/provider mismatch")
    target_probe = target_adapter.probe(target_request)
    _validate_probe(target_request, target_probe)
    probes.append(target_probe)
    if target_probe.state == "UNAVAILABLE":
        return _projection_result(
            projection_id,
            "UNAVAILABLE",
            probes,
            source_ref,
            source_path,
            source=source_observation,
            unresolved=(f"TARGET_ROUTE_UNAVAILABLE:{target_request.route_ref}",),
        )
    if target_probe.state not in RETRIEVABLE_PROBE_STATES:
        return _projection_result(
            projection_id,
            "UNRESOLVED",
            probes,
            source_ref,
            source_path,
            source=source_observation,
            unresolved=(f"TARGET_ROUTE_NOT_CURRENTLY_REACHABLE:{target_request.route_ref}:{target_probe.state}",),
        )

    target_observation = target_adapter.read(target_request)
    if target_observation is not None:
        _validate_read(target_request, target_observation)
        binding_issue = _event_binding_issue(target_request, target_observation)
        if binding_issue is not None:
            status, reason = binding_issue
            return _projection_result(
                projection_id,
                status,
                probes,
                source_ref,
                source_path,
                source=source_observation,
                target=target_observation,
                unresolved=(reason,),
            )

    audit = audit_registered_projections(
        fabric,
        {
            projection_id: {
                "source": source_observation,
                "target": target_observation,
                "source_ref": source_ref,
                "source_path": source_path,
            }
        },
    )[0]
    unresolved = (audit.reason,) if audit.status == "UNRESOLVED" else ()
    return _projection_result(
        projection_id,
        audit.status,
        probes,
        source_ref,
        source_path,
        source=source_observation,
        target=target_observation,
        audit=audit,
        unresolved=unresolved,
    )
