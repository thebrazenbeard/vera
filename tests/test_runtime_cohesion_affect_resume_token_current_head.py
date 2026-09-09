import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    build_affective_resume_token,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveResumeTokenCurrentHeadTests(unittest.TestCase):
    def make_row(self, *, state_version=7):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="resume-token-current-head-test",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row, build_affective_resume_token(row)

    def test_both_exported_live_restore_boundaries_require_resume_token(self):
        self.assertIn(
            "expected_resume_token",
            inspect.signature(VeraAffectiveCycle.restore_from_state_row).parameters,
        )
        self.assertIn(
            "expected_resume_token",
            inspect.signature(restore_host_from_state_row).parameters,
        )

    def test_exact_resume_token_allows_exact_current_frontier(self):
        checkpoint, row, token = self.make_row(state_version=7)
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )
        self.assertEqual(cycle._next_state_version, 8)

    def test_same_checkpoint_with_changed_provider_version_is_rejected(self):
        checkpoint, row, token = self.make_row(state_version=7)
        replayed = dict(row)
        replayed["state_version"] = 8
        self.assertEqual(replayed["checkpoint_sha256"], token["checkpoint_sha256"])

        with self.assertRaisesRegex(ValueError, r"(?i)(resume|version|frontier)"):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                replayed,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
            )

    def test_resume_token_must_bind_runtime_source_and_checkpoint(self):
        checkpoint, row, token = self.make_row(state_version=7)
        for field, value in (
            ("runtime_instance_id", "other-runtime"),
            ("source_commit", "0" * 40),
            ("checkpoint_sha256", "0" * 64),
        ):
            with self.subTest(field=field):
                bad = dict(token)
                bad[field] = value
                with self.assertRaisesRegex(ValueError, r"(?i)(resume|checkpoint|source|runtime)"):
                    VeraAffectiveCycle.restore_from_state_row(
                        CONTRACT_PATH.read_text(encoding="utf-8"),
                        json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                        row,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        expected_resume_token=bad,
                    )


if __name__ == "__main__":
    unittest.main()
