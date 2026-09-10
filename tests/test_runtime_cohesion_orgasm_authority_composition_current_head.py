from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_authority import AffectiveAuthorityBoundary
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal, TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedVerifier:
    verifier_id = "runtime-owned-affective-authority-test"

    def __init__(self, now):
        self.now = now

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT":
            return None
        if subject.get("source") != "trusted-test-authority":
            return None
        if subject.get("expiry_or_supersession") is not None:
            return None
        observed_at = subject.get("observed_at")
        if not isinstance(observed_at, str):
            return None
        try:
            observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        if observed.tzinfo is None:
            return None
        age = self.now - observed.astimezone(timezone.utc)
        if age < timedelta(0) or age > timedelta(minutes=5):
            return None
        actor = subject.get("actor")
        if not isinstance(actor, str) or not actor:
            return None

        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "authority-evidence-1",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class RejectingVerifier:
    verifier_id = "rejecting-runtime-owned-affective-authority-test"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        return None


class FakeMonotonicClock:
    def __init__(self, start=1000.0):
        self.value = float(start)

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += float(seconds)


class RuntimeOwnedAuthorityCompositionTests(unittest.TestCase):
    NOW = datetime(2026, 9, 10, 17, 40, tzinfo=timezone.utc)

    def setUp(self):
        reset = getattr(authority_module, "_reset_affective_authorization_verifier_for_tests", None)
        if callable(reset):
            reset()

    def tearDown(self):
        reset = getattr(authority_module, "_reset_affective_authorization_verifier_for_tests", None)
        if callable(reset):
            reset()

    def host(self, runtime_instance_id="authority-composition-current-head"):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id=runtime_instance_id,
        )

    def subject(self, effect, **overrides):
        value = {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": effect,
            "source": "trusted-test-authority",
            "observed_at": "2026-09-10T17:39:00Z",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }
        value.update(overrides)
        return value

    def install(self, verifier):
        installer = getattr(authority_module, "_install_affective_authorization_verifier", None)
        self.assertTrue(callable(installer), "authority verifier composition needs a private runtime installer")
        installer(verifier)

    def test_public_boundary_constructor_has_no_verifier_injection_surface(self):
        self.assertNotIn("authorization_verifier", inspect.signature(AffectiveAuthorityBoundary).parameters)
        with self.assertRaises(TypeError):
            AffectiveAuthorityBoundary(authorization_verifier=TrustedVerifier(self.NOW))

    def test_no_runtime_verifier_means_no_privileged_trigger(self):
        boundary = AffectiveAuthorityBoundary()
        with self.assertRaisesRegex(TriggerRejected, r"(?i)(verifier|authority|authorization|composition)"):
            boundary.force_admin_test(
                self.host(),
                authorization_subject=self.subject("ADMIN_FORCED_TEST"),
            )

    def test_runtime_owned_verifier_binds_exact_authority_evidence_to_receipt(self):
        self.install(TrustedVerifier(self.NOW))
        boundary = AffectiveAuthorityBoundary()
        receipt = boundary.force_admin_test(
            self.host(),
            authorization_subject=self.subject("ADMIN_FORCED_TEST"),
        )

        provenance = receipt["trigger_provenance"]
        self.assertIsInstance(provenance, Mapping)
        self.assertEqual(provenance["verifier_id"], TrustedVerifier.verifier_id)
        self.assertEqual(provenance["actor"], "patrick")
        self.assertEqual(provenance["referent"], "vera")
        self.assertEqual(provenance["proposition_or_effect_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(provenance["currentness"], "CURRENT")
        self.assertIsNone(provenance["expiry_or_supersession"])
        self.assertRegex(provenance["evidence_digest"], r"^[0-9a-f]{64}$")

    def test_first_installed_verifier_cannot_be_replaced(self):
        trusted = TrustedVerifier(self.NOW)
        self.install(trusted)
        with self.assertRaises(RuntimeError):
            self.install(RejectingVerifier())

    def test_rejecting_runtime_verifier_cannot_be_overridden_by_valid_looking_subject(self):
        self.install(RejectingVerifier())
        boundary = AffectiveAuthorityBoundary()
        with self.assertRaisesRegex(TriggerRejected, r"(?i)(verif|authority|authorization|evidence)"):
            boundary.force_admin_test(
                self.host(),
                authorization_subject=self.subject("ADMIN_FORCED_TEST"),
            )

    def test_verified_context_is_applied_by_boundary_not_by_caller_boolean(self):
        self.install(TrustedVerifier(self.NOW))
        boundary = AffectiveAuthorityBoundary()
        clock = FakeMonotonicClock()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            context_eligible=False,
        )
        with patch("runtime_cohesion.orgasm._monotonic_now", side_effect=clock):
            observed = boundary.observe(
                self.host("verified-context-current-head"),
                appraisal,
                context_subject=self.subject("ORGANIC_CONTEXT_ELIGIBILITY"),
            )
        self.assertTrue(observed["state"]["context_eligible"])

    def test_simulation_time_cannot_satisfy_boundary_privileged_cooldown(self):
        self.install(TrustedVerifier(self.NOW))
        boundary = AffectiveAuthorityBoundary()
        host = self.host("authority-cooldown-current-head")
        clock = FakeMonotonicClock()
        subject = self.subject("ADMIN_FORCED_TEST")

        with patch("runtime_cohesion.affect_authority._monotonic_now", side_effect=clock):
            boundary.force_admin_test(host, authorization_subject=subject)
            host.advance_time(20.0)

            with self.assertRaisesRegex(TriggerRejected, r"(?i)(cooldown|interval|monotonic|time)"):
                boundary.force_admin_test(host, authorization_subject=subject)

            clock.advance(11.0)
            receipt = boundary.force_admin_test(host, authorization_subject=subject)
            self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")


if __name__ == "__main__":
    unittest.main()
