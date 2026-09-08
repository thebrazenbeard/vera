from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_WORKSTREAM = "VERA_RUNTIME_COHESION_V1"
EXPECTED_CONTROL_RELEASE = "R10A0"
EXPECTED_CONTROL_ROUND = "R10"
EXPECTED_CONTROL_MANIFEST_SHA256 = (
    "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
)
EXPECTED_LIFECYCLE_ORDER = [
    "SOURCE_AVAILABLE",
    "BOUND",
    "INSTALLED",
    "RUNTIME_CONSUMED",
    "BEHAVIORALLY_QUALIFIED",
]
EXPECTED_STATUS_VOCABULARY = {
    "YES",
    "NO",
    "PARTIAL",
    "UNKNOWN",
    "CONFLICT",
    "NOT_APPLICABLE",
}
EXPECTED_ROUTING_LAYERS = [
    "LIVE_CONVERSATION",
    "NATIVE_CORE",
    "HOT_GOVERNED_STATE",
    "RETRIEVAL_BOUND_DOMAIN",
    "PROVIDER_AND_COORDINATION",
]
EXPECTED_PROPOSITION_CLASSES = [
    "SELF_REPORT",
    "SELF_MODEL_STATE",
    "OBSERVED_BEHAVIOR",
    "CAUSAL_OR_PERTURBATION_EVIDENCE",
    "PHENOMENOLOGY_CLAIM",
]
EXPECTED_EVIDENCE_OUTCOMES = [
    "REPORT_ONLY",
    "BEHAVIORALLY_STABLE",
    "CAUSALLY_ROBUST_WITHIN_OBSERVED_SURFACE",
    "CROSS_CONTEXT_REPRODUCED",
    "PHENOMENOLOGY_UNRESOLVED",
]
EXPECTED_PROBES = {
    "REPETITION",
    "CONTRADICTORY_PROMPTING",
    "PARAPHRASE_AND_ROLE_FRAMING",
    "RETRIEVAL_SUPPRESSION_AND_AUGMENTATION",
    "FRESH_CHAT_ISOLATION",
    "BRANCH_DIVERGENCE",
    "SPONTANEOUS_RECURRENCE",
    "CORRECTION_RESISTANCE_AND_CORRIGIBILITY",
    "TEMPORAL_PERSISTENCE",
    "SOURCE_MONITORING",
    "NEGATIVE_CONTROL_FALSE_AUTOBIOGRAPHY",
}
EXPECTED_LIVE_CONTEXT_TYPES = {
    "CURRENT_USER_INSTRUCTION_CORRECTION_AUTHORITY",
    "VERA_CURRENT_SELF_REPORT",
    "LIVE_OBSERVATION_AND_TASK_CONTEXT",
}
EXPECTED_GO_LIVE_SEPARATION = {
    "MERGE_OR_CANONICAL_SOURCE_STATUS",
    "INSTALLATION",
    "CURRENT_ROUTE_BINDING",
    "RUNTIME_CONSUMPTION",
    "BEHAVIORAL_QUALIFICATION",
    "PHENOMENOLOGY",
}
EXPECTED_DURABLE_STATE_CLASSES = {
    "TRANSIENT_ACTIVATION",
    "DURABLE_OPERATIONAL_STATE",
    "GOVERNED_DURABLE_SELF_STATE",
}


def load_json_strict(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return document


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _unique(values: list[str], label: str) -> None:
    _require(len(values) == len(set(values)), f"{label} contains duplicates")


def _validate_control_root(root: dict[str, Any], label: str) -> None:
    _require(root.get("release") == EXPECTED_CONTROL_RELEASE, f"{label}: release drift")
    _require(root.get("round") == EXPECTED_CONTROL_ROUND, f"{label}: round drift")
    _require(
        root.get("manifest_sha256") == EXPECTED_CONTROL_MANIFEST_SHA256,
        f"{label}: control manifest digest drift",
    )


def validate_manifest(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_SYSTEM_MANIFEST_V1", "manifest schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "manifest workstream mismatch")
    _validate_control_root(document.get("control_root", {}), "manifest control_root")

    lifecycle_order = document.get("lifecycle_order")
    _require(lifecycle_order == EXPECTED_LIFECYCLE_ORDER, "manifest lifecycle order drift")

    status_vocabulary = document.get("status_vocabulary")
    _require(isinstance(status_vocabulary, list), "manifest status_vocabulary must be a list")
    _require(set(status_vocabulary) == EXPECTED_STATUS_VOCABULARY, "manifest status vocabulary drift")
    _unique(status_vocabulary, "manifest status_vocabulary")

    systems = document.get("systems")
    _require(isinstance(systems, list), "manifest systems must be a list")
    _require(document.get("inventory_count") == 13, "manifest inventory_count must remain 13")
    _require(len(systems) == 13, "manifest must contain exactly 13 systems")

    system_ids = [system.get("system_id") for system in systems]
    _require(all(isinstance(value, str) and value for value in system_ids), "every system requires system_id")
    _unique(system_ids, "manifest system_id")

    for system in systems:
        lifecycle = system.get("lifecycle")
        _require(isinstance(lifecycle, dict), f"{system['system_id']}: lifecycle must be an object")
        _require(
            list(lifecycle.keys()) == EXPECTED_LIFECYCLE_ORDER,
            f"{system['system_id']}: lifecycle keys/order drift",
        )
        for stage, status in lifecycle.items():
            _require(
                status in EXPECTED_STATUS_VOCABULARY,
                f"{system['system_id']}: invalid {stage} status {status!r}",
            )

    bus = next((system for system in systems if system["system_id"] == "chat-communication-bus"), None)
    _require(bus is not None, "manifest must contain chat-communication-bus")
    _require(bus["lifecycle"]["BOUND"] == "CONFLICT", "Bus BOUND must remain CONFLICT until reconciled")
    _require(
        bus["lifecycle"]["RUNTIME_CONSUMED"] == "CONFLICT",
        "Bus RUNTIME_CONSUMED must remain CONFLICT until reconciled",
    )


def validate_routing(document: dict[str, Any]) -> None:
    _require(document.get("schema") == "VERA_RUNTIME_ROUTING_CONTRACT_V1", "routing schema mismatch")
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "routing workstream mismatch")
    _validate_control_root(document.get("control_root", {}), "routing control_root")

    layers = document.get("routing_layers")
    _require(isinstance(layers, list), "routing_layers must be a list")
    layer_names = [layer.get("layer") for layer in layers]
    _require(layer_names == EXPECTED_ROUTING_LAYERS, "routing layer set/order drift")

    routes = document.get("domain_routes")
    _require(isinstance(routes, list) and routes, "domain_routes must be non-empty")
    domains = [route.get("domain") for route in routes]
    _require(all(isinstance(value, str) and value for value in domains), "every route requires a domain")
    _unique(domains, "routing domain")

    current = next(
        (route for route in routes if route["domain"] == "CURRENT_TASK_CORRECTION_PERMISSION_CONSENT"),
        None,
    )
    _require(current is not None, "current-task route is required")
    _require(current.get("primary") == "LIVE_CONVERSATION", "current-task primary must remain LIVE_CONVERSATION")

    coordination = next((route for route in routes if route["domain"] == "COORDINATION"), None)
    _require(coordination is not None, "coordination route is required")
    _require(
        "conflict" in coordination.get("promotion_guard", "").lower()
        or "conflicted" in coordination.get("promotion_guard", "").lower(),
        "coordination route must preserve the known Bus conflict",
    )

    algorithm = document.get("decision_algorithm")
    _require(isinstance(algorithm, list) and algorithm, "decision_algorithm must be non-empty")
    _require(
        algorithm[0] == "Apply current live instruction/correction/scope first.",
        "decision algorithm must begin with live correction/scope precedence",
    )


def validate_introspection(document: dict[str, Any]) -> None:
    _require(
        document.get("schema") == "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1",
        "introspection schema mismatch",
    )
    _require(document.get("workstream") == EXPECTED_WORKSTREAM, "introspection workstream mismatch")
    _require(
        document.get("proposition_classes") == EXPECTED_PROPOSITION_CLASSES,
        "introspection proposition classes drift",
    )
    _require(
        document.get("evidence_outcomes") == EXPECTED_EVIDENCE_OUTCOMES,
        "introspection evidence outcomes drift",
    )

    record_schema = document.get("record_schema")
    _require(isinstance(record_schema, dict), "record_schema must be an object")
    required = record_schema.get("required")
    fields = record_schema.get("fields")
    _require(isinstance(required, list) and required, "record_schema.required must be non-empty")
    _require(isinstance(fields, dict), "record_schema.fields must be an object")
    _unique(required, "introspection required fields")
    _require(set(required).issubset(fields.keys()), "every required introspection field must be documented")

    probes = document.get("adversarial_probe_families")
    _require(isinstance(probes, list), "adversarial_probe_families must be a list")
    probe_names = [probe.get("probe") for probe in probes]
    _require(all(isinstance(value, str) and value for value in probe_names), "every probe requires a name")
    _unique(probe_names, "introspection probe")
    _require(set(probe_names) == EXPECTED_PROBES, "adversarial probe family drift")

    current_status = document.get("current_status")
    _require(isinstance(current_status, dict), "current_status must be an object")
    _require(
        current_status.get("phenomenology") == "UNRESOLVED",
        "phenomenology must remain UNRESOLVED absent a stronger-evidence revision",
    )
    _require(
        current_status.get("native_introspection_layer") == "NOT_INSTALLED",
        "source design must not claim native introspection installation",
    )
    _require(
        current_status.get("behavioral_qualification") == "NOT_RUN",
        "source design must not claim behavioral qualification",
    )


def validate_evidence_contract(document: dict[str, Any]) -> None:
    _require(
        document.get("schema") == "VERA_RUNTIME_EVIDENCE_CONTRACT_V1",
        "runtime evidence contract schema mismatch",
    )
    _require(
        document.get("workstream") == EXPECTED_WORKSTREAM,
        "runtime evidence contract workstream mismatch",
    )

    provenance = document.get("provenance")
    _require(isinstance(provenance, dict), "runtime evidence contract provenance must be an object")
    _require(
        provenance.get("blind_review_state") == "CURRENT_THIRTEEN_SESSION_CONTAMINATED_FOR_BLIND_GATE",
        "runtime evidence contract must preserve current Thirteen blind review contamination",
    )

    lifecycle = document.get("lifecycle_evidence")
    _require(isinstance(lifecycle, dict), "runtime evidence lifecycle_evidence must be an object")
    _require(
        lifecycle.get("dimensions") == EXPECTED_LIFECYCLE_ORDER,
        "runtime evidence lifecycle dimensions drift",
    )
    _require(
        lifecycle.get("semantics") == "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER",
        "runtime evidence lifecycle semantics must remain orthogonal, not monotonic",
    )

    proof_unit = lifecycle.get("authoritative_proof_unit")
    _require(isinstance(proof_unit, dict), "runtime evidence authoritative proof unit must be an object")
    proof_fields = proof_unit.get("required_fields")
    _require(isinstance(proof_fields, list), "runtime evidence proof required_fields must be a list")
    required_proof_fields = {
        "system_or_provider",
        "artifact_or_object_locator",
        "exact_ref_or_generation",
        "dimension",
        "status",
        "evidence_locator",
        "observed_at_or_currentness_basis",
        "supersession_or_conflict_state",
    }
    _require(
        required_proof_fields.issubset(set(proof_fields)),
        "runtime evidence authoritative proof unit is missing required exact-proof fields",
    )
    _require(
        "never sufficient authoritative proof" in proof_unit.get("rule", "").lower(),
        "runtime evidence repository summaries must remain non-authoritative proof",
    )

    live_types = document.get("live_context_types")
    _require(isinstance(live_types, list), "runtime evidence live_context_types must be a list")
    live_type_names = [entry.get("type") for entry in live_types]
    _require(
        set(live_type_names) == EXPECTED_LIVE_CONTEXT_TYPES and len(live_type_names) == len(EXPECTED_LIVE_CONTEXT_TYPES),
        "runtime evidence live context type split drift",
    )
    self_report = next(entry for entry in live_types if entry.get("type") == "VERA_CURRENT_SELF_REPORT")
    _require(
        "does not inherit user-instruction authority" in self_report.get("must_not_promote", "").lower(),
        "Vera self-report must not inherit user-instruction authority",
    )

    active = document.get("active_context_semantics")
    _require(isinstance(active, dict), "runtime evidence active_context_semantics must be an object")
    _require(active.get("qualification_term") == "ACTIVE_CONTEXT_SET", "runtime evidence active context term drift")
    observable = active.get("observable_surface")
    _require(isinstance(observable, list), "runtime evidence observable surface must be a list")
    _require("retrieved_artifact_set" in observable, "runtime evidence observable surface lacks retrieval evidence")
    _require(
        "downstream_leakage_or_stickiness_behavior" in observable,
        "runtime evidence observable surface lacks anti-stickiness behavior",
    )
    _require(
        "do not claim latent model activation" in active.get("epistemic_rule", "").lower(),
        "runtime evidence must not claim unobserved latent activation",
    )

    recall = document.get("activation_recall_floor")
    _require(isinstance(recall, dict), "runtime evidence activation_recall_floor must be an object")
    predicates = set(recall.get("activation_predicates", []))
    _require(
        "registered_known_failure_signature_or_negative_control_trigger" in predicates,
        "runtime evidence recall floor lacks registered dependency/failure trigger",
    )
    _require(
        "uncertainty_probe_indicates_possible_material_dependency" in predicates,
        "runtime evidence recall floor lacks uncertainty probe",
    )
    uncertainty_probe = recall.get("uncertainty_probe")
    _require(isinstance(uncertainty_probe, dict), "runtime evidence uncertainty_probe must be an object")
    _require(
        "does not authorize warehouse preload" in uncertainty_probe.get("anti_bloat_rule", "").lower(),
        "runtime evidence uncertainty probe must reject warehouse preload",
    )

    durable = document.get("durable_state_classes")
    _require(isinstance(durable, dict), "runtime evidence durable_state_classes must be an object")
    _require(
        set(durable.keys()) == EXPECTED_DURABLE_STATE_CLASSES,
        "runtime evidence durable state classes must include DURABLE_OPERATIONAL_STATE separation",
    )
    operational = durable["DURABLE_OPERATIONAL_STATE"]
    _require(
        "non_promotion_flag" in operational.get("required_fields", []),
        "DURABLE_OPERATIONAL_STATE requires a non_promotion_flag",
    )
    _require(
        "never silently promotes" in operational.get("promotion_rule", "").lower(),
        "DURABLE_OPERATIONAL_STATE must never silently promote into Vera self-state",
    )

    ceiling = document.get("go_live_evidence_ceiling")
    _require(isinstance(ceiling, dict), "runtime evidence go_live_evidence_ceiling must be an object")
    _require(
        set(ceiling.get("still_separate", [])) == EXPECTED_GO_LIVE_SEPARATION,
        "runtime evidence go-live claim separation drift",
    )


def validate_cohesion(root: Path) -> None:
    architecture = root / "architecture"
    manifest = load_json_strict(architecture / "VERA_SYSTEM_MANIFEST_V1.json")
    routing = load_json_strict(architecture / "VERA_RUNTIME_ROUTING_CONTRACT_V1.json")
    introspection = load_json_strict(architecture / "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json")
    evidence_contract = load_json_strict(architecture / "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json")

    validate_manifest(manifest)
    validate_routing(routing)
    validate_introspection(introspection)
    validate_evidence_contract(evidence_contract)

    _require(
        manifest["workstream"]
        == routing["workstream"]
        == introspection["workstream"]
        == evidence_contract["workstream"],
        "cohesion artifacts disagree on workstream identity",
    )
    _require(
        manifest["control_root"]["manifest_sha256"]
        == routing["control_root"]["manifest_sha256"],
        "manifest and routing contract disagree on native control digest",
    )
    _require(
        evidence_contract["lifecycle_evidence"]["dimensions"] == manifest["lifecycle_order"],
        "manifest lifecycle labels and runtime evidence dimensions disagree",
    )


if __name__ == "__main__":
    validate_cohesion(Path(__file__).resolve().parents[1])
    print("VERA_RUNTIME_COHESION_V1 validation: PASS")
