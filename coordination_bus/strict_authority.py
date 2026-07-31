"""Strict public authority boundary for V.E.R.A. coordination bus v1.

Legacy stored addresses remain decodable, but new actors may not enter through an
obsolete route. A caller-supplied permission is also insufficient to publish a
DECISION: the exact actor and canonical decision draft require a verifier-issued,
single-use authority envelope.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import hmac
import json
from typing import Any, Iterable, Protocol, runtime_checkable
from uuid import uuid4

from .contracts import (
    ActorContext as _CompatibilityActorContext,
    CoordinationEventDraft,
    OBSOLETE_WORKSTREAMS,
    canonicalize,
    validate_text,
)
from .core import CoordinationBus as _BaseCoordinationBus, _receipted
from .verified_temporal import CoordinationBus as _VerifierBoundCoordinationBus

DECISION_AUTHORITY_ENVELOPE_SCHEMA = "VERA_DECISION_AUTHORITY_ENVELOPE_V1"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


class ActorContext(_CompatibilityActorContext):
    """Strict public actor context.

    Compatibility aliases are for decoding historical stored rows only. New
    actor construction rejects obsolete and unknown routes immediately.
    """

    def __init__(
        self,
        workstream: str,
        permissions: Iterable[str] = frozenset(),
    ) -> None:
        if workstream in OBSOLETE_WORKSTREAMS:
            raise ValueError(
                f"workstream uses obsolete route {workstream!r}; "
                "use 'workstream/initiatives'"
            )
        _CompatibilityActorContext.__init__(
            self,
            workstream=workstream,
            permissions=frozenset(permissions),
        )
        self.validate()


@dataclass(frozen=True)
class DecisionAuthorityEnvelope:
    schema: str
    issuer_id: str
    subject: str
    nonce: str
    verification_token: str

    def canonical_body(self) -> dict[str, str]:
        return {
            "schema": self.schema,
            "issuer_id": self.issuer_id,
            "subject": self.subject,
            "nonce": self.nonce,
        }


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
    """Reference single-use issuer/verifier with an externally held HMAC key."""

    def __init__(self, issuer_id: str, secret: bytes) -> None:
        validate_text(issuer_id, "issuer_id")
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ValueError("secret must be at least 32 bytes")
        self.issuer_id = issuer_id
        self._secret = secret
        self._used_tokens: set[str] = set()

    def issue(self, *, subject: str) -> DecisionAuthorityEnvelope:
        validate_text(subject, "decision subject")
        unsigned = DecisionAuthorityEnvelope(
            schema=DECISION_AUTHORITY_ENVELOPE_SCHEMA,
            issuer_id=self.issuer_id,
            subject=subject,
            nonce=str(uuid4()),
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
            if envelope.schema != DECISION_AUTHORITY_ENVELOPE_SCHEMA:
                return False
            if envelope.issuer_id != self.issuer_id:
                return False
            if envelope.subject != expected_subject:
                return False
            validate_text(envelope.nonce, "decision authority nonce")
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


def decision_subject(
    actor_workstream: str,
    draft: CoordinationEventDraft,
) -> str:
    """Bind authority to one exact actor and canonical DECISION draft."""

    validate_text(actor_workstream, "actor_workstream")
    if draft.event_type != "DECISION":
        raise ValueError("decision authority subject requires a DECISION draft")
    body = {
        "operation": "coordination_post",
        "actor_workstream": actor_workstream,
        "draft": draft.canonical_dict(),
    }
    return "coordination-decision:" + sha256(_canonical_bytes(body)).hexdigest()


class CoordinationBus(_VerifierBoundCoordinationBus):
    """Final public facade with temporal and decision authority verification."""

    def __init__(
        self,
        repository: Any,
        *,
        evidence_verifier: Any | None = None,
        receipt_time_provider: Any | None = None,
        decision_authority_verifier: DecisionAuthorityVerifier | None = None,
    ) -> None:
        super().__init__(
            repository,
            evidence_verifier=evidence_verifier,
            receipt_time_provider=receipt_time_provider,
        )
        self._decision_authority_verifier = decision_authority_verifier

    @_receipted("coordination_post")
    def coordination_post(
        self,
        actor: ActorContext,
        draft: CoordinationEventDraft,
        *,
        decision_authority: DecisionAuthorityEnvelope | None = None,
    ):
        if not isinstance(actor, ActorContext):
            raise TypeError(
                "actor must be constructed through coordination_bus.ActorContext"
            )
        actor.validate()
        draft.validate()

        if draft.event_type == "DECISION":
            subject = decision_subject(actor.canonical_workstream, draft)
            verifier = self._decision_authority_verifier
            if verifier is None:
                raise PermissionError(
                    "DECISION requires an injected trusted decision authority verifier"
                )
            if not isinstance(decision_authority, DecisionAuthorityEnvelope):
                raise PermissionError(
                    "DECISION requires a verifier-issued DecisionAuthorityEnvelope"
                )
            if not verifier.verify(
                decision_authority,
                expected_subject=subject,
            ):
                raise PermissionError(
                    "decision authority verification failed for the exact actor and draft"
                )
        elif decision_authority is not None:
            raise ValueError("decision_authority is valid only for DECISION drafts")

        original = getattr(_BaseCoordinationBus.coordination_post, "__wrapped__")
        return original(self, actor, draft)
