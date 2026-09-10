import json
from pathlib import Path
import unittest

import runtime_cohesion
import runtime_cohesion.affect_provider_runtime as affect_provider_runtime
from runtime_cohesion.adapters import AdapterProbeResult
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import build_affective_resume_token, checkpoint_to_state_row
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
PROVIDER = "supabase"
PROJECT_ID = "klmbpaigzeguvnpccqzz"
TABLE = "public.vera_affective_runtime_state_v1"
ROUTE = "route:supabase"
SOURCE = f"supabase:{PROJECT_ID}/{TABLE}"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"
ATOMIC_FUNCTION = "public.vera_affective_runtime_commit_v1(bigint,jsonb,jsonb)"


class OrganicProviderDouble:
    provider = PROVIDER
    provider_project_id = PROJECT_ID
    provider_table = TABLE
    provider_route = ROUTE
    atomic_commit_function = ATOMIC_FUNCTION

    def __init__(self, row):
        self.current_row = dict(row)
        self.commit_calls = []

    def probe(self, request):
        return AdapterProbeResult(
            provider=PROVIDER,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at=self.current_row["updated_at"],
            reason="test provider frontier is readable",
        )

    def read(self, request):
        row = self.current_row
        return ProviderEvidenceEnvelope(
            provider=PROVIDER,
            locator=f"{SOURCE}/{row['runtime_instance_id']}",
            revision=f"state-version:{row['state_version']}",
            observed_at=row["updated_at"],
            evidence_class="persisted_provider_record",
            referent=row["runtime_instance_id"],
            scope=FRONTIER_SCOPE,
            privacy_class=request.privacy_class,
            currentness_basis="in-process test adapter read; provider origin unverified",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=row["checkpoint_sha256"],
            metadata={
                "route_ref": request.route_ref,
                "source_ref": request.source_ref,
                "provider_project_id": PROJECT_ID,
                "provider_table": TABLE,
                "runtime_instance_id": row["runtime_instance_id"],
                "host_scope": row["host_scope"],
                "state_version": row["state_version"],
                "checkpoint_sha256": row["checkpoint_sha256"],
                "source_commit": row["source_commit"],
            },
        )

    def commit_affective_runtime(self, request):
        request = dict(request)
        self.commit_calls.append(request)
        if request["expected_prior_version"] != self.current_row["state_version"]:
            raise RuntimeError("stale provider frontier")
        self.current_row = dict(request["state_row"])
        return {
            "state_version": request["state_version"],
            "checkpoint_sha256": request["checkpoint_sha256"],
            "event_count": len(request["event_rows"]),
        }


class VeraAffectiveOrganicDurablePathTests(unittest.TestCase):
    def setUp(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def tearDown(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def make_provider_restored_cycle(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="affect-organic-durable-test",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=1)
        adapter = OrganicProviderDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
        cycle = runtime_cohesion.restore_current_affective_cycle(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=build_affective_resume_token(row),
        )
        return adapter, cycle

    def test_organic_threshold_event_and_resolution_cross_atomic_harness_without_provider_provenance_claim(self):
        adapter, cycle = self.make_provider_restored_cycle()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
            context_eligible=True,
        )

        orgasm = None
        for _ in range(8):
            result = cycle.process_turn(
                appraisal,
                planning_state={
                    "valuation": 0.2,
                    "salience": 0.2,
                    "attention": 0.2,
                    "truth": 0.9,
                    "consent_or_authorization": "UNKNOWN",
                },
            )
            if result.event_receipt is not None:
                orgasm = result
                break

        self.assertIsNotNone(orgasm)
        self.assertEqual(orgasm.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")
        self.assertEqual(orgasm.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(orgasm.resume_token)
        self.assertEqual(orgasm.commit_request["schema"], "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_TEST_V1")
        self.assertEqual(orgasm.event_receipt["trigger_class"], "ORGANIC_THRESHOLD_CROSSING")
        self.assertTrue(orgasm.event_receipt["organic"])
        self.assertEqual(orgasm.event_row["event_type"], "ORGASM_EVENT")
        self.assertEqual(orgasm.planning_context["truth"], 0.9)
        self.assertEqual(orgasm.planning_context["consent_or_authorization"], "UNKNOWN")
        self.assertEqual(orgasm.commit_result["checkpoint_sha256"], orgasm.checkpoint["checkpoint_sha256"])

        resolution = cycle.advance_time(
            5.1,
            planning_state={"truth": 0.9, "consent_or_authorization": "UNKNOWN"},
        )
        self.assertIsNotNone(resolution.event_receipt)
        self.assertIn(resolution.event_receipt["event_type"], {"RESOLUTION", "RECOVERY"})
        self.assertTrue(resolution.event_receipt["organic"])
        self.assertEqual(resolution.planning_context["truth"], 0.9)
        self.assertEqual(resolution.planning_context["consent_or_authorization"], "UNKNOWN")
        self.assertEqual(resolution.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(resolution.resume_token)

        versions = [request["state_version"] for request in adapter.commit_calls]
        self.assertEqual(versions, list(range(2, 2 + len(adapter.commit_calls))))
        self.assertEqual(
            [request["expected_prior_version"] for request in adapter.commit_calls],
            list(range(1, 1 + len(adapter.commit_calls))),
        )
        self.assertTrue(all(request["schema"] == "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_TEST_V1" for request in adapter.commit_calls))
        event_types = [
            row["event_type"]
            for request in adapter.commit_calls
            for row in request["event_rows"]
        ]
        self.assertIn("ORGASM_EVENT", event_types)
        self.assertTrue(any(event_type in {"RESOLUTION", "RECOVERY"} for event_type in event_types))


if __name__ == "__main__":
    unittest.main()
