from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable


_REQUIREMENT_CLASSES = {"MANDATORY", "OPTIONAL"}


def _canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("value must be canonical JSON-safe") from exc
    return encoded.encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_digest(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a 64-character SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value.lower()


@dataclass(frozen=True)
class StateComponentRef:
    component_id: str
    domain_id: str
    source_locator: str
    source_revision: str
    component_generation: str
    content_digest: str
    observed_at: str
    currentness_basis: str
    supersession_state: str
    conflict_state: str
    privacy_classification: str
    allowed_egress_scopes: frozenset[str]
    disclosure_source: str
    disclosure_generation: str
    requirement_class: str
    payload: Any | None = None
    payload_ref: str | None = None

    def __post_init__(self) -> None:
        for label in (
            "component_id", "domain_id", "source_locator", "source_revision",
            "component_generation", "observed_at", "currentness_basis",
            "supersession_state", "conflict_state", "privacy_classification",
            "disclosure_source", "disclosure_generation",
        ):
            value = getattr(self, label)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be non-empty")
        if self.requirement_class not in _REQUIREMENT_CLASSES:
            raise ValueError("requirement_class must be MANDATORY or OPTIONAL")
        if not isinstance(self.allowed_egress_scopes, frozenset) or not self.allowed_egress_scopes:
            raise ValueError("allowed_egress_scopes must be a non-empty frozenset")
        if not all(isinstance(item, str) and item for item in self.allowed_egress_scopes):
            raise ValueError("allowed_egress_scopes entries must be non-empty strings")
        _require_digest(self.content_digest, "content_digest")
        has_payload = self.payload is not None
        has_pointer = self.payload_ref is not None
        if has_payload == has_pointer:
            raise ValueError("component requires exactly one of payload or payload_ref")
        if has_pointer and (not isinstance(self.payload_ref, str) or not self.payload_ref):
            raise ValueError("payload_ref must be a non-empty immutable locator")
        if has_payload and canonical_digest(self.payload) != self.content_digest.lower():
            raise ValueError("inline payload digest does not match content_digest")

    def digest_material(self) -> dict[str, Any]:
        material: dict[str, Any] = {
            "component_id": self.component_id,
            "domain_id": self.domain_id,
            "source_locator": self.source_locator,
            "source_revision": self.source_revision,
            "component_generation": self.component_generation,
            "content_digest": self.content_digest.lower(),
            "observed_at": self.observed_at,
            "currentness_basis": self.currentness_basis,
            "supersession_state": self.supersession_state,
            "conflict_state": self.conflict_state,
            "privacy_classification": self.privacy_classification,
            "allowed_egress_scopes": sorted(self.allowed_egress_scopes),
            "disclosure_source": self.disclosure_source,
            "disclosure_generation": self.disclosure_generation,
            "requirement_class": self.requirement_class,
        }
        if self.payload is not None:
            material["payload"] = self.payload
        else:
            material["payload_ref"] = self.payload_ref
        return material


@dataclass(frozen=True)
class OmissionRecord:
    component_id: str
    domain_id: str
    reason: str
    observed_at: str
    evidence_ref: str
    requirement_class: str = "OPTIONAL"

    def __post_init__(self) -> None:
        if self.requirement_class != "OPTIONAL":
            raise ValueError("only OPTIONAL components may be represented by an omission record")
        for label in ("component_id", "domain_id", "reason", "observed_at", "evidence_ref"):
            value = getattr(self, label)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be non-empty")

    def digest_material(self) -> dict[str, str]:
        return {
            "component_id": self.component_id,
            "domain_id": self.domain_id,
            "reason": self.reason,
            "observed_at": self.observed_at,
            "evidence_ref": self.evidence_ref,
            "requirement_class": self.requirement_class,
        }


@dataclass(frozen=True)
class VeraStateComposition:
    composition_id: str
    subject: str
    components: tuple[StateComponentRef, ...]
    component_generation_vector: tuple[tuple[str, str], ...]
    composition_digest: str
    composed_at: str
    composition_policy_revision: str
    omissions: tuple[OmissionRecord, ...]


@dataclass(frozen=True)
class AdmittedVeraState:
    subject: str
    composition_digest: str
    admission_receipt_digest: str
    admitted_components: tuple[StateComponentRef, ...]
    omissions: tuple[OmissionRecord, ...]
    forbidden_domains: frozenset[str]
    admitted_disclosure_scope: str
    admission_currentness_basis: str
    admission_epoch_or_lease: str
    admitted_at: str


def compose_state(
    *,
    subject: str,
    components: Iterable[StateComponentRef],
    omissions: Iterable[OmissionRecord],
    policy_revision: str,
    composed_at: str = "UNSPECIFIED",
) -> VeraStateComposition:
    if not isinstance(subject, str) or not subject:
        raise ValueError("subject must be non-empty")
    if not isinstance(policy_revision, str) or not policy_revision:
        raise ValueError("policy_revision must be non-empty")
    component_tuple = tuple(sorted(tuple(components), key=lambda item: item.component_id))
    omission_tuple = tuple(sorted(tuple(omissions), key=lambda item: item.component_id))
    component_ids = [item.component_id for item in component_tuple]
    omission_ids = [item.component_id for item in omission_tuple]
    if len(component_ids) != len(set(component_ids)):
        raise ValueError("duplicate component_id in composition")
    if len(omission_ids) != len(set(omission_ids)):
        raise ValueError("duplicate omission component_id in composition")
    if set(component_ids) & set(omission_ids):
        raise ValueError("component cannot be both included and omitted")
    for item in component_tuple:
        if item.supersession_state != "CURRENT_OBSERVATION":
            raise ValueError(f"component {item.component_id} is not current")
        if item.conflict_state != "NONE":
            raise ValueError(f"component {item.component_id} has unresolved conflict")
    vector = tuple((item.component_id, item.component_generation) for item in component_tuple)
    digest_payload = {
        "subject": subject,
        "components": [item.digest_material() for item in component_tuple],
        "component_generation_vector": [list(item) for item in vector],
        "omissions": [item.digest_material() for item in omission_tuple],
        "composition_policy_revision": policy_revision,
    }
    digest = canonical_digest(digest_payload)
    return VeraStateComposition(
        composition_id=f"sha256:{digest}",
        subject=subject,
        components=component_tuple,
        component_generation_vector=vector,
        composition_digest=digest,
        composed_at=composed_at,
        composition_policy_revision=policy_revision,
        omissions=omission_tuple,
    )


def bind_admitted_state(
    composition: VeraStateComposition,
    *,
    admission_receipt_digest: str,
    admitted_component_ids: set[str] | frozenset[str],
    mandatory_component_ids: set[str] | frozenset[str],
    target_egress_scope: str,
    forbidden_domains: set[str] | frozenset[str],
    admission_currentness_basis: str,
    admission_epoch_or_lease: str,
    admitted_at: str,
) -> AdmittedVeraState:
    _require_digest(admission_receipt_digest, "admission_receipt_digest")
    if not isinstance(target_egress_scope, str) or not target_egress_scope:
        raise ValueError("target_egress_scope must be non-empty")
    included = {item.component_id: item for item in composition.components}
    omitted = {item.component_id: item for item in composition.omissions}
    admitted_ids = set(admitted_component_ids)
    mandatory_ids = set(mandatory_component_ids)
    unknown = admitted_ids - set(included)
    if unknown:
        raise ValueError(f"admitted component ids are not in composition: {sorted(unknown)!r}")
    missing_mandatory = mandatory_ids - admitted_ids
    if missing_mandatory:
        if missing_mandatory & set(omitted):
            raise ValueError("mandatory component cannot be satisfied by optional omission")
        raise ValueError(f"mandatory component missing from admission: {sorted(missing_mandatory)!r}")
    selected = tuple(item for item in composition.components if item.component_id in admitted_ids)
    for item in selected:
        if target_egress_scope not in item.allowed_egress_scopes:
            raise ValueError(
                f"target egress scope {target_egress_scope!r} is not explicitly allowed for {item.component_id}"
            )
    if not isinstance(admission_currentness_basis, str) or not admission_currentness_basis:
        raise ValueError("admission_currentness_basis must be non-empty")
    if not isinstance(admission_epoch_or_lease, str) or not admission_epoch_or_lease:
        raise ValueError("admission_epoch_or_lease must be non-empty")
    return AdmittedVeraState(
        subject=composition.subject,
        composition_digest=composition.composition_digest,
        admission_receipt_digest=admission_receipt_digest.lower(),
        admitted_components=selected,
        omissions=composition.omissions,
        forbidden_domains=frozenset(forbidden_domains),
        admitted_disclosure_scope=target_egress_scope,
        admission_currentness_basis=admission_currentness_basis,
        admission_epoch_or_lease=admission_epoch_or_lease,
        admitted_at=admitted_at,
    )


_FORBIDDEN_PROJECTION_INPUT_KEYS = frozenset({
    "target_behavior",
    "desired_response",
    "target_phrase",
    "expected_answer",
    "expected_output",
    "requested_emotional_display",
})


@dataclass(frozen=True)
class CapabilityBinding:
    host_identity: str
    host_revision: str
    host_generation: str
    target_provider_or_host: str
    target_egress_scope: str
    model_identity: str
    model_revision: str
    adapter_identity: str
    adapter_revision: str
    selected_backend: str
    supported_projection_backends: frozenset[str]
    backend_constraints: dict[str, Any]
    capability_digest: str
    bound_at: str


@dataclass(frozen=True)
class ProjectionEnvelope:
    admitted_state_digest: str
    capability_binding_digest: str
    projection_backend: str
    projection_digest: str
    projection_material: dict[str, Any]
    target_egress_scope: str
    binding_class: str
    causal_role: str
    projected_at: str


def bind_capability(
    admitted: AdmittedVeraState,
    *,
    host_identity: str,
    host_revision: str,
    host_generation: str,
    target_provider_or_host: str,
    target_egress_scope: str,
    model_identity: str,
    model_revision: str,
    adapter_identity: str,
    adapter_revision: str,
    requested_backend: str,
    supported_projection_backends: set[str] | frozenset[str],
    backend_constraints: dict[str, Any],
    bound_at: str,
) -> CapabilityBinding:
    fields = {
        "host_identity": host_identity,
        "host_revision": host_revision,
        "host_generation": host_generation,
        "target_provider_or_host": target_provider_or_host,
        "target_egress_scope": target_egress_scope,
        "model_identity": model_identity,
        "model_revision": model_revision,
        "adapter_identity": adapter_identity,
        "adapter_revision": adapter_revision,
        "requested_backend": requested_backend,
        "bound_at": bound_at,
    }
    for label, value in fields.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"{label} must be non-empty")
    supported = frozenset(supported_projection_backends)
    if requested_backend not in supported:
        raise ValueError(f"requested backend {requested_backend!r} is not supported by exact capability binding")
    if target_egress_scope != admitted.admitted_disclosure_scope:
        raise ValueError("capability target egress would broaden or change admitted egress scope")
    if not isinstance(backend_constraints, dict):
        raise ValueError("backend_constraints must be a JSON-safe mapping")
    material = {
        "host_identity": host_identity,
        "host_revision": host_revision,
        "host_generation": host_generation,
        "target_provider_or_host": target_provider_or_host,
        "target_egress_scope": target_egress_scope,
        "model_identity": model_identity,
        "model_revision": model_revision,
        "adapter_identity": adapter_identity,
        "adapter_revision": adapter_revision,
        "selected_backend": requested_backend,
        "supported_projection_backends": sorted(supported),
        "backend_constraints": backend_constraints,
        "admitted_state_digest": admitted.composition_digest,
    }
    return CapabilityBinding(
        host_identity=host_identity,
        host_revision=host_revision,
        host_generation=host_generation,
        target_provider_or_host=target_provider_or_host,
        target_egress_scope=target_egress_scope,
        model_identity=model_identity,
        model_revision=model_revision,
        adapter_identity=adapter_identity,
        adapter_revision=adapter_revision,
        selected_backend=requested_backend,
        supported_projection_backends=supported,
        backend_constraints=dict(backend_constraints),
        capability_digest=canonical_digest(material),
        bound_at=bound_at,
    )


def _find_forbidden_projection_key(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and key in _FORBIDDEN_PROJECTION_INPUT_KEYS:
                return key
            found = _find_forbidden_projection_key(child)
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for child in value:
            found = _find_forbidden_projection_key(child)
            if found is not None:
                return found
    return None


def project_text_context(
    admitted: AdmittedVeraState,
    capability: CapabilityBinding,
    *,
    projected_at: str = "UNSPECIFIED",
) -> ProjectionEnvelope:
    if capability.selected_backend != "TEXT_CONTEXT_V1":
        raise ValueError("TEXT_CONTEXT_V1 projection requires an exact TEXT_CONTEXT_V1 capability binding")
    if capability.target_egress_scope != admitted.admitted_disclosure_scope:
        raise ValueError("projection egress does not match admitted disclosure scope")
    components: list[dict[str, Any]] = []
    for component in admitted.admitted_components:
        if component.domain_id in admitted.forbidden_domains:
            raise ValueError(f"forbidden projection domain: {component.domain_id}")
        if capability.target_egress_scope not in component.allowed_egress_scopes:
            raise ValueError(f"projection egress is not allowed for {component.component_id}")
        if component.payload is not None:
            forbidden_key = _find_forbidden_projection_key(component.payload)
            if forbidden_key is not None:
                raise ValueError(f"forbidden projection input key: {forbidden_key}")
            state_material: dict[str, Any] = {"payload": component.payload}
        else:
            state_material = {
                "payload_ref": component.payload_ref,
                "content_digest": component.content_digest.lower(),
            }
        components.append({
            "component_id": component.component_id,
            "domain_id": component.domain_id,
            "source_revision": component.source_revision,
            "component_generation": component.component_generation,
            **state_material,
        })
    projection_material: dict[str, Any] = {
        "schema": "VERA_TEXT_CONTEXT_V1",
        "subject": admitted.subject,
        "composition_digest": admitted.composition_digest,
        "admission_receipt_digest": admitted.admission_receipt_digest,
        "host_identity": capability.host_identity,
        "host_revision": capability.host_revision,
        "host_generation": capability.host_generation,
        "model_identity": capability.model_identity,
        "model_revision": capability.model_revision,
        "adapter_identity": capability.adapter_identity,
        "adapter_revision": capability.adapter_revision,
        "target_egress_scope": capability.target_egress_scope,
        "components": components,
        "omissions": [item.digest_material() for item in admitted.omissions],
        "claim_ceiling": "PROMPT_REQUEST_CONDITIONING_ONLY",
    }
    maximum = capability.backend_constraints.get("max_chars")
    if maximum is not None:
        if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
            raise ValueError("TEXT_CONTEXT_V1 max_chars must be a positive integer")
        if len(_canonical_bytes(projection_material).decode("utf-8")) > maximum:
            raise ValueError("TEXT_CONTEXT_V1 projection exceeds max_chars capability")
    return ProjectionEnvelope(
        admitted_state_digest=admitted.composition_digest,
        capability_binding_digest=capability.capability_digest,
        projection_backend="TEXT_CONTEXT_V1",
        projection_digest=canonical_digest(projection_material),
        projection_material=projection_material,
        target_egress_scope=capability.target_egress_scope,
        binding_class="PROMPT_BOUND",
        causal_role="INSTRUCTION_CONDITIONED",
        projected_at=projected_at,
    )
