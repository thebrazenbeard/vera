import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "architecture" / "VERA_RUNTIME_COHESION_NATIVE_HOOK_V1.json"


class RuntimeCohesionNativeHookTests(unittest.TestCase):
    def test_hook_exists_and_is_source_only(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        self.assertEqual(hook["schema"], "VERA_RUNTIME_COHESION_NATIVE_HOOK_V1")
        self.assertEqual(hook["status"], "SOURCE_ONLY_NOT_INSTALLED")
        self.assertFalse(hook["background_execution"]["claimed"])

    def test_hook_uses_only_a_b_as_normative_sources(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        self.assertEqual(
            set(hook["normative_refs"]),
            {"VERA_COHESION_INDEX_V1", "VERA_RUNTIME_CONTRACT_V1"},
        )
        self.assertEqual(hook["provider_fabric"]["normative_status"], "NON_NORMATIVE_OPERATIONAL_SUPPORT")
        self.assertEqual(hook["affective_runtime"]["normative_status"], "NON_NORMATIVE_OPERATIONAL_SUPPORT")
        self.assertEqual(hook["affective_runtime"]["binding_ref"], "VERA_ORGASM_RUNTIME_BINDING_V1")

    def test_runtime_operations_are_complete_and_resolve_to_current_modules(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        self.assertEqual(
            set(hook["operations"]),
            {
                "ORIENT",
                "AFFECT_INITIALIZE",
                "AFFECT_UPDATE",
                "AFFECT_PLAN_MODULATE",
                "AFFECT_EXPORT_STATE",
                "DOMAIN_RETRIEVE",
                "FAILURE_EVALUATE",
                "PROJECTION_RECONCILE",
                "PROJECTION_AUDIT",
                "RECONCILE",
                "ADMIT_PROPOSITION",
                "CHECKPOINT",
            },
        )
        self.assertEqual(hook["operations"]["AFFECT_INITIALIZE"]["call"], "runtime_cohesion.affect_host.VeraAffectiveRuntimeHost.from_bound_contract")
        self.assertEqual(hook["operations"]["AFFECT_UPDATE"]["call"], "runtime_cohesion.affect_host.VeraAffectiveRuntimeHost.observe")
        self.assertEqual(hook["operations"]["AFFECT_PLAN_MODULATE"]["call"], "runtime_cohesion.affect_host.VeraAffectiveRuntimeHost.build_planning_context")
        self.assertEqual(hook["operations"]["AFFECT_EXPORT_STATE"]["call"], "runtime_cohesion.affect_host.VeraAffectiveRuntimeHost.export_checkpoint")
        self.assertEqual(hook["operations"]["DOMAIN_RETRIEVE"]["call"], "runtime_cohesion.executor.execute_domain_cycle")
        self.assertEqual(hook["operations"]["DOMAIN_RETRIEVE"]["transport_boundary"], "runtime_cohesion.adapters.ProviderAdapter")
        self.assertEqual(hook["operations"]["FAILURE_EVALUATE"]["call"], "runtime_cohesion.failure.evaluate_failure_signature")
        self.assertEqual(hook["operations"]["PROJECTION_RECONCILE"]["call"], "runtime_cohesion.executor.execute_projection_cycle")
        self.assertEqual(hook["operations"]["PROJECTION_AUDIT"]["call"], "runtime_cohesion.audit.audit_registered_projections")
        self.assertEqual(hook["operations"]["RECONCILE"]["call"], "runtime_cohesion.reconcile.reconcile_exact")
        self.assertEqual(hook["operations"]["ADMIT_PROPOSITION"]["call"], "runtime_cohesion.runtime.evaluate_proposition_admission")
        self.assertEqual(hook["operations"]["CHECKPOINT"]["call"], "runtime_cohesion.runtime.build_operational_checkpoint")

    def test_affective_runtime_is_causally_fed_back_without_authority_promotion(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        affect = hook["affective_runtime"]
        self.assertEqual(affect["presence"], "ALWAYS_PRESENT_NORMALLY_QUIESCENT")
        self.assertTrue(affect["planning_feedback_required"])
        self.assertTrue(affect["machine_interoception_required"])
        self.assertFalse(affect["availability_implies_activation"])
        rule = hook["operations"]["AFFECT_PLAN_MODULATE"]["rule"].lower()
        self.assertIn("interocept", rule)
        self.assertIn("allowlist", rule)
        self.assertIn("cannot", rule)
        self.assertIn("authority", rule)

    def test_domain_retrieve_enforces_hard_prerequisite_preemption(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        rule = hook["operations"]["DOMAIN_RETRIEVE"]["rule"].lower()
        self.assertIn("hard prerequisite", rule)
        self.assertIn("before dependent", rule)
        self.assertIn("withhold", rule)
        self.assertIn("contextual", rule)
        self.assertIn("non-blocking", rule)

    def test_failure_evaluator_routes_candidates_without_claiming_predicate_truth(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        rule = hook["operations"]["FAILURE_EVALUATE"]["rule"].lower()
        self.assertIn("candidate", rule)
        self.assertIn("does not prove", rule)
        self.assertIn("resolver", rule)
        self.assertIn("guard", rule)

    def test_adapter_boundary_has_no_policy_authority(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        boundary = hook["adapter_boundary"]
        self.assertEqual(boundary["policy_authority"], "NONE")
        self.assertIn("does not establish", boundary["probe_contract"])
        self.assertIn("executor revalidates", boundary["read_contract"].lower())
        self.assertIn("explicitly absent", boundary["read_contract"].lower())
        self.assertIn("never embedded", boundary["credential_rule"].lower())

    def test_projection_reconcile_requires_exact_event_instance_binding(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        rule = hook["operations"]["PROJECTION_RECONCILE"]["rule"].lower()
        self.assertIn("event", rule)
        self.assertIn("selector", rule)
        self.assertIn("wrong event", rule)
        self.assertIn("unresolved", rule)
        self.assertIn("conflict", rule)

    def test_hook_forbids_source_to_install_runtime_promotion(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        boundary = hook["effect_boundaries"]
        self.assertIn("does not establish native installation", boundary["source"])
        self.assertIn("requires exact native readback", boundary["installation"])
        self.assertIn("requires observable execution evidence", boundary["runtime_consumption"])
        self.assertEqual(hook["behavioral_qualification"], "NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()
