import copy
import hashlib
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import ContractError, OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class AffectiveContractBindingLaunderingTests(unittest.TestCase):
    def canonical_contract_text(self):
        return CONTRACT_PATH.read_text(encoding="utf-8")

    def canonical_contract(self):
        return json.loads(self.canonical_contract_text())

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def partial_contract(self):
        contract = copy.deepcopy(self.canonical_contract())
        contract.pop("authorization_boundary", None)
        contract.pop("participating_systems", None)
        contract["state_families"].pop("stimulus_appraisal", None)
        contract.pop("organic_climax_predicate", None)
        return contract

    def test_partial_contract_cannot_emit_production_claim_bearing_receipt(self):
        binding = self.binding()
        try:
            runtime = OrgasmRuntime(
                self.partial_contract(),
                runtime_instance_id="partial-contract-runtime",
                source_revision=binding["source_commit"],
            )
        except ContractError:
            return

        receipt = runtime.force_admin_test(authorized=True)
        self.assertNotEqual(
            receipt.get("claim"),
            "ENGINEERED_ORGASM_ANALOGUE_OCCURRED",
            "an unbound/partial direct runtime must not emit production engineered-event evidence",
        )

    def test_partial_runtime_cannot_be_laundered_through_canonical_looking_host_binding(self):
        binding = self.binding()
        runtime = OrgasmRuntime(
            self.partial_contract(),
            runtime_instance_id="partial-contract-host-laundering",
            source_revision=binding["source_commit"],
        )
        raw = self.canonical_contract_text().encode("utf-8")

        with self.assertRaisesRegex(AffectiveBindingError, r"(?i)(contract|binding|runtime|source)"):
            VeraAffectiveRuntimeHost(
                runtime,
                binding=binding,
                contract_blob_sha=binding["source_blob_sha"],
                contract_sha256=hashlib.sha256(raw).hexdigest(),
            )

    def test_exact_bound_factory_preserves_positive_canonical_path(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            self.canonical_contract_text(),
            self.binding(),
            runtime_instance_id="canonical-bound-positive-control",
        )
        checkpoint = host.export_checkpoint()
        self.assertEqual(checkpoint["subject"], "vera")
        self.assertEqual(
            checkpoint["source_binding"]["source_commit"],
            self.binding()["source_commit"],
        )
        self.assertEqual(
            checkpoint["source_binding"]["source_blob_sha"],
            self.binding()["source_blob_sha"],
        )


if __name__ == "__main__":
    unittest.main()
