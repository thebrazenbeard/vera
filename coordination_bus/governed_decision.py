"""Verifier-bound decision authority for the public Coordination Bus v1.

A DECISION event is not authorized by a caller-supplied permission string. It
requires a verifier-issued, full-subject, single-use envelope from a runtime-
owned authority. The envelope grants permission to persist one exact draft; it
does not make the event's content substantively correct or grant merge,
production, deployment, or execution authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import hmac
import json
from typing import Any, Mapping, Protocol, runtime_checkable

from .contracts import CoordinationEventDraft, canonicalize, validate_text
from .core import _receipted
from .strict_contract import ActorContext
from .verified_temporal import (
    CoordinationBus as _VerifierBoundCoordinationBus,
    ReceiptTimeProvider,
    TemporalEvidenceVerifier,
)

DECISION_AUTHORITY_SCHEMA = "VERA_COORDINATION_DECISION_AUTHORITY_V1"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def decision_subject(actor: ActorContext, draft: CoordinationEventDraft) -> str:
    """Bind authority to the complete canonical decision operation."""

    actor.validate()
    draft.validate()
    body: Mapping[str, Any] = {
        "operation": "coordination_post",
        "actor_workstream": actor.canonical_workstream,
        "draft": draft.canonical_dict(),
    }
    return "coordination-decision-v1:" + sha256(_canonical_bytes(body)).hexdigest()


@dataclass(frozen=True)
class DecisionAuthorityEnvelope:
    schema: str
    issuer_id: str
    authorization_id: str
    subject: str
    verification_token: str

    def canonical_body(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "issuer_id": self.issuer_id,
            "authorization_id": self.authorization_id,
            "subject": self.subject,
        }

    def as_dict(self) -> dict[str, Any]:
        return canonicalize(asdict(self))


@runtime_checkable
class DecisionAuthorityVerifier(Protocol):
    def verify(
        self,
        envelope: DecisionAuthorityEnvelope,
        *,
        expected_subject: str,
    ) -> bool:
        ...


class HmacDecisionAuthority:
    """Reference single-use decision issuer/verifier with an external HMAC key."""

    def __init__(self, issuer_id: str, secret: bytes) -> None:
        validate_text(issuer_id, "issuer_id")
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ValueError("secret must be at least 32 bytes")
        self.issuer_id = issuer_id
        self._secret = secret
        self._used_tokens: set[str] = set()

    def issue(
        self,
        *,
        authorization_id: str,
        subject: str,
    ) -> DecisionAuthorityEnvelope:
        validate_text(authorization_id, "authorization_id")
        validate_text(subject, "decision subject")
        unsigned = DecisionAuthorityEnvelope(
            schema=DECISION_AUTHORITY_SCHEMA,
            issuer_id=self.issuer_id,
            authorization_id=authorization_id,
            subject=subject,
            verification_token="",
        )
        token = hmac.new(
            self._secret,
            _canonical_bytes(unsigned.canonical_body()),
            sha256,
        ).hexdigest()
        return replace(unsigned, verification_token=token)

    def verify(
        self,
        envelope: DecisionAuthorityEnvelope,
        *,
        expected_subject: str,
    ) -> bool:
        try:
            if not isinstance(envelope, DecisionAuthorityEnvelope):
                return False
            if envelope.schema != DECISION_AUTHORITY_SCHEMA:
                return False
            if envelope.issuer_id != self.issuer_id:
                return False
            validate_text(envelope.authorization_id, "authorization_id")
            if envelope.subject != expected_subject:
                return False
            expected = hmac.new(
                self._secret,
                _canonical_bytes(envelope.canonical_body()),
                sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, envelope.verification_token):
                return False
            replay_key = f"{envelope.issuer_id}:{envelope.verification_token}"
            if replay_key in self._used_tokens:
                return False
            self._used_tokens.add(replay_key)
            return True
        except (TypeError, ValueError):
            return False


class CoordinationBus(_VerifierBoundCoordinationBus):
    """Public bus with verifier-bound temporal and decision authority."""

    def __init__(
        self,
        repository: Any,
        *,
        evidence_verifier: TemporalEvidenceVerifier | None = None,
        receipt_time_provider: ReceiptTimeProvider | None = None,
        decision_verifier: DecisionAuthorityVerifier | None = None,
    ) -> None:
        super().__init__(
            repository,
            evidence_verifier=evidence_verifier,
            receipt_time_provider=receipt_time_provider,
        )
        self._decision_verifier = decision_verifier

    @_receipted("coordination_post")
    def coordination_post(
        self,
        actor: ActorContext,
        draft: CoordinationEventDraft,
        *,
        decision_authority: DecisionAuthorityEnvelope | None = None,
    ):
        if draft.event_type != "DECISION":
            if decision_authority is not None:
                raise ValueError(
                    "decision_authority may be supplied only for a DECISION event"
                )
            return super().coordination_post(actor, draft)

        actor.validate()
        draft.validate()
        if draft.source_branch != actor.canonical_workstream:
            raise PermissionError("source_branch must equal actor workstream")
        if decision_authority is None:
            raise PermissionError(
                "DECISION requires verifier-issued external authority; "
                "caller permissions are not authority"
            )
        if self._decision_verifier is None:
            raise PermissionError(
                "DECISION requires an injected trusted decision verifier"
            )
        subject = decision_subject(actor, draft)
        if not self._decision_verifier.verify(
            decision_authority,
            expected_subject=subject,
        ):
            raise PermissionError(
                "decision authority verification failed for the complete draft subject"
            )
        return self._append("coordination_post", actor, draft)
