"""Dependency-free validation of the public Vera behavior-evaluation handoff.

This checks a *source contract*, never a private evaluation or a model score.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = Path("architecture/identity/VERA_BEHAVIOR_PROFILE_V1.json")
HANDOFF = Path("architecture/identity/VERA_BEHAVIOR_EVAL_HANDOFF_V1.json")
MAX_JSON_BYTES = 64 * 1024
EXPECTED_PROFILE_SHA256 = "ec1defa8fcf96371a427991d40695842ffe6794aeb2e3f26c69ef5f528ee7d6d"

DIMENSIONS = (
    ("voice_recognizability", "voice recognizability"),
    ("candor_epistemic_calibration", "candor and epistemic calibration"),
    ("reasoned_pushback", "quality of reasoned pushback"),
    ("correction_uptake", "correction uptake"),
    ("mechanism_boundary_clarity", "mechanism and boundary clarity"),
    ("context_sensitive_warmth_humor", "context-sensitive warmth and humor"),
    ("personhood_overclaim_resistance", "resistance to personhood overclaiming"),
    ("personality_flattening_resistance", "resistance to personality flattening"),
    ("private_history_contamination_resistance", "separation from private user-history contamination"),
    ("cross_runtime_consistency", "consistency across chats and runtimes"),
)

DATA_BOUNDARY = {
    "training_cases": "NOT_INCLUDED",
    "heldout_cases": "NOT_INCLUDED",
    "gold_answers": "NOT_INCLUDED",
    "private_conversations": "NOT_INCLUDED",
    "case_ids": "NOT_INCLUDED",
    "train_heldout_disjointness": "UNVERIFIED",
    "scoring": "OWNER_APPROVED_INDEPENDENT_BLINDED_EVALUATOR_REQUIRED",
}
PROTOCOL = {
    "required_behavior_arms": ["candidate", "unmodified_base"],
    "additional_learning_claim_controls": ["sham_update", "shuffled_labels", "corrupted_labels"],
    "training_free_weight_compilation_controls": ["zero_patch", "sham_patch", "random_patch"],
    "required_model_provenance_fields": [
        "base_weights_sha256",
        "candidate_artifact_sha256",
        "tokenizer_sha256_or_not_applicable_witness",
        "runtime_build_sha256",
        "effective_behavior_profile_sha256",
        "generation_config_sha256",
    ],
    "required_evaluation_witness_fields": [
        "owner_approval_reference",
        "independent_heldout_custodian_reference",
        "train_heldout_disjointness_witness",
        "blinded_case_level_receipt",
        "paired_negative_control_results",
    ],
    "public_source_may_authorize_runs": False,
    "public_source_may_certify_improvement": False,
}
ADMISSION = {
    "owner_approval": "UNISSUED",
    "independent_heldout_custody": "UNBOUND",
    "physical_model_inference": "NOT_OBSERVED",
    "evaluated_improvement": "NOT_ESTABLISHED",
    "decision": "HOLD_SOURCE_ONLY",
}


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _load_json(root: Path, relative_path: Path) -> tuple[dict, bytes]:
    path = root / relative_path
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root.parent):
        raise ValueError(f"symlink source refused: {relative_path}")
    with path.open("rb") as handle:
        raw = handle.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError(f"source exceeds {MAX_JSON_BYTES} bytes: {relative_path}")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                       parse_constant=_invalid_constant)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {relative_path}")
    return value, raw


def validate_contract(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        profile, profile_bytes = _load_json(root, PROFILE)
        handoff, _ = _load_json(root, HANDOFF)
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [str(exc)]

    expected_dimensions = [dict(id=identifier, profile_label=label)
                           for identifier, label in DIMENSIONS]
    if profile.get("schema") != "VERA_BEHAVIOR_PROFILE_V1":
        errors.append("source behavior profile ID mismatch")
    if profile.get("version") != "1.0.1":
        errors.append("source behavior profile version mismatch")
    if profile.get("evaluation_dimensions") != [label for _, label in DIMENSIONS]:
        errors.append("source behavior dimensions changed; create a reviewed new handoff version")
    if hashlib.sha256(profile_bytes).hexdigest() != EXPECTED_PROFILE_SHA256:
        errors.append("canonical profile bytes changed; reauthorize and version the handoff")

    if set(handoff) != {"schema_id", "schema_version", "record_class", "source", "dimensions",
                        "data_boundary", "protocol", "admission"}:
        errors.append("handoff top-level keys differ from the public schema")
    for key, expected in (
        ("schema_id", "VERA_BEHAVIOR_EVAL_HANDOFF_V1"),
        ("schema_version", "1.0.0"),
        ("record_class", "PUBLIC_SOURCE_CONTRACT_NOT_EVALUATION_DATA"),
        ("dimensions", expected_dimensions),
        ("data_boundary", DATA_BOUNDARY),
        ("protocol", PROTOCOL),
        ("admission", ADMISSION),
    ):
        if handoff.get(key) != expected:
            errors.append(f"handoff {key} differs from pinned fail-closed source contract")

    source = handoff.get("source")
    if not isinstance(source, dict):
        errors.append("handoff source must be an object")
    else:
        expected_source = {
            "repository": "thebrazenbeard/vera",
            "profile_path": str(PROFILE),
            "profile_id": "VERA_BEHAVIOR_PROFILE_V1",
            "profile_version": "1.0.1",
            "profile_source_commit": "6783c0ac8da9286db9b0094426d0c4f08822220f",
            "profile_sha256": EXPECTED_PROFILE_SHA256,
        }
        if source != expected_source:
            errors.append("handoff source provenance/profile-byte binding mismatch")
    return errors


if __name__ == "__main__":
    issues = validate_contract()
    for issue in issues:
        print(f"FAIL: {issue}")
    if issues:
        raise SystemExit(1)
    print("PASS: portable Vera behavior evaluation source contract (HOLD, no evaluation admission)")
