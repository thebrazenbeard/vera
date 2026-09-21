"""Pure Vera multi-surface coherent-currentness cut evaluator.

This module evaluates supplied readback evidence only. It performs no external read,
does not grant authority, does not establish Vera identity, and does not authorize
effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any


def _nonempty(value: Any, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a non-empty exact string")
    return value


def _sha256(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _digest(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


class SurfaceStatus(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class CutDisposition(StrEnum):
    CURRENT = "CURRENT"
    RETRY_AFFECTED_SURFACES = "RETRY_AFFECTED_SURFACES"
    UNSTABLE_UNKNOWN = "UNSTABLE_UNKNOWN"
    BLOCKED_REQUIRED_SURFACE = "BLOCKED_REQUIRED_SURFACE"


@dataclass(frozen=True)
class SurfaceReadback:
    surface_id: str
    required: bool
    status: SurfaceStatus
    start_frontier: str
    end_frontier: str
    readback_identity: str
    result_digest: str

    def __post_init__(self) -> None:
        _nonempty(self.surface_id, "surface_id")
        if type(self.required) is not bool:
            raise ValueError("required must be boolean")
        if type(self.status) is not SurfaceStatus:
            raise ValueError("status must be exact SurfaceStatus")
        _nonempty(self.start_frontier, "start_frontier")
        _nonempty(self.end_frontier, "end_frontier")
        _nonempty(self.readback_identity, "readback_identity")
        _sha256(self.result_digest, "result_digest")

    @property
    def moved(self) -> bool:
        return self.start_frontier != self.end_frontier

    def payload(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "required": self.required,
            "status": self.status.value,
            "start_frontier": self.start_frontier,
            "end_frontier": self.end_frontier,
            "readback_identity": self.readback_identity,
            "result_digest": self.result_digest,
        }


@dataclass(frozen=True)
class CoherentCurrentnessCut:
    cut_id: str
    live_input_digest: str
    restored_frontier_digest: str | None
    retry_count: int
    surfaces: tuple[SurfaceReadback, ...]

    def __post_init__(self) -> None:
        _nonempty(self.cut_id, "cut_id")
        _sha256(self.live_input_digest, "live_input_digest")
        if self.restored_frontier_digest is not None:
            _sha256(self.restored_frontier_digest, "restored_frontier_digest")
        if type(self.retry_count) is not int or isinstance(self.retry_count, bool):
            raise ValueError("retry_count must be exact int")
        if self.retry_count not in (0, 1):
            raise ValueError("retry_count must be 0 or 1")
        if type(self.surfaces) is not tuple or not self.surfaces:
            raise ValueError("surfaces must be a non-empty tuple")
        if any(type(item) is not SurfaceReadback for item in self.surfaces):
            raise ValueError("surfaces must contain exact SurfaceReadback values")
        ids = [item.surface_id for item in self.surfaces]
        if len(ids) != len(set(ids)):
            raise ValueError("surface_id values must be unique")

    @property
    def digest(self) -> str:
        return _digest(
            {
                "schema": "VERA_COHERENT_CURRENTNESS_CUT_V1",
                "cut_id": self.cut_id,
                "live_input_digest": self.live_input_digest,
                "restored_frontier_digest": self.restored_frontier_digest,
                "retry_count": self.retry_count,
                "surfaces": [
                    item.payload()
                    for item in sorted(self.surfaces, key=lambda row: row.surface_id)
                ],
            }
        )


@dataclass(frozen=True)
class CurrentnessDecision:
    disposition: CutDisposition
    cut_digest: str
    affected_surfaces: tuple[str, ...]
    live_input_controls: bool
    authority_granted: bool = False
    identity_established: bool = False
    effect_authorized: bool = False


def evaluate_currentness_cut(cut: CoherentCurrentnessCut) -> CurrentnessDecision:
    if type(cut) is not CoherentCurrentnessCut:
        raise TypeError("cut must be exact CoherentCurrentnessCut")

    required = tuple(item for item in cut.surfaces if item.required)

    blocked = tuple(
        sorted(
            item.surface_id
            for item in required
            if item.status is not SurfaceStatus.COMPLETE
        )
    )
    if blocked:
        return CurrentnessDecision(
            disposition=CutDisposition.BLOCKED_REQUIRED_SURFACE,
            cut_digest=cut.digest,
            affected_surfaces=blocked,
            live_input_controls=True,
        )

    moved = tuple(sorted(item.surface_id for item in required if item.moved))
    if moved and cut.retry_count == 0:
        return CurrentnessDecision(
            disposition=CutDisposition.RETRY_AFFECTED_SURFACES,
            cut_digest=cut.digest,
            affected_surfaces=moved,
            live_input_controls=True,
        )
    if moved:
        return CurrentnessDecision(
            disposition=CutDisposition.UNSTABLE_UNKNOWN,
            cut_digest=cut.digest,
            affected_surfaces=moved,
            live_input_controls=True,
        )

    return CurrentnessDecision(
        disposition=CutDisposition.CURRENT,
        cut_digest=cut.digest,
        affected_surfaces=(),
        live_input_controls=True,
    )


__all__ = [
    "CoherentCurrentnessCut",
    "CurrentnessDecision",
    "CutDisposition",
    "SurfaceReadback",
    "SurfaceStatus",
    "evaluate_currentness_cut",
]
