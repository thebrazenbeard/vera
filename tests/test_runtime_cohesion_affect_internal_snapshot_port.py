import hashlib
import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_integration_bound import CohesionAffectiveIntegrationPort
from runtime_cohesion.orgasm import OrgasmRuntime


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedVerifier:
    verifier_id = "internal-snapshot-port-test-verifier"

    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, dict):
            return None
        if subject.get("state") != "ALLOW":
            return None
        if subject.get("referent") != expected_referent:
            return None
        if subject.get("proposition_or_effect_class") != expected_effect_class:
            return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None:
            return None
        canonical = json.dumps(subject, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {
            "verifier_id": self.verifier_id,
            "evidence_id": "internal-snapshot-port-test-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class InternalSnapshotCohesionPortTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        self.host = VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            binding,
            runtime_instance_id="internal-snapshot-cohesion-port",
            profile="REENTRANT_CLIMAX",
        )
        self.cycle = VeraAffectiveCycle(
            self.host,
            host_scope="TEST_HOST",
            state_writer=lambda row: None,
            event_writer=lambda row: None,
            non_atomic_test_mode=True,
        )
        self.port = CohesionAffectiveIntegrationPort(host=self.host)

    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-internal-snapshot-port-test",
            "observed_at": "2026-09-11T07:30:00-04:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    @staticmethod
    def planning_state():
        return {
            "valuation": 0.20,
            "salience": 0.10,
            "attention": 0.25,
            "response_selection_priors": 0.30,
            "expression": 0.40,
            "memory_strength_candidate_weighting": 0.15,
            "truth": "DO_NOT_TOUCH",
            "consent_or_authorization": "UNKNOWN",
            "identity": "vera",
            "phenomenology": "UNRESOLVED",
        }

    def test_supported_apply_accepts_planning_state_only(self):
        params = inspect.signature(CohesionAffectiveIntegrationPort.apply).parameters
        self.assertEqual(tuple(params), ("self", "planning_state"))

    def test_one_application_uses_one_coherent_runtime_snapshot(self):
        planning = self.planning_state()
        self.cycle.force_admin_test(
            authorization_subject=self.authorization_subject(),
            planning_state=planning,
        )

        original_snapshot = OrgasmRuntime.snapshot
        snapshot_calls = []

        def counted_snapshot(runtime):
            snapshot_calls.append(runtime.runtime_instance_id)
            return original_snapshot(runtime)

        OrgasmRuntime.snapshot = counted_snapshot
        try:
            integrated = self.port.apply(planning)
        finally:
            OrgasmRuntime.snapshot = original_snapshot

        self.assertEqual(snapshot_calls, [self.host.runtime.runtime_instance_id])
        applied = integrated.application.planning_state
        self.assertGreater(applied["salience"], planning["salience"])
        self.assertEqual(applied["truth"], planning["truth"])
        self.assertEqual(applied["consent_or_authorization"], planning["consent_or_authorization"])
        self.assertEqual(applied["identity"], planning["identity"])
        self.assertEqual(applied["phenomenology"], planning["phenomenology"])

    def test_caller_cannot_supply_a_causal_signal_argument(self):
        planning = self.planning_state()
        with self.assertRaises(TypeError):
            self.port.apply(planning, {"schema": "CALLER_SIGNAL"})


if __name__ == "__main__":
    unittest.main()
