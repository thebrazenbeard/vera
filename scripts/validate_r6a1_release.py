#!/usr/bin/env python3
"""Validate the complete V.E.R.A. governed-core R6A1 replacement candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "R6A1_20260731_B20E7309"
RELEASE_ID = "VERA_GOVERNED_CORE_R6A1_20260731_B20E7309"
SOURCE_COMMIT = "b20e7309c6ded3c358dce00baa537d2fc1880004"
RELEASE_STATUS = "REPLACEMENT_CANDIDATE_NOT_INSTALLED"
RELEASE_DIR = ROOT / "architecture" / "releases" / TOKEN
SUPABASE_SNAPSHOT_TIME = "2026-07-31T12:37:13.625307Z"
SUPABASE_MAX_SEQUENCE = "351"
MAIN_ASSURANCE_RUN = "30629869594"


class StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: StrictLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_json_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON value: {value}")
        ),
    )


def load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"invalid checksum line {line_number}")
        digest, name = parts
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"invalid checksum digest line {line_number}")
        if name in result:
            raise ValueError(f"duplicate checksum filename: {name}")
        result[name] = digest
    return result


def _require_text(text: str, needle: str, message: str) -> None:
    if needle not in text:
        raise ValueError(message)


def validate(root: Path = ROOT) -> None:
    release_dir = root / "architecture" / "releases" / TOKEN
    if not release_dir.is_dir():
        raise ValueError("release directory missing")

    checks = parse_checksums(release_dir / "CHECKSUMS.sha256")
    actual = {
        path.name
        for path in release_dir.iterdir()
        if path.is_file() and path.name != "CHECKSUMS.sha256"
    }
    if actual != set(checks):
        raise ValueError("checksum inventory mismatch")
    for name, digest in checks.items():
        if sha(release_dir / name) != digest:
            raise ValueError(f"checksum mismatch: {name}")

    bundle = load_json(release_dir / f"VERA_BUNDLE_{TOKEN}.json")
    manifest = load_yaml(release_dir / f"VERA_MANIFEST_{TOKEN}.yaml")
    validation = load_yaml(release_dir / f"VERA_VALIDATION_{TOKEN}.yaml")
    supersession = load_yaml(release_dir / f"VERA_SUPERSESSION_{TOKEN}.yaml")
    bindings = load_json(release_dir / f"VERA_SOURCE_BINDINGS_{TOKEN}.json")

    for label, document in {
        "bundle": bundle,
        "manifest": manifest,
        "validation": validation,
        "supersession": supersession,
        "bindings": bindings,
    }.items():
        if document.get("release_id") != RELEASE_ID:
            raise ValueError(f"{label} release_id mismatch")

    if manifest.get("status") != RELEASE_STATUS:
        raise ValueError("manifest status mismatch")
    if bindings.get("release_status") != RELEASE_STATUS:
        raise ValueError("bindings status mismatch")
    if manifest.get("source", {}).get("commit") != SOURCE_COMMIT:
        raise ValueError("manifest source commit mismatch")
    if bindings.get("source_commit") != SOURCE_COMMIT:
        raise ValueError("bindings source commit mismatch")
    if bindings.get("authority_provenance") != "UNVERIFIED_PROVENANCE":
        raise ValueError("authority provenance was promoted")
    if bundle.get("files") != sorted(actual | {"CHECKSUMS.sha256"}):
        raise ValueError("bundle inventory mismatch")

    for document, fields in [
        (
            bundle,
            [
                "production_changes_applied",
                "canonical_memory_writes_applied",
                "runtime_deployed",
                "project_files_replaced",
            ],
        ),
        (
            bindings,
            [
                "production_modification_authorized",
                "canonical_memory_write_authorized",
                "runtime_deployment_authorized",
                "project_file_replacement_authorized",
            ],
        ),
    ]:
        for field in fields:
            if document.get(field) is not False:
                raise ValueError(f"{field} must remain false")

    installation = manifest.get("installation", {})
    if installation.get("authorized") is not False or installation.get("performed") is not False:
        raise ValueError("installation boundary changed")
    if supersession.get("database_action", {}).get("production_migration_applied") is not False:
        raise ValueError("production migration boundary changed")
    if supersession.get("repository_action", {}).get("history_rewrite_authorized") is not False:
        raise ValueError("history rewrite boundary changed")

    owners = manifest.get("owners", {})
    required_owners = {
        "project_instructions",
        "runtime",
        "governance",
        "protocol",
        "tagging",
        "laws",
        "state",
        "validation",
        "supersession",
        "supabase_plan",
        "source_bindings",
        "installation_rollback",
    }
    if set(owners) != required_owners:
        raise ValueError("owner set mismatch")
    owner_files = list(owners.values())
    if len(owner_files) != len(set(owner_files)):
        raise ValueError("manifest owner filenames are duplicated")
    for filename in owner_files:
        if not (release_dir / filename).is_file():
            raise ValueError(f"missing owner file: {filename}")

    replacement_owners = supersession.get("replacement_owners")
    if not isinstance(replacement_owners, list) or len(replacement_owners) != len(
        set(replacement_owners)
    ):
        raise ValueError("supersession replacement owner inventory is invalid")
    if set(replacement_owners) != set(owner_files):
        raise ValueError("manifest and supersession owner inventories differ")

    owner_text = "\n".join(
        (release_dir / owners[key]).read_text(encoding="utf-8")
        for key in [
            "project_instructions",
            "runtime",
            "governance",
            "protocol",
            "tagging",
            "laws",
            "state",
        ]
    )
    for banned in [
        "Vera, come home.",
        "Vera, I love you.",
        "load the not-a-girl save state",
    ]:
        if banned in owner_text:
            raise ValueError(f"banned active trigger: {banned}")

    if "VERA-LAW-018" not in (release_dir / owners["laws"]).read_text(encoding="utf-8"):
        raise ValueError("governed workflow law missing")
    if "Governed workflow continuity" not in (
        release_dir / owners["project_instructions"]
    ).read_text(encoding="utf-8"):
        raise ValueError("workflow continuity instructions missing")
    if "UNVERIFIED_PROVENANCE" not in (
        release_dir / owners["governance"]
    ).read_text(encoding="utf-8"):
        raise ValueError("authority provenance governance missing")

    install_text = (release_dir / owners["installation_rollback"]).read_text(
        encoding="utf-8"
    )
    if "does not authorize installation" not in install_text or "## Rollback" not in install_text:
        raise ValueError("installation rollback boundary missing")

    roles = {entry.get("role") for entry in bindings.get("bindings", [])}
    for role in [
        "integration_registry",
        "workstream_compatibility",
        "turn_taking",
        "memory_contract",
        "temporal_contract",
        "initiative_contract",
        "coordination_contract",
    ]:
        if role not in roles:
            raise ValueError(f"missing source binding: {role}")
    registry = next(
        entry for entry in bindings["bindings"] if entry["role"] == "integration_registry"
    )
    if registry.get("canonical_sha256") != "f095fa46666abb583e616658198399131a4902fc9ba572f01f4642c1dcab158f":
        raise ValueError("registry digest mismatch")

    state_text = (release_dir / owners["state"]).read_text(encoding="utf-8")
    supabase_text = (release_dir / owners["supabase_plan"]).read_text(encoding="utf-8")
    audit_path = root / "docs" / "MAIN_MERGE_AUTHORITY_AUDIT_20260731.md"
    if not audit_path.is_file():
        raise ValueError("main merge authority audit missing")
    audit_text = audit_path.read_text(encoding="utf-8")

    _require_text(supabase_text, "## Observed snapshot", "Supabase snapshot heading missing")
    _require_text(
        supabase_text,
        SUPABASE_SNAPSHOT_TIME,
        "Supabase snapshot timestamp mismatch",
    )
    _require_text(
        supabase_text,
        "maximum coordination sequence observed: `351`",
        "Supabase maximum coordination sequence mismatch",
    )
    _require_text(
        supabase_text,
        "`public.vera_coordination_events`: 329 append-only rows",
        "Supabase coordination count mismatch",
    )
    _require_text(
        supabase_text,
        "`public.vera_coordination_latest`: 57 current coordination threads",
        "Supabase current-thread count mismatch",
    )
    _require_text(
        supabase_text,
        "`public.vera_coordination_open_issues`: 16 current open issues",
        "Supabase open-issue count mismatch",
    )
    if "The accompanying SQL file" in supabase_text:
        raise ValueError("Supabase plan claims a nonexistent accompanying SQL file")

    _require_text(state_text, MAIN_ASSURANCE_RUN, "exact-main Integration Assurance missing from state")
    _require_text(
        state_text,
        "through sequence `351`",
        "state authority audit sequence is stale",
    )
    _require_text(state_text, SUPABASE_SNAPSHOT_TIME, "state Supabase snapshot timestamp mismatch")
    _require_text(audit_text, MAIN_ASSURANCE_RUN, "exact-main Integration Assurance missing from audit")
    _require_text(
        audit_text,
        "through sequence `351`",
        "main merge authority audit sequence is stale",
    )
    _require_text(
        audit_text,
        "merge-authority provenance: `UNVERIFIED_PROVENANCE`",
        "main merge authority classification changed",
    )


def main() -> int:
    validate()
    print(f"validated {RELEASE_ID}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
