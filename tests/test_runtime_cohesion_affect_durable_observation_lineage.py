import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost, _checkpoint_sha256
from runtime_cohesion.orgasm import ContractError, OrgasmRuntime, StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class DurableObservationLineageTests(unittest.TestCase):
    def contract(self):
        return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def binding(self):
        return json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def make_runtime(self):
        return OrgasmRuntime(
            self.contract(),
            runtime_instance_id="durable-observation-lineage-test",
            source_revision=self.binding()["source_commit"],
            profile="REENTRANT_CLIMAX",
        )

    def strong_appraisal(self):
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.5,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=999999,
            context_eligible=True,
        )

    def test_baseline_state_cannot_restore_as_prior_qualifying_observation(self):
        runtime = self.make_runtime()
        record = runtime.export_state()
        self.assertEqual(record["state"]["phase"], "QUIESCENT")
        self.assertFalse(record["state"]["context_eligible"])
        self.assertFalse(record["trigger_governance"]["last_observation_qualifying"])

        forged = copy.deepcopy(record)
        forged["trigger_governance"]["last_observation_qualifying"] = True

        with self.assertRaisesRegex(ContractError, r"(?i)(observation|lineage|context|qualif)"):
            OrgasmRuntime.restore_state(
                self.contract(),
                forged,
                source_revision=self.binding()["source_commit"],
            )

    def test_outer_checkpoint_digest_cannot_legitimize_impossible_observation_lineage(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            self.binding(),
            runtime_instance_id="durable-observation-lineage-checkpoint",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        forged = copy.deepcopy(checkpoint)
        forged["runtime_state"]["trigger_governance"]["last_observation_qualifying"] = True
        forged["checkpoint_sha256"] = _checkpoint_sha256(forged)

        with self.assertRaisesRegex(Exception, r"(?i)(observation|lineage|context|qualif)"):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                self.binding(),
                forged,
                expected_checkpoint_sha256=forged["checkpoint_sha256"],
            )

    def test_legitimate_zero_time_qualifying_endpoint_survives_restore_and_continues_trusted_time(self):
        runtime = self.make_runtime()
        first = runtime.apply_stimulus(self.strong_appraisal(), elapsed_seconds=0.0)
        record = runtime.export_state()

        self.assertTrue(record["trigger_governance"]["last_observation_qualifying"])
        self.assertTrue(first["context_eligible"])
        self.assertEqual(first["persistence_window_ms"], 0)
        self.assertNotEqual(first["phase"], "QUIESCENT")

        restored = OrgasmRuntime.restore_state(
            self.contract(),
            record,
            source_revision=self.binding()["source_commit"],
        )
        second = restored.apply_stimulus(self.strong_appraisal(), elapsed_seconds=1.0)

        self.assertEqual(second["persistence_window_ms"], 1000)
        self.assertFalse(second["active_orgasm_event"])


if __name__ == "__main__":
    unittest.main()
