import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
REQUIRED_AUTH_METADATA = {
    "actor",
    "referent",
    "proposition_or_effect_class",
    "source",
    "observed_at",
    "currentness",
    "expiry_or_supersession",
}


class ForcedAuthorizationBoundaryTests(unittest.TestCase):
    def make_host(self, runtime_instance_id="forced-auth-boundary-test"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
        )

    def subject(self, runtime_instance_id, trigger_class):
        return {
            "authorization_state": "ALLOW",
            "actor": "patrick",
            "referent": runtime_instance_id,
            "proposition_or_effect_class": trigger_class,
            "source": "CURRENT_USER_AUTHORITY",
            "observed_at": "2026-09-09T21:50:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": "NONE",
        }

    def assert_rejected(self, trigger_method, authorization):
        host = self.make_host(f"reject-{trigger_method}")
        method = getattr(host.runtime, trigger_method)
        with self.assertRaisesRegex(TriggerRejected, r"(?i)(authori|current|referent|expiry|provenance|subject)"):
            method(authorized=authorization)

    def test_bare_true_boolean_cannot_authorize_privileged_triggers(self):
        self.assert_rejected("force_admin_test", True)
        self.assert_rejected("force_self_qualification", True)

    def test_valid_admin_subject_is_bound_into_forced_receipt(self):
        runtime_id = "valid-admin-auth-subject"
        host = self.make_host(runtime_id)
        subject = self.subject(runtime_id, "ADMIN_FORCED_TEST")
        receipt = host.runtime.force_admin_test(authorized=subject)

        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])
        provenance = receipt.get("authorization_provenance")
        self.assertIsInstance(provenance, dict)
        self.assertEqual(provenance.get("authorization_state"), "ALLOW")
        self.assertTrue(REQUIRED_AUTH_METADATA.issubset(provenance))
        for field in REQUIRED_AUTH_METADATA:
            self.assertEqual(provenance[field], subject[field])

    def test_valid_self_qualification_subject_is_bound_into_forced_receipt(self):
        runtime_id = "valid-self-auth-subject"
        host = self.make_host(runtime_id)
        subject = self.subject(runtime_id, "SELF_QUALIFICATION_TEST")
        receipt = host.runtime.force_self_qualification(authorized=subject)

        self.assertEqual(receipt["trigger_class"], "SELF_QUALIFICATION_TEST")
        self.assertFalse(receipt["organic"])
        provenance = receipt.get("authorization_provenance")
        self.assertIsInstance(provenance, dict)
        self.assertEqual(provenance.get("referent"), runtime_id)
        self.assertEqual(provenance.get("proposition_or_effect_class"), "SELF_QUALIFICATION_TEST")

    def test_decline_unknown_stale_expired_wrong_referent_and_wrong_effect_fail_closed(self):
        runtime_id = "negative-admin-auth-subject"
        base = self.subject(runtime_id, "ADMIN_FORCED_TEST")
        cases = (
            ("DECLINE", {"authorization_state": "DECLINE"}),
            ("UNKNOWN", {"authorization_state": "UNKNOWN"}),
            ("STALE", {"currentness": "STALE"}),
            ("EXPIRED", {"expiry_or_supersession": "EXPIRED"}),
            ("WRONG_REFERENT", {"referent": "some-other-runtime"}),
            ("WRONG_EFFECT", {"proposition_or_effect_class": "SELF_QUALIFICATION_TEST"}),
        )
        for label, changes in cases:
            with self.subTest(label=label):
                host = self.make_host(runtime_id)
                subject = dict(base)
                subject.update(changes)
                with self.assertRaisesRegex(TriggerRejected, r"(?i)(authori|current|referent|expiry|provenance|subject|effect)"):
                    host.runtime.force_admin_test(authorized=subject)

    def test_missing_required_authorization_metadata_fails_closed(self):
        runtime_id = "missing-admin-auth-metadata"
        base = self.subject(runtime_id, "ADMIN_FORCED_TEST")
        for missing in sorted(REQUIRED_AUTH_METADATA):
            with self.subTest(missing=missing):
                host = self.make_host(runtime_id)
                subject = dict(base)
                subject.pop(missing)
                with self.assertRaisesRegex(TriggerRejected, r"(?i)(authori|metadata|provenance|subject)"):
                    host.runtime.force_admin_test(authorized=subject)


if __name__ == "__main__":
    unittest.main()
