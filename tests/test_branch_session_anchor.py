from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import inspect
import json
import unittest
from uuid import UUID, uuid4

from protocol.branch_session_anchor import (
    AnchorValidationError,
    AppendOnlyAnchorSet,
    IdempotencyConflict,
    calculate_elapsed,
    compute_content_hash,
    resolve_scope,
    stable_scope_id,
    validate_anchor,
)


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def exposed_identity(value: str) -> dict:
    return {"status": "EXPOSED", "value": value, "source": "PROVIDER_EXPOSED_ID"}


def unavailable_identity() -> dict:
    return {"status": "UNAVAILABLE", "value": None, "source": "PROVIDER_ID_UNAVAILABLE"}


def exact(timestamp: str) -> dict:
    return {
        "observed_at": timestamp,
        "precision": "EXACT",
        "lower_bound": None,
        "upper_bound": None,
        "source": "TOOL_EXPOSED_TIMESTAMP",
    }


def bounded(observed: str, lower: str, upper: str) -> dict:
    return {
        "observed_at": observed,
        "precision": "BOUNDED",
        "lower_bound": lower,
        "upper_bound": upper,
        "source": "USER_REPORTED_TIMESTAMP",
    }


def unavailable_time() -> dict:
    return {
        "observed_at": None,
        "precision": "UNKNOWN",
        "lower_bound": None,
        "upper_bound": None,
        "source": "EVENT_TIME_UNAVAILABLE",
    }


def finalize(value: dict) -> dict:
    value["content_hash"] = compute_content_hash(value)
    return value


def anchor(
    *,
    conversation: str = "conv-a",
    branch: str = "branch-a",
    kind: str = "ENTRY",
    exposed: bool = True,
    project_id: str = "vera-chatgpt-instance",
    scope_id: str | None = None,
    scope_instance_id: str | None = None,
    session_id: str | None = None,
    prior_anchor_id: str | None = None,
) -> dict:
    value = {
        "schema": "VERA_BRANCH_SESSION_ANCHOR_V1",
        "anchor_id": str(uuid4()),
        "project_id": project_id,
        "conversation_identity": exposed_identity(conversation) if exposed else unavailable_identity(),
        "branch_identity": exposed_identity(branch) if exposed else unavailable_identity(),
        "scope_mode": "STABLE" if exposed else "EPHEMERAL",
        "scope_id": scope_id or (
            stable_scope_id(project_id, conversation, branch) if exposed else str(uuid4())
        ),
        "scope_instance_id": scope_instance_id or str(uuid4()),
        "session_id": session_id or str(uuid4()),
        "checkpoint_id": None,
        "anchor_kind": kind,
        "entry_reason": "NEW_OR_RESUMED_CHAT" if kind == "ENTRY" else None,
        "exit_reason": None if kind == "ENTRY" else "BRANCH_HANDOFF",
        "exit_details": None,
        "prior_anchor_id": prior_anchor_id,
        "predecessor_checkpoint_evidence": None,
        "event_time": exact("2026-07-29T14:50:00+00:00"),
        "source": "VISIBLE_RUNTIME",
        "content_hash": "0" * 64,
        "idempotency_key": digest(str(uuid4())),
        "payload": {},
    }
    return finalize(value)


def material_exit_from(predecessor: dict, *, reason: str = "BRANCH_HANDOFF") -> dict:
    value = anchor(
        conversation=predecessor["conversation_identity"]["value"] or "unused",
        branch=predecessor["branch_identity"]["value"] or "unused",
        kind="MATERIAL_EXIT",
        exposed=predecessor["scope_mode"] == "STABLE",
        project_id=predecessor["project_id"],
        scope_id=predecessor["scope_id"],
        scope_instance_id=predecessor["scope_instance_id"],
        session_id=predecessor["session_id"],
        prior_anchor_id=predecessor["anchor_id"],
    )
    value["exit_reason"] = reason
    return finalize(value)


class IdentityEvidenceTests(unittest.TestCase):
    def test_project_conversation_branch_session_checkpoint_are_distinct(self):
        value = anchor()
        value["checkpoint_id"] = "checkpoint-001"
        finalize(value)
        validate_anchor(value)
        identities = {
            value["project_id"], value["conversation_identity"]["value"],
            value["branch_identity"]["value"], value["session_id"], value["checkpoint_id"],
        }
        self.assertEqual(5, len(identities))

    def test_stable_scope_requires_both_provider_ids(self):
        value = anchor()
        value["branch_identity"] = unavailable_identity()
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_missing_identity_source_is_rejected(self):
        value = anchor()
        del value["conversation_identity"]["source"]
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_fabricated_exposed_identity_source_is_rejected(self):
        value = anchor()
        value["conversation_identity"]["source"] = "MODEL_INFERRED"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_unavailable_identity_requires_matching_source(self):
        value = anchor(exposed=False)
        value["branch_identity"]["source"] = "PROVIDER_EXPOSED_ID"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_exposed_identity_rejects_unavailable_source(self):
        value = anchor()
        value["branch_identity"]["source"] = "PROVIDER_ID_UNAVAILABLE"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_event_time_source_is_required(self):
        value = anchor()
        del value["event_time"]["source"]
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_fabricated_event_time_source_is_rejected(self):
        value = anchor()
        value["event_time"]["source"] = "MODEL_CLOCK"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_event_time_source_must_match_precision(self):
        value = anchor()
        value["event_time"]["source"] = "USER_REPORTED_TIMESTAMP"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_unavailable_event_time_requires_null_evidence(self):
        value = anchor()
        value["event_time"] = unavailable_time()
        value["event_time"]["observed_at"] = "2026-07-29T14:50:00+00:00"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)


class ScopeResolutionTests(unittest.TestCase):
    def test_stable_scope_uses_approved_hash_inputs(self):
        result = resolve_scope(
            "vera-chatgpt-instance", exposed_identity("conv-a"), exposed_identity("branch-a")
        )
        self.assertEqual("STABLE", result["mode"])
        self.assertTrue(result["durable_recognition"])
        self.assertEqual(
            stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-a"),
            result["scope_id"],
        )

    def test_unexposed_ids_force_ephemeral_scope(self):
        result = resolve_scope(
            "vera-chatgpt-instance", exposed_identity("conv-a"), unavailable_identity()
        )
        self.assertEqual("EPHEMERAL", result["mode"])
        self.assertFalse(result["durable_recognition"])
        UUID(result["scope_id"])

    def test_ephemeral_scope_value_cannot_be_passed_positionally(self):
        with self.assertRaises(TypeError):
            resolve_scope(
                "vera-chatgpt-instance",
                exposed_identity("conv-a"),
                unavailable_identity(),
                str(uuid4()),
            )

    def test_default_generator_produces_fresh_ephemeral_scopes(self):
        first = resolve_scope(
            "vera-chatgpt-instance", exposed_identity("conv-a"), unavailable_identity()
        )
        second = resolve_scope(
            "vera-chatgpt-instance", exposed_identity("conv-a"), unavailable_identity()
        )
        self.assertNotEqual(first["scope_id"], second["scope_id"])

    def test_generator_dependency_is_keyword_only_for_tests(self):
        fixed = UUID("11111111-1111-4111-8111-111111111111")
        result = resolve_scope(
            "vera-chatgpt-instance",
            exposed_identity("conv-a"),
            unavailable_identity(),
            uuid_factory=lambda: fixed,
        )
        self.assertEqual(str(fixed), result["scope_id"])
        self.assertIn("uuid_factory", inspect.signature(resolve_scope).parameters)

    def test_concurrent_conversations_are_separate(self):
        self.assertNotEqual(
            stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-a"),
            stable_scope_id("vera-chatgpt-instance", "conv-b", "branch-a"),
        )

    def test_concurrent_branches_are_separate(self):
        self.assertNotEqual(
            stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-a"),
            stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-b"),
        )


class AnchorValidationTests(unittest.TestCase):
    def test_fresh_chat_without_ids_has_no_prior_anchor(self):
        validate_anchor(anchor(exposed=False))

    def test_ephemeral_entry_cannot_claim_durable_predecessor(self):
        with self.assertRaises(AnchorValidationError):
            validate_anchor(anchor(exposed=False, prior_anchor_id=str(uuid4())))

    def test_material_exit_reason_is_enum(self):
        value = anchor(kind="MATERIAL_EXIT", prior_anchor_id=str(uuid4()))
        value["exit_reason"] = "because this felt material"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_material_exit_optional_details_are_validated(self):
        value = anchor(kind="MATERIAL_EXIT", prior_anchor_id=str(uuid4()))
        value["exit_details"] = ""
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_range_is_not_a_precision_category(self):
        value = anchor()
        value["event_time"]["precision"] = "RANGE"
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_checkpoint_cannot_be_session_identity(self):
        value = anchor()
        value["checkpoint_id"] = value["session_id"]
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_unrestricted_payload_field_is_rejected(self):
        value = anchor()
        value["payload"]["arbitrary"] = {"anything": True}
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def assert_nested_reserved_rejected(self, reserved_key: str):
        value = anchor()
        value["payload"] = {
            "details": {"note": "ordinary", "wrapper": {reserved_key: True}}
        }
        finalize(value)
        with self.assertRaisesRegex(AnchorValidationError, "reserved continuity"):
            validate_anchor(value)

    def test_nested_hidden_activity_claim_field_is_rejected(self):
        self.assert_nested_reserved_rejected("hidden_activity")

    def test_nested_invented_identity_claim_field_is_rejected(self):
        self.assert_nested_reserved_rejected("invented_identity")

    def test_nested_waiting_claim_field_is_rejected(self):
        self.assert_nested_reserved_rejected("waiting")

    def test_nested_uninterrupted_continuity_field_is_rejected(self):
        self.assert_nested_reserved_rejected("uninterrupted_continuity")

    def test_free_text_is_not_semantically_policed(self):
        value = anchor()
        value["payload"] = {
            "details": {
                "note": "The user discussed waiting and continuity as concepts, not claims."
            }
        }
        finalize(value)
        validate_anchor(value)

    def test_record_time_is_excluded_from_content_hash(self):
        value = anchor()
        original_hash = value["content_hash"]
        value["record_time"] = "2026-07-29T15:20:00+00:00"
        self.assertEqual(original_hash, compute_content_hash(value))
        validate_anchor(value)


class PredecessorTests(unittest.TestCase):
    def test_stable_entry_accepts_existing_same_scope_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor()
        store.append(predecessor)
        resumed = anchor(prior_anchor_id=predecessor["anchor_id"], scope_id=predecessor["scope_id"])
        self.assertEqual("APPENDED", store.append(resumed).outcome)

    def test_stable_entry_rejects_nonexistent_predecessor(self):
        with self.assertRaisesRegex(AnchorValidationError, "must exist"):
            AppendOnlyAnchorSet().append(anchor(prior_anchor_id=str(uuid4())))

    def test_stable_entry_rejects_cross_project_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor(project_id="project-a")
        store.append(predecessor)
        with self.assertRaises(AnchorValidationError):
            store.append(anchor(project_id="project-b", prior_anchor_id=predecessor["anchor_id"]))

    def test_stable_entry_rejects_cross_scope_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor(conversation="conv-a")
        store.append(predecessor)
        with self.assertRaises(AnchorValidationError):
            store.append(anchor(conversation="conv-b", prior_anchor_id=predecessor["anchor_id"]))

    def test_verified_checkpoint_can_support_missing_stable_predecessor(self):
        store = AppendOnlyAnchorSet()
        prior = str(uuid4())
        value = anchor(prior_anchor_id=prior)
        value["predecessor_checkpoint_evidence"] = {
            "status": "VERIFIED",
            "source": "CHECKPOINT_OWNER_VERIFIED",
            "checkpoint_id": "checkpoint-verified-001",
            "predecessor_anchor_id": prior,
            "project_id": value["project_id"],
            "scope_id": value["scope_id"],
        }
        finalize(value)
        self.assertEqual("APPENDED", store.append(value).outcome)

    def test_unverified_checkpoint_predecessor_is_rejected(self):
        prior = str(uuid4())
        value = anchor(prior_anchor_id=prior)
        value["predecessor_checkpoint_evidence"] = {
            "status": "UNVERIFIED",
            "source": "CHECKPOINT_OWNER_VERIFIED",
            "checkpoint_id": "checkpoint-unverified-001",
            "predecessor_anchor_id": prior,
            "project_id": value["project_id"],
            "scope_id": value["scope_id"],
        }
        finalize(value)
        with self.assertRaises(AnchorValidationError):
            AppendOnlyAnchorSet().append(value)

    def test_material_exit_accepts_existing_same_session_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor()
        store.append(predecessor)
        self.assertEqual("APPENDED", store.append(material_exit_from(predecessor)).outcome)

    def test_material_exit_rejects_nonexistent_predecessor(self):
        value = anchor(kind="MATERIAL_EXIT", prior_anchor_id=str(uuid4()))
        with self.assertRaisesRegex(AnchorValidationError, "does not exist"):
            AppendOnlyAnchorSet().append(value)

    def test_material_exit_rejects_cross_project_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor(project_id="project-a")
        store.append(predecessor)
        value = material_exit_from(predecessor)
        value["project_id"] = "project-b"
        value["scope_id"] = stable_scope_id("project-b", "conv-a", "branch-a")
        finalize(value)
        with self.assertRaisesRegex(AnchorValidationError, "project_id"):
            store.append(value)

    def test_material_exit_rejects_cross_scope_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor()
        store.append(predecessor)
        value = material_exit_from(predecessor)
        value["conversation_identity"] = exposed_identity("conv-b")
        value["scope_id"] = stable_scope_id(value["project_id"], "conv-b", "branch-a")
        finalize(value)
        with self.assertRaisesRegex(AnchorValidationError, "scope_id"):
            store.append(value)

    def test_material_exit_rejects_cross_scope_instance_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor()
        store.append(predecessor)
        value = material_exit_from(predecessor)
        value["scope_instance_id"] = str(uuid4())
        finalize(value)
        with self.assertRaisesRegex(AnchorValidationError, "scope_instance_id"):
            store.append(value)

    def test_material_exit_rejects_cross_session_predecessor(self):
        store = AppendOnlyAnchorSet()
        predecessor = anchor()
        store.append(predecessor)
        value = material_exit_from(predecessor)
        value["session_id"] = str(uuid4())
        finalize(value)
        with self.assertRaisesRegex(AnchorValidationError, "session_id"):
            store.append(value)


class CanonicalHashAndIdempotencyTests(unittest.TestCase):
    def test_duplicate_same_canonical_content_returns_existing(self):
        store = AppendOnlyAnchorSet()
        value = anchor()
        first = store.append(value)
        second = store.append(deepcopy(value))
        self.assertEqual("APPENDED", first.outcome)
        self.assertEqual("EXISTING", second.outcome)
        self.assertEqual(first.anchor_id, second.anchor_id)

    def assert_old_claimed_hash_conflicts(self, first: dict, second: dict):
        store = AppendOnlyAnchorSet()
        store.append(first)
        second["idempotency_key"] = first["idempotency_key"]
        second["content_hash"] = first["content_hash"]
        with self.assertRaisesRegex(IdempotencyConflict, "CONFLICTED"):
            store.append(second)

    def test_changed_payload_with_old_claimed_hash_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["payload"] = {"labels": ["changed"]}
        self.assert_old_claimed_hash_conflicts(first, second)

    def test_changed_identity_with_old_claimed_hash_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["conversation_identity"] = exposed_identity("conv-b")
        second["scope_id"] = stable_scope_id(second["project_id"], "conv-b", "branch-a")
        self.assert_old_claimed_hash_conflicts(first, second)

    def test_changed_predecessor_with_old_claimed_hash_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["prior_anchor_id"] = str(uuid4())
        self.assert_old_claimed_hash_conflicts(first, second)

    def test_changed_timestamp_with_old_claimed_hash_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["event_time"] = exact("2026-07-29T14:51:00+00:00")
        self.assert_old_claimed_hash_conflicts(first, second)

    def test_changed_anchor_kind_with_old_claimed_hash_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["anchor_kind"] = "MATERIAL_EXIT"
        second["entry_reason"] = None
        second["exit_reason"] = "SESSION_CLOSE"
        second["prior_anchor_id"] = str(uuid4())
        self.assert_old_claimed_hash_conflicts(first, second)

    def test_changed_anchor_id_with_same_key_conflicts(self):
        first = anchor()
        second = deepcopy(first)
        second["anchor_id"] = str(uuid4())
        second["content_hash"] = compute_content_hash(second)
        second["idempotency_key"] = first["idempotency_key"]
        store = AppendOnlyAnchorSet()
        store.append(first)
        with self.assertRaisesRegex(IdempotencyConflict, "different canonical content"):
            store.append(second)


class ElapsedTests(unittest.TestCase):
    def test_exact_elapsed(self):
        result = calculate_elapsed(
            exact("2026-07-29T10:00:00-04:00"),
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual({"status": "EXACT", "seconds": 3600.0}, result)

    def test_reversed_exact_interval_is_conflicted(self):
        result = calculate_elapsed(
            exact("2026-07-29T15:00:00+00:00"),
            exact("2026-07-29T14:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("CONFLICTED", result["status"])
        self.assertEqual("END_PRECEDES_START", result["reason"])

    def test_bounded_elapsed_uses_range_representation(self):
        result = calculate_elapsed(
            bounded(
                "2026-07-29T14:00:00+00:00",
                "2026-07-29T13:55:00+00:00",
                "2026-07-29T14:05:00+00:00",
            ),
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("BOUNDED", result["status"])
        self.assertEqual(3300.0, result["range"]["lower_seconds"])
        self.assertEqual(3900.0, result["range"]["upper_seconds"])

    def test_fully_reversed_bounded_interval_is_conflicted(self):
        start = bounded(
            "2026-07-29T15:00:00+00:00",
            "2026-07-29T14:55:00+00:00",
            "2026-07-29T15:05:00+00:00",
        )
        end = bounded(
            "2026-07-29T14:00:00+00:00",
            "2026-07-29T13:55:00+00:00",
            "2026-07-29T14:05:00+00:00",
        )
        result = calculate_elapsed(start, end, start_scope_id="same", end_scope_id="same")
        self.assertEqual("CONFLICTED", result["status"])
        self.assertEqual("END_PRECEDES_START", result["reason"])

    def test_missing_endpoint_is_unavailable(self):
        result = calculate_elapsed(
            None,
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("UNAVAILABLE", result["status"])

    def test_unknown_precision_is_unavailable(self):
        result = calculate_elapsed(
            unavailable_time(),
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("UNAVAILABLE", result["status"])

    def test_scope_mismatch_is_conflicted(self):
        result = calculate_elapsed(
            exact("2026-07-29T14:00:00+00:00"),
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="chat-a",
            end_scope_id="chat-b",
        )
        self.assertEqual("CONFLICTED", result["status"])

    def test_result_never_claims_waiting_or_hidden_activity(self):
        result = calculate_elapsed(
            exact("2026-07-29T14:00:00+00:00"),
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        serialized = json.dumps(result)
        self.assertNotIn("waiting", serialized)
        self.assertNotIn("activity", serialized)


if __name__ == "__main__":
    unittest.main()
