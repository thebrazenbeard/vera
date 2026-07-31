#!/usr/bin/env python3
"""Strict validation for the bounded V.E.R.A. integration-owner registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROUTES = {
    "workstream/identity",
    "workstream/time",
    "workstream/memory",
    "workstream/initiatives",
    "workstream/coordination",
    "workstream/integration",
}
OBSOLETE_ROUTE = "workstream/initiative"
EXTERNAL_AUTHORITY = "EXTERNAL_EXPLICIT_AUTHORIZATION"


class DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def validate_schema(instance: Any, schema: Any) -> None:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors
        )
        raise ValueError(f"integration registry schema validation failed: {detail}")


def validate_semantics(registry: dict[str, Any]) -> None:
    owners = registry["owners"]
    routes = [owner["route"] for owner in owners]
    route_set = set(routes)
    if len(routes) != len(route_set):
        raise ValueError("duplicate bounded owner route")
    if route_set != REQUIRED_ROUTES:
        raise ValueError(
            f"bounded owner routes differ from required set: "
            f"{sorted(route_set ^ REQUIRED_ROUTES)}"
        )

    aliases = registry["route_aliases"]
    if OBSOLETE_ROUTE in aliases or OBSOLETE_ROUTE in aliases.values():
        raise ValueError("obsolete singular Initiatives route is forbidden as alias")

    by_route = {owner["route"]: owner for owner in owners}
    for owner in owners:
        for dependency in (
            owner["upstream_dependencies"] + owner["downstream_dependencies"]
        ):
            if dependency not in route_set:
                raise ValueError(f"dependency references undeclared route: {dependency}")
        if owner["authority_owner"] not in route_set:
            raise ValueError("authority owner must be a declared workstream route")
        if owner["permission_owner"] not in route_set:
            raise ValueError("permission owner must be a declared workstream route")
        if owner["merge_authority"] != EXTERNAL_AUTHORITY:
            raise ValueError("CI or component state cannot supply merge authority")
        if owner["production_authority"] != EXTERNAL_AUTHORITY:
            raise ValueError("CI or component state cannot supply production authority")
        if owner["execution_authorized"]:
            raise ValueError(f"{owner['route']} may not claim execution authority")

    coordination = by_route["workstream/coordination"]
    if (
        coordination["record_class"] != "OPERATIONAL_COORDINATION"
        or coordination["canonical_memory_eligible"]
    ):
        raise ValueError("Coordination must remain operational and non-memory")

    initiatives = by_route["workstream/initiatives"]
    if initiatives["execution_authorized"]:
        raise ValueError("Initiatives may select or abstain but may not execute")

    integration = by_route["workstream/integration"]
    forbidden_component_classes = {
        "TEMPORAL_EVIDENCE", "CANONICAL_MEMORY", "ACTION_SELECTION",
        "OPERATIONAL_COORDINATION",
    }
    if integration["record_class"] in forbidden_component_classes:
        raise ValueError("Integration may own assurance, not component semantics")


def validate_registry(root: Path = ROOT) -> None:
    registry = load_json_strict(
        root / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
    )
    schema = load_json_strict(
        root / "schemas/vera_integration_registry_v1.schema.json"
    )
    validate_schema(registry, schema)
    validate_semantics(registry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate_registry(args.root.resolve())
    print("integration registry: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
