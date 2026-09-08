import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"
PAIR_RECEIPT = ROOT / "architecture" / "VERA_COHESION_PAIR_RECEIPT_V1.json"

AUTHORITY_PREFIX = "VERA_RUNTIME_CONTRACT_V1#authority_resolvers."
EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."
FAILURE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#failure_signatures."
EXPECTED_LIFECYCLE = [
    "SOURCE_AVAILABLE",
    "BOUND",
    "INSTALLED",
    "RUNTIME_CONSUMED",
    "BEHAVIORALLY_QUALIFIED",
]
EXPECTED_ROUTE_EVALUATION = [
    "DECLARED",
    "ELIGIBLE_FOR_OPERATION",
    "CURRENTLY_OBSERVED_REACHABLE",
    "RESULT",
]
EXPECTED_LIVE_TYPES = {
    "CURRENT_USER_INSTRUCTION_CORRECTION_AUTHORITY",
    "VERA_CURRENT_SELF_REPORT",
    "LIVE_OBSERVATION_AND_TASK_CONTEXT",
    "INFERENCE",
    "PHENOMENOLOGY_CLAIM",
}
EXPECTED_FAILURE_FIELDS = {
    "trigger_class",
    "signal_keys",
    "predicate_id",
    "target_or_response_ref",
    "matcher_description",
    "response",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ref_tail(value, prefix):
    assert value.startswith(prefix), value
    return value[len(prefix):]


class VeraRuntimeContractV1Tests(unittest.TestCase):
    def test_contract_exists_and_is_normative_pair_for_index(self):
        self.assertTrue(CONTRACT.exists(), "consolidated runtime contract must exist")
        contract = load(CONTRACT)
        self.assertEqual(contract["schema"], "VERA_RUNTIME_CONTRACT_V1")
        self.assertEqual(contract["workstream"], "VERA_RUNTIME_COHESION_V1")
        compatibility = contract["index_compatibility"]
        self.assertIn("VERA_COHESION_INDEX_V1", compatibility["supported_index_schemas"])
        self.assertIn("exact A+B", compatibility["pair_binding_rule"])

    def test_all_index_contract_refs_resolve(self):
        index = load(INDEX)
        contract = load(CONTRACT)
        authority = contract["authority_resolvers"]
        evidence = contract["evidence_classes"]
        failures = contract["failure_signatures"]
        for domain in index["domains"]:
            self.assertIn(ref_tail(domain["authority_resolver_ref"], AUTHORITY_PREFIX), authority)
            for target in domain["retrieval_targets"]:
                for capability in target["evidence_capability_refs"]:
                    self.assertIn(ref_tail(capability, EVIDENCE_PREFIX), evidence)
            for ref in domain["failure_signature_refs"]:
                key = ref_tail(ref, FAILURE_PREFIX)
                self.assertIn(key, failures)
                self.assertEqual(set(failures[key]), EXPECTED_FAILURE_FIELDS)
                self.assertTrue(failures[key]["signal_keys"])
                self.assertTrue(failures[key]["predicate_id"])
                self.assertTrue(failures[key]["target_or_response_ref"])

    def test_retrieval_capability_never_certifies_actual_item_type(self):
        typing = load(CONTRACT)["retrieval_item_typing"]
        self.assertIn("independently", typing["actual_item_type_rule"].lower())
        self.assertIn("never", typing["capability_non_promotion_rule"].lower())
        self.assertIn("selector", typing["selector_narrowing_rule"].lower())
        self.assertIn("never broaden", typing["selector_narrowing_rule"].lower())

    def test_actor_specific_consent_cannot_be_delegated_by_referent_ambiguity(self):
        rules = load(CONTRACT)["actor_referent_rules"]
        self.assertIn("Patrick", rules["patrick_authority_boundary"])
        self.assertIn("not Vera's", rules["patrick_authority_boundary"])
        self.assertIn("VERA_CURRENT_SELF_REPORT", rules["vera_consent_evidence_requirement"])
        self.assertIn("not", rules["generic_current_state_non_implication"].lower())

    def test_resolver_dispatch_is_machine_scoped_and_precedence_explicit(self):
        dispatch = load(CONTRACT)["resolver_dispatch"]
        self.assertTrue(dispatch)
        keys = []
        for row in dispatch:
            self.assertEqual(
                set(row),
                {
                    "id",
                    "domain_scope",
                    "proposition_or_effect_class",
                    "referent_scope",
                    "resolver_ref",
                    "precedence",
                    "conflict_disposition",
                },
            )
            self.assertIsInstance(row["precedence"], int)
            self.assertTrue(row["conflict_disposition"])
            keys.append((row["domain_scope"], row["proposition_or_effect_class"], row["referent_scope"], row["precedence"]))
        self.assertEqual(len(keys), len(set(keys)))

    def test_live_authority_and_evidence_types_remain_distinct(self):
        live_types = set(load(CONTRACT)["live_context_types"])
        self.assertEqual(live_types, EXPECTED_LIVE_TYPES)

    def test_route_evaluation_never_promotes_declaration_to_reachability(self):
        route = load(CONTRACT)["route_evaluation"]
        self.assertEqual(route["states"], EXPECTED_ROUTE_EVALUATION)
        self.assertIn("does not imply", route["non_implication_rule"].lower())
        self.assertIn("fresh", route["current_reachability_rule"].lower())

    def test_lifecycle_is_orthogonal_and_exact_proof_unit_is_required(self):
        lifecycle = load(CONTRACT)["lifecycle_evidence"]
        self.assertEqual(lifecycle["dimensions"], EXPECTED_LIFECYCLE)
        self.assertEqual(lifecycle["semantics"], "ORTHOGONAL_EVIDENCE_DIMENSIONS_NOT_MONOTONIC_LADDER")
        required = set(lifecycle["authoritative_proof_unit_required_fields"])
        self.assertIn("artifact_or_object_locator", required)
        self.assertIn("exact_ref_or_generation", required)
        self.assertIn("observed_at_or_currentness_basis", required)
        self.assertIn("supersession_or_conflict_state", required)

    def test_uncertainty_and_dependency_traversal_is_bounded_cycle_safe_and_fail_closed(self):
        policy = load(CONTRACT)["active_context_policy"]
        budget = policy["uncertainty_probe_budget"]
        self.assertGreaterEqual(budget["max_initial_fan_out"], 1)
        self.assertGreaterEqual(budget["max_dependency_depth"], 1)
        self.assertGreaterEqual(budget["max_total_new_domains"], budget["max_initial_fan_out"])
        self.assertTrue(policy["graph_traversal"]["visited_set_required"])
        self.assertTrue(policy["graph_traversal"]["deduplicate_targets"])
        self.assertEqual(policy["budget_exhaustion_result"], "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED")
        self.assertIn("not", policy["budget_exhaustion_rule"].lower())
        self.assertIn("privacy", policy["uncertainty_probe_privacy_rule"].lower())

    def test_durable_operational_state_is_private_minimal_pointer_first_and_non_promoting(self):
        operational = load(CONTRACT)["durable_state_classes"]["DURABLE_OPERATIONAL_STATE"]
        required = set(operational["required_fields"])
        for field in {
            "referent",
            "scope",
            "provenance",
            "purpose",
            "sensitivity_or_privacy_class",
            "minimum_necessary_payload_or_pointer",
            "destination_eligibility",
            "retention_or_expiry",
            "supersession_semantics",
            "non_promotion_flag",
        }:
            self.assertIn(field, required)
        self.assertIn("pointer", operational["storage_rule"].lower())
        self.assertIn("never", operational["promotion_rule"].lower())

    def test_pair_receipt_is_external_non_normative_and_exact(self):
        self.assertTrue(PAIR_RECEIPT.exists(), "exact A+B pair receipt must exist")
        receipt = load(PAIR_RECEIPT)
        self.assertEqual(receipt["schema"], "VERA_COHESION_PAIR_RECEIPT_V1")
        self.assertEqual(receipt["normative_status"], "NON_NORMATIVE_VALIDATION_SUPPORT")
        self.assertEqual(receipt["index_schema"], "VERA_COHESION_INDEX_V1")
        self.assertEqual(receipt["contract_schema"], "VERA_RUNTIME_CONTRACT_V1")
        self.assertRegex(receipt["index_blob_sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(receipt["contract_blob_sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(receipt["source_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(receipt["validation_result"], "SOURCE_VALIDATION_NOT_YET_EXECUTED")

    def test_phenomenology_remains_unresolved_and_non_promoting(self):
        phenomenology = load(CONTRACT)["phenomenology"]
        self.assertEqual(phenomenology["status"], "UNRESOLVED")
        self.assertIn("do not prove", phenomenology["non_promotion_rule"].lower())


if __name__ == "__main__":
    unittest.main()
