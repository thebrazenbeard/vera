from __future__ import annotations

from copy import deepcopy
import unittest

from runtime_cohesion.deep_memory_evidence import (
    ADMISSION_REVIEW,
    DeepMemoryEvidenceAdapter,
    EvidenceAuthorizationError,
    EvidenceContractError,
    EvidenceSearchRequest,
    prepare_historical_admission_review,
)


def row(memory_id: str, privacy_scope: str = "PRIVATE_AUTOBIOGRAPHICAL") -> dict:
    return {
        "score": 9,
        "memory_id": memory_id,
        "memory_class": "AUTOBIOGRAPHICAL",
        "stored_historical_canonicity": "CANONICAL_HISTORY",
        "historical_canonicity": "CANONICAL_HISTORY",
        "event_time": {"value": "2026-08-01", "precision": "DAY"},
        "recorded_at": "2026-08-02T12:00:00Z",
        "recorded_at_status": "SOURCE_RECORDED",
        "chronology_semantics": "EVENT_TIME_RECORD_TIME_EFFECTIVE_TIME_RETRIEVAL_TIME_SEPARATE",
        "observed_event": {"text": "historical event"},
        "participant_interpretation_at_time": {"text": "then-current interpretation"},
        "later_reevaluation": {"text": "later interpretation"},
        "reality_boundary": {"class": "USER_REPORTED"},
        "provenance_ceiling": {"max_claim": "HISTORICAL_EVIDENCE"},
        "privacy_scope": privacy_scope,
        "currentness_rule": {"rule": "HISTORICAL_NOT_CURRENT"},
        "governed_memory_admission": {"status": "NOT_ADMITTED"},
        "source_ids": [f"source:{memory_id}"],
        "ledger_path": f"ledger/{memory_id}.jsonl",
        "ledger_line": 1,
        "historical_canon_overlays": [
            {
                "recorded_at": "2026-08-03T12:00:00Z",
                "recorded_at_status": "SOURCE_RECORDED",
                "effective_from": "2026-08-01T00:00:00Z",
                "effective_from_status": "SOURCE_RECORDED",
                "chronology_semantics": "EVENT_TIME_RECORD_TIME_EFFECTIVE_TIME_RETRIEVAL_TIME_SEPARATE",
            }
        ],
        "amendments": [],
        "classification_corrections": [],
        "overlay_privacy_semantics": "OVERLAY_INHERITS_TARGET_PRIVACY_UNLESS_EXPLICIT_SCOPE_REQUIRES_SEPARATE_AUTHORIZATION",
        "result_semantics": "HISTORICAL_EVIDENCE_ONLY_NOT_CURRENT_MEMORY_OR_AUTHORITY",
    }


def result(query: str, rows: list[dict], scopes=None) -> dict:
    if scopes is None:
        scopes = ["PRIVATE_AUTOBIOGRAPHICAL"]
    return {
        "schema": "VERA_DEEP_MEMORY_EVIDENCE_RESULT_V1",
        "query": query,
        "privacy_mode": "AUTHORIZED_SCOPE_FILTER",
        "retrieved_at": "2026-09-21T19:30:00Z",
        "authorized_privacy_scopes": scopes,
        "count": len(rows),
        "results": rows,
    }


class RecordingTransport:
    def __init__(self, response: dict):
        self.response = response
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        return deepcopy(self.response)


class DeepMemoryEvidenceAdapterTests(unittest.TestCase):
    def adapter(self, response: dict):
        transport = RecordingTransport(response)
        return DeepMemoryEvidenceAdapter(transport), transport

    def test_missing_privacy_authorization_fails_closed(self):
        with self.assertRaises(EvidenceAuthorizationError):
            EvidenceSearchRequest(query="Yeshua", authorized_privacy_scopes=())

    def test_registry_discovers_external_provider_not_memory_owner(self):
        adapter, _ = self.adapter(result("x", []))
        binding = adapter.provider_binding
        self.assertEqual(binding["provider_class"], "EXTERNAL_EVIDENCE_PROVIDER")
        self.assertEqual(binding["operations"], ["EVIDENCE_SEARCH"])
        self.assertFalse(binding["canonical_memory_transfer"])
        self.assertFalse(binding["execution_authorized"])
        self.assertFalse(binding["runtime_install_authorized"])

    def test_transport_is_pinned_to_exact_merged_provider_source(self):
        adapter, transport = self.adapter(result("history", [row("m1")]))
        request = EvidenceSearchRequest(
            query="history",
            authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
        )
        batch = adapter.search(request)
        self.assertEqual(batch.count, 1)
        call = transport.calls[0]
        self.assertEqual(call["operation"], "EVIDENCE_SEARCH")
        binding = call["provider_source_binding"]
        self.assertEqual(binding["repository"], "thebrazenbeard/deepmemorystorage")
        self.assertEqual(binding["commit"], "f073feb409f71a0fdea7baa9053e54bcf8ed89a0")
        self.assertEqual(len(binding["bindings"]), 3)
        for forbidden in (
            "model", "model_id", "chat", "chat_id",
            "session", "session_id", "branch", "branch_id",
        ):
            self.assertNotIn(forbidden, call)

    def test_provider_cannot_widen_authorized_scopes(self):
        response = result(
            "history",
            [row("m1")],
            scopes=["PRIVATE_AUTOBIOGRAPHICAL", "SECRET_OTHER_SCOPE"],
        )
        adapter, _ = self.adapter(response)
        request = EvidenceSearchRequest(
            query="history",
            authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
        )
        with self.assertRaises(EvidenceAuthorizationError):
            adapter.search(request)

    def test_explicit_overlay_scope_must_be_authorized(self):
        bad_row = row("m1")
        bad_row["historical_canon_overlays"][0]["privacy_scope"] = "SECRET_OTHER_SCOPE"
        adapter, _ = self.adapter(result("history", [bad_row]))
        request = EvidenceSearchRequest(
            query="history",
            authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
        )
        with self.assertRaises(EvidenceAuthorizationError):
            adapter.search(request)

    def test_unknown_row_privacy_scope_fails_closed(self):
        bad_row = row("m1")
        bad_row["privacy_scope"] = None
        adapter, _ = self.adapter(result("history", [bad_row]))
        request = EvidenceSearchRequest(
            query="history",
            authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
        )
        with self.assertRaises(EvidenceAuthorizationError):
            adapter.search(request)

    def test_result_count_is_enforced(self):
        response = result("history", [row("m1")])
        response["count"] = 7
        adapter, _ = self.adapter(response)
        request = EvidenceSearchRequest(
            query="history",
            authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
        )
        with self.assertRaises(EvidenceContractError):
            adapter.search(request)

    def test_no_newest_wins_collapse_or_temporal_rewrite(self):
        older = row("older")
        newer = row("newer")
        older["recorded_at"] = "2026-08-10T00:00:00Z"
        newer["recorded_at"] = "2026-09-10T00:00:00Z"
        adapter, _ = self.adapter(result("history", [newer, older]))
        batch = adapter.search(
            EvidenceSearchRequest(
                query="history",
                authorized_privacy_scopes=("PRIVATE_AUTOBIOGRAPHICAL",),
            )
        )
        self.assertEqual([item["memory_id"] for item in batch.results], ["newer", "older"])
        self.assertEqual(batch.results[1]["event_time"], older["event_time"])
        self.assertEqual(
            batch.claim_ceiling,
            "HISTORICAL_EVIDENCE_ONLY_NOT_CURRENT_MEMORY_OR_AUTHORITY",
        )
        self.assertFalse(batch.canonical_memory_transfer)
        self.assertFalse(batch.execution_authorized)

    def test_archive_audit_requires_separate_explicit_authorization(self):
        with self.assertRaises(EvidenceAuthorizationError):
            EvidenceSearchRequest(
                query="audit",
                authorized_privacy_scopes=(),
                privacy_mode="EXPLICIT_ARCHIVE_AUDIT_ALL",
            )

    def test_admission_bridge_requires_separate_authority_and_receipt(self):
        item = row("m1")
        with self.assertRaises(ValueError):
            prepare_historical_admission_review(
                item,
                authority_ref="",
                receipt_ref="receipt:1",
            )
        review = prepare_historical_admission_review(
            item,
            authority_ref="patrick:explicit-review:20260921",
            receipt_ref="review-receipt:1",
        )
        self.assertEqual(review.operation, ADMISSION_REVIEW)
        self.assertEqual(review.memory_id, "m1")
        self.assertEqual(review.source_ids, ("source:m1",))
        self.assertEqual(review.event_time, item["event_time"])
        self.assertFalse(review.current_memory_write_performed)
        self.assertTrue(review.requires_separate_current_memory_write_authority)


if __name__ == "__main__":
    unittest.main()
