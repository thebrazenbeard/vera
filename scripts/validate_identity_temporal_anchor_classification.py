#!/usr/bin/env python3
"""Validate the noncanonical routing classification of Identity Temporal Anchor V1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_RECORD_CLASS = "PROJECT_CONFIGURATION"
EXPECTED_INSTRUCTION_TRUST = "DATA_NOT_INSTRUCTION"
EXPECTED_CANONICAL_MEMORY_ELIGIBLE = False


class DuplicateKeyError(ValueError):
    """Raised when JSON contains duplicate object keys."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def validate_contract(root: Path) -> list[str]:
    anchor_path = root / "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json"
    if not anchor_path.is_file():
        return [f"missing required temporal anchor artifact: {anchor_path}"]

    try:
        anchor = load_json(anchor_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    errors: list[str] = []
    if anchor.get("record_class") != EXPECTED_RECORD_CLASS:
        errors.append("identity temporal anchor must remain PROJECT_CONFIGURATION")
    if anchor.get("instruction_trust") != EXPECTED_INSTRUCTION_TRUST:
        errors.append("identity temporal anchor must remain DATA_NOT_INSTRUCTION")
    if anchor.get("canonical_memory_eligible") is not EXPECTED_CANONICAL_MEMORY_ELIGIBLE:
        errors.append("identity temporal anchor must remain ineligible for canonical memory")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated noncanonical identity temporal anchor classification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
