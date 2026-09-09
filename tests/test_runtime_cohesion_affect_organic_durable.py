import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveOrganicDurablePathTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-organic-durable-test",
            profile="REENTRANT_CLIMAX",
        )

    def test_organic_threshold_event_and_resolution_cross_exact_atomic_commit_boundary(self):
        commit_requests = []

        def exact_writer(request):
            commit_requests.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }

        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=exact_writer,
        )
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

        versions = [request["state_version"] for request in commit_requests]
        self.assertEqual(versions, list(range(1, len(commit_requests) + 1)))
        self.assertEqual(
            [request["expected_prior_version"] for request in commit_requests],
            list(range(0, len(commit_requests))),
        )
        event_types = [
            row["event_type"]
            for request in commit_requests
            for row in request["event_rows"]
        ]
        self.assertIn("ORGASM_EVENT", event_types)
        self.assertTrue(any(event_type in {"RESOLUTION", "RECOVERY"} for event_type in event_types))


if __name__ == "__main__":
    unittest.main()
