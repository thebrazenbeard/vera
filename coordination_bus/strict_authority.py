"""Strict public facade for V.E.R.A. Coordination Bus v1.

Historical stored addresses remain decodable in the storage contract. New actor
contexts must use canonical routes, and the public bus rejects internal
compatibility actors. Temporal and decision authority verification live only in
``verified_temporal.py``.
"""

from __future__ import annotations

from .contracts import CoordinationEventDraft
from .core import _receipted
from .strict_contract import ActorContext
from .verified_temporal import (
    CoordinationBus as _VerifierBoundCoordinationBus,
    DecisionAuthorityEnvelope,
    DecisionAuthorityInput,
)


class CoordinationBus(_VerifierBoundCoordinationBus):
    """Only public bus facade, requiring the strict public actor type."""

    @_receipted("coordination_post")
    def coordination_post(
        self,
        actor: ActorContext,
        draft: CoordinationEventDraft,
        *,
        decision_authority: DecisionAuthorityInput = None,
    ):
        if not isinstance(actor, ActorContext):
            raise TypeError(
                "actor must be constructed through coordination_bus.ActorContext"
            )
        return super().coordination_post(
            actor,
            draft,
            decision_authority=decision_authority,
        )


__all__ = [
    "ActorContext",
    "CoordinationBus",
    "DecisionAuthorityEnvelope",
]
