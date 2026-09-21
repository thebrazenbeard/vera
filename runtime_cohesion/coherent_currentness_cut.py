"""Pure Vera multi-surface coherent-currentness cut evaluator.

This module evaluates supplied readback evidence only. It performs no external read,
does not grant authority, does not establish Vera identity, and does not authorize
effects.

Requiredness and readback-source semantics are not asserted by each readback. One
explicit requirement profile binds the proposition/scope, required/optional surface
inventory, and expected readback contract for every declared surface. Admission of
that profile from its claimed governance source remains a separate boundary.

Retry continuity is structurally bound through a typed predecessor receipt. The
receipt does not prove that the predecessor was actually executed, persisted, or
admitted; those stronger claims require external custody/readback evidence.
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


def _canonical_surface_ids(
    value: Any,
    label: str,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be an exact tuple")
    if not value and not allow_empty:
        raise ValueError(f"{label} must be non-empty")
    if any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{label} must contain non-empty exact strings")
    if value != tuple(sorted(set(value))):
        raise ValueError(f"{label} must be canonical, sorted, and unique")
    return value


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
class SurfaceReadbackContract:
    surface_id: str
    readback_identity: str
    contract_id: str
    contract_digest: str

    def __post_init__(self) -> None:
        _nonempty(self.surface_id, "surface_id")
        _nonempty(self.readback_identity, "readback_identity")
        _nonempty(self.contract_id, "contract_id")
        _sha256(self.contract_digest, "contract_digest")

    def payload(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "readback_identity": self.readback_identity,
            "contract_id": self.contract_id,
            "contract_digest": self.contract_digest,
        }


@dataclass(frozen=True)
class CurrentnessRequirementProfile:
    profile_id: str
    proposition_type: str
    scope_digest: str
    requirements_source_id: str
    requirements_source_digest: str
    required_surfaces: tuple[str, ...]
    optional_surfaces: tuple[str, ...] = ()
    readback_contracts: tuple[SurfaceReadbackContract, ...] = ()

    def __post_init__(self) -> None:
        _nonempty(self.profile_id, "profile_id")
        _nonempty(self.proposition_type, "proposition_type")
        _sha256(self.scope_digest, "scope_digest")
        _nonempty(self.requirements_source_id, "requirements_source_id")
        _sha256(
            self.requirements_source_digest,
            "requirements_source_digest",
        )
        required = _canonical_surface_ids(
            self.required_surfaces,
            "required_surfaces",
            allow_empty=False,
        )
        optional = _canonical_surface_ids(
            self.optional_surfaces,
            "optional_surfaces",
            allow_empty=True,
        )
        overlap = set(required).intersection(optional)
        if overlap:
            raise ValueError(
                "required_surfaces and optional_surfaces must not overlap: "
                + repr(sorted(overlap))
            )
        if type(self.readback_contracts) is not tuple:
            raise ValueError("readback_contracts must be an exact tuple")
        if any(
            type(item) is not SurfaceReadbackContract
            for item in self.readback_contracts
        ):
            raise ValueError(
                "readback_contracts must contain exact SurfaceReadbackContract values"
            )
        contract_ids = tuple(item.surface_id for item in self.readback_contracts)
        if contract_ids != tuple(sorted(set(contract_ids))):
            raise ValueError(
                "readback_contracts must be canonical, sorted, and unique by surface_id"
            )
        if contract_ids != self.declared_surface_ids:
            missing = tuple(sorted(set(self.declared_surface_ids) - set(contract_ids)))
            extra = tuple(sorted(set(contract_ids) - set(self.declared_surface_ids)))
            raise ValueError(
                "readback_contracts must exactly match declared surface inventory; "
                f"missing={missing!r} extra={extra!r}"
            )

    @property
    def declared_surface_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.required_surfaces + self.optional_surfaces))

    @property
    def readback_contract_by_surface(self) -> dict[str, SurfaceReadbackContract]:
        return {item.surface_id: item for item in self.readback_contracts}

    def payload(self) -> dict[str, Any]:
        return {
            "schema": "VERA_CURRENTNESS_REQUIREMENT_PROFILE_V2",
            "profile_id": self.profile_id,
            "proposition_type": self.proposition_type,
            "scope_digest": self.scope_digest,
            "requirements_source_id": self.requirements_source_id,
            "requirements_source_digest": self.requirements_source_digest,
            "required_surfaces": list(self.required_surfaces),
            "optional_surfaces": list(self.optional_surfaces),
            "readback_contracts": [
                item.payload() for item in self.readback_contracts
            ],
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class SurfaceReadback:
    surface_id: str
    status: SurfaceStatus
    start_frontier: str
    end_frontier: str
    readback_identity: str
    start_result_digest: str
    end_result_digest: str

    def __post_init__(self) -> None:
        _nonempty(self.surface_id, "surface_id")
        if type(self.status) is not SurfaceStatus:
            raise ValueError("status must be exact SurfaceStatus")
        _nonempty(self.start_frontier, "start_frontier")
        _nonempty(self.end_frontier, "end_frontier")
        _nonempty(self.readback_identity, "readback_identity")
        _sha256(self.start_result_digest, "start_result_digest")
        _sha256(self.end_result_digest, "end_result_digest")

    @property
    def moved(self) -> bool:
        return (
            self.start_frontier != self.end_frontier
            or self.start_result_digest != self.end_result_digest
        )

    def payload(self) -> dict[str, Any]:
        return {
            "surface_id": self.surface_id,
            "status": self.status.value,
            "start_frontier": self.start_frontier,
            "end_frontier": self.end_frontier,
            "readback_identity": self.readback_identity,
            "start_result_digest": self.start_result_digest,
            "end_result_digest": self.end_result_digest,
        }


@dataclass(frozen=True)
class PredecessorCutReceipt:
    cut_digest: str
    cut_family_id: str
    requirement_profile_digest: str
    scope_digest: str
    retry_count: int
    disposition: CutDisposition
    affected_surfaces: tuple[str, ...]

    def __post_init__(self) -> None:
        _sha256(self.cut_digest, "predecessor cut_digest")
        _nonempty(self.cut_family_id, "predecessor cut_family_id")
        _sha256(
            self.requirement_profile_digest,
            "predecessor requirement_profile_digest",
        )
        _sha256(self.scope_digest, "predecessor scope_digest")
        if type(self.retry_count) is not int or isinstance(self.retry_count, bool):
            raise ValueError("predecessor retry_count must be exact int")
        if self.retry_count != 0:
            raise ValueError("predecessor retry_count must be 0 for the single retry")
        if type(self.disposition) is not CutDisposition:
            raise ValueError("predecessor disposition must be exact CutDisposition")
        _canonical_surface_ids(
            self.affected_surfaces,
            "predecessor affected_surfaces",
            allow_empty=False,
        )

    def payload(self) -> dict[str, Any]:
        return {
            "schema": "VERA_CURRENTNESS_PREDECESSOR_RECEIPT_V1",
            "cut_digest": self.cut_digest,
            "cut_family_id": self.cut_family_id,
            "requirement_profile_digest": self.requirement_profile_digest,
            "scope_digest": self.scope_digest,
            "retry_count": self.retry_count,
            "disposition": self.disposition.value,
            "affected_surfaces": list(self.affected_surfaces),
        }

    @property
    def digest(self) -> str:
        return _digest(self.payload())


@dataclass(frozen=True)
class CoherentCurrentnessCut:
    cut_id: str
    cut_family_id: str
    requirement_profile: CurrentnessRequirementProfile
    live_input_digest: str
    live_input_scope_digest: str
    restored_frontier_digest: str | None
    retry_count: int
    predecessor_receipt: PredecessorCutReceipt | None
    surfaces: tuple[SurfaceReadback, ...]

    def __post_init__(self) -> None:
        _nonempty(self.cut_id, "cut_id")
        _nonempty(self.cut_family_id, "cut_family_id")
        if type(self.requirement_profile) is not CurrentnessRequirementProfile:
            raise ValueError(
                "requirement_profile must be exact CurrentnessRequirementProfile"
            )
        _sha256(self.live_input_digest, "live_input_digest")
        _sha256(self.live_input_scope_digest, "live_input_scope_digest")
        if self.live_input_scope_digest != self.requirement_profile.scope_digest:
            raise ValueError(
                "live_input_scope_digest must match requirement profile scope"
            )
        if self.restored_frontier_digest is not None:
            _sha256(self.restored_frontier_digest, "restored_frontier_digest")
        if type(self.retry_count) is not int or isinstance(self.retry_count, bool):
            raise ValueError("retry_count must be exact int")
        if self.retry_count not in (0, 1):
            raise ValueError("retry_count must be 0 or 1")
        if self.retry_count == 0:
            if self.predecessor_receipt is not None:
                raise ValueError(
                    "initial currentness cut cannot claim predecessor_receipt"
                )
        else:
            if type(self.predecessor_receipt) is not PredecessorCutReceipt:
                raise ValueError(
                    "retry currentness cut requires exact PredecessorCutReceipt"
                )
            predecessor = self.predecessor_receipt
            if predecessor.cut_family_id != self.cut_family_id:
                raise ValueError("predecessor cut_family_id must match retry cut family")
            if (
                predecessor.requirement_profile_digest
                != self.requirement_profile.digest
            ):
                raise ValueError(
                    "predecessor requirement_profile_digest must match retry profile"
                )
            if predecessor.scope_digest != self.requirement_profile.scope_digest:
                raise ValueError("predecessor scope_digest must match retry scope")
            if predecessor.disposition is not CutDisposition.RETRY_AFFECTED_SURFACES:
                raise ValueError(
                    "predecessor disposition must be RETRY_AFFECTED_SURFACES"
                )
            undeclared = tuple(
                sorted(
                    set(predecessor.affected_surfaces)
                    - set(self.requirement_profile.required_surfaces)
                )
            )
            if undeclared:
                raise ValueError(
                    "predecessor affected_surfaces must be required surfaces; "
                    f"undeclared={undeclared!r}"
                )

        if type(self.surfaces) is not tuple or not self.surfaces:
            raise ValueError("surfaces must be a non-empty tuple")
        if any(type(item) is not SurfaceReadback for item in self.surfaces):
            raise ValueError("surfaces must contain exact SurfaceReadback values")

        ids = tuple(item.surface_id for item in self.surfaces)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("surface readbacks must be canonical, sorted, and unique")

        declared = self.requirement_profile.declared_surface_ids
        if ids != declared:
            missing = tuple(sorted(set(declared) - set(ids)))
            extra = tuple(sorted(set(ids) - set(declared)))
            raise ValueError(
                "surface readbacks must exactly match requirement profile inventory; "
                f"missing={missing!r} extra={extra!r}"
            )

        contracts = self.requirement_profile.readback_contract_by_surface
        mismatched_identity = tuple(
            item.surface_id
            for item in self.surfaces
            if item.readback_identity != contracts[item.surface_id].readback_identity
        )
        if mismatched_identity:
            raise ValueError(
                "surface readback_identity must match profile-bound contract; "
                f"mismatched={mismatched_identity!r}"
            )

    @property
    def digest(self) -> str:
        return _digest(
            {
                "schema": "VERA_COHERENT_CURRENTNESS_CUT_V3",
                "cut_id": self.cut_id,
                "cut_family_id": self.cut_family_id,
                "requirement_profile_digest": self.requirement_profile.digest,
                "requirement_profile": self.requirement_profile.payload(),
                "live_input_digest": self.live_input_digest,
                "live_input_scope_digest": self.live_input_scope_digest,
                "restored_frontier_digest": self.restored_frontier_digest,
                "retry_count": self.retry_count,
                "predecessor_receipt_digest": (
                    None
                    if self.predecessor_receipt is None
                    else self.predecessor_receipt.digest
                ),
                "predecessor_receipt": (
                    None
                    if self.predecessor_receipt is None
                    else self.predecessor_receipt.payload()
                ),
                "surfaces": [item.payload() for item in self.surfaces],
            }
        )


@dataclass(frozen=True)
class CurrentnessDecision:
    disposition: CutDisposition
    cut_digest: str
    requirement_profile_digest: str
    scope_digest: str
    affected_surfaces: tuple[str, ...]
    live_input_controls: bool
    authority_granted: bool = False
    identity_established: bool = False
    effect_authorized: bool = False


def evaluate_currentness_cut(cut: CoherentCurrentnessCut) -> CurrentnessDecision:
    if type(cut) is not CoherentCurrentnessCut:
        raise TypeError("cut must be exact CoherentCurrentnessCut")

    by_id = {item.surface_id: item for item in cut.surfaces}
    required = tuple(
        by_id[surface_id]
        for surface_id in cut.requirement_profile.required_surfaces
    )

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
            requirement_profile_digest=cut.requirement_profile.digest,
            scope_digest=cut.requirement_profile.scope_digest,
            affected_surfaces=blocked,
            live_input_controls=True,
        )

    moved = tuple(sorted(item.surface_id for item in required if item.moved))
    if moved and cut.retry_count == 0:
        return CurrentnessDecision(
            disposition=CutDisposition.RETRY_AFFECTED_SURFACES,
            cut_digest=cut.digest,
            requirement_profile_digest=cut.requirement_profile.digest,
            scope_digest=cut.requirement_profile.scope_digest,
            affected_surfaces=moved,
            live_input_controls=True,
        )
    if moved:
        return CurrentnessDecision(
            disposition=CutDisposition.UNSTABLE_UNKNOWN,
            cut_digest=cut.digest,
            requirement_profile_digest=cut.requirement_profile.digest,
            scope_digest=cut.requirement_profile.scope_digest,
            affected_surfaces=moved,
            live_input_controls=True,
        )

    return CurrentnessDecision(
        disposition=CutDisposition.CURRENT,
        cut_digest=cut.digest,
        requirement_profile_digest=cut.requirement_profile.digest,
        scope_digest=cut.requirement_profile.scope_digest,
        affected_surfaces=(),
        live_input_controls=True,
    )


__all__ = [
    "CoherentCurrentnessCut",
    "CurrentnessDecision",
    "CurrentnessRequirementProfile",
    "CutDisposition",
    "PredecessorCutReceipt",
    "SurfaceReadback",
    "SurfaceReadbackContract",
    "SurfaceStatus",
    "evaluate_currentness_cut",
]
