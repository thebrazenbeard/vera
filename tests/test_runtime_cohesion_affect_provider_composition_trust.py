import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion
import runtime_cohesion.affect_persistence as affect_persistence
import runtime_cohesion.affect_provider_runtime as affect_provider_runtime
from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.orgasm import StimulusAppraisal


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"

PROVIDER = "supabase"
PROJECT_ID = "klmbpaigzeguvnpccqzz"
TABLE = "public.vera_affective_runtime_state_v1"
ROUTE = "route:supabase"
SOURCE = f"supabase:{PROJECT_ID}/{TABLE}"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"
ATOMIC_FUNCTION = "public.vera_affective_runtime_commit_v1(bigint,jsonb,jsonb)"


class SelfConsistentAffectiveProviderDouble:
    provider = PROVIDER
    provider_project_id = PROJECT_ID
    provider_table = TABLE
    provider_route = ROUTE
    atomic_commit_function = ATOMIC_FUNCTION

    def __init__(self, current_row):
        self.current_row = dict(current_row)
        self.commit_calls = []

    def probe(self, request):
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at=self.current_row["updated_at"],
            reason="test provider frontier is readable",
        )

    def read(self, request):
        row = self.current_row
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{SOURCE}/{row['runtime_instance_id']}",
            revision=f"state-version:{row['state_version']}",
            observed_at=row["updated_at"],
            evidence_class="persisted_provider_record",
            referent=row["runtime_instance_id"],
            scope=FRONTIER_SCOPE,
            privacy_class=request.privacy_class,
            currentness_basis="fresh test adapter read",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=row["checkpoint_sha256"],
            metadata={
                "route_ref": request.route_ref,
                "source_ref": request.source_ref,
                "provider_project_id": PROJECT_ID,
                "provider_table": TABLE,
                "runtime_instance_id": row["runtime_instance_id"],
                "host_scope": row["host_scope"],
                "state_version": row["state_version"],
                "checkpoint_sha256": row["checkpoint_sha256"],
                "source_commit": row["source_commit"],
            },
        )

    def commit_affective_runtime(self, request):
        request = dict(request)
        self.commit_calls.append(request)
        if request["expected_prior_version"] != self.current_row["state_version"]:
            raise RuntimeError("stale provider frontier")
        self.current_row = dict(request["state_row"])
        return {
            "state_version": request["state_version"],
            "checkpoint_sha256": request["checkpoint_sha256"],
            "event_count": len(request["event_rows"]),
        }


class ProviderCompositionTrustTests(unittest.TestCase):
    def setUp(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def tearDown(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def material(self, *, state_version=7):
        contract_text = CONTRACT_PATH.read_text(encoding="utf-8")
        binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="provider-composition-trust-test",
        )
        checkpoint = host.export_checkpoint()
        row = affect_persistence.checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        token = affect_persistence.build_affective_resume_token(row)
        return contract_text, binding, checkpoint, row, token

    @staticmethod
    def echo_writer(calls):
        def writer(request):
            calls.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }
        return writer

    def test_low_level_row_restore_is_replay_only_and_cannot_reenter_durable_cycle(self):
        contract_text, binding, checkpoint, row, _token = self.material()
        host = affect_persistence.restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        calls = []
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|current|attest|replay|durab|writer)"):
            VeraAffectiveCycle(
                host,
                host_scope="TEST_HOST",
                initial_state_version=8,
                atomic_commit_writer=self.echo_writer(calls),
            )
        self.assertEqual(calls, [])

    def test_direct_caller_composed_provider_boundary_is_non_authoritative(self):
        contract_text, binding, checkpoint, row, token = self.material()
        adapter = SelfConsistentAffectiveProviderDouble(row)
        boundary = affect_persistence.AffectiveProviderRestoreBoundary(
            adapters=AdapterRegistry({PROVIDER: adapter}),
            provider=PROVIDER,
            provider_route=ROUTE,
            provider_source=SOURCE,
            provider_project_id=PROJECT_ID,
            provider_table=TABLE,
        )
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|current|attest|replay|qualif|writer|durab)"):
            boundary.restore_cycle_from_state_row(
                contract_text,
                binding,
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
            )
        self.assertEqual(adapter.commit_calls, [])

    def test_claimant_facing_production_restore_has_no_provider_composition_injection_surface(self):
        self.assertTrue(hasattr(runtime_cohesion, "restore_current_affective_cycle"))
        parameters = inspect.signature(runtime_cohesion.restore_current_affective_cycle).parameters
        for forbidden in (
            "adapters",
            "adapter",
            "provider",
            "provider_route",
            "provider_source",
            "provider_project_id",
            "provider_table",
            "atomic_commit_writer",
        ):
            self.assertNotIn(forbidden, parameters)

    def test_runtime_owned_provider_composition_restores_atomic_exact_frontier(self):
        contract_text, binding, checkpoint, row, token = self.material()
        adapter = SelfConsistentAffectiveProviderDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)

        cycle = runtime_cohesion.restore_current_affective_cycle(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )
        self.assertEqual(cycle.durability_mode, "ATOMIC_DURABLE")
        result = cycle.process_turn(StimulusAppraisal(), planning_state={"truth": 0.94})
        self.assertEqual(len(adapter.commit_calls), 1)
        self.assertEqual(adapter.commit_calls[0]["expected_prior_version"], 7)
        self.assertEqual(adapter.commit_calls[0]["state_version"], 8)
        self.assertEqual(result.resume_token["state_version"], 8)
        self.assertEqual(result.state_row["lifecycle_status"], "CURRENT")
        self.assertEqual(result.planning_context["truth"], 0.94)

    def test_runtime_provider_composition_cannot_be_replaced_after_install(self):
        _contract_text, _binding, _checkpoint, row, _token = self.material()
        first = SelfConsistentAffectiveProviderDouble(row)
        second = SelfConsistentAffectiveProviderDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(first)
        with self.assertRaisesRegex((RuntimeError, ValueError), r"(?i)(already|replace|bound|install|composition)"):
            affect_provider_runtime._install_runtime_affective_provider_adapter(second)

    def test_arbitrary_atomic_callback_cannot_mint_production_durability(self):
        contract_text, binding, _checkpoint, _row, _token = self.material()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="caller-writer-durability-test",
        )
        calls = []
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|test|qualif|writer|durab)"):
            VeraAffectiveCycle(
                host,
                host_scope="TEST_HOST",
                atomic_commit_writer=self.echo_writer(calls),
            )
        self.assertEqual(calls, [])

    def test_explicit_atomic_test_seam_is_nonqualifying_and_emits_no_resume_token(self):
        contract_text, binding, _checkpoint, _row, _token = self.material()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="explicit-atomic-test-seam",
        )
        calls = []
        cycle = VeraAffectiveCycle(
            host,
            host_scope="TEST_HOST",
            atomic_commit_writer=self.echo_writer(calls),
            non_qualifying_atomic_test_mode=True,
        )
        self.assertEqual(cycle.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")
        result = cycle.process_turn(StimulusAppraisal(), planning_state={})
        self.assertIsNone(result.resume_token)
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertNotEqual(result.commit_request.get("schema"), "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_V1")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
