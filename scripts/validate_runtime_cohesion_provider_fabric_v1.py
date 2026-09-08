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
            "source_ref_pattern",
            "source_path_pattern",
            "source_revision_field",
            "target_revision_field",
            "claim_ceiling",
        ):
            if not isinstance(projection.get(field), str) or not projection.get(field).strip():
                errors.append(f"projection {projection_id!r} requires non-empty {field}")

    rules = fabric.get("global_rules", {})
    for field in (
        "projection_scope",
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
