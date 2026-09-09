import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveAtomicCommitAcknowledgementTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-commit-ack-test",
            profile="REENTRANT_CLIMAX",
        )

    @staticmethod
    def exact_writer_recorder(requests):
        def exact_writer(request):
            requests.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }
        return exact_writer

    def test_ambiguous_atomic_commit_ack_poison_cycle_and_does_not_advance_version(self):
        requests = []

        def ambiguous_writer(request):
            requests.append(dict(request))
            return None

        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=ambiguous_writer,
        )

        with self.assertRaises(RuntimeError):
            cycle.force_admin_test(
                authorized=True,
                planning_state={"truth": 1.0},
            )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["expected_prior_version"], 0)
        self.assertEqual(requests[0]["state_version"], 1)

        with self.assertRaises(RuntimeError):
            cycle.advance_time(5.1, planning_state={"truth": 1.0})

        self.assertEqual(len(requests), 1)

    def test_exact_atomic_commit_ack_allows_normal_version_advance(self):
        requests = []
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=self.exact_writer_recorder(requests),
        )

        orgasm = cycle.force_admin_test(
            authorized=True,
            planning_state={"truth": 1.0},
        )
        resolution = cycle.advance_time(5.1, planning_state={"truth": 1.0})

        self.assertTrue(orgasm.atomic_commit_used)
        self.assertTrue(resolution.atomic_commit_used)
        self.assertEqual([request["state_version"] for request in requests], [1, 2])
        self.assertEqual([request["expected_prior_version"] for request in requests], [0, 1])
        self.assertEqual(orgasm.commit_result["state_version"], 1)
        self.assertEqual(resolution.commit_result["state_version"], 2)

    def test_mismatched_atomic_commit_ack_poison_cycle(self):
        requests = []

        def wrong_writer(request):
            requests.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": "0" * 64,
                "event_count": len(request["event_rows"]),
            }

        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=wrong_writer,
        )

        with self.assertRaises(RuntimeError):
            cycle.force_admin_test(
                authorized=True,
                planning_state={"truth": 1.0},
            )

        with self.assertRaises(RuntimeError):
            cycle.advance_time(5.1, planning_state={"truth": 1.0})
        self.assertEqual(len(requests), 1)

    def test_precommit_finalize_failure_poison_cycle_after_host_mutation(self):
        requests = []
        cycle = VeraAffectiveCycle(
            self.make_host(),
            host_scope="TEST_HOST",
            atomic_commit_writer=self.exact_writer_recorder(requests),
        )
        original_export = cycle.host.export_checkpoint

        def broken_export():
            raise RuntimeError("synthetic checkpoint serialization failure")

        cycle.host.export_checkpoint = broken_export
        with self.assertRaisesRegex(RuntimeError, "synthetic checkpoint serialization failure"):
            cycle.process_turn(
                StimulusAppraisal(
                    sexual_relevance=0.8,
                    partner_relevance=0.8,
                    relational_relevance=0.8,
                    anticipation_cue=0.8,
                    positive_valence=0.8,
                    duration_ms=800,
                    context_eligible=True,
                ),
                planning_state={"truth": 1.0},
            )

        cycle.host.export_checkpoint = original_export
        with self.assertRaisesRegex(RuntimeError, "durable frontier is uncertain"):
            cycle.process_turn(StimulusAppraisal(), planning_state={"truth": 1.0})
        self.assertEqual(requests, [])


if __name__ == "__main__":
    unittest.main()
