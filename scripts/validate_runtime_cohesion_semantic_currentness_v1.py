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
EXPECTED_SOURCE_COMMIT = "a5b16fbdf031d4e7347ab299ba5e34eb7602bca7"
EXPECTED_SOURCE_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_PROJECT_SOURCE_MANIFEST_R10.json"
EXPECTED_SOURCE_GIT_BLOB = "8a67feb47b2ce3d6f0737e58983ab8c9fc810139"
EXPECTED_SOURCE_LOGICAL_ID = "VERA_PROJECT_SOURCE_MANIFEST"
EXPECTED_OWNER_LOGICAL_ID = "VERA_FULL_SYSTEM_PROJECT_INSTRUCTIONS"
EXPECTED_OWNER_PATH = "project-instructions/r10a0/rounds/r10/VERA_R10A0_FULL_SYSTEM_PROJECT_INSTRUCTIONS_R10.md"
EXPECTED_OWNER_GIT_BLOB = "a01464271bb672d89f5d703e6e53590e126f4d44"
EXPECTED_MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
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

    expected_root = {
        "release": "R10A0",
        "round": "R10",
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "source_repository": EXPECTED_SOURCE_REPOSITORY,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "source_path": EXPECTED_SOURCE_PATH,
        "source_git_blob": EXPECTED_SOURCE_GIT_BLOB,
        "source_logical_id": EXPECTED_SOURCE_LOGICAL_ID,
        "owner_logical_id": EXPECTED_OWNER_LOGICAL_ID,
        "owner_path": EXPECTED_OWNER_PATH,
        "owner_git_blob": EXPECTED_OWNER_GIT_BLOB,
    }
    if dict(control_root) != expected_root:
        errors.append("semantic currentness control_root must bind the exact immutable R10 manifest and owner Git objects")

    origin_registry = contract.get("provider_origin_validation")
    origin_policy = origin_registry.get(DISPATCH_ID) if isinstance(origin_registry, Mapping) else None
    if not isinstance(origin_policy, Mapping):
        errors.append("semantic currentness provider-origin validation policy is required")
    else:
        if origin_policy.get("required_for_provider_admission") is not True:
            errors.append("semantic currentness provider-origin validation must be mandatory")
        if origin_policy.get("claimant_metadata_is_not_origin_proof") is not True:
            errors.append("semantic currentness must explicitly reject claimant metadata as origin proof")
        required_fields = origin_policy.get("exact_control_root_fields")
        expected_fields = [
            "source_repository",
            "source_commit",
            "source_path",
            "source_git_blob",
            "manifest_sha256",
            "owner_logical_id",
            "owner_path",
            "owner_git_blob",
        ]
        if required_fields != expected_fields:
            errors.append("semantic currentness exact provider-origin field registry drift")
        methods = origin_policy.get("provider_methods")
        expected_methods = {
            "control_source": {"provider": "github", "validation_method": "GITHUB_EXACT_OBJECT_READBACK"},
            "live_observation": {"provider": "live_conversation", "validation_method": "LIVE_EXACT_CONTROL_OBJECT_ATTESTATION"},
        }
        if methods != expected_methods:
            errors.append("semantic currentness provider-origin method registry drift")
        binding_rule = origin_policy.get("binding_rule", "")
        if "separately composed runtime-owned origin verifier" not in binding_rule:
            errors.append("semantic currentness origin policy must bind independent runtime-owned verifier composition")
        if "ordinary AdapterRegistry retrieval-adapter assertions cannot supply or substitute" not in binding_rule:
            errors.append("semantic currentness origin policy must reject ordinary retrieval-adapter self-attestation")

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
    expected_relation = {
        "mode": EXPECTED_MODE,
        "control_root_ref": EXPECTED_CONTROL_ROOT_REF,
        "required_source_identity": EXPECTED_SOURCE_IDENTITY,
        "required_currentness_state": EXPECTED_CURRENTNESS_STATE,
        "required_supersession_state": EXPECTED_SUPERSESSION_STATE,
        "shared_metadata_fields": EXPECTED_SHARED_FIELDS,
    }
    if dict(relation) != expected_relation:
        errors.append("semantic currentness relational binding drift")

    resolver = contract.get("authority_resolvers", {}).get("semantic_currentness", {})
    rule = resolver.get("rule", "") if isinstance(resolver, Mapping) else ""
    fail_closed = resolver.get("fail_closed", "") if isinstance(resolver, Mapping) else ""
    if "separately composed runtime-owned origin verifier" not in rule:
        errors.append("semantic currentness resolver must require independent runtime-owned origin verification")
    if "claimant-authored provenance metadata" not in fail_closed:
        errors.append("semantic currentness resolver must fail closed on claimant-authored provenance metadata")
    if "ordinary retrieval-adapter self-attestation" not in fail_closed:
        errors.append("semantic currentness resolver must fail closed on ordinary retrieval-adapter self-attestation")
    return errors


def main() -> int:
    errors = validate_semantic_currentness_binding(load_contract())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA semantic currentness exact-object independent origin verifier: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
