import inspect
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_cycle import VeraAffectiveCycle
from runtime_cohesion.affect_host import VeraAffectiveRuntimeHost
from runtime_cohesion.affect_persistence import (
    PersistenceRecordError,
    build_affective_resume_token,
    checkpoint_to_state_row,
    restore_host_from_state_row,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


class TrustedResumeFrontierVerifierDouble:
    """Test double for a separately retained provider/read trust boundary.

    The verifier owns a snapshot captured before the candidate restore row is
    presented. A token freshly projected from the candidate row cannot change
    that retained frontier.
    """

    verifier_id = "trusted-affective-provider-read-test-double"
    provider_class = "SUPABASE_POSTGRES"
    provider_project_id = "klmbpaigzeguvnpccqzz"

    def __init__(self, trusted_row):
        self.calls = 0
        self._trusted = {
            "runtime_instance_id": trusted_row["runtime_instance_id"],
            "state_version": trusted_row["state_version"],
            "checkpoint_sha256": trusted_row["checkpoint_sha256"],
            "source_commit": trusted_row["source_commit"],
        }

    def verify(self, candidate_row, *, expected_resume_token):
        self.calls += 1
        candidate = {
            "runtime_instance_id": candidate_row.get("runtime_instance_id"),
            "state_version": candidate_row.get("state_version"),
            "checkpoint_sha256": candidate_row.get("checkpoint_sha256"),
            "source_commit": candidate_row.get("source_commit"),
        }
        if candidate != self._trusted:
            return None

        token = dict(expected_resume_token)
        expected_token = {
            "schema": "VERA_AFFECTIVE_RUNTIME_RESUME_TOKEN_V1",
            **self._trusted,
        }
        if token != expected_token:
            return None

        evidence_core = {
            "verifier_id": self.verifier_id,
            "provider_class": self.provider_class,
            "provider_project_id": self.provider_project_id,
            "runtime_instance_id": self._trusted["runtime_instance_id"],
            "state_version": self._trusted["state_version"],
            "checkpoint_sha256": self._trusted["checkpoint_sha256"],
            "source_commit": self._trusted["source_commit"],
        }
        canonical = json.dumps(
            evidence_core,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return {
            **evidence_core,
            "evidence_id": (
                f"provider-read:{self._trusted['runtime_instance_id']}:"
                f"{self._trusted['state_version']}"
            ),
            "evidence_digest": __import__("hashlib").sha256(
                canonical.encode("utf-8")
            ).hexdigest(),
        }


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

    def test_live_restore_surfaces_require_independent_frontier_verifier(self):
        self.assertIn(
            "resume_frontier_verifier",
            inspect.signature(VeraAffectiveCycle.restore_from_state_row).parameters,
        )
        self.assertIn(
            "resume_frontier_verifier",
            inspect.signature(restore_host_from_state_row).parameters,
        )

    def test_row_derived_token_alone_is_not_live_frontier_authentication(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|verif|attest|trusted|resume)",
        ):
            restore_host_from_state_row(
                contract_text,
                binding,
                row,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=token,
                resume_frontier_verifier=None,
            )

    def test_lower_restore_positive_crosses_separately_retained_provider_frontier(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()
        verifier = TrustedResumeFrontierVerifierDouble(row)

        host = restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
            resume_frontier_verifier=verifier,
        )

        self.assertEqual(verifier.calls, 1)
        self.assertEqual(
            host.runtime.runtime_instance_id,
            row["runtime_instance_id"],
        )

    def test_cycle_restore_uses_the_same_independent_frontier_boundary(self):
        checkpoint, row, token = self.make_row()
        contract_text, binding = self.contract_text_and_binding()
        verifier = TrustedResumeFrontierVerifierDouble(row)

        cycle = VeraAffectiveCycle.restore_from_state_row(
            contract_text,
            binding,
            row,
            host_scope="TEST_HOST",
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
            expected_resume_token=token,
            resume_frontier_verifier=verifier,
        )

        self.assertEqual(verifier.calls, 1)
        self.assertEqual(cycle._next_state_version, row["state_version"] + 1)

    def test_fresh_candidate_derived_token_cannot_rewrite_trusted_provider_frontier(self):
        checkpoint, trusted_row, _trusted_token = self.make_row(state_version=7)
        contract_text, binding = self.contract_text_and_binding()
        verifier = TrustedResumeFrontierVerifierDouble(trusted_row)

        replayed = dict(trusted_row)
        replayed["state_version"] = 8
        candidate_derived_token = build_affective_resume_token(replayed)

        # The mutable candidate row and its deterministic token now agree with
        # each other. Only the separately retained provider frontier disagrees.
        self.assertEqual(
            candidate_derived_token["state_version"],
            replayed["state_version"],
        )
        self.assertEqual(
            candidate_derived_token["checkpoint_sha256"],
            replayed["checkpoint_sha256"],
        )

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|verif|attest|trusted|resume)",
        ):
            restore_host_from_state_row(
                contract_text,
                binding,
                replayed,
                expected_host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=candidate_derived_token,
                resume_frontier_verifier=verifier,
            )

        self.assertEqual(verifier.calls, 1)

    def test_cycle_restore_rejects_candidate_row_and_token_that_only_vouch_for_each_other(self):
        checkpoint, trusted_row, _trusted_token = self.make_row(state_version=7)
        contract_text, binding = self.contract_text_and_binding()
        verifier = TrustedResumeFrontierVerifierDouble(trusted_row)

        replayed = dict(trusted_row)
        replayed["state_version"] = 8
        candidate_derived_token = build_affective_resume_token(replayed)

        with self.assertRaisesRegex(
            (PersistenceRecordError, ValueError),
            r"(?i)(frontier|provider|verif|attest|trusted|resume)",
        ):
            VeraAffectiveCycle.restore_from_state_row(
                contract_text,
                binding,
                replayed,
                host_scope="TEST_HOST",
                expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
                expected_resume_token=candidate_derived_token,
                resume_frontier_verifier=verifier,
            )

        self.assertEqual(verifier.calls, 1)


if __name__ == "__main__":
    unittest.main()
