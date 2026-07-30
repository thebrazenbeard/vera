from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_proof_artifact() -> dict[str, Any]:
    """Build the deterministic fixture proof artifact."""
    raise NotImplementedError("proof builder staged for repository transfer")


def write_proof_artifact(path: Path) -> dict[str, Any]:
    artifact = build_proof_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact
