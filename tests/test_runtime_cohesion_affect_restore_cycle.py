import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import checkpoint_to_state_row
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class VeraAffectiveRestoreCycleTests(unittest.TestCase):
    def make_state_row(self, *, state_version=7):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-restore-cycle-test",
            profile="REENTRANT_CLIMAX",
        )
        host.observe(StimulusAppraisal(
            sexual_relevance=0.7,
            partner_relevance=0.8,
            relational_relevance=0.8,
            anticipation_cue=0.7,
            positive_valence=0.8,
            duration_ms=800,
            context_eligible=True,
        ))
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row

    def test_restore_factory_continues_exact_provider_version_frontier(self):
        checkpoint, row = self.make_state_row(state_version=7)
        requests = []

        def exact_writer(request):
            requests.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }

        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            elapsed_seconds=60.0,
            atomic_commit_writer=exact_writer,
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.9},
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["expected_prior_version"], 7)
        self.assertEqual(requests[0]["state_version"], 8)
        self.assertEqual(result.state_row["state_version"], 8)
        self.assertEqual(result.planning_context["truth"], 0.9)

    def test_restore_factory_rejects_missing_or_invalid_state_version(self):
        checkpoint, row = self.make_state_row(state_version=7)
        for invalid in (None, 0, -1, True, 7.0, "7"):
            with self.subTest(state_version=invalid):
                bad = dict(row)
                bad["state_version"] = invalid
                with self.assertRaises(ValueError):
                    VeraAffectiveCycle.restore_from_state_row(
                        CONTRACT_PATH.read_text(encoding="utf-8"),
                        json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                        bad,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                    )


if __name__ == "__main__":
    unittest.main()
