#!/usr/bin/env python3
"""Validate the R6A1 replacement-release source-binding contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BINDING_PATH = (
    ROOT
    / "architecture"
    / "releases"
    / "R6A1_20260731_B20E7309"
    / "VERA_SOURCE_BINDINGS_R6A1_20260731_B20E7309.json"
)
RELEASE_ID = "VERA_GOVERNED_CORE_R6A1_20260731_B20E7309"
SOURCE_COMMIT = "b20e7309c6ded3c358dce00baa537d2fc1880004"
REGISTRY_SHA256 = "f095fa46666abb583e616658198399131a4902fc9ba572f01f4642c1dcab158f"
NONINSTALLABLE_STATUS = "REPLACEMENT_CANDIDATE_NOT_INSTALLED"
REQUIRED_ROLES = {
    "project_identity",
    "behavior_profile",
    "governed_workflow_continuity",
    "identity_temporal_anchor",
    "integration_registry",
    "workstream_compatibility",
    "turn_taking",
    "memory_contract",
    "temporal_contract",
    "initiative_contract",
    "coordination_contract",
    "orchestration_state",
}
BLOB_BOUND_ROLES = {"integration_registry", "workstream_compatibility"}


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs_no_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON value: {value}")
        ),
    )


def load_binding(path: Path = BINDING_PATH) -> dict[str, Any]:
    document = load_json_strict(path)
    if not isinstance(document, dict):
        raise ValueError("source binding document must be an object")
    return document


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def validate_repository_artifact(root: Path, relative: str) -> Path:
    """Require a case-exact regular non-symlink file below the repository root."""
    pure = PurePosixPath(relative)
    if (
        pure.is_absolute()
        or not pure.parts
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        raise ValueError(f"invalid binding path: {relative!r}")

    current = root.resolve()
    for index, part in enumerate(pure.parts):
        if current.is_symlink() or not current.is_dir():
            raise ValueError(f"binding path traverses an invalid parent: {relative!r}")
        entries = {entry.name: entry for entry in current.iterdir()}
        candidate = entries.get(part)
        if candidate is None:
            case_match = next(
                (name for name in entries if name.casefold() == part.casefold()),
                None,
            )
            if case_match is not None:
                raise ValueError(
                    f"binding path has case drift: {relative!r} "
                    f"(observed {case_match!r})"
                )
            raise ValueError(f"missing bound artifact: {relative!r}")
        if candidate.is_symlink():
            raise ValueError(f"bound artifact may not be a symlink: {relative!r}")
        current = candidate
        if index < len(pure.parts) - 1 and not current.is_dir():
            raise ValueError(f"binding parent is not a directory: {relative!r}")

    if not current.is_file():
        raise ValueError(f"bound artifact is not a regular file: {relative!r}")
    return current


def validate(document: dict[str, Any], root: Path = ROOT) -> None:
    root = root.resolve()
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
    if any(not isinstance(entry, dict) for entry in bindings):
        raise ValueError("every binding must be an object")

    roles = [entry.get("role") for entry in bindings]
    paths = [entry.get("path") for entry in bindings]
    if set(roles) != REQUIRED_ROLES or len(roles) != len(REQUIRED_ROLES):
        raise ValueError("binding roles differ from required exact set")
    if len(paths) != len(set(paths)) or any(
        not isinstance(path, str) or not path for path in paths
    ):
        raise ValueError("binding paths must be unique non-empty strings")

    by_role = {entry["role"]: entry for entry in bindings}
    for role, entry in by_role.items():
        artifact = validate_repository_artifact(root, entry["path"])
        declared_blob = entry.get("git_blob_sha")
        if role in BLOB_BOUND_ROLES and not isinstance(declared_blob, str):
            raise ValueError(f"{role} must declare a Git blob SHA")
        if declared_blob is not None and git_blob_sha(artifact) != declared_blob:
            raise ValueError(f"{role} Git blob SHA does not match bound bytes")

    registry = by_role["integration_registry"]
    registry_document = load_json_strict(root / registry["path"])
    actual_registry_sha256 = canonical_json_sha256(registry_document)
    if registry.get("canonical_sha256") != REGISTRY_SHA256:
        raise ValueError("registry canonical SHA-256 differs from release intent")
    if actual_registry_sha256 != registry.get("canonical_sha256"):
        raise ValueError("registry canonical SHA-256 does not match bound bytes")

    future = document.get("required_future_files")
    if future not in (None, []):
        raise ValueError(
            "completed replacement candidate cannot declare unresolved future files"
        )


def main() -> int:
    validate(load_binding())
    print(f"validated R6A1 source bindings at {SOURCE_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
