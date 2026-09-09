import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import ContractError, OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
CANONICAL_CLAIM = "ENGINEERED_ORGASM_ANALOGUE_OCCURRED"


class DirectOrgasmContractBindingTests(unittest.TestCase):
    def canonical_contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def stripped_but_plausible_contract(self):
        contract = copy.deepcopy(self.canonical_contract())
        for key in (
            "authorization_boundary",
            "participating_systems",
            "organic_climax_predicate",
            "dynamic_rules",
            "runtime_effects",
            "receipt_requirements",
        ):
            contract.pop(key, None)
        contract["state_families"].pop("stimulus_appraisal", None)
        contract["state_families"].pop("entrainment", None)
        contract["hard_firewalls"].pop("never_directly_establish_or_overwrite", None)
        return contract

    def assert_direct_engine_not_production_claim_capable(self, contract, source_revision):
        try:
            runtime = OrgasmRuntime(
                contract,
                runtime_instance_id="direct-contract-binding-test",
                source_revision=source_revision,
            )
        except ContractError:
            return

        receipt = runtime._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        self.assertNotEqual(
            receipt.get("claim"),
            CANONICAL_CLAIM,
            "an unbound direct engine may not emit the production engineered-event claim",
        )

    def test_partial_plausible_contract_cannot_emit_production_claim(self):
        self.assert_direct_engine_not_production_claim_capable(
            self.stripped_but_plausible_contract(),
            self.binding()["source_commit"],
        )

    def test_arbitrary_source_revision_cannot_make_direct_engine_production_claim_capable(self):
        self.assert_direct_engine_not_production_claim_capable(
            self.canonical_contract(),
            "0" * 40,
        )

    def test_exact_bound_host_path_remains_production_claim_capable(self):
        binding = self.binding()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            binding,
            runtime_instance_id="exact-bound-contract-positive",
        )
        receipt = host.runtime._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        self.assertEqual(receipt["claim"], CANONICAL_CLAIM)
        self.assertEqual(receipt["source_revision"], binding["source_commit"])
        self.assertEqual(host.binding["source_repository"], "thebrazenbeard/sexuality")
        self.assertEqual(host.binding["source_path"], "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json")
        self.assertEqual(host.contract_blob_sha, binding["source_blob_sha"])


if __name__ == "__main__":
    unittest.main()
