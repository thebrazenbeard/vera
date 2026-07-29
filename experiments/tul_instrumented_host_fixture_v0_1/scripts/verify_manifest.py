#!/usr/bin/env python3
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"
failures = []
for line in MANIFEST.read_text(encoding="utf-8").splitlines():
    expected, rel = line.split("  ", 1)
    path = ROOT / rel
    if not path.exists():
        failures.append(f"missing: {rel}")
        continue
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        failures.append(f"mismatch: {rel}")
if failures:
    raise SystemExit("\n".join(failures))
print(f"verified {len(MANIFEST.read_text(encoding='utf-8').splitlines())} files")
