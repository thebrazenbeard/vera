#!/usr/bin/env python3
import hashlib
from pathlib import Path

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


files = sorted(
    path
    for root in INCLUDE_ROOTS
    for path in root.rglob("*")
    if is_reproducible_source(path)
)

lines = []
for path in files:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(REPOSITORY).as_posix()}")

MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(MANIFEST)
