import inspect
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
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

PROVIDER_PROJECT_ID = "klmbpaigzeguvnpccqzz"
PROVIDER_TABLE = "public.vera_affective_runtime_state_v1"
FRONTIER_SCOPE = "VERA_AFFECTIVE_RUNTIME_PROVIDER_FRONTIER_V1"


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
        row = checkpoint_to_state_row(
            checkpoint,
            host_scope="TEST_HOST",
            state_version=state_version,
        )
        return checkpoint, row, build_affective_resume_token(row)

    @staticmethod
    def provider_read_evidence(row):
        """Model the typed result of an independently executed provider read.

        Production trust belongs to the runtime-owned provider adapter/read
        boundary. The candidate row does not select a verifier and this evidence
        does not grant semantic authority; it only binds an observed provider
        frontier.
        """
        return ProviderEvidenceEnvelope(
            provider="supabase",
            locator=(
                f"supabase:{PROVIDER_PROJECT_ID}/{PROVIDER_TABLE}/"
                f"{row['runtime_instance_id']}"
            ),
            revision=f"state-version:{row['state_version']}",
            observed_at=row["updated_at"],
            evidence_class="persisted_provider_record",
            referent=row["runtime_instance_id"],
            scope=FRONTIER_SCOPE,
            privacy_class="GOVERNED",
            currentness_basis="fresh exact provider readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            content_digest=row["checkpoint_sha256"],
            metadata={
                "provider_project_id": PROVIDER_PROJECT_ID,
                "provider_table": PROVIDER_TABLE,
                "runtime_instance_id": row["runtime_instance_id"],
                "host_scope": row["host_scope"],
                "state_version": row["state_version"],
                "checkpoint_sha256": row["checkpoint_sha256"],
                "source_commit": row["source_commit"],
            },
        )

    def test_live_restore_surfaces_require_typed_provider_read_evidence(self):
        self.assertIn(
            "resume_frontier_evidence",
            inspect.signature(VeraAffectiveCycle.restore_from_state_row).parameters,
        )
        self.assertIn(
            "resume_frontier_evidence",
            inspect.signature(restore_host_from_state_row).parameters,
        )

    def test_row_derived_token_alone_is_not_live_frontier_authentication(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|evidence|current|readback|resume)",
        ):
            restore_host_from_state_row(
                contract_text,
                binding,
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
                resume_frontier_evidence=None,
            )

    def test_lower_restore_accepts_exact_typed_current_provider_readback(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()
        evidence = self.provider_read_evidence(row)

        host = restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
            resume_frontier_evidence=evidence,
        )

        self.assertEqual(host.runtime.runtime_instance_id, row["runtime_instance_id"])

    def test_cycle_restore_accepts_the_same_exact_typed_provider_readback(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()
        evidence = self.provider_read_evidence(row)

        cycle = VeraAffectiveCycle.restore_from_state_row(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
            resume_frontier_evidence=evidence,
        )

        self.assertEqual(cycle._next_state_version, row["state_version"] + 1)

    def test_candidate_row_and_freshly_derived_token_cannot_rewrite_provider_readback(self):
        checkpoint, trusted_row, _trusted_token = self.make_row(state_version=7)
        contract_text, binding = self.contract_text_and_binding()
        evidence = self.provider_read_evidence(trusted_row)

        replayed = dict(trusted_row)
        replayed["state_version"] = 8
        candidate_token = build_affective_resume_token(replayed)

        # Candidate row and deterministic token agree. The independent typed
        # provider observation still binds the actually observed version 7.
        self.assertEqual(candidate_token["state_version"], replayed["state_version"])
        self.assertEqual(
            candidate_token["checkpoint_sha256"],
            replayed["checkpoint_sha256"],
        )
        self.assertEqual(evidence.metadata["state_version"], 7)

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|evidence|current|revision|version|resume)",
        ):
            restore_host_from_state_row(
                contract_text,
                binding,
                replayed,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=candidate_token,
                resume_frontier_evidence=evidence,
            )

    def test_cycle_restore_rejects_candidate_row_and_token_that_only_vouch_for_each_other(self):
        checkpoint, trusted_row, _trusted_token = self.make_row(state_version=7)
        contract_text, binding = self.contract_text_and_binding()
        evidence = self.provider_read_evidence(trusted_row)

        replayed = dict(trusted_row)
        replayed["state_version"] = 8
        candidate_token = build_affective_resume_token(replayed)

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|evidence|current|revision|version|resume)",
        ):
            VeraAffectiveCycle.restore_from_state_row(
                contract_text,
                binding,
                replayed,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=candidate_token,
                resume_frontier_evidence=evidence,
            )

    def test_duck_typed_provider_read_lookalike_is_not_equivalent_to_provider_evidence(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()
        real = self.provider_read_evidence(row)
        lookalike = SimpleNamespace(**real.__dict__)

        with self.assertRaisesRegex(
            (PersistenceRecordError, TypeError, ValueError),
            r"(?i)(provider|evidence|envelope|frontier|type|readback)",
        ):
            restore_host_from_state_row(
                contract_text,
                binding,
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
                resume_frontier_evidence=lookalike,
            )

    def test_noncurrent_or_conflicted_provider_evidence_cannot_establish_live_frontier(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()

        cases = (
            ("superseded", {"supersession_state": "SUPERSEDED"}),
            ("conflict", {"conflict_state": "CONFLICT"}),
        )
        for label, overrides in cases:
            with self.subTest(case=label):
                kwargs = dict(
                    provider="supabase",
                    locator=(
                        f"supabase:{PROVIDER_PROJECT_ID}/{PROVIDER_TABLE}/"
                        f"{row['runtime_instance_id']}"
                    ),
                    revision=f"state-version:{row['state_version']}",
                    observed_at=row["updated_at"],
                    evidence_class="persisted_provider_record",
                    referent=row["runtime_instance_id"],
                    scope=FRONTIER_SCOPE,
                    privacy_class="GOVERNED",
                    currentness_basis="fresh exact provider readback",
                    supersession_state="CURRENT_OBSERVATION",
                    conflict_state="NONE",
                    content_digest=row["checkpoint_sha256"],
                    metadata={
                        "provider_project_id": PROVIDER_PROJECT_ID,
                        "provider_table": PROVIDER_TABLE,
                        "runtime_instance_id": row["runtime_instance_id"],
                        "host_scope": row["host_scope"],
                        "state_version": row["state_version"],
                        "checkpoint_sha256": row["checkpoint_sha256"],
                        "source_commit": row["source_commit"],
                    },
                )
                kwargs.update(overrides)
                evidence = ProviderEvidenceEnvelope(**kwargs)

                with self.assertRaisesRegex(
                    (PersistenceRecordError, ValueError),
                    r"(?i)(current|supersed|conflict|provider|frontier|evidence)",
                ):
                    restore_host_from_state_row(
                        contract_text,
                        binding,
                        row,
                        expected_host_scope="TEST_HOST",
                        expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                        expected_resume_token=token,
                        resume_frontier_evidence=evidence,
                    )


if __name__ == "__main__":
    unittest.main()
