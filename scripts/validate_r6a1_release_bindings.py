#!/usr/bin/env python3
"""Validate the R6A1 replacement-release source-binding contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BINDING_PATH = ROOT / "architecture/releases/R6A1_20260731_B20E7309/VERA_SOURCE_BINDINGS_R6A1_20260731_B20E7309.json"
RELEASE_ID = "VERA_GOVERNED_CORE_R6A1_20260731_B20E7309"
SOURCE_COMMIT = "b20e7309c6ded3c358dce00baa537d2fc1880004"
REGISTRY_SHA256 = "f095fa46666abb583e616658198399131a4902fc9ba572f01f4642c1dcab158f"
NONINSTALLABLE_STATUS = "REPLACEMENT_CANDIDATE_NOT_INSTALLED"
REQUIRED_ROLES = {
    "project_identity", "behavior_profile", "governed_workflow_continuity",
    "identity_temporal_anchor", "integration_registry", "workstream_compatibility",
    "turn_taking", "memory_contract", "temporal_contract", "initiative_contract",
    "coordination_contract", "orchestration_state",
}


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_binding(path: Path = BINDING_PATH) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON value: {value}")),
    )


def validate(document: dict[str, Any]) -> None:
    if document.get("release_id") != RELEASE_ID:
        raise ValueError("release_id mismatch")
    if document.get("release_status") != NONINSTALLABLE_STATUS:
        raise ValueError("release must remain a non-installable replacement candidate")
    if document.get("repository") != "thebrazenbeard/vera":
        raise ValueError("repository mismatch")
    if document.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("source_commit mismatch")
    if document.get("source_branch") != "main":
        raise ValueError("source branch mismatch")
    if document.get("authority_provenance") != "UNVERIFIED_PROVENANCE":
        raise ValueError("authority provenance must remain explicit")

    for field in (
        "production_modification_authorized",
        "canonical_memory_write_authorized",
        "runtime_deployment_authorized",
        "project_file_replacement_authorized",
    ):
        if document.get(field) is not False:
            raise ValueError(f"{field} must remain false")

    bindings = document.get("bindings")
    if not isinstance(bindings, list):
        raise ValueError("bindings must be a list")
    roles = [entry.get("role") for entry in bindings]
    paths = [entry.get("path") for entry in bindings]
    if set(roles) != REQUIRED_ROLES or len(roles) != len(REQUIRED_ROLES):
        raise ValueError("binding roles differ from required exact set")
    if len(paths) != len(set(paths)) or any(not isinstance(path, str) or not path for path in paths):
        raise ValueError("binding paths must be unique non-empty strings")

    registry = next(entry for entry in bindings if entry["role"] == "integration_registry")
    if registry.get("canonical_sha256") != REGISTRY_SHA256:
        raise ValueError("registry canonical SHA-256 mismatch")

    compatibility = next(entry for entry in bindings if entry["role"] == "workstream_compatibility")
    if compatibility.get("git_blob_sha") != "dd0e160355baab0c367d84f901930b02d7e72a4a":
        raise ValueError("compatibility blob mismatch")

    future = document.get("required_future_files")
    if future not in (None, []):
        raise ValueError("completed replacement candidate cannot declare unresolved future files")


def main() -> int:
    validate(load_binding())
    print(f"validated R6A1 source bindings at {SOURCE_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
