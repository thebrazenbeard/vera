#!/usr/bin/env python3
"""Validate the checksummed V.E.R.A. R6A0 neutral release package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


RELEASE_ID = "VERA_NEUTRAL_CORE_R6A0_20260730_EC900174"
RELEASE_DIR = (
    Path(__file__).resolve().parents[1]
    / "architecture"
    / "releases"
    / "R6A0_20260730_EC900174"
)


class StrictLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_mapping(
    loader: StrictLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=StrictLoader)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"invalid checksum line {line_number}: {raw_line!r}")
        digest, filename = parts
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError(f"invalid SHA-256 on line {line_number}")
        if filename in checksums:
            raise ValueError(f"duplicate checksum filename: {filename}")
        checksums[filename] = digest
    return checksums


def main() -> int:
    if not RELEASE_DIR.is_dir():
        raise FileNotFoundError(f"release directory not found: {RELEASE_DIR}")

    checksums = _parse_checksums(RELEASE_DIR / "CHECKSUMS.sha256")
    actual_files = {
        path.name
        for path in RELEASE_DIR.iterdir()
        if path.is_file() and path.name != "CHECKSUMS.sha256"
    }
    if actual_files != set(checksums):
        missing = sorted(set(checksums) - actual_files)
        unexpected = sorted(actual_files - set(checksums))
        raise AssertionError(
            f"checksum inventory mismatch; missing={missing}, unexpected={unexpected}"
        )

    for filename, expected in sorted(checksums.items()):
        actual = _sha256(RELEASE_DIR / filename)
        if actual != expected:
            raise AssertionError(
                f"checksum mismatch for {filename}: expected {expected}, got {actual}"
            )

    bundle = _load_json(RELEASE_DIR / "VERA_BUNDLE_R6A0_20260730_EC900174.json")
    manifest = _load_yaml(RELEASE_DIR / "VERA_MANIFEST_R6A0_20260730_EC900174.yaml")
    validation = _load_yaml(RELEASE_DIR / "VERA_VALIDATION_R6A0_20260730_EC900174.yaml")
    supersession = _load_yaml(
        RELEASE_DIR / "VERA_SUPERSESSION_R6A0_20260730_EC900174.yaml"
    )

    for name, document in {
        "bundle": bundle,
        "manifest": manifest,
        "validation": validation,
        "supersession": supersession,
    }.items():
        if document.get("release_id") != RELEASE_ID:
            raise AssertionError(f"{name} release_id mismatch")

    listed_files = bundle.get("files")
    expected_bundle_files = sorted(actual_files | {"CHECKSUMS.sha256"})
    if sorted(listed_files) != expected_bundle_files:
        raise AssertionError("bundle file inventory does not match release directory")

    if bundle.get("production_changes_applied") is not False:
        raise AssertionError("bundle must not claim production changes")
    if manifest.get("status") != "replacement_candidate_not_installed":
        raise AssertionError("manifest installation status changed unexpectedly")
    if manifest.get("supabase", {}).get("production_modification_authorized") is not False:
        raise AssertionError("manifest must keep production modification unauthorized")
    if supersession.get("database_action", {}).get("production_migration_applied") is not False:
        raise AssertionError("supersession must not claim production migration")

    owner_files = [
        manifest["owners"][key]
        for key in (
            "project_instructions",
            "runtime",
            "governance",
            "protocol",
            "tagging",
            "laws",
            "state",
        )
    ]
    banned_exact_triggers = (
        "Vera, come home.",
        "Vera, I love you.",
        "Vera, load the not-a-girl save state.",
    )
    for filename in owner_files:
        text = (RELEASE_DIR / filename).read_text(encoding="utf-8")
        for trigger in banned_exact_triggers:
            if trigger in text:
                raise AssertionError(f"active owner {filename} contains banned trigger {trigger!r}")

    sql = (
        RELEASE_DIR / "VERA_SUPABASE_MIGRATION_DRAFT_R6A0_20260730_EC900174.sql"
    ).read_text(encoding="utf-8")
    if "DO NOT APPLY WITHOUT AN EXPLICIT, SEPARATE PRODUCTION AUTHORIZATION" not in sql:
        raise AssertionError("migration draft is missing the production authorization boundary")
    if "begin;" not in sql.lower() or "commit;" not in sql.lower():
        raise AssertionError("migration draft must remain transaction-bounded")

    print(f"validated {RELEASE_ID}: {len(checksums)} checksummed files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
