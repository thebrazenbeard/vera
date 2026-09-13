from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "predecessor_import_batch.py"
TABLE = "vera_save_state_events"
MEMORY_TABLE = "vera_memory_epoch_events_v1"


def snapshot_digest(row_texts: list[str]) -> str:
    preimage = "[" + ", ".join(row_texts) + "]"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def write_manifest(path: Path, table: str, row_texts: list[str]) -> None:
    path.write_text(json.dumps({"tables": {f"public.{table}": {
        "rows": len(row_texts), "sha256": snapshot_digest(row_texts)
    }}}), encoding="utf-8")


def envelope(table: str, ordinal: int, row_text: str) -> dict:
    return {"source_table": table, "source_ordinal": ordinal,
            "source_row_jsonb_text": row_text}

def run_batch(tmp_path: Path, records: list[dict], manifest_table: str, manifest_rows: list[str]):
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    manifest = tmp_path / "manifest.json"
    source.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")
    write_manifest(manifest, manifest_table, manifest_rows)
    result = subprocess.run([
        sys.executable, str(SCRIPT), "--input", str(source), "--output", str(target),
        "--manifest", str(manifest), "--operation-id", "op-1"
    ], text=True, capture_output=True, check=False)
    rows = []
    if target.exists():
        rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    return result, rows


def save_row(record_id: str, privacy: str = "PRIVATE_RELATIONAL", statement: str = "x") -> str:
    return json.dumps({"privacy_scope": privacy, "record_id": record_id, "statement": statement},
                      separators=(", ", ": "), ensure_ascii=False)


def memory_row(event_id: str, payload: str = "x") -> str:
    return json.dumps({"event_id": event_id, "event_payload": {"value": payload}},
                      separators=(", ", ": "), ensure_ascii=False)

def test_exact_single_table_batch_binds_source_cut(tmp_path: Path) -> None:
    texts = [
        save_row("00000000-0000-0000-0000-000000000001", statement="a"),
        save_row("00000000-0000-0000-0000-000000000002", statement="b"),
    ]
    result, rows = run_batch(tmp_path,
        [envelope(TABLE, 1, texts[0]), envelope(TABLE, 2, texts[1])], TABLE, texts)
    assert result.returncode == 0, result.stderr
    assert len(rows) == 2
    assert [r["source_ordinal"] for r in rows] == [1, 2]
    assert all(r["source_snapshot_sha256"] == snapshot_digest(texts) for r in rows)
    assert rows[0]["source_row_sha256"] == hashlib.sha256(texts[0].encode()).hexdigest()
    assert rows[0]["privacy_class"] == "PRIVATE_RELATIONAL"
    assert "admitted" not in rows[0] and "current" not in rows[0]


def test_memory_epoch_has_non_broadenable_private_floor(tmp_path: Path) -> None:
    text = memory_row("00000000-0000-0000-0000-000000000010")
    result, rows = run_batch(tmp_path, [envelope(MEMORY_TABLE, 1, text)], MEMORY_TABLE, [text])
    assert result.returncode == 0, result.stderr
    assert rows[0]["privacy_class"] == "PRIVATE_AUTOBIOGRAPHICAL"

def test_dropped_or_added_rows_fail_closed(tmp_path: Path) -> None:
    texts = [save_row("00000000-0000-0000-0000-000000000001"),
             save_row("00000000-0000-0000-0000-000000000002")]
    result, _ = run_batch(tmp_path / "drop", [envelope(TABLE, 1, texts[0])], TABLE, texts)
    assert result.returncode != 0 and "row count" in result.stderr.lower()
    extra = save_row("00000000-0000-0000-0000-000000000003")
    result, _ = run_batch(tmp_path / "add",
        [envelope(TABLE, 1, texts[0]), envelope(TABLE, 2, texts[1]), envelope(TABLE, 3, extra)], TABLE, texts)
    assert result.returncode != 0 and "row count" in result.stderr.lower()


def test_mutated_row_fails_snapshot_digest(tmp_path: Path) -> None:
    source = save_row("00000000-0000-0000-0000-000000000001", statement="source")
    changed = save_row("00000000-0000-0000-0000-000000000001", statement="changed")
    result, _ = run_batch(tmp_path, [envelope(TABLE, 1, changed)], TABLE, [source])
    assert result.returncode != 0 and "snapshot digest" in result.stderr.lower()


def test_mixed_table_batch_is_rejected(tmp_path: Path) -> None:
    one = save_row("00000000-0000-0000-0000-000000000001")
    mem = memory_row("00000000-0000-0000-0000-000000000010")
    result, _ = run_batch(tmp_path, [envelope(TABLE, 1, one), envelope(MEMORY_TABLE, 2, mem)], TABLE, [one, mem])
    assert result.returncode != 0 and "one source table" in result.stderr.lower()

def test_duplicate_pk_or_bad_ordinals_are_rejected(tmp_path: Path) -> None:
    a = save_row("00000000-0000-0000-0000-000000000001", statement="a")
    b = save_row("00000000-0000-0000-0000-000000000001", statement="b")
    result, _ = run_batch(tmp_path / "dupe",
        [envelope(TABLE, 1, a), envelope(TABLE, 2, b)], TABLE, [a, b])
    assert result.returncode != 0 and "duplicate primary key" in result.stderr.lower()

    c = save_row("00000000-0000-0000-0000-000000000002")
    result, _ = run_batch(tmp_path / "ordinal",
        [envelope(TABLE, 1, a), envelope(TABLE, 3, c)], TABLE, [a, c])
    assert result.returncode != 0 and "ordinal" in result.stderr.lower()


def test_malformed_source_jsonb_text_is_rejected(tmp_path: Path) -> None:
    bad = '{"record_id":'
    result, _ = run_batch(tmp_path, [envelope(TABLE, 1, bad)], TABLE, [bad])
    assert result.returncode != 0 and "json" in result.stderr.lower()
