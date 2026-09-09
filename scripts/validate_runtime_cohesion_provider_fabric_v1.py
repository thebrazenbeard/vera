#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT_PATH = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
FABRIC_PATH = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
EVENT_SELECTOR_TOKENS = {"$source_ref", "$source_path", "$source_revision"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_provider_fabric(
    index: Mapping[str, Any],
    contract: Mapping[str, Any],
    fabric: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []

    if fabric.get("schema") != "VERA_PROVIDER_FABRIC_V1":
        errors.append("fabric schema must be VERA_PROVIDER_FABRIC_V1")
    if fabric.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("provider fabric must be NON_NORMATIVE_OPERATIONAL_SUPPORT")
    if set(fabric.get("normative_pair_refs", [])) != {
        "VERA_COHESION_INDEX_V1",
        "VERA_RUNTIME_CONTRACT_V1",
    }:
        errors.append("provider fabric normative_pair_refs must point only to the A+B schemas")

    evidence_classes = set(contract.get("evidence_classes", {}))
    privacy_classes = set(contract.get("privacy_classes", []))
    route_ids = {
        row.get("id")
        for row in index.get("route_declarations", [])
        if isinstance(row, Mapping) and isinstance(row.get("id"), str)
    }
    providers = fabric.get("providers")
    if not isinstance(providers, Mapping) or not providers:
        errors.append("provider fabric requires a non-empty providers map")
        providers = {}

    for provider_id, provider in providers.items():
        if not isinstance(provider, Mapping):
            errors.append(f"provider {provider_id!r} must be an object")
            continue
        if not provider.get("promotion_guard"):
            errors.append(f"provider {provider_id!r} requires promotion_guard")
        capabilities = provider.get("evidence_capability_refs")
        if not isinstance(capabilities, list) or not capabilities:
            errors.append(f"provider {provider_id!r} requires evidence_capability_refs")
        else:
            for capability in capabilities:
                if capability not in evidence_classes:
                    errors.append(f"provider {provider_id!r} references unknown evidence class {capability!r}")
        provider_routes = provider.get("route_refs")
        if not isinstance(provider_routes, list) or not provider_routes:
            errors.append(f"provider {provider_id!r} requires route_refs")
        else:
            for route_ref in provider_routes:
                if route_ref not in route_ids:
                    errors.append(f"provider {provider_id!r} references unknown route {route_ref!r}")

    comparison_modes = set(fabric.get("comparison_modes", {}))
    projection_ids: set[str] = set()
    for projection in fabric.get("projections", []):
        if not isinstance(projection, Mapping):
            errors.append("projection rows must be objects")
            continue
        projection_id = projection.get("id")
        if not isinstance(projection_id, str) or not projection_id:
            errors.append("projection requires id")
        elif projection_id in projection_ids:
            errors.append(f"duplicate projection id {projection_id!r}")
        else:
            projection_ids.add(projection_id)

        for field in ("source_provider", "target_provider"):
            provider_id = projection.get(field)
            if provider_id not in providers:
                errors.append(f"projection {projection_id!r} references unknown provider {provider_id!r} in {field}")
        mode = projection.get("comparison_mode")
        if mode not in comparison_modes:
            errors.append(f"projection {projection_id!r} references unknown comparison mode {mode!r}")
        for field in (
            "source_subject",
            "target_subject",
            "source_route_ref",
            "target_route_ref",
            "source_evidence_class",
            "target_evidence_class",
            "privacy_class",
            "source_ref_pattern",
            "source_path_pattern",
            "source_revision_field",
            "target_revision_field",
            "claim_ceiling",
        ):
            if not isinstance(projection.get(field), str) or not projection.get(field).strip():
                errors.append(f"projection {projection_id!r} requires non-empty {field}")

        for selector_field in ("source_event_selector", "target_event_selector"):
            selector = projection.get(selector_field)
            if selector is None:
                continue
            if not isinstance(selector, Mapping):
                errors.append(f"projection {projection_id!r} {selector_field} must be a mapping")
                continue
            for field_name, template in selector.items():
                if not isinstance(field_name, str) or not field_name.strip():
                    errors.append(f"projection {projection_id!r} {selector_field} has an invalid field name")
                if not isinstance(template, str) or not template.strip():
                    errors.append(f"projection {projection_id!r} {selector_field} has an invalid selector value")
                    continue
                if template.startswith("$") and template not in EVENT_SELECTOR_TOKENS:
                    errors.append(
                        f"projection {projection_id!r} {selector_field} references unsupported token {template!r}"
                    )

        source_provider_id = projection.get("source_provider")
        target_provider_id = projection.get("target_provider")
        source_provider = providers.get(source_provider_id, {}) if isinstance(providers, Mapping) else {}
        target_provider = providers.get(target_provider_id, {}) if isinstance(providers, Mapping) else {}
        source_route = projection.get("source_route_ref")
        target_route = projection.get("target_route_ref")
        source_class = projection.get("source_evidence_class")
        target_class = projection.get("target_evidence_class")
        privacy_class = projection.get("privacy_class")

        if source_route not in source_provider.get("route_refs", []):
            errors.append(f"projection {projection_id!r} source_route_ref is not bound to source provider")
        if target_route not in target_provider.get("route_refs", []):
            errors.append(f"projection {projection_id!r} target_route_ref is not bound to target provider")
        if source_class not in evidence_classes or source_class not in source_provider.get("evidence_capability_refs", []):
            errors.append(f"projection {projection_id!r} source_evidence_class is not supported by source provider/B")
        if target_class not in evidence_classes or target_class not in target_provider.get("evidence_capability_refs", []):
            errors.append(f"projection {projection_id!r} target_evidence_class is not supported by target provider/B")
        if privacy_class not in privacy_classes:
            errors.append(f"projection {projection_id!r} privacy_class is not declared by B")

    rules = fabric.get("global_rules", {})
    for field in (
        "projection_scope",
        "event_instance_binding",
        "newest_timestamp",
        "returned_item_typing",
        "missing_observation",
        "conflict",
        "temporal",
    ):
        if not isinstance(rules.get(field), str) or not rules.get(field).strip():
            errors.append(f"provider fabric global_rules requires {field}")

    return errors


def main() -> int:
    errors = validate_provider_fabric(load(INDEX_PATH), load(CONTRACT_PATH), load(FABRIC_PATH))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA_PROVIDER_FABRIC_V1: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
