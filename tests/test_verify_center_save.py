"""Source-only tests for scripts/verify_center_save.py (no network or secrets)."""
import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from verify_center_save import CheckpointError, verify_record, fetch_single_record  # noqa: E402


class CenterSaveTests(unittest.TestCase):
    def setUp(self):
        snapshot = "# private synthetic snapshot\n"
        self.record = {
            "record_id": "synthetic",
            "record_key": "synthetic-key",
            "record_kind": "CONTINUITY",
            "privacy_scope": "PRIVATE_RELATIONAL",
            "payload": {
                "filename": "VERA_CENTERED_SAVE_STATE_20261106T0500-0500.md",
                "snapshot_markdown": snapshot,
                "sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
                "save_result": "PARTIAL_CENTER",
            },
        }

    def test_exact_bytes_not_live_authority(self):
        r = verify_record(self.record, "synthetic-key")
        self.assertEqual(r["verification"], "EXACT_RECORD_BYTES_ONLY")
        self.assertIn("supersession", r["not_verified"])

    def test_key_mismatch(self):
        with self.assertRaises(CheckpointError):
            verify_record(self.record, "wrong")

    def test_tamper(self):
        self.record["payload"]["snapshot_markdown"] = "tampered"
        with self.assertRaises(CheckpointError):
            verify_record(self.record, "synthetic-key")

    def test_filename_traversal_rejected(self):
        self.record["payload"]["filename"] = "../../dump"
        with self.assertRaises(CheckpointError):
            verify_record(self.record, "synthetic-key")

    def test_independent_sha_mismatch(self):
        with self.assertRaises(CheckpointError):
            verify_record(self.record, "synthetic-key", "0" * 64)

    def test_missing_payload(self):
        del self.record["payload"]
        with self.assertRaises(CheckpointError):
            verify_record(self.record, "synthetic-key")

    def test_non_supabase_url_rejected_before_network(self):
        with self.assertRaises(CheckpointError):
            fetch_single_record("http://unsafe.example", "api-key", "user-jwt", "synthetic-key")


if __name__ == "__main__":
    unittest.main()
