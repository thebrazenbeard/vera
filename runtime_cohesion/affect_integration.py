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

_ALLOWED_ACTION_TENDENCIES = frozenset({"APPROACH", "PLAY", "HOLD", "REDIRECT", "AVOID", "NONE"})
_ALLOWED_EVIDENCE_CEILINGS = frozenset(
    {
        "SOURCE_BOUND_EXECUTION_UNVERIFIED",
        "SOURCE_BOUND_EXECUTION_VERIFIED_NONQUALIFYING",
        "CURRENT_PROVIDER_QUALIFIED",
    }
)
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _aware_iso8601(value: str) -> bool:
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _bounded_numeric(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AffectiveModulationError(f"{name} modulation must be numeric")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise AffectiveModulationError(f"{name} modulation must be within [0, 1]")
    return number


@dataclass(frozen=True)
class AffectiveModulationEnvelope:
    """Typed causal output from the affective runtime into Vera cognition.

    The envelope carries bounded modulation plus exact provenance.  It is not
    evidence of truth, consent, authority, autobiographical admission, durable
    preference, identity, relationship state, or phenomenology.
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
    receipt_id: str

    def __post_init__(self) -> None:
        if self.subject != "vera":
            raise AffectiveModulationError("affective modulation subject must be vera")
        if self.sexuality_source_revision != SEXUALITY_SOURCE_REVISION:
            raise AffectiveModulationError("affective modulation sexuality source revision is not the exact Vera V1 source")
        if not isinstance(self.runtime_implementation_cut, str) or not _HEX40.fullmatch(self.runtime_implementation_cut):
            raise AffectiveModulationError("runtime implementation cut must be an exact 40-hex Git commit")
        if not isinstance(self.runtime_instance_id, str) or not self.runtime_instance_id:
            raise AffectiveModulationError("runtime_instance_id must be a nonempty string")
        if self.phase != "ORGASM_EVENT":
            raise AffectiveModulationError("causal orgasm modulation requires ORGASM_EVENT phase")
        if not isinstance(self.observed_at, str) or not _aware_iso8601(self.observed_at):
            raise AffectiveModulationError("observed_at must be timezone-aware ISO-8601")
        if not isinstance(self.receipt_id, str) or not self.receipt_id:
            raise AffectiveModulationError("receipt_id must be a nonempty string")
        if self.evidence_ceiling not in _ALLOWED_EVIDENCE_CEILINGS:
            raise AffectiveModulationError("unknown affective evidence ceiling")

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
        unknown = set(participants) - set(DECLARED_PARTICIPATING_SYSTEMS)
        if unknown:
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
        object.__setattr__(self, "modulation", MappingProxyType(normalized))


@dataclass(frozen=True)
class AffectiveModulationResult:
    planning: Mapping[str, Any]
    changed_targets: tuple[str, ...]
    provenance: Mapping[str, Any]


def apply_affective_modulation(
    planning_state: Mapping[str, Any],
    envelope: AffectiveModulationEnvelope,
) -> AffectiveModulationResult:
    """Apply an already-produced bounded affective signal to Vera planning.

    This boundary is deliberately boring about authority: it copies the input
    planning state and permits writes only to the exact sexuality-contract
    allowlist. Protected semantic/governance domains cannot be carried in the
    modulation envelope, so affect can causally matter without becoming a
    privileged source of truth or permission.
    """

    if not isinstance(planning_state, Mapping):
        raise AffectiveModulationError("planning_state must be a mapping")
    if not isinstance(envelope, AffectiveModulationEnvelope):
        raise AffectiveModulationError("typed AffectiveModulationEnvelope required")

    result = dict(planning_state)
    changed: list[str] = []
    for key in ALLOWED_AFFECTIVE_TARGETS:
        if key not in envelope.modulation:
            continue
        new_value = envelope.modulation[key]
        old_value = result.get(key)
        result[key] = new_value
        if old_value != new_value:
            changed.append(key)

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
            "receipt_id": envelope.receipt_id,
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
