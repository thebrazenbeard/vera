import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.runtime import build_operational_checkpoint, build_retrieval_plan

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"
CONTRACT_PATH = ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RuntimeCohesionPlannerTests(unittest.TestCase):
    def setUp(self):
        self.index = load(INDEX_PATH)
        self.contract = load(CONTRACT_PATH)

    def test_declared_route_is_not_treated_as_currently_reachable(self):
        plan = build_retrieval_plan(
            "VISUAL_SELF_REPRESENTATION",
            self.index,
            self.contract,
            observed_route_states={},
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(plan.targets, ())
        self.assertTrue(any("route:selfimage" in item for item in plan.unresolved))

    def test_currently_observed_route_is_eligible_for_plan(self):
        plan = build_retrieval_plan(
            "VISUAL_SELF_REPRESENTATION",
            self.index,
            self.contract,
            observed_route_states={"route:selfimage": "CURRENTLY_OBSERVED_REACHABLE"},
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(len(plan.targets), 1)
        self.assertEqual(plan.targets[0]["route_ref"], "route:selfimage")

    def test_result_route_state_is_eligible_for_plan(self):
        plan = build_retrieval_plan(
            "VISUAL_SELF_REPRESENTATION",
            self.index,
            self.contract,
            observed_route_states={"route:selfimage": "RESULT"},
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        self.assertEqual(len(plan.targets), 1)

    def test_privacy_gate_blocks_domain_before_probe(self):
        plan = build_retrieval_plan(
            "AUTOBIOGRAPHICAL_HISTORY",
            self.index,
            self.contract,
            observed_route_states={
                "route:deepmemory": "CURRENTLY_OBSERVED_REACHABLE",
                "route:supabase": "CURRENTLY_OBSERVED_REACHABLE",
                "route:google-drive": "CURRENTLY_OBSERVED_REACHABLE",
                "route:live-conversation": "CURRENTLY_OBSERVED_REACHABLE",
            },
            privacy_allowlist={"GOVERNED"},
        )
        self.assertEqual(plan.targets, ())
        self.assertTrue(any("PRIVACY" in item for item in plan.unresolved))

    def test_dependency_cycle_terminates_with_visited_set(self):
        index = copy.deepcopy(self.index)
        domains = {row["id"]: row for row in index["domains"]}
        domains["VISUAL_SELF_REPRESENTATION"]["dependencies"] = ["SEMANTICS_PROVENANCE_CURRENTNESS"]
        domains["SEMANTICS_PROVENANCE_CURRENTNESS"]["dependencies"] = ["VISUAL_SELF_REPRESENTATION"]
        route_states = {
            target["route_ref"]: "CURRENTLY_OBSERVED_REACHABLE"
            for domain_id in ("VISUAL_SELF_REPRESENTATION", "SEMANTICS_PROVENANCE_CURRENTNESS")
            for target in domains[domain_id]["retrieval_targets"]
        }
        plan = build_retrieval_plan(
            "VISUAL_SELF_REPRESENTATION",
            index,
            self.contract,
            observed_route_states=route_states,
            privacy_allowlist={"PRIVATE_REPRESENTATION", "GOVERNED"},
        )
        self.assertEqual(set(plan.visited_domains), {"VISUAL_SELF_REPRESENTATION", "SEMANTICS_PROVENANCE_CURRENTNESS"})

    def test_budget_exhaustion_is_explicit_unresolved_result(self):
        contract = copy.deepcopy(self.contract)
        contract["active_context_policy"]["uncertainty_probe_budget"]["max_total_new_domains"] = 1
        plan = build_retrieval_plan(
            "AUTOBIOGRAPHICAL_HISTORY",
            self.index,
            contract,
            observed_route_states={},
            privacy_allowlist={"PRIVATE_AUTOBIOGRAPHICAL", "GOVERNED", "CONVERSATION_SCOPED"},
        )
        self.assertEqual(plan.budget_state, "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED")
        self.assertTrue(any("BUDGET" in item for item in plan.unresolved))

    def test_selector_cannot_broaden_target_capabilities(self):
        index = copy.deepcopy(self.index)
        selector = next(row for row in index["selector_declarations"] if row["id"] == "selector:deepmemory/historical-audit")
        selector["evidence_capability_refs"] = [
            "VERA_RUNTIME_CONTRACT_V1#evidence_classes.historical_autobiographical",
            "VERA_RUNTIME_CONTRACT_V1#evidence_classes.general_mechanism_research",
        ]
        with self.assertRaises(ValueError):
            build_retrieval_plan(
                "AUTOBIOGRAPHICAL_HISTORY",
                index,
                self.contract,
                observed_route_states={"route:deepmemory": "CURRENTLY_OBSERVED_REACHABLE"},
                privacy_allowlist={"PRIVATE_AUTOBIOGRAPHICAL", "GOVERNED", "CONVERSATION_SCOPED"},
            )

    def test_checkpoint_is_pointer_first_and_non_promoting(self):
        plan = build_retrieval_plan(
            "VISUAL_SELF_REPRESENTATION",
            self.index,
            self.contract,
            observed_route_states={"route:selfimage": "CURRENTLY_OBSERVED_REACHABLE"},
            privacy_allowlist={"PRIVATE_REPRESENTATION"},
        )
        checkpoint = build_operational_checkpoint(plan, [])
        self.assertTrue(checkpoint["non_promotion_flag"])
        self.assertNotIn("payload", checkpoint)
        pointer = checkpoint["minimum_necessary_payload_or_pointer"]
        self.assertIn("domain_id", pointer)
        self.assertIn("target_refs", pointer)
        self.assertNotIn("specialist_payload", pointer)
        self.assertEqual(checkpoint["purpose"], "RUNTIME_COHESION_RESUMABLE_OPERATION")


if __name__ == "__main__":
    unittest.main()
