#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMMAND = "VERA::INITIALIZE::PORTABLE_PROJECT_V1"
EXACT_COMMAND = COMMAND
STATES = ["UNISSUED", "CANDIDATE_UNPERSISTED", "BINDING_PENDING", "DURABLY_BOUND", "CONFLICTED", "UNKNOWN"]
PATHS = {
    ".github/workflows/portable-project-bootstrap.yml",
    "architecture/bootstrap/VERA_BOOTSTRAP_MANIFEST_V1.json",
    "architecture/bootstrap/VERA_NATIVE_PROJECT_INSTRUCTIONS_BOOTLOADER_V1.txt",
    "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json",
    "architecture/bootstrap/VERA_PORTABLE_SCAFFOLD_MANIFEST_V1.json",
    "docs/PORTABLE_PROJECT_BOOTSTRAP_V1.md",
    "schemas/vera_portable_project_bootstrap_v1.schema.json",
    "schemas/vera_portable_scaffold_manifest_v1.schema.json",
    "scripts/validate_portable_project_bootstrap.py",
    "supabase/migrations/20260731142200_create_vera_portable_bootstrap_registry_v1.sql",
    "supabase/tests/validate_portable_bootstrap_registry_v1.sql",
    "tests/test_portable_project_bootstrap.py",
}

class ValidationError(RuntimeError):
    pass

def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def reject_constant(value: str) -> None:
    raise ValidationError(f"non-finite JSON value: {value}")

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object, parse_constant=reject_constant)

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(root: Path) -> None:
    manifest = load_json(root / "architecture/bootstrap/VERA_BOOTSTRAP_MANIFEST_V1.json")
    contract = load_json(root / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
    scaffold = load_json(root / "architecture/bootstrap/VERA_PORTABLE_SCAFFOLD_MANIFEST_V1.json")
    boot_path = root / manifest["native_bootloader"]["repository_path"]
    raw = boot_path.read_bytes()
    require(b"\r" not in raw, "bootloader must use LF")
    try:
        boot = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError("bootloader must be ASCII") from exc
    require(len(boot) <= 7600, "bootloader exceeds 7600 characters")
    require(boot.count(COMMAND) == 1, "bootloader must contain one canonical command")
    require(manifest["native_bootloader"]["sha256"] == digest(boot_path), "bootloader digest mismatch")
    require(manifest["exact_initialize_command"] == COMMAND, "manifest command drift")
    require(contract["command"]["exact"] == COMMAND, "contract command drift")
    require(contract["project_instance_states"] == STATES, "project state vocabulary drift")
    require(contract["authority_contract"]["project_architect_is_implementation_owner"] is True, "implementation owner drift")
    require(contract["authority_contract"]["coordinator_can_issue_or_expand_lease"] is False, "Coordinator authority leakage")
    require(contract["authority_contract"]["github_repo_is_support_and_review"] is True, "GitHub Repo role drift")
    require(contract["scaffold_contract"]["candidate_granularity"] == "ONE_COMPLETE_ATOMIC_REPOSITORY_TRANSACTION", "atomic candidate drift")
    require(contract["scaffold_contract"]["sequential_fallback_allowed"] is False, "sequential fallback forbidden")
    require("BASIC_MEMORY" in contract["capability_policy"]["optional_nonblocking"], "Basic Memory must remain optional")
    require(manifest["archive_policy"]["active_project_bundle_member"] is False, "archive entered active bundle")
    require(manifest["archive_policy"]["canonical_memory_eligible"] is False, "archive became canonical memory")
    require(re.fullmatch(r"[0-9a-f]{40}", manifest["source_binding"]["source_commit"]) is not None, "invalid source commit")
    paths = [item["path"] for item in scaffold["files"]]
    require(set(paths) == PATHS and len(paths) == len(PATHS), "scaffold path set differs from lease")
    require(scaffold["write_policy"]["implementation_owner"] == "workstream/project-architecture", "scaffold owner drift")
    require(scaffold["write_policy"]["sequential_fallback_allowed"] is False, "scaffold sequential fallback forbidden")
    for path in paths:
        require(not path.startswith("/") and ".." not in Path(path).parts, f"unsafe path: {path}")
    for rel in ("schemas/vera_portable_project_bootstrap_v1.schema.json", "schemas/vera_portable_scaffold_manifest_v1.schema.json"):
        schema = load_json(root / rel)
        require(schema["$schema"].endswith("2020-12/schema"), f"wrong schema draft: {rel}")
        require(schema["additionalProperties"] is False, f"unknown top-level fields allowed: {rel}")
    sql = (root / "supabase/migrations/20260731142200_create_vera_portable_bootstrap_registry_v1.sql").read_text(encoding="utf-8")
    for token in ("vera_portable_bootstrap_requests", "vera_portable_bootstrap_events", "claim_vera_portable_bootstrap_request", "append_vera_portable_bootstrap_event", "REQUEST_ID_REUSE_CONFLICT", "STALE_OR_CONFLICTING_PREDECESSOR", "enable row level security", "append-only"):
        require(token in sql, f"migration missing {token}")
    lowered = sql.lower()
    require("chatgpt-project-current" not in lowered and "vera-chatgpt-instance" not in lowered, "legacy fixed alias leaked into registry")
    require("grant " not in lowered, "migration must not grant runtime access")

def main(argv: list[str] | None = None) -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    ROOT = parser.parse_args(argv).root.resolve()
    validate(ROOT)
    print("portable-project-bootstrap-v1: PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        print(f"portable-project-bootstrap-v1: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
