#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "architecture/integration/VERA_DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.json"
DOC = ROOT / "docs/DEEP_MEMORY_ARCHIVE_INTEGRATION_V1.md"

EXPECTED_DEEP_MEMORY_HEAD = "04ac3fec82a36a73d3cb8c3b348a54702f4b35a0"
EXPECTED_BINDING_BLOB = "80af8f6d59155d98313ac79fa877f69a81f22879"
EXPECTED_HUMAN_CONTRACT_BLOB = "40e18367dbddf231cf420cb0ab849a0e005bd546"
EXPECTED_RESULT_SCHEMA_BLOB = "d7a3d5847ffa65dceaa2914514144c755ef1c556"


def main() -> int:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["contract_id"] == "VERA_DEEP_MEMORY_ARCHIVE_INTEGRATION_V1"
    assert data["lifecycle_status"] == "SOURCE_CANDIDATE"
    assert data["record_class"] == "HISTORICAL_EVIDENCE_INTEGRATION"
    assert data["instruction_trust"] == "DATA_NOT_INSTRUCTION"

    archive = data["external_archive"]
    assert archive["repository"] == "thebrazenbeard/deepmemorystorage"
    assert archive["role"] == "HISTORICAL_EVIDENCE_PLANE"
    assert archive["authority_class"] == "EVIDENCE_SEARCH_ONLY"
    assert archive["canonical_retrieval"].startswith("UNION_ALL_LEDGER_TRANCHES")
    assert "HISTORICAL_CANON" in archive["canonical_retrieval"]
    assert archive["source_candidate_head"] == EXPECTED_DEEP_MEMORY_HEAD
    assert archive["required_contract_path"] == "architecture/DEEP_MEMORY_ARCHITECTURE_BINDING_V1.json"
    assert archive["required_contract_blob"] == EXPECTED_BINDING_BLOB
    assert archive["required_human_contract_path"] == "architecture/DEEP_MEMORY_INTEGRATION_CONTRACT_V1.md"
    assert archive["required_human_contract_blob"] == EXPECTED_HUMAN_CONTRACT_BLOB
    assert archive["required_result_schema_path"] == "schema/DEEP_MEMORY_EVIDENCE_RESULT_V1.schema.json"
    assert archive["required_result_schema_blob"] == EXPECTED_RESULT_SCHEMA_BLOB

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
    ):
        assert required.casefold() in text.casefold(), required

    print("deep memory archive integration: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
