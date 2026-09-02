#!/usr/bin/env python3
"""Validate the current proportional workflow-continuity contract (V2)."""

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

CONTRACT = "architecture/identity/VERA_GOVERNED_WORKFLOW_CONTINUITY_V2.json"
SCHEMA = "schemas/vera_governed_workflow_continuity_v2.schema.json"
POINTER = "architecture/identity/WORKFLOW_CONTINUITY_CURRENT.json"
DOC = "docs/GOVERNED_WORKFLOW_CONTINUITY_V2.md"
PRECEDENCE = "docs/PROTOCOL_EXECUTION_PRECEDENCE_V2.md"
TURN_TAKING = "docs/WORKSTREAM_TURN_TAKING_PROTOCOL_V2.md"
IDENTITY = "architecture/identity/VERA_PROJECT_IDENTITY_V1.json"
BEHAVIOR = "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json"

REQUIRED_BEHAVIORS = {
    "READ_SHARED_STATE_BEFORE_REQUESTING_KNOWN_INFORMATION",
    "HONOR_SPECIFIC_CURRENT_INSTRUCTION_WITHIN_SCOPE",
    "INCLUDE_NECESSARY_REVERSIBLE_SETUP",
    "CONTINUE_SAFE_AUTHORIZED_REVERSIBLE_WORK",
    "USE_PROPORTIONAL_WRITER_OWNERSHIP_CONTROL",
    "HONOR_REPOSITORY_LOCAL_STEWARDSHIP",
    "USE_EXACT_HEADS_WHEN_CLAIM_DEPENDS_ON_EXACT_STATE",
    "ROUTE_WORK_BEARING_COORDINATION_THROUGH_GITHUB",
    "CORRECT_BEHAVIOR_BEFORE_EXPLANATION",
    "ESCALATE_ONLY_AT_GENUINE_AUTHORITY_BOUNDARIES",
    "COMPLETE_CLEAR_EXECUTABLE_WORK_BEFORE_STATUS_ONLY_REPORTING",
}

REQUIRED_STOPS = {
    "MATERIAL_TARGET_OR_OUTCOME_AMBIGUITY",
    "CONFLICTING_CURRENT_INSTRUCTIONS",
    "COMPETING_CURRENT_WRITER_ON_SHARED_TARGET",
    "REPOSITORY_LOCAL_STEWARD_BOUNDARY",
    "PROTECTED_EFFECT_AUTHORITY_MISSING",
    "DETERMINISTIC_AUTH_TOOL_SCHEMA_INTEGRITY_FAILURE",
    "DIVERGENT_OR_AMBIGUOUS_NON_IDEMPOTENT_EFFECT",
    "FAILED_VERIFICATION_PREVENTS_SAFE_CONTINUATION",
    "SAFETY_OR_POLICY_BOUNDARY",
}

EXPECTED_CLASSES = {
    0: "OBSERVE",
    1: "ISOLATED_REVERSIBLE_WORK",
    2: "SHARED_MUTABLE_WORK",
    3: "PROTECTED_EFFECT",
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
    pass


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
    paths = [CONTRACT, SCHEMA, POINTER, DOC, PRECEDENCE, TURN_TAKING, IDENTITY, BEHAVIOR]
    for relative in paths:
        if not (root / relative).is_file():
            errors.append(f"missing Protocol V2 artifact: {relative}")
    if errors:
        return errors

    try:
        contract = load_json(root / CONTRACT)
        schema = load_json(root / SCHEMA)
        pointer = load_json(root / POINTER)
        identity = load_json(root / IDENTITY)
        behavior = load_json(root / BEHAVIOR)
        doc = (root / DOC).read_text(encoding="utf-8")
        precedence = (root / PRECEDENCE).read_text(encoding="utf-8")
        turn_taking = (root / TURN_TAKING).read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if Draft202012Validator is None:
        return ["jsonschema dependency is required for Protocol V2 validation"]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"Protocol V2 schema is invalid: {exc.message}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.absolute_path)):
        path = "$" if not error.absolute_path else "$." + ".".join(str(x) for x in error.absolute_path)
        errors.append(f"Protocol V2 schema violation at {path}: {error.message}")

    if pointer.get("current_contract_id") != "VERA_GOVERNED_WORKFLOW_CONTINUITY_V2":
        errors.append("current workflow pointer must resolve to V2")
    if pointer.get("current_contract_version") != "2.0.0":
        errors.append("current workflow pointer version must be 2.0.0")
    if pointer.get("current_contract_path") != CONTRACT:
        errors.append("current workflow pointer path must resolve to V2 contract")
    if pointer.get("coordination_surface") != "GITHUB_ONLY":
        errors.append("current workflow pointer must preserve GitHub-only work coordination")

    identity_ref = contract.get("identity_ref", {})
    behavior_ref = contract.get("behavior_profile_ref", {})
    if identity_ref.get("identity_id") != identity.get("identity_id") or identity_ref.get("version") != identity.get("version"):
        errors.append("Protocol V2 identity reference does not match current identity contract")
    if behavior_ref.get("profile_id") != behavior.get("profile_id") or behavior_ref.get("version") != behavior.get("version"):
        errors.append("Protocol V2 behavior reference does not match current behavior profile")

    authority = contract.get("authority", {})
    if authority.get("owner") != "USER" or authority.get("model_self_authority") is not False:
        errors.append("Protocol V2 authority must remain USER-owned and non-self-authorizing")

    if set(contract.get("required_behaviors", [])) != REQUIRED_BEHAVIORS:
        errors.append("Protocol V2 required behavior set drifted")
    if set(contract.get("stop_conditions", [])) != REQUIRED_STOPS:
        errors.append("Protocol V2 hard-stop set drifted")

    classes = contract.get("effect_classes")
    if not isinstance(classes, list):
        errors.append("Protocol V2 effect_classes must be a list")
    else:
        observed: dict[int, str] = {}
        for item in classes:
            if isinstance(item, dict) and isinstance(item.get("class"), int) and isinstance(item.get("name"), str):
                observed[item["class"]] = item["name"]
        if observed != EXPECTED_CLASSES:
            errors.append("Protocol V2 effect classes must be exactly 0/1/2/3 with canonical names")

    stewardship = contract.get("repository_stewardship_rule")
    if not isinstance(stewardship, str) or "repository-local steward" not in stewardship.lower() or "Patrick" not in stewardship:
        errors.append("Protocol V2 must bind Patrick-designated repository-local stewardship")

    if "same permission" not in str(contract.get("instruction_sufficiency_rule", "")):
        errors.append("Protocol V2 must reject redundant permission restatement")
    if "manufacture additional blocking gates" not in str(contract.get("good_enough_rule", "")).lower():
        errors.append("Protocol V2 must reject manufactured completion gates")

    reality = contract.get("reality_boundary")
    excluded = set(reality.get("does_not_establish", [])) if isinstance(reality, dict) else set()
    missing = FORBIDDEN_SUBJECTIVE_CLAIMS - excluded
    if missing:
        errors.append("Protocol V2 reality boundary missing: " + ", ".join(sorted(missing)))

    required_text = {
        DOC: ("Governed Workflow Continuity", "specific", "protected", "GitHub"),
        PRECEDENCE: ("DO -> VERIFY -> REPORT", "Necessary-step inclusion", "Class 3"),
        TURN_TAKING: ("Current nonproduction workstream coordination protocol", "Class-1", "protected effect"),
    }
    for relative, phrases in required_text.items():
        text = {DOC: doc, PRECEDENCE: precedence, TURN_TAKING: turn_taking}[relative]
        for phrase in phrases:
            if phrase not in text:
                errors.append(f"{relative} missing required Protocol V2 text: {phrase}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated VERA_GOVERNED_WORKFLOW_CONTINUITY_V2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
