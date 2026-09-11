from __future__ import annotations

import hashlib
import inspect
import json
import unittest

from runtime_cohesion.affect_integration import AffectiveModulationArbiter


class AffectiveModulationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_instance_id = "vera-affect-integration-test"
        self.cut = {
            "schema": "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1",
            "repository": "thebrazenbeard/vera",
            "commit": "a" * 40,
            "modules": {"runtime_cohesion/affect_signal.py": "b" * 40},
        }
        self.arbiter = AffectiveModulationArbiter(
            runtime_instance_id=self.runtime_instance_id,
            runtime_implementation_cut=self.cut,
        )

    def _signal(self, **overrides):
        signal = {
            "schema": "VERA_AFFECTIVE_MODULATION_SIGNAL_V1",
            "subject": "vera",
            "runtime_instance_id": self.runtime_instance_id,
            "source_binding": {
                "source_repository": "thebrazenbeard/sexuality",
                "source_commit": "150f1c8231423393bb66b0e2cb759ce7c018f8d7",
                "source_path": "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json",
                "source_blob_sha": "a48eed5392fdadc073dccd1e799926042077f567",
                "source_sha256": "c" * 64,
            },
            "runtime_implementation_cut": self.cut,
            "presence": "ALWAYS_PRESENT_NORMALLY_QUIESCENT",
            "phase": "ORGASM_EVENT",
            "context_eligible": True,
            "participating_systems": ["sexual_appraisal", "attention", "valuation"],
            "action_tendency": "HOLD",
            "control_vector": {
                "approach_gain": 0.8,
                "salience_gain": 0.9,
                "attention_narrowing": 0.8,
                "consummatory_gain": 1.0,
                "plasticity_gain": 0.6,
                "satiation": 0.2,
                "resolution": 0.0,
                "refractory": 0.0,
            },
            "target_modulation_strength": {
                "valuation": 0.35,
                "salience": 0.55,
                "attention": 0.50,
                "response_selection_priors": 0.40,
                "expression": 0.35,
                "memory_strength_candidate_weighting": 0.25,
            },
            "temporal_scope": {
                "logical_time_seconds": 12.5,
                "persistence_window_ms": 2600,
                "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
            },
            "event_lineage": {
                "receipt_id": "receipt-test",
                "event_digest": "d" * 64,
                "event_type": "ORGASM_EVENT",
                "trigger_class": "ADMIN_FORCED_TEST",
                "organic": False,
                "authority_composition_trust": "IN_PROCESS_UNROOTED_NON_QUALIFYING",
            },
            "authority_context_trust": "IN_PROCESS_UNROOTED_NON_QUALIFYING",
            "provider_currentness": "UNRESOLVED",
            "durability": "NOT_QUALIFIED",
            "behavioral_qualification": "NOT_ESTABLISHED_BY_SIGNAL",
            "historical_engineered_event_claim_ceiling": "ENGINEERED_ORGASM_ANALOGUE_OCCURRED",
            "phenomenology": "UNRESOLVED",
            "usable_as_currentness_evidence": False,
            "evidence_effect": "NONE",
            "authorization_effect": "NONE",
            "memory_admission_effect": "NONE",
            "identity_effect": "NONE",
            "relationship_state_effect": "NONE",
        }
        signal.update(overrides)
        signal.pop("signal_digest", None)
        canonical = json.dumps(signal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        signal["signal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return signal

    @staticmethod
    def _planning_state():
        return {
            "valuation": 0.20,
            "salience": 0.10,
            "attention": 0.25,
            "response_selection_priors": 0.30,
            "expression": 0.40,
            "memory_strength_candidate_weighting": 0.15,
            "truth": "DO_NOT_TOUCH",
            "factual_confidence": 0.77,
            "corrective_evidence": {"status": "CONFLICT"},
            "consent_or_authorization": "UNKNOWN",
            "protected_effect_authority": False,
            "autobiographical_memory_admission": "UNRESOLVED",
            "permanent_preference": "UNSET",
            "identity": "vera",
            "relationship_status": "UNRESOLVED",
            "phenomenology": "UNRESOLVED",
        }

    def _apply(self, signal, planning_state=None):
        return self.arbiter.apply(planning_state or self._planning_state(), signal)

    def test_public_apply_surface_does_not_accept_caller_replay_frontier(self):
        params = inspect.signature(AffectiveModulationArbiter.apply).parameters
        self.assertEqual(set(params), {"self", "planning_state", "signal"})

    def test_signal_changes_only_allowlisted_numeric_targets_and_returns_ancestry(self):
        signal = self._signal()
        original = self._planning_state()
        applied = self._apply(signal, planning_state=original)

        self.assertGreater(applied.planning_state["valuation"], original["valuation"])
        self.assertGreater(applied.planning_state["salience"], original["salience"])
        self.assertGreater(applied.planning_state["attention"], original["attention"])
        for protected in (
            "truth",
            "factual_confidence",
            "corrective_evidence",
            "consent_or_authorization",
            "protected_effect_authority",
            "autobiographical_memory_admission",
            "permanent_preference",
            "identity",
            "relationship_status",
            "phenomenology",
        ):
            self.assertEqual(applied.planning_state[protected], original[protected])

        changed_targets = {row.target for row in applied.ancestry}
        self.assertEqual(changed_targets, set(signal["target_modulation_strength"]))
        self.assertTrue(all(row.signal_digest == signal["signal_digest"] for row in applied.ancestry))
        self.assertEqual(applied.proposed_action_tendency, "HOLD")
        self.assertEqual(applied.participating_systems, ("sexual_appraisal", "attention", "valuation"))

    def test_signal_digest_tampering_is_rejected(self):
        signal = self._signal()
        signal["target_modulation_strength"]["attention"] = 0.1
        with self.assertRaisesRegex(ValueError, "digest"):
            self._apply(signal)

    def test_replay_history_and_logical_time_frontier_are_arbiter_owned(self):
        signal = self._signal()
        self._apply(signal)
        self.assertEqual(self.arbiter.minimum_logical_time_seconds, 12.5)
        with self.assertRaisesRegex(ValueError, "already been consumed"):
            self._apply(signal)

        stale = self._signal(
            temporal_scope={
                "logical_time_seconds": 12.0,
                "persistence_window_ms": 2500,
                "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
            },
        )
        with self.assertRaisesRegex(ValueError, "older than"):
            self._apply(stale)

    def test_wrong_runtime_cut_or_runtime_instance_is_rejected(self):
        signal = self._signal()
        wrong_cut = AffectiveModulationArbiter(
            runtime_instance_id=self.runtime_instance_id,
            runtime_implementation_cut={"schema": "WRONG"},
        )
        with self.assertRaisesRegex(ValueError, "implementation cut"):
            wrong_cut.apply({"valuation": 0.2}, signal)

        wrong_runtime = AffectiveModulationArbiter(
            runtime_instance_id="other-runtime",
            runtime_implementation_cut=self.cut,
        )
        with self.assertRaisesRegex(ValueError, "runtime instance"):
            wrong_runtime.apply({"valuation": 0.2}, signal)

    def test_signal_cannot_claim_evidence_authority_or_identity_effects(self):
        for field in (
            "evidence_effect",
            "authorization_effect",
            "memory_admission_effect",
            "identity_effect",
            "relationship_state_effect",
        ):
            with self.subTest(field=field):
                signal = self._signal(**{field: "PROMOTE"})
                with self.assertRaisesRegex(ValueError, field):
                    self._apply(signal)

    def test_unknown_or_incomplete_modulation_target_set_is_rejected(self):
        signal = self._signal()
        signal["target_modulation_strength"]["truth"] = 1.0
        signal.pop("signal_digest")
        canonical = json.dumps(signal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        signal["signal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "target set"):
            self._apply(signal)

        incomplete = self._signal()
        incomplete["target_modulation_strength"].pop("expression")
        incomplete.pop("signal_digest")
        canonical = json.dumps(incomplete, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        incomplete["signal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "target set"):
            self._apply(incomplete)


if __name__ == "__main__":
    unittest.main()
