"""Strict public actor construction for Coordination Bus v1.

Stored coordination rows may retain historical addresses, but new runtime actor
contexts must use canonical routes. This module intentionally subclasses the
storage-compatible contract type so existing bus internals continue to accept
it without normalizing obsolete input.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    ActorContext as _StoredCompatibleActorContext,
    OBSOLETE_WORKSTREAMS,
    WORKSTREAMS,
    validate_text,
)


@dataclass(frozen=True)
class ActorContext(_StoredCompatibleActorContext):
    """Public actor context that rejects obsolete and unknown routes."""

    def __post_init__(self) -> None:
        validate_text(self.workstream, "workstream")
        if self.workstream in OBSOLETE_WORKSTREAMS:
            raise ValueError(
                f"workstream uses obsolete route {self.workstream!r}; "
                "use 'workstream/initiatives'"
            )
        if self.workstream not in WORKSTREAMS:
            raise ValueError(f"workstream must be one of {sorted(WORKSTREAMS)}")
