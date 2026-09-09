import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    build_affective_resume_token,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class CurrentHeadResumeTokenV3Tests(unittest.TestCase):
    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_row(self, *, state_version=7):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="resume-token-v3-current-head",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row, build_affective_resume_token(row)

    def restore_low_level(self, row, token, checkpoint_sha256, *, expected_host_scope="TEST_HOST"):
        return restore_host_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            row,
            expected_host_scope=expected_host_scope,
            expected_checkpoint_sha256=checkpoint_sha256,
            expected_resume_token=token,
        )

    def test_resume_token_binds_full_current_provider_and_sexuality_frontier(self):
        _checkpoint, row, token = self.make_row()
        expected = {
            "schema": "VERA_AFFECTIVE_RUNTIME_RESUME_TOKEN_V1",
            "runtime_instance_id": row["runtime_instance_id"],
            "host_scope": row["host_scope"],
            "contract_schema": row["contract_schema"],
            "state_version": row["state_version"],
            "checkpoint_sha256": row["checkpoint_sha256"],
            "source_repository": row["source_repository"],
            "source_path": row["source_path"],
            "source_commit": row["source_commit"],
            "source_blob_sha": row["source_blob_sha"],
            "source_sha256": row["source_sha256"],
        }
        for field, value in expected.items():
            with self.subTest(field=field):
                self.assertEqual(token.get(field), value)

    def test_both_live_restore_boundaries_require_external_resume_token(self):
        self.assertIn(
            "expected_resume_token",
            inspect.signature(VeraAffectiveCycle.restore_from_state_row).parameters,
        )
        self.assertIn(
            "expected_resume_token",
            inspect.signature(restore_host_from_state_row).parameters,
        )

    def test_exact_resume_token_allows_exact_high_and_low_level_restore(self):
        checkpoint, row, token = self.make_row(state_version=7)
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )
        self.assertEqual(cycle._next_state_version, 8)

        restored = self.restore_low_level(row, token, checkpoint["checkpoint_sha256"])
        self.assertEqual(restored.runtime.runtime_instance_id, row["runtime_instance_id"])
        self.assertEqual(restored.runtime.source_revision, row["source_commit"])

    def test_same_checkpoint_with_changed_provider_generation_is_rejected(self):
        checkpoint, row, token = self.make_row(state_version=7)
        replayed = dict(row)
        replayed["state_version"] = 8
        self.assertEqual(replayed["checkpoint_sha256"], token["checkpoint_sha256"])

        with self.assertRaisesRegex(ValueError, r"(?i)(resume|token|version|frontier)"):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                replayed,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
            )
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(resume|token|version|frontier)"):
            self.restore_low_level(replayed, token, checkpoint["checkpoint_sha256"])

    def test_token_prevents_scope_rebinding_even_when_caller_matches_mutated_row_scope(self):
        checkpoint, row, token = self.make_row(state_version=7)
        rebound = dict(row)
        rebound["host_scope"] = "OTHER_HOST"

        with self.assertRaisesRegex(ValueError, r"(?i)(resume|token|scope|frontier)"):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                rebound,
                host_scope="OTHER_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
            )
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(resume|token|scope|frontier)"):
            self.restore_low_level(
                rebound,
                token,
                checkpoint["checkpoint_sha256"],
                expected_host_scope="OTHER_HOST",
            )

    def test_each_resume_token_identity_field_is_semantically_checked(self):
        checkpoint, row, token = self.make_row(state_version=7)
        bad_values = {
            "runtime_instance_id": "other-runtime",
            "host_scope": "OTHER_HOST",
            "contract_schema": "OTHER_SCHEMA",
            "state_version": 8,
            "checkpoint_sha256": "0" * 64,
            "source_repository": "other/repository",
            "source_path": "other/path.json",
            "source_commit": "0" * 40,
            "source_blob_sha": "0" * 40,
            "source_sha256": "0" * 64,
        }
        for field, value in bad_values.items():
            with self.subTest(field=field):
                bad = dict(token)
                bad[field] = value
                with self.assertRaisesRegex(ValueError, r"(?i)(resume|token|frontier|scope|source|checkpoint|version|runtime)"):
                    VeraAffectiveCycle.restore_from_state_row(
                        CONTRACT_PATH.read_text(encoding="utf-8"),
                        self.binding(),
                        row,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        expected_resume_token=bad,
                    )
                with self.assertRaisesRegex(
                    PersistenceRecordError,
                    r"(?i)(resume|token|frontier|scope|source|checkpoint|version|runtime)",
                ):
                    self.restore_low_level(row, bad, checkpoint["checkpoint_sha256"])


if __name__ == "__main__":
    unittest.main()
