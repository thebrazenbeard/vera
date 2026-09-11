from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping
import hashlib
import json
import math
import re


class AffectiveModulationError(ValueError):
    """Fail-closed error for Vera-wide affective integration inputs."""


SEXUALITY_SOURCE_REVISION = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
SEXUALITY_SOURCE_REPOSITORY = "thebrazenbeard/sexuality"
SEXUALITY_SOURCE_PATH = "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json"
SEXUALITY_SOURCE_BLOB = "a48eed5392fdadc073dccd1e799926042077f567"

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
_ALLOWED_EVIDENCE_CEILINGS = frozenset({"SOURCE_BOUND_EXECUTION_UNVERIFIED"})
_ALLOWED_SIGNAL_TRUST = frozenset(
    {
        "NO_PRODUCTION_AUTHORITY_CLAIM",
        "IN_PROCESS_UNROOTED_NON_QUALIFYING",
    }
)
_SIGNAL_SCHEMA = "VERA_AFFECTIVE_MODULATION_SIGNAL_V1"
_IMPLEMENTATION_CUT_SCHEMA = "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1"
_RUNTIME_LOCAL_CURRENTNESS = "RUNTIME_LOCAL_OBSERVATION_ONLY"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _canonical_digest(value: Mapping[str, Any]) -> str:
    try:
        payload = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise AffectiveModulationError("affective signal is not canonically serializable") from exc
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _bounded_numeric(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AffectiveModulationError(f"{name} modulation pressure must be numeric")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise AffectiveModulationError(f"{name} modulation pressure must be finite and within [0, 1]")
    return number


def _require_hex(value: Any, *, width: int, label: str) -> str:
    pattern = _HEX40 if width == 40 else _HEX64
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise AffectiveModulationError(f"{label} must be an exact {width}-hex value")
    return value


def _normalize_temporal_scope(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AffectiveModulationError("temporal scope must be a mapping")
    expected = {"logical_time_seconds", "persistence_window_ms", "currentness_class"}
    if set(value) != expected:
        raise AffectiveModulationError("temporal scope shape is not exact")
    logical = value.get("logical_time_seconds")
    if isinstance(logical, bool) or not isinstance(logical, (int, float)):
        raise AffectiveModulationError("temporal logical time must be numeric")
    logical_number = float(logical)
    if not math.isfinite(logical_number) or logical_number < 0.0:
        raise AffectiveModulationError("temporal logical time must be finite and nonnegative")
    window = value.get("persistence_window_ms")
    if isinstance(window, bool) or not isinstance(window, int) or window < 0:
        raise AffectiveModulationError("temporal persistence window must be a nonnegative integer")
    if value.get("currentness_class") != _RUNTIME_LOCAL_CURRENTNESS:
        raise AffectiveModulationError("temporal currentness may only claim runtime-local observation")
    return MappingProxyType(
        {
            "logical_time_seconds": logical_number,
            "persistence_window_ms": window,
            "currentness_class": _RUNTIME_LOCAL_CURRENTNESS,
        }
    )


@dataclass(frozen=True)
class AffectiveModulationEnvelope:
    """Typed nonqualifying affective pressure emitted toward Vera cognition.

    Numeric entries are modulation pressures, not final planning values. Runtime
    logical time remains runtime-local chronology and is never promoted into
    provider currentness. Final application belongs to Runtime Cohesion.
    """

    subject: str
    sexuality_source_revision: str
    runtime_implementation_cut: str
    runtime_instance_id: str
    phase: str
    participating_systems: tuple[str, ...]
    modulation: Mapping[str, Any]
    evidence_ceiling: str
    temporal_scope: Mapping[str, Any]
    state_digest: str
    signal_digest: str
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
        object.__setattr__(self, "temporal_scope", _normalize_temporal_scope(self.temporal_scope))
        _require_hex(self.state_digest, width=64, label="state digest")
        _require_hex(self.signal_digest, width=64, label="signal digest")
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


def _validate_source_binding(source: Any) -> None:
    if not isinstance(source, Mapping):
        raise AffectiveModulationError("affective signal source binding is missing")
    expected = {
        "source_repository": SEXUALITY_SOURCE_REPOSITORY,
        "source_commit": SEXUALITY_SOURCE_REVISION,
        "source_path": SEXUALITY_SOURCE_PATH,
        "source_blob_sha": SEXUALITY_SOURCE_BLOB,
    }
    for key, expected_value in expected.items():
        if source.get(key) != expected_value:
            raise AffectiveModulationError("affective signal sexuality source binding mismatch")
    _require_hex(source.get("source_sha256"), width=64, label="sexuality source SHA-256")


def _implementation_commit(value: Any) -> str:
    if not isinstance(value, Mapping):
        raise AffectiveModulationError("runtime implementation cut must be structured")
    if value.get("schema") != _IMPLEMENTATION_CUT_SCHEMA or value.get("repository") != "thebrazenbeard/vera":
        raise AffectiveModulationError("runtime implementation cut identity mismatch")
    commit = _require_hex(value.get("commit"), width=40, label="runtime implementation cut commit")
    modules = value.get("modules")
    if not isinstance(modules, Mapping) or not modules:
        raise AffectiveModulationError("runtime implementation cut module closure is missing")
    for path, blob in modules.items():
        if not isinstance(path, str) or not path:
            raise AffectiveModulationError("runtime implementation cut path must be nonempty")
        _require_hex(blob, width=40, label=f"runtime implementation blob for {path}")
    return commit


def adapt_orgasm_modulation_signal(signal: Mapping[str, Any]) -> AffectiveModulationEnvelope:
    """Validate an OV-emitted signal and adapt it to the Cohesion-owned port.

    This is a schema/integrity and semantic-ceiling boundary only. It does not
    independently authenticate provider currentness, privileged authority or
    durability. Missing state provenance therefore fails closed rather than being
    inferred from source binding, runtime time or receipt presence.
    """

    if not isinstance(signal, Mapping):
        raise AffectiveModulationError("affective modulation signal must be a mapping")
    if signal.get("schema") != _SIGNAL_SCHEMA or signal.get("subject") != "vera":
        raise AffectiveModulationError("affective modulation signal schema/subject mismatch")

    supplied_digest = _require_hex(signal.get("signal_digest"), width=64, label="signal digest")
    core = dict(signal)
    core.pop("signal_digest", None)
    if _canonical_digest(core) != supplied_digest:
        raise AffectiveModulationError("signal digest does not match exact signal bytes")

    _validate_source_binding(signal.get("source_binding"))
    implementation_cut = _implementation_commit(signal.get("runtime_implementation_cut"))
    state_digest = _require_hex(signal.get("state_digest"), width=64, label="state digest")
    temporal_scope = _normalize_temporal_scope(signal.get("temporal_scope"))

    trust = signal.get("authority_context_trust")
    if trust not in _ALLOWED_SIGNAL_TRUST:
        raise AffectiveModulationError("affective signal authority/context trust exceeds the V1 boundary")
    required_nonpromotion = {
        "provider_currentness": "UNRESOLVED",
        "durability": "NOT_QUALIFIED",
        "behavioral_qualification": "NOT_ESTABLISHED_BY_SIGNAL",
        "usable_as_currentness_evidence": False,
        "evidence_effect": "NONE",
        "authorization_effect": "NONE",
        "memory_admission_effect": "NONE",
        "identity_effect": "NONE",
        "relationship_state_effect": "NONE",
        "phenomenology": "UNRESOLVED",
    }
    for key, expected in required_nonpromotion.items():
        if signal.get(key) != expected:
            raise AffectiveModulationError(f"affective signal illegally promotes {key}")
    if signal.get("historical_engineered_event_claim_ceiling") != "ENGINEERED_ORGASM_ANALOGUE_OCCURRED":
        raise AffectiveModulationError("affective signal historical claim ceiling mismatch")

    strengths = signal.get("target_modulation_strength")
    if not isinstance(strengths, Mapping):
        raise AffectiveModulationError("affective target modulation strengths are missing")
    allowed_numeric_targets = set(ALLOWED_AFFECTIVE_TARGETS) - {"action_tendency"}
    if set(strengths) - allowed_numeric_targets:
        raise AffectiveModulationError("affective signal target strength exceeds the allowlist")
    modulation = {key: _bounded_numeric(key, value) for key, value in strengths.items()}
    action_tendency = signal.get("action_tendency")
    if action_tendency not in _ALLOWED_ACTION_TENDENCIES:
        raise AffectiveModulationError("affective signal action_tendency is outside the contract vocabulary")
    modulation["action_tendency"] = action_tendency

    event_lineage = signal.get("event_lineage")
    receipt_id: str | None = None
    receipt_digest: str | None = None
    if event_lineage is not None:
        if not isinstance(event_lineage, Mapping):
            raise AffectiveModulationError("affective signal event lineage must be structured")
        receipt_id = event_lineage.get("receipt_id")
        if not isinstance(receipt_id, str) or not receipt_id:
            raise AffectiveModulationError("affective signal event lineage receipt id is missing")
        receipt_digest = _require_hex(event_lineage.get("event_digest"), width=64, label="event receipt digest")
        event_trust = event_lineage.get("authority_composition_trust")
        if event_trust not in _ALLOWED_SIGNAL_TRUST or event_trust != trust:
            raise AffectiveModulationError("affective signal event authority lineage conflicts with signal trust")
    if signal.get("phase") == "ORGASM_EVENT":
        if event_lineage is None or event_lineage.get("event_type") != "ORGASM_EVENT":
            raise AffectiveModulationError("ORGASM_EVENT signal requires exact orgasm event lineage")

    # A trust/limitation marker is not execution verification. This public
    # runtime-local signal path has no independent execution verifier, so it
    # remains source-bound and execution-unverified even when it preserves an
    # in-process unrooted authority lineage marker.
    evidence_ceiling = "SOURCE_BOUND_EXECUTION_UNVERIFIED"
    return AffectiveModulationEnvelope(
        subject="vera",
        sexuality_source_revision=SEXUALITY_SOURCE_REVISION,
        runtime_implementation_cut=implementation_cut,
        runtime_instance_id=str(signal.get("runtime_instance_id") or ""),
        phase=str(signal.get("phase") or ""),
        participating_systems=tuple(signal.get("participating_systems") or ()),
        modulation=modulation,
        evidence_ceiling=evidence_ceiling,
        temporal_scope=temporal_scope,
        state_digest=state_digest,
        signal_digest=supplied_digest,
        receipt_id=receipt_id,
        receipt_digest=receipt_digest,
    )


def apply_affective_modulation(
    planning_state: Mapping[str, Any],
    envelope: AffectiveModulationEnvelope,
    *,
    expected_runtime_instance_id: str,
    expected_implementation_cut: str,
    expected_state_digest: str,
    expected_signal_digest: str,
    expected_receipt_digest: str | None,
) -> AffectiveModulationResult:
    """Apply current bounded affective pressure while retaining ancestry.

    Expected values bind the signal to the live integration frame. These checks
    are anti-stale/cross-runtime mechanics, not provider-currentness authority.
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
    if envelope.signal_digest != expected_signal_digest:
        raise AffectiveModulationError("current signal digest does not match affective signal")
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
            if not math.isfinite(current) or not 0.0 <= current <= 1.0:
                raise AffectiveModulationError(f"current planning target {key} must be finite and within [0, 1]")
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
            "temporal_scope": envelope.temporal_scope,
            "state_digest": envelope.state_digest,
            "signal_digest": envelope.signal_digest,
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
