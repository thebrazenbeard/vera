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


def validate_cohesion(root: Path) -> None:
    architecture = root / "architecture"
    manifest = load_json_strict(architecture / "VERA_SYSTEM_MANIFEST_V1.json")
    routing = load_json_strict(architecture / "VERA_RUNTIME_ROUTING_CONTRACT_V1.json")
    introspection = load_json_strict(architecture / "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json")

    validate_manifest(manifest)
    validate_routing(routing)
    validate_introspection(introspection)

    _require(
        manifest["workstream"] == routing["workstream"] == introspection["workstream"],
        "cohesion artifacts disagree on workstream identity",
    )
    _require(
        manifest["control_root"]["manifest_sha256"]
        == routing["control_root"]["manifest_sha256"],
        "manifest and routing contract disagree on native control digest",
    )


if __name__ == "__main__":
    validate_cohesion(Path(__file__).resolve().parents[1])
    print("VERA_RUNTIME_COHESION_V1 validation: PASS")
