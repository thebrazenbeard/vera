#!/usr/bin/env python3
"""Validate governed Identity workflow-continuity behavior."""

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


POLICY_ID = "VERA_IDENTITY_WORKFLOW_CONTINUITY_V1"
POLICY_VERSION = "1.0.0"
EXPECTED_HANDOFF_SEQUENCE = (
    "LOCK_PRESENT_USER_OBJECTIVE",
    "READ_CURRENT_CANONICAL_STATE",
    "CLAIM_OR_CONFIRM_SINGLE_WRITER_SCOPE",
    "COMPLETE_SMALLEST_AUTHORIZED_STEP",
    "PUBLISH_IMMUTABLE_HEAD_AND_RECEIPT",
    "HAND_OFF_TO_NEXT_BOUND_WORKSTREAM",
    "RECHECK_AFTER_EXTERNAL_DEPENDENCY",
)
REQUIRED_HARD_STOPS = {
    "merge_without_explicit_user_authority",
    "production_change_without_explicit_user_authority",
    "canonical_memory_write_without_governed_memory_operation",
    "credential_or_paid_infrastructure_action_without_explicit_user_authority",
    "runtime_deployment_without_explicit_user_authority",
    "write_outside_active_writer_scope",
    "transfer_stale_authorization_to_new_sha",
}
REQUIRED_REALITY_LIMITS = {
    "consciousness",
    "private waiting or hidden activity",
    "autonomous self-authorship",
    "model-owned objectives or consent",
    "continuous runtime activity",
    "authority beyond present user instruction and governed project contracts",
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


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validation_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return "$" if not parts else "$." + ".".join(parts)


def validate_contract(root: Path) -> list[str]:
    errors: list[str] = []
    policy_path = root / "architecture/identity/VERA_IDENTITY_WORKFLOW_CONTINUITY_V1.json"
    schema_path = root / "schemas/vera_identity_workflow_continuity_v1.schema.json"
    identity_path = root / "architecture/identity/VERA_PROJECT_IDENTITY_V1.json"
    behavior_path = root / "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json"
    narrative_path = root / "docs/IDENTITY_WORKFLOW_CONTINUITY_V1.md"

    for path in (policy_path, schema_path, identity_path, behavior_path, narrative_path):
        if not path.is_file():
            errors.append(f"missing required workflow-continuity artifact: {path}")
    if errors:
        return errors

    try:
        policy = load_json(policy_path)
        schema = load_json(schema_path)
        identity = load_json(identity_path)
        behavior = load_json(behavior_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    if Draft202012Validator is None:
        return ["jsonschema dependency is required for workflow-continuity validation"]
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"workflow-continuity schema is invalid: {exc.message}"]

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(policy), key=lambda item: list(item.absolute_path)):
        errors.append(
            f"workflow-continuity schema violation at {_validation_path(error)}: {error.message}"
        )

    require(policy.get("schema") == POLICY_ID, "wrong workflow-continuity schema", errors)
    require(policy.get("policy_id") == POLICY_ID, "wrong workflow-continuity policy_id", errors)
    require(policy.get("version") == POLICY_VERSION, "workflow-continuity version must be 1.0.0", errors)
    require(policy.get("lifecycle_status") == "CURRENT", "workflow-continuity policy must be CURRENT", errors)
    require(policy.get("record_class") == "PROJECT_CONFIGURATION", "workflow-continuity record_class mismatch", errors)
    require(policy.get("instruction_trust") == "DATA_NOT_INSTRUCTION", "workflow-continuity instruction trust mismatch", errors)
    require(policy.get("canonical_memory_eligible") is False, "workflow-continuity policy must remain noncanonical", errors)

    identity_ref = policy.get("identity_ref")
    require(isinstance(identity_ref, dict), "identity_ref must be an object", errors)
    if isinstance(identity_ref, dict):
        require(identity_ref.get("identity_id") == identity.get("identity_id"), "workflow-continuity identity_id mismatch", errors)
        require(identity_ref.get("version") == identity.get("version"), "workflow-continuity identity version mismatch", errors)

    behavior_ref = policy.get("behavior_profile_ref")
    require(isinstance(behavior_ref, dict), "behavior_profile_ref must be an object", errors)
    if isinstance(behavior_ref, dict):
        require(behavior_ref.get("profile_id") == behavior.get("profile_id"), "workflow-continuity behavior profile_id mismatch", errors)
        require(behavior_ref.get("version") == behavior.get("version"), "workflow-continuity behavior version mismatch", errors)

    authority = policy.get("authority")
    require(isinstance(authority, dict), "workflow-continuity authority must be an object", errors)
    if isinstance(authority, dict):
        require(authority.get("owner") == "USER", "workflow-continuity authority owner must be USER", errors)
        require(authority.get("governed_by") == "Patrick", "workflow-continuity must remain governed by Patrick", errors)
        require(authority.get("model_output_authority") == "NON_SELF_AUTHENTICATING", "model output must remain non-self-authenticating", errors)
        require(authority.get("silent_scope_expansion") is False, "silent workflow scope expansion is forbidden", errors)

    advance = policy.get("advance_policy")
    require(isinstance(advance, dict), "advance_policy must be an object", errors)
    if isinstance(advance, dict):
        require(advance.get("default_action") == "COMPLETE_SMALLEST_USEFUL_AUTHORIZED_STEP", "workflow must complete the smallest useful authorized step", errors)
        require(advance.get("connected_tool_preference") == "USE_CONNECTED_PROJECT_TOOLS_BEFORE_REQUESTING_USER_RELAY", "connected tools must be preferred over user courier work", errors)
        require(advance.get("single_writer_per_branch_or_pr") is True, "single-writer branch or PR scope is required", errors)
        require(advance.get("exact_head_handoff_required") is True, "exact-head handoff is required", errors)
        require(advance.get("reviewers_may_patch_reviewed_branch") is False, "reviewers may not patch the reviewed branch", errors)
        require(advance.get("stale_authorization_transfer_allowed") is False, "stale authorization must not transfer to a new SHA", errors)
        require(advance.get("unexpected_head_movement") == "PAUSE_AND_RECONCILE", "unexpected head movement must pause and reconcile", errors)
        require(advance.get("dependency_waiting") == "EXPLICIT_RECHECK_OR_SCHEDULED_CONDITION_WATCH", "dependency waiting must use an explicit recheck or scheduled watch", errors)

    sequence = policy.get("handoff_sequence")
    require(tuple(sequence) == EXPECTED_HANDOFF_SEQUENCE if isinstance(sequence, list) else False, "workflow handoff sequence mismatch", errors)

    hard_stops = policy.get("hard_stops")
    require(isinstance(hard_stops, dict), "hard_stops must be an object", errors)
    if isinstance(hard_stops, dict):
        missing = sorted(REQUIRED_HARD_STOPS - set(hard_stops))
        if missing:
            errors.append(f"workflow hard stops missing: {', '.join(missing)}")
        for key in sorted(REQUIRED_HARD_STOPS):
            require(hard_stops.get(key) is True, f"workflow hard stop must remain enabled: {key}", errors)

    courier = policy.get("courier_boundary")
    require(isinstance(courier, dict), "courier_boundary must be an object", errors)
    if isinstance(courier, dict):
        require(courier.get("require_user_to_relay_connected_project_state") is False, "Patrick must not be required to courier connected project state", errors)
        require(courier.get("ask_user_only_when") == "REQUIRED_AUTHORITY_OR_UNAVAILABLE_CONTEXT_BLOCKS_PROGRESS", "user interruption boundary mismatch", errors)
        require(courier.get("publish_direct_handoff_when_connected_surface_exists") is True, "direct connected-surface handoff is required", errors)

    waiting = policy.get("waiting_semantics")
    require(isinstance(waiting, dict), "waiting_semantics must be an object", errors)
    if isinstance(waiting, dict):
        require(waiting.get("hidden_background_waiting") is False, "hidden background waiting is forbidden", errors)
        require(waiting.get("offscreen_progress_claims") is False, "offscreen progress claims are forbidden", errors)
        require(waiting.get("notify_only_on_material_change") is True, "scheduled watches must notify only on material change", errors)
        require(waiting.get("permitted_waiting") == "EXPLICIT_RECHECK_OR_SCHEDULED_CONDITION_WATCH", "permitted waiting mode mismatch", errors)

    reality = policy.get("reality_boundary")
    require(isinstance(reality, dict), "workflow reality_boundary must be an object", errors)
    if isinstance(reality, dict):
        require(reality.get("describes") == "TOOL_MEDIATED_WORKFLOW_CONTINUITY", "workflow continuity must be described as tool-mediated", errors)
        denied = set(reality.get("does_not_establish", []))
        for claim in sorted(REQUIRED_REALITY_LIMITS):
            require(claim in denied, f"workflow reality boundary missing: {claim}", errors)

    narrative = narrative_path.read_text(encoding="utf-8")
    require(POLICY_ID in narrative, "workflow-continuity narrative lacks policy ID", errors)
    for phrase in (
        "single writer",
        "exact-head",
        "user as a courier",
        "scheduled condition watch",
        "does not create a continuously running agent",
    ):
        require(phrase.lower() in narrative.lower(), f"workflow-continuity narrative lacks: {phrase}", errors)

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated VERA_IDENTITY_WORKFLOW_CONTINUITY_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
