#!/usr/bin/env python3
"""Validate fail-closed temporal anchoring for V.E.R.A. Identity artifacts."""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover
    Draft202012Validator = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment,misc]


ANCHOR_VERSION = "1.0.0"
ANCHOR_ID = "VERA_IDENTITY_TEMPORAL_ANCHOR_V1__IDENTITY_1_0_2__BEHAVIOR_1_0_1"
ANCHORED_REVISION_CONTRACT = (
    "REQUIRES_SEPARATELY_REVIEWED_VERIFIER_OWNED_TEMPORAL_EVIDENCE_CONTRACT"
)
BACKDATING_POLICY = "FORBIDDEN_WITHOUT_EXTERNALLY_VERIFIED_STATE_TIME"


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


def canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def validate_unknown_evidence(
    role: str, evidence: dict[str, Any], errors: list[str]
) -> None:
    if evidence.get("precision") != "UNKNOWN":
        errors.append(
            f"{role} Temporal Anchor V1 forbids caller-certified non-UNKNOWN evidence"
        )
    if evidence.get("temporal_claim") is not False:
        errors.append(f"{role} UNKNOWN evidence must have temporal_claim false")
    if any(
        evidence.get(field) is not None
        for field in ("value", "lower_bound", "upper_bound")
    ):
        errors.append(f"{role} UNKNOWN evidence forbids timestamps and bounds")
    source = evidence.get("source")
    if not isinstance(source, str) or not source.strip():
        errors.append(f"{role} UNKNOWN evidence requires an explanatory source")


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

    if Draft202012Validator is None:
        return ["jsonschema dependency is required for temporal anchor validation"]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"temporal anchor schema is invalid: {exc.message}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(anchor), key=lambda item: list(item.absolute_path)):
        path = "$" if not error.absolute_path else "$." + ".".join(
            str(part) for part in error.absolute_path
        )
        errors.append(f"temporal anchor schema violation at {path}: {error.message}")

    identity_ref = anchor.get("identity_ref")
    if not isinstance(identity_ref, dict):
        errors.append("identity_ref must be an object")
        identity_ref = {}
    behavior_ref = anchor.get("behavior_profile_ref")
    if not isinstance(behavior_ref, dict):
        errors.append("behavior_profile_ref must be an object")
        behavior_ref = {}

    if identity_ref.get("identity_id") != identity.get("identity_id"):
        errors.append("temporal anchor identity_id does not match canonical identity")
    if identity_ref.get("version") != identity.get("version"):
        errors.append("temporal anchor identity version does not match canonical identity")
    if behavior_ref.get("profile_id") != behavior.get("profile_id"):
        errors.append("temporal anchor profile_id does not match behavior profile")
    if behavior_ref.get("version") != behavior.get("version"):
        errors.append("temporal anchor behavior version does not match behavior profile")

    expected_anchor_id = (
        "VERA_IDENTITY_TEMPORAL_ANCHOR_V1__IDENTITY_"
        + str(identity.get("version", "")).replace(".", "_")
        + "__BEHAVIOR_"
        + str(behavior.get("version", "")).replace(".", "_")
    )
    if anchor.get("anchor_id") != expected_anchor_id or expected_anchor_id != ANCHOR_ID:
        errors.append("temporal anchor ID must bind the exact identity and behavior versions")
    if anchor.get("anchor_version") != ANCHOR_VERSION:
        errors.append("temporal anchor version must be 1.0.0")

    if anchor.get("lineage_status") != "ROOT":
        errors.append("Temporal Anchor V1 must remain the ROOT anchor")
    if anchor.get("predecessor_anchor_ref") is not None:
        errors.append("ROOT temporal anchor forbids a predecessor reference")
    if anchor.get("supersedes_anchor_id") is not None:
        errors.append("ROOT temporal anchor forbids supersession")

    subject = {
        "operation": "IDENTITY_VERSION_TEMPORAL_ANCHOR",
        "anchor_version": ANCHOR_VERSION,
        "identity_id": identity_ref.get("identity_id"),
        "identity_version": identity_ref.get("version"),
        "behavior_profile_id": behavior_ref.get("profile_id"),
        "behavior_profile_version": behavior_ref.get("version"),
    }
    subject_binding = anchor.get("subject_binding")
    if not isinstance(subject_binding, dict):
        errors.append("subject_binding must be an object")
    else:
        if subject_binding.get("operation") != subject["operation"]:
            errors.append("temporal anchor subject operation mismatch")
        if subject_binding.get("subject_hash_algorithm") != "SHA-256":
            errors.append("temporal anchor subject hash algorithm must be SHA-256")
        if subject_binding.get("subject_hash") != canonical_hash(subject):
            errors.append("temporal anchor subject hash does not bind exact versions")

    if anchor.get("version_effectiveness") != "UNANCHORED":
        errors.append("Temporal Anchor V1 must remain UNANCHORED")
    if anchor.get("effective_time_role") != "state_time":
        errors.append("identity version effectiveness must derive only from state_time")
    if anchor.get("anchored_revision_contract") != ANCHORED_REVISION_CONTRACT:
        errors.append("anchored successor requires a separately reviewed verifier-owned contract")
    if anchor.get("backdating_policy") != BACKDATING_POLICY:
        errors.append("identity backdating must remain forbidden without verified state_time")
    if anchor.get("retrieval_time_semantics") != "INVOCATION_TIME_ONLY_NOT_VERSION_EFFECTIVENESS":
        errors.append("retrieval_time must remain invocation-only and cannot establish effectiveness")

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
            validate_unknown_evidence(role, evidence, errors)
        else:
            errors.append(f"missing temporal evidence role: {role}")

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
    print("validated fail-closed VERA_IDENTITY_TEMPORAL_ANCHOR_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
