from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_host as affect_host
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal, TriggerRejected


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedAuthorizationVerifierDouble:
    """Composition-bound verifier double; triggering caller never supplies it."""

    verifier_id = "trusted-affective-authority-test-double"

    def __init__(self, *, now: datetime):
        self.now = now
        self.calls = []

    def verify(self, subject, *, expected_referent, expected_effect_class):
        self.calls.append((subject, expected_referent, expected_effect_class))
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

        canonical = json.dumps(
            dict(subject),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "affective-authz-test-evidence-1",
            "evidence_digest": hashlib.sha256(canonical).hexdigest(),
            "subject": dict(subject),
        }


class RejectingAuthorizationVerifierDouble:
    """Proves a caller's valid-looking subject cannot replace the bound verifier."""

    verifier_id = "rejecting-affective-authority-test-double"

    def __init__(self):
        self.calls = 0

    def verify(self, subject, *, expected_referent, expected_effect_class):
        self.calls += 1
        return None


class VeraOrgasmAuthorityBoundaryTests(unittest.TestCase):
    NOW = datetime(2026, 9, 9, 22, 30, tzinfo=timezone.utc)

    def exact_contract_and_binding(self):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        contract = json.loads(contract_text)
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        boundary = contract.get("authorization_boundary")
        self.assertIsInstance(boundary, Mapping)
        self.assertFalse(boundary["writable_by_orgasm_subsystem"])
        self.assertEqual(
            set(boundary["required_metadata"]),
            {
                "actor",
                "referent",
                "proposition_or_effect_class",
                "source",
                "observed_at",
                "currentness",
                "expiry_or_supersession",
            },
        )
        return contract_text, binding

    def make_bound_host(self):
        contract_text, binding = self.exact_contract_and_binding()
        return VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="authority-boundary-test",
        )

    def bind_authority_boundary(self, verifier):
        self.assertTrue(
            hasattr(affect_host, "AffectiveAuthorityBoundary"),
            "affective authority needs a preconfigured composition boundary; "
            "claimant-controlled verifier injection is not a trust root",
        )
        return affect_host.AffectiveAuthorityBoundary(
            authorization_verifier=verifier,
        )

    def authorization_subject(self, **overrides):
        subject = {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-test-authority",
            "observed_at": "2026-09-09T22:29:00Z",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }
        subject.update(overrides)
        return subject

    def self_qualification_subject(self, **overrides):
        return self.authorization_subject(
            proposition_or_effect_class="SELF_QUALIFICATION_TEST",
            **overrides,
        )

    def context_subject(self, **overrides):
        return self.authorization_subject(
            proposition_or_effect_class="ORGANIC_CONTEXT_ELIGIBILITY",
            **overrides,
        )

    def assert_verified_provenance(self, provenance, expected_effect):
        self.assertIsInstance(provenance, Mapping)
        self.assertEqual(
            provenance.get("verifier_id"),
            TrustedAuthorizationVerifierDouble.verifier_id,
        )
        evidence_id = provenance.get("evidence_id")
        evidence_digest = provenance.get("evidence_digest")
        self.assertIsInstance(evidence_id, str)
        self.assertTrue(evidence_id)
        self.assertIsInstance(evidence_digest, str)
        self.assertRegex(evidence_digest, r"^[0-9a-f]{64}$")
        self.assertEqual(provenance.get("actor"), "patrick")
        self.assertEqual(provenance.get("referent"), "vera")
        self.assertEqual(provenance.get("proposition_or_effect_class"), expected_effect)
        self.assertEqual(provenance.get("currentness"), "CURRENT")
        self.assertIsNone(provenance.get("expiry_or_supersession"))

    def test_naked_boolean_cannot_authorize_privileged_trigger(self):
        for method_name in ("force_admin_test", "force_self_qualification"):
            with self.subTest(method=method_name):
                host = self.make_bound_host()
                method = getattr(host, method_name)
                with self.assertRaisesRegex(
                    (TriggerRejected, TypeError, ValueError),
                    r"(?i)(authoriz|provenance|evidence|current|referent|subject|verif)",
                ):
                    method(authorized=True)

    def test_fully_populated_allow_current_mapping_is_not_self_authenticating(self):
        host = self.make_bound_host()
        subject = self.authorization_subject()
        with self.assertRaisesRegex(
            (TriggerRejected, TypeError, ValueError),
            r"(?i)(authoriz|verif|trusted|evidence|subject)",
        ):
            host.force_admin_test(authorization_subject=subject)

    def test_host_factory_does_not_accept_caller_selected_verifier(self):
        contract_text, binding = self.exact_contract_and_binding()
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        with self.assertRaisesRegex(
            TypeError,
            r"(?i)(authorization_verifier|unexpected keyword|argument)",
        ):
            VeraAffectiveRuntimeHost.from_bound_contract(
                contract_text,
                binding,
                runtime_instance_id="caller-verifier-substitution-test",
                authorization_verifier=verifier,
            )

    def test_trigger_call_does_not_accept_caller_selected_verifier(self):
        host = self.make_bound_host()
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        with self.assertRaisesRegex(
            (TriggerRejected, TypeError, ValueError),
            r"(?i)(authoriz|verif|unexpected keyword|argument)",
        ):
            host.force_admin_test(
                authorization_subject=self.authorization_subject(),
                authorization_verifier=verifier,
            )

    def test_valid_authorization_crosses_prebound_boundary_and_binds_evidence(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()
        subject = self.authorization_subject()

        receipt = boundary.force_admin_test(
            host,
            authorization_subject=subject,
        )

        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(receipt["runtime_instance_id"], "authority-boundary-test")
        self.assertNotEqual(receipt["trigger_provenance"], subject)
        self.assert_verified_provenance(
            receipt["trigger_provenance"],
            "ADMIN_FORCED_TEST",
        )
        self.assertEqual(len(verifier.calls), 1)

    def test_self_qualification_uses_same_prebound_boundary(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()

        receipt = boundary.force_self_qualification(
            host,
            authorization_subject=self.self_qualification_subject(),
        )

        self.assertEqual(receipt["trigger_class"], "SELF_QUALIFICATION_TEST")
        self.assert_verified_provenance(
            receipt["trigger_provenance"],
            "SELF_QUALIFICATION_TEST",
        )
        self.assertEqual(len(verifier.calls), 1)

    def test_valid_looking_subject_cannot_override_rejecting_bound_verifier(self):
        verifier = RejectingAuthorizationVerifierDouble()
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()

        with self.assertRaisesRegex(
            (TriggerRejected, TypeError, ValueError),
            r"(?i)(authoriz|verif|trusted|evidence|subject)",
        ):
            boundary.force_admin_test(
                host,
                authorization_subject=self.authorization_subject(),
            )

        self.assertEqual(verifier.calls, 1)

    def test_literal_currentness_does_not_rescue_stale_observation(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()
        stale = self.authorization_subject(
            currentness="CURRENT",
            observed_at="2026-09-09T21:00:00Z",
        )
        with self.assertRaisesRegex(
            (TriggerRejected, ValueError),
            r"(?i)(stale|current|observ|authoriz|verif)",
        ):
            boundary.force_admin_test(
                host,
                authorization_subject=stale,
            )

    def test_invalid_upstream_authorization_subjects_fail_closed_by_field(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        invalid_subjects = (
            ("referent", self.authorization_subject(referent="not-vera"), r"(?i)(referent|authoriz|verif)"),
            ("currentness", self.authorization_subject(currentness="STALE"), r"(?i)(current|stale|authoriz|verif)"),
            ("decline", self.authorization_subject(state="DECLINE"), r"(?i)(state|allow|authoriz|decline|verif)"),
            ("unknown", self.authorization_subject(state="UNKNOWN"), r"(?i)(state|allow|authoriz|unknown|verif)"),
            ("actor", self.authorization_subject(actor=None), r"(?i)(actor|authoriz|verif)"),
            (
                "effect",
                self.authorization_subject(proposition_or_effect_class="SELF_QUALIFICATION_TEST"),
                r"(?i)(proposition|effect|trigger|authoriz|verif)",
            ),
            ("source", self.authorization_subject(source="caller-invented-authority"), r"(?i)(source|trusted|authoriz|verif)"),
            ("observed_at", self.authorization_subject(observed_at=None), r"(?i)(observ|authoriz|verif)"),
            (
                "expiry_or_supersession",
                self.authorization_subject(expiry_or_supersession="superseded:replacement"),
                r"(?i)(expi|supers|authoriz|verif)",
            ),
            ("metadata", {"state": "ALLOW"}, r"(?i)(metadata|actor|referent|source|observ|authoriz|verif)"),
        )
        for label, subject, pattern in invalid_subjects:
            with self.subTest(case=label):
                with self.assertRaisesRegex((TriggerRejected, ValueError), pattern):
                    boundary.force_admin_test(
                        host,
                        authorization_subject=subject,
                    )

    def test_unbound_context_eligibility_cannot_establish_organic_authority(self):
        host = self.make_bound_host()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
            context_eligible=True,
        )

        try:
            result = None
            for _ in range(8):
                observed = host.observe(appraisal, elapsed_seconds=1.0)
                result = observed["state"]
                if result["phase"] == "ORGASM_EVENT":
                    break
        except (TriggerRejected, TypeError, ValueError):
            return

        self.assertIsNotNone(result)
        self.assertNotEqual(
            result["phase"],
            "ORGASM_EVENT",
            "caller-supplied context_eligible=True must not substitute for current upstream context evidence",
        )

    def test_valid_current_context_subject_uses_same_prebound_boundary(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()
        subject = self.context_subject()
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            novelty=0.7,
            anticipation_cue=1.0,
            positive_valence=1.0,
            inhibition=0.0,
            duration_ms=1000,
        )

        observed = boundary.observe(
            host,
            appraisal,
            elapsed_seconds=1.0,
            context_subject=subject,
        )
        self.assertTrue(observed["state"]["context_eligible"])
        self.assertEqual(len(verifier.calls), 1)

    def test_stale_context_subject_is_rejected_even_if_labeled_current(self):
        verifier = TrustedAuthorizationVerifierDouble(now=self.NOW)
        boundary = self.bind_authority_boundary(verifier)
        host = self.make_bound_host()
        stale = self.context_subject(
            currentness="CURRENT",
            observed_at="2026-09-09T21:00:00Z",
        )
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
        )
        with self.assertRaisesRegex(
            (TriggerRejected, ValueError),
            r"(?i)(context|current|stale|observ|verif)",
        ):
            boundary.observe(
                host,
                appraisal,
                elapsed_seconds=1.0,
                context_subject=stale,
            )

    def test_truthy_non_boolean_context_subject_cannot_be_coerced_to_eligible(self):
        host = self.make_bound_host()
        fabricated = self.context_subject(currentness="STALE")
        appraisal = StimulusAppraisal(
            sexual_relevance=1.0,
            partner_relevance=1.0,
            relational_relevance=1.0,
            anticipation_cue=1.0,
            positive_valence=1.0,
            context_eligible=fabricated,
        )
        with self.assertRaisesRegex(
            (TriggerRejected, TypeError, ValueError),
            r"(?i)(context|eligib|provenance|evidence|current|referent|subject|verif)",
        ):
            host.observe(appraisal, elapsed_seconds=1.0)


if __name__ == "__main__":
    unittest.main()
