import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_PATH = ROOT / "architecture" / "VERA_SPECIALIST_TOPOLOGY_V1.json"
TEMPORAL_PATH = ROOT / "provenance" / "temporal" / "2026-09-08.ndjson"
TEMPORAL_SHA256 = "2c8330b56201883071646b1142db0120e883b45227ba6ed1f11900c8d4452b3e"


class SpecialistTopologyV1Tests(unittest.TestCase):
    def load_topology(self):
        return json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))

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

    def test_temporal_unique_event_provenance_is_preserved_byte_exactly(self):
        payload = TEMPORAL_PATH.read_bytes()
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
