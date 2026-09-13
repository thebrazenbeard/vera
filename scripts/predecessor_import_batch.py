from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SOURCE_PROVIDER = "klmbpaigzeguvnpccqzz"
SOURCE_SCHEMA = "public"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

TABLES: dict[str, tuple[str, str | None]] = {
    "vera_affective_runtime_events_v1": ("event_id", "PROJECT_INTERNAL"),
    "vera_affective_runtime_state_v1": ("runtime_instance_id", "PROJECT_INTERNAL"),
    "vera_context_events_v3": ("record_id", None),
    "vera_memory_epoch_archive_receipts_v1": ("archive_receipt_id", "PROJECT_INTERNAL"),
    "vera_memory_epoch_events_v1": ("event_id", "PROJECT_INTERNAL"),
    "vera_memory_epoch_provider_receipts_v1": ("receipt_id", "PROJECT_INTERNAL"),
    "vera_memory_epoch_subjects_v1": ("subject_id", "PROJECT_INTERNAL"),
    "vera_save_state_events": ("record_id", None),
    "vera_save_state_supersession_edges": ("edge_id", "PROJECT_INTERNAL"),
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def transform(record: dict[str, Any], *, snapshot_sha256: str, operation_id: str) -> dict[str, Any]:
    table = record.get("source_table")
    row = record.get("row")
    if table not in TABLES:
        raise ValueError(f"unsupported source_table: {table!r}")
    if not isinstance(row, dict):
        raise ValueError("row must be a JSON object")

    pk_field, default_privacy = TABLES[table]
    if pk_field not in row or row[pk_field] in (None, ""):
        raise ValueError(f"missing primary-key field {pk_field!r} for {table}")

    privacy = row.get("privacy_scope", default_privacy)
    if not isinstance(privacy, str) or not privacy:
        raise ValueError(f"missing privacy scope for {table}")

    row_bytes = canonical(row).encode("utf-8")
    return {
        "operation_id": operation_id,
        "source_provider": SOURCE_PROVIDER,
        "source_schema": SOURCE_SCHEMA,
        "source_table": table,
        "source_pk": {pk_field: row[pk_field]},
        "source_row_sha256": hashlib.sha256(row_bytes).hexdigest(),
        "source_snapshot_sha256": snapshot_sha256,
        "source_payload": row,
        "privacy_class": privacy,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform predecessor rows into locked Vera import-staging records.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--snapshot-sha256", required=True)
    parser.add_argument("--operation-id", required=True)
    args = parser.parse_args()
    if not SHA256_RE.fullmatch(args.snapshot_sha256):
        parser.error("--snapshot-sha256 must be 64 lowercase hex characters")
    if not args.operation_id.strip():
        parser.error("--operation-id must be non-empty")
    return args


def main() -> int:
    args = parse_args()
    output = args.output
    temp = output.with_name(output.name + ".tmp")
    try:
        with args.input.open("r", encoding="utf-8") as source, temp.open("w", encoding="utf-8", newline="\n") as target:
            for line_number, raw in enumerate(source, start=1):
                if not raw.strip():
                    continue
                try:
                    record = json.loads(raw)
                    staged = transform(record, snapshot_sha256=args.snapshot_sha256, operation_id=args.operation_id)
                except Exception as exc:
                    raise ValueError(f"line {line_number}: {exc}") from exc
                target.write(canonical(staged) + "\n")
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
