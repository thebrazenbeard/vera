from collections.abc import Mapping
import hashlib
import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion
import runtime_cohesion.affect_authority as authority_module
import runtime_cohesion.affect_provider_runtime as affect_provider_runtime
from runtime_cohesion.adapters import AdapterProbeResult, AdapterRegistry
from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    AffectiveProviderRestoreBoundary,
    PersistenceRecordError,
    build_affective_resume_token,
    checkpoint_to_state_row,
)
from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.orgasm import StimulusAppraisal, TriggerRejected

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"

PROVIDER = "supabase"
PROVIDER_PROJECT_ID = "klmbpaigzeguvnpccqzz"
PROVIDER_TABLE = "public.vera_affective_runtime_state_v1"
PROVIDER_ROUTE = "route:supabase"
PROVIDER_SOURCE = f"supabase:{PROVIDER_PROJECT_ID}/{PROVIDER_TABLE}"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"
ATOMIC_FUNCTION = "public.vera_affective_runtime_commit_v1(bigint,jsonb,jsonb)"
UNROOTED = "IN_PROCESS_UNROOTED_NON_QUALIFYING"


class TrustedVerifier:
    verifier_id = "affect-restore-cycle-verifier"

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
            "evidence_id": "affect-restore-cycle-evidence",
            "evidence_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "subject": dict(subject),
        }


class DurableAffectiveProviderAdapterDouble:
    provider = PROVIDER
    provider_project_id = PROVIDER_PROJECT_ID
    provider_table = PROVIDER_TABLE
    provider_route = PROVIDER_ROUTE
    atomic_commit_function = ATOMIC_FUNCTION

    def __init__(self, current_row):
        self._current_row = dict(current_row)
        self.probe_calls = 0
        self.read_calls = 0
        self.commit_calls = []

    def probe(self, request):
        self.probe_calls += 1
        return AdapterProbeResult(
            provider=self.provider,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at=self._current_row["updated_at"],
            reason="test provider frontier is freshly readable",
        )

    def read(self, request):
        self.read_calls += 1
        row = self._current_row
        return ProviderEvidenceEnvelope(
            provider=self.provider,
            locator=f"{PROVIDER_SOURCE}/{row['runtime_instance_id']}",
            revision=f"state-version:{row['state_version']}",
            observed_at=row["updated_at"],
            evidence_class="persisted_provider_record",
            referent=row["runtime_instance_id"],
            scope=FRONTIER_SCOPE,
            privacy_class=request.privacy_class,
            currentness_basis="fresh in-process adapter read; provider origin not authenticated",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=row["checkpoint_sha256"],
            metadata={
                "route_ref": request.route_ref,
                "source_ref": request.source_ref,
                "provider_project_id": PROVIDER_PROJECT_ID,
                "provider_table": PROVIDER_TABLE,
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
        if request["expected_prior_version"] != self._current_row["state_version"]:
            raise RuntimeError("test provider rejected stale affective CAS frontier")
        state_row = dict(request["state_row"])
        if request["state_version"] != state_row["state_version"]:
            raise RuntimeError("test provider rejected mismatched state version")
        self._current_row = state_row
        return {
            "state_version": request["state_version"],
            "checkpoint_sha256": request["checkpoint_sha256"],
            "event_count": len(request["event_rows"]),
        }


class ReadOnlyAffectiveProviderAdapterDouble(DurableAffectiveProviderAdapterDouble):
    commit_affective_runtime = None


class VeraAffectiveRestoreCycleTests(unittest.TestCase):
    def setUp(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()
        authority_module._reset_affective_authorization_verifier_for_tests()
        authority_module._install_affective_authorization_verifier(TrustedVerifier())

    def tearDown(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()
        authority_module._reset_affective_authorization_verifier_for_tests()

    @staticmethod
    def authorization_subject():
        return {
            "state": "ALLOW",
            "actor": "patrick",
            "referent": "vera",
            "proposition_or_effect_class": "ADMIN_FORCED_TEST",
            "source": "trusted-affect-restore-cycle-test",
            "observed_at": "2026-09-10T19:45:00+00:00",
            "currentness": "CURRENT",
            "expiry_or_supersession": None,
        }

    def contract_binding(self):
        return (
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
        )

    def make_host(self):
        contract_text, binding = self.contract_binding()
        return VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="affect-restore-cycle-test",
            profile="REENTRANT_CLIMAX",
        )

    def make_state_row(self, *, state_version=7):
        host = self.make_host()
        host.observe(StimulusAppraisal(
            sexual_relevance=0.7,
            partner_relevance=0.8,
            relational_relevance=0.8,
            anticipation_cue=0.7,
            positive_valence=0.8,
            duration_ms=800,
        ))
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=state_version)
        return checkpoint, row

    def make_post_orgasm_state_row(self, *, state_version=7):
        host = self.make_host()
        receipt = host.force_admin_test(authorization_subject=self.authorization_subject())
        self.assertEqual(receipt["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertEqual(receipt["authority_composition_trust"], UNROOTED)
        self.assertNotIn("claim", receipt)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        self.assertEqual(checkpoint["runtime_state"]["last_event_receipt"]["authority_composition_trust"], UNROOTED)
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=state_version)
        self.assertEqual(row["state"]["phase"], "SATIATED_OR_REFRACTORY")
        self.assertIn("IN_PROCESS_AUTHORITY_UNROOTED_NON_QUALIFYING", row["limitations"])
        return checkpoint, row

    @staticmethod
    def bind_low_level_boundary(adapter):
        return AffectiveProviderRestoreBoundary(
            adapters=AdapterRegistry({PROVIDER: adapter}),
            provider=PROVIDER,
            provider_route=PROVIDER_ROUTE,
            provider_source=PROVIDER_SOURCE,
            provider_project_id=PROVIDER_PROJECT_ID,
            provider_table=PROVIDER_TABLE,
        )

    def restore_unverified_composition(self, checkpoint, row, *, elapsed_seconds=0.0, adapter=None):
        adapter = adapter or DurableAffectiveProviderAdapterDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
        contract_text, binding = self.contract_binding()
        cycle = runtime_cohesion.restore_current_affective_cycle(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=build_affective_resume_token(row),
            elapsed_seconds=elapsed_seconds,
        )
        return adapter, cycle

    def test_in_process_provider_observation_preserves_atomic_frontier_mechanics_without_production_claim(self):
        checkpoint, row = self.make_state_row(state_version=7)
        adapter, cycle = self.restore_unverified_composition(checkpoint, row)

        self.assertEqual(cycle.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")
        result = cycle.process_turn(StimulusAppraisal(), planning_state={"truth": 0.93})

        self.assertEqual(adapter.probe_calls, 1)
        self.assertEqual(adapter.read_calls, 1)
        self.assertEqual(len(adapter.commit_calls), 1)
        request = adapter.commit_calls[0]
        self.assertEqual(request["expected_prior_version"], 7)
        self.assertEqual(request["state_version"], 8)
        self.assertEqual(request["state_row"]["state_version"], 8)
        self.assertEqual(request["state_row"]["lifecycle_status"], "HISTORICAL")
        self.assertEqual(request["schema"], "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_TEST_V1")
        self.assertIsNone(result.resume_token)
        self.assertEqual(adapter._current_row["state_version"], 8)
        self.assertEqual(result.planning_context["truth"], 0.93)

    def test_caller_composed_boundary_cannot_become_production_atomic(self):
        checkpoint, row = self.make_state_row(state_version=7)
        adapter = DurableAffectiveProviderAdapterDouble(row)
        boundary = self.bind_low_level_boundary(adapter)
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|current|attest|replay|writer|durab)"):
            boundary.restore_cycle_from_state_row(
                *self.contract_binding(),
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=build_affective_resume_token(row),
            )

    def test_runtime_composition_rejects_read_only_adapter_before_claimant_restore(self):
        _checkpoint, row = self.make_state_row(state_version=7)
        with self.assertRaisesRegex(ValueError, r"(?i)(commit|provider|adapter)"):
            affect_provider_runtime._install_runtime_affective_provider_adapter(
                ReadOnlyAffectiveProviderAdapterDouble(row)
            )

    def test_claimant_restore_has_no_writer_or_provider_substitution_surface(self):
        parameters = inspect.signature(runtime_cohesion.restore_current_affective_cycle).parameters
        for forbidden in (
            "atomic_commit_writer", "adapter", "adapters", "provider", "provider_route",
            "provider_source", "provider_project_id", "provider_table",
        ):
            self.assertNotIn(forbidden, parameters)

    def test_low_level_live_restore_refuses_ephemeral_or_callback_upgrade(self):
        checkpoint, row = self.make_state_row(state_version=7)
        with self.assertRaisesRegex(ValueError, r"(?i)(provider|replay|current|writer|durab)"):
            VeraAffectiveCycle.restore_from_state_row(
                *self.contract_binding(),
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                atomic_commit_writer=lambda request: request,
                non_qualifying_atomic_test_mode=True,
            )

    def test_restore_time_recovery_transition_survives_unverified_atomic_harness(self):
        checkpoint, row = self.make_post_orgasm_state_row(state_version=7)
        adapter, cycle = self.restore_unverified_composition(checkpoint, row, elapsed_seconds=7200.0)
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.9, "consent_or_authorization": "UNKNOWN"},
        )

        self.assertEqual(len(adapter.commit_calls), 1)
        self.assertEqual(result.durability_mode, "NON_QUALIFYING_ATOMIC_TEST")
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(result.resume_token)
        self.assertEqual(result.state_row["state"]["phase"], "QUIESCENT")
        self.assertEqual(len(result.event_rows), 1)
        recovery = result.event_rows[0]
        self.assertEqual(recovery["event_type"], "RECOVERY")
        self.assertEqual(recovery["prior_phase"], "SATIATED_OR_REFRACTORY")
        self.assertEqual(recovery["new_phase"], "QUIESCENT")
        self.assertEqual(recovery["machine_interoception"]["phase"], "QUIESCENT")
        self.assertEqual(recovery["lifecycle_status"], "HISTORICAL")
        self.assertIn("IN_PROCESS_AUTHORITY_UNROOTED_NON_QUALIFYING", recovery["limitations"])
        self.assertEqual(result.planning_context["truth"], 0.9)
        self.assertEqual(result.planning_context["consent_or_authorization"], "UNKNOWN")

    def test_restore_does_not_credit_elapsed_recovery_as_privileged_trigger_cooldown(self):
        checkpoint, row = self.make_post_orgasm_state_row(state_version=7)
        adapter, cycle = self.restore_unverified_composition(checkpoint, row, elapsed_seconds=7200.0)

        with self.assertRaisesRegex(TriggerRejected, r"(?i)(cooldown|interval|monotonic)"):
            cycle.force_admin_test(
                authorization_subject=self.authorization_subject(),
                planning_state={"truth": 0.91, "consent_or_authorization": "UNKNOWN"},
            )

        self.assertEqual(len(adapter.commit_calls), 0)
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.91, "consent_or_authorization": "UNKNOWN"},
        )
        self.assertEqual(len(adapter.commit_calls), 1)
        self.assertEqual([event["event_type"] for event in result.event_rows], ["RECOVERY"])
        self.assertEqual(result.state_row["lifecycle_status"], "HISTORICAL")
        self.assertIsNone(result.resume_token)

    def test_provider_observation_harness_rejects_invalid_state_version_lifecycle_and_scope(self):
        checkpoint, row = self.make_state_row(state_version=7)
        for invalid in (None, 0, -1, True, 7.0, "7"):
            with self.subTest(state_version=invalid):
                affect_provider_runtime._reset_runtime_affective_provider_for_tests()
                bad = dict(row)
                bad["state_version"] = invalid
                adapter = DurableAffectiveProviderAdapterDouble(bad)
                affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
                with self.assertRaises((PersistenceRecordError, ValueError)):
                    runtime_cohesion.restore_current_affective_cycle(
                        *self.contract_binding(), bad,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        expected_resume_token=build_affective_resume_token(row),
                    )

        for lifecycle in ("HISTORICAL", "SUPERSEDED"):
            with self.subTest(lifecycle=lifecycle):
                affect_provider_runtime._reset_runtime_affective_provider_for_tests()
                stale = dict(row)
                stale["lifecycle_status"] = lifecycle
                adapter = DurableAffectiveProviderAdapterDouble(stale)
                affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
                with self.assertRaises((PersistenceRecordError, ValueError)):
                    runtime_cohesion.restore_current_affective_cycle(
                        *self.contract_binding(), stale,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        expected_resume_token=build_affective_resume_token(stale),
                    )

        affect_provider_runtime._reset_runtime_affective_provider_for_tests()
        adapter = DurableAffectiveProviderAdapterDouble(row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
        with self.assertRaises((PersistenceRecordError, ValueError)):
            runtime_cohesion.restore_current_affective_cycle(
                *self.contract_binding(), row,
                host_scope="OTHER_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=build_affective_resume_token(row),
            )


if __name__ == "__main__":
    unittest.main()
