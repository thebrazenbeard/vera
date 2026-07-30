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

files = sorted(
    path
    for root in INCLUDE_ROOTS
    for path in root.rglob("*")
    if path.is_file()
    and path != MANIFEST
    and "__pycache__" not in path.parts
    and not path.name.endswith(".pyc")
)

lines = []
for path in files:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(REPOSITORY).as_posix()}")

MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(MANIFEST)
