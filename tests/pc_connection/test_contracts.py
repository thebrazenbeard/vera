from __future__ import annotations

import copy
import unittest

from pc_connection.contracts import (
    ArtifactAuthorization,
    ArtifactManifest,
    ArtifactSource,
    AuthorizationEnvelope,
    ContractError,
    DestinationPolicy,
    JobEnvelope,
    MAX_ARTIFACT_BYTES,
    RetentionPolicy,
)


def valid_authorization() -> dict:
    return {
        "schema_version": "VERA_PCCC_AUTHORIZATION_V1",
        "envelope_id": "00000000-0000-7000-8000-000000000011",
        "job_id": "00000000-0000-7000-8000-000000000012",
        "issuer_id": "issuer/pccc-owner",
        "subject_user_id": "user/patrick-a-sims",
        "host_id": "00000000-0000-7000-8000-000000000003",
        "operation": "PING",
        "operation_version": 1,
        "parameters_digest": "0" * 64,
        "artifact_manifest_digest": "0" * 64,
        "read_roots_digest": "1" * 64,
        "write_root_id": "NONE",
        "authorization_id": "00000000-0000-7000-8000-000000000013",
        "authorization_revision": 1,
        "issued_at": "2026-08-01T20:00:00.000000Z",
        "not_before": "2026-08-01T20:00:00.000000Z",
        "expires_at": "2026-08-01T20:15:00.000000Z",
        "nonce": "00000000-0000-7000-8000-000000000014",
        "max_attempts": 1,
        "lease_ttl_seconds": 90,
        "protocol_min_version": "1.0.0",
        "agent_min_version": "0.1.0",
        "issuer_revocation_epoch": 0,
        "host_revocation_epoch": 0,
    }


def valid_job() -> dict:
    return {
        "schema_version": "VERA_PCCC_JOB_V1",
        "envelope_id": "00000000-0000-7000-8000-000000000001",
        "request_id": "00000000-0000-7000-8000-000000000002",
        "idempotency_key": "example-submit-001",
        "project_id": "vera-reciprocal-agency-environment",
        "requester_principal_id": "user/patrick-a-sims",
        "requester_principal_type": "USER",
        "host_id": "00000000-0000-7000-8000-000000000003",
        "operation_id": "PING",
        "operation_version": 1,
        "parameters_digest": "0" * 64,
        "artifact_manifest_digest": "0" * 64,
        "read_roots_digest": "1" * 64,
        "write_root_id": "NONE",
        "authorization_id": "00000000-0000-7000-8000-000000000004",
        "authorization_revision": 1,
        "not_before": "2026-08-01T20:00:00.000000Z",
        "expires_at": "2026-08-01T20:15:00.000000Z",
        "timeout_seconds": 30,
        "max_attempts": 1,
        "lease_ttl_seconds": 90,
        "retry_class": "PURE_READ",
        "protocol_min_version": "1.0.0",
        "agent_min_version": "0.1.0",
        "required_local_policy_digest": "2" * 64,
        "required_capability_digest": "3" * 64,
        "issuer_revocation_epoch": 0,
        "host_revocation_epoch": 0,
        "nonce": "00000000-0000-7000-8000-000000000005",
        "trace_correlation_id": (
            "00000000-0000-7000-8000-000000000006"
        ),
    }


def valid_artifact() -> dict:
    digest = "a" * 64
    value = {
        "schema_version": "VERA_PCCC_ARTIFACT_MANIFEST_V1",
        "manifest_id": "00000000-0000-7000-8000-000000000021",
        "manifest_digest_algorithm": "SHA-256",
        "manifest_sha256": "0" * 64,
        "artifact_id": "00000000-0000-7000-8000-000000000022",
        "content_id": f"urn:sha256:{digest}:1024",
        "logical_name": "evidence",
        "declared_filename": "evidence.json",
        "byte_length": 1024,
        "sha256": digest,
        "content_class": "TEST_EVIDENCE",
        "privacy_class": "PROJECT",
        "execution_class": "NON_EXECUTABLE",
        "archive_class": "NOT_ARCHIVE",
        "media_type_declared": "application/json",
        "source": {
            "store": "LOCAL_ONLY",
            "locator": r"VERA_ROOT\evidence.json",
            "immutable_locator_version": "sha256:a",
        },
        "destination_policy": {
            "store": "LOCAL_ONLY",
            "backend_profile_id": "LOCAL_ONLY",
            "backend_profile_digest": "b" * 64,
            "remote_transfer_enabled": False,
            "relative_path": r"artifacts\store\evidence.json",
        },
        "authorization": {
            "authorization_id": (
                "00000000-0000-7000-8000-000000000023"
            ),
            "revision": 1,
            "allowed_host_id": (
                "00000000-0000-7000-8000-000000000003"
            ),
            "allowed_job_id": (
                "00000000-0000-7000-8000-000000000012"
            ),
            "allowed_operations": ["HASH_FILE"],
            "max_bytes": 1024,
            "issued_at": "2026-08-01T20:00:00.000000Z",
            "expires_at": "2026-08-01T20:15:00.000000Z",
        },
        "retention": {
            "class": "PROJECT",
            "retain_until": "2027-08-01T20:00:00.000000Z",
        },
        "created_at": "2026-08-01T20:00:00.000000Z",
    }
    provisional = ArtifactManifest(
        schema_version=value["schema_version"],
        manifest_id=value["manifest_id"],
        manifest_digest_algorithm=value["manifest_digest_algorithm"],
        manifest_sha256=value["manifest_sha256"],
        artifact_id=value["artifact_id"],
        content_id=value["content_id"],
        logical_name=value["logical_name"],
        declared_filename=value["declared_filename"],
        byte_length=value["byte_length"],
        sha256=value["sha256"],
        content_class=value["content_class"],
        privacy_class=value["privacy_class"],
        execution_class=value["execution_class"],
        archive_class=value["archive_class"],
        media_type_declared=value["media_type_declared"],
        source=ArtifactSource(**value["source"]),
        destination_policy=DestinationPolicy(
            **value["destination_policy"]
        ),
        authorization=ArtifactAuthorization(
            authorization_id=value["authorization"]["authorization_id"],
            revision=value["authorization"]["revision"],
            allowed_host_id=value["authorization"]["allowed_host_id"],
            allowed_job_id=value["authorization"]["allowed_job_id"],
            allowed_operations=tuple(
                value["authorization"]["allowed_operations"]
            ),
            max_bytes=value["authorization"]["max_bytes"],
            issued_at=value["authorization"]["issued_at"],
            expires_at=value["authorization"]["expires_at"],
        ),
        retention=RetentionPolicy(
            retention_class=value["retention"]["class"],
            retain_until=value["retention"]["retain_until"],
        ),
        created_at=value["created_at"],
    )
    value["manifest_sha256"] = (
        provisional.computed_manifest_sha256()
    )
    return value


class AuthorizationTests(unittest.TestCase):
    def test_known_vector(self) -> None:
        envelope = AuthorizationEnvelope.from_mapping(
            valid_authorization()
        )
        self.assertEqual(
            envelope.digest(),
            "7c68c7d618be45b23149b04b4713447c"
            "8e190ef186c30d1cfad33b7c7774133c",
        )

    def test_signature_and_key_fields_are_unknown(self) -> None:
        for field in (
            "issuer_key_id",
            "signature",
            "device_proof",
        ):
            value = valid_authorization()
            value[field] = "forbidden"
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    ContractError,
                    "unknown fields",
                ):
                    AuthorizationEnvelope.from_mapping(value)

    def test_uuidv4_and_second_precision_are_rejected(self) -> None:
        value = valid_authorization()
        value["job_id"] = (
            "22222222-2222-4222-8222-222222222222"
        )
        with self.assertRaisesRegex(ContractError, "UUIDv7"):
            AuthorizationEnvelope.from_mapping(value)
        value = valid_authorization()
        value["issued_at"] = "2026-08-01T20:00:00Z"
        with self.assertRaisesRegex(
            ContractError,
            "six fractional",
        ):
            AuthorizationEnvelope.from_mapping(value)

    def test_enabled_operation_requires_no_write_scope(self) -> None:
        value = valid_authorization()
        value["write_root_id"] = "PCCC_WRITE_ROOT"
        with self.assertRaisesRegex(ContractError, "write_root_id NONE"):
            AuthorizationEnvelope.from_mapping(value)

    def test_remote_operations_are_recognized_but_denied(self) -> None:
        for operation in ("UPLOAD_ARTIFACT", "DOWNLOAD_ARTIFACT"):
            value = valid_authorization()
            value["operation"] = operation
            with self.subTest(operation=operation):
                with self.assertRaisesRegex(
                    ContractError,
                    "EXEC_OPERATION_DENIED",
                ):
                    AuthorizationEnvelope.from_mapping(value)


class JobTests(unittest.TestCase):
    def test_known_protocol_vector(self) -> None:
        self.assertEqual(
            JobEnvelope.from_mapping(valid_job()).digest(),
            "759fff9b5be4d3e44de761e1a5cacb9c"
            "41f6bb860debe5aff2e15944af5b0c5f",
        )

    def test_changed_field_changes_digest(self) -> None:
        first = JobEnvelope.from_mapping(valid_job()).digest()
        value = valid_job()
        value["host_revocation_epoch"] = 1
        self.assertNotEqual(
            first,
            JobEnvelope.from_mapping(value).digest(),
        )

    def test_direct_command_execution_is_rejected(self) -> None:
        value = valid_job()
        value["operation_id"] = "RUN_COMMAND"
        with self.assertRaisesRegex(ContractError, "recognized"):
            JobEnvelope.from_mapping(value)

    def test_job_remote_transfer_is_denied(self) -> None:
        value = valid_job()
        value["operation_id"] = "UPLOAD_ARTIFACT"
        with self.assertRaisesRegex(
            ContractError,
            "EXEC_OPERATION_DENIED",
        ):
            JobEnvelope.from_mapping(value)


class ArtifactTests(unittest.TestCase):
    def test_valid_local_manifest(self) -> None:
        manifest = ArtifactManifest.from_mapping(valid_artifact())
        self.assertEqual(
            manifest.manifest_sha256,
            manifest.computed_manifest_sha256(),
        )

    def test_self_digest_mismatch_is_rejected(self) -> None:
        value = valid_artifact()
        value["manifest_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            ContractError,
            "manifest_sha256",
        ):
            ArtifactManifest.from_mapping(value)

    def test_remote_backend_and_operations_are_disabled(self) -> None:
        value = valid_artifact()
        value["destination_policy"]["store"] = "SUPABASE_STORAGE"
        with self.assertRaisesRegex(ContractError, "LOCAL_ONLY"):
            ArtifactManifest.from_mapping(value)
        value = valid_artifact()
        value["authorization"]["allowed_operations"] = [
            "UPLOAD_ARTIFACT"
        ]
        with self.assertRaisesRegex(
            ContractError,
            "EXEC_OPERATION_DENIED",
        ):
            ArtifactManifest.from_mapping(copy.deepcopy(value))

    def test_executable_and_oversize_are_rejected(self) -> None:
        value = valid_artifact()
        value["execution_class"] = "EXECUTABLE_UNTRUSTED"
        with self.assertRaisesRegex(ContractError, "executable"):
            ArtifactManifest.from_mapping(value)
        value = valid_artifact()
        value["byte_length"] = MAX_ARTIFACT_BYTES + 1
        with self.assertRaisesRegex(ContractError, "byte_length"):
            ArtifactManifest.from_mapping(value)


if __name__ == "__main__":
    unittest.main()
