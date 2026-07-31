from __future__ import annotations

import copy
import importlib.util
import json
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
    files = []
    for index, path in enumerate(sorted(validator.PATHS)):
        files.append({
            "path": path,
            "mode": "100644",
            "size": 100 + index,
            "sha256": "c" * 64 if path == validator.MANIFEST_PATH else f"{index + 1:064x}"[-64:],
            "git_blob_sha": f"{index + 1:040x}"[-40:],
            "release_commit": release_commit,
        })
    immutable = {
        "command_version": "V1",
        "release_id": validator.RELEASE_ID,
        "manifest_sha256": "c" * 64,
        "project_template_id": validator.TEMPLATE_ID,
        "target_fingerprint": "d" * 64,
        "canonical_request": validator.COMMAND,
        "source_repository": "thebrazenbeard/vera",
        "source_base_commit": validator.BASE_SHA,
        "requested_mode": "CREATE_OR_VERIFY",
    }
    authority = [{
        "verifier_role": "workstream/project-architecture",
        "lease_id": "LEASE-TEST",
        "repository": "thebrazenbeard/vera",
        "branch": "feature/portable-project-bootstrap-v1",
        "base_sha": validator.BASE_SHA,
        "observed_at": "2026-07-31T16:00:06Z",
        "operation": "VERIFY_BOOTSTRAP_BINDING",
    }]
    path_digest = validator.path_set_digest(validator.PATHS)
    package_digest = validator.package_digest(files)
    source = [{
        "release_commit": release_commit,
        "path_set_sha256": path_digest,
        "package_sha256": package_digest,
        "validation_run_id": "TEST-RUN-1",
        "observed_at": "2026-07-31T16:00:06Z",
    }]
    request_key = validator.request_key(immutable)
    input_digest = validator.input_digest(immutable)
    project_instance = "0198f4d2-8a6d-7b10-8abc-1234567890ab"
    durable = {
        "confirmed": True,
        "confirmation_id": str(uuid.uuid4()),
        "confirmation_record_time": "2026-07-31T16:00:08Z",
        "request_key": request_key,
        "input_digest": input_digest,
        "project_instance_id": project_instance,
        "binding_event_id": str(uuid.uuid4()),
        "binding_record_time": "2026-07-31T16:00:04Z",
        "retrieval_time": "2026-07-31T16:00:07Z",
        "readback_nonce": str(uuid.uuid4()),
        "immutable_inputs": copy.deepcopy(immutable),
        "authority_evidence": copy.deepcopy(authority),
        "source_evidence": copy.deepcopy(source),
        "authority_evidence_digest": validator.authority_evidence_digest(authority),
        "source_evidence_digest": validator.source_evidence_digest(source),
    }
    return {
        "schema_id": "VERA_PORTABLE_BOOTSTRAP_RECEIPT_V1",
        "receipt_id": str(uuid.uuid4()),
        "request": {"request_key": request_key, "input_digest": input_digest, "immutable_inputs": immutable},
        "project_scope": {
            "project_template_id": validator.TEMPLATE_ID,
            "project_instance_id": project_instance,
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
            "path_set_sha256": path_digest,
            "package_sha256": package_digest,
            "files": files,
        },
        "authority_evidence": authority,
        "source_evidence": source,
        "temporal_evidence": {
            "event_time": unknown(),
            "state_time": exact("2026-07-31T16:00:03Z"),
            "effective_time": {"precision": "BOUNDED", "value": None, "lower": "2026-07-31T16:00:00Z", "upper": "2026-07-31T16:00:02Z"},
            "observed_time": exact("2026-07-31T16:00:03Z"),
            "record_time": exact("2026-07-31T16:00:04Z"),
            "retrieval_time": exact("2026-07-31T16:00:07Z"),
        },
        "durable_readback": durable,
        "effects": [{
            "effect_class": "GITHUB_WRITE",
            "target": "thebrazenbeard/vera@feature/portable-project-bootstrap-v1",
            "confirmed": True,
            "confirmation_locator": "commit:" + release_commit,
            "authority_reference": "LEASE-TEST",
            "observed_at": "2026-07-31T16:00:07Z",
        }],
        "limitations": ["Disposable validation is not production application."],
        "result": "INITIALIZED",
        "merge_authorized": False,
        "production_supabase_authorized": False,
        "canonical_memory_write_authorized": False,
        "project_file_replacement_authorized": False,
    }


def registry_attestation(receipt: dict[str, object]) -> dict[str, object]:
    return copy.deepcopy(receipt["durable_readback"])


def release_attestation(receipt: dict[str, object]) -> dict[str, object]:
    bindings = receipt["source_bindings"]
    return {
        "release_commit": bindings["portable_release_commit"],
        "base_source_commit": bindings["base_source_commit"],
        "path_set_sha256": bindings["path_set_sha256"],
        "package_sha256": bindings["package_sha256"],
        "files": copy.deepcopy(bindings["files"]),
    }


class PortableBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = validator.load_json(ROOT / "schemas/vera_portable_project_bootstrap_v1.schema.json")

    def assert_receipt_fails(self, receipt: dict[str, object], *, registry: dict[str, object] | None = None, release: dict[str, object] | None = None) -> None:
        if registry is None:
            registry = registry_attestation(receipt)
        if release is None:
            release = release_attestation(receipt)
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(receipt, self.schema, registry_attestation=registry, external_release_attestation=release)

    def test_full_package(self) -> None:
        self.assertIsNone(validator.validate(ROOT))

    def test_known_digest_vectors(self) -> None:
        validator.validate_known_vectors()

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_non_finite_json_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"a":NaN}', encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.load_json(path)

    def test_receipt_valid_with_two_external_attestations(self) -> None:
        receipt = sample_receipt()
        validator.validate_receipt(receipt, self.schema, registry_attestation=registry_attestation(receipt), external_release_attestation=release_attestation(receipt))

    def test_durable_requires_independent_registry_attestation(self) -> None:
        receipt = sample_receipt()
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(receipt, self.schema, external_release_attestation=release_attestation(receipt))

    def test_initialized_requires_external_git_attestation(self) -> None:
        receipt = sample_receipt()
        with self.assertRaises(validator.ValidationError):
            validator.validate_receipt(receipt, self.schema, registry_attestation=registry_attestation(receipt))

    def test_pending_or_committed_cannot_initialize(self) -> None:
        for state in ("BINDING_PENDING", "BINDING_VERIFIED", "BINDING_COMMITTED"):
            with self.subTest(state=state):
                receipt = sample_receipt()
                receipt["project_scope"]["binding_state"] = state
                self.assert_receipt_fails(receipt)

    def test_identity_edge_mutation_matrix(self) -> None:
        cases = []
        def add(name, mutate): cases.append((name, mutate))
        add("PROJECT_TEMPLATE_ID", lambda r: r["project_scope"].__setitem__("project_template_id", "urn:wrong"))
        add("REQUEST_KEY", lambda r: r["request"].__setitem__("request_key", "9" * 64))
        add("INPUT_DIGEST", lambda r: r["request"].__setitem__("input_digest", "8" * 64))
        add("IMMUTABLE_REQUEST_FIELD", lambda r: r["request"]["immutable_inputs"].__setitem__("requested_mode", "DRY_RUN_VERIFY_ONLY"))
        add("DUPLICATE_PATH", lambda r: r["source_bindings"]["files"].__setitem__(1, copy.deepcopy(r["source_bindings"]["files"][0])))
        add("MISSING_PATH", lambda r: r["source_bindings"]["files"].pop())
        add("EXTRA_PATH", lambda r: r["source_bindings"]["files"].append({**copy.deepcopy(r["source_bindings"]["files"][0]), "path": "extra"}))
        add("FILE_RELEASE_COMMIT", lambda r: r["source_bindings"]["files"][0].__setitem__("release_commit", "2" * 40))
        add("FILE_SIZE", lambda r: r["source_bindings"]["files"][0].__setitem__("size", r["source_bindings"]["files"][0]["size"] + 1))
        add("FILE_SHA256", lambda r: r["source_bindings"]["files"][0].__setitem__("sha256", "7" * 64))
        add("FILE_GIT_BLOB", lambda r: r["source_bindings"]["files"][0].__setitem__("git_blob_sha", "6" * 40))
        add("PATH_SET_SHA256", lambda r: r["source_bindings"].__setitem__("path_set_sha256", "5" * 64))
        add("PACKAGE_SHA256", lambda r: r["source_bindings"].__setitem__("package_sha256", "4" * 64))
        add("MANIFEST_SHA256", lambda r: r["request"]["immutable_inputs"].__setitem__("manifest_sha256", "3" * 64))
        add("AUTHORITY_EVIDENCE", lambda r: r["authority_evidence"][0].__setitem__("operation", "DIFFERENT"))
        add("SOURCE_EVIDENCE", lambda r: r["source_evidence"][0].__setitem__("validation_run_id", "OTHER"))
        add("AUTHORITY_EVIDENCE_DIGEST", lambda r: r["durable_readback"].__setitem__("authority_evidence_digest", "2" * 64))
        add("SOURCE_EVIDENCE_DIGEST", lambda r: r["durable_readback"].__setitem__("source_evidence_digest", "1" * 64))
        for name, mutate in cases:
            with self.subTest(edge=name):
                receipt = sample_receipt()
                registry = registry_attestation(receipt)
                release = release_attestation(receipt)
                mutate(receipt)
                self.assert_receipt_fails(receipt, registry=registry, release=release)

    def test_registry_attestation_one_field_mismatch_fails(self) -> None:
        receipt = sample_receipt()
        registry = registry_attestation(receipt)
        registry["binding_event_id"] = str(uuid.uuid4())
        self.assert_receipt_fails(receipt, registry=registry, release=release_attestation(receipt))

    def test_external_attestation_one_file_mismatch_fails(self) -> None:
        receipt = sample_receipt()
        release = release_attestation(receipt)
        release["files"][0]["git_blob_sha"] = "f" * 40
        self.assert_receipt_fails(receipt, registry=registry_attestation(receipt), release=release)

    def test_contract_schema_rejects_commit_as_durable(self) -> None:
        contract = validator.load_json(ROOT / "architecture/bootstrap/VERA_PORTABLE_PROJECT_BOOTSTRAP_V1.json")
        hostile = copy.deepcopy(contract)
        hostile["durable_registry"]["candidate_pending_verified_or_committed_are_durable"] = True
        with self.assertRaises(validator.ValidationError):
            validator.validate_schema_instance(self.schema, hostile, "hostile contract")

    def test_exact_release_binding_in_temporary_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
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
