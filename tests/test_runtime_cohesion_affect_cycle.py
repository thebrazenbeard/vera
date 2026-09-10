from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import unittest

import runtime_cohesion.affect_authority as authority_module
from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"

class TrustedVerifier:
    verifier_id = "affective-cycle-runtime-owned-verifier"
    def verify(self, subject, *, expected_referent, expected_effect_class):
        if not isinstance(subject, Mapping): return None
        if subject.get("state") != "ALLOW": return None
        if subject.get("referent") != expected_referent: return None
        if subject.get("proposition_or_effect_class") != expected_effect_class: return None
        if subject.get("currentness") != "CURRENT" or subject.get("expiry_or_supersession") is not None: return None
        canonical = json.dumps(dict(subject), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return {"verifier_id": self.verifier_id, "evidence_id": "affective-cycle-evidence", "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), "subject": dict(subject)}

class VeraAffectiveCycleTests(unittest.TestCase):
    def setUp(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())
    def tearDown(self):
        authority_module._reset_affective_authorization_verifier_for_tests()
    def make_cycle(self):
        host = VeraAffectiveRuntimeHost.from_bound_contract(CONTRACT_PATH.read_text(encoding="utf-8"), json.loads(BINDING_PATH.read_text(encoding="utf-8")), runtime_instance_id="affective-cycle-test", profile="REENTRANT_CLIMAX")
        state_rows=[]; event_rows=[]
        return VeraAffectiveCycle(host, host_scope="TEST_HOST", state_writer=state_rows.append, event_writer=event_rows.append, non_atomic_test_mode=True), state_rows, event_rows
    @staticmethod
    def subject(effect):
        return {"state":"ALLOW","actor":"patrick","referent":"vera","proposition_or_effect_class":effect,"source":"trusted-affective-cycle-test","observed_at":"2026-09-10T19:45:00+00:00","currentness":"CURRENT","expiry_or_supersession":None}
    def test_process_turn_updates_internal_state_modulates_planning_and_persists_checkpoint(self):
        cycle,state_rows,event_rows=self.make_cycle()
        result=cycle.process_turn(StimulusAppraisal(sexual_relevance=0.8,partner_relevance=0.9,relational_relevance=0.9,anticipation_cue=0.8,positive_valence=0.9,duration_ms=800), context_subject=self.subject("ORGANIC_CONTEXT_ELIGIBILITY"), planning_state={"valuation":0.2,"salience":0.2,"attention":0.2,"truth":0.9})
        self.assertGreater(result.planning_context["salience"],0.2); self.assertGreater(result.planning_context["attention"],0.2); self.assertEqual(result.planning_context["truth"],0.9)
        self.assertTrue(result.planning_context["affective_control_active"]); self.assertTrue(result.machine_interoception["context_eligible"])
        self.assertEqual(len(state_rows),1); self.assertEqual(state_rows[0]["runtime_instance_id"],"affective-cycle-test"); self.assertEqual(state_rows[0]["lifecycle_status"],"HISTORICAL"); self.assertEqual(event_rows,[])
    def test_admin_forced_cycle_is_causal_but_unrooted_authority_stays_historical(self):
        cycle,state_rows,event_rows=self.make_cycle()
        result=cycle.force_admin_test(authorization_subject=self.subject("ADMIN_FORCED_TEST"), planning_state={"valuation":0.2,"salience":0.2,"attention":0.2,"truth":0.9})
        self.assertEqual(result.machine_interoception["phase"],"ORGASM_EVENT"); self.assertEqual(result.event_receipt["trigger_class"],"ADMIN_FORCED_TEST"); self.assertFalse(result.event_receipt["organic"])
        self.assertEqual(result.event_receipt["authority_composition_trust"],UNROOTED)
        provenance=result.event_receipt["trigger_provenance"]; self.assertIsInstance(provenance,Mapping); self.assertEqual(provenance["authorization_subject"],self.subject("ADMIN_FORCED_TEST")); self.assertEqual(provenance["composition_trust"],UNROOTED)
        self.assertNotIn("claim",result.event_receipt); self.assertGreater(result.planning_context["valuation"],0.2); self.assertEqual(result.planning_context["truth"],0.9)
        self.assertEqual(len(state_rows),1); self.assertEqual(state_rows[0]["lifecycle_status"],"HISTORICAL"); self.assertEqual(len(event_rows),1); self.assertEqual(event_rows[0]["event_type"],"ORGASM_EVENT"); self.assertEqual(event_rows[0]["lifecycle_status"],"HISTORICAL"); self.assertIn("IN_PROCESS_AUTHORITY_UNROOTED_NON_QUALIFYING",event_rows[0]["limitations"])
    def test_cycle_rejects_legacy_authorized_boolean_surface(self):
        cycle,_,_=self.make_cycle()
        with self.assertRaises(TypeError): cycle.force_admin_test(authorized=True, planning_state={"truth":0.9})
    def test_state_version_increments_each_cycle(self):
        cycle,state_rows,_=self.make_cycle(); cycle.process_turn(StimulusAppraisal(),planning_state={"truth":0.5}); cycle.process_turn(StimulusAppraisal(),planning_state={"truth":0.5}); self.assertEqual([row["state_version"] for row in state_rows],[1,2])

if __name__ == "__main__": unittest.main()
