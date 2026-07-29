#!/usr/bin/env python3
from pathlib import Path

from tul_fixture.proof import write_proof_artifact

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "proof" / "tul_instrumented_host_fixture_proof_v0_1.json"
write_proof_artifact(OUTPUT)
print(OUTPUT)
