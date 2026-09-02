#!/usr/bin/env python3
"""Validate the current workflow-continuity integration overlay.

The legacy V1 integration registry and compatibility matrix remain independently
validated historical evidence. They no longer define current workflow semantics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.validate_governed_workflow_continuity_v2 import validate_contract

ROOT = Path(__file__).resolve().parents[1]
OVERLAY_PATH = "architecture/integration/WORKFLOW_CONTINUITY_INTEGRATION_CURRENT.json"
POINTER_PATH = "architecture/identity/WORKFLOW_CONTINUITY_CURRENT.json"
CURRENT_CONTRACT = "VERA_GOVERNED_WORKFLOW_CONTINUITY_V2"
HISTORICAL_CONTRACT = "VERA_GOVERNED_WORKFLOW_CONTINUITY_V1"
REQUIRED_CAPABILITIES = {
    "SPECIFIC_CURRENT_INSTRUCTION_PRECEDENCE",
    "NECESSARY_REVERSIBLE_SETUP",
    "PROPORTIONAL_EFFECT_CLASSES",
    "PROPORTIONAL_WRITER_OWNERSHIP",
    "REPOSITORY_LOCAL_STEWARDSHIP",
    "EXACT_STATE_EVIDENCE_WHERE_MATERIAL",
    "GITHUB_ONLY_WORK_COORDINATION",
    "CORRECTION_PERFORMANCE",
    "USER_COURIER_AVOIDANCE",
    "PROTECTED_EFFECT_BOUNDARIES",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def validate_workflow_continuity_integration(root: Path = ROOT) -> None:
    root = root.resolve()
    overlay_file = root / OVERLAY_PATH
    pointer_file = root / POINTER_PATH
    if not overlay_file.is_file():
        raise ValueError("missing current workflow integration overlay")
    if not pointer_file.is_file():
        raise ValueError("missing current workflow pointer")

    overlay = _load(overlay_file)
    pointer = _load(pointer_file)

    if overlay.get("lifecycle_status") != "CURRENT":
        raise ValueError("workflow integration overlay must be CURRENT")
    if overlay.get("current_workflow_contract_id") != CURRENT_CONTRACT:
        raise ValueError("workflow integration overlay must resolve to V2")
    if pointer.get("current_contract_id") != CURRENT_CONTRACT:
        raise ValueError("workflow current pointer must resolve to V2")
    if overlay.get("current_workflow_contract_path") != pointer.get("current_contract_path"):
        raise ValueError("workflow integration overlay and current pointer disagree on contract path")
    if overlay.get("historical_workflow_contract") != HISTORICAL_CONTRACT:
        raise ValueError("workflow integration overlay must classify V1 as historical predecessor")

    capabilities = overlay.get("required_capabilities")
    if not isinstance(capabilities, list) or set(capabilities) != REQUIRED_CAPABILITIES:
        raise ValueError("workflow integration overlay capability set differs")

    for field in ("historical_integration_registry", "historical_compatibility_matrix"):
        relative = overlay.get(field)
        if not isinstance(relative, str) or not (root / relative).is_file():
            raise ValueError(f"workflow integration overlay missing historical evidence path: {field}")

    rule = overlay.get("routing_rule")
    if not isinstance(rule, str) or "must not re-promote V1 lease semantics" not in rule:
        raise ValueError("workflow integration overlay must forbid V1 semantic re-promotion")

    v2_errors = validate_contract(root)
    if v2_errors:
        raise ValueError("current Protocol V2 contract invalid: " + "; ".join(v2_errors))


def validate_repository(root: Path = ROOT) -> None:
    validate_workflow_continuity_integration(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate_repository(args.root)
    print("workflow-continuity current integration overlay: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
