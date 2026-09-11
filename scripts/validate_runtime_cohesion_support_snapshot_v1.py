#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
RECEIPT_PATH = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"
EXPECTED_SEMANTICS = "GIT_TREE_CONTAINS_EXACT_OPERATIONAL_SUPPORT_PATH_BLOBS"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def validate_snapshot_validator_binding(root: Path, receipt: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    binding = receipt.get("operational_support_snapshot_validator")
    if not isinstance(binding, Mapping):
        return ["pair receipt operational_support_snapshot_validator binding is required"]
    relative_path = binding.get("path")
    path_error = _validate_relative_path(relative_path)
    if path_error:
        return [f"snapshot validator {path_error}"]
    if relative_path != "scripts/validate_runtime_cohesion_support_snapshot_v1.py":
        errors.append("snapshot validator path drift")
        return errors
    expected_blob = binding.get("blob_sha")
    if not _valid_git_sha(expected_blob):
        errors.append("snapshot validator requires exact lowercase Git blob SHA")
        return errors
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append("snapshot validator path escapes repository root")
        return errors
    if not candidate.is_file():
        errors.append("snapshot validator path does not resolve to a file")
        return errors
    observed_blob = _git_blob_sha(candidate)
    if observed_blob != expected_blob:
        errors.append(
            f"snapshot validator blob mismatch: receipt={expected_blob} observed={observed_blob}"
        )
    return errors


def _valid_git_sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(char in "0123456789abcdef" for char in value)
    )


def _validate_relative_path(relative_path: Any) -> str | None:
    if not isinstance(relative_path, str) or not relative_path.strip():
        return "requires non-empty path"
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        return f"path escapes repository root: {relative_path!r}"
    return None


def _git_tree_blob_sha(root: Path, source_commit: str, relative_path: str) -> tuple[str | None, str | None]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-tree", source_commit, "--", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        return None, (
            f"operational support source_commit tree unavailable for {source_commit}: "
            f"{process.stderr.strip() or 'git ls-tree failed'}"
        )
    rows = [row for row in process.stdout.splitlines() if row.strip()]
    if len(rows) != 1:
        return None, (
            f"operational support source_commit tree must resolve exactly one object "
            f"for {relative_path}"
        )
    header, sep, observed_path = rows[0].partition("\t")
    if not sep or observed_path != relative_path:
        return None, f"operational support source_commit tree path mismatch for {relative_path}"
    fields = header.split()
    if len(fields) != 3 or fields[1] != "blob":
        return None, f"operational support source_commit tree object must be a blob for {relative_path}"
    observed_blob = fields[2]
    if not _valid_git_sha(observed_blob):
        return None, f"operational support source_commit tree returned invalid blob SHA for {relative_path}"
    return observed_blob, None


def validate_operational_support_snapshot(
    root: Path,
    receipt: Mapping[str, Any],
) -> list[str]:
    """Bind the non-normative operational support set to one immutable Git tree."""
    errors: list[str] = []

    source_commit = receipt.get("operational_support_source_commit")
    if not _valid_git_sha(source_commit):
        errors.append("pair receipt operational_support_source_commit must be an exact lowercase Git SHA")
        return errors
    if receipt.get("operational_support_source_commit_semantics") != EXPECTED_SEMANTICS:
        errors.append(
            "pair receipt operational_support_source_commit_semantics must explicitly bind "
            "all support path/blob pairs to one Git tree"
        )

    support = receipt.get("operational_support")
    if not isinstance(support, Mapping):
        errors.append("pair receipt operational support mapping is required")
        return errors
    if support.get("normative_status") != "NON_NORMATIVE_OPERATIONAL_SUPPORT":
        errors.append("pair receipt operational support must remain NON_NORMATIVE_OPERATIONAL_SUPPORT")

    rows = [(name, row) for name, row in support.items() if name != "normative_status"]
    if not rows:
        errors.append("pair receipt operational support requires at least one bound support object")
        return errors

    for name, row in rows:
        if not isinstance(name, str) or not name:
            errors.append("operational support entry requires a non-empty name")
            continue
        if not isinstance(row, Mapping):
            errors.append(f"operational support {name!r} must be an object")
            continue

        relative_path = row.get("path")
        path_error = _validate_relative_path(relative_path)
        if path_error:
            errors.append(f"operational support {name!r} {path_error}")
            continue

        blob_sha = row.get("blob_sha")
        if not _valid_git_sha(blob_sha):
            errors.append(f"operational support {name!r} requires exact lowercase Git blob SHA")
            continue

        observed_blob, tree_error = _git_tree_blob_sha(root, source_commit, relative_path)
        if tree_error:
            errors.append(f"operational support {name!r}: {tree_error}")
            continue
        if observed_blob != blob_sha:
            errors.append(
                f"operational support {name!r} snapshot blob mismatch: "
                f"receipt={blob_sha} observed={observed_blob} path={relative_path} "
                f"source_commit={source_commit}"
            )

    return errors


def main() -> int:
    receipt = load(RECEIPT_PATH)
    errors = [
        *validate_snapshot_validator_binding(ROOT, receipt),
        *validate_operational_support_snapshot(ROOT, receipt),
    ]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("VERA_COHESION_PAIR_RECEIPT_V1 operational support snapshot: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
