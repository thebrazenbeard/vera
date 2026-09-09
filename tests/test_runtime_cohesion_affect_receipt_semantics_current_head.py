import copy
import hashlib
import json
from pathlib import Path
import unittest

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


class CurrentHeadReceiptSemanticsTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_host_with_receipt(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="vera-receipt-semantics-current-head",
        )
        # Use the private event-emission unit so this semantic-receipt review is
        # independent of the separately unresolved privileged-authority boundary.
        host.runtime._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
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

        with self.assertRaisesRegex(Exception, r"(?i)(receipt|trigger|provenance)"):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                forged,
                expected_checkpoint_sha256=forged["checkpoint_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
