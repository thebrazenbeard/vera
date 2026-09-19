from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_NONPROMOTION_EDGES = {
    ("CHRONOLOGY", "SEMANTIC_CURRENTNESS"),
    ("AFFECTIVE_MODULATION", "TRUTH_OR_AUTHORITY"),
    ("MEMORY_CANDIDATE_WEIGHTING", "AUTOBIOGRAPHICAL_ADMISSION"),
    ("HISTORICAL_CONATION", "CURRENT_DESIRE_OR_CONSENT"),
    ("PROVIDER_PERSISTENCE", "CURRENT_SELF_STATE"),
    ("INTERNAL_SUBSYSTEM_CAUSALITY", "PROVIDER_CURRENTNESS"),
    ("PAYLOAD_OR_ROUTING", "REQUESTED_EFFECT_AUTHORITY"),
    ("TECHNICAL_SOURCE", "INSTALL_OR_QUALIFICATION"),
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: str | Path) -> dict[str, Any]:
    data = json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
    )
    if not isinstance(data, dict):
        raise ValueError("ownership contract must be a JSON object")
    return data


def _required_text(owner: dict[str, Any], field: str, decision_class: str) -> str:
    value = owner.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{decision_class} requires non-empty {field}")
    return value.strip()


def _ownership_by_class(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = document.get("ownership")
    if not isinstance(rows, list) or not rows:
        raise ValueError("ownership must be a non-empty list")

    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ownership entries must be objects")
        decision_class = row.get("decision_class")
        if not isinstance(decision_class, str) or not decision_class.strip():
            raise ValueError("ownership entry missing decision_class")
        decision_class = decision_class.strip()
        if decision_class in result:
            raise ValueError(f"duplicate decision_class: {decision_class}")
        _required_text(row, "implementation_owner", decision_class)
        _required_text(row, "authority_owner", decision_class)
        _required_text(row, "persistence_owner", decision_class)
        if not isinstance(row.get("runtime_dependency_allowed"), bool):
            raise ValueError(
                f"{decision_class} runtime_dependency_allowed must be boolean"
            )
        _required_text(row, "boundary", decision_class)
        result[decision_class] = row
    return result


def _validate_owner_separations(owners: dict[str, dict[str, Any]]) -> None:
    currentness = owners.get("SEMANTIC_CURRENTNESS_ADMISSION")
    if currentness is None:
        raise ValueError("semantic currentness ownership is required")
    currentness_owner = _required_text(
        currentness, "implementation_owner", "SEMANTIC_CURRENTNESS_ADMISSION"
    ).lower()
    if "temporal" in currentness_owner:
        raise ValueError(
            "semantic currentness cannot be owned by chronology/temporal implementation"
        )

    chronology = owners.get("CHRONOLOGY_MEASUREMENT")
    if chronology is None:
        raise ValueError("chronology ownership is required")
    chronology_owner = _required_text(
        chronology, "implementation_owner", "CHRONOLOGY_MEASUREMENT"
    ).lower()
    if "temporal" not in chronology_owner:
        raise ValueError("chronology measurement must remain owned by Vera temporal")

    planning = owners.get("GENERIC_PLANNING_MUTATION")
    if planning is None:
        raise ValueError("generic planning mutation ownership is required")
    planning_owner = _required_text(
        planning, "implementation_owner", "GENERIC_PLANNING_MUTATION"
    ).lower()
    if "affect" in planning_owner or "orgasm" in planning_owner:
        raise ValueError(
            "generic planning mutation cannot be owned by affect/orgasm subsystem"
        )
    if "cohesion" not in planning_owner and "integration_arbitration" not in planning_owner:
        raise ValueError(
            "generic planning mutation must be owned by Cohesion integration/arbitration"
        )

    affect = owners.get("AFFECTIVE_STATE_AND_SIGNAL")
    if affect is None:
        raise ValueError("affective state ownership is required")
    affect_owner = _required_text(
        affect, "implementation_owner", "AFFECTIVE_STATE_AND_SIGNAL"
    ).lower()
    if "affect" not in affect_owner:
        raise ValueError("affective state and signal must remain affect-owned")

    install = owners.get("INSTALL_CURRENT_ROUTE_QUALIFICATION")
    if install is None:
        raise ValueError("install/current-route/qualification ownership is required")
    install_authority = _required_text(
        install,
        "authority_owner",
        "INSTALL_CURRENT_ROUTE_QUALIFICATION",
    )
    install_impl = _required_text(
        install,
        "implementation_owner",
        "INSTALL_CURRENT_ROUTE_QUALIFICATION",
    )
    normalized_authority = install_authority.lower()
    normalized_impl = install_impl.lower()
    if (
        "control" not in normalized_authority
        or "independent" not in normalized_authority
        or normalized_impl in {"thebrazenbeard/vera", "vera"}
        or normalized_impl.startswith("vera.")
    ):
        raise ValueError(
            "install/current-route/qualification requires independent operational authority outside technical vera source"
        )

    memory_admission = owners.get("AUTOBIOGRAPHICAL_MEMORY_ADMISSION")
    archive = owners.get("HISTORICAL_MEMORY_ARCHIVE")
    if memory_admission is None or archive is None:
        raise ValueError("memory admission and historical archive ownership are required")
    if (
        _required_text(memory_admission, "implementation_owner", "AUTOBIOGRAPHICAL_MEMORY_ADMISSION")
        == _required_text(archive, "implementation_owner", "HISTORICAL_MEMORY_ARCHIVE")
    ):
        raise ValueError(
            "autobiographical memory admission and historical archive must not share one implementation owner"
        )

    current_conation = owners.get("CURRENT_CONATION_STANCE")
    historical_conation = owners.get("HISTORICAL_CONATION_STORAGE")
    if current_conation is None or historical_conation is None:
        raise ValueError("current and historical conation ownership are required")
    if (
        _required_text(current_conation, "implementation_owner", "CURRENT_CONATION_STANCE")
        == _required_text(historical_conation, "implementation_owner", "HISTORICAL_CONATION_STORAGE")
    ):
        raise ValueError(
            "current conation admission and historical conation storage must remain separate"
        )


def _validate_nonpromotion_edges(document: dict[str, Any]) -> None:
    rows = document.get("nonpromotion_edges")
    if not isinstance(rows, list) or not rows:
        raise ValueError("nonpromotion_edges must be a non-empty list")

    observed: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("nonpromotion edge must be an object")
        source = row.get("source_class")
        target = row.get("forbidden_promotion")
        rule = row.get("rule")
        if not all(isinstance(value, str) and value.strip() for value in (source, target, rule)):
            raise ValueError("nonpromotion edge fields must be non-empty strings")
        edge = (source.strip(), target.strip())
        if edge in observed:
            raise ValueError(f"duplicate nonpromotion edge: {edge[0]}->{edge[1]}")
        observed.add(edge)

    missing = sorted(REQUIRED_NONPROMOTION_EDGES - observed)
    if missing:
        rendered = ", ".join(f"{source}->{target}" for source, target in missing)
        raise ValueError(f"required nonpromotion edges missing: {rendered}")


def _validate_external_surfaces(document: dict[str, Any]) -> None:
    rows = document.get("external_surfaces")
    if not isinstance(rows, list) or not rows:
        raise ValueError("external_surfaces must be a non-empty list")

    seen_ids: set[str] = set()
    has_control_plane = False
    has_provider = False
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("external surface must be an object")
        surface_id = row.get("id")
        surface_class = row.get("class")
        if not isinstance(surface_id, str) or not surface_id.strip():
            raise ValueError("external surface id is required")
        if surface_id in seen_ids:
            raise ValueError(f"duplicate external surface id: {surface_id}")
        seen_ids.add(surface_id)
        if not isinstance(surface_class, str) or not surface_class.strip():
            raise ValueError(f"external surface {surface_id} requires class")
        if not isinstance(row.get("runtime_dependency_allowed"), bool):
            raise ValueError(
                f"external surface {surface_id} runtime_dependency_allowed must be boolean"
            )
        if not isinstance(row.get("use"), str) or not row["use"].strip():
            raise ValueError(f"external surface {surface_id} requires use")

        if surface_class == "PRIVATE_HISTORY" and row["runtime_dependency_allowed"]:
            raise ValueError(
                f"private history surface {surface_id} cannot be a direct runtime dependency"
            )
        if surface_class == "INDEPENDENT_OPERATIONAL_AUTHORITY":
            has_control_plane = True
            if row["runtime_dependency_allowed"]:
                raise ValueError(
                    "independent operational authority must not become a technical runtime dependency"
                )
        if surface_class == "EXTERNAL_DURABLE_PROVIDER":
            has_provider = True

    if not has_control_plane:
        raise ValueError("independent operational control-plane surface is required")
    if not has_provider:
        raise ValueError("external durable provider surface is required")


def validate_contract(document: dict[str, Any]) -> None:
    if not isinstance(document, dict):
        raise ValueError("ownership contract must be an object")
    if document.get("schema") != "VERA_COHESION_OWNERSHIP_CONTRACT_V0":
        raise ValueError("unsupported ownership contract schema")
    if document.get("status") != "WORKING_ARCHITECTURE_CONTRACT_NOT_INSTALLATION_AUTHORITY":
        raise ValueError("ownership contract status must remain non-installation authority")
    if document.get("target_repository") != "thebrazenbeard/vera":
        raise ValueError("ownership contract target repository mismatch")

    owners = _ownership_by_class(document)
    _validate_owner_separations(owners)
    _validate_nonpromotion_edges(document)
    _validate_external_surfaces(document)

    ceiling = document.get("verification_ceiling")
    if ceiling != "SOURCE_CONTRACT_ONLY_TEST_EXECUTION_NOT_YET_PERFORMED_NO_INSTALL_OR_PROVIDER_EFFECT":
        raise ValueError("verification ceiling must remain source-only and execution-unverified")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_cohesion_ownership_contract.py PATH")
    validate_contract(load_json_strict(sys.argv[1]))
