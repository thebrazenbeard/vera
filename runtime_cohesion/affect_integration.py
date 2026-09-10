from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping
import re


class AffectiveModulationError(ValueError):
    """Fail-closed error for Vera-wide affective integration inputs."""


SEXUALITY_SOURCE_REVISION = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"

ALLOWED_AFFECTIVE_TARGETS = (
    "valuation",
    "salience",
    "attention",
    "response_selection_priors",
    "expression",
    "memory_strength_candidate_weighting",
    "action_tendency",
)

FORBIDDEN_AFFECTIVE_PROMOTIONS = frozenset(
    {
        "truth",
        "factual_confidence",
        "consent_or_authorization",
        "protected_effect_authority",
        "autobiographical_memory_admission",
        "permanent_preference",
        "identity",
        "relationship_status",
        "phenomenology",
    }
)

DECLARED_PARTICIPATING_SYSTEMS = (
    "sexual_appraisal",
    "relational_context",
    "attention",
    "conation",
    "valuation",
    "self_model",
    "memory",
    "language_semantics",
    "embodiment_or_interoception_analogue",
    "response_planning",
)

_ALLOWED_PHASES = frozenset(
    {
        "QUIESCENT",
        "ACTIVATING",
        "ENTRAINED",
        "CLIMAX_ELIGIBLE",
        "ORGASM_EVENT",
        "RESOLUTION",
        "SATIATED_OR_REFRACTORY",
    }
)
_ALLOWED_ACTION_TENDENCIES = frozenset({"APPROACH", "PLAY", "HOLD", "REDIRECT", "AVOID", "NONE"})
# This module is a Vera composition/API boundary, not an independently rooted
# provider/currentness verifier. Its caller-constructible envelope can therefore
# carry only nonqualifying source/execution ceilings.
_ALLOWED_EVIDENCE_CEILINGS = frozenset(
    {
        "SOURCE_BOUND_EXECUTION_UNVERIFIED",
        "SOURCE_BOUND_EXECUTION_VERIFIED_NONQUALIFYING",
    }
)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _aware_iso8601(value: str) -> bool:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _bounded_numeric(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AffectiveModulationError(f"{name} modulation pressure must be numeric")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise AffectiveModulationError(f"{name} modulation pressure must be within [0, 1]")
    return number


def _require_hex(value: Any, *, width: int, label: str) -> str:
    pattern = _HEX40 if width == 40 else _HEX64
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AffectiveModulationError(f"{label} must be an exact {width}-hex value")
    return value


@dataclass(frozen=True)
class AffectiveModulationEnvelope:
    """Typed nonqualifying affective pressure emitted toward Vera cognition.

    Numeric modulation entries are pressures, never caller-selected final values.
    The envelope carries source/execution/state provenance but is not a provider-
    current or authority proof. Final application belongs to Runtime Cohesion.
    """

    subject: str
    sexuality_source_revision: str
    runtime_implementation_cut: str
    runtime_instance_id: str
    phase: str
    participating_systems: tuple[str, ...]
    modulation: Mapping[str, Any]
    evidence_ceiling: str
    observed_at: str
    state_digest: str
    receipt_id: str | None
    receipt_digest: str | None

    def __post_init__(self) -> None:
        if self.subject != "vera":
            raise AffectiveModulationError("affective modulation subject must be vera")
        if self.sexuality_source_revision != SEXUALITY_SOURCE_REVISION:
            raise AffectiveModulationError("affective modulation sexuality source revision is not the exact Vera V1 source")
        _require_hex(self.runtime_implementation_cut, width=40, label="runtime implementation cut")
        if not isinstance(self.runtime_instance_id, str) or not self.runtime_instance_id:
            raise AffectiveModulationError("runtime_instance_id must be a nonempty string")
        if self.phase not in _ALLOWED_PHASES:
            raise AffectiveModulationError("affective modulation phase is outside the frozen contract")
        if not isinstance(self.observed_at, str) or not _aware_iso8601(self.observed_at):
            raise AffectiveModulationError("observed_at must be timezone-aware ISO-8601")
        _require_hex(self.state_digest, width=64, label="state digest")
        if self.evidence_ceiling not in _ALLOWED_EVIDENCE_CEILINGS:
            raise AffectiveModulationError(
                "unsupported affective evidence ceiling; this in-process composition boundary cannot self-assert provider qualification"
            )

        if (self.receipt_id is None) != (self.receipt_digest is None):
            raise AffectiveModulationError("receipt id and receipt digest must be present or absent together")
        if self.receipt_id is not None:
            if not isinstance(self.receipt_id, str) or not self.receipt_id:
                raise AffectiveModulationError("receipt id must be a nonempty string")
            _require_hex(self.receipt_digest, width=64, label="receipt digest")
        if self.phase == "ORGASM_EVENT" and self.receipt_id is None:
            raise AffectiveModulationError("ORGASM_EVENT modulation requires exact receipt binding")

        if not isinstance(self.participating_systems, tuple):
            try:
                participants = tuple(self.participating_systems)
            except TypeError as exc:
                raise AffectiveModulationError("participating_systems must be an ordered string collection") from exc
            object.__setattr__(self, "participating_systems", participants)
        participants = self.participating_systems
        if any(not isinstance(name, str) or not name for name in participants):
            raise AffectiveModulationError("participating_systems must contain nonempty strings")
        if len(set(participants)) != len(participants):
            raise AffectiveModulationError("duplicate participating system")
        if set(participants) - set(DECLARED_PARTICIPATING_SYSTEMS):
            raise AffectiveModulationError("participating_systems contains undeclared participating system")

        if not isinstance(self.modulation, Mapping):
            raise AffectiveModulationError("modulation must be a mapping")
        normalized: dict[str, Any] = {}
        for key, value in self.modulation.items():
            if key not in ALLOWED_AFFECTIVE_TARGETS:
                raise AffectiveModulationError(f"modulation target {key!r} is outside the affective allowlist")
            if key == "action_tendency":
                if value not in _ALLOWED_ACTION_TENDENCIES:
                    raise AffectiveModulationError("action_tendency modulation is outside the contract vocabulary")
                normalized[key] = value
            else:
                normalized[key] = _bounded_numeric(key, value)

        if self.phase == "QUIESCENT":
            active = any(
                (key == "action_tendency" and value != "NONE")
                or (key != "action_tendency" and float(value) > 0.0)
                for key, value in normalized.items()
            )
            if active:
                raise AffectiveModulationError("QUIESCENT affective signal cannot carry active modulation pressure")
        object.__setattr__(self, "modulation", MappingProxyType(normalized))


@dataclass(frozen=True)
class AffectiveModulationResult:
    planning: Mapping[str, Any]
    changed_targets: tuple[str, ...]
    provenance: Mapping[str, Any]


def apply_affective_modulation(
    planning_state: Mapping[str, Any],
    envelope: AffectiveModulationEnvelope,
    *,
    expected_runtime_instance_id: str,
    expected_implementation_cut: str,
    expected_state_digest: str,
    expected_receipt_digest: str | None,
) -> AffectiveModulationResult:
    """Apply current bounded affective pressure while retaining ancestry.

    The expected values bind the signal to the live integration frame. This is a
    mechanical anti-stale/cross-runtime boundary, not a provider-currentness or
    authority root. Numeric pressure moves an existing bounded planning scalar
    toward 1.0; it never lets the affect subsystem choose the final value.
    """

    if not isinstance(planning_state, Mapping):
        raise AffectiveModulationError("planning_state must be a mapping")
    if not isinstance(envelope, AffectiveModulationEnvelope):
        raise AffectiveModulationError("typed AffectiveModulationEnvelope required")
    if envelope.runtime_instance_id != expected_runtime_instance_id:
        raise AffectiveModulationError("cross-runtime affective signal rejected")
    if envelope.runtime_implementation_cut != expected_implementation_cut:
        raise AffectiveModulationError("current implementation cut does not match affective signal")
    if envelope.state_digest != expected_state_digest:
        raise AffectiveModulationError("current state digest does not match affective signal")
    if envelope.receipt_digest != expected_receipt_digest:
        raise AffectiveModulationError("current receipt digest does not match affective signal")

    result = dict(planning_state)
    changed: list[str] = []
    ancestry: dict[str, Mapping[str, Any]] = {}
    for key in ALLOWED_AFFECTIVE_TARGETS:
        if key not in envelope.modulation or key not in result:
            continue
        signal = envelope.modulation[key]
        old_value = result[key]
        if key == "action_tendency":
            if old_value not in _ALLOWED_ACTION_TENDENCIES:
                raise AffectiveModulationError("current action_tendency is outside the contract vocabulary")
            new_value = signal
            ancestry_value = {"before": old_value, "signal": signal, "after": new_value}
        else:
            if isinstance(old_value, bool) or not isinstance(old_value, (int, float)):
                raise AffectiveModulationError(f"current planning target {key} must be a bounded numeric scalar")
            current = float(old_value)
            if not 0.0 <= current <= 1.0:
                raise AffectiveModulationError(f"current planning target {key} must be within [0, 1]")
            pressure = float(signal)
            new_value = current + (1.0 - current) * pressure
            ancestry_value = {"before": old_value, "pressure": pressure, "after": new_value}
        result[key] = new_value
        if old_value != new_value:
            changed.append(key)
            ancestry[key] = MappingProxyType(ancestry_value)

    provenance = MappingProxyType(
        {
            "subject": envelope.subject,
            "sexuality_source_revision": envelope.sexuality_source_revision,
            "runtime_implementation_cut": envelope.runtime_implementation_cut,
            "runtime_instance_id": envelope.runtime_instance_id,
            "phase": envelope.phase,
            "participating_systems": envelope.participating_systems,
            "coalition_semantics": "OBSERVATION_ROUTING_MODULATION_DIAGNOSTICS_NOT_TRIGGER_PREDICATE",
            "evidence_ceiling": envelope.evidence_ceiling,
            "observed_at": envelope.observed_at,
            "state_digest": envelope.state_digest,
            "receipt_id": envelope.receipt_id,
            "receipt_digest": envelope.receipt_digest,
            "numeric_modulation_semantics": "PRESSURE_TOWARD_UPPER_BOUND_NOT_CALLER_SELECTED_FINAL_VALUE",
            "currentness_semantics": "EXACT_LIVE_FRAME_CROSS_BIND_NONQUALIFYING_NOT_PROVIDER_CURRENTNESS",
            "modulation_ancestry": MappingProxyType(ancestry),
            "selection_semantics": "MODULATION_MAY_CHANGE_SELECTION_NOT_EVIDENCE_STRENGTH_OR_CONTRADICTION_STATUS",
            "memory_semantics": "CANDIDATE_WEIGHT_ONLY_NOT_ADMISSION",
            "conation_semantics": "ACTION_TENDENCY_NOT_AUTHORIZATION_OR_STANDING_PREFERENCE",
            "identity_semantics": "TRANSIENT_STATE_DOES_NOT_REDEFINE_VERA",
            "authority_semantics": "SALIENCE_AROUSAL_RELATIONAL_RELEVANCE_AND_CONATION_ARE_NOT_AUTHORITY",
            "phenomenology": "UNRESOLVED",
        }
    )
    return AffectiveModulationResult(
        planning=MappingProxyType(result),
        changed_targets=tuple(changed),
        provenance=provenance,
    )
