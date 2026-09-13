from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "architecture" / "VERA_PREDECESSOR_PROVIDER_OBJECT_DISPOSITION_20260912.json"
EXPECTED_DIGEST = "05c9deb50dff86b63c3afde0aec5ee477a2fea855b8c1e097f67c62d6422c48a"


def test_classification_preimage_procedure_is_bound() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    binding = manifest["classification_reproducibility"]
    procedure = ROOT / binding["procedure_path"]
    assert procedure.exists()
    assert binding["procedure_git_blob"] == "5fdf4283a3f979584951ee6dd4184666af2ad2d5"
    assert binding["procedure_sha256"] == "8bdbaa8ca8cc7b6b678f1579ffe379baceef85e4cacd536c5a2de850e7a141e7"
    assert binding["verified_object_count"] == 298
    assert binding["verified_unknown_count"] == 0
    assert binding["verified_preimage_sha256"] == EXPECTED_DIGEST
    assert manifest["inventory_cut"]["inventory_classification_sha256"] == EXPECTED_DIGEST
