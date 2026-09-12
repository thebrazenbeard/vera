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
