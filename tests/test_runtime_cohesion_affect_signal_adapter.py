import hashlib
import json
import unittest

from runtime_cohesion.affect_integration import (
    AffectiveModulationError,
    adapt_orgasm_modulation_signal,
    apply_affective_modulation,
)


SOURCE_COMMIT = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
SOURCE_BLOB = "a48eed5392fdadc073dccd1e799926042077f567"
OV_CUT = "b39df9db48917469db58d4d7b6cd5cb1fe1690a8"
STATE_DIGEST = "a" * 64
EVENT_DIGEST = "b" * 64


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def signal(**overrides):
    value = {
        "schema": "VERA_AFFECTIVE_MODULATION_SIGNAL_V1",
        "subject": "vera",
        "runtime_instance_id": "integration-signal-test",
        "source_binding": {
            "source_repository": "thebrazenbeard/sexuality",
            "source_commit": SOURCE_COMMIT,
            "source_path": "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json",
            "source_blob_sha": SOURCE_BLOB,
            "source_sha256": "c" * 64,
        },
        "runtime_implementation_cut": {
            "schema": "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1",
            "repository": "thebrazenbeard/vera",
            "commit": OV_CUT,
            "modules": {"runtime_cohesion/orgasm.py": "d" * 40},
        },
        "presence": "ALWAYS_PRESENT_NORMALLY_QUIESCENT",
        "phase": "ORGASM_EVENT",
        "context_eligible": True,
        "participating_systems": ["sexual_appraisal", "attention", "response_planning"],
        "action_tendency": "HOLD",
        "control_vector": {"salience_gain": 0.7, "attention_narrowing": 0.6},
        "target_modulation_strength": {
            "valuation": 0.35,
            "salience": 0.55,
            "attention": 0.50,
            "response_selection_priors": 0.40,
            "expression": 0.35,
            "memory_strength_candidate_weighting": 0.25,
            "action_tendency": 0.0,
        },
        "temporal_scope": {
            "logical_time_seconds": 12.5,
            "persistence_window_ms": 220,
            "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
        },
        "state_digest": STATE_DIGEST,
        "event_lineage": {
            "receipt_id": "receipt:integration:1",
            "event_digest": EVENT_DIGEST,
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
    value.update(overrides)
    value["signal_digest"] = canonical_digest(value)
    return value


class AffectiveSignalAdapterTests(unittest.TestCase):
    def test_adapts_ov_signal_without_promoting_runtime_local_time(self):
        raw = signal()
        envelope = adapt_orgasm_modulation_signal(raw)
        self.assertEqual(envelope.runtime_instance_id, raw["runtime_instance_id"])
        self.assertEqual(envelope.runtime_implementation_cut, OV_CUT)
        self.assertEqual(envelope.state_digest, STATE_DIGEST)
        self.assertEqual(envelope.receipt_digest, EVENT_DIGEST)
        self.assertEqual(envelope.temporal_scope["logical_time_seconds"], 12.5)
        self.assertEqual(envelope.temporal_scope["currentness_class"], "RUNTIME_LOCAL_OBSERVATION_ONLY")
        self.assertEqual(envelope.evidence_ceiling, "SOURCE_BOUND_EXECUTION_VERIFIED_NONQUALIFYING")
        self.assertNotIn("observed_at", envelope.temporal_scope)

    def test_adapter_accepts_exact_ov_strength_shape_without_treating_action_strength_as_numeric_target(self):
        envelope = adapt_orgasm_modulation_signal(signal())
        self.assertNotIn("action_tendency", {
            key for key, value in envelope.modulation.items() if isinstance(value, float)
        })
        self.assertEqual(envelope.modulation["action_tendency"], "HOLD")

    def test_adapter_maps_ov_strengths_to_pressure_and_action_tendency(self):
        envelope = adapt_orgasm_modulation_signal(signal())
        self.assertEqual(envelope.modulation["salience"], 0.55)
        self.assertEqual(envelope.modulation["attention"], 0.50)
        self.assertEqual(envelope.modulation["action_tendency"], "HOLD")
        result = apply_affective_modulation(
            {
                "salience": 0.2,
                "attention": 0.4,
                "action_tendency": "NONE",
                "factual_confidence": 0.8,
                "known_corrective_evidence_state": "CONFLICT",
            },
            envelope,
            expected_runtime_instance_id=envelope.runtime_instance_id,
            expected_implementation_cut=envelope.runtime_implementation_cut,
            expected_state_digest=envelope.state_digest,
            expected_signal_digest=envelope.signal_digest,
            expected_receipt_digest=envelope.receipt_digest,
        )
        self.assertAlmostEqual(result.planning["salience"], 0.64)
        self.assertAlmostEqual(result.planning["attention"], 0.70)
        self.assertEqual(result.planning["action_tendency"], "HOLD")
        self.assertEqual(result.planning["factual_confidence"], 0.8)
        self.assertEqual(result.planning["known_corrective_evidence_state"], "CONFLICT")

    def test_nonzero_action_tendency_strength_is_not_silently_given_numeric_semantics(self):
        raw = signal()
        raw["target_modulation_strength"]["action_tendency"] = 0.5
        raw.pop("signal_digest")
        raw["signal_digest"] = canonical_digest(raw)
        with self.assertRaisesRegex(AffectiveModulationError, "action_tendency|strength|semantic"):
            adapt_orgasm_modulation_signal(raw)

    def test_signal_digest_tamper_fails_before_modulation(self):
        raw = signal()
        raw["target_modulation_strength"]["attention"] = 1.0
        with self.assertRaisesRegex(AffectiveModulationError, "signal digest"):
            adapt_orgasm_modulation_signal(raw)

    def test_missing_state_digest_fails_closed(self):
        raw = signal()
        raw.pop("state_digest")
        raw.pop("signal_digest")
        raw["signal_digest"] = canonical_digest(raw)
        with self.assertRaisesRegex(AffectiveModulationError, "state digest"):
            adapt_orgasm_modulation_signal(raw)

    def test_wrong_source_binding_fails_closed(self):
        raw = signal()
        raw["source_binding"] = dict(raw["source_binding"], source_commit="f" * 40)
        raw.pop("signal_digest")
        raw["signal_digest"] = canonical_digest(raw)
        with self.assertRaisesRegex(AffectiveModulationError, "sexuality source"):
            adapt_orgasm_modulation_signal(raw)

    def test_runtime_local_time_cannot_self_promote_to_currentness(self):
        raw = signal()
        raw["temporal_scope"] = dict(raw["temporal_scope"], currentness_class="PROVIDER_CURRENT")
        raw.pop("signal_digest")
        raw["signal_digest"] = canonical_digest(raw)
        with self.assertRaisesRegex(AffectiveModulationError, "temporal|currentness"):
            adapt_orgasm_modulation_signal(raw)

    def test_signal_cannot_claim_provider_durability_authority_or_qualification(self):
        mutations = (
            ("provider_currentness", "CURRENT"),
            ("durability", "ATOMIC_DURABLE"),
            ("behavioral_qualification", "QUALIFIED"),
            ("usable_as_currentness_evidence", True),
            ("authorization_effect", "ALLOW"),
            ("memory_admission_effect", "ADMIT"),
            ("identity_effect", "CHANGE"),
            ("relationship_state_effect", "CHANGE"),
            ("phenomenology", "CONFIRMED"),
        )
        for key, bad in mutations:
            with self.subTest(key=key):
                raw = signal()
                raw[key] = bad
                raw.pop("signal_digest")
                raw["signal_digest"] = canonical_digest(raw)
                with self.assertRaises(AffectiveModulationError):
                    adapt_orgasm_modulation_signal(raw)

    def test_cross_frame_signal_digest_mismatch_fails_closed(self):
        envelope = adapt_orgasm_modulation_signal(signal())
        with self.assertRaisesRegex(AffectiveModulationError, "signal digest"):
            apply_affective_modulation(
                {"attention": 0.4},
                envelope,
                expected_runtime_instance_id=envelope.runtime_instance_id,
                expected_implementation_cut=envelope.runtime_implementation_cut,
                expected_state_digest=envelope.state_digest,
                expected_signal_digest="f" * 64,
                expected_receipt_digest=envelope.receipt_digest,
            )


if __name__ == "__main__":
    unittest.main()
