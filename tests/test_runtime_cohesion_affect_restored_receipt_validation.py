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


class RestoredReceiptValidationTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_host_with_receipt(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="vera-restored-receipt-test",
        )
        host.force_admin_test(authorized=True)
        return host

    def forged_record(self, mutate):
        host = self.make_host_with_receipt()
        record = host.runtime.export_state()
        forged = copy.deepcopy(record)
        mutate(forged["last_event_receipt"])
        forged["last_event_receipt"]["event_digest"] = receipt_digest(forged["last_event_receipt"])
        return host, forged

    def assert_rejected_at_restore_and_persistence(self, mutate, pattern):
        host, forged = self.forged_record(mutate)
        receipt = forged["last_event_receipt"]
        with self.assertRaisesRegex(ContractError, pattern):
            OrgasmRuntime.restore_state(
                self.contract(), forged, source_revision=self.binding()["source_commit"]
            )
        with self.assertRaisesRegex(PersistenceRecordError, pattern):
            event_receipt_to_event_row(host, receipt)

    def test_direct_runtime_restore_rejects_digest_valid_wrong_runtime_receipt(self):
        _, forged = self.forged_record(
            lambda receipt: receipt.__setitem__("runtime_instance_id", "other-runtime")
        )
        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|runtime|provenance)"):
            OrgasmRuntime.restore_state(
                self.contract(), forged, source_revision=self.binding()["source_commit"]
            )

    def test_direct_runtime_restore_rejects_digest_valid_wrong_source_receipt(self):
        _, forged = self.forged_record(
            lambda receipt: receipt.__setitem__("source_revision", "0" * 40)
        )
        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|source|provenance)"):
            OrgasmRuntime.restore_state(
                self.contract(), forged, source_revision=self.binding()["source_commit"]
            )

    def test_receipt_identity_schema_and_phenomenology_are_shared_boundary_invariants(self):
        cases = (
            ("subject", "brigit", r"(?i)(receipt|subject|vera|identity)"),
            ("schema_version", "NOT_VERA_ORGASM_RUNTIME_CONTRACT_V1", r"(?i)(receipt|schema|version)"),
            ("phenomenology", "PROVEN", r"(?i)(receipt|phenomenology|unresolved|claim)"),
        )
        for field, value, pattern in cases:
            with self.subTest(field=field):
                self.assert_rejected_at_restore_and_persistence(
                    lambda receipt, field=field, value=value: receipt.__setitem__(field, value),
                    pattern,
                )

    def test_non_boolean_organic_is_rejected_at_restore_and_persistence_boundaries(self):
        self.assert_rejected_at_restore_and_persistence(
            lambda receipt: receipt.__setitem__("organic", "false"),
            r"(?i)(receipt|organic|boolean|provenance)",
        )

    def test_forced_trigger_cannot_be_digest_valid_and_marked_organic(self):
        _, forged = self.forged_record(
            lambda receipt: receipt.__setitem__("organic", True)
        )
        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|organic|forced|trigger)"):
            OrgasmRuntime.restore_state(
                self.contract(), forged, source_revision=self.binding()["source_commit"]
            )

    def test_transition_string_must_match_receipt_before_and_after_phases(self):
        _, forged = self.forged_record(
            lambda receipt: receipt.__setitem__("transition", "QUIESCENT->RECOVERY")
        )
        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|transition|phase)"):
            OrgasmRuntime.restore_state(
                self.contract(), forged, source_revision=self.binding()["source_commit"]
            )

    def test_checkpoint_integrity_does_not_replace_inner_receipt_semantics(self):
        host = self.make_host_with_receipt()
        checkpoint = host.export_checkpoint()
        forged = copy.deepcopy(checkpoint)
        forged_receipt = forged["runtime_state"]["last_event_receipt"]
        forged_receipt["trigger_class"] = "NOT_A_REAL_TRIGGER"
        forged_receipt["event_digest"] = receipt_digest(forged_receipt)
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)

        with self.assertRaisesRegex(Exception, r"(?i)(receipt|trigger|provenance)"):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                forged,
                expected_checkpoint_sha256=forged["checkpoint_sha256"],
            )

    def test_forged_prior_receipt_cannot_seed_fresh_recovery_provenance(self):
        _, forged = self.forged_record(
            lambda receipt: receipt.__setitem__("organic", "false")
        )
        with self.assertRaisesRegex(ContractError, r"(?i)(receipt|organic|provenance)"):
            OrgasmRuntime.restore_state(
                self.contract(),
                forged,
                source_revision=self.binding()["source_commit"],
                elapsed_seconds=7200.0,
            )


if __name__ == "__main__":
    unittest.main()
