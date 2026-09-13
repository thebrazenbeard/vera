from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

SOURCE_PROVIDER = "klmbpaigzeguvnpccqzz"
SOURCE_SCHEMA = "public"
DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "architecture"
    / "VERA_PREDECESSOR_MIGRATION_CARGO_SNAPSHOT_20260912.json"
)

TABLES: dict[str, tuple[str, str | None]] = {
    "vera_affective_runtime_events_v1": ("event_id", "PROJECT_INTERNAL"),
    "vera_affective_runtime_state_v1": ("runtime_instance_id", "PROJECT_INTERNAL"),
    "vera_context_events_v3": ("record_id", None),
    "vera_memory_epoch_archive_receipts_v1": ("archive_receipt_id", None),
    "vera_memory_epoch_events_v1": ("event_id", None),
    "vera_memory_epoch_provider_receipts_v1": ("receipt_id", None),
    "vera_memory_epoch_subjects_v1": ("subject_id", None),
    "vera_save_state_events": ("record_id", None),
    "vera_save_state_supersession_edges": ("edge_id", "PROJECT_INTERNAL"),
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables = data.get("tables")
    if not isinstance(tables, dict):
        raise ValueError("manifest must contain a tables object")
    return data


def privacy_for(table: str, row: dict[str, Any], default_privacy: str | None) -> str:
    if table.startswith("vera_memory_epoch_"):
        return "PRIVATE_AUTOBIOGRAPHICAL"
    privacy = row.get("privacy_scope", default_privacy)
    if not isinstance(privacy, str) or not privacy:
        raise ValueError(f"missing privacy scope for {table}")
    return privacy


def parse_record(record: dict[str, Any]) -> tuple[str, int, str, dict[str, Any]]:
    table = record.get("source_table")
    ordinal = record.get("source_ordinal")
    row_text = record.get("source_row_jsonb_text")
    if table not in TABLES:
        raise ValueError(f"unsupported source_table: {table!r}")
    if not isinstance(ordinal, int) or isinstance(ordinal, bool) or ordinal < 1:
        raise ValueError("source_ordinal must be a positive integer")
    if not isinstance(row_text, str) or not row_text:
        raise ValueError("source_row_jsonb_text must be non-empty text")
    try:
        row = json.loads(row_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"source_row_jsonb_text is not valid JSON: {exc.msg}") from exc
    if not isinstance(row, dict):
        raise ValueError("source row must decode to a JSON object")
    return table, ordinal, row_text, row


def validate_batch(records: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[str, str, list[tuple[int, str, dict[str, Any]]]]:
    if not records:
        raise ValueError("batch is empty")
    parsed = [parse_record(record) for record in records]
    tables = {item[0] for item in parsed}
    if len(tables) != 1:
        raise ValueError("batch must contain exactly one source table")
    table = next(iter(tables))
    parsed.sort(key=lambda item: item[1])
    ordinals = [item[1] for item in parsed]
    if ordinals != list(range(1, len(parsed) + 1)):
        raise ValueError("source ordinals must be unique and contiguous from 1")

    pk_field, _ = TABLES[table]
    seen_pks: set[str] = set()
    for _, _, _, row in parsed:
        if pk_field not in row or row[pk_field] in (None, ""):
            raise ValueError(f"missing primary-key field {pk_field!r} for {table}")
        pk_key = canonical(row[pk_field])
        if pk_key in seen_pks:
            raise ValueError(f"duplicate primary key for {table}: {row[pk_field]!r}")
        seen_pks.add(pk_key)

    table_key = f"{SOURCE_SCHEMA}.{table}"
    expected = manifest["tables"].get(table_key)
    if not isinstance(expected, dict):
        raise ValueError(f"manifest has no source cut for {table_key}")
    expected_rows = expected.get("rows")
    expected_digest = expected.get("sha256")
    if expected_rows != len(parsed):
        raise ValueError(f"row count mismatch for {table_key}: expected {expected_rows}, got {len(parsed)}")
    row_texts = [item[2] for item in parsed]
    preimage = "[" + ", ".join(row_texts) + "]"
    actual_digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    if actual_digest != expected_digest:
        raise ValueError(
            f"snapshot digest mismatch for {table_key}: expected {expected_digest}, got {actual_digest}"
        )
    return table, expected_digest, [(item[1], item[2], item[3]) for item in parsed]


def stage_batch(records: list[dict[str, Any]], manifest: dict[str, Any], operation_id: str) -> list[dict[str, Any]]:
    table, snapshot_digest, parsed = validate_batch(records, manifest)
    pk_field, default_privacy = TABLES[table]
    staged: list[dict[str, Any]] = []
    for ordinal, row_text, row in parsed:
        staged.append({
            "operation_id": operation_id,
            "source_provider": SOURCE_PROVIDER,
            "source_schema": SOURCE_SCHEMA,
            "source_table": table,
            "source_ordinal": ordinal,
            "source_pk": {pk_field: row[pk_field]},
            "source_row_sha256": hashlib.sha256(row_text.encode("utf-8")).hexdigest(),
            "source_snapshot_sha256": snapshot_digest,
            "source_row_jsonb_text": row_text,
            "source_payload": row,
            "privacy_class": privacy_for(table, row, default_privacy),
        })
    return staged


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one exact predecessor source cut and emit locked import-staging records."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--operation-id", required=True)
    args = parser.parse_args()
    if not args.operation_id.strip():
        parser.error("--operation-id must be non-empty")
    return args


def main() -> int:
    args = parse_args()
    output = args.output
    temp = output.with_name(output.name + ".tmp")
    try:
        manifest = load_manifest(args.manifest)
        records = []
        with args.input.open("r", encoding="utf-8") as source:
            for line_number, raw in enumerate(source, start=1):
                if not raw.strip():
                    continue
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"line {line_number}: invalid envelope JSON: {exc.msg}") from exc
                if not isinstance(record, dict):
                    raise ValueError(f"line {line_number}: envelope must be a JSON object")
                records.append(record)
        staged = stage_batch(records, manifest, args.operation_id)
        with temp.open("w", encoding="utf-8", newline="\n") as target:
            for record in staged:
                target.write(canonical(record) + "\n")
        os.replace(temp, output)
        return 0
    except Exception as exc:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
