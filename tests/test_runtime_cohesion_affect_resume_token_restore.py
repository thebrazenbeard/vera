import inspect
import json
from pathlib import Path
import unittest

import runtime_cohesion
import runtime_cohesion.affect_provider_runtime as affect_provider_runtime
from runtime_cohesion.adapters import AdapterProbeResult
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    build_affective_resume_token,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)
from runtime_cohesion.evidence import ProviderEvidenceEnvelope

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


class ResumeProviderDouble:
    provider = PROVIDER
    provider_project_id = PROJECT_ID
    provider_table = TABLE
    provider_route = ROUTE
    atomic_commit_function = ATOMIC_FUNCTION

    def __init__(self, row):
        self.current_row = dict(row)

    def probe(self, request):
        return AdapterProbeResult(
            provider=PROVIDER,
            route_ref=request.route_ref,
            state="CURRENTLY_OBSERVED_REACHABLE",
            observed_at=self.current_row["updated_at"],
            reason="test provider frontier is readable",
        )

    def read(self, request):
        row = self.current_row
        return ProviderEvidenceEnvelope(
            provider=PROVIDER,
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
        if request["expected_prior_version"] != self.current_row["state_version"]:
            raise RuntimeError("stale provider frontier")
        self.current_row = dict(request["state_row"])
        return {
            "state_version": request["state_version"],
            "checkpoint_sha256": request["checkpoint_sha256"],
            "event_count": len(request["event_rows"]),
        }


class VeraAffectiveResumeTokenRestoreTests(unittest.TestCase):
    def setUp(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def tearDown(self):
        affect_provider_runtime._reset_runtime_affective_provider_for_tests()

    def contract_text_and_binding(self):
        return (
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
        )

    def make_row(self, *, state_version=7):
        contract_text, binding = self.contract_text_and_binding()
        host = VeraAffectiveRuntimeHost.from_bound_contract(
            contract_text,
            binding,
            runtime_instance_id="resume-token-restore-test",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        row = checkpoint_to_state_row(checkpoint, host_scope="TEST_HOST", state_version=state_version)
        return checkpoint, row, build_affective_resume_token(row)

    def restore_provider(self, checkpoint, row, token, *, provider_row=None):
        adapter = ResumeProviderDouble(provider_row or row)
        affect_provider_runtime._install_runtime_affective_provider_adapter(adapter)
        contract_text, binding = self.contract_text_and_binding()
        return runtime_cohesion.restore_current_affective_cycle(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )

    def test_claimant_provider_restore_requires_external_resume_token(self):
        self.assertIn("expected_resume_token", inspect.signature(runtime_cohesion.restore_current_affective_cycle).parameters)
        self.assertNotIn("expected_resume_token", inspect.signature(restore_host_from_state_row).parameters)

    def test_exact_resume_token_binds_provider_state_version_frontier(self):
        checkpoint, row, token = self.make_row(state_version=7)
        cycle = self.restore_provider(checkpoint, row, token)
        self.assertEqual(cycle._next_state_version, 8)
        self.assertEqual(cycle.durability_mode, "ATOMIC_DURABLE")

    def test_low_level_restore_accepts_exact_bytes_only_as_replay_host(self):
        checkpoint, row, _token = self.make_row(state_version=7)
        contract_text, binding = self.contract_text_and_binding()
        host = restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        self.assertEqual(host.runtime.runtime_instance_id, row["runtime_instance_id"])

    def test_same_checkpoint_with_changed_candidate_version_is_rejected_by_provider_currentness(self):
        checkpoint, provider_row, _token = self.make_row(state_version=7)
        replayed = dict(provider_row)
        replayed["state_version"] = 8
        replayed_token = build_affective_resume_token(replayed)
        with self.assertRaisesRegex((PersistenceRecordError, ValueError), r"(?i)(provider|frontier|version|current|resume)"):
            self.restore_provider(checkpoint, replayed, replayed_token, provider_row=provider_row)

    def test_resume_token_must_bind_runtime_source_checkpoint_and_version(self):
        checkpoint, row, token = self.make_row(state_version=7)
        for field, value in (
            ("runtime_instance_id", "other-runtime"),
            ("source_commit", "0" * 40),
            ("checkpoint_sha256", "0" * 64),
            ("state_version", 8),
        ):
            with self.subTest(field=field):
                affect_provider_runtime._reset_runtime_affective_provider_for_tests()
                bad = dict(token)
                bad[field] = value
                with self.assertRaisesRegex((PersistenceRecordError, ValueError), r"(?i)(resume|frontier|provider|source|checkpoint|version)"):
                    self.restore_provider(checkpoint, row, bad)


if __name__ == "__main__":
    unittest.main()
