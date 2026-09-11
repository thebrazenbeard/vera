from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .affect_bound_runtime import BoundVeraOrgasmRuntime
from .affect_host import VeraAffectiveRuntimeHost
from .orgasm import OrgasmRuntime


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
_HOST_SIGNAL_METHODS = frozenset({
    "machine_interoception",
    "experience_control_vector",
})
_RUNTIME_OBSERVATION_METHODS = frozenset({
    "snapshot",
    "export_state",
    "_organic_climax_eligible",
    "_refractory_reentry_blocked",
})


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _digest(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validated_signal_origin(host: VeraAffectiveRuntimeHost) -> BoundVeraOrgasmRuntime:
    """Validate the supported in-process causal call surface before signal derivation.

    This is an API/process-boundary check, not hostile-process isolation. It
    rejects ordinary instance-level callable shadowing that would otherwise make
    exact source/class provenance coexist with caller-interposed computation.
    """
    if type(host) is not VeraAffectiveRuntimeHost:
        raise TypeError("affective modulation signal requires the exact VeraAffectiveRuntimeHost class")

    shadowed_host = sorted(_HOST_SIGNAL_METHODS.intersection(host.__dict__))
    if shadowed_host:
        raise ValueError(
            "affective host has caller-shadowed signal derivation methods: "
            + ",".join(shadowed_host)
        )

    runtime = host.runtime
    if type(runtime) is not BoundVeraOrgasmRuntime:
        raise TypeError("affective host runtime must be the exact BoundVeraOrgasmRuntime class")
    shadowed_runtime = sorted(_RUNTIME_OBSERVATION_METHODS.intersection(runtime.__dict__))
    if shadowed_runtime:
        raise ValueError(
            "affective runtime has caller-shadowed observation methods: "
            + ",".join(shadowed_runtime)
        )
    return runtime


def _target_strengths(
    allowed: set[str],
    frame: Mapping[str, Any],
    vector: Mapping[str, float],
) -> dict[str, float]:
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
    relationship state or phenomenology. Caller-defined host subclasses and
    ordinary instance-level shadowing of causal observation methods are rejected.
    """
    runtime = _validated_signal_origin(host)

    # Invoke the exact class-owned host primitives after proving that ordinary
    # instance attributes have not shadowed the causal call targets.
    frame = VeraAffectiveRuntimeHost.machine_interoception(host)
    vector = {
        key: float(value)
        for key, value in VeraAffectiveRuntimeHost.experience_control_vector(host).items()
    }
    # Bypass any instance-dispatched export_state replacement as an additional
    # belt-and-suspenders measure; the shadow check above remains the fail-closed
    # supported-API guard.
    runtime_state = OrgasmRuntime.export_state(runtime)
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

    binding = host.binding
    source_binding = {
        "source_repository": binding["source_repository"],
        "source_commit": binding["source_commit"],
        "source_path": binding["source_path"],
        "source_blob_sha": host.contract_blob_sha,
        "source_sha256": host.contract_sha256,
    }
    allowed = set(runtime.contract["hard_firewalls"]["may_influence"])

    signal: dict[str, Any] = {
        "schema": _SIGNAL_SCHEMA,
        "subject": "vera",
        "runtime_instance_id": runtime.runtime_instance_id,
        "source_binding": source_binding,
        "runtime_implementation_cut": json.loads(json.dumps(host.runtime_implementation_cut)),
        "presence": frame["presence"],
        "phase": frame["phase"],
        "context_eligible": bool(frame["context_eligible"]),
        "participating_systems": list(state["participating_systems"]),
        "action_tendency": frame["action_tendency"],
        "control_vector": vector,
        "target_modulation_strength": _target_strengths(allowed, frame, vector),
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
        "historical_engineered_event_claim_ceiling": runtime.contract["claim_ceiling"]["engineered_event"],
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
