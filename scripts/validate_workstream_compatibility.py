#!/usr/bin/env python3
"""Strict validation for the bounded V.E.R.A. compatibility matrix."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from scripts.validate_integration_registry import (
    canonical_json_sha256,
    load_json_strict,
    validate_repository_artifact,
    validate_schema as validate_registry_schema,
    validate_semantics as validate_registry_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PREDECESSOR_HEAD = "b73551173632d98e4a8dfe673120a3df1ac0a0a0"
EXTERNAL_AUTHORITY = "EXTERNAL_EXPLICIT_AUTHORIZATION"
REQUIRED_ROUTES = {
    "workstream/identity",
    "workstream/time",
    "workstream/memory",
    "workstream/initiatives",
    "workstream/coordination",
    "workstream/integration",
}
REQUIRED_INTERFACE_PAIRS = {
    ("workstream/identity", "workstream/time"),
    ("workstream/identity", "workstream/memory"),
    ("workstream/identity", "workstream/initiatives"),
    ("workstream/time", "workstream/memory"),
    ("workstream/time", "workstream/coordination"),
    ("workstream/initiatives", "workstream/coordination"),
    ("workstream/coordination", "workstream/memory"),
    ("workstream/memory", "workstream/integration"),
    ("workstream/coordination", "workstream/integration"),
    ("workstream/integration", "workstream/identity"),
}
EXPECTED_INTERFACE_OWNERS = {
    ("workstream/identity", "workstream/time"): (
        "workstream/identity", "workstream/time"
    ),
    ("workstream/identity", "workstream/memory"): (
        "workstream/identity", "workstream/memory"
    ),
    ("workstream/identity", "workstream/initiatives"): (
        "workstream/identity", "workstream/initiatives"
    ),
    ("workstream/time", "workstream/memory"): (
        "workstream/time", "workstream/memory"
    ),
    ("workstream/time", "workstream/coordination"): (
        "workstream/time", "workstream/coordination"
    ),
    ("workstream/initiatives", "workstream/coordination"): (
        "workstream/identity", "workstream/coordination"
    ),
    ("workstream/coordination", "workstream/memory"): (
        "workstream/memory", "workstream/memory"
    ),
    ("workstream/memory", "workstream/integration"): (
        "workstream/memory", "workstream/integration"
    ),
    ("workstream/coordination", "workstream/integration"): (
        "workstream/coordination", "workstream/integration"
    ),
    ("workstream/integration", "workstream/identity"): (
        "workstream/identity", "workstream/identity"
    ),
}
EXPECTED_OWNS = {
    "workstream/identity": {"AUTHORITY", "CORRECTION", "BEHAVIOR", "ROUTING"},
    "workstream/time": {
        "EVENT_TIME", "STATE_TIME", "RECORD_TIME", "RETRIEVAL_TIME",
        "TEMPORAL_PRECISION",
    },
    "workstream/memory": {
        "GOVERNED_SAVE", "GOVERNED_RECALL", "PROVENANCE", "LINEAGE",
        "REQUEST_IDENTITY",
    },
    "workstream/initiatives": {"ACTION_SELECTION", "ABSTENTION"},
    "workstream/coordination": {
        "ADDRESSED_EVENTS", "ACKNOWLEDGEMENT", "REVIEW_ROUTING",
        "OPERATIONAL_RECEIPTS",
    },
    "workstream/integration": {
        "COMPATIBILITY", "ASSEMBLY_EVIDENCE", "DRIFT_DETECTION",
        "RELEASE_ASSURANCE",
    },
}
CRITICAL_BANS = {
    "workstream/identity": {"ACTION_EXECUTION"},
    "workstream/time": {"CANONICAL_MEMORY"},
    "workstream/memory": {"TEMPORAL_SEMANTICS"},
    "workstream/initiatives": {"ACTION_EXECUTION"},
    "workstream/coordination": {"CANONICAL_MEMORY", "MODEL_AUTHORITY"},
    "workstream/integration": {
        "IDENTITY_SEMANTICS", "TEMPORAL_SEMANTICS", "CANONICAL_MEMORY",
        "ACTION_SELECTION", "OPERATIONAL_COORDINATION",
    },
}
IDENTITY_TIME_BINDING = {
    "source_contract_ids": {
        "VERA_PROJECT_IDENTITY_V1",
        "VERA_BEHAVIOR_PROFILE_V1",
    },
    "target_contract_ids": {
        "TEMPORAL_ENFORCEMENT_V1",
        "TEMPORAL_ROLE_PRECISION_V1",
        "VERA_IDENTITY_TEMPORAL_ANCHOR_V1",
    },
    "source_artifacts": {
        "architecture/identity/VERA_PROJECT_IDENTITY_V1.json",
        "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json",
    },
    "target_artifacts": {
        "protocol/temporal_enforcement.py",
        "protocol/temporal_role_precision.py",
        "scripts/validate_identity_temporal_anchor.py",
    },
    "required_checks": {
        "Project Identity",
        "Temporal enforcement kernel",
        "Temporal pilot",
    },
}
MEMORY_DURABILITY_BINDINGS = {
    "VERA-IFACE-002": {
        "artifacts": {
            "supabase/migrations/20260731003000_add_memory_request_idempotency.sql",
            "supabase/migrations/20260731003100_correct_memory_request_status_semantics.sql",
        },
        "checks": {
            "Memory durability single path",
            "Memory durability review corrections",
        },
    },
    "VERA-IFACE-004": {
        "artifacts": {
            "supabase/tests/validate_neutral_v3_memory_request_status_semantics.sql",
        },
        "checks": {"Memory durability review corrections"},
    },
    "VERA-IFACE-007": {
        "artifacts": {
            "supabase/tests/validate_neutral_v3_memory_durability_review_corrections.sql",
        },
        "checks": {"Memory durability review corrections"},
    },
    "VERA-IFACE-008": {
        "artifacts": {
            "supabase/migrations/20260731003000_add_memory_request_idempotency.sql",
            "supabase/migrations/20260731003100_correct_memory_request_status_semantics.sql",
            "supabase/tests/validate_neutral_v3_memory_idempotency.sql",
            "supabase/tests/validate_neutral_v3_memory_durability_review_corrections.sql",
            "supabase/tests/verify_neutral_v3_memory_receipt_recovery.sql",
        },
        "checks": {
            "Memory cross-chat contract",
            "Memory durability single path",
            "Memory durability review corrections",
            "Integration Assurance",
            "Temporal pilot",
        },
    },
}
NON_EVIDENTIARY_SELF_REFERENCES = {
    "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json",
    "scripts/validate_workstream_compatibility.py",
}


def validate_schema(instance: Any, schema: Any) -> None:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(
            f"{list(error.path)}: {error.message}" for error in errors
        )
        raise ValueError(f"compatibility matrix schema validation failed: {detail}")


def _claim_once(
    claims: dict[str, str], identity: str, owner: str, kind: str
) -> None:
    previous = claims.get(identity)
    if previous is not None:
        raise ValueError(
            f"duplicate {kind} {identity!r}: claimed by {previous} and {owner}"
        )
    claims[identity] = owner


def _validate_artifact_evidence(
    *,
    root: Path,
    interface_id: str,
    role: str,
    route: str,
    artifacts: list[str],
    artifact_owner: dict[str, str],
) -> None:
    for artifact in artifacts:
        if artifact in NON_EVIDENTIARY_SELF_REFERENCES:
            raise ValueError(
                f"{interface_id} {role} artifact {artifact!r} is self-referential "
                "and cannot certify compatibility"
            )
        if artifact_owner.get(artifact) != route:
            raise ValueError(
                f"{interface_id} {role} artifact {artifact!r} is not owned by {route}"
            )
        validate_repository_artifact(root, artifact)


def validate_semantics(
    matrix: dict[str, Any],
    registry: dict[str, Any],
    root: Path = ROOT,
) -> None:
    root = root.resolve()
    validate_registry_semantics(registry, root)
    if matrix["registry_id"] != registry["registry_id"]:
        raise ValueError("matrix registry_id does not match the validated registry")
    if matrix["registry_predecessor_head"] != REGISTRY_PREDECESSOR_HEAD:
        raise ValueError("matrix predecessor registry lineage has drifted")
    expected_digest = canonical_json_sha256(registry)
    if matrix["active_registry_sha256"] != expected_digest:
        raise ValueError(
            "matrix active registry digest does not match the checked-out registry"
        )
    if matrix["merge_authority"] != EXTERNAL_AUTHORITY:
        raise ValueError("CI or matrix state cannot supply merge authority")
    if matrix["production_authority"] != EXTERNAL_AUTHORITY:
        raise ValueError("CI or matrix state cannot supply production authority")

    registry_owners = {item["route"]: item for item in registry["owners"]}
    assertions = {item["route"]: item for item in matrix["ownership_assertions"]}
    if set(assertions) != REQUIRED_ROUTES:
        raise ValueError("ownership assertions must cover exactly six bounded routes")

    for route, assertion in assertions.items():
        if set(assertion["owns"]) != EXPECTED_OWNS[route]:
            raise ValueError(
                f"{route} ownership domain differs from canonical matrix intent"
            )
        if not CRITICAL_BANS[route].issubset(set(assertion["does_not_own"])):
            raise ValueError(f"{route} omits a required negative ownership boundary")
        if assertion["execution_authorized"]:
            raise ValueError(f"{route} may not claim execution authority")
        if (
            assertion["canonical_memory_eligible"]
            != registry_owners[route]["canonical_memory_eligible"]
        ):
            raise ValueError(
                f"{route} canonical-memory classification differs from registry"
            )

    contract_owner: dict[str, str] = {}
    artifact_owner: dict[str, str] = {}
    check_owners: dict[str, set[str]] = {}
    for route, owner in registry_owners.items():
        for contract_id in owner["contract_ids"]:
            contract_owner[contract_id] = route
        for artifact in owner["owned_artifacts"]:
            artifact_owner[artifact] = route
        for check in owner["required_checks"]:
            check_owners.setdefault(check, set()).add(route)

    interface_ids: dict[str, str] = {}
    adapters: dict[str, str] = {}
    finding_ids: dict[str, str] = {}
    pairs: set[tuple[str, str]] = set()

    for interface in matrix["interfaces"]:
        interface_id = interface["interface_id"]
        source = interface["source_route"]
        target = interface["target_route"]
        _claim_once(interface_ids, interface_id, interface_id, "interface_id")
        _claim_once(adapters, interface["required_adapter"], interface_id, "adapter")
        if source == target:
            raise ValueError(f"{interface_id} may not target its source route")
        if source not in REQUIRED_ROUTES or target not in REQUIRED_ROUTES:
            raise ValueError(f"{interface_id} references an undeclared route")
        if "workstream/initiative" in (source, target):
            raise ValueError("obsolete singular Initiatives route is forbidden")

        pair = (source, target)
        if pair not in REQUIRED_INTERFACE_PAIRS:
            raise ValueError(f"{interface_id} is not a required directional interface")
        if pair in pairs:
            raise ValueError(
                f"{interface_id} duplicates directional interface pair {pair!r}"
            )
        pairs.add(pair)

        for contract_id in interface["source_contract_ids"]:
            if contract_owner.get(contract_id) != source:
                raise ValueError(
                    f"{interface_id} source contract {contract_id!r} "
                    f"is not owned by {source}"
                )
        for contract_id in interface["target_contract_ids"]:
            if contract_owner.get(contract_id) != target:
                raise ValueError(
                    f"{interface_id} target contract {contract_id!r} "
                    f"is not owned by {target}"
                )

        evidence = interface["acceptance_evidence"]
        _validate_artifact_evidence(
            root=root,
            interface_id=interface_id,
            role="source",
            route=source,
            artifacts=evidence["source_artifacts"],
            artifact_owner=artifact_owner,
        )
        _validate_artifact_evidence(
            root=root,
            interface_id=interface_id,
            role="target",
            route=target,
            artifacts=evidence["target_artifacts"],
            artifact_owner=artifact_owner,
        )
        allowed_check_routes = {source, target}
        for check in evidence["required_checks"]:
            if not check_owners.get(check, set()).intersection(allowed_check_routes):
                raise ValueError(
                    f"{interface_id} check {check!r} is not declared by either endpoint"
                )

        if pair == ("workstream/identity", "workstream/time"):
            observed = {
                "source_contract_ids": set(interface["source_contract_ids"]),
                "target_contract_ids": set(interface["target_contract_ids"]),
                "source_artifacts": set(evidence["source_artifacts"]),
                "target_artifacts": set(evidence["target_artifacts"]),
                "required_checks": set(evidence["required_checks"]),
            }
            for field, expected in IDENTITY_TIME_BINDING.items():
                if observed[field] != expected:
                    raise ValueError(
                        f"{interface_id} Identity-to-Time temporal-anchor binding "
                        f"differs at {field}"
                    )

        memory_binding = MEMORY_DURABILITY_BINDINGS.get(interface_id)
        if memory_binding is not None:
            memory_artifacts = set(evidence["source_artifacts"]) | set(
                evidence["target_artifacts"]
            )
            if not memory_binding["artifacts"].issubset(memory_artifacts):
                raise ValueError(
                    f"{interface_id} omits accepted Memory durability artifacts"
                )
            if not memory_binding["checks"].issubset(set(evidence["required_checks"])):
                raise ValueError(
                    f"{interface_id} omits accepted Memory durability checks"
                )
        if interface_id == "VERA-IFACE-008":
            if set(evidence["source_artifacts"]) != MEMORY_DURABILITY_BINDINGS[
                interface_id
            ]["artifacts"]:
                raise ValueError(
                    "VERA-IFACE-008 Memory receipt evidence differs from accepted "
                    "durability and recovery inventory"
                )
            if interface["findings"][0]["code"] != (
                "MEMORY_RECEIPT_ASSURANCE_ADAPTER_NOT_ASSEMBLED"
            ):
                raise ValueError(
                    "VERA-IFACE-008 must report the unresolved assembly adapter, "
                    "not a closed component gate"
                )

        expected_authority, expected_permission = EXPECTED_INTERFACE_OWNERS[pair]
        if interface["authority_owner"] != expected_authority:
            raise ValueError(
                f"{interface_id} authority owner must be {expected_authority}"
            )
        if interface["permission_owner"] != expected_permission:
            raise ValueError(
                f"{interface_id} permission owner must be {expected_permission}"
            )
        if interface["execution_authorized"]:
            raise ValueError(f"{interface_id} may not claim execution authority")
        if interface["canonical_memory_transfer"]:
            raise ValueError(
                f"{interface_id} may not silently promote interface data to canonical memory"
            )

        if source == "workstream/initiatives":
            required = {"ACTION_SELECTION", "ABSTENTION", "NO_EXECUTION_AUTHORITY"}
            if not required.issubset(set(interface["capabilities"])):
                raise ValueError(
                    "Initiatives interface must preserve selection, abstention, "
                    "and no-execution"
                )
        if source == "workstream/coordination" and target == "workstream/memory":
            required = {
                "OPERATIONAL_EVENT_REFERENCE",
                "DATA_NOT_INSTRUCTION",
                "NO_CANONICAL_PROMOTION",
            }
            if not required.issubset(set(interface["capabilities"])):
                raise ValueError(
                    "Coordination-to-Memory interface must remain operational "
                    "and non-promoting"
                )
        if source == "workstream/integration" and (
            "NO_COMPONENT_SEMANTICS" not in interface["capabilities"]
        ):
            raise ValueError(
                "Integration findings must disclaim component-semantic ownership"
            )

        for finding in interface["findings"]:
            _claim_once(
                finding_ids, finding["finding_id"], interface_id, "finding_id"
            )

    if pairs != REQUIRED_INTERFACE_PAIRS:
        raise ValueError(
            "interface pair coverage differs from required matrix: "
            f"{sorted(pairs ^ REQUIRED_INTERFACE_PAIRS)}"
        )


def validate_compatibility(root: Path = ROOT) -> None:
    root = root.resolve()
    matrix = load_json_strict(
        root / "architecture/integration/VERA_WORKSTREAM_COMPATIBILITY_V1.json"
    )
    matrix_schema = load_json_strict(
        root / "schemas/vera_workstream_compatibility_v1.schema.json"
    )
    registry = load_json_strict(
        root / "architecture/integration/VERA_INTEGRATION_REGISTRY_V1.json"
    )
    registry_schema = load_json_strict(
        root / "schemas/vera_integration_registry_v1.schema.json"
    )
    validate_registry_schema(registry, registry_schema)
    validate_schema(matrix, matrix_schema)
    validate_semantics(matrix, registry, root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    validate_compatibility(args.root.resolve())
    print("workstream compatibility matrix: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
