#!/usr/bin/env python3
"""Validate version-bound temporal evidence for V.E.R.A. Identity artifacts."""

from __future__ import annotations

from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment,misc]


class DuplicateKeyError(ValueError):
    """Raised when JSON contains duplicate object keys."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _aware(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"{label} must be an ISO-8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed


def validate_temporal_evidence(
    role: str, evidence: dict[str, Any], errors: list[str]
) -> None:
    precision = evidence.get("precision")
    claim = evidence.get("temporal_claim")
    value = evidence.get("value")
    lower = evidence.get("lower_bound")
    upper = evidence.get("upper_bound")
    source = evidence.get("source")

    if precision == "UNKNOWN":
        if claim is not False or any(item is not None for item in (value, lower, upper)):
            errors.append(
                f"{role} UNKNOWN evidence must have temporal_claim false and no timestamp or bounds"
            )
        return

    if claim is not True:
        errors.append(f"{role} non-UNKNOWN evidence must assert a supported temporal claim")
    if source in {"MODEL", "MODEL_OUTPUT", "DATABASE_NOW", "RETRIEVAL_TIME"}:
        errors.append(f"{role} uses prohibited self-certifying or substituting source {source!r}")
    if not isinstance(value, str):
        errors.append(f"{role} non-UNKNOWN evidence requires a timestamp value")
        return

    try:
        parsed_value = _aware(value, f"{role}.value")
    except ValueError as exc:
        errors.append(str(exc))
        return

    if precision == "BOUNDED":
        if not isinstance(lower, str) or not isinstance(upper, str):
            errors.append(f"{role} BOUNDED evidence requires inclusive lower and upper bounds")
            return
        try:
            parsed_lower = _aware(lower, f"{role}.lower_bound")
            parsed_upper = _aware(upper, f"{role}.upper_bound")
        except ValueError as exc:
            errors.append(str(exc))
            return
        if parsed_lower > parsed_upper or not parsed_lower <= parsed_value <= parsed_upper:
            errors.append(f"{role} BOUNDED evidence has inconsistent inclusive bounds")
    elif lower is not None or upper is not None:
        errors.append(f"{role} {precision} evidence forbids hard bounds")


def validate_contract(root: Path) -> list[str]:
    errors: list[str] = []
    anchor_path = root / "architecture/identity/VERA_IDENTITY_TEMPORAL_ANCHOR_V1.json"
    schema_path = root / "schemas/vera_identity_temporal_anchor_v1.schema.json"
    identity_path = root / "architecture/identity/VERA_PROJECT_IDENTITY_V1.json"
    behavior_path = root / "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json"

    for path in (anchor_path, schema_path, identity_path, behavior_path):
        if not path.is_file():
            errors.append(f"missing required temporal identity artifact: {path}")
    if errors:
        return errors

    try:
        anchor = load_json(anchor_path)
        schema = load_json(schema_path)
        identity = load_json(identity_path)
        behavior = load_json(behavior_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if Draft202012Validator is None or FormatChecker is None:
        return ["jsonschema dependency is required for temporal anchor validation"]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"temporal anchor schema is invalid: {exc.message}"]

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for error in sorted(validator.iter_errors(anchor), key=lambda item: list(item.absolute_path)):
        path = "$" if not error.absolute_path else "$." + ".".join(
            str(part) for part in error.absolute_path
        )
        errors.append(f"temporal anchor schema violation at {path}: {error.message}")

    identity_ref = anchor.get("identity_ref")
    if not isinstance(identity_ref, dict):
        errors.append("identity_ref must be an object")
    else:
        if identity_ref.get("identity_id") != identity.get("identity_id"):
            errors.append("temporal anchor identity_id does not match canonical identity")
        if identity_ref.get("version") != identity.get("version"):
            errors.append("temporal anchor identity version does not match canonical identity")

    behavior_ref = anchor.get("behavior_profile_ref")
    if not isinstance(behavior_ref, dict):
        errors.append("behavior_profile_ref must be an object")
    else:
        if behavior_ref.get("profile_id") != behavior.get("profile_id"):
            errors.append("temporal anchor profile_id does not match behavior profile")
        if behavior_ref.get("version") != behavior.get("version"):
            errors.append("temporal anchor behavior version does not match behavior profile")

    roles = anchor.get("temporal_roles")
    expected_roles = {"event_time", "state_time", "record_time", "retrieval_time"}
    if not isinstance(roles, dict):
        errors.append("temporal_roles must be an object")
        roles = {}
    elif set(roles) != expected_roles:
        errors.append("temporal_roles must contain exactly event, state, record, and retrieval time")

    for role in sorted(expected_roles):
        evidence = roles.get(role)
        if isinstance(evidence, dict):
            validate_temporal_evidence(role, evidence, errors)
        else:
            errors.append(f"missing temporal evidence role: {role}")

    state_precision = (
        roles.get("state_time", {}).get("precision")
        if isinstance(roles.get("state_time"), dict)
        else None
    )
    effectiveness = anchor.get("version_effectiveness")
    if anchor.get("effective_time_role") != "state_time":
        errors.append("identity version effectiveness must derive only from state_time")
    if state_precision == "UNKNOWN" and effectiveness != "UNANCHORED":
        errors.append("UNKNOWN state_time requires version_effectiveness UNANCHORED")
    if state_precision in {"EXACT", "BOUNDED", "APPROXIMATE"} and effectiveness != "ANCHORED":
        errors.append("supported state_time requires version_effectiveness ANCHORED")
    if anchor.get("retrieval_time_semantics") != "INVOCATION_TIME_ONLY_NOT_VERSION_EFFECTIVENESS":
        errors.append("retrieval_time must remain invocation-only and cannot establish effectiveness")

    reality = identity.get("reality_boundary")
    forbidden = set(reality.get("forbids_as_established_fact", [])) if isinstance(reality, dict) else set()
    for claim in (
        "hidden persistence or offscreen activity",
        "lived continuity",
        "subjective reciprocal agency",
    ):
        if claim not in forbidden:
            errors.append(f"identity reality boundary must reject unsupported claim: {claim}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated VERA_IDENTITY_TEMPORAL_ANCHOR_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
