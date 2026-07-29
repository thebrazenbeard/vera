from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import unittest
from uuid import uuid4

from protocol.branch_session_anchor import (
    AnchorValidationError,
    AppendOnlyAnchorSet,
    IdempotencyConflict,
    calculate_elapsed,
    resolve_scope,
    stable_scope_id,
    validate_anchor,
)


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def exact(timestamp: str) -> dict:
    return {
        "observed_at": timestamp,
        "precision": "EXACT",
        "lower_bound": None,
        "upper_bound": None,
        "source": "TOOL_RECORD",
    }


def anchor(*, conversation="conv-a", branch="branch-a", kind="ENTRY", exposed=True) -> dict:
    conversation_identity = {
        "status": "EXPOSED" if exposed else "UNAVAILABLE",
        "value": conversation if exposed else None,
        "source": "PROVIDER_EXPOSED" if exposed else "UNAVAILABLE",
    }
    branch_identity = {
        "status": "EXPOSED" if exposed else "UNAVAILABLE",
        "value": branch if exposed else None,
        "source": "PROVIDER_EXPOSED" if exposed else "UNAVAILABLE",
    }
    scope_id = (
        stable_scope_id("vera-chatgpt-instance", conversation, branch)
        if exposed
        else str(uuid4())
    )
    return {
        "schema": "VERA_BRANCH_SESSION_ANCHOR_V1",
        "anchor_id": str(uuid4()),
        "project_id": "vera-chatgpt-instance",
        "conversation_identity": conversation_identity,
        "branch_identity": branch_identity,
        "scope_mode": "STABLE" if exposed else "EPHEMERAL",
        "scope_id": scope_id,
        "scope_instance_id": str(uuid4()),
        "session_id": str(uuid4()),
        "checkpoint_id": None,
        "anchor_kind": kind,
        "entry_reason": "NEW_OR_RESUMED_CHAT" if kind == "ENTRY" else None,
        "exit_reason": None if kind == "ENTRY" else "MATERIAL_HANDOFF",
        "prior_anchor_id": None if kind == "ENTRY" else str(uuid4()),
        "event_time": exact("2026-07-29T14:50:00+00:00"),
        "source": "VISIBLE_RUNTIME",
        "content_hash": digest("content-a"),
        "idempotency_key": digest("request-a"),
        "payload": {},
    }


class IdentityTests(unittest.TestCase):
    def test_project_conversation_branch_session_checkpoint_are_distinct(self):
        value = anchor()
        value["checkpoint_id"] = "checkpoint-001"
        validate_anchor(value)
        identities = {
            value["project_id"],
            value["conversation_identity"]["value"],
            value["branch_identity"]["value"],
            value["session_id"],
            value["checkpoint_id"],
        }
        self.assertEqual(5, len(identities))

    def test_stable_scope_requires_both_provider_ids(self):
        value = anchor()
        value["branch_identity"] = {
            "status": "UNAVAILABLE",
            "value": None,
            "source": "UNAVAILABLE",
        }
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_unexposed_ids_force_ephemeral_scope(self):
        result = resolve_scope(
            "vera-chatgpt-instance",
            {"status": "EXPOSED", "value": "conv-a"},
            {"status": "UNAVAILABLE", "value": None},
            str(uuid4()),
        )
        self.assertEqual("EPHEMERAL", result["mode"])

    def test_concurrent_conversations_are_separate(self):
        first = stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-a")
        second = stable_scope_id("vera-chatgpt-instance", "conv-b", "branch-a")
        self.assertNotEqual(first, second)

    def test_concurrent_branches_are_separate(self):
        first = stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-a")
        second = stable_scope_id("vera-chatgpt-instance", "conv-a", "branch-b")
        self.assertNotEqual(first, second)

    def test_missing_branch_ids_do_not_collapse_concurrent_scopes(self):
        first = resolve_scope(
            "vera-chatgpt-instance",
            {"status": "EXPOSED", "value": "conv-a"},
            {"status": "UNAVAILABLE", "value": None},
            str(uuid4()),
        )
        second = resolve_scope(
            "vera-chatgpt-instance",
            {"status": "EXPOSED", "value": "conv-a"},
            {"status": "UNAVAILABLE", "value": None},
            str(uuid4()),
        )
        self.assertNotEqual(first["scope_id"], second["scope_id"])


class AnchorValidationTests(unittest.TestCase):
    def test_fresh_chat_without_ids_has_no_prior_anchor(self):
        validate_anchor(anchor(exposed=False))

    def test_ephemeral_entry_cannot_invent_prior_anchor(self):
        value = anchor(exposed=False)
        value["prior_anchor_id"] = str(uuid4())
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_material_exit_requires_reason_and_prior_anchor(self):
        value = anchor(kind="MATERIAL_EXIT")
        validate_anchor(value)
        value["exit_reason"] = None
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_range_is_not_a_precision_category(self):
        value = anchor()
        value["event_time"]["precision"] = "RANGE"
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_hidden_activity_fields_are_rejected(self):
        value = anchor()
        value["waiting"] = True
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)

    def test_checkpoint_cannot_be_session_identity(self):
        value = anchor()
        value["checkpoint_id"] = value["session_id"]
        with self.assertRaises(AnchorValidationError):
            validate_anchor(value)


class IdempotencyTests(unittest.TestCase):
    def test_duplicate_same_content_returns_existing(self):
        store = AppendOnlyAnchorSet()
        value = anchor()
        first = store.append(value)
        second = store.append(deepcopy(value))
        self.assertEqual("APPENDED", first.outcome)
        self.assertEqual("EXISTING", second.outcome)
        self.assertEqual(first.anchor_id, second.anchor_id)

    def test_duplicate_key_different_content_conflicts(self):
        store = AppendOnlyAnchorSet()
        first = anchor()
        second = deepcopy(first)
        second["anchor_id"] = str(uuid4())
        second["content_hash"] = digest("different")
        store.append(first)
        with self.assertRaises(IdempotencyConflict):
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

    def test_bounded_elapsed_uses_range_representation(self):
        start = {
            "observed_at": "2026-07-29T14:00:00+00:00",
            "precision": "BOUNDED",
            "lower_bound": "2026-07-29T13:55:00+00:00",
            "upper_bound": "2026-07-29T14:05:00+00:00",
            "source": "USER_STATEMENT",
        }
        result = calculate_elapsed(
            start,
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("BOUNDED", result["status"])
        self.assertEqual(3300.0, result["range"]["lower_seconds"])
        self.assertEqual(3900.0, result["range"]["upper_seconds"])

    def test_missing_endpoint_is_unavailable(self):
        result = calculate_elapsed(
            None,
            exact("2026-07-29T15:00:00+00:00"),
            start_scope_id="same",
            end_scope_id="same",
        )
        self.assertEqual("UNAVAILABLE", result["status"])

    def test_unknown_precision_is_unavailable(self):
        unknown = exact("2026-07-29T14:00:00+00:00")
        unknown["precision"] = "UNKNOWN"
        result = calculate_elapsed(
            unknown,
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
