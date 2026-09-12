from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import PersistenceRecordError, checkpoint_to_state_row, restore_host_from_state_row

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
MIGRATION = ROOT / "supabase" / "migrations" / "20260909181500_close_vera_affective_runtime_first_write_race_v1.sql"


class TrustedVerifier:
    verifier_id = "affect-trigger-governance-persistence-verifier"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "trigger-governance-persistence-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class VeraAffectiveTriggerGovernancePersistenceTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-trigger-governance-persistence-test",
            "observed_at": "2026-09-10T20:00:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-trigger-governance-persistence-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_unrooted_trigger_governance_can_be_recorded_historically_but_not_restored_as_current(self):
        host = self.make_host()
        receipt = host.force_admin_test(authorization_subject=self.authorization_subject())
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertNotIn("claim", receipt)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=1,
            lifecycle_status="HISTORICAL",
        )

        self.assertIn("trigger_governance", row)
        self.assertEqual(row["trigger_governance"]["schema"], "VERA_ORGASM_TRIGGER_GOVERNANCE_V1")
        self.assertEqual(row["lifecycle_status"], "HISTORICAL")

        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(current|lifecycle|historical)"):
            restore_host_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )

    def test_provider_migration_carries_trigger_governance_through_atomic_state_commit(self):
        sql = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertIn("add column if not exists trigger_governance jsonb", sql)
        self.assertIn("trigger_governance,", sql)
        self.assertIn("p_state_row->'trigger_governance'", sql)
        self.assertIn("trigger_governance = excluded.trigger_governance", sql)


if __name__ == "__main__":
    unittest.main()
