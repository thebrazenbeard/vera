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

    def test_runtime_operations_are_complete_and_resolve_to_current_modules(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        self.assertEqual(
            set(hook["operations"]),
            {"ORIENT", "DOMAIN_RETRIEVE", "PROJECTION_AUDIT", "RECONCILE", "CHECKPOINT"},
        )
        self.assertEqual(hook["operations"]["DOMAIN_RETRIEVE"]["call"], "runtime_cohesion.runtime.build_retrieval_plan")
        self.assertEqual(hook["operations"]["PROJECTION_AUDIT"]["call"], "runtime_cohesion.audit.audit_registered_projections")
        self.assertEqual(hook["operations"]["RECONCILE"]["call"], "runtime_cohesion.reconcile.reconcile_exact")
        self.assertEqual(hook["operations"]["CHECKPOINT"]["call"], "runtime_cohesion.runtime.build_operational_checkpoint")

    def test_hook_forbids_source_to_install_runtime_promotion(self):
        hook = json.loads(HOOK.read_text(encoding="utf-8"))
        boundary = hook["effect_boundaries"]
        self.assertIn("does not establish native installation", boundary["source"])
        self.assertIn("requires exact native readback", boundary["installation"])
        self.assertIn("requires observable execution evidence", boundary["runtime_consumption"])
        self.assertEqual(hook["behavioral_qualification"], "NOT_QUALIFIED")


if __name__ == "__main__":
    unittest.main()
