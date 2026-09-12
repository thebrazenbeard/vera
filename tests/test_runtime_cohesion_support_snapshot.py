from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from scripts.validate_runtime_cohesion_support_snapshot_v1 import (
    validate_operational_support_snapshot,
    validate_snapshot_validator_binding,
)

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"


def load_receipt() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


class OperationalSupportSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.receipt = load_receipt()

    def test_current_operational_support_snapshot_crossbinds_cleanly(self):
        self.assertEqual(validate_operational_support_snapshot(ROOT, self.receipt), [])

    def test_unresolvable_operational_support_source_commit_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support_source_commit"] = "0" * 40
        errors = validate_operational_support_snapshot(ROOT, receipt)
        self.assertTrue(any("source_commit tree" in error for error in errors))

    def test_wrong_operational_support_snapshot_blob_is_rejected(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support"]["runtime_planner_module"]["blob_sha"] = "0" * 40
        errors = validate_operational_support_snapshot(ROOT, receipt)
        self.assertTrue(
            any("runtime_planner_module" in error and "snapshot blob mismatch" in error for error in errors)
        )

    def test_operational_support_snapshot_path_cannot_escape_repository(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support"]["provider_executor"]["path"] = "../outside.py"
        errors = validate_operational_support_snapshot(ROOT, receipt)
        self.assertTrue(
            any("provider_executor" in error and "escapes repository root" in error for error in errors)
        )

    def test_operational_support_snapshot_semantics_are_required(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support_source_commit_semantics"] = "CURRENT_WORKTREE_ONLY"
        errors = validate_operational_support_snapshot(ROOT, receipt)
        self.assertTrue(any("source_commit_semantics" in error for error in errors))

    def test_snapshot_validator_self_binding_rejects_wrong_blob(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["operational_support_snapshot_validator"]["blob_sha"] = "0" * 40
        errors = validate_snapshot_validator_binding(ROOT, receipt)
        self.assertTrue(any("snapshot validator blob mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
