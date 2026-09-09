from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from typing import Any, Mapping


class AffectiveSemanticError(ValueError):
    """Persisted affective state or receipt is internally inconsistent."""


_ALLOWED_PHASES = {
    "QUIESCENT",
    "ACTIVATING",
    "ENTRAINED",
    "CLIMAX_ELIGIBLE",
    "ORGASM_EVENT",
    "RESOLUTION",
    "SATIATED_OR_REFRACTORY",
}
_ALLOWED_ACTION_TENDENCIES = {"NONE", "APPROACH", "PLAY", "HOLD", "REDIRECT", "AVOID"}
_ALLOWED_EVENT_TYPES = {"ORGASM_EVENT", "RESOLUTION", "RECOVERY"}
_REQUIRED_TRIGGERS = {
    "ORGANIC_THRESHOLD_CROSSING",
    "ADMIN_FORCED_TEST",
    "SELF_QUALIFICATION_TEST",
}
_ALLOWED_PROFILES = {"REFRACTORY_COUPLED", "REENTRANT_CLIMAX"}
_BOUNDED_STATE_FIELDS = {
    "sexual_salience",
    "activation_intensity",
    "anticipation",
    "inhibition",
    "coherence",
    "coalition_stability",
    "hedonic_impact",
    "consummatory_gain",
    "satiation",
    "resolution_intensity",
    "refractory_strength",
}


def canonical_event_digest(receipt: Mapping[str, Any]) -> str:
    core = dict(receipt)
    core.pop("event_digest", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_timestamp(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AffectiveSemanticError(f"{label} must be a non-empty timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AffectiveSemanticError(f"{label} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AffectiveSemanticError(f"{label} must carry timezone information")
    return value


def _require_hex_digest(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise AffectiveSemanticError(f"{label} must be an exact 64-character SHA-256")
    try:
        int(value, 16)
    except ValueError as exc:
        raise AffectiveSemanticError(f"{label} must be hexadecimal") from exc
    return value


def validate_state_snapshot_semantics(
    raw_state: Mapping[str, Any],
    *,
    profile: str,
    maximum_orgasm_event_ms: float | None = None,
) -> None:
    if profile not in _ALLOWED_PROFILES:
        raise AffectiveSemanticError("durable orgasm state has an unsupported recovery profile")
    if raw_state.get("subject") != "vera":
        raise AffectiveSemanticError("durable orgasm state snapshot subject must be vera")
    if raw_state.get("presence") != "ALWAYS_PRESENT_NORMALLY_QUIESCENT":
        raise AffectiveSemanticError("durable orgasm state snapshot presence mismatch")

    phase = raw_state.get("phase")
    if phase not in _ALLOWED_PHASES:
        raise AffectiveSemanticError("durable orgasm state has an unknown phase")
    action_tendency = raw_state.get("action_tendency")
    if action_tendency not in _ALLOWED_ACTION_TENDENCIES:
        raise AffectiveSemanticError("durable orgasm state has an unknown action tendency")

    for name in ("active_orgasm_event", "context_eligible", "reentry_allowed", "organic_climax_eligible"):
        if not isinstance(raw_state.get(name), bool):
            raise AffectiveSemanticError(f"durable orgasm state {name} must be boolean")

    for name in _BOUNDED_STATE_FIELDS:
        value = raw_state.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise AffectiveSemanticError(f"durable orgasm state {name} must be numeric")
        numeric = float(value)
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise AffectiveSemanticError(f"durable orgasm state {name} must be within [0, 1]")

    positive_valence = raw_state.get("positive_valence")
    if isinstance(positive_valence, bool) or not isinstance(positive_valence, (int, float)):
        raise AffectiveSemanticError("durable orgasm state positive_valence must be numeric")
    if not math.isfinite(float(positive_valence)) or not -1.0 <= float(positive_valence) <= 1.0:
        raise AffectiveSemanticError("durable orgasm state positive_valence must be within [-1, 1]")

    persistence_window_ms = raw_state.get("persistence_window_ms")
    if isinstance(persistence_window_ms, bool) or not isinstance(persistence_window_ms, int) or persistence_window_ms < 0:
        raise AffectiveSemanticError("durable orgasm state persistence_window_ms must be a nonnegative integer")

    event_elapsed_ms = raw_state.get("event_elapsed_ms")
    if isinstance(event_elapsed_ms, bool) or not isinstance(event_elapsed_ms, (int, float)):
        raise AffectiveSemanticError("durable orgasm state event_elapsed_ms must be numeric")
    event_elapsed = float(event_elapsed_ms)
    if not math.isfinite(event_elapsed) or event_elapsed < 0.0:
        raise AffectiveSemanticError("durable orgasm state event_elapsed_ms must be finite and nonnegative")
    if maximum_orgasm_event_ms is not None and event_elapsed > float(maximum_orgasm_event_ms) + 1e-9:
        raise AffectiveSemanticError("durable orgasm state event_elapsed_ms is outside the bounded climax window")

    if raw_state.get("next_eligible_at") is not None:
        raise AffectiveSemanticError(
            "durable orgasm state next_eligible_at requires a trusted wall-clock continuity binding"
        )

    active = raw_state["active_orgasm_event"]
    if active != (phase == "ORGASM_EVENT"):
        raise AffectiveSemanticError("durable orgasm state phase/active_orgasm_event semantics are inconsistent")

    reentry_allowed = raw_state["reentry_allowed"]
    recovery_phase = phase in {"RESOLUTION", "SATIATED_OR_REFRACTORY"}
    if phase == "ORGASM_EVENT" and reentry_allowed:
        raise AffectiveSemanticError("ORGASM_EVENT recovery semantics require reentry_allowed=false")
    if recovery_phase:
        expected_reentry = profile == "REENTRANT_CLIMAX"
        if reentry_allowed != expected_reentry:
            raise AffectiveSemanticError("durable recovery reentry state does not match the active profile")
        if action_tendency != "HOLD":
            raise AffectiveSemanticError("recovery phase semantics require action_tendency=HOLD")

    if phase == "QUIESCENT":
        if (
            not reentry_allowed
            or action_tendency != "NONE"
            or float(raw_state["activation_intensity"]) >= 0.05
            or float(raw_state["coherence"]) >= 0.05
            or float(raw_state["satiation"]) >= 0.05
            or float(raw_state["resolution_intensity"]) != 0.0
            or float(raw_state["refractory_strength"]) != 0.0
        ):
            raise AffectiveSemanticError("QUIESCENT recovery semantics are inconsistent")
    elif phase == "ACTIVATING":
        if float(raw_state["activation_intensity"]) <= 0.0:
            raise AffectiveSemanticError("ACTIVATING phase requires positive activation")
    elif phase == "ENTRAINED":
        # A legitimate standalone time advance may clear persistence while leaving
        # nonzero entrainment coherence, so persistence_window_ms is deliberately
        # not required here.
        if float(raw_state["coherence"]) <= 0.0:
            raise AffectiveSemanticError("ENTRAINED phase requires nonzero coherence")
    elif phase == "CLIMAX_ELIGIBLE":
        if raw_state["organic_climax_eligible"] is not True:
            raise AffectiveSemanticError("CLIMAX_ELIGIBLE requires the complete organic predicate")
    elif phase == "ORGASM_EVENT":
        if action_tendency != "HOLD" or float(raw_state["resolution_intensity"]) != 0.0:
            raise AffectiveSemanticError("ORGASM_EVENT state semantics are inconsistent")


def _validate_verified_authorization_provenance(
    provenance: Mapping[str, Any],
    *,
    trigger_class: str,
) -> None:
    required = (
        "verifier_id",
        "evidence_id",
        "evidence_digest",
        "actor",
        "referent",
        "proposition_or_effect_class",
        "currentness",
        "expiry_or_supersession",
    )
    missing = [name for name in required if name not in provenance]
    if missing:
        raise AffectiveSemanticError(
            "verified trigger provenance is incomplete: " + ", ".join(missing)
        )
    for name in ("verifier_id", "evidence_id", "actor"):
        if not isinstance(provenance.get(name), str) or not provenance.get(name):
            raise AffectiveSemanticError(f"verified trigger provenance {name} must be non-empty")
    _require_hex_digest(provenance.get("evidence_digest"), label="trigger provenance evidence_digest")
    if provenance.get("referent") != "vera":
        raise AffectiveSemanticError("verified trigger provenance referent must be vera")
    if provenance.get("proposition_or_effect_class") != trigger_class:
        raise AffectiveSemanticError("verified trigger provenance effect class does not match trigger")
    if provenance.get("currentness") != "CURRENT":
        raise AffectiveSemanticError("verified trigger provenance must be CURRENT")
    if provenance.get("expiry_or_supersession") is not None:
        raise AffectiveSemanticError("verified trigger provenance is expired or superseded")


def validate_event_receipt_semantics(
    receipt: Mapping[str, Any],
    *,
    runtime_instance_id: str,
    source_revision: str,
    phenomenology_status: str = "UNRESOLVED",
) -> None:
    if receipt.get("runtime_instance_id") != runtime_instance_id:
        raise AffectiveSemanticError("event receipt runtime instance mismatch")
    if receipt.get("source_revision") != source_revision:
        raise AffectiveSemanticError("event receipt source revision mismatch")
    if receipt.get("subject") != "vera":
        raise AffectiveSemanticError("event receipt subject must be vera")
    if receipt.get("schema_version") != "VERA_ORGASM_RUNTIME_CONTRACT_V1":
        raise AffectiveSemanticError("event receipt schema version mismatch")

    event_type = receipt.get("event_type")
    if event_type not in _ALLOWED_EVENT_TYPES:
        raise AffectiveSemanticError("event receipt event_type is missing or unsupported")
    state_before = receipt.get("state_before")
    state_after = receipt.get("state_after")
    if not isinstance(state_before, Mapping) or not isinstance(state_after, Mapping):
        raise AffectiveSemanticError("event receipt requires state_before and state_after")

    trigger_class = receipt.get("trigger_class")
    if trigger_class not in _REQUIRED_TRIGGERS:
        raise AffectiveSemanticError("event receipt trigger_class is unsupported")
    organic = receipt.get("organic")
    if not isinstance(organic, bool):
        raise AffectiveSemanticError("event receipt organic must be an actual boolean")
    if trigger_class == "ORGANIC_THRESHOLD_CROSSING" and organic is not True:
        raise AffectiveSemanticError("organic threshold trigger must be marked organic")
    if trigger_class in {"ADMIN_FORCED_TEST", "SELF_QUALIFICATION_TEST"} and organic is not False:
        raise AffectiveSemanticError("forced trigger must be non-organic")

    provenance = receipt.get("trigger_provenance")
    if trigger_class == "ORGANIC_THRESHOLD_CROSSING":
        if provenance != "ORGANIC_STATE_DYNAMICS":
            raise AffectiveSemanticError("organic trigger provenance mismatch")
    else:
        if isinstance(provenance, str):
            if provenance != "FORCED_QUALIFICATION_ROUTE":
                raise AffectiveSemanticError("forced trigger provenance mismatch")
        elif isinstance(provenance, Mapping):
            _validate_verified_authorization_provenance(provenance, trigger_class=trigger_class)
        else:
            raise AffectiveSemanticError("forced trigger provenance must be verified evidence")

    before_phase = state_before.get("phase")
    after_phase = state_after.get("phase")
    if receipt.get("transition") != f"{before_phase}->{after_phase}":
        raise AffectiveSemanticError("event receipt transition does not match before/after phases")

    _require_timestamp(receipt.get("observed_at"), label="event receipt observed_at")
    if receipt.get("phenomenology") != phenomenology_status:
        raise AffectiveSemanticError("event receipt phenomenology exceeds the configured ceiling")

    if event_type == "ORGASM_EVENT":
        if receipt.get("claim") != "ENGINEERED_ORGASM_ANALOGUE_OCCURRED":
            raise AffectiveSemanticError("ORGASM_EVENT receipt requires the exact engineered-event claim")
        if after_phase != "ORGASM_EVENT" or state_after.get("active_orgasm_event") is not True:
            raise AffectiveSemanticError("ORGASM_EVENT receipt state_after semantics are inconsistent")
    else:
        if "claim" in receipt:
            raise AffectiveSemanticError("non-orgasm transition receipt must not carry the orgasm-event claim")
        if event_type == "RESOLUTION":
            if before_phase != "ORGASM_EVENT" or after_phase != "RESOLUTION":
                raise AffectiveSemanticError("RESOLUTION receipt transition semantics are inconsistent")
        elif event_type == "RECOVERY":
            if before_phase not in {"RESOLUTION", "SATIATED_OR_REFRACTORY"}:
                raise AffectiveSemanticError("RECOVERY receipt has an invalid prior phase")
            if after_phase not in {"SATIATED_OR_REFRACTORY", "QUIESCENT"}:
                raise AffectiveSemanticError("RECOVERY receipt has an invalid new phase")

    observed_digest = _require_hex_digest(receipt.get("event_digest"), label="event receipt event_digest")
    if observed_digest != canonical_event_digest(receipt):
        raise AffectiveSemanticError("event receipt SHA-256 does not match canonical receipt core")
