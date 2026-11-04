"""Fail closed on ambiguous runtime-cohesion JSON source syntax.

This is a source-byte gate. It neither reads a native Project installation nor
asserts that any runtime has consumed these contracts. The historical cohesion
validator and its exact-byte pair receipt remain untouched.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SOURCE_FILENAMES = (
    "VERA_SYSTEM_MANIFEST_V1.json",
    "VERA_RUNTIME_ROUTING_CONTRACT_V1.json",
    "VERA_INTROSPECTION_EVIDENCE_SCHEMA_V1.json",
    "VERA_RUNTIME_EVIDENCE_CONTRACT_V1.json",
    "VERA_COHESION_INDEX_V1.json",
    "VERA_RUNTIME_CONTRACT_V1.json",
    "VERA_COHESION_PAIR_RECEIPT_V1.json",
)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def load_unambiguous_json(path: Path) -> dict[str, Any]:
    """Reject nested/escaped duplicate keys and nonstandard numeric constants."""
    with path.open("r", encoding="utf-8-sig") as handle:
        document = json.load(
            handle,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonstandard_constant,
        )
    if not isinstance(document, dict):
        raise ValueError("top-level runtime-cohesion source must be a JSON object")
    return document


def validate_source_syntax(root: Path) -> tuple[str, ...]:
    architecture = root / "architecture"
    for filename in SOURCE_FILENAMES:
        load_unambiguous_json(architecture / filename)
    return SOURCE_FILENAMES


if __name__ == "__main__":
    validated = validate_source_syntax(Path(__file__).resolve().parents[1])
    print(f"VERA runtime-cohesion JSON source: {len(validated)} unambiguous files; native installation UNKNOWN")
