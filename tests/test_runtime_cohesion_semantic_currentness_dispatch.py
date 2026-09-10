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
MANIFEST_SHA256 = "b7c70b1ad2c3bc533c7560320fb9a03b827f3eafad6296894216d75281b8dca1"
SOURCE_IDENTITY = "VERA_R10A0_PROJECT_SOURCE_MANIFEST_R10.json"
CURRENTNESS_STATE = "CURRENT_EXACT_R10_BINDING"


def exact_binding(**overrides):
    binding = {
        "control_release": "R10A0",
        "control_round": "R10",
        "control_manifest_sha256": MANIFEST_SHA256,
        "binding_source_identity": SOURCE_IDENTITY,
        "binding_source_revision": MANIFEST_SHA256,
        "binding_currentness_state": CURRENTNESS_STATE,
        "binding_supersession_state": "CURRENT_OBSERVATION",
    }
    binding.update(overrides)
    return binding


def envelope(
    evidence_class,
    *,
    conflict_state="NONE",
    supersession_state="CURRENT_OBSERVATION",
    proposition=PROPOSITION,
    referent_scope=REFERENT,
    binding=None,
):
    metadata = {
        "proposition_or_effect_class": proposition,
        "referent_scope": referent_scope,
    }
    if binding is not None:
        metadata.update(binding)
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
        metadata=metadata,
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
        decisive = CONTRACT["resolver_dispatch_decisive_evidence"][DISPATCH_ID]
        self.assertEqual(decisive["all_of"], ["control_source", "live_observation"])
        self.assertEqual(decisive["any_of"], [])
        self.assertEqual(
            decisive["relational_binding"],
            {
                "mode": "EXACT_SHARED_R10_CONTROL_BINDING",
                "control_root_ref": "VERA_RUNTIME_CONTRACT_V1#control_root",
                "required_source_identity": SOURCE_IDENTITY,
                "required_currentness_state": CURRENTNESS_STATE,
                "required_supersession_state": "CURRENT_OBSERVATION",
                "shared_metadata_fields": [
                    "control_release",
                    "control_round",
                    "control_manifest_sha256",
                    "binding_source_identity",
                    "binding_source_revision",
                    "binding_currentness_state",
                    "binding_supersession_state",
                ],
            },
        )

    def test_semantic_research_is_context_not_decisive_currentness_authority(self):
        decision = self.decide([
            envelope("semantic_research"),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("control_source", decision.required_evidence_classes)

    def test_exact_cross_bound_r10_control_and_live_observation_can_satisfy_currentness(self):
        decision = self.decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "ADMITTED")
        self.assertEqual(decision.dispatch_id, DISPATCH_ID)
        self.assertIn("exact shared R10", decision.reason)

    def test_fresh_r8a2_control_source_cannot_satisfy_r10_currentness(self):
        decision = self.decide([
            envelope(
                "control_source",
                binding=exact_binding(
                    control_release="R8A2",
                    control_round="R8",
                    control_manifest_sha256="8" * 64,
                    binding_source_revision="8" * 64,
                ),
            ),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("control root", decision.reason)

    def test_wrong_r10_manifest_cannot_satisfy_currentness(self):
        decision = self.decide([
            envelope(
                "control_source",
                binding=exact_binding(
                    control_manifest_sha256="0" * 64,
                    binding_source_revision="0" * 64,
                ),
            ),
            envelope("live_observation", binding=exact_binding()),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("control root", decision.reason)

    def test_live_observation_bound_to_different_source_revision_is_conflict(self):
        decision = self.decide([
            envelope("control_source", binding=exact_binding()),
            envelope(
                "live_observation",
                binding=exact_binding(binding_source_revision="f" * 64),
            ),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("same exact source", decision.reason)

    def test_generic_unbound_live_observation_is_unresolved(self):
        decision = self.decide([
            envelope("control_source", binding=exact_binding()),
            envelope("live_observation"),
        ])
        self.assertEqual(decision.status, "UNRESOLVED")
        self.assertIn("binding metadata", decision.reason)

    def test_wrong_currentness_state_cannot_satisfy_currentness(self):
        decision = self.decide([
            envelope("control_source", binding=exact_binding()),
            envelope(
                "live_observation",
                binding=exact_binding(binding_currentness_state="HISTORICAL"),
            ),
        ])
        self.assertEqual(decision.status, "CONFLICT")
        self.assertIn("currentness", decision.reason)

    def test_conflict_or_supersession_fails_closed(self):
        cases = (
            envelope("control_source", conflict_state="CONFLICT", binding=exact_binding()),
            envelope("control_source", supersession_state="SUPERSEDED", binding=exact_binding()),
        )
        for control in cases:
            with self.subTest(control=control):
                decision = self.decide([
                    control,
                    envelope("live_observation", binding=exact_binding()),
                ])
                self.assertNotEqual(decision.status, "ADMITTED")

    def test_wrong_proposition_or_referent_scope_cannot_satisfy_currentness(self):
        for bad in (
            envelope("control_source", proposition="OTHER_PROPOSITION", binding=exact_binding()),
            envelope("control_source", referent_scope="OTHER_REFERENT", binding=exact_binding()),
        ):
            with self.subTest(bad=bad):
                decision = self.decide([
                    bad,
                    envelope("live_observation", binding=exact_binding()),
                ])
                self.assertNotEqual(decision.status, "ADMITTED")


if __name__ == "__main__":
    unittest.main()
