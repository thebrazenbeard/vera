#!/usr/bin/env python3
"""Validate workflow-continuity registration across Integration assurance surfaces."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from scripts.validate_integration_registry import load_json_strict
from scripts.validate_workstream_compatibility import validate_semantics as validate_matrix_semantics


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_CONTRACT = "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1"
CLASSIFICATION_VALIDATOR = "scripts/validate_identity_temporal_anchor_classification.py"
WORKFLOW_ARTIFACTS = {
    "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
    "docs/GOVERNED_WORKFLOW_CONTINUITY_V1.md",
    "schemas/vera_governed_workflow_continuity_v1.schema.json",
    "scripts/validate_governed_workflow_continuity.py",
    "tests/test_governed_workflow_continuity.py",
}
INTERFACE_BINDINGS = {
    "VERA-IFACE-002": {
        "contract_field": "source_contract_ids",
        "artifact_role": "source_artifacts",
        "artifacts": {
            "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
            "scripts/validate_governed_workflow_continuity.py",
        },
        "capabilities": {
            "GOVERNED_WORKFLOW_CONTINUITY",
            "AUTHORITY_BOUNDARY_STOP",
        },
    },
    "VERA-IFACE-003": {
        "contract_field": "source_contract_ids",
        "artifact_role": "source_artifacts",
        "artifacts": {
            "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
            "scripts/validate_governed_workflow_continuity.py",
        },
        "capabilities": {
            "SAFE_AUTHORIZED_ADVANCEMENT",
            "WRITER_LEASE_BOUNDARY",
            "ABSTENTION_ON_HARD_STOP",
        },
    },
    "VERA-IFACE-010": {
        "contract_field": "target_contract_ids",
        "artifact_role": "target_artifacts",
        "artifacts": {
            "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json",
            "scripts/validate_governed_workflow_continuity.py",
        },
        "capabilities": {
            "WORKFLOW_CONTINUITY_FINDING",
            "AUTHORITY_STOP_PRESERVATION",
        },
    },
}
COORDINATION_EVIDENCE_CAPABILITIES = {
    "EXACT_HEAD_HANDOFF",
    "WRITER_LEASE_EVIDENCE",
    "STALE_STATE_RECONCILIATION",
    "USER_COURIER_AVOIDANCE",
}


def _owner(registry: dict[str, Any], route: str) -> dict[str, Any]:
    return next(item for item in registry["owners"] if item["route"] == route)


def _interface(matrix: dict[str, Any], interface_id: str) -> dict[str, Any]:
    return next(
        item for item in matrix["interfaces"]
        if item["interface_id"] == interface_id
    )


def validate_workflow_continuity_integration(
    matrix: dict[str, Any],
    registry: dict[str, Any],
    root: Path = ROOT,
) -> None:
    """Validate the new Identity behavior contract without weakening prior gates."""
    identity = _owner(registry, "workstream/identity")
    if WORKFLOW_CONTRACT not in identity["contract_ids"]:
        raise ValueError("Identity owner omits governed workflow-continuity contract")
    missing_artifacts = WORKFLOW_ARTIFACTS - set(identity["owned_artifacts"])
    if missing_artifacts:
        raise ValueError(
            "Identity owner omits governed workflow-continuity artifacts: "
            + ", ".join(sorted(missing_artifacts))
        )
    if CLASSIFICATION_VALIDATOR not in identity["owned_artifacts"]:
        raise ValueError("Identity owner omits temporal-anchor classification validator")
    if "Project Identity" not in identity["required_checks"]:
        raise ValueError("Identity owner omits Project Identity workflow evidence")

    for interface_id, binding in INTERFACE_BINDINGS.items():
        interface = _interface(matrix, interface_id)
        if WORKFLOW_CONTRACT not in interface[binding["contract_field"]]:
            raise ValueError(f"{interface_id} omits governed workflow-continuity contract")
        evidence = interface["acceptance_evidence"]
        missing = binding["artifacts"] - set(evidence[binding["artifact_role"]])
        if missing:
            raise ValueError(
                f"{interface_id} omits governed workflow-continuity evidence: "
                + ", ".join(sorted(missing))
            )
        missing_capabilities = binding["capabilities"] - set(interface["capabilities"])
        if missing_capabilities:
            raise ValueError(
                f"{interface_id} omits governed workflow-continuity capabilities: "
                + ", ".join(sorted(missing_capabilities))
            )
        if interface["execution_authorized"]:
            raise ValueError(f"{interface_id} may not gain execution authority")
        if interface["canonical_memory_transfer"]:
            raise ValueError(f"{interface_id} may not transfer canonical memory")

    coordination = _interface(matrix, "VERA-IFACE-009")
    missing_coordination = (
        COORDINATION_EVIDENCE_CAPABILITIES - set(coordination["capabilities"])
    )
    if missing_coordination:
        raise ValueError(
            "VERA-IFACE-009 omits workflow-continuity coordination evidence: "
            + ", ".join(sorted(missing_coordination))
        )
    if coordination["execution_authorized"]:
        raise ValueError("VERA-IFACE-009 may not gain execution authority")
    if coordination["canonical_memory_transfer"]:
        raise ValueError("VERA-IFACE-009 may not transfer canonical memory")

    # Run the full inherited registry and matrix gates after the focused checks so
    # hostile omissions receive a workflow-specific diagnostic without bypassing
    # any existing authority, ownership, artifact, or digest validation.
    validate_matrix_semantics(matrix, registry, root)


def validate_repository(root: Path = ROOT) -> None:
    root = root.resolve()
    matrix = load_json_strict(
        root / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
    )
    registry = load_json_strict(
        root / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
    )
    validate_workflow_continuity_integration(matrix, registry, root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate_repository(args.root.resolve())
    print("workflow-continuity integration inventory: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
