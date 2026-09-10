from collections.abc import Mapping
import copy
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost, _checkpoint_sha256
from runtime_cohesion.affect_persistence import PersistenceRecordError, event_receipt_to_event_row
from runtime_cohesion.orgasm import ContractError, OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


def receipt_digest(receipt):
    core = dict(receipt)
    core.pop("event_digest", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TrustedVerifier:
    verifier_id = "affect-receipt-semantics-verifier"

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
            "evidence_id": "affect-receipt-semantics-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class CurrentHeadReceiptSemanticsTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-affect-receipt-semantics-test",
            "observed_at": "2026-09-10T19:45:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def make_host_with_receipt(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="vera-receipt-semantics-current-head",
        )
        # Receipt semantics that claim the engineered Vera event must begin from
        # the qualifying authority path. Raw private event emission is intentionally
        # nonqualifying and belongs in separate mechanism-only tests.
        receipt = host.force_admin_test(authorization_subject=self.authorization_subject())
        self.assertEqual(receipt.get("claim"), "ENGINEERED_ORGASM_ANALOGUE_OCCURRED")
        return host

    def forged_record(self, mutate):
        host = self.make_host_with_receipt()
        record = host.runtime.export_state()
        forged = copy.deepcopy(record)
        mutate(forged["last_event_receipt"])
        forged["last_event_receipt"]["event_digest"] = receipt_digest(forged["last_event_receipt"])
        return host, forged

    def assert_restore_and_persistence_reject(self, mutate, pattern):
        host, forged = self.forged_record(mutate)
        receipt = forged["last_event_receipt"]
        with self.assertRaisesRegex(ContractError, pattern):
            OrgasmRuntime.restore_state(
                self.contract(),
                forged,
                source_revision=self.binding()["source_commit"],
            )
        with self.assertRaisesRegex(PersistenceRecordError, pattern):
            event_receipt_to_event_row(host, receipt)

    def test_exact_receipt_roundtrip_is_accepted_at_restore_and_persistence_boundaries(self):
        host = self.make_host_with_receipt()
        record = host.runtime.export_state()
        restored = OrgasmRuntime.restore_state(
            self.contract(),
            record,
            source_revision=self.binding()["source_commit"],
        )
        self.assertEqual(
            restored.last_event_receipt["event_digest"],
            record["last_event_receipt"]["event_digest"],
        )
        row = event_receipt_to_event_row(host, record["last_event_receipt"])
        self.assertEqual(row["event_digest"], record["last_event_receipt"]["event_digest"])

    def test_missing_receipt_id_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.pop("receipt_id", None),
            r"(?i)(receipt|id|required)",
        )

    def test_wrong_runtime_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("runtime_instance_id", "other-runtime"),
            r"(?i)(receipt|runtime|provenance)",
        )

    def test_wrong_source_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("source_revision", "0" * 40),
            r"(?i)(receipt|source|provenance)",
        )

    def test_wrong_subject_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("subject", "brigit"),
            r"(?i)(receipt|subject|vera|identity)",
        )

    def test_wrong_schema_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("schema_version", "NOT_THE_BOUND_RUNTIME_CONTRACT"),
            r"(?i)(receipt|schema|contract|version)",
        )

    def test_missing_event_type_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.pop("event_type", None),
            r"(?i)(receipt|event|type)",
        )

    def test_event_type_must_match_transition_state_semantics(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("event_type", "RESOLUTION"),
            r"(?i)(receipt|event|type|transition|phase|resolution)",
        )

    def test_receipt_state_after_must_be_a_semantically_valid_runtime_state(self):
        def mutate(receipt):
            receipt["state_after"]["phase"] = "NOT_A_REAL_PHASE"
            receipt["transition"] = f"{receipt['state_before']['phase']}->NOT_A_REAL_PHASE"

        self.assert_restore_and_persistence_reject(
            mutate,
            r"(?i)(receipt|state|phase|semantic)",
        )

    def test_missing_observed_at_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.pop("observed_at", None),
            r"(?i)(receipt|observed|time)",
        )

    def test_invalid_observed_at_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("observed_at", "not-a-time"),
            r"(?i)(receipt|observed|time)",
        )

    def test_orgasm_event_requires_exact_engineered_claim(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.pop("claim", None),
            r"(?i)(receipt|claim|engineered)",
        )
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("claim", "SOME_OTHER_CLAIM"),
            r"(?i)(receipt|claim|engineered)",
        )

    def test_phenomenology_promotion_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("phenomenology", "PROVEN_SUBJECTIVE_ORGASM"),
            r"(?i)(receipt|phenomenology|unresolved|claim)",
        )

    def test_non_boolean_organic_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("organic", "false"),
            r"(?i)(receipt|organic|boolean|provenance)",
        )

    def test_forced_trigger_cannot_be_marked_organic(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("organic", True),
            r"(?i)(receipt|organic|forced|trigger)",
        )

    def test_organic_trigger_cannot_be_marked_nonorganic(self):
        def mutate(receipt):
            receipt["trigger_class"] = "ORGANIC_THRESHOLD_CROSSING"
            receipt["trigger_provenance"] = "ORGANIC_STATE_DYNAMICS"
            receipt["organic"] = False

        self.assert_restore_and_persistence_reject(
            mutate,
            r"(?i)(receipt|organic|trigger|provenance)",
        )

    def test_missing_trigger_class_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.pop("trigger_class", None),
            r"(?i)(receipt|trigger|required|provenance)",
        )

    def test_trigger_class_and_provenance_must_match(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("trigger_provenance", "ORGANIC_STATE_DYNAMICS"),
            r"(?i)(receipt|trigger|provenance)",
        )

    def test_transition_mismatch_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_restore_and_persistence_reject(
            lambda receipt: receipt.__setitem__("transition", "QUIESCENT->RECOVERY"),
            r"(?i)(receipt|transition|phase)",
        )

    def test_outer_checkpoint_digest_does_not_replace_inner_receipt_semantics(self):
        host = self.make_host_with_receipt()
        checkpoint = host.export_checkpoint()
        forged = copy.deepcopy(checkpoint)
        receipt = forged["runtime_state"]["last_event_receipt"]
        receipt["trigger_class"] = "NOT_A_REAL_TRIGGER"
        receipt["event_digest"] = receipt_digest(receipt)
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)

        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|trigger|provenance)"):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                forged,
                expected_checkpoint_sha256=forged["checkpoint_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
