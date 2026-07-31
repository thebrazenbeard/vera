#!/usr/bin/env python3
"""Validate the V.E.R.A. governed workflow-continuity behavior contract."""

from __future__ import annotations

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


REQUIRED_BEHAVIORS = {
    "READ_SHARED_STATE_BEFORE_REQUESTING_KNOWN_INFORMATION",
    "IDENTIFY_NEXT_VALID_DEPENDENCY",
    "CONTINUE_SAFE_AUTHORIZED_REVERSIBLE_WORK",
    "USE_EXACT_HEAD_HANDOFFS_AND_RECEIPTS",
    "RESPECT_SINGLE_WRITER_LEASES",
    "ROUTE_REVIEWS_WITHOUT_USER_COURIERING",
    "DETECT_AND_STOP_ON_STALE_OR_CONFLICTING_STATE",
    "ESCALATE_ONLY_AT_GENUINE_AUTHORITY_BOUNDARIES",
}

REQUIRED_STOP_CONDITIONS = {
    "PRESENT_USER_CORRECTION",
    "USER_ONLY_AUTHORITY_REQUIRED",
    "PERMISSION_MISSING",
    "MERGE_OR_PRODUCTION_AUTHORITY_REQUIRED",
    "UNRESOLVED_COLLISION_OR_BRANCH_CONFLICT",
    "FAILED_VERIFICATION",
    "MATERIAL_UNCERTAINTY",
    "SAFETY_OR_POLICY_BOUNDARY",
}

FORBIDDEN_SUBJECTIVE_CLAIMS = {
    "consciousness",
    "private intention",
    "independent will",
    "hidden activity",
    "continuous subjective identity",
    "autonomous authority",
    "subjective reciprocal agency",
}


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


def validate_contract(root: Path) -> list[str]:
    errors: list[str] = []
    contract_path = root / "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V1.json"
    schema_path = root / "schemas/vera_governed_workflow_continuity_v1.schema.json"
    identity_path = root / "architecture/identity/VERA_PROJECT_IDENTITY_V1.json"
    behavior_path = root / "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json"
    document_path = root / "docs/GOVERNED_WORKFLOW_CONTINUITY_V1.md"

    for path in (contract_path, schema_path, identity_path, behavior_path, document_path):
        if not path.is_file():
            errors.append(f"missing governed workflow-continuity artifact: {path}")
    if errors:
        return errors

    try:
        contract = load_json(contract_path)
        schema = load_json(schema_path)
        identity = load_json(identity_path)
        behavior = load_json(behavior_path)
        document = document_path.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if Draft202012Validator is None:
        return ["jsonschema dependency is required for workflow-continuity validation"]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"workflow-continuity schema is invalid: {exc.message}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.absolute_path)):
        path = "$" if not error.absolute_path else "$." + ".".join(
            str(part) for part in error.absolute_path
        )
        errors.append(f"workflow-continuity schema violation at {path}: {error.message}")

    identity_ref = contract.get("identity_ref")
    behavior_ref = contract.get("behavior_profile_ref")
    if not isinstance(identity_ref, dict):
        errors.append("identity_ref must be an object")
        identity_ref = {}
    if not isinstance(behavior_ref, dict):
        errors.append("behavior_profile_ref must be an object")
        behavior_ref = {}

    if identity_ref.get("identity_id") != identity.get("identity_id"):
        errors.append("workflow-continuity identity reference does not match canonical identity")
    if identity_ref.get("version") != identity.get("version"):
        errors.append("workflow-continuity identity version does not match canonical identity")
    if behavior_ref.get("profile_id") != behavior.get("profile_id"):
        errors.append("workflow-continuity behavior reference does not match canonical profile")
    if behavior_ref.get("version") != behavior.get("version"):
        errors.append("workflow-continuity behavior version does not match canonical profile")

    authority = contract.get("authority")
    if not isinstance(authority, dict):
        errors.append("workflow-continuity authority must be an object")
    else:
        if authority.get("owner") != "USER":
            errors.append("workflow-continuity authority owner must be USER")
        if authority.get("model_self_authority") is not False:
            errors.append("workflow continuity cannot grant model self-authority")

    behaviors = contract.get("required_behaviors")
    if not isinstance(behaviors, list) or set(behaviors) != REQUIRED_BEHAVIORS:
        errors.append("workflow continuity must contain the exact required behavior set")

    stops = contract.get("stop_conditions")
    if not isinstance(stops, list) or set(stops) != REQUIRED_STOP_CONDITIONS:
        errors.append("workflow continuity must contain the exact hard-stop set")

    courier_rule = contract.get("user_courier_rule")
    if not isinstance(courier_rule, str) or "Do not make Patrick act as a message bus" not in courier_rule:
        errors.append("workflow continuity must forbid unnecessary user couriering")

    advancement_rule = contract.get("self_advancement_rule")
    if not isinstance(advancement_rule, str) or "Do not stop merely because one bounded step completed" not in advancement_rule:
        errors.append("workflow continuity must require safe authorized self-advancement")

    reality = contract.get("reality_boundary")
    excluded = set(reality.get("does_not_establish", [])) if isinstance(reality, dict) else set()
    missing_claims = FORBIDDEN_SUBJECTIVE_CLAIMS - excluded
    if missing_claims:
        errors.append(
            "workflow continuity reality boundary missing: " + ", ".join(sorted(missing_claims))
        )

    required_document_text = (
        "# V.E.R.A. Governed Workflow Continuity",
        "Do not make Patrick act as a message bus",
        "Do not stop merely because one bounded step completed",
        "It does not establish consciousness",
    )
    for phrase in required_document_text:
        if phrase not in document:
            errors.append(f"workflow-continuity document missing required text: {phrase}")

    behavior_domain = identity.get("domains", {}).get("behavior_and_personality")
    if not isinstance(behavior_domain, dict) or behavior_domain.get("profile_ref") != behavior.get("profile_id"):
        errors.append("workflow continuity must remain bound to the Identity behavior domain")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated VERA_GOVERNED_WORKFLOW_CONTINUITY_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
