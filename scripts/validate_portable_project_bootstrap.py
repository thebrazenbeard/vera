#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
COMMAND = "VERA::INITIALIZE::PORTABLE_PROJECT_V1"
BASE_SHA = "fc761beab263f2fab010cde2fab424b2b8358bb7"
SELF_EXCLUDED_PATH = "architecture/bootstrap/VERA_PORTABLE_SCAFFOLD_MANIFEST_V1.json"
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
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=reject_constant,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def schema_errors(schema: dict[str, Any], instance: Any) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [error.message for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.path))]


def validate_schema_instance(schema: dict[str, Any], instance: Any, label: str) -> None:
    errors = schema_errors(schema, instance)
    if errors:
        raise ValidationError(f"{label} schema failure: {'; '.join(errors[:5])}")


def receipt_schema(root_schema: dict[str, Any]) -> dict[str, Any]:
    schema = copy.deepcopy(root_schema["$defs"]["receipt"])
    schema["$schema"] = root_schema["$schema"]
    schema["$defs"] = copy.deepcopy(root_schema["$defs"])
    return schema


def validate_receipt(receipt: dict[str, Any], root_schema: dict[str, Any]) -> None:
    validate_schema_instance(receipt_schema(root_schema), receipt, "receipt")
    result = receipt["result"]
    binding_state = receipt["project_scope"]["binding_state"]
    readback = receipt["durable_readback"]
    if binding_state == "DURABLY_BOUND":
        require(readback["confirmed"] is True, "durable binding requires confirmed exact read-back")
        require(readback["project_instance_id"] == receipt["project_scope"]["project_instance_id"], "read-back project instance mismatch")
        require(readback["request_key"] == receipt["request"]["request_key"], "read-back request key mismatch")
        require(readback["input_digest"] == receipt["request"]["input_digest"], "read-back input digest mismatch")
    if result == "INITIALIZED":
        require(binding_state == "DURABLY_BOUND", "INITIALIZED requires DURABLY_BOUND")
        require(any(effect["confirmed"] for effect in receipt["effects"]), "INITIALIZED requires a confirmed effect")
    for effect in receipt["effects"]:
        if effect["confirmed"]:
            require(effect["confirmation_locator"], "confirmed effect requires independent locator")
            require(effect["authority_reference"], "confirmed effect requires authority reference")


def git(*args: str, root: Path, input: bytes | None = None) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=root, stderr=subprocess.STDOUT, input=input)
    except subprocess.CalledProcessError as exc:
        raise ValidationError(f"git {' '.join(args)} failed: {exc.output.decode(errors='replace').strip()}") from exc


def git_blob_sha(value: bytes, root: Path) -> str:
    return git("hash-object", "--stdin", root=root, input=value).decode().strip()  # type: ignore[call-arg]


def external_release_attestation(root: Path, release_commit: str) -> dict[str, Any]:
    require(re.fullmatch(r"[0-9a-f]{40}", release_commit) is not None, "invalid release commit")
    resolved = git("rev-parse", f"{release_commit}^{{commit}}", root=root).decode().strip()
    require(resolved == release_commit, "release commit did not resolve exactly")
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE_SHA, release_commit], cwd=root, check=True)
    files: list[dict[str, Any]] = []
    for path in sorted(PATHS):
        line = git("ls-tree", release_commit, "--", path, root=root).decode().strip()
        require(bool(line), f"release commit missing {path}")
        left, listed_path = line.split("\t", 1)
        mode, kind, blob_sha = left.split()
        require(kind == "blob" and listed_path == path, f"unexpected tree entry for {path}")
        committed = git("show", f"{release_commit}:{path}", root=root)
        working = (root / path).read_bytes()
        require(committed == working, f"working bytes differ from release commit: {path}")
        computed_blob = git("hash-object", "--stdin", root=root, input=committed).decode().strip()  # type: ignore[call-arg]
        require(computed_blob == blob_sha, f"Git blob identity mismatch: {path}")
        files.append(
            {
                "path": path,
                "mode": mode,
                "size": len(committed),
                "sha256": sha256_bytes(committed),
                "git_blob_sha": blob_sha,
                "release_commit": release_commit,
            }
        )
    path_set = sha256_bytes(("\n".join(sorted(PATHS)) + "\n").encode("ascii"))
    package_sha = sha256_bytes(canonical_json(files))
    return {
        "release_commit": release_commit,
        "base_source_commit": BASE_SHA,
        "path_set_sha256": path_set,
        "package_sha256": package_sha,
        "files": files,
    }


def validate_sql(root: Path) -> None:
    sql = (root / "supabase/migrations/20260731142200_create_vera_portable_bootstrap_registry_v1.sql").read_text(encoding="utf-8")
    lowered = sql.lower()
    required = (
        "vera_generate_uuid_v7",
        "vera_valid_temporal_point",
        "vera_valid_temporal_evidence",
        "vera_valid_authority_evidence",
        "vera_valid_source_evidence",
        "vera_portable_bootstrap_bindings",
        "request_id_reuse_conflict",
        "prior_state_mismatch",
        "illegal_bootstrap_transition",
        "verifier_evidence_required",
        "unverified_binding_cannot_commit",
        "read_vera_portable_bootstrap_binding",
        "durably_bound",
        "enable row level security",
        "portable bootstrap registry is append-only",
    )
    for token in required:
        require(token in lowered, f"migration missing semantic guard: {token}")
    claim_match = re.search(
        r"create function public\.claim_vera_portable_bootstrap_request\s*\((.*?)\)\s*returns",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    require(claim_match is not None, "claim function signature missing")
    claim_args = claim_match.group(1).lower()
    for forbidden in ("p_request_key", "p_input_digest", "p_project_instance_id", "p_initial_state"):
        require(forbidden not in claim_args, f"caller-controlled identity leaked into claim function: {forbidden}")
    requests_match = re.search(
        r"create table public\.vera_portable_bootstrap_requests\s*\((.*?)\);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    require(requests_match is not None, "request table missing")
    request_columns = requests_match.group(1).lower()
    require("initial_state" not in request_columns, "attempt-local state persisted in request table")
    view_match = re.search(
        r"create view public\.vera_portable_bootstrap_current.*?as\s*(.*?);",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    require(view_match is not None, "durable current view missing")
    view_body = view_match.group(1).lower()
    require("vera_portable_bootstrap_bindings" in view_body, "durable view not bound to committed bindings")
    require("binding_pending" not in view_body and "candidate_unpersisted" not in view_body, "pending state leaked into durable view")
    require("grant " not in lowered, "migration must not grant runtime access")
    require("chatgpt-project-current" not in lowered and "vera-chatgpt-instance" not in lowered, "legacy fixed alias leaked into registry")


def validate_workflow(root: Path) -> None:
    workflow = (root / ".github/workflows/portable-project-bootstrap.yml").read_text(encoding="utf-8")
    required = (
        "github.event.pull_request.head.sha || github.sha",
        "fetch-depth: 0",
        "--require-release-binding",
        "Stage unrelated repository migrations aside",
        "mv supabase/migrations /tmp/vera_repository_migrations",
        "mkdir -p supabase/migrations",
        "Apply only the standalone bootstrap registry migration",
        "/tmp/vera_repository_migrations/20260731142200_create_vera_portable_bootstrap_registry_v1.sql",
        "Probe concurrent identical and conflicting claims",
        "It does not prove replay of every historical migration or production application.",
    )
    for token in required:
        require(token in workflow, f"workflow missing exact-head or isolated-CI guard: {token}")
    require(workflow.index("mv supabase/migrations") < workflow.index("supabase start"), "legacy migrations are staged too late")


def validate(root: Path, release_commit: str | None = None, require_release_binding: bool = False) -> dict[str, Any] | None:
    manifest_path = root / "architecture/bootstrap/VERA_BOOTSTRAP_MANIFEST_V1.json"
    contract_path = root / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json"
    scaffold_path = root / "architecture/bootstrap/VERA_PORTABLE_SCAFFOLD_MANIFEST_V1.json"
    bootstrap_schema_path = root / "schemas/vera_portable_project_bootstrap_v1.schema.json"
    scaffold_schema_path = root / "schemas/vera_portable_scaffold_manifest_v1.schema.json"

    manifest = load_json(manifest_path)
    contract = load_json(contract_path)
    scaffold = load_json(scaffold_path)
    bootstrap_schema = load_json(bootstrap_schema_path)
    scaffold_schema = load_json(scaffold_schema_path)

    validate_schema_instance(bootstrap_schema, contract, "bootstrap contract")
    validate_schema_instance(scaffold_schema, scaffold, "scaffold manifest")

    boot_path = root / manifest["native_bootloader"]["repository_path"]
    raw = boot_path.read_bytes()
    require(b"\r" not in raw, "bootloader must use LF")
    try:
        boot = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValidationError("bootloader must be ASCII") from exc
    require(len(boot) <= 7600, "bootloader exceeds 7600 characters")
    require(boot.count(COMMAND) == 1, "bootloader must contain exactly one canonical command")
    require(manifest["native_bootloader"]["sha256"] == sha256_bytes(raw), "bootloader digest mismatch")
    require(manifest["exact_initialize_command"] == COMMAND, "manifest command drift")
    require(manifest["source_binding"]["base_source_commit"] == BASE_SHA, "base source drift")
    release_policy = manifest["source_binding"]["portable_release_evidence"]
    require(release_policy["resolution"] == "EXTERNAL_EXACT_HEAD_ATTESTATION_REQUIRED", "release evidence became self-asserted")
    require(release_policy["embedded_release_commit"] is False, "self-referential release commit embedded")
    require(release_policy["path_set_sha256"] == sha256_bytes(("\n".join(sorted(PATHS)) + "\n").encode("ascii")), "manifest path-set digest drift")
    require(manifest["archive_policy"]["active_project_bundle_member"] is False, "archive entered active bundle")
    require(manifest["archive_policy"]["canonical_memory_eligible"] is False, "archive became canonical memory")

    entries = scaffold["files"]
    require(len(entries) == len(PATHS), "scaffold path count drift")
    entry_paths = [entry["path"] for entry in entries]
    require(len(set(entry_paths)) == len(entry_paths) and set(entry_paths) == PATHS, "scaffold path set differs from lease")
    require(scaffold["path_set_sha256"] == sha256_bytes(("\n".join(sorted(PATHS)) + "\n").encode("ascii")), "scaffold path-set digest mismatch")
    non_self_bindings: list[dict[str, Any]] = []
    for entry in entries:
        path = entry["path"]
        require(not path.startswith("/") and ".." not in Path(path).parts, f"unsafe path: {path}")
        binding = entry["binding"]
        if path == SELF_EXCLUDED_PATH:
            require(binding["self_excluded"] is True, "scaffold manifest must be self-excluded")
            require(binding["embedded_size"] is None and binding["embedded_sha256"] is None, "self-excluded binding must be null")
        else:
            require(binding["self_excluded"] is False, f"unexpected self-exclusion: {path}")
            data = (root / path).read_bytes()
            require(binding["embedded_size"] == len(data), f"embedded size mismatch: {path}")
            require(binding["embedded_sha256"] == sha256_bytes(data), f"embedded digest mismatch: {path}")
            non_self_bindings.append(
                {"path": path, "mode": entry["mode"], "size": len(data), "sha256": sha256_bytes(data)}
            )
        require(binding["external_git_blob_required"] is True, f"external Git binding not required: {path}")
    require(scaffold["embedded_package_sha256"] == sha256_bytes(canonical_json(non_self_bindings)), "embedded package digest mismatch")

    validate_sql(root)
    validate_workflow(root)

    attestation = None
    if release_commit is not None:
        attestation = external_release_attestation(root, release_commit)
        require(attestation["path_set_sha256"] == scaffold["path_set_sha256"], "external path-set digest mismatch")
    elif require_release_binding:
        raise ValidationError("exact release binding is required but no release commit was provided")

    return attestation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--release-commit")
    parser.add_argument("--require-release-binding", action="store_true")
    args = parser.parse_args(argv)
    attestation = validate(args.root.resolve(), args.release_commit, args.require_release_binding)
    print("portable-project-bootstrap-v1: PASS")
    if attestation:
        print(json.dumps(attestation, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        print(f"portable-project-bootstrap-v1: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
