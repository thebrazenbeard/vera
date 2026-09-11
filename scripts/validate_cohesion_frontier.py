from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_PROTECTED_EFFECTS = {
    "MERGE",
    "PRODUCTION_PROVIDER_MUTATION",
    "INSTALL_OR_CUTOVER",
    "CREDENTIAL_OR_PERMISSION_CHANGE",
    "PAID_CI_OR_OTHER_SPEND",
    "CANONICAL_MEMORY_PROMOTION",
    "BEHAVIORAL_QUALIFICATION",
    "AUTHORITY_PROMOTION",
    "PHENOMENOLOGY_PROMOTION",
}

REQUIRED_MUTABLE_INPUTS = {
    "vera-main",
    "vera-cohesion-pr104",
    "vera-affective-pr64",
    "vera-ov-cv-pr113",
}

EXPECTED_PR113_HEAD = "f7dbc3deeaaaeb46dcf7c7ea6b56a822f253232d"
EXPECTED_PR113_AHEAD_FROM_OVERLAP_AUDIT = 10
EXPECTED_PR113_RUNTIME_GENERATION = "ba6221f56b98be69c3ede1be9e3502eff897ca1a"
EXPECTED_PR113_BINDING_BLOB = "037883261bd324e8080c323f1d96ff32179780ee"
EXPECTED_PR113_DETACHMENT_TEST = "tests/test_runtime_cohesion_affect_observation_detachment.py"
EXPECTED_PR113_BINDING_PATH = "architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json"


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: str | Path) -> dict[str, Any]:
    data = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    if not isinstance(data, dict):
        raise ValueError("document must be a JSON object")
    return data


def _require_git_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError(f"{label} must be an exact 40-character Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _registry_heads(registry: dict[str, Any]) -> dict[str, str | None]:
    sources = registry.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source registry sources must be a list")
    result: dict[str, str | None] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source registry entry must be an object")
        source_id = source.get("id")
        if isinstance(source_id, str):
            result[source_id] = source.get("observed_head")
    return result


def validate_frontier(frontier: dict[str, Any], registry: dict[str, Any]) -> None:
    if frontier.get("schema") != "VERA_COHESION_FRONTIER_V0":
        raise ValueError("unsupported frontier schema")
    if frontier.get("status") != "WORKING_EVIDENCE_CUT_NOT_INSTALLATION_AUTHORITY":
        raise ValueError("frontier status must remain non-installation authority")
    if frontier.get("target_repository") != "thebrazenbeard/vera":
        raise ValueError("frontier target repository mismatch")
    if frontier.get("stop_on_drift") is not True:
        raise ValueError("frontier must stop on material drift")

    items = frontier.get("mutable_inputs")
    if not isinstance(items, list) or not items:
        raise ValueError("frontier mutable_inputs must be a non-empty list")

    ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("mutable input must be an object")
        source_id = item.get("id")
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("mutable input id must be non-empty")
        ids.append(source_id)
        by_id[source_id] = item
        _require_git_sha(item.get("current_observed_head"), f"{source_id} current head")
        _require_git_sha(item.get("source_registry_head"), f"{source_id} registry head")

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate mutable input id")
    if not REQUIRED_MUTABLE_INPUTS.issubset(by_id):
        raise ValueError("required mutable input is missing")

    registry_heads = _registry_heads(registry)
    for source_id, item in by_id.items():
        if source_id not in registry_heads:
            raise ValueError(f"frontier input missing from source registry: {source_id}")
        if item["source_registry_head"] != registry_heads[source_id]:
            raise ValueError(f"frontier registry predecessor mismatch: {source_id}")

        changed = item.get("current_observed_head") != item.get("source_registry_head")
        if item.get("changed_since_registry") is not changed:
            raise ValueError(f"changed_since_registry is inconsistent for {source_id}")
        if changed and item.get("supersedes_registry_head") != item.get("source_registry_head"):
            raise ValueError(f"registry predecessor must be explicitly superseded for {source_id}")

    pr113 = by_id["vera-ov-cv-pr113"]
    if pr113.get("current_observed_head") != EXPECTED_PR113_HEAD:
        raise ValueError("PR113 current head does not match the refreshed evidence cut")
    drift = pr113.get("material_drift")
    if not isinstance(drift, dict):
        raise ValueError("PR113 material drift record is required")
    paths = drift.get("changed_paths_since_overlap_audit")
    if not isinstance(paths, list) or not paths:
        raise ValueError("PR113 material drift must list changed paths")
    runtime_paths = [path for path in paths if isinstance(path, str) and path.startswith("runtime_cohesion/")]
    if runtime_paths and drift.get("classification") == "METADATA_ONLY":
        raise ValueError("runtime source drift cannot be classified as metadata only")
    if runtime_paths and drift.get("reconciliation_required_before_harvest") is not True:
        raise ValueError("material drift requires reconciliation before harvest")
    if (
        drift.get("ahead_by_since_overlap_audit") != EXPECTED_PR113_AHEAD_FROM_OVERLAP_AUDIT
        or drift.get("behind_by_since_overlap_audit") != 0
    ):
        raise ValueError("PR113 comparison counts do not match the observed evidence cut")
    if drift.get("runtime_generation") != EXPECTED_PR113_RUNTIME_GENERATION:
        raise ValueError("PR113 runtime generation does not match the observed freeze")
    if drift.get("binding_blob") != EXPECTED_PR113_BINDING_BLOB:
        raise ValueError("PR113 binding blob does not match the observed freeze")
    if EXPECTED_PR113_DETACHMENT_TEST not in paths:
        raise ValueError("PR113 detached-observation regression is missing from the evidence cut")
    if EXPECTED_PR113_BINDING_PATH not in paths:
        raise ValueError("PR113 bound freeze is missing from the evidence cut")

    protected = frontier.get("protected_effects_not_authorized")
    if not isinstance(protected, list) or not REQUIRED_PROTECTED_EFFECTS.issubset(set(protected)):
        raise ValueError("protected effect ceiling is incomplete")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    frontier = load_json_strict(root / "architecture/cohesion/VERA_COHESION_FRONTIER_V0_20260911.json")
    registry = load_json_strict(root / "architecture/cohesion/VERA_COHESION_SOURCE_REGISTRY_V0_20260911.json")
    validate_frontier(frontier, registry)
    print("VERA_COHESION_FRONTIER_V0: VALID")
