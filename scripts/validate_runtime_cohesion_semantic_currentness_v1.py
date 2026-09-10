#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
DISPATCH_ID = "dispatch:semantic-currentness"
EXPECTED_MODE = "EXACT_SHARED_R10_CONTROL_BINDING"
EXPECTED_CONTROL_ROOT_REF = "VERA_RUNTIME_CONTRACT_V1#control_root"
EXPECTED_SOURCE_REPOSITORY = "thebrazenbeard/vera-control-plane"
EXPECTED_SOURCE_LOGICAL_ID = "VERA_PROJECT_SOURCE_MANIFEST"
EXPECTED_OWNER_LOGICAL_ID = "VERA_FULL_SYSTEM_PROJECT_INSTRUCTIONS"
EXPECTED_SOURCE_IDENTITY = f"github:{EXPECTED_SOURCE_REPOSITORY}#{EXPECTED_SOURCE_LOGICAL_ID}"
EXPECTED_CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"
EXPECTED_SUPERSESSION_STATE = "CURRENT_OBSERVATION"
EXPECTED_SHARED_FIELDS = [
    "control_release",
    "control_round",
    "control_manifest_sha256",
    "binding_source_identity",
    "binding_source_revision",
    "binding_currentness_state",
    "binding_supersession_state",
]


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("runtime contract must be an object")
    return value


def validate_semantic_currentness_binding(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    control_root = contract.get("control_root")
    if not isinstance(control_root, Mapping):
        return ["runtime contract control_root is required"]
    if control_root.get("release") != "R10A0":
        errors.append("semantic currentness requires exact R10A0 control release")
    if control_root.get("round") != "R10":
        errors.append("semantic currentness requires exact R10 control round")
    manifest = control_root.get("manifest_sha256")
    if not isinstance(manifest, str) or len(manifest) != 64:
        errors.append("semantic currentness requires exact control manifest SHA-256")
    if control_root.get("source_repository") != EXPECTED_SOURCE_REPOSITORY:
        errors.append("semantic currentness control source repository drift")
    if control_root.get("source_logical_id") != EXPECTED_SOURCE_LOGICAL_ID:
        errors.append("semantic currentness control source logical id drift")
    if control_root.get("owner_logical_id") != EXPECTED_OWNER_LOGICAL_ID:
        errors.append("semantic currentness control owner logical id drift")

    registry = contract.get("resolver_dispatch_decisive_evidence")
    decisive = registry.get(DISPATCH_ID) if isinstance(registry, Mapping) else None
    if not isinstance(decisive, Mapping):
        return errors + ["semantic currentness decisive-evidence entry is required"]
    if decisive.get("all_of") != ["control_source", "live_observation"]:
        errors.append("semantic currentness must still require control_source plus live_observation")
    if decisive.get("any_of") != []:
        errors.append("semantic currentness any_of must remain empty")

    relation = decisive.get("relational_binding")
    if not isinstance(relation, Mapping):
        return errors + ["semantic currentness relational_binding is required"]
    expected = {
        "mode": EXPECTED_MODE,
        "control_root_ref": EXPECTED_CONTROL_ROOT_REF,
        "required_source_identity": EXPECTED_SOURCE_IDENTITY,
        "required_currentness_state": EXPECTED_CURRENTNESS_STATE,
        "required_supersession_state": EXPECTED_SUPERSESSION_STATE,
        "shared_metadata_fields": EXPECTED_SHARED_FIELDS,
    }
    if dict(relation) != expected:
        errors.append("semantic currentness relational binding drift")

    resolver = contract.get("authority_resolvers", {}).get("semantic_currentness", {})
    rule = resolver.get("rule", "") if isinstance(resolver, Mapping) else ""
    fail_closed = resolver.get("fail_closed", "") if isinstance(resolver, Mapping) else ""
    if "relationally cross-bound" not in rule:
        errors.append("semantic currentness resolver must state relational cross-binding")
    if "conflicting predecessor/control artifact" not in fail_closed:
        errors.append("semantic currentness resolver must fail closed on conflicting control artifacts")
    return errors


def main() -> int:
    errors = validate_semantic_currentness_binding(load_contract())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA semantic currentness relational binding: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
