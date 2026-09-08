from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .evidence import ProviderEvidenceEnvelope


PROBE_STATES = {
    "ELIGIBLE_FOR_OPERATION",
    "CURRENTLY_OBSERVED_REACHABLE",
    "RESULT",
    "UNAVAILABLE",
    "UNKNOWN",
}


@dataclass(frozen=True)
class AdapterRequest:
    domain_id: str
    provider: str
    source_ref: str
    route_ref: str
    selector_ref: str | None
    privacy_class: str
    evidence_capability_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("domain_id", "provider", "source_ref", "route_ref", "privacy_class"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be non-empty")
        if not self.evidence_capability_refs:
            raise ValueError("evidence_capability_refs must be non-empty")


@dataclass(frozen=True)
class AdapterProbeResult:
    provider: str
    route_ref: str
    state: str
    observed_at: str
    reason: str

    def __post_init__(self) -> None:
        if not self.provider or not self.route_ref or not self.observed_at:
            raise ValueError("probe provider/route_ref/observed_at must be non-empty")
        if self.state not in PROBE_STATES:
            raise ValueError(f"unsupported adapter probe state: {self.state}")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("probe reason must be non-empty")


class ProviderAdapter(Protocol):
    provider: str

    def probe(self, request: AdapterRequest) -> AdapterProbeResult: ...

    def read(self, request: AdapterRequest) -> ProviderEvidenceEnvelope: ...


class AdapterRegistry:
    """Runtime-owned adapter lookup; adapters do not carry policy authority."""

    def __init__(self, adapters: Mapping[str, ProviderAdapter]):
        self._adapters = dict(adapters)

    def get(self, provider: str) -> ProviderAdapter | None:
        return self._adapters.get(provider)

    def providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))
