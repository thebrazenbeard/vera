"""Runtime-owned verification for V.E.R.A. temporal evidence claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import hmac
import json
from typing import Any, Mapping, Protocol

from .contracts import canonicalize, validate_text

TEMPORAL_PRECISIONS = frozenset({"EXACT", "BOUNDED", "APPROXIMATE", "UNKNOWN"})
_RECORD_TIME_SOURCES = frozenset({"DATABASE_RECORD_TIME", "COORDINATION_RECORD_TIME"})
_EVIDENCE_SCHEMA = "VERA_TEMPORAL_EVIDENCE_V2"
_BINDING_SCHEMA = "VERA_TEMPORAL_EVIDENCE_BINDING_V1"


def _aware(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{name} must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone offset")
    return parsed


def canonical_hash(value: Any) -> str:
    return sha256(json.dumps(
        canonicalize(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TemporalEvidenceBinding:
    """Exact role and operation subject to which evidence is bound."""

    role: str
    actor_workstream: str
    operation: str
    subject_hash: str
    thread_key: str | None = None
    source_event_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        role: str,
        actor_workstream: str,
        operation: str,
        subject: Mapping[str, Any],
        thread_key: str | None = None,
        source_event_id: str | None = None,
    ) -> "TemporalEvidenceBinding":
        validate_text(role, "temporal role")
        validate_text(actor_workstream, "actor_workstream")
        validate_text(operation, "operation")
        if thread_key is not None:
            validate_text(thread_key, "thread_key")
        if source_event_id is not None:
            validate_text(source_event_id, "source_event_id")
        return cls(
            role=role,
            actor_workstream=actor_workstream,
            operation=operation,
            subject_hash=canonical_hash(subject),
            thread_key=thread_key,
            source_event_id=source_event_id,
        )

    def as_dict(self) -> dict[str, Any]:
        return canonicalize({"schema": _BINDING_SCHEMA, **asdict(self)})

    @property
    def binding_hash(self) -> str:
        return canonical_hash(self.as_dict())


@dataclass(frozen=True)
class TemporalEvidence:
    """Untrusted claim. It contains no caller-controlled ``verified`` flag."""

    precision: str
    source: str
    value: str | None = None
    lower_bound: str | None = None
    upper_bound: str | None = None
    reference_id: str | None = None
    binding: TemporalEvidenceBinding | None = None
    verification_token: str | None = None

    @classmethod
    def unknown(cls, source: str = "UNAVAILABLE") -> "TemporalEvidence":
        return cls("UNKNOWN", source)

    @classmethod
    def exact(
        cls,
        value: str,
        *,
        source: str,
        reference_id: str,
        binding: TemporalEvidenceBinding,
        verification_token: str,
    ) -> "TemporalEvidence":
        return cls(
            "EXACT", source, value=value, reference_id=reference_id,
            binding=binding, verification_token=verification_token,
        )

    def claim_dict(self) -> dict[str, Any]:
        return canonicalize({
            "schema": _EVIDENCE_SCHEMA,
            "precision": self.precision,
            "source": self.source,
            "value": self.value,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "reference_id": self.reference_id,
        })

    def validate_shape(self, *, role: str) -> None:
        if self.precision not in TEMPORAL_PRECISIONS:
            raise ValueError(f"unsupported temporal precision {self.precision!r}")
        validate_text(self.source, "temporal source")
        if self.precision == "UNKNOWN":
            if any(value is not None for value in (
                self.value, self.lower_bound, self.upper_bound,
                self.reference_id, self.binding, self.verification_token,
            )):
                raise ValueError("UNKNOWN evidence forbids claims, bindings, and tokens")
            return
        if role != "record_time" and self.source in _RECORD_TIME_SOURCES:
            raise ValueError(f"database record_time cannot substitute for {role}")
        validate_text(self.reference_id or "", "temporal reference_id")
        validate_text(self.verification_token or "", "temporal verification_token")
        if self.binding is None:
            raise ValueError("non-UNKNOWN evidence requires a verifier binding")
        if self.value is None:
            raise ValueError(f"{self.precision} evidence requires value")
        value = _aware(self.value, f"{role}.value")
        if self.precision == "BOUNDED":
            if self.lower_bound is None or self.upper_bound is None:
                raise ValueError("BOUNDED evidence requires both inclusive bounds")
            lower = _aware(self.lower_bound, f"{role}.lower_bound")
            upper = _aware(self.upper_bound, f"{role}.upper_bound")
            if lower > upper or not lower <= value <= upper:
                raise ValueError("BOUNDED evidence has inconsistent bounds")
        elif self.lower_bound is not None or self.upper_bound is not None:
            raise ValueError(f"{self.precision} evidence forbids hard bounds")


class TemporalEvidenceVerifier(Protocol):
    verifier_id: str

    def is_trusted_source(self, source: str) -> bool: ...

    def verify(
        self,
        evidence: TemporalEvidence,
        binding: TemporalEvidenceBinding,
    ) -> bool: ...


def temporal_evidence_message(
    evidence: TemporalEvidence,
    binding: TemporalEvidenceBinding,
) -> bytes:
    return json.dumps(
        canonicalize({"claim": evidence.claim_dict(), "binding": binding.as_dict()}),
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")


class HmacTemporalEvidenceVerifier:
    """Reference opaque-token verifier owned by the runtime, not the caller."""

    def __init__(
        self,
        issuer_keys: Mapping[str, bytes],
        *,
        verifier_id: str = "HMAC_SHA256_TEMPORAL_VERIFIER_V1",
    ) -> None:
        validate_text(verifier_id, "verifier_id")
        normalized: dict[str, bytes] = {}
        for issuer, key in issuer_keys.items():
            validate_text(issuer, "issuer")
            if not isinstance(key, bytes) or not key:
                raise ValueError("issuer keys must be non-empty bytes")
            normalized[issuer] = bytes(key)
        if not normalized:
            raise ValueError("at least one trusted temporal issuer is required")
        self._issuer_keys = normalized
        self.verifier_id = verifier_id

    def is_trusted_source(self, source: str) -> bool:
        return source in self._issuer_keys

    def verify(
        self,
        evidence: TemporalEvidence,
        binding: TemporalEvidenceBinding,
    ) -> bool:
        key = self._issuer_keys.get(evidence.source)
        token = evidence.verification_token
        if key is None or token is None:
            return False
        expected = hmac.new(
            key, temporal_evidence_message(evidence, binding), sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, token)
