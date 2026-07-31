from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_portable_project_bootstrap.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


def exact(value: str) -> dict[str, object]:
    return {"precision": "EXACT", "value": value, "lower": None, "upper": None}


def unknown() -> dict[str, object]:
    return {"precision": "UNKNOWN", "value": None, "lower": None, "upper": None}


def sample_receipt() -> dict[str, object]:
    release_commit = "1" * 40
    files = [
        {
            "path": path,
            "mode": "100644",
            "size": 10 + index,
            "sha256": f"{index + 1:064x}"[-64:],
            "git_blob_sha": f"{index + 1:040x}"[-40:],
            "release_commit": release_commit,
        }
        for index, path in enumerate(sorted(validator.PATHS))
    ]
    return {
        "schema_id": "VERA_PORTABLE_BOOTSTRAP_RECEIPT_V1",
        "receipt_id": str(uuid.uuid4()),
        "request": {
            "request_key": "a" * 64,
            "input_digest": "b" * 64,
            "immutable_inputs": {
                "command_version": "V1",
                "release_id": "VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1",
                "manifest_sha256": "c" * 64,
                "project_template_id": "urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1",
                "target_fingerprint": "d" * 64,
                "canonical_request": "VERA::INITIALIZE::PORTABLE_PROJECT_V1",
                "source_repository": "thebrazenbeard/vera",
                "source_base_commit": validator.BASE_SHA,
                "requested_mode": "CREATE_OR_VERIFY",
            },
        },
        "project_scope": {
            "project_template_id": "urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1",
            "project_instance_id": "0198f4d2-8a6d-7b10-8abc-1234567890ab",
            "branch_id": str(uuid.uuid4()),
            "conversation_scope_id": None,
            "session_id": None,
            "checkpoint_id": None,
            "record_scope_id": "e" * 64,
            "binding_state": "DURABLY_BOUND",
        },
        "source_bindings": {
            "base_source_commit": validator.BASE_SHA,
            "portable_release_commit": release_commit,
            "path_set_sha256": "f" * 64,
            "package_sha256": "1" * 64,
            "files": files,
        },
        "authority_evidence": [
            {
                "verifier_role": "workstream/project-architecture",
                "lease_id": "LEASE-TEST",
                "repository": "thebrazenbeard/vera",
                "branch": "feature/portable-project-bootstrap-v1",
                "base_sha": validator.BASE_SHA,
                "observed_at": "2026-07-31T16:00:00Z",
                "operation": "CREATE_OR_VERIFY",
            }
        ],
        "temporal_evidence": {
            "event_time": unknown(),
            "state_time": exact("2026-07-31T16:00:00Z"),
            "effective_time": {
                "precision": "BOUNDED",
                "value": None,
                "lower": "2026-07-31T16:00:00Z",
                "upper": "2026-07-31T16:00:02Z",
            },
            "observed_time": exact("2026-07-31T16:00:03Z"),
            "record_time": exact("2026-07-31T16:00:04Z"),
            "retrieval_time": exact("2026-07-31T16:00:05Z"),
        },
        "durable_readback": {
            "confirmed": True,
            "request_key": "a" * 64,
            "input_digest": "b" * 64,
            "project_instance_id": "0198f4d2-8a6d-7b10-8abc-1234567890ab",
            "binding_event_id": str(uuid.uuid4()),
            "binding_record_time": "2026-07-31T16:00:04Z",
            "retrieval_time": "2026-07-31T16:00:05Z",
            "readback_nonce": str(uuid.uuid4()),
            "source_evidence_digest": "2" * 64,
            "authority_evidence_digest": "3" * 64,
        },
        "effects": [
            {
                "effect_class": "GITHUB_WRITE",
                "target": "thebrazenbeard/vera@feature/portable-project-bootstrap-v1",
                "confirmed": True,
                "confirmation_locator": "commit:1111111111111111111111111111111111111111",
                "authority_reference": "LEASE-TEST",
                "observed_at": "2026-07-31T16:00:05Z",
            }
        ],
        "limitations": ["Disposable validation is not production application."],
        "result": "INITIALIZED",
        "merge_authorized": False,
        "production_supabase_authorized": False,
        "canonical_memory_write_authorized": False,
        "project_file_replacement_authorized": False,
    }


class PortableBootstrapTests(unittest.TestCase):
    def test_full_package(self) -> None:
        self.assertIsNone(validator.validate(ROOT))

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"a": 1, "a": 2}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_non_finite_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"a": NaN}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_contract_schema_rejects_caller_supplied_identity(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = copy.deepcopy(contract)
        hostile["identity_contract"]["project_instance_id"]["caller_supplied"] = True
        with self.assertRaises(validator.ValidationError):
            validator.validate_schema_instance(schema, hostile, "hostile contract")

    def test_contract_schema_rejects_shallow_replacement(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = copy.deepcopy(contract)
        hostile["temporal_contract"] = {"precisions": ["EXACT"]}
        with self.assertRaises(validator.ValidationError):
            validator.validate_schema_instance(schema, hostile, "hostile contract")

    def test_receipt_valid(self) -> None:
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        validator.validate_receipt(sample_receipt(), schema)

    def test_receipt_unknown_field_rejected(self) -> None:
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = sample_receipt()
        hostile["self_authorized"] = True
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(hostile, schema)

    def test_receipt_pending_cannot_initialize(self) -> None:
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = sample_receipt()
        hostile["project_scope"]["binding_state"] = "BINDING_PENDING"
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(hostile, schema)

    def test_receipt_readback_must_match_request(self) -> None:
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = sample_receipt()
        hostile["durable_readback"]["request_key"] = "9" * 64
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(hostile, schema)

    def test_confirmed_effect_requires_independent_locator(self) -> None:
        schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")
        hostile = sample_receipt()
        hostile["effects"][0]["confirmation_locator"] = None
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(hostile, schema)

    def test_no_named_chat_dependency(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        prohibited = set(contract["prohibited_dependencies"])
        self.assertTrue(
            {"chat_title", "historical_chat_id", "named_chat_route", "fixed_conversation_alias", "chatgpt-project-current"}.issubset(prohibited)
        )

    def test_basic_memory_optional(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        self.assertIn("BASIC_MEMORY", contract["capability_policy"]["optional_nonblocking"])

    def test_project_architect_and_coordinator_roles(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        self.assertTrue(contract["authority_contract"]["project_architect_is_implementation_owner"])
        self.assertTrue(contract["authority_contract"]["coordinator_manages_team_routing"])
        self.assertFalse(contract["authority_contract"]["coordinator_can_issue_or_expand_lease"])

    def test_exact_release_binding_in_temporary_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / ".base").write_text("base\n", encoding="ascii")
            subprocess.run(["git", "add", ".base"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "package"], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            previous = validator.BASE_SHA
            validator.BASE_SHA = base
            try:
                attestation = validator.external_release_attestation(repo, head)
            finally:
                validator.BASE_SHA = previous
            self.assertEqual(len(attestation["files"]), 12)
            self.assertEqual(attestation["release_commit"], head)


if __name__ == "__main__":
    unittest.main()
