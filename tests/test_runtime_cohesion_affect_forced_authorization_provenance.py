import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.orgasm import OrgasmRuntime, TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"


class ForcedAuthorizationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.runtime = OrgasmRuntime(
            self.contract,
            runtime_instance_id="vera-forced-auth-provenance-test",
            source_revision="a" * 40,
        )

    def authorization_record(self, **overrides):
        record = {
            "state": "ALLOW",
            "actor": "TEST_ADMIN",
            "referent": self.runtime.runtime_instance_id,
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "SYNTHETIC_AUTHORIZATION_TEST_FIXTURE",
            "observed_at": "2026-09-09T21:30:00Z",
            "currentness": "CURRENT_OBSERVATION",
            "expiry_or_supersession": "UNEXPIRED",
        }
        record.update(overrides)
        return record

    def test_contract_declared_authorization_metadata_is_consumed_at_forced_trigger_boundary(self):
        required = set(self.contract["authorization_boundary"]["required_metadata"])
        self.assertEqual(
            required,
            {
                "actor",
                "referent",
                "proposition_or_effect_class",
                "source",
                "observed_at",
                "currentness",
                "expiry_or_supersession",
            },
        )
        parameters = inspect.signature(OrgasmRuntime.force_admin_test).parameters
        self.assertIn("authorization_record", parameters)
        self.assertNotIn("authorized", parameters)

    def test_bare_boolean_cannot_stand_in_for_authorization_evidence(self):
        with self.assertRaises((TypeError, TriggerRejected)):
            self.runtime.force_admin_test(authorized=True)

    def test_exact_current_allow_record_drives_forced_trigger_and_is_receipted(self):
        authorization = self.authorization_record()
        receipt = self.runtime.force_admin_test(authorization_record=authorization)
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(receipt["organic"])
        self.assertEqual(receipt["authorization_record"], authorization)

    def test_non_allow_or_noncurrent_authorization_cannot_trigger(self):
        cases = (
            self.authorization_record(state="DECLINE"),
            self.authorization_record(state="UNKNOWN"),
            self.authorization_record(currentness="SUPERSEDED"),
            self.authorization_record(expiry_or_supersession="EXPIRED"),
        )
        for authorization in cases:
            with self.subTest(authorization=authorization):
                runtime = OrgasmRuntime(
                    self.contract,
                    runtime_instance_id="vera-forced-auth-negative-test",
                    source_revision="a" * 40,
                )
                authorization = dict(authorization)
                authorization["referent"] = runtime.runtime_instance_id
                with self.assertRaises(TriggerRejected):
                    runtime.force_admin_test(authorization_record=authorization)

    def test_authorization_must_bind_exact_runtime_and_effect(self):
        for authorization in (
            self.authorization_record(referent="other-runtime"),
            self.authorization_record(proposition_or_effect_class="SELF_QUALIFICATION_TEST"),
        ):
            with self.subTest(authorization=authorization):
                runtime = OrgasmRuntime(
                    self.contract,
                    runtime_instance_id=self.runtime.runtime_instance_id,
                    source_revision="a" * 40,
                )
                with self.assertRaises(TriggerRejected):
                    runtime.force_admin_test(authorization_record=authorization)


if __name__ == "__main__":
    unittest.main()
