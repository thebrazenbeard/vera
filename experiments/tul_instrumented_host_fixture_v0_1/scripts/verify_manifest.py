#!/usr/bin/env python3
import hashlib
from pathlib import Path

EXPERIMENT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[3]
MANIFEST = EXPERIMENT / "SHA256SUMS.txt"

lines = MANIFEST.read_text(encoding="utf-8").splitlines()
failures = []
for line in lines:
    expected, rel = line.split("  ", 1)
    path = REPOSITORY / rel
    if not path.is_file():
        failures.append(f"missing: {rel}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        failures.append(f"mismatch: {rel}")

if failures:
    raise SystemExit("\n".join(failures))
print(f"verified {len(lines)} files")
