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
UNBOUND_STATUS = "UNBOUND_NON_QUALIFYING"
EXACT_BOUND_STATUS = "EXACT_BOUND_SOURCE"


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

    def mutated_canonical_shaped_contract(self):
        contract = copy.deepcopy(self.canonical_contract())
        original = float(contract["experimental_bootstrap_defaults"]["minimum_coherence_window_ms"])
        contract["experimental_bootstrap_defaults"]["minimum_coherence_window_ms"] = (
            2600 if abs(original - 2600) > 1e-9 else 2700
        )
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
        status = receipt.get("qualification_status") or getattr(
            runtime, "qualification_status", None
        )
        self.assertEqual(
            status,
            UNBOUND_STATUS,
            "if direct engine construction remains available, its evidence must be explicitly non-qualifying rather than merely claim-less",
        )

    def test_partial_plausible_contract_cannot_emit_production_claim(self):
        self.assert_direct_engine_not_production_claim_capable(
            self.stripped_but_plausible_contract(),
            self.binding()["source_commit"],
        )

    def test_canonical_shaped_but_byte_mutated_contract_cannot_emit_production_claim(self):
        self.assert_direct_engine_not_production_claim_capable(
            self.mutated_canonical_shaped_contract(),
            self.binding()["source_commit"],
        )

    def test_arbitrary_source_revision_cannot_make_direct_engine_production_claim_capable(self):
        self.assert_direct_engine_not_production_claim_capable(
            self.canonical_contract(),
            "0" * 40,
        )

    def test_public_base_exact_bound_loader_cannot_mint_production_claim(self):
        runtime = OrgasmRuntime.from_exact_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="direct-exact-bound-loader-negative",
        )
        receipt = runtime.force_admin_test(authorized=True)
        self.assertNotEqual(
            receipt.get("claim"),
            CANONICAL_CLAIM,
            "the public base loader may verify source bytes but may not itself promote a forced event to production evidence",
        )

    def test_exact_bound_host_establishes_source_capability_without_authorizing_an_event(self):
        binding = self.binding()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            binding,
            runtime_instance_id="exact-bound-contract-positive",
        )
        checkpoint = host.export_checkpoint()

        # Exact source binding is necessary for the production claim capability,
        # but it is not itself authority to fire ADMIN_FORCED_TEST or any other
        # event. Authorization/context provenance is a separate runtime boundary.
        self.assertEqual(host.runtime.qualification_status, EXACT_BOUND_STATUS)
        self.assertIsNone(host.runtime.last_event_receipt)
        self.assertEqual(host.runtime.source_revision, binding["source_commit"])
        self.assertEqual(checkpoint["source_binding"]["source_commit"], binding["source_commit"])
        self.assertEqual(checkpoint["source_binding"]["source_blob_sha"], binding["source_blob_sha"])
        self.assertEqual(host.binding["source_repository"], "thebrazenbeard/sexuality")
        self.assertEqual(host.binding["source_path"], "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json")


if __name__ == "__main__":
    unittest.main()
