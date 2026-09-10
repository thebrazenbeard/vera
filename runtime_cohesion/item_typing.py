from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from types import MappingProxyType
from typing import Mapping, Protocol
import weakref

from .adapters import AdapterRequest
from .evidence import (
    ALLOWED_CONFLICT_STATES,
    ALLOWED_SUPERSESSION_STATES,
    ProviderEvidenceEnvelope,
)


@dataclass(frozen=True)
class ProviderItemTypeProof:
    """Runtime-owned provenance/type/currentness result for one returned item.

    The proof is deliberately separate from ``ProviderEvidenceEnvelope`` and
    from ``AdapterRegistry``. An ordinary retrieval adapter may return an item,
    but it cannot certify the item's evidence class merely by placing a class
    name inside that returned envelope. A separately composed runtime verifier
    must derive the type/currentness result from provider/object/receipt
    provenance and bind it to the exact returned object. Projection reads also
    bind the exact requested event ref/path here so audit/replay cannot qualify
    on weaker event evidence than the executing read path.

    This is a supported-API/process trust boundary, not cryptographic isolation
    from arbitrary hostile code already executing inside the same process.
    """

    issuer_provider: str
    route_ref: str
    source_ref: str
    locator: str
    revision: str
    observed_at: str
    derived_evidence_class: str
    currentness_basis: str
    supersession_state: str
    conflict_state: str
    validation_method: str
    provenance_ref: str
    content_digest: str | None = None
    receipt_ref: str | None = None
    event_ref: str | None = None
    event_path: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "issuer_provider",
            "route_ref",
            "source_ref",
            "locator",
            "revision",
            "observed_at",
            "derived_evidence_class",
            "currentness_basis",
            "validation_method",
            "provenance_ref",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.supersession_state not in ALLOWED_SUPERSESSION_STATES:
            raise ValueError(f"unsupported item-type supersession_state: {self.supersession_state}")
        if self.conflict_state not in ALLOWED_CONFLICT_STATES:
            raise ValueError(f"unsupported item-type conflict_state: {self.conflict_state}")
        if self.content_digest is not None and (not isinstance(self.content_digest, str) or not self.content_digest.strip()):
            raise ValueError("content_digest must be non-empty when supplied")
        if self.receipt_ref is not None and (not isinstance(self.receipt_ref, str) or not self.receipt_ref.strip()):
            raise ValueError("receipt_ref must be non-empty when supplied")
        if (self.event_ref is None) != (self.event_path is None):
            raise ValueError("item-type event_ref and event_path must be supplied together")
        if self.event_ref is not None:
            if not isinstance(self.event_ref, str) or not self.event_ref:
                raise ValueError("item-type event_ref must be non-empty when supplied")
            if not isinstance(self.event_path, str) or not self.event_path:
                raise ValueError("item-type event_path must be non-empty when supplied")
        candidate = self.observed_at[:-1] + "+00:00" if self.observed_at.endswith("Z") else self.observed_at
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError("item-type observed_at must be valid ISO-8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("item-type observed_at must be timezone-aware")


class ProviderItemTypeVerifier(Protocol):
    provider: str

    def verify(
        self,
        request: AdapterRequest,
        envelope: ProviderEvidenceEnvelope,
    ) -> ProviderItemTypeProof | None: ...


@dataclass(frozen=True)
class ValidatedItemType:
    issuer_provider: str
    route_ref: str
    source_ref: str
    locator: str
    revision: str
    observed_at: str
    derived_evidence_class: str
    currentness_basis: str
    supersession_state: str
    conflict_state: str
    validation_method: str
    provenance_ref: str
    content_digest: str | None
    receipt_ref: str | None
    event_ref: str | None
    event_path: str | None


_COMPOSITION_LOCK = RLock()
_RUNTIME_ITEM_TYPE_VERIFIERS: Mapping[str, ProviderItemTypeVerifier] | None = None
_REGISTRY_LOCK = RLock()
_VALIDATED_ITEMS: dict[
    int,
    tuple[weakref.ReferenceType[ProviderEvidenceEnvelope], ValidatedItemType],
] = {}


def _install_item_type_verifiers(verifiers: Mapping[str, ProviderItemTypeVerifier]) -> None:
    """Install one runtime-owned item-typing verifier composition.

    This composition is intentionally distinct from ordinary retrieval adapters.
    Public executor callers cannot pass a replacement verifier mapping per call.
    """

    if not isinstance(verifiers, Mapping) or not verifiers:
        raise ValueError("item-type verifier composition must be a non-empty mapping")
    normalized: dict[str, ProviderItemTypeVerifier] = {}
    for provider, verifier in verifiers.items():
        if not isinstance(provider, str) or not provider:
            raise ValueError("item-type verifier provider keys must be non-empty strings")
        if getattr(verifier, "provider", None) != provider:
            raise ValueError(f"item-type verifier provider mismatch for {provider!r}")
        if not callable(getattr(verifier, "verify", None)):
            raise ValueError(f"item-type verifier for {provider!r} lacks verify")
        normalized[provider] = verifier

    global _RUNTIME_ITEM_TYPE_VERIFIERS
    with _COMPOSITION_LOCK:
        if _RUNTIME_ITEM_TYPE_VERIFIERS is None:
            _RUNTIME_ITEM_TYPE_VERIFIERS = MappingProxyType(dict(normalized))
            return
        existing = _RUNTIME_ITEM_TYPE_VERIFIERS
        if set(existing) == set(normalized) and all(existing[key] is normalized[key] for key in existing):
            return
        raise RuntimeError("runtime item-type verifier composition is already installed and cannot be replaced")


def _reset_item_type_verifiers_for_tests() -> None:
    """Private test-isolation hook; never a provider/currentness operation."""

    global _RUNTIME_ITEM_TYPE_VERIFIERS
    with _COMPOSITION_LOCK:
        _RUNTIME_ITEM_TYPE_VERIFIERS = None
    with _REGISTRY_LOCK:
        _VALIDATED_ITEMS.clear()


def _runtime_item_type_verifier(provider: str) -> ProviderItemTypeVerifier | None:
    with _COMPOSITION_LOCK:
        verifiers = _RUNTIME_ITEM_TYPE_VERIFIERS
        return None if verifiers is None else verifiers.get(provider)


def _register_validated_item(envelope: ProviderEvidenceEnvelope, validated: ValidatedItemType) -> None:
    key = id(envelope)

    def cleanup(ref, *, registry_key=key):
        with _REGISTRY_LOCK:
            current = _VALIDATED_ITEMS.get(registry_key)
            if current is not None and current[0] is ref:
                _VALIDATED_ITEMS.pop(registry_key, None)

    with _REGISTRY_LOCK:
        _VALIDATED_ITEMS[key] = (weakref.ref(envelope, cleanup), validated)


def validated_item_type(
    request: AdapterRequest,
    envelope: ProviderEvidenceEnvelope,
) -> ValidatedItemType | None:
    """Derive and cross-bind an item's actual type/currentness independently.

    The retrieval target capability set is intentionally ignored here. The
    caller compares the independently derived class against both the envelope
    claim and the capability ceiling only *after* this boundary succeeds.
    Domain-specific referent policy is intentionally absent from this primitive.
    """

    verifier = _runtime_item_type_verifier(request.provider)
    if verifier is None:
        return None
    try:
        proof = verifier.verify(request, envelope)
    except Exception:
        return None
    if not isinstance(proof, ProviderItemTypeProof):
        return None

    exact_pairs = (
        (proof.issuer_provider, request.provider),
        (proof.route_ref, request.route_ref),
        (proof.source_ref, request.source_ref),
        (proof.locator, envelope.locator),
        (proof.revision, envelope.revision),
        (proof.observed_at, envelope.observed_at),
        (proof.currentness_basis, envelope.currentness_basis),
        (proof.supersession_state, envelope.supersession_state),
        (proof.conflict_state, envelope.conflict_state),
        (proof.content_digest, envelope.content_digest),
        (proof.receipt_ref, envelope.receipt_ref),
        (proof.event_ref, request.event_ref),
        (proof.event_path, request.event_path),
    )
    if any(actual != expected for actual, expected in exact_pairs):
        return None

    validated = ValidatedItemType(
        issuer_provider=proof.issuer_provider,
        route_ref=proof.route_ref,
        source_ref=proof.source_ref,
        locator=proof.locator,
        revision=proof.revision,
        observed_at=proof.observed_at,
        derived_evidence_class=proof.derived_evidence_class,
        currentness_basis=proof.currentness_basis,
        supersession_state=proof.supersession_state,
        conflict_state=proof.conflict_state,
        validation_method=proof.validation_method,
        provenance_ref=proof.provenance_ref,
        content_digest=proof.content_digest,
        receipt_ref=proof.receipt_ref,
        event_ref=proof.event_ref,
        event_path=proof.event_path,
    )
    _register_validated_item(envelope, validated)
    return validated


def validated_item_event_binding(
    envelope: ProviderEvidenceEnvelope,
    *,
    provider: str,
    route_ref: str,
    source_ref: str,
    event_ref: str,
    event_path: str,
) -> ValidatedItemType | None:
    """Resolve the exact event identity already proven for this live item object.

    Audit/replay surfaces can consume this proof but cannot mint it from envelope
    metadata. The proof originates only from the separately composed runtime-owned
    item verifier used at the provider read boundary.
    """

    key = id(envelope)
    with _REGISTRY_LOCK:
        entry = _VALIDATED_ITEMS.get(key)
        validated = entry[1] if entry is not None and entry[0]() is envelope else None
    if validated is None:
        return None
    expected = (
        provider,
        route_ref,
        source_ref,
        envelope.locator,
        envelope.revision,
        envelope.observed_at,
        envelope.currentness_basis,
        envelope.supersession_state,
        envelope.conflict_state,
        envelope.content_digest,
        envelope.receipt_ref,
        event_ref,
        event_path,
    )
    observed = (
        validated.issuer_provider,
        validated.route_ref,
        validated.source_ref,
        validated.locator,
        validated.revision,
        validated.observed_at,
        validated.currentness_basis,
        validated.supersession_state,
        validated.conflict_state,
        validated.content_digest,
        validated.receipt_ref,
        validated.event_ref,
        validated.event_path,
    )
    return validated if observed == expected else None
