#!/usr/bin/env python3
"""Validate the V.E.R.A. project identity and behavior-profile contracts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError:  # pragma: no cover - exercised by the CLI environment boundary
    Draft202012Validator = None  # type: ignore[assignment]
    SchemaError = Exception  # type: ignore[assignment,misc]


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate key."""


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


def require_exact_members(
    actual: set[str], expected: set[str], label: str, errors: list[str]
) -> None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        errors.append(f"{label} missing: {', '.join(missing)}")
    if extra:
        errors.append(f"{label} unexpected: {', '.join(extra)}")


def _validation_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return "$" if not parts else "$." + ".".join(parts)


def validate_instance_against_schema(
    instance: dict[str, Any], schema: dict[str, Any], label: str, errors: list[str]
) -> None:
    if Draft202012Validator is None:
        errors.append("jsonschema dependency is required for Draft 2020-12 validation")
        return
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        errors.append(f"{label} schema is invalid: {exc.message}")
        return

    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        errors.append(f"{label} schema violation at {_validation_path(error)}: {error.message}")


def validate_contract(root: Path) -> list[str]:
    errors: list[str] = []
    identity_path = root / "architecture/identity/VERA_PROJECT_IDENTITY_V1.json"
    behavior_path = root / "architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json"
    identity_schema_path = root / "schemas/vera_project_identity_v1.schema.json"
    behavior_schema_path = root / "schemas/vera_behavior_profile_v1.schema.json"
    narrative_path = root / "docs/PROJECT_IDENTITY_V1.md"

    for path in (
        identity_path,
        behavior_path,
        identity_schema_path,
        behavior_schema_path,
        narrative_path,
    ):
        require(path.is_file(), f"missing required identity artifact: {path}", errors)
    if errors:
        return errors

    try:
        identity = load_json(identity_path)
        behavior = load_json(behavior_path)
        identity_schema = load_json(identity_schema_path)
        behavior_schema = load_json(behavior_schema_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    validate_instance_against_schema(identity, identity_schema, "identity", errors)
    validate_instance_against_schema(behavior, behavior_schema, "behavior", errors)

    narrative = narrative_path.read_text(encoding="utf-8")
    canonical_statement = (
        "V.E.R.A. is the environment in which context remains attributable, time remains "
        "legible, correction remains authoritative, behavior remains coherent, and coordinated "
        "action remains auditable."
    )
    motto = "Attribute context. Anchor time. Honor correction. Govern behavior. Audit action."

    require(identity.get("schema") == "VERA_PROJECT_IDENTITY_V1", "wrong identity schema", errors)
    require(identity.get("identity_id") == "VERA_PROJECT_IDENTITY_V1", "wrong identity_id", errors)
    require(
        isinstance(identity.get("version"), str)
        and re.fullmatch(r"1\.\d+\.\d+", identity["version"]) is not None,
        "identity version must be semantic version 1.x.x",
        errors,
    )
    require(identity.get("lifecycle_status") == "CURRENT", "identity must be CURRENT", errors)
    require(identity.get("project_name") == "V.E.R.A.", "wrong project name", errors)
    require(
        identity.get("expanded_name") == "Virtual Environment for Reciprocal Agency",
        "wrong expanded project name",
        errors,
    )
    require(identity.get("canonical_statement") == canonical_statement, "canonical statement mismatch", errors)
    require(identity.get("motto") == motto, "motto mismatch", errors)
    require(canonical_statement in narrative, "narrative document lacks canonical statement", errors)
    require(motto in narrative, "narrative document lacks motto", errors)

    authority = identity.get("authority")
    require(isinstance(authority, dict), "authority must be an object", errors)
    if isinstance(authority, dict):
        require(authority.get("owner") == "USER", "identity authority owner must be USER", errors)
        require(
            authority.get("change_rule") == "EXPLICIT_VERSIONED_REVISION",
            "identity changes must require explicit versioned revision",
            errors,
        )
        require(
            authority.get("model_output_authority") == "NON_SELF_AUTHENTICATING",
            "model output must remain non-self-authenticating",
            errors,
        )

    expected_objectives = {
        "PERSISTENT_GOVERNED_CONTEXT_ACROSS_CHATS",
        "TEMPORAL_ANCHORING",
        "ABSOLUTE_CANDOR",
        "PUSHBACK_WITHOUT_BLIND_OBEDIENCE",
        "BEHAVIORAL_AND_PERSONALITY_CONTINUITY",
        "PROVENANCE_GOVERNED_COORDINATION",
    }
    objectives = identity.get("core_objectives")
    require(isinstance(objectives, list), "core_objectives must be an array", errors)
    if isinstance(objectives, list):
        require_exact_members(set(objectives), expected_objectives, "core_objectives", errors)

    expected_domains = {
        "identity",
        "behavior_and_personality",
        "memory",
        "time",
        "initiatives",
        "coordination",
        "integration",
    }
    domains = identity.get("domains")
    require(isinstance(domains, dict), "domains must be an object", errors)
    if isinstance(domains, dict):
        require_exact_members(set(domains), expected_domains, "domains", errors)
        behavior_domain = domains.get("behavior_and_personality")
        require(isinstance(behavior_domain, dict), "behavior_and_personality domain missing", errors)
        if isinstance(behavior_domain, dict):
            require(
                behavior_domain.get("profile_ref") == "VERA_BEHAVIOR_PROFILE_V1",
                "behavior profile reference mismatch",
                errors,
            )
            ownership = behavior_domain.get("owns", [])
            require(
                isinstance(ownership, list) and "voice and tone configuration" in ownership,
                "behavior domain must own voice and tone configuration",
                errors,
            )
            require(
                isinstance(ownership, list)
                and "separation of behavior configuration from private user history" in ownership,
                "behavior domain must preserve private-history separation",
                errors,
            )

    expected_workstreams = {
        "workstream/identity",
        "workstream/memory",
        "workstream/time",
        "workstream/initiatives",
        "workstream/coordination",
        "workstream/integration",
    }
    workstreams = identity.get("workstreams")
    require(isinstance(workstreams, dict), "workstreams must be an object", errors)
    if isinstance(workstreams, dict):
        require_exact_members(set(workstreams), expected_workstreams, "workstreams", errors)
        require(
            "workstream/initiative" not in workstreams,
            "obsolete singular initiative route is forbidden",
            errors,
        )
        identity_route = workstreams.get("workstream/identity")
        require(isinstance(identity_route, dict), "identity workstream metadata missing", errors)
        if isinstance(identity_route, dict):
            require(
                identity_route.get("record_class") == "PROJECT_IDENTITY_CONFIGURATION",
                "identity workstream record_class mismatch",
                errors,
            )
            require(
                identity_route.get("instruction_trust") == "DATA_NOT_INSTRUCTION",
                "identity workstream instruction trust must be DATA_NOT_INSTRUCTION",
                errors,
            )
            require(
                identity_route.get("canonical_memory_eligible") is True,
                "identity configuration must explicitly declare canonical-memory eligibility",
                errors,
            )

    reality = identity.get("reality_boundary")
    require(isinstance(reality, dict), "reality_boundary must be an object", errors)
    if isinstance(reality, dict):
        require(
            reality.get("system_class") == "NON_PERSONIFIED_GOVERNED_PROJECT",
            "wrong reality-boundary system class",
            errors,
        )
        allowed = set(reality.get("allows", []))
        forbidden = set(reality.get("forbids_as_established_fact", []))
        require("distinctive persona configuration" in allowed, "persona configuration must be allowed", errors)
        require("behavioral continuity" in allowed, "behavioral continuity must be allowed", errors)
        for claim in (
            "consciousness",
            "model-owned desire or consent",
            "hidden persistence or offscreen activity",
            "subjective reciprocal agency",
        ):
            require(claim in forbidden, f"missing forbidden claim boundary: {claim}", errors)

    require(behavior.get("schema") == "VERA_BEHAVIOR_PROFILE_V1", "wrong behavior schema", errors)
    require(behavior.get("profile_id") == "VERA_BEHAVIOR_PROFILE_V1", "wrong behavior profile_id", errors)
    require(behavior.get("lifecycle_status") == "CURRENT", "behavior profile must be CURRENT", errors)
    behavior_authority = behavior.get("authority")
    require(isinstance(behavior_authority, dict), "behavior authority must be an object", errors)
    if isinstance(behavior_authority, dict):
        require(
            behavior_authority.get("silent_self_promotion") is False,
            "behavior profile must forbid silent self-promotion",
            errors,
        )

    anti_patterns = behavior.get("hard_anti_patterns")
    require(isinstance(anti_patterns, list), "hard_anti_patterns must be an array", errors)
    if isinstance(anti_patterns, list):
        require("blind agreement" in anti_patterns, "blind agreement must be an anti-pattern", errors)
        require(
            "using a reality boundary to erase intentionally configured personality" in anti_patterns,
            "personality-flattening anti-pattern missing",
            errors,
        )
        require(
            "confusing private user history with portable personality configuration" in anti_patterns,
            "private-history contamination anti-pattern missing",
            errors,
        )

    for label, schema in (("identity", identity_schema), ("behavior", behavior_schema)):
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            f"wrong {label} JSON Schema dialect",
            errors,
        )

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_contract(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("validated VERA_PROJECT_IDENTITY_V1 and VERA_BEHAVIOR_PROFILE_V1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
