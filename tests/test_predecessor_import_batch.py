from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "predecessor_import_batch.py"
SNAPSHOT = "a" * 64


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def run_batch(tmp_path: Path, records: list[dict]) -> list[dict]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    source.write_text("".join(canonical(r) + "\n" for r in records), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(source), "--output", str(target), "--snapshot-sha256", SNAPSHOT, "--operation-id", "op-1"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]


def test_save_state_row_gets_stable_identity_digest_and_privacy(tmp_path: Path) -> None:
    row = {
        "record_id": "00000000-0000-0000-0000-000000000001",
        "privacy_scope": "PRIVATE_RELATIONAL",
        "statement": "private",
        "payload": {"b": 2, "a": 1},
    }
    [staged] = run_batch(tmp_path, [{"source_table": "vera_save_state_events", "row": row}])
    assert staged["source_provider"] == "klmbpaigzeguvnpccqzz"
    assert staged["source_schema"] == "public"
    assert staged["source_table"] == "vera_save_state_events"
    assert staged["source_pk"] == {"record_id": row["record_id"]}
    assert staged["privacy_class"] == "PRIVATE_RELATIONAL"
    assert staged["source_snapshot_sha256"] == SNAPSHOT
    assert staged["source_row_sha256"] == hashlib.sha256(canonical(row).encode()).hexdigest()
    assert staged["source_payload"] == row
    assert "admitted" not in staged
    assert "current" not in staged


def test_memory_receipt_uses_receipt_id_and_project_internal_privacy(tmp_path: Path) -> None:
    row = {"receipt_id": "00000000-0000-0000-0000-000000000002", "result": "VERIFIED_EXACT"}
    [staged] = run_batch(tmp_path, [{"source_table": "vera_memory_epoch_provider_receipts_v1", "row": row}])
    assert staged["source_pk"] == {"receipt_id": row["receipt_id"]}
    assert staged["privacy_class"] == "PROJECT_INTERNAL"
