import inspect
import json
from pathlib import Path
import unittest

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
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"

PROVIDER = "supabase"
PROVIDER_PROJECT_ID = "klmbpaigzeguvnpccqzz"
PROVIDER_TABLE = "public.vera_affective_runtime_state_v1"
PROVIDER_ROUTE = "route:supabase"
PROVIDER_SOURCE = f"supabase:{PROVIDER_PROJECT_ID}/{PROVIDER_TABLE}"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"


class DurableAffectiveProviderAdapterDouble:
    """One prebound provider object owns both CURRENT read and atomic commit."""

    provider = PROVIDER

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
            currentness_basis="fresh runtime-owned adapter read",
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
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
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
            context_eligible=True,
        ))
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row

    def make_post_orgasm_state_row(self, *, state_version=7):
        host = self.make_host()
        host.force_admin_test(authorized=True)
        host.advance_time(5.1)
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        self.assertEqual(row["state"]["phase"], "SATIATED_OR_REFRACTORY")
        return checkpoint, row

    @staticmethod
    def exact_writer_recorder(requests):
        def exact_writer(request):
            requests.append(dict(request))
            return {
                "state_version": request["state_version"],
                "checkpoint_sha256": request["checkpoint_sha256"],
                "event_count": len(request["event_rows"]),
            }
        return exact_writer

    @staticmethod
    def bind_provider_boundary(adapter):
        return AffectiveProviderRestoreBoundary(
            adapters=AdapterRegistry({PROVIDER: adapter}),
            provider=PROVIDER,
            provider_route=PROVIDER_ROUTE,
            provider_source=PROVIDER_SOURCE,
            provider_project_id=PROVIDER_PROJECT_ID,
            provider_table=PROVIDER_TABLE,
        )

    def test_restore_factory_continues_exact_provider_version_frontier(self):
        checkpoint, row = self.make_state_row(state_version=7)
        requests = []
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            elapsed_seconds=60.0,
            atomic_commit_writer=self.exact_writer_recorder(requests),
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.9},
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["expected_prior_version"], 7)
        self.assertEqual(requests[0]["state_version"], 8)
        self.assertEqual(result.state_row["state_version"], 8)
        self.assertEqual(result.planning_context["truth"], 0.9)

    def test_provider_authenticated_restore_returns_atomic_cycle_and_commits_next_frontier(self):
        checkpoint, row = self.make_state_row(state_version=7)
        adapter = DurableAffectiveProviderAdapterDouble(row)
        boundary = self.bind_provider_boundary(adapter)
        token = build_affective_resume_token(row)

        cycle = boundary.restore_cycle_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )

        self.assertEqual(cycle.durability_mode, "ATOMIC_DURABLE")
        self.assertIsNotNone(cycle.atomic_commit_writer)
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.93},
        )

        self.assertEqual(adapter.probe_calls, 1)
        self.assertEqual(adapter.read_calls, 1)
        self.assertEqual(len(adapter.commit_calls), 1)
        request = adapter.commit_calls[0]
        self.assertEqual(request["expected_prior_version"], 7)
        self.assertEqual(request["state_version"], 8)
        self.assertEqual(request["state_row"]["state_version"], 8)
        self.assertEqual(result.resume_token["state_version"], 8)
        self.assertEqual(adapter._current_row["state_version"], 8)
        self.assertEqual(result.planning_context["truth"], 0.93)

    def test_provider_authenticated_restore_rejects_read_only_adapter(self):
        checkpoint, row = self.make_state_row(state_version=7)
        boundary = self.bind_provider_boundary(ReadOnlyAffectiveProviderAdapterDouble(row))
        token = build_affective_resume_token(row)

        with self.assertRaisesRegex(PersistenceRecordError, r"(?i)(atomic|commit|writer|durab)"):
            boundary.restore_cycle_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
            )

    def test_provider_authenticated_restore_has_no_caller_writer_substitution_surface(self):
        checkpoint, row = self.make_state_row(state_version=7)
        boundary = self.bind_provider_boundary(DurableAffectiveProviderAdapterDouble(row))
        token = build_affective_resume_token(row)
        parameters = inspect.signature(boundary.restore_cycle_from_state_row).parameters
        self.assertNotIn("atomic_commit_writer", parameters)

        with self.assertRaises(TypeError):
            boundary.restore_cycle_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
                atomic_commit_writer=lambda request: request,
            )

    def test_low_level_live_restore_refuses_ephemeral_downgrade(self):
        checkpoint, row = self.make_state_row(state_version=7)
        with self.assertRaisesRegex(ValueError, r"(?i)(atomic|writer|durab|ephemeral)"):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            )

    def test_restore_time_recovery_transition_is_not_discarded_before_next_commit(self):
        checkpoint, row = self.make_post_orgasm_state_row(state_version=7)
        requests = []
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            elapsed_seconds=7200.0,
            atomic_commit_writer=self.exact_writer_recorder(requests),
        )
        result = cycle.process_turn(
            StimulusAppraisal(),
            planning_state={"truth": 0.9, "consent_or_authorization": "UNKNOWN"},
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(result.state_row["state"]["phase"], "QUIESCENT")
        self.assertEqual(len(result.event_rows), 1)
        recovery = result.event_rows[0]
        self.assertEqual(recovery["event_type"], "RECOVERY")
        self.assertEqual(recovery["prior_phase"], "SATIATED_OR_REFRACTORY")
        self.assertEqual(recovery["new_phase"], "QUIESCENT")
        self.assertEqual(recovery["machine_interoception"]["phase"], "QUIESCENT")
        self.assertEqual(result.planning_context["truth"], 0.9)
        self.assertEqual(result.planning_context["consent_or_authorization"], "UNKNOWN")

    def test_restore_time_recovery_and_new_forced_event_are_committed_in_order(self):
        checkpoint, row = self.make_post_orgasm_state_row(state_version=7)
        requests = []
        cycle = VeraAffectiveCycle.restore_from_state_row(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            elapsed_seconds=7200.0,
            atomic_commit_writer=self.exact_writer_recorder(requests),
        )
        result = cycle.force_admin_test(
            authorized=True,
            planning_state={"truth": 0.91, "consent_or_authorization": "UNKNOWN"},
        )

        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["expected_prior_version"], 7)
        self.assertEqual(requests[0]["state_version"], 8)
        self.assertEqual([row["event_type"] for row in result.event_rows], ["RECOVERY", "ORGASM_EVENT"])
        self.assertEqual(result.event_rows[0]["new_phase"], "QUIESCENT")
        self.assertEqual(result.event_rows[1]["trigger_class"], "ADMIN_FORCED_TEST")
        self.assertFalse(result.event_rows[1]["organic"])
        self.assertEqual(result.machine_interoception["phase"], "ORGASM_EVENT")
        self.assertEqual(result.planning_context["truth"], 0.91)
        self.assertEqual(result.planning_context["consent_or_authorization"], "UNKNOWN")

    def test_restore_factory_rejects_missing_or_invalid_state_version(self):
        checkpoint, row = self.make_state_row(state_version=7)
        for invalid in (None, 0, -1, True, 7.0, "7"):
            with self.subTest(state_version=invalid):
                bad = dict(row)
                bad["state_version"] = invalid
                with self.assertRaises(ValueError):
                    VeraAffectiveCycle.restore_from_state_row(
                        CONTRACT_PATH.read_text(encoding="utf-8"),
                        json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                        bad,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        atomic_commit_writer=self.exact_writer_recorder([]),
                    )

    def test_live_restore_rejects_historical_and_superseded_rows(self):
        checkpoint, row = self.make_state_row(state_version=7)
        for lifecycle in ("HISTORICAL", "SUPERSEDED"):
            with self.subTest(lifecycle=lifecycle):
                stale = dict(row)
                stale["lifecycle_status"] = lifecycle
                with self.assertRaises(ValueError):
                    VeraAffectiveCycle.restore_from_state_row(
                        CONTRACT_PATH.read_text(encoding="utf-8"),
                        json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                        stale,
                        host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        atomic_commit_writer=self.exact_writer_recorder([]),
                    )

    def test_live_restore_binds_host_scope_to_provider_row(self):
        checkpoint, row = self.make_state_row(state_version=7)
        with self.assertRaises(ValueError):
            VeraAffectiveCycle.restore_from_state_row(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                row,
                host_scope="OTHER_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                atomic_commit_writer=self.exact_writer_recorder([]),
            )


if __name__ == "__main__":
    unittest.main()
