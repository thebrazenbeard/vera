#!/usr/bin/env python3
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"
EXCLUDE = {MANIFEST}

files = sorted(
    path for path in ROOT.rglob("*")
    if path.is_file()
    and path not in EXCLUDE
    and "__pycache__" not in path.parts
    and not path.name.endswith(".pyc")
)
lines = []
for path in files:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(MANIFEST)
