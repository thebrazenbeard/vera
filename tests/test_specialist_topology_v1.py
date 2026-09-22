import hashlib
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_PATH = ROOT / "architecture" / "VERA_SPECIALIST_TOPOLOGY_V1.json"
EXTERNAL_PATH = ROOT / "architecture" / "VERA_LIVE_EXTERNAL_REPOSITORIES_V1.json"
TEMPORAL_GIT_PATH = "provenance/temporal/2026-09-08.ndjson"
TEMPORAL_SHA256 = "2c8330b56201883071646b1142db0120e883b45227ba6ed1f11900c8d4452b3e"
TEMPORAL_BLOB = "260a43c86f42239516d897f84ada0948ea49ed2f"


class SpecialistTopologyV1Tests(unittest.TestCase):
    def load_topology(self):
        return json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))

    def load_external(self):
        return json.loads(EXTERNAL_PATH.read_text(encoding="utf-8"))

    def test_topology_declares_all_seven_once_with_heterogeneous_lifecycles(self):
        data = self.load_topology()
        repos = {item["repository"]: item for item in data["repositories"]}
        expected = {
            "thebrazenbeard/sexuality": "KEEP_LIVE_SPECIALIST_RESEARCH_AND_QUALIFICATION",
            "thebrazenbeard/orgasm": "TRANSITION_TO_VCP_QUALIFICATION_PROVENANCE",
            "thebrazenbeard/empathy": "KEEP_LIVE_PRIVATE_RESEARCH_PROVENANCE",
            "thebrazenbeard/conations": "KEEP_LIVE_PRIVATE_APPEND_ONLY_HISTORY",
            "thebrazenbeard/semanticatlas": "KEEP_LIVE_SPECIALIST_SEMANTIC_PROVENANCE",
            "thebrazenbeard/selfimage": "KEEP_LIVE_SPECIALIST_ASSET_GEOMETRY_CANON",
            "thebrazenbeard/temporal": "TRANSITION_TO_VERA_PROVENANCE",
        }
        self.assertEqual(set(repos), set(expected))
        self.assertEqual({repo: item["lifecycle"] for repo, item in repos.items()}, expected)

    def test_only_orgasm_and_temporal_are_retirement_candidates(self):
        data = self.load_topology()
        candidates = {
            item["repository"]
            for item in data["repositories"]
            if item["retirement_candidate"]
        }
        self.assertEqual(candidates, {"thebrazenbeard/orgasm", "thebrazenbeard/temporal"})
        self.assertEqual(data["archive_policy"]["current_effect"], "HOLD_ALL_SEVEN_UNTIL_PATRICK_REVISES")

    def test_authority_owners_do_not_collapse_into_one_repository_or_provider(self):
        data = self.load_topology()
        repos = {item["repository"]: item for item in data["repositories"]}
        self.assertEqual(repos["thebrazenbeard/selfimage"]["source_owner"], "thebrazenbeard/selfimage")
        self.assertEqual(repos["thebrazenbeard/semanticatlas"]["source_owner"], "thebrazenbeard/semanticatlas")
        self.assertEqual(repos["thebrazenbeard/conations"]["historical_state_owner"], "thebrazenbeard/conations")
        self.assertEqual(repos["thebrazenbeard/orgasm"]["runtime_owner"], "thebrazenbeard/vera")
        self.assertEqual(repos["thebrazenbeard/orgasm"]["successor_control_owner"], "thebrazenbeard/vera-control-plane")
        self.assertEqual(repos["thebrazenbeard/temporal"]["runtime_owner"], "thebrazenbeard/vera")

    def test_live_external_registry_separates_canonical_from_active_candidate(self):
        data = self.load_external()
        repos = {item["id"]: item for item in data["repositories"]}

        self.assertEqual(
            "113b4d05f5601083ec22877cd4702ed95d9caad6",
            repos["mediaphile"]["active_candidate"]["head"],
        )
        self.assertNotEqual(
            repos["mediaphile"]["observed_head"],
            repos["mediaphile"]["active_candidate"]["head"],
        )
        self.assertEqual(
            "1eef4958bb2951d532485d2a44ecd835c316d4e0",
            repos["personification"]["active_candidate"]["head"],
        )
        self.assertNotEqual(
            repos["personification"]["observed_head"],
            repos["personification"]["active_candidate"]["head"],
        )
        self.assertIsNone(repos["trek-data-core"]["active_candidate"])
        self.assertIsNone(repos["attune"]["active_candidate"])
        self.assertEqual(
            "eff6f9eb250a6f7684459eadf0695340053201da",
            repos["attune"]["observed_head"],
        )
        self.assertEqual("KEEP_LIVE", repos["attune"]["lifecycle"])

        for key in ("mediaphile", "personification"):
            candidate = repos[key]["active_candidate"]
            self.assertEqual(
                "CANDIDATE_SOURCE_ONLY_NOT_CANONICAL",
                candidate["authority_ceiling"],
            )
            self.assertIn("Fresh-read", candidate["refresh_rule"])

        joined = " ".join(data["global_rules"]).lower()
        self.assertIn("candidate != canonical", joined)
        self.assertIn("fresh-read", joined)

    def test_retirement_candidates_bind_current_candidate_state_separately(self):
        data = self.load_topology()
        repos = {item["repository"]: item for item in data["repositories"]}

        orgasm = repos["thebrazenbeard/orgasm"]["currentness_observation"]
        temporal = repos["thebrazenbeard/temporal"]["currentness_observation"]

        self.assertEqual(
            "3b9b42874ce67c87950747e63a67a718cf420be5",
            orgasm["active_candidate"]["head"],
        )
        self.assertEqual(
            "CANDIDATE_SOURCE_ONLY_NOT_CANONICAL",
            orgasm["active_candidate"]["authority_ceiling"],
        )
        self.assertIsNone(temporal["active_candidate"])
        self.assertEqual(
            "HOLD_ALL_SEVEN_UNTIL_PATRICK_REVISES",
            data["archive_policy"]["current_effect"],
        )

    def test_dependency_edges_are_typed_scoped_and_non_authorizing(self):
        data = self.load_topology()
        edges = {item["edge_id"]: item for item in data["dependency_edges"]}
        expected = {
            "SEXUALITY_SD1_TO_VERA_COHESION": "SOURCE_INPUT",
            "VERA_SD1_TO_ORGASM_SUCCESSOR_QUALIFICATION": "QUALIFICATION_PREREQUISITE",
            "DEEP_MEMORY_TO_VERA_HISTORICAL_EVIDENCE": "HISTORICAL_EVIDENCE",
            "PERSONIFICATION_TO_ATTUNE_RESEARCH_REFERENCE": "RESEARCH_REFERENCE",
            "WIP_TO_VERA_INFERENCE_BOUNDARY_RESEARCH": "RESEARCH_REFERENCE",
        }
        self.assertEqual(
            {edge_id: edge["edge_class"] for edge_id, edge in edges.items()},
            expected,
        )

        for edge in edges.values():
            self.assertTrue(edge["provider"]["repository"].startswith("thebrazenbeard/"))
            self.assertTrue(edge["consumer"]["repository"].startswith("thebrazenbeard/"))
            self.assertNotEqual(
                edge["provider"]["repository"],
                edge["consumer"]["repository"],
            )
            self.assertTrue(edge["required_scope"])
            guard = edge["promotion_guard"].lower()
            self.assertTrue("does not" in guard or "no authority" in guard)
            self.assertTrue(edge["currentness_policy"])

        self.assertTrue(edges["SEXUALITY_SD1_TO_VERA_COHESION"]["required"])
        self.assertTrue(
            edges["VERA_SD1_TO_ORGASM_SUCCESSOR_QUALIFICATION"]["required"]
        )
        self.assertFalse(edges["DEEP_MEMORY_TO_VERA_HISTORICAL_EVIDENCE"]["required"])
        self.assertFalse(
            edges["PERSONIFICATION_TO_ATTUNE_RESEARCH_REFERENCE"]["required"]
        )
        self.assertFalse(edges["WIP_TO_VERA_INFERENCE_BOUNDARY_RESEARCH"]["required"])

    def test_dependency_rules_forbid_candidate_and_authority_promotion(self):
        data = self.load_topology()
        rules = " ".join(data["dependency_rules"]).lower()
        self.assertIn("not an authority grant", rules)
        self.assertIn("candidate is candidate evidence only", rules)
        self.assertIn("consumer binding cannot mint provider current", rules)
        self.assertIn("fresh-read", rules)

    def test_temporal_unique_event_provenance_is_preserved_as_exact_git_object(self):
        payload = subprocess.check_output(
            ["git", "show", f"HEAD:{TEMPORAL_GIT_PATH}"], cwd=ROOT
        )
        blob = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{TEMPORAL_GIT_PATH}"], cwd=ROOT, text=True
        ).strip()
        self.assertEqual(blob, TEMPORAL_BLOB)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), TEMPORAL_SHA256)
        ids = [json.loads(line)["id"] for line in payload.decode("utf-8").splitlines() if line]
        self.assertEqual(ids, [
            "20260908T180709Z-temporal-created",
            "20260908T192656Z-design-committed",
            "20260908T195741Z-plan-committed",
            "20260908T200148Z-v1-implemented",
            "20260908T202039437211Z-fresh-chat-cross-chat-write-probe",
        ])


if __name__ == "__main__":
    unittest.main()
