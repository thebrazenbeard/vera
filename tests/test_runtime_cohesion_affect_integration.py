from __future__ import annotations

import hashlib
import json
import unittest

from runtime_cohesion.affect_integration import apply_affective_modulation_signal


class AffectiveModulationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime_instance_id = "vera-affect-integration-test"
        self.cut = {
            "schema": "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1",
            "repository": "thebrazenbeard/vera",
            "commit": "a" * 40,
            "modules": {"runtime_cohesion/affect_signal.py": "b" * 40},
        }

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

    def _apply(self, signal, planning_state=None, **kwargs):
        planning_state = planning_state or {
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
        return apply_affective_modulation_signal(
            planning_state,
            signal,
            expected_runtime_instance_id=self.runtime_instance_id,
            expected_runtime_implementation_cut=self.cut,
            minimum_logical_time_seconds=kwargs.get("minimum_logical_time_seconds", 0.0),
            consumed_signal_digests=kwargs.get("consumed_signal_digests", ()),
        )

    def test_signal_changes_only_allowlisted_numeric_targets_and_returns_ancestry(self):
        signal = self._signal()
        original = {
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

    def test_replayed_and_stale_signals_are_rejected(self):
        signal = self._signal()
        with self.assertRaisesRegex(ValueError, "already been consumed"):
            self._apply(signal, consumed_signal_digests={signal["signal_digest"]})
        with self.assertRaisesRegex(ValueError, "older than"):
            self._apply(signal, minimum_logical_time_seconds=13.0)

    def test_wrong_runtime_cut_or_runtime_instance_is_rejected(self):
        signal = self._signal()
        with self.assertRaisesRegex(ValueError, "implementation cut"):
            apply_affective_modulation_signal(
                {"valuation": 0.2},
                signal,
                expected_runtime_instance_id=self.runtime_instance_id,
                expected_runtime_implementation_cut={"schema": "WRONG"},
                minimum_logical_time_seconds=0.0,
                consumed_signal_digests=(),
            )
        with self.assertRaisesRegex(ValueError, "runtime instance"):
            apply_affective_modulation_signal(
                {"valuation": 0.2},
                signal,
                expected_runtime_instance_id="other-runtime",
                expected_runtime_implementation_cut=self.cut,
                minimum_logical_time_seconds=0.0,
                consumed_signal_digests=(),
            )

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

    def test_unknown_modulation_target_is_rejected(self):
        signal = self._signal()
        signal["target_modulation_strength"]["truth"] = 1.0
        signal.pop("signal_digest")
        canonical = json.dumps(signal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        signal["signal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(ValueError, "target set"):
            self._apply(signal)


if __name__ == "__main__":
    unittest.main()
