import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.runtime import evaluate_proposition_admission

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "architecture" / "VERA_RUNTIME_CONTRACT_V1.json").read_text(encoding="utf-8"))

DOMAIN = "SEMANTICS_PROVENANCE_CURRENTNESS"
PROPOSITION = "SEMANTIC_PROVENANCE_CURRENTNESS_STATUS"
REFERENT = "EXACT_PROPOSITION_REFERENT_SOURCE_BINDING"
DISPATCH_ID = "dispatch:semantic-currentness"


def envelope(
    evidence_class,
    *,
    conflict_state="NONE",
    supersession_state="CURRENT_OBSERVATION",
    proposition=PROPOSITION,
    referent_scope=REFERENT,
):
    return ProviderEvidenceEnvelope(
        provider="test",
        locator=f"test:{evidence_class}",
        revision="semantic-currentness-fixture-v1",
        observed_at="2026-09-10T09:40:00Z",
        evidence_class=evidence_class,
        referent=DOMAIN,
        scope="RETRIEVED_ITEM",
        privacy_class="GOVERNED",
        currentness_basis="fresh exact fixture readback",
        supersession_state=supersession_state,
        conflict_state=conflict_state,
        metadata={
            "proposition_or_effect_class": proposition,
            "referent_scope": referent_scope,
        },
    )


class SemanticCurrentnessDispatchTests(unittest.TestCase):
    def decide(self, observations):
        return evaluate_proposition_admission(
            DOMAIN,
            PROPOSITION,
            REFERENT,
            observations,
            CONTRACT,
        )

    def test_contract_declares_exact_semantic_currentness_dispatch(self):
        dispatch = [row for row in CONTRACT["resolver_dispatch"] if row["id"] == DISPATCH_ID]
        self.assertEqual(len(dispatch), 1)
        self.assertEqual(
            dispatch[0],
            {
                "id": DISPATCH_ID,
                "domain_scope": DOMAIN,
                "proposition_or_effect_class": PROPOSITION,
                "referent_scope": REFERENT,
                "resolver_ref": "semantic_currentness",
                "precedence": 105,
                "conflict_disposition": "EXACT_PROPOSITION_REFERENT_SOURCE_TEMPORAL_SCOPE_AND_SUPERSESSION_REQUIRED",
            },
        )
        self.assertEqual(
            CONTRACT["resolver_dispatch_decisive_evidence"][DISPATCH_ID],
            {"all_of": ["control_source", "live_observation"], "any_of": []},
        )

    def test_semantic_research_is_context_not_decisive_currentness_authority(self):
        decision = self.decide([
            envelope("semantic_research"),
            envelope("live_observation"),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("control_source", decision.required_evidence_classes)

    def test_exact_control_source_plus_live_observation_can_satisfy_currentness(self):
        decision = self.decide([
            envelope("control_source"),
            envelope("live_observation"),
        ])
        self.assertEqual(decision.status, "ADMITTED")
        self.assertEqual(decision.dispatch_id, DISPATCH_ID)

    def test_conflict_or_supersession_fails_closed(self):
        cases = (
            envelope("control_source", conflict_state="CONFLICT"),
            envelope("control_source", supersession_state="SUPERSEDED"),
        )
        for control in cases:
            with self.subTest(control=control):
                decision = self.decide([control, envelope("live_observation")])
                self.assertNotEqual(decision.status, "ADMITTED")

    def test_wrong_proposition_or_referent_scope_cannot_satisfy_currentness(self):
        for bad in (
            envelope("control_source", proposition="OTHER_PROPOSITION"),
            envelope("control_source", referent_scope="OTHER_REFERENT"),
        ):
            with self.subTest(bad=bad):
                decision = self.decide([bad, envelope("live_observation")])
                self.assertNotEqual(decision.status, "ADMITTED")


if __name__ == "__main__":
    unittest.main()
