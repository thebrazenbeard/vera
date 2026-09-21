#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/integration/VERA_DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.json"
DOC = ROOT / "docs/DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.md"
WORKFLOW = ROOT / ".github/workflows/deep-memory-archive-integration.yml"
VENDORED_RESULT_SCHEMA = ROOT / "architecture/integration/vendor/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json"
VENDORED_BINDING = ROOT / "architecture/integration/vendor/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json"
VENDORED_HUMAN_CONTRACT = ROOT / "architecture/integration/vendor/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md"

EXPECTED_REVIEWED_PROVIDER_HEAD = "539b5988e0913130427da3d1098d84592d1122cf"
EXPECTED_MERGED_PROVIDER_COMMIT = "f073feb409f71a0fdea7baa9053e54bcf8ed89a0"
EXPECTED_BINDING_BLOB = "a951cbfad09e2dcc3685a04e47680df16a6edfc9"
EXPECTED_HUMAN_CONTRACT_BLOB = "35f9be1c67d5898724ac85256af8cc9e667039f1"
EXPECTED_RESULT_SCHEMA_BLOB = "d9c0b09e16557c4871b2095bdf06962a3562ebf0"


def external_action_pins(workflow_text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in workflow_text.splitlines():
        match = re.match(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", line)
        if match is None:
            continue
        ref = match.group(1).strip("\"'")
        if ref.startswith("./"):
            continue
        if "@" not in ref:
            raise AssertionError(f"external action ref is unpinned: {ref}")
        action, pin = ref.rsplit("@", 1)
        if not action or re.fullmatch(r"[0-9a-f]{40}", pin) is None:
            raise AssertionError(f"external action ref is not immutable: {ref}")
        pins[action] = pin
    return pins


def git_blob_sha1(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    completed = subprocess.run(
        ["git", "hash-object", f"--path={relative}", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    digest = completed.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{40}", digest), digest
    return digest


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["contract_id"] == "VERA_DEEP_MEMORY_ARCHIVE_INTEGRATION_V1"
    assert data["lifecycle_status"] == "SOURCE_CANDIDATE"
    assert data["record_class"] == "HISTORICAL_EVIDENCE_INTEGRATION"
    assert data["instruction_trust"] == "DATA_NOT_INSTRUCTION"

    ci = data["ci_validation"]
    expected_ci_pins = {
        "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
        "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    }
    assert ci["external_action_pins"] == expected_ci_pins
    assert ci["external_action_ref_policy"] == "IMMUTABLE_COMMIT_SHA_ONLY"
    assert ci["workflow_vendor_trigger"] == "architecture/integration/vendor/**"
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    assert external_action_pins(workflow_text) == expected_ci_pins
    assert workflow_text.count('      - "architecture/integration/vendor/**"') == 2

    archive = data["external_archive"]
    assert archive["repository"] == "thebrazenbeard/deepmemorystorage"
    assert archive["role"] == "HISTORICAL_EVIDENCE_PLANE"
    assert archive["authority_class"] == "EVIDENCE_SEARCH_ONLY"
    assert archive["canonical_retrieval"].startswith("UNION_ALL_LEDGER_TRANCHES")
    assert "HISTORICAL_CANON" in archive["canonical_retrieval"]
    assert archive["reviewed_provider_head"] == EXPECTED_REVIEWED_PROVIDER_HEAD
    assert archive["source_merged_commit"] == EXPECTED_MERGED_PROVIDER_COMMIT
    assert archive["source_state"] == "MERGED_SOURCE"
    assert "source_candidate_head" not in archive
    assert archive["required_contract_path"] == "architecture/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json"
    assert archive["required_contract_blob"] == EXPECTED_BINDING_BLOB
    assert archive["required_human_contract_path"] == "architecture/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md"
    assert archive["required_human_contract_blob"] == EXPECTED_HUMAN_CONTRACT_BLOB
    assert archive["required_result_schema_path"] == "schema/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json"
    assert archive["required_result_schema_blob"] == EXPECTED_RESULT_SCHEMA_BLOB
    assert archive["vendored_result_schema_path"] == "architecture/integration/vendor/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json"
    assert archive["vendored_contract_path"] == "architecture/integration/vendor/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json"
    assert archive["vendored_human_contract_path"] == "architecture/integration/vendor/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md"
    assert VENDORED_RESULT_SCHEMA.is_file()
    assert VENDORED_BINDING.is_file()
    assert VENDORED_HUMAN_CONTRACT.is_file()
    assert git_blob_sha1(VENDORED_RESULT_SCHEMA) == EXPECTED_RESULT_SCHEMA_BLOB
    assert git_blob_sha1(VENDORED_BINDING) == EXPECTED_BINDING_BLOB
    assert git_blob_sha1(VENDORED_HUMAN_CONTRACT) == EXPECTED_HUMAN_CONTRACT_BLOB
    provider_binding = json.loads(VENDORED_BINDING.read_text(encoding="utf-8"))
    assert provider_binding["schema"] == "VERA_DEEP_MEMORY_ARCHITECTURE_BINDING_V1"
    assert provider_binding["role"] == "HISTORICAL_EVIDENCE_PLANE"
    assert provider_binding["authority_class"] == "EVIDENCE_SEARCH_ONLY"
    assert provider_binding["current_authority"] is False
    assert provider_binding["automatic_runtime_consumption"] is False
    provider_validation = provider_binding["validation"]
    assert provider_validation["latest_receipt_exact_lineage_requires_corpus_subject_digest"] is True
    assert provider_validation["latest_receipt_row_count_match_is_not_exact_lineage"] is True
    assert provider_validation["receipt_continues_policy"] == "IMMEDIATE_NUMERIC_PREDECESSOR_ONLY"
    assert provider_validation["receipt_path_identity"] == "FILENAME_STEM_MUST_EQUAL_PASS_ID"
    assert provider_validation["workflow_external_actions"] == "IMMUTABLE_COMMIT_SHA_ONLY"
    assert provider_validation["workflow_external_action_ref_scan"] == "ALL_EXTERNAL_USES_REFS_MUST_MATCH_PIN_REGISTRY"
    human_contract = VENDORED_HUMAN_CONTRACT.read_text(encoding="utf-8").casefold()
    for phrase in (
        "immediately preceding numeric pass",
        "every external github action",
        "row-count agreement alone",
        "historical evidence plane",
    ):
        assert phrase in human_contract, phrase
    provider_schema = json.loads(VENDORED_RESULT_SCHEMA.read_text(encoding="utf-8"))
    assert provider_schema["$id"] == "VERA_DEEP_MEMORY_EVIDENCE_RESULT_V1"
    assert "authorized_privacy_scopes" in provider_schema["required"]
    assert "retrieved_at" in provider_schema["required"]
    provider_required = set(provider_schema["properties"]["results"]["items"]["required"])
    vera_required = {
        "memory_id",
        "memory_class",
        "stored_historical_canonicity",
        "historical_canonicity",
        "event_time",
        "recorded_at",
        "recorded_at_status",
        "chronology_semantics",
        "provenance_ceiling",
        "privacy_scope",
        "currentness_rule",
        "governed_memory_admission",
        "source_ids",
        "ledger_path",
        "overlay_privacy_semantics",
        "result_semantics",
    }
    assert vera_required <= provider_required, sorted(vera_required - provider_required)
    provider_properties = provider_schema["properties"]["results"]["items"]["properties"]
    for overlay_name in ("historical_canon_overlays", "amendments", "classification_corrections"):
        overlay_required = set(provider_properties[overlay_name]["items"]["required"])
        assert {"recorded_at", "recorded_at_status", "effective_from", "effective_from_status", "chronology_semantics"} <= overlay_required

    current = data["current_memory_plane"]
    assert current["route"] == "workstream/memory"
    assert current["contract_id"] == "VERA_MEMORY_CROSS_CHAT_CONTRACT_V1"
    assert current["automatic_archive_projection"] is False
    assert current["automatic_archive_admission"] is False

    bridge = data["bridge"]
    assert bridge["mode"] == "EXPLICIT_REVIEW_ONLY"
    assert bridge["automatic"] is False
    assert bridge["requires_separate_authority"] is True

    retrieval = data["retrieval"]
    assert retrieval["operation"] == "EVIDENCE_SEARCH"
    assert retrieval["result_class"] == "HISTORICAL_EVIDENCE"
    assert retrieval["result_schema"] == "VERA_DEEP_MEMORY_EVIDENCE_RESULT_V1"
    assert retrieval["privacy_default"] == "FAIL_CLOSED_EXACT_AUTHORIZED_SCOPE"
    assert retrieval["overlay_privacy"] == "INHERIT_TARGET_UNLESS_EXPLICIT_SCOPE_REQUIRES_SEPARATE_AUTHORIZATION"
    assert "stored_vs_effective_historical_canonicity" in retrieval["required_boundaries"]
    assert "event_time_vs_record_time_vs_retrieval_time" in retrieval["required_boundaries"]
    assert retrieval["archive_audit_override"] == "EXPLICIT_ARCHIVE_AUDIT_ALL_PRIVATE_REPOSITORY_ONLY"

    assert data["execution_authorized"] is False
    assert data["canonical_memory_eligible"] is False
    assert data["merge_authority"] == "EXTERNAL_EXPLICIT_AUTHORIZATION"
    assert data["production_authority"] == "EXTERNAL_EXPLICIT_AUTHORIZATION"

    required_non_effects = {
        "NO_PRODUCTION_MIGRATION",
        "NO_PROVIDER_MUTATION",
        "NO_CURRENT_MEMORY_WRITE",
        "NO_R9B0_PROMOTION",
        "NO_RUNTIME_INSTALL",
        "NO_PRIVATE_PUBLICATION",
    }
    assert set(data["non_effects"]) == required_non_effects
    assert DOC.is_file()

    text = DOC.read_text(encoding="utf-8")
    for required in (
        "historical evidence plane",
        "current governed memory",
        "no automatic Deep Memory -> current memory promotion",
        "CANONICAL_HISTORY",
        "EVIDENCE_SEARCH",
        "Pass 010",
        "conclusion derived only from that overlay",
    ):
        assert required.casefold() in text.casefold(), required

    print("deep memory archive integration: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
