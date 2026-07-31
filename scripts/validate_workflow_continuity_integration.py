#!/usr/bin/env python3
"""Validate governed workflow-continuity registration and interface evidence."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from scripts.validate_integration_registry import load_json_strict, validate_registry
from scripts.validate_workstream_compatibility import validate_compatibility

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_CONTRACT = "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1"
PROJECT_IDENTITY_CHECK = "Project Identity"
REQUIRED_IDENTITY_ARTIFACTS = {
    "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
    "docs/GOVERNED_WORKFLOW_CONTINUITY_V1.md",
    "schemas/vera_governed_workflow_continuity_v1.schema.json",
    "scripts/validate_governed_workflow_continuity.py",
    "tests/test_governed_workflow_continuity.py",
    "scripts/validate_identity_temporal_anchor_classification.py",
}
REQUIRED_INTERFACE_ARTIFACTS = {
    "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
    "scripts/validate_governed_workflow_continuity.py",
}
REQUIRED_INTERFACES = {
    "VERA-IFACE-002": "workstream/memory",
    "VERA-IFACE-003": "workstream/initiatives",
}


def _owner(registry: dict[str, Any], route: str) -> dict[str, Any]:
    return next(item for item in registry["owners"] if item["route"] == route)


def _interface(matrix: dict[str, Any], interface_id: str) -> dict[str, Any]:
    return next(
        item for item in matrix["interfaces"]
        if item["interface_id"] == interface_id
    )


def validate_binding(matrix: dict[str, Any], registry: dict[str, Any]) -> None:
    identity = _owner(registry, "workstream/identity")
    if WORKFLOW_CONTRACT not in identity["contract_ids"]:
        raise ValueError("Identity registry omits governed workflow-continuity contract")

    observed_artifacts = set(identity["owned_artifacts"])
    missing = REQUIRED_IDENTITY_ARTIFACTS - observed_artifacts
    if missing:
        raise ValueError(
            "Identity registry omits governed workflow-continuity artifacts: "
            f"{sorted(missing)}"
        )
    if PROJECT_IDENTITY_CHECK not in identity["required_checks"]:
        raise ValueError("Identity registry omits Project Identity workflow evidence")

    for interface_id, target_route in REQUIRED_INTERFACES.items():
        interface = _interface(matrix, interface_id)
        if interface["source_route"] != "workstream/identity":
            raise ValueError(f"{interface_id} source must remain workstream/identity")
        if interface["target_route"] != target_route:
            raise ValueError(f"{interface_id} target must remain {target_route}")
        if WORKFLOW_CONTRACT not in interface["source_contract_ids"]:
            raise ValueError(f"{interface_id} omits governed workflow-continuity contract")

        evidence = interface["acceptance_evidence"]
        missing_evidence = REQUIRED_INTERFACE_ARTIFACTS - set(
            evidence["source_artifacts"]
        )
        if missing_evidence:
            raise ValueError(
                f"{interface_id} omits governed workflow-continuity evidence: "
                f"{sorted(missing_evidence)}"
            )
        if PROJECT_IDENTITY_CHECK not in evidence["required_checks"]:
            raise ValueError(f"{interface_id} omits Project Identity workflow evidence")
        if interface["execution_authorized"]:
            raise ValueError(f"{interface_id} may not grant execution authority")
        if interface["canonical_memory_transfer"]:
            raise ValueError(f"{interface_id} may not grant canonical-memory transfer")


def validate_contract(root: Path = ROOT) -> None:
    root = root.resolve()
    validate_registry(root)
    validate_compatibility(root)
    registry = load_json_strict(
        root / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
    )
    matrix = load_json_strict(
        root / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
    )
    validate_binding(matrix, registry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate_contract(args.root)
    print("governed workflow continuity integration: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
