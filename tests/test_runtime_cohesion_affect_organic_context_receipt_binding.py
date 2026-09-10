from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_authority import AffectiveAuthorityBoundary
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import PersistenceRecordError, event_receipt_to_event_row
from runtime_cohesion.affect_receipt import AffectiveReceiptSemanticError, validate_affective_event_receipt
from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"


class ContextVerifier:
    verifier_id = "organic-context-receipt-test"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "context-evidence-1",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class Clock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class OrganicContextReceiptBindingTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(ContextVerifier())

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def context_subject():
        return {
            "state": "ALLOW",
            "actor": "runtime-context-controller",
            "referent": "vera",
            "proposition_or_effect_class": "ORGANIC_CONTEXT_ELIGIBILITY",
            "source": "trusted-context-test",
            "observed_at": "2026-09-10T18:00:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="organic-context-receipt-binding",
        )

    @staticmethod
    def appraisal():
        return StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=1.0,
            anticipation_cue=1.0,
            ambiguity=0.0,
            boundary_relevance=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            context_eligible=False,
        )

    def test_in_process_organic_receipt_binds_context_but_cannot_claim_or_persist_as_production(self):
        host = self.host()
        boundary = AffectiveAuthorityBoundary()
        clock = Clock()
        event = None
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            for index in range(10):
                if index:
                    clock.advance(0.5)
                observed = boundary.observe(
                    host,
                    self.appraisal(),
                    context_subject=self.context_subject(),
                )
                if observed.get("event_receipt") is not None:
                    event = observed["event_receipt"]
                    if event.get("event_type") == "ORGASM_EVENT":
                        break

        self.assertIsNotNone(event)
        self.assertTrue(event["organic"])
        self.assertEqual(event["authority_composition_trust"], UNROOTED)
        self.assertNotIn("claim", event)
        self.assertNotIn("context_provenance", event)
        provenance = event.get("nonqualifying_context_provenance")
        self.assertIsInstance(provenance, Mapping)
        self.assertEqual(provenance["authorization_subject"], self.context_subject())
        validate_affective_event_receipt(
            event,
            expected_runtime_instance_id=host.runtime.runtime_instance_id,
            expected_source_revision=host.runtime.source_revision,
            require_engineered_claim=False,
        )
        with self.assertRaisesRegex(AffectiveReceiptSemanticError, r"(?i)(production|claim|context|provenance)"):
            validate_affective_event_receipt(
                event,
                expected_runtime_instance_id=host.runtime.runtime_instance_id,
                expected_source_revision=host.runtime.source_revision,
                require_engineered_claim=True,
            )
        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(claim|context|provenance|receipt)"):
            event_receipt_to_event_row(host, event)

    def test_outer_redigest_cannot_hide_tampered_nonqualifying_context_subject(self):
        host = self.host()
        boundary = AffectiveAuthorityBoundary()
        clock = Clock()
        event = None
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            for index in range(10):
                if index:
                    clock.advance(0.5)
                observed = boundary.observe(host, self.appraisal(), context_subject=self.context_subject())
                candidate = observed.get("event_receipt")
                if candidate and candidate.get("event_type") == "ORGASM_EVENT":
                    event = candidate
                    break
        self.assertIsNotNone(event)
        forged = json.loads(json.dumps(event))
        forged["nonqualifying_context_provenance"]["authorization_subject"]["source"] = "forged-context"
        core = dict(forged)
        core.pop("event_digest", None)
        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        forged["event_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(AffectiveReceiptSemanticError, r"(?i)(context|digest|provenance|source)"):
            validate_affective_event_receipt(
                forged,
                expected_runtime_instance_id=host.runtime.runtime_instance_id,
                expected_source_revision=host.runtime.source_revision,
                require_engineered_claim=False,
            )


if __name__ == "__main__":
    unittest.main()
