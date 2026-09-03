#!/usr/bin/env python3
import hashlib
import re
from pathlib import Path, PurePosixPath

EXPERIMENT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]
MANIFEST = EXPERIMENT / "SHA256SUMS.txt"
INCLUDE_ROOTS = (
    EXPERIMENT,
    REPOSITORY / "src" / "tul_fixture",
)
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def is_reproducible_source(path: Path) -> bool:
    relative_parts = path.relative_to(REPOSITORY).parts
    return (
        path.is_file()
        and not path.is_symlink()
        and path != MANIFEST
        and not any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_parts)
        and not any(part.endswith(".egg-info") for part in relative_parts)
        and not path.name.endswith((".pyc", ".pyo"))
    )


def expected_manifest_paths() -> set[str]:
    return {
        path.relative_to(REPOSITORY).as_posix()
        for root in INCLUDE_ROOTS
        for path in root.rglob("*")
        if is_reproducible_source(path)
    }


failures = []
entries: dict[str, str] = {}

for line_number, line in enumerate(
    MANIFEST.read_text(encoding="utf-8").splitlines(), start=1
):
    try:
        expected, rel = line.split("  ", 1)
    except ValueError:
        failures.append(f"malformed line {line_number}")
        continue

    if not SHA256_RE.fullmatch(expected):
        failures.append(f"invalid sha256 on line {line_number}")
        continue

    pure_rel = PurePosixPath(rel)
    if (
        not rel
        or pure_rel.is_absolute()
        or rel != pure_rel.as_posix()
        or any(part in {"", ".", ".."} for part in pure_rel.parts)
    ):
        failures.append(f"invalid path on line {line_number}: {rel!r}")
        continue
    if rel in entries:
        failures.append(f"duplicate entry: {rel}")
        continue

    path = REPOSITORY.joinpath(*pure_rel.parts)
    try:
        path.resolve().relative_to(REPOSITORY)
    except ValueError:
        failures.append(f"path escapes repository: {rel}")
        continue

    entries[rel] = expected

expected_paths = expected_manifest_paths()
manifest_paths = set(entries)
for rel in sorted(expected_paths - manifest_paths):
    failures.append(f"unlisted: {rel}")
for rel in sorted(manifest_paths - expected_paths):
    failures.append(f"out of scope: {rel}")

for rel, expected in sorted(entries.items()):
    path = REPOSITORY.joinpath(*PurePosixPath(rel).parts)
    if not path.is_file() or path.is_symlink():
        failures.append(f"missing or non-regular: {rel}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        failures.append(f"mismatch: {rel}")

if failures:
    raise SystemExit("\n".join(failures))
print(f"verified {len(entries)} files with complete boundary coverage")
