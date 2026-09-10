from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_authority import AffectiveAuthorityBoundary
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import PersistenceRecordError, event_receipt_to_event_row
from runtime_cohesion.affect_receipt import AffectiveReceiptSemanticError, validate_affective_event_receipt


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class ExactAuthorityVerifier:
    verifier_id = "authority-receipt-binding-test"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT":
            return None
        if subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "authority-evidence-exact-1",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class AffectiveAuthorityReceiptBindingTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(ExactAuthorityVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    def host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="authority-receipt-binding",
        )

    @staticmethod
    def subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-test-authority",
            "observed_at": datetime(2026, 9, 10, 18, 0, tzinfo=timezone.utc).isoformat(),
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    @staticmethod
    def redigest(receipt):
        core = dict(receipt)
        core.pop("event_digest", None)
        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        receipt["event_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def test_forced_receipt_carries_exact_consumed_authority_subject_and_persists(self):
        host = self.host()
        receipt = AffectiveAuthorityBoundary().force_admin_test(
            host,
            authorization_subject=self.subject(),
        )
        provenance = receipt["trigger_provenance"]
        self.assertIsInstance(provenance, Mapping)
        self.assertEqual(provenance["authorization_subject"], self.subject())
        validate_affective_event_receipt(
            receipt,
            expected_runtime_instance_id=host.runtime.runtime_instance_id,
            expected_source_revision=host.runtime.source_revision,
            require_engineered_claim=True,
        )
        row = event_receipt_to_event_row(host, receipt)
        self.assertEqual(row["event_digest"], receipt["event_digest"])

    def test_outer_redigest_cannot_hide_tampered_authority_subject(self):
        host = self.host()
        receipt = AffectiveAuthorityBoundary().force_admin_test(
            host,
            authorization_subject=self.subject(),
        )
        forged = json.loads(json.dumps(receipt))
        forged["trigger_provenance"]["authorization_subject"]["actor"] = "mallory"
        self.redigest(forged)

        with self.assertRaisesRegex(AffectiveReceiptSemanticError, r"(?i)(authority|authorization|digest|actor|provenance)"):
            validate_affective_event_receipt(
                forged,
                expected_runtime_instance_id=host.runtime.runtime_instance_id,
                expected_source_revision=host.runtime.source_revision,
                require_engineered_claim=True,
            )
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(authority|authorization|digest|actor|provenance|receipt)"):
            event_receipt_to_event_row(host, forged)


if __name__ == "__main__":
    unittest.main()
