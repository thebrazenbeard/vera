"""Trusted temporal-evidence boundary for the public V.E.R.A. coordination bus.

Non-UNKNOWN temporal evidence is accepted only inside a verifier-issued envelope
bound to an issuer, temporal role, operation subject, evidence value, precision,
and bounds. UNKNOWN evidence remains usable without external verification.

The reference HMAC authority is suitable for tests and bounded runtimes where
the signing secret is held outside untrusted callers. Production may inject any
verifier implementing ``TemporalEvidenceVerifier``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import hmac
import json
from typing import Any, Callable, Protocol, runtime_checkable

from .contracts import ActorContext, canonicalize, validate_text
from .core import _receipted
from .temporal import (
    CoordinationBus as _TemporalCoordinationBus,
    TemporalCoordinationResult,
    TemporalEvidence,
)


EVIDENCE_ENVELOPE_SCHEMA = "VERA_TEMPORAL_EVIDENCE_ENVELOPE_V1"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class TemporalEvidenceEnvelope:
    """Opaque verifier-issued binding around one temporal evidence claim."""

    schema: str
    issuer_id: str
    role: str
    subject: str
    evidence: TemporalEvidence
    verification_token: str

    def canonical_body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "issuer_id": self.issuer_id,
            "role": self.role,
            "subject": self.subject,
            "evidence": self.evidence.as_dict(),
        }

    def as_dict(self) -> dict[str, Any]:
        return canonicalize(asdict(self))


@runtime_checkable
class TemporalEvidenceVerifier(Protocol):
    """Runtime trust boundary for non-UNKNOWN temporal evidence."""

    def verify(
        self,
        envelope: TemporalEvidenceEnvelope,
        *,
        expected_role: str,
        expected_subject: str,
    ) -> bool:
        ...


class HmacTemporalEvidenceAuthority:
    """Reference issuer/verifier using an externally held HMAC-SHA256 secret."""

    def __init__(self, issuer_id: str, secret: bytes) -> None:
        validate_text(issuer_id, "issuer_id")
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ValueError("secret must be at least 32 bytes")
        self.issuer_id = issuer_id
        self._secret = secret

    def issue(
        self,
        evidence: TemporalEvidence,
        *,
        role: str,
        subject: str,
    ) -> TemporalEvidenceEnvelope:
        validate_text(role, "temporal role")
        validate_text(subject, "temporal subject")
        evidence.validate(role=role)
        unsigned = TemporalEvidenceEnvelope(
            schema=EVIDENCE_ENVELOPE_SCHEMA,
            issuer_id=self.issuer_id,
            role=role,
            subject=subject,
            evidence=evidence,
            verification_token="",
        )
        token = hmac.new(
            self._secret, _canonical_bytes(unsigned.canonical_body()), sha256
        ).hexdigest()
        return replace(unsigned, verification_token=token)

    def verify(
        self,
        envelope: TemporalEvidenceEnvelope,
        *,
        expected_role: str,
        expected_subject: str,
    ) -> bool:
        try:
            if not isinstance(envelope, TemporalEvidenceEnvelope):
                return False
            if envelope.schema != EVIDENCE_ENVELOPE_SCHEMA:
                return False
            if envelope.issuer_id != self.issuer_id:
                return False
            if envelope.role != expected_role:
                return False
            if envelope.subject != expected_subject:
                return False
            envelope.evidence.validate(role=expected_role)
            expected = hmac.new(
                self._secret,
                _canonical_bytes(envelope.canonical_body()),
                sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, envelope.verification_token)
        except (TypeError, ValueError):
            return False


TemporalEvidenceInput = TemporalEvidence | TemporalEvidenceEnvelope | None
ReceiptTimeProvider = Callable[[str, str], TemporalEvidenceInput]


def entry_checkpoint_subject(
    workstream: str, after_sequence: int, limit: int
) -> str:
    return (
        f"coordination-entry:{workstream}:"
        f"after_sequence={after_sequence}:limit={limit}"
    )


def acknowledgement_subject(event_id: str) -> str:
    return f"coordination-acknowledgement:event_id={event_id}"


def exit_checkpoint_subject(
    workstream: str, thread_key: str, target_branch: str | None
) -> str:
    target = target_branch if target_branch is not None else "NONE"
    return (
        f"coordination-exit:{workstream}:"
        f"thread_key={thread_key}:target_branch={target}"
    )


def receipt_subject(result: Any) -> str:
    """Bind receipt evidence to the deterministic operation-result identity."""

    receipt = result.receipt
    body = {
        "operation": receipt.operation,
        "result_class": receipt.result_class,
        "actor_workstream": receipt.actor_workstream,
        "thread_key": receipt.thread_key,
        "event_id": receipt.event_id,
        "event_sequence": receipt.event_sequence,
        "target_branch": receipt.target_branch,
        "base_result_hash": receipt.result_hash,
    }
    return "coordination-receipt:" + sha256(_canonical_bytes(body)).hexdigest()


class CoordinationBus(_TemporalCoordinationBus):
    """Strict public bus with verifier-bound non-UNKNOWN temporal evidence."""

    def __init__(
        self,
        repository: Any,
        *,
        evidence_verifier: TemporalEvidenceVerifier | None = None,
        receipt_time_provider: ReceiptTimeProvider | None = None,
    ) -> None:
        # The parent provider is deliberately disabled. Receipt evidence is
        # verified here before it is attached to the public receipt.
        super().__init__(repository, receipt_time_provider=None)
        self._evidence_verifier = evidence_verifier
        self._trusted_receipt_time_provider = receipt_time_provider

    def _verified_claim(
        self,
        value: TemporalEvidenceInput,
        *,
        role: str,
        subject: str,
    ) -> TemporalEvidence | None:
        if value is None:
            return None
        if isinstance(value, TemporalEvidence):
            value.validate(role=role)
            if value.precision != "UNKNOWN":
                raise ValueError(
                    f"non-UNKNOWN {role} requires a verifier-issued "
                    "TemporalEvidenceEnvelope"
                )
            return value
        if not isinstance(value, TemporalEvidenceEnvelope):
            raise TypeError(
                f"{role} must be TemporalEvidence, "
                "TemporalEvidenceEnvelope, or None"
            )
        if self._evidence_verifier is None:
            raise ValueError(
                f"non-UNKNOWN {role} requires an injected trusted verifier"
            )
        if not self._evidence_verifier.verify(
            value,
            expected_role=role,
            expected_subject=subject,
        ):
            raise ValueError(
                f"temporal evidence verification failed for role {role!r} "
                f"and subject {subject!r}"
            )
        return value.evidence

    def _wrap(self, result: Any, **kwargs: Any) -> TemporalCoordinationResult:
        wrapped = super()._wrap(result, **kwargs)
        provider = self._trusted_receipt_time_provider
        if provider is None:
            return wrapped

        subject = receipt_subject(result)
        try:
            candidate = provider("receipt_time", subject)
            verified = self._verified_claim(
                candidate,
                role="receipt_time",
                subject=subject,
            )
            receipt_time = (
                verified
                if verified is not None
                else TemporalEvidence.unknown("RECEIPT_TIME_UNAVAILABLE")
            )
        except (TypeError, ValueError):
            receipt_time = TemporalEvidence.unknown(
                "UNVERIFIED_RECEIPT_TIME_REJECTED"
            )

        # Parent result_hash already excludes receipt_time. Replacing only this
        # field preserves deterministic hashing across receipt-generation times.
        return replace(
            wrapped,
            receipt=replace(wrapped.receipt, receipt_time=receipt_time),
        )

    @_receipted("coordination_entry_checkpoint")
    def entry_checkpoint(
        self,
        actor: ActorContext,
        *,
        after_sequence: int = 0,
        limit: int = 100,
        entry_time: TemporalEvidenceInput = None,
        retrieval_time: TemporalEvidenceInput = None,
    ) -> TemporalCoordinationResult:
        subject = entry_checkpoint_subject(
            actor.workstream, after_sequence, limit
        )
        entry = self._verified_claim(
            entry_time, role="entry_time", subject=subject
        )
        retrieval = self._verified_claim(
            retrieval_time, role="retrieval_time", subject=subject
        )
        return super().entry_checkpoint(
            actor,
            after_sequence=after_sequence,
            limit=limit,
            entry_time=entry,
            retrieval_time=retrieval,
        )

    @_receipted("coordination_acknowledge")
    def coordination_acknowledge(
        self,
        actor: ActorContext,
        *,
        event_id: str,
        summary: str,
        acknowledgement_time: TemporalEvidenceInput = None,
        consumption_time: TemporalEvidenceInput = None,
        payload: dict[str, Any] | None = None,
        reference_data: dict[str, Any] | None = None,
    ) -> TemporalCoordinationResult:
        subject = acknowledgement_subject(event_id)
        acknowledgement = self._verified_claim(
            acknowledgement_time,
            role="acknowledgement_time",
            subject=subject,
        )
        consumption = self._verified_claim(
            consumption_time,
            role="consumption_time",
            subject=subject,
        )
        return super().coordination_acknowledge(
            actor,
            event_id=event_id,
            summary=summary,
            acknowledgement_time=acknowledgement,
            consumption_time=consumption,
            payload=payload,
            reference_data=reference_data,
        )

    @_receipted("coordination_exit_checkpoint")
    def exit_checkpoint(
        self,
        actor: ActorContext,
        *,
        thread_key: str,
        target_branch: str | None,
        objective: str,
        summary: str,
        material: bool,
        status: str = "IN_PROGRESS",
        active_issue: str | None = None,
        acknowledges_event_id: str | None = None,
        event_time: TemporalEvidenceInput = None,
        state_time: TemporalEvidenceInput = None,
        reference_data: dict[str, Any] | None = None,
    ) -> TemporalCoordinationResult:
        subject = exit_checkpoint_subject(
            actor.workstream, thread_key, target_branch
        )
        event = self._verified_claim(
            event_time, role="event_time", subject=subject
        )
        state = self._verified_claim(
            state_time, role="state_time", subject=subject
        )
        return super().exit_checkpoint(
            actor,
            thread_key=thread_key,
            target_branch=target_branch,
            objective=objective,
            summary=summary,
            material=material,
            status=status,
            active_issue=active_issue,
            acknowledges_event_id=acknowledges_event_id,
            event_time=event,
            state_time=state,
            reference_data=reference_data,
        )
