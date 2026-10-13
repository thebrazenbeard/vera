"""Read-only reconciliation of explicitly bound Vera Supabase portfolio inclusion.

The provider inventory must be supplied by an external, fresh, read-only query.
This program never connects to Supabase, handles credentials, modifies providers,
or treats a matched database table as proof of Vera runtime consumption.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

CONTRACT = (
    Path(__file__).resolve().parents[1]
    / "supabase" / "composition" / "PORTFOLIO_INCLUSION_V1.json"
)
NAME = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
EDGE = re.compile(r"^edge:[a-z][a-z0-9-]*$")
DEPLOYED = {
    "DEPLOYED_PROVIDER_STATE",
    "DEPLOYED_INDEPENDENT_SERVICE",
    "DEPLOYED_HISTORICAL_STATE",
}
CANDIDATES = {"DESIGN_ONLY_OPTIONAL", "SEPARATE_OWNER_CANDIDATE"}
LOCAL = {"LOCAL_NON_SUPABASE"}


def _list_of_strings(data: dict[str, Any], field: str) -> list[str]:
    value = data.get(field, [])
    if not isinstance(value, list) or any(type(v) is not str for v in value):
        raise ValueError(f"{field} must be an array of exact strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field} has duplicate values")
    return value


def reconcile(
    contract: dict[str, Any],
    inventory: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(contract, dict) or contract.get("schema") != "VERA_SUPABASE_PORTFOLIO_INCLUSION_V1":
        raise ValueError("invalid inclusion contract")
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be an object")
    tables = _list_of_strings(inventory, "tables")
    edges = _list_of_strings(inventory, "edge_functions")
    if any(NAME.fullmatch(name) is None for name in tables):
        raise ValueError("inventory tables must be exact schema.table names")
    if any(re.fullmatch(r"[a-z][a-z0-9-]*", name) is None for name in edges):
        raise ValueError("invalid edge function name")
    observed = set(tables) | {"edge:" + slug for slug in edges}

    components = contract.get("components")
    if not isinstance(components, list) or not components:
        raise ValueError("missing components")
    seen_ids: set[str] = set()
    seen_objects: set[str] = set()
    findings: list[dict[str, str]] = []
    for item in components:
        if not isinstance(item, dict):
            raise ValueError("component must be an object")
        identity = item.get("id")
        category = item.get("classification")
        if not isinstance(identity, str) or not identity or identity in seen_ids:
            raise ValueError("duplicate or invalid component id")
        seen_ids.add(identity)
        if category not in DEPLOYED | CANDIDATES | LOCAL:
            raise ValueError(f"unknown classification: {identity}")
        expected = _list_of_strings(item, "observed_objects")
        proposed = _list_of_strings(item, "candidate_objects")
        if category in DEPLOYED and not expected:
            raise ValueError(f"deployed component has no observed objects: {identity}")
        if category not in DEPLOYED and expected:
            raise ValueError(f"candidate/local component claims deployment: {identity}")
        if category in LOCAL and proposed:
            raise ValueError(f"local component has a Supabase target: {identity}")
        for name in expected + proposed:
            if not NAME.fullmatch(name) and not EDGE.fullmatch(name):
                raise ValueError(f"invalid contract object: {name}")
            if name in seen_objects:
                raise ValueError(f"object assigned to multiple components: {name}")
            seen_objects.add(name)
        for name in expected:
            if name not in observed:
                findings.append({"component": identity, "object": name, "reason": "DEPLOYED_OBJECT_MISSING"})
        for name in proposed:
            if name in observed:
                findings.append({"component": identity, "object": name, "reason": "CANDIDATE_APPEARED_WITHOUT_ADMISSION"})
    return {
        "schema": "VERA_SUPABASE_INCLUSION_RECONCILIATION_V1",
        "status": "DRIFT" if findings else "MATCH",
        "checked_components": len(components),
        "observed_tables": len(tables),
        "observed_edge_functions": len(edges),
        "findings": findings,
        "unknown_observed_objects": sorted(observed - seen_objects),
        "runtime_consumption_verified": False,
        "permission_to_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    args = parser.parse_args()
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        report = reconcile(contract, inventory)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
