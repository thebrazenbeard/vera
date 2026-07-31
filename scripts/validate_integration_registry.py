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

EXPECTED_OWNER_IDENTITIES = {
    "workstream/identity": {
        "contract_ids": {
            "VERA_PROJECT_IDENTITY_V1",
            "VERA_BEHAVIOR_PROFILE_V1",
        },
        "owned_artifacts": {
            "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
            "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json",
        },
        "required_checks": {"Project Identity"},
    },
    "workstream/time": {
        "contract_ids": {
            "TEMPORAL_ENFORCEMENT_V1",
            "TEMPORAL_ROLE_PRECISION_V1",
        },
        "owned_artifacts": {
            "protocol/temporal_enforcement.py",
            "protocol/temporal_role_precision.py",
        },
        "required_checks": {
            "Temporal enforcement kernel",
            "Temporal pilot",
        },
    },
    "workstream/memory": {
        "contract_ids": {"VERA_MEMORY_CROSS_CHAT_CONTRACT_V1"},
        "owned_artifacts": {
            "supabase/migrations/20260730213000_harden_neutral_v3_memory_contract.sql",
            "supabase/migrations/20260730213100_tighten_neutral_v3_memory_governance.sql",
            "supabase/migrations/20260730213200_close_neutral_v3_memory_review_gaps.sql",
            "supabase/tests/validate_neutral_v3_memory_contract.sql",
            "supabase/tests/validate_neutral_v3_memory_governance.sql",
            "supabase/tests/validate_neutral_v3_memory_review_corrections.sql",
            "supabase/tests/validate_neutral_v3_memory_temporal_fields.sql",
        },
        "required_checks": {
            "Memory cross-chat contract",
            "Temporal pilot",
        },
    },
    "workstream/initiatives": {
        "contract_ids": {"VERA_INITIATIVE_KERNEL_V0_1"},
        "owned_artifacts": {"protocol/initiative_kernel.py"},
        "required_checks": {
            "Initiative kernel",
            "Temporal pilot",
        },
    },
    "workstream/coordination": {
        "contract_ids": {"VERA_COORDINATION_BUS_V1"},
        "owned_artifacts": {
            "coordination_bus/__init__.py",
            "coordination_bus/contracts.py",
            "coordination_bus/core.py",
            "coordination_bus/in_memory.py",
            "coordination_bus/supabase_sql.py",
            "coordination_bus/temporal.py",
            "coordination_bus/verified_temporal.py",
        },
        "required_checks": {
            "Coordination bus",
            "Temporal pilot",
        },
    },
    "workstream/integration": {
        "contract_ids": {"VERA_INTEGRATION_ASSURANCE_V1"},
        "owned_artifacts": {
            "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json",
            "scripts/validate_integration_registry.py",
        },
        "required_checks": {"Integration Assurance"},
    },
}


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


def _claim_once(
    claimed: dict[str, str],
    *,
    identity: str,
    route: str,
    field_name: str,
) -> None:
    previous = claimed.get(identity)
    if previous is not None:
        raise ValueError(
            f"cross-owner {field_name} collision: {identity!r} "
            f"claimed by {previous} and {route}"
        )
    claimed[identity] = route


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
    contract_claims: dict[str, str] = {}
    artifact_claims: dict[str, str] = {}

    for owner in owners:
        route = owner["route"]
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
            raise ValueError(f"{route} may not claim execution authority")

        for contract_id in owner["contract_ids"]:
            _claim_once(
                contract_claims,
                identity=contract_id,
                route=route,
                field_name="contract_id",
            )
        for artifact in owner["owned_artifacts"]:
            _claim_once(
                artifact_claims,
                identity=artifact,
                route=route,
                field_name="owned_artifact",
            )

        expected = EXPECTED_OWNER_IDENTITIES[route]
        for field_name in ("contract_ids", "owned_artifacts", "required_checks"):
            actual_values = owner[field_name]
            if len(actual_values) != len(set(actual_values)):
                raise ValueError(f"{route} contains duplicate {field_name}")
            actual = set(actual_values)
            if actual != expected[field_name]:
                raise ValueError(
                    f"{route} {field_name} differ from canonical source intent: "
                    f"{sorted(actual ^ expected[field_name])}"
                )

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
        "TEMPORAL_EVIDENCE",
        "CANONICAL_MEMORY",
        "ACTION_SELECTION",
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
