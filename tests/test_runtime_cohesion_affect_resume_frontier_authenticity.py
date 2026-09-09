import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import runtime_cohesion.affect_persistence as affect_persistence
from runtime_cohesion.adapters import (
    AdapterProbeResult,
    AdapterRegistry,
)
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.evidence import ProviderEvidenceEnvelope


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"

PROVIDER = "supabase"
PROVIDER_PROJECT_ID = "klmbpaigzeguvnpccqzz"
PROVIDER_TABLE = "public.vera_affective_runtime_state_v1"
PROVIDER_ROUTE = "route:supabase"
PROVIDER_SOURCE = f"supabase:{PROVIDER_PROJECT_ID}/{PROVIDER_TABLE}"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"


class AffectiveProviderReadAdapterDouble:
    """Runtime-owned adapter double; claimant row/token do not configure it."""

    provider = PROVIDER

    def __init__(self, current_row):
        self._current_row = dict(current_row)
        self.probe_calls = 0
        self.read_calls = 0

    def advance_provider_frontier(self, row):
        self._current_row = dict(row)

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


class DuckTypedAffectiveProviderReadAdapterDouble(AffectiveProviderReadAdapterDouble):
    def read(self, request):
        real = super().read(request)
        return SimpleNamespace(**real.__dict__)


class VeraAffectiveResumeFrontierAuthenticityTests(unittest.TestCase):
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
            runtime_instance_id="resume-frontier-authenticity-test",
            profile="REENTRANT_CLIMAX",
        )
        checkpoint = host.export_checkpoint()
        row = affect_persistence.checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row, affect_persistence.build_affective_resume_token(row)

    def bind_restore_boundary(self, adapter):
        self.assertTrue(
            hasattr(affect_persistence, "AffectiveProviderRestoreBoundary"),
            "live affective restore needs a provider-read boundary configured outside claimant input",
        )
        boundary_type = affect_persistence.AffectiveProviderRestoreBoundary
        return boundary_type(
            adapters=AdapterRegistry({PROVIDER: adapter}),
            provider=PROVIDER,
            provider_route=PROVIDER_ROUTE,
            provider_source=PROVIDER_SOURCE,
            provider_project_id=PROVIDER_PROJECT_ID,
            provider_table=PROVIDER_TABLE,
        )

    def restore_host(self, boundary, checkpoint, row, token):
        contract_text, binding = self.contract_text_and_binding()
        return boundary.restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )

    def restore_cycle(self, boundary, checkpoint, row, token):
        contract_text, binding = self.contract_text_and_binding()
        return boundary.restore_cycle_from_state_row(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
        )

    def test_exact_current_frontier_accepts_through_prebound_provider_read_boundary(self):
        checkpoint, row, token = self.make_row(state_version=7)
        adapter = AffectiveProviderReadAdapterDouble(row)
        boundary = self.bind_restore_boundary(adapter)

        host = self.restore_host(boundary, checkpoint, row, token)

        self.assertEqual(host.runtime.runtime_instance_id, row["runtime_instance_id"])
        self.assertEqual(adapter.probe_calls, 1)
        self.assertEqual(adapter.read_calls, 1)

    def test_cycle_restore_uses_same_prebound_provider_read_boundary(self):
        checkpoint, row, token = self.make_row(state_version=7)
        adapter = AffectiveProviderReadAdapterDouble(row)
        boundary = self.bind_restore_boundary(adapter)

        cycle = self.restore_cycle(boundary, checkpoint, row, token)

        self.assertEqual(cycle._next_state_version, 8)
        self.assertEqual(adapter.probe_calls, 1)
        self.assertEqual(adapter.read_calls, 1)

    def test_candidate_row_and_candidate_token_cannot_vouch_for_themselves(self):
        checkpoint, trusted_row, _trusted_token = self.make_row(state_version=7)
        adapter = AffectiveProviderReadAdapterDouble(trusted_row)
        boundary = self.bind_restore_boundary(adapter)

        candidate = dict(trusted_row)
        candidate["state_version"] = 8
        candidate_token = affect_persistence.build_affective_resume_token(candidate)

        self.assertEqual(candidate_token["state_version"], candidate["state_version"])
        self.assertEqual(
            candidate_token["checkpoint_sha256"],
            candidate["checkpoint_sha256"],
        )

        with self.assertRaisesRegex(
            (affect_persistence.PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|current|read|version|resume)",
        ):
            self.restore_host(boundary, checkpoint, candidate, candidate_token)

        self.assertEqual(adapter.read_calls, 1)

    def test_once_valid_old_row_fails_after_provider_frontier_advances(self):
        checkpoint, old_row, old_token = self.make_row(state_version=7)
        adapter = AffectiveProviderReadAdapterDouble(old_row)
        boundary = self.bind_restore_boundary(adapter)

        # This was once the exact provider frontier.
        old_host = self.restore_host(boundary, checkpoint, old_row, old_token)
        self.assertEqual(old_host.runtime.runtime_instance_id, old_row["runtime_instance_id"])

        newer_row = dict(old_row)
        newer_row["state_version"] = 8
        adapter.advance_provider_frontier(newer_row)

        with self.assertRaisesRegex(
            (affect_persistence.PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|current|stale|read|version|resume)",
        ):
            self.restore_host(boundary, checkpoint, old_row, old_token)

        self.assertEqual(adapter.read_calls, 2)

    def test_current_row_succeeds_after_same_provider_frontier_advance(self):
        checkpoint, old_row, _old_token = self.make_row(state_version=7)
        adapter = AffectiveProviderReadAdapterDouble(old_row)
        boundary = self.bind_restore_boundary(adapter)

        current_row = dict(old_row)
        current_row["state_version"] = 8
        current_token = affect_persistence.build_affective_resume_token(current_row)
        adapter.advance_provider_frontier(current_row)

        host = self.restore_host(boundary, checkpoint, current_row, current_token)

        self.assertEqual(host.runtime.runtime_instance_id, current_row["runtime_instance_id"])
        self.assertEqual(adapter.read_calls, 1)

    def test_caller_constructed_provider_envelope_is_not_a_live_restore_positive(self):
        checkpoint, row, token = self.make_row(state_version=7)
        caller_envelope = AffectiveProviderReadAdapterDouble(row).read(
            SimpleNamespace(
                route_ref=PROVIDER_ROUTE,
                source_ref=PROVIDER_SOURCE,
                privacy_class="GOVERNED",
            )
        )
        contract_text, binding = self.contract_text_and_binding()

        # The low-level claimant path may not treat a caller-created envelope as
        # equivalent to a read performed by the prebound provider adapter.
        with self.assertRaisesRegex(
            (affect_persistence.PersistenceRecordError, TypeError, ValueError),
            r"(?i)(provider|read|frontier|evidence|bound|resume)",
        ):
            affect_persistence.restore_host_from_state_row(
                contract_text,
                binding,
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
                resume_frontier_evidence=caller_envelope,
            )

    def test_duck_typed_adapter_read_cannot_impersonate_provider_evidence(self):
        checkpoint, row, token = self.make_row(state_version=7)
        adapter = DuckTypedAffectiveProviderReadAdapterDouble(row)
        boundary = self.bind_restore_boundary(adapter)

        with self.assertRaisesRegex(
            (affect_persistence.PersistenceRecordError, TypeError, ValueError),
            r"(?i)(provider|evidence|envelope|frontier|type|read)",
        ):
            self.restore_host(boundary, checkpoint, row, token)

        self.assertEqual(adapter.read_calls, 1)


if __name__ == "__main__":
    unittest.main()
