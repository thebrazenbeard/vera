from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    build_affective_resume_token,
    checkpoint_to_state_row,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"
LIMITATION = "IN_PROCESS_AUTHORITY_UNROOTED_NON_QUALIFYING"


class TrustedVerifier:
    verifier_id = "affect-unrooted-currentness-verifier"

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
            "evidence_id": "affect-unrooted-currentness-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class UnrootedCurrentnessTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-unrooted-currentness-test",
            "observed_at": "2026-09-10T22:50:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def host(self, runtime_instance_id="unrooted-currentness-test"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
            profile="REENTRANT_CLIMAX",
        )

    def unrooted_recovery_checkpoint(self):
        host = self.host()
        receipt = host.force_admin_test(authorization_subject=self.subject())
        self.assertEqual(receipt["authority_composition_trust"], UNROOTED)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        last = checkpoint["runtime_state"]["last_event_receipt"]
        self.assertIn(last["event_type"], {"RESOLUTION", "RECOVERY"})
        self.assertEqual(last["authority_composition_trust"], UNROOTED)
        return checkpoint

    def test_unrooted_recovery_checkpoint_cannot_form_current_state_row(self):
        checkpoint = self.unrooted_recovery_checkpoint()
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(current|unrooted|nonqualifying|authority|lineage)"):
            checkpoint_to_state_row(
                checkpoint,
                host_scope="TEST_HOST",
                state_version=2,
                lifecycle_status="CURRENT",
            )

    def test_unrooted_recovery_checkpoint_can_form_historical_state_row(self):
        checkpoint = self.unrooted_recovery_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=2,
            lifecycle_status="HISTORICAL",
        )
        self.assertEqual(row["lifecycle_status"], "HISTORICAL")
        self.assertIn(LIMITATION, row["limitations"])
        self.assertEqual(row["last_event_receipt"]["authority_composition_trust"], UNROOTED)

    def test_resume_token_rejects_unrooted_lineage_even_if_caller_relabels_row_current(self):
        checkpoint = self.unrooted_recovery_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=2,
            lifecycle_status="HISTORICAL",
        )
        forged = dict(row)
        forged["lifecycle_status"] = "CURRENT"
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(resume|unrooted|nonqualifying|authority|lineage)"):
            build_affective_resume_token(forged)

    def test_resume_token_rejects_unrooted_receipt_even_if_caller_strips_limitations(self):
        checkpoint = self.unrooted_recovery_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=2,
            lifecycle_status="HISTORICAL",
        )
        forged = dict(row)
        forged["lifecycle_status"] = "CURRENT"
        forged["limitations"] = []
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(resume|unrooted|nonqualifying|authority|lineage)"):
            build_affective_resume_token(forged)

    def test_pre_event_current_state_can_still_receive_resume_token(self):
        host = self.host("pre-event-currentness-test")
        row = checkpoint_to_state_row(
            host.export_checkpoint(),
            host_scope="TEST_HOST",
            state_version=1,
            lifecycle_status="CURRENT",
        )
        token = build_affective_resume_token(row)
        self.assertEqual(token["runtime_instance_id"], "pre-event-currentness-test")
        self.assertEqual(token["state_version"], 1)


if __name__ == "__main__":
    unittest.main()
