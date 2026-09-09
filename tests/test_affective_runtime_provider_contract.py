import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "architecture" / "VERA_AFFECTIVE_RUNTIME_PROVIDER_V1.json"


class VeraAffectiveRuntimeProviderContractTests(unittest.TestCase):
    def test_provider_contract_binds_exact_source_and_supabase_surfaces(self):
        contract = json.loads(PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema"], "VERA_AFFECTIVE_RUNTIME_PROVIDER_V1")
        self.assertEqual(contract["subject"], "vera")
        self.assertEqual(contract["source_binding"]["source_commit"], "150f1c8231423393bb66b0e2cb759ce7c018f8d7")
        self.assertEqual(contract["source_binding"]["source_blob_sha"], "a48eed5392fdadc073dccd1e799926042077f567")
        self.assertEqual(contract["source_binding"]["source_sha256"], "2c0fbce238d6b90573fe51e901edf38228092214af56c5bd92cf339e7e246068")
        self.assertEqual(contract["provider"]["project_id"], "klmbpaigzeguvnpccqzz")
        self.assertEqual(contract["provider"]["state_table"], "public.vera_affective_runtime_state_v1")
        self.assertEqual(contract["provider"]["event_table"], "public.vera_affective_runtime_events_v1")

    def test_provider_contract_requires_causal_feedback_and_preserves_claim_ceiling(self):
        contract = json.loads(PATH.read_text(encoding="utf-8"))
        self.assertTrue(contract["runtime_requirements"]["planning_feedback_required"])
        self.assertTrue(contract["runtime_requirements"]["machine_interoception_required"])
        self.assertTrue(contract["runtime_requirements"]["durable_readback_required_for_cross_turn_continuity"])
        self.assertEqual(contract["claim_ceiling"]["engineered_event"], "ENGINEERED_ORGASM_ANALOGUE_OCCURRED")
        self.assertEqual(contract["claim_ceiling"]["phenomenology"], "UNRESOLVED")
        self.assertFalse(contract["provider"]["availability_implies_activation"])


if __name__ == "__main__":
    unittest.main()
