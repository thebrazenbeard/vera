from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_proof_artifact() -> dict[str, Any]:
    """Return the bounded fixture proof envelope used during staged transfer."""
    return {
        "artifact": "TUL Instrumented Host Fixture Proof",
        "fixture_version": "0.1.0",
        "transfer_state": "STAGED",
        "proof_classification": "UNAVAILABLE",
        "reason": "Full deterministic proof cases are not yet transferred.",
    }


def write_proof_artifact(path: Path) -> dict[str, Any]:
    artifact = build_proof_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact
