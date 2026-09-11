from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Collection, Mapping


_SIGNAL_SCHEMA = "VERA_AFFECTIVE_MODULATION_SIGNAL_V1"
_CANONICAL_SOURCE = {
    "source_repository": "thebrazenbeard/sexuality",
    "source_commit": "150f1c8231423393bb66b0e2cb759ce7c018f8d7",
    "source_path": "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json",
    "source_blob_sha": "a48eed5392fdadc073dccd1e799926042077f567",
}
_ALLOWED_NUMERIC_TARGETS = {
    "valuation",
    "salience",
    "attention",
    "response_selection_priors",
    "expression",
    "memory_strength_candidate_weighting",
}
_ALLOWED_PARTICIPATING_SYSTEMS = {
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
}
_ALLOWED_PHASES = {
    "QUIESCENT",
    "ACTIVATING",
    "ENTRAINED",
    "CLIMAX_ELIGIBLE",
    "ORGASM_EVENT",
    "RESOLUTION",
    "SATIATED_OR_REFRACTORY",
}
_ALLOWED_ACTION_TENDENCIES = {"APPROACH", "PLAY", "HOLD", "REDIRECT", "AVOID", "NONE"}
_ALLOWED_TRUST = {"NO_PRODUCTION_AUTHORITY_CLAIM", "IN_PROCESS_UNROOTED_NON_QUALIFYING"}
_CONTROL_VECTOR_KEYS = {
    "approach_gain",
    "salience_gain",
    "attention_narrowing",
    "consummatory_gain",
    "plasticity_gain",
    "satiation",
    "resolution",
    "refractory",
}


@dataclass(frozen=True)
class AffectiveModulationAncestry:
    target: str
    prior_value: float
    strength: float
    resulting_value: float
    signal_digest: str
    runtime_instance_id: str
    phase: str
    event_digest: str | None


@dataclass(frozen=True)
class AffectiveModulationApplication:
    planning_state: dict[str, Any]
    ancestry: tuple[AffectiveModulationAncestry, ...]
    signal_digest: str
    runtime_instance_id: str
    logical_time_seconds: float
    participating_systems: tuple[str, ...]
    proposed_action_tendency: str


def _canonical_digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_hex(value: Any, *, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise ValueError(f"{label} must be an exact {length}-character hexadecimal digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _bounded_number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError(f"{label} must be finite and within [0,1]")
    return numeric


def _validate_signal(
    signal: Mapping[str, Any],
    *,
    expected_runtime_instance_id: str,
    expected_runtime_implementation_cut: Mapping[str, Any],
    minimum_logical_time_seconds: float,
    consumed_signal_digests: Collection[str],
) -> tuple[str, float, tuple[str, ...], str, dict[str, float], str | None]:
    if signal.get("schema") != _SIGNAL_SCHEMA:
        raise ValueError("unsupported affective modulation signal schema")
    if signal.get("subject") != "vera":
        raise ValueError("affective modulation signal must be Vera-scoped")
    if signal.get("runtime_instance_id") != expected_runtime_instance_id:
        raise ValueError("affective modulation signal runtime instance mismatch")
    if signal.get("runtime_implementation_cut") != expected_runtime_implementation_cut:
        raise ValueError("affective modulation signal implementation cut mismatch")

    source = signal.get("source_binding")
    if not isinstance(source, Mapping):
        raise ValueError("affective modulation signal requires exact source binding")
    for key, expected in _CANONICAL_SOURCE.items():
        if source.get(key) != expected:
            raise ValueError(f"affective modulation signal source mismatch: {key}")
    _require_hex(source.get("source_sha256"), length=64, label="source_sha256")

    digest = _require_hex(signal.get("signal_digest"), length=64, label="signal_digest")
    core = dict(signal)
    core.pop("signal_digest", None)
    if _canonical_digest(core) != digest:
        raise ValueError("affective modulation signal digest does not match signal bytes")
    if digest in consumed_signal_digests:
        raise ValueError("affective modulation signal digest has already been consumed")

    phase = signal.get("phase")
    if phase not in _ALLOWED_PHASES:
        raise ValueError("affective modulation signal phase is invalid")
    if signal.get("presence") != "ALWAYS_PRESENT_NORMALLY_QUIESCENT":
        raise ValueError("affective modulation signal presence is invalid")
    action_tendency = signal.get("action_tendency")
    if action_tendency not in _ALLOWED_ACTION_TENDENCIES:
        raise ValueError("affective modulation signal action tendency is invalid")

    systems = signal.get("participating_systems")
    if not isinstance(systems, list) or any(not isinstance(item, str) or not item for item in systems):
        raise ValueError("affective modulation signal participating_systems must be a string list")
    if len(systems) != len(set(systems)) or not set(systems).issubset(_ALLOWED_PARTICIPATING_SYSTEMS):
        raise ValueError("affective modulation signal participating_systems are duplicated or out of vocabulary")

    vector = signal.get("control_vector")
    if not isinstance(vector, Mapping) or set(vector) != _CONTROL_VECTOR_KEYS:
        raise ValueError("affective modulation signal control vector is incomplete or broadened")
    for key, value in vector.items():
        _bounded_number(value, label=f"control_vector.{key}")

    strengths = signal.get("target_modulation_strength")
    if not isinstance(strengths, Mapping) or not set(strengths).issubset(_ALLOWED_NUMERIC_TARGETS):
        raise ValueError("affective modulation signal target set is broadened")
    normalized_strengths = {
        str(target): _bounded_number(value, label=f"target_modulation_strength.{target}")
        for target, value in strengths.items()
    }

    temporal = signal.get("temporal_scope")
    if not isinstance(temporal, Mapping):
        raise ValueError("affective modulation signal temporal scope is missing")
    if temporal.get("currentness_class") != "RUNTIME_LOCAL_OBSERVATION_ONLY":
        raise ValueError("affective modulation signal cannot promote runtime-local observation to currentness evidence")
    logical_time = temporal.get("logical_time_seconds")
    if isinstance(logical_time, bool) or not isinstance(logical_time, (int, float)):
        raise ValueError("affective modulation signal logical_time_seconds must be numeric")
    logical_time = float(logical_time)
    if not math.isfinite(logical_time) or logical_time < 0.0:
        raise ValueError("affective modulation signal logical_time_seconds must be finite and nonnegative")
    if isinstance(minimum_logical_time_seconds, bool) or not isinstance(minimum_logical_time_seconds, (int, float)):
        raise ValueError("minimum_logical_time_seconds must be numeric")
    if logical_time < float(minimum_logical_time_seconds):
        raise ValueError("affective modulation signal is older than the receiving integration frontier")
    persistence_ms = temporal.get("persistence_window_ms")
    if isinstance(persistence_ms, bool) or not isinstance(persistence_ms, int) or persistence_ms < 0:
        raise ValueError("affective modulation signal persistence_window_ms must be a nonnegative integer")

    if signal.get("authority_context_trust") not in _ALLOWED_TRUST:
        raise ValueError("affective modulation signal claims an unsupported authority/context trust class")
    expected_ceilings = {
        "provider_currentness": "UNRESOLVED",
        "durability": "NOT_QUALIFIED",
        "behavioral_qualification": "NOT_ESTABLISHED_BY_SIGNAL",
        "historical_engineered_event_claim_ceiling": "ENGINEERED_ORGASM_ANALOGUE_OCCURRED",
        "phenomenology": "UNRESOLVED",
        "usable_as_currentness_evidence": False,
        "evidence_effect": "NONE",
        "authorization_effect": "NONE",
        "memory_admission_effect": "NONE",
        "identity_effect": "NONE",
        "relationship_state_effect": "NONE",
    }
    for key, expected in expected_ceilings.items():
        if signal.get(key) != expected:
            raise ValueError(f"affective modulation signal illegally broadens {key}")

    event_digest: str | None = None
    event_lineage = signal.get("event_lineage")
    if event_lineage is not None:
        if not isinstance(event_lineage, Mapping):
            raise ValueError("affective modulation signal event lineage must be structured or null")
        candidate_digest = event_lineage.get("event_digest")
        if candidate_digest is not None:
            event_digest = _require_hex(candidate_digest, length=64, label="event_lineage.event_digest")
        lineage_trust = event_lineage.get("authority_composition_trust")
        if lineage_trust is not None and lineage_trust not in _ALLOWED_TRUST:
            raise ValueError("affective modulation signal event lineage carries unsupported trust")
        if lineage_trust == "IN_PROCESS_UNROOTED_NON_QUALIFYING" and signal.get("authority_context_trust") != lineage_trust:
            raise ValueError("affective modulation signal drops unrooted event-lineage trust")

    return digest, logical_time, tuple(systems), str(action_tendency), normalized_strengths, event_digest


def apply_affective_modulation_signal(
    planning_state: Mapping[str, Any],
    signal: Mapping[str, Any],
    *,
    expected_runtime_instance_id: str,
    expected_runtime_implementation_cut: Mapping[str, Any],
    minimum_logical_time_seconds: float,
    consumed_signal_digests: Collection[str],
) -> AffectiveModulationApplication:
    """Apply one OV affective proposal at the Cohesion-owned arbitration boundary.

    Only the explicit numeric affective target allowlist can change. Every other
    planning key is copied through untouched. Signal metadata is not evidence,
    authorization, autobiographical admission, identity, relationship state or
    phenomenology. Per-target ancestry is returned for every material mutation.
    """
    if not isinstance(planning_state, Mapping):
        raise TypeError("planning_state must be a mapping")
    if not isinstance(signal, Mapping):
        raise TypeError("signal must be a mapping")
    if not isinstance(expected_runtime_instance_id, str) or not expected_runtime_instance_id:
        raise ValueError("expected_runtime_instance_id is required")
    if not isinstance(expected_runtime_implementation_cut, Mapping):
        raise ValueError("expected_runtime_implementation_cut must be a mapping")

    digest, logical_time, systems, action_tendency, strengths, event_digest = _validate_signal(
        signal,
        expected_runtime_instance_id=expected_runtime_instance_id,
        expected_runtime_implementation_cut=expected_runtime_implementation_cut,
        minimum_logical_time_seconds=minimum_logical_time_seconds,
        consumed_signal_digests=consumed_signal_digests,
    )

    result = dict(planning_state)
    ancestry: list[AffectiveModulationAncestry] = []
    phase = str(signal["phase"])
    for target, strength in strengths.items():
        if strength <= 0.0:
            continue
        prior = result.get(target)
        if isinstance(prior, bool) or not isinstance(prior, (int, float)):
            continue
        prior_value = float(prior)
        if not math.isfinite(prior_value) or not 0.0 <= prior_value <= 1.0:
            raise ValueError(f"planning target {target} must be finite and within [0,1]")
        resulting_value = min(1.0, max(0.0, prior_value + (1.0 - prior_value) * strength))
        result[target] = resulting_value
        ancestry.append(
            AffectiveModulationAncestry(
                target=target,
                prior_value=prior_value,
                strength=strength,
                resulting_value=resulting_value,
                signal_digest=digest,
                runtime_instance_id=expected_runtime_instance_id,
                phase=phase,
                event_digest=event_digest,
            )
        )

    return AffectiveModulationApplication(
        planning_state=result,
        ancestry=tuple(ancestry),
        signal_digest=digest,
        runtime_instance_id=expected_runtime_instance_id,
        logical_time_seconds=logical_time,
        participating_systems=systems,
        proposed_action_tendency=action_tendency,
    )


__all__ = [
    "AffectiveModulationAncestry",
    "AffectiveModulationApplication",
    "apply_affective_modulation_signal",
]
