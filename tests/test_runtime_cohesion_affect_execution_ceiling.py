import hashlib
import json
import unittest

from runtime_cohesion.affect_integration import (
    AffectiveModulationEnvelope,
    AffectiveModulationError,
    adapt_orgasm_modulation_signal,
)


SOURCE = "150f1c8231423393bb66b0e2cb759ce7c018f8d7"
SOURCE_BLOB = "a48eed5392fdadc073dccd1e799926042077f567"
CUT = "b39df9db48917469db58d4d7b6cd5cb1fe1690a8"
STATE_DIGEST = "a" * 64
RECEIPT_DIGEST = "b" * 64
SIGNAL_DIGEST = "c" * 64


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def unrooted_signal():
    value = {
        "schema": "VERA_AFFECTIVE_MODULATION_SIGNAL_V1",
        "subject": "vera",
        "runtime_instance_id": "execution-ceiling-test",
        "source_binding": {
            "source_repository": "thebrazenbeard/sexuality",
            "source_commit": SOURCE,
            "source_path": "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json",
            "source_blob_sha": SOURCE_BLOB,
            "source_sha256": "d" * 64,
        },
        "runtime_implementation_cut": {
            "schema": "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1",
            "repository": "thebrazenbeard/vera",
            "commit": CUT,
            "modules": {"runtime_cohesion/orgasm.py": "e" * 40},
        },
        "presence": "ALWAYS_PRESENT_NORMALLY_QUIESCENT",
        "phase": "ORGASM_EVENT",
        "context_eligible": False,
        "participating_systems": ["sexual_appraisal", "attention", "response_planning"],
        "action_tendency": "HOLD",
        "control_vector": {},
        "target_modulation_strength": {"attention": 0.5},
        "temporal_scope": {
            "logical_time_seconds": 1.0,
            "persistence_window_ms": 0,
            "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
        },
        "state_digest": STATE_DIGEST,
        "event_lineage": {
            "receipt_id": "receipt:execution-ceiling:1",
            "event_digest": RECEIPT_DIGEST,
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
    value["signal_digest"] = canonical_digest(value)
    return value


class AffectiveExecutionCeilingTests(unittest.TestCase):
    def test_unrooted_signal_does_not_become_execution_verified_by_marker_alone(self):
        envelope = adapt_orgasm_modulation_signal(unrooted_signal())
        self.assertEqual(envelope.evidence_ceiling, "SOURCE_BOUND_EXECUTION_UNVERIFIED")

    def test_public_envelope_cannot_self_assert_execution_verified_nonqualifying(self):
        with self.assertRaisesRegex(AffectiveModulationError, "evidence ceiling"):
            AffectiveModulationEnvelope(
                subject="vera",
                sexuality_source_revision=SOURCE,
                runtime_implementation_cut=CUT,
                runtime_instance_id="execution-ceiling-public-envelope",
                phase="ACTIVATING",
                participating_systems=("attention",),
                modulation={"attention": 0.1},
                evidence_ceiling="SOURCE_BOUND_EXECUTION_VERIFIED_NONQUALIFYING",
                temporal_scope={
                    "logical_time_seconds": 1.0,
                    "persistence_window_ms": 0,
                    "currentness_class": "RUNTIME_LOCAL_OBSERVATION_ONLY",
                },
                state_digest=STATE_DIGEST,
                signal_digest=SIGNAL_DIGEST,
                receipt_id=None,
                receipt_digest=None,
            )


if __name__ == "__main__":
    unittest.main()
