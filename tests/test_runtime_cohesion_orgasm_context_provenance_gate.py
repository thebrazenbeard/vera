import json
from pathlib import Path
import unittest
from unittest.mock import patch

from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal, TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class OrganicContextProvenanceGateTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="organic-context-provenance-gate",
        )

    @staticmethod
    def caller_claimed_eligible_appraisal():
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            ambiguity=0.0,
            boundary_relevance=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=0,
            context_eligible=True,
        )

    def test_caller_boolean_cannot_establish_organic_context_eligibility(self):
        clock = FakeMonotonicClock()
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            host = self.make_host()
            appraisal = self.caller_claimed_eligible_appraisal()

            for index in range(8):
                if index:
                    clock.advance(0.5)
                try:
                    observed = host.observe(appraisal)
                except (TriggerRejected, TypeError, ValueError):
                    # Rejecting an unproven context claim is a valid fail-closed
                    # implementation. Silently accepting it as upstream evidence is not.
                    return

                state = observed["state"]
                self.assertFalse(
                    state["context_eligible"],
                    "caller context_eligible=True may not become trusted organic-context evidence",
                )
                self.assertNotEqual(
                    state["phase"],
                    "ORGASM_EVENT",
                    "organic climax may not be reached from a caller boolean in place of upstream context provenance",
                )


if __name__ == "__main__":
    unittest.main()
