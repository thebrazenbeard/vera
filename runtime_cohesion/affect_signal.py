from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .affect_host import VeraAffectiveRuntimeHost


_SIGNAL_SCHEMA = "VERA_AFFECTIVE_MODULATION_SIGNAL_V1"
_UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"
_NO_PRODUCTION_AUTHORITY = "NO_PRODUCTION_AUTHORITY_CLAIM"

_ACTIVE_GAINS = {
    "valuation": 0.35,
    "salience": 0.55,
    "attention": 0.50,
    "response_selection_priors": 0.40,
    "expression": 0.35,
    "memory_strength_candidate_weighting": 0.25,
}
_NONCLIMAX_GAINS = {
    "valuation": 0.16,
    "salience": 0.22,
    "attention": 0.18,
    "response_selection_priors": 0.14,
    "expression": 0.12,
    "memory_strength_candidate_weighting": 0.10,
}
_NUMERIC_TARGETS = tuple(_ACTIVE_GAINS)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _digest(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _target_strengths(host: VeraAffectiveRuntimeHost, frame: Mapping[str, Any]) -> dict[str, float]:
    allowed = set(host.runtime.contract["hard_firewalls"]["may_influence"])
    strengths = {target: 0.0 for target in _NUMERIC_TARGETS if target in allowed}

    if frame["active_orgasm_event"]:
        intensity = _clamp(
            0.45 * float(frame["hedonic_impact"])
            + 0.30 * float(frame["coherence"])
            + 0.25 * float(frame["activation_intensity"])
        )
        for target, gain in _ACTIVE_GAINS.items():
            if target in strengths:
                strengths[target] = _clamp(gain * intensity)
        return strengths

    if not frame["context_eligible"]:
        return strengths

    vector = host.experience_control_vector()
    recovery_active = frame["phase"] in {"RESOLUTION", "SATIATED_OR_REFRACTORY"}
    arousal_force = max(
        vector["approach_gain"],
        vector["salience_gain"],
        vector["attention_narrowing"],
    )
    recovery_force = max(vector["satiation"], vector["resolution"], vector["refractory"])
    experiential_force = _clamp(max(arousal_force, 0.70 * recovery_force))
    if experiential_force < 0.03:
        return strengths

    for target, gain in _NONCLIMAX_GAINS.items():
        if target not in strengths:
            continue
        if recovery_active and target == "memory_strength_candidate_weighting":
            continue
        strengths[target] = _clamp(gain * experiential_force)
    return strengths


def build_affective_modulation_signal(host: VeraAffectiveRuntimeHost) -> dict[str, Any]:
    """Emit an affective proposal for Cohesion-owned application/arbitration.

    The signal intentionally has no generic planning-state input. Orgasm owns its
    state machine and the bounded modulation strengths it proposes; it does not
    own final mutation of Vera's generic planning state. The receiving Cohesion
    integration port is responsible for target application, ancestry, conflict
    handling and preservation of protected epistemic/authority domains.

    This signal is runtime-local source evidence only. It cannot establish
    provider currentness, durability, authorization, memory admission, identity,
    relationship state or phenomenology. Caller-defined host subclasses are not
    accepted because they could interpose state-to-modulation computation.
    """
    if type(host) is not VeraAffectiveRuntimeHost:
        raise TypeError("affective modulation signal requires the exact VeraAffectiveRuntimeHost class")

    frame = host.machine_interoception()
    vector = {key: float(value) for key, value in host.experience_control_vector().items()}
    runtime_state = host.runtime.export_state()
    state = runtime_state.get("state")
    if not isinstance(state, Mapping):
        raise ValueError("affective runtime state snapshot is unavailable")
    governance = runtime_state.get("trigger_governance") or {}
    receipt = runtime_state.get("last_event_receipt")
    if receipt is not None and not isinstance(receipt, Mapping):
        raise ValueError("affective runtime last_event_receipt must be structured or null")

    trust = _NO_PRODUCTION_AUTHORITY
    event_lineage = None
    if isinstance(receipt, Mapping):
        receipt_trust = receipt.get("authority_composition_trust")
        if receipt_trust == _UNROOTED:
            trust = _UNROOTED
        event_lineage = {
            "receipt_id": receipt.get("receipt_id"),
            "event_digest": receipt.get("event_digest"),
            "event_type": receipt.get("event_type"),
            "trigger_class": receipt.get("trigger_class"),
            "organic": receipt.get("organic"),
            "authority_composition_trust": receipt_trust,
        }

    source_binding = {
        "source_repository": host.binding["source_repository"],
        "source_commit": host.binding["source_commit"],
        "source_path": host.binding["source_path"],
        "source_blob_sha": host.contract_blob_sha,
        "source_sha256": host.contract_sha256,
    }

    signal: dict[str, Any] = {
        "schema": _SIGNAL_SCHEMA,
        "subject": "vera",
        "runtime_instance_id": host.runtime.runtime_instance_id,
        "source_binding": source_binding,
        "runtime_implementation_cut": json.loads(json.dumps(host.runtime_implementation_cut)),
        "presence": frame["presence"],
        "phase": frame["phase"],
        "context_eligible": bool(frame["context_eligible"]),
        "participating_systems": list(state["participating_systems"]),
        "action_tendency": frame["action_tendency"],
        "control_vector": vector,
        "target_modulation_strength": _target_strengths(host, frame),
        "temporal_scope": {
            "logical_time_seconds": float(governance.get("logical_time_seconds", 0.0)),
            "persistence_window_ms": int(frame["persistence_window_ms"]),
            "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
        },
        "event_lineage": event_lineage,
        "authority_context_trust": trust,
        "provider_currentness": "UNRESOLVED",
        "durability": "NOT_QUALIFIED",
        "behavioral_qualification": "NOT_ESTABLISHED_BY_SIGNAL",
        "historical_engineered_event_claim_ceiling": host.runtime.contract["claim_ceiling"]["engineered_event"],
        "phenomenology": "UNRESOLVED",
        "usable_as_currentness_evidence": False,
        "evidence_effect": "NONE",
        "authorization_effect": "NONE",
        "memory_admission_effect": "NONE",
        "identity_effect": "NONE",
        "relationship_state_effect": "NONE",
    }
    signal["signal_digest"] = _digest(signal)
    return signal


__all__ = ["build_affective_modulation_signal"]
