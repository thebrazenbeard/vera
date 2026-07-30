from __future__ import annotations

import json

from tul_fixture.proof import build_proof_artifact, write_proof_artifact


def _walk_strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_strings(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_strings(child)
    elif isinstance(value, str):
        yield value


def test_build_proof_artifact_requires_complete_host_controlled_proof():
    artifact = build_proof_artifact()

    assert artifact["artifact"] == "TUL Instrumented Host Fixture Proof"
    assert artifact["fixture_version"] == "0.1.0"
    assert artifact["contract_baseline"] == "TUL Host Capability Requirement v0.1.3"
    assert artifact["generated_at"] == "deterministic-fixture"
    assert artifact["proof_classification"] == "FULL"

    assert artifact["scope"] == {
        "host_controlled_fixture": True,
        "native_chatgpt_support_proven": False,
        "native_codex_support_proven": False,
        "semantic_payload_stored": False,
        "storage_used": False,
    }


def test_positive_case_proves_exact_lifecycle_without_semantic_payload():
    positive = build_proof_artifact()["positive_full_lifecycle"]

    assert positive["semantic_payload_included"] is False
    assert positive["inbound"]["time_semantics"] == "MESSAGE_CREATION"
    assert positive["generation"]["time_semantics"] == "GENERATION_INVOCATION_START"
    assert positive["assistant"]["time_semantics"] == "MESSAGE_CREATION"
    assert positive["assistant"]["capture_mode"] == "POST_RESPONSE"

    evaluation = positive["evaluation"]
    assert evaluation["capability"] == "FULL"
    assert evaluation["causal_binding"] == "EXACT"
    assert evaluation["inbound_to_generation"]["status"] == "EXACT"
    assert evaluation["inbound_to_generation"]["value_seconds"] == 2.0
    assert evaluation["inbound_to_assistant"]["status"] == "EXACT"
    assert evaluation["inbound_to_assistant"]["value_seconds"] == 5.0


def test_negative_cases_preserve_conflict_unavailable_and_approximation():
    negative = build_proof_artifact()["negative_cases"]

    mismatch = negative["causal_binding_mismatch"]
    assert mismatch["causal_binding"] == "CONFLICTED"
    assert mismatch["inbound_to_generation"]["status"] == "CONFLICTED"
    assert mismatch["inbound_to_assistant"]["status"] == "CONFLICTED"

    rejected = negative["codex_turn_metadata_rejected"]
    assert rejected["status"] == "CONFLICTED"
    assert any("CODEX_TURN_METADATA" in reason for reason in rejected["reasons"])

    missing = negative["missing_inbound_creation"]
    assert missing["status"] == "UNAVAILABLE"
    assert missing["value_seconds"] is None

    approximation = negative["documented_approximation"]
    assert approximation["status"] == "APPROXIMATE"
    assert approximation["value_seconds"] == 7.0
    assert any("error model" in reason for reason in approximation["reasons"])


def test_write_proof_artifact_is_deterministic_and_excludes_fixture_text(tmp_path):
    path = tmp_path / "proof.json"

    first = write_proof_artifact(path)
    first_bytes = path.read_bytes()
    second = write_proof_artifact(path)
    second_bytes = path.read_bytes()

    assert first == second
    assert first_bytes == second_bytes
    assert json.loads(first_bytes) == first

    serialized_strings = "\n".join(_walk_strings(first)).lower()
    assert "hello" not in serialized_strings
    assert "reply" not in serialized_strings
    assert "user_text" not in serialized_strings
    assert "model_output" not in serialized_strings
