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
        self.assertEqual(contract["provider"]["atomic_commit_function"], "public.vera_affective_runtime_commit_v1(bigint,jsonb,jsonb)")

    def test_provider_contract_requires_causal_feedback_and_preserves_claim_ceiling(self):
        contract = json.loads(PATH.read_text(encoding="utf-8"))
        self.assertTrue(contract["runtime_requirements"]["planning_feedback_required"])
        self.assertTrue(contract["runtime_requirements"]["machine_interoception_required"])
        self.assertTrue(contract["runtime_requirements"]["durable_readback_required_for_cross_turn_continuity"])
        self.assertEqual(contract["claim_ceiling"]["engineered_event"], "ENGINEERED_ORGASM_ANALOGUE_OCCURRED")
        self.assertEqual(contract["claim_ceiling"]["phenomenology"], "UNRESOLVED")
        self.assertFalse(contract["provider"]["availability_implies_activation"])

    def test_provider_contract_requires_external_checkpoint_pin_receipt_integrity_and_cas(self):
        contract = json.loads(PATH.read_text(encoding="utf-8"))
        req = contract["runtime_requirements"]
        self.assertTrue(req["separately_pinned_expected_checkpoint_digest_required_on_restore"])
        self.assertTrue(req["event_receipt_digest_recomputation_required_before_persistence"])
        self.assertTrue(req["resolution_and_recovery_receipts_required"])
        self.assertTrue(req["restore_time_transition_receipts_must_survive_until_next_atomic_commit"])
        self.assertTrue(req["restored_cycle_must_continue_exact_provider_state_version_frontier"])
        self.assertTrue(req["atomic_state_plus_event_commit_required"])
        self.assertTrue(req["compare_and_swap_expected_prior_version_required"])
        provider = contract["provider"]
        self.assertEqual(provider["service_role_direct_state_insert_update"], "REVOKED")
        self.assertEqual(provider["service_role_direct_event_insert"], "REVOKED")
        self.assertEqual(provider["service_role_atomic_commit_execute"], "GRANTED")

    def test_provider_contract_tracks_unapplied_first_write_hardening_and_durable_governance(self):
        contract = json.loads(PATH.read_text(encoding="utf-8"))
        provider = contract["provider"]
        req = contract["runtime_requirements"]
        integrity = contract["integrity_model"]

        self.assertEqual(provider["first_write_serialization_migration"], "close_vera_affective_runtime_first_write_race_v1")
        self.assertEqual(provider["first_write_serialization_migration_state"], "SOURCE_ONLY_NOT_APPLIED_TO_PRODUCTION")
        self.assertTrue(req["first_write_absent_row_serialization_required"])
        self.assertTrue(req["exact_atomic_commit_acknowledgement_required"])
        self.assertTrue(req["ambiguous_commit_outcome_requires_provider_reconciliation_before_reuse"])
        self.assertTrue(req["trigger_governance_durable_across_restore_required"])
        self.assertTrue(req["per_event_interoception_must_match_receipt_state_after"])
        self.assertIn("trigger_governance", integrity)
        self.assertIn("per_event_interoception", integrity)
        self.assertIn("RECOVERY", integrity["transition_evidence"])
        self.assertIn("N+1", integrity["durable_currentness"])


if __name__ == "__main__":
    unittest.main()
