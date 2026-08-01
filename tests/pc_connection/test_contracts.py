from __future__ import annotations

import unittest

from pc_connection.contracts import (
    ArtifactManifest,
    AuthorizationEnvelope,
    CHUNK_SIZE_BYTES,
    ContractError,
)


def valid_authorization() -> dict:
    return {
        "schema_version": "VERA_PCCC_AUTHORIZATION_ENVELOPE_V1",
        "envelope_id": "11111111-1111-4111-8111-111111111111",
        "job_id": "22222222-2222-4222-8222-222222222222",
        "issuer_id": "issuer:pccc",
        "issuer_key_id": "key:issuer:1",
        "subject_user_id": "user:patrick",
        "host_id": "host:windows:1",
        "operation": "HASH_FILE",
        "operation_version": "1.0.0",
        "parameters_digest": "1" * 64,
        "artifact_manifest_digest": "2" * 64,
        "read_roots_digest": "3" * 64,
        "write_root_id": "PCCC_WRITE_ROOT_V1",
        "authorization_id": "33333333-3333-4333-8333-333333333333",
        "authorization_revision": 1,
        "issued_at": "2026-08-01T20:00:00Z",
        "not_before": "2026-08-01T20:00:00Z",
        "expires_at": "2026-08-01T20:15:00Z",
        "nonce": "nonce-0123456789",
        "max_attempts": 3,
        "lease_ttl_seconds": 90,
        "protocol_min_version": "1.0.0",
        "agent_min_version": "0.1.0",
        "issuer_revocation_epoch": 0,
        "host_revocation_epoch": 0,
    }


def valid_artifact() -> dict:
    length = CHUNK_SIZE_BYTES + 1
    digest = "a" * 64
    return {
        "schema_version": "VERA_PCCC_ARTIFACT_MANIFEST_V1",
        "manifest_id": "44444444-4444-4444-8444-444444444444",
        "artifact_id": "55555555-5555-4555-8555-555555555555",
        "filename": "evidence.json",
        "byte_length": length,
        "sha256": digest,
        "content_id": f"sha256:{digest}:{length}",
        "media_type": "application/json",
        "content_class": "REPORT",
        "privacy": "PROJECT",
        "source_store": "LOCAL_ONLY",
        "target_store": "SUPABASE_STORAGE",
        "created_at": "2026-08-01T20:00:00Z",
        "chunk_size_bytes": CHUNK_SIZE_BYTES,
        "chunk_count": 2,
        "executable": False,
        "archive": False,
        "retention_class": "PROJECT",
    }


class AuthorizationEnvelopeTests(unittest.TestCase):
    def test_valid_authorization_has_stable_digest(self) -> None:
        envelope = AuthorizationEnvelope.from_mapping(valid_authorization())
        self.assertEqual(len(envelope.digest()), 64)
        self.assertEqual(envelope.digest(), envelope.digest())

    def test_unknown_field_is_rejected(self) -> None:
        value = valid_authorization()
        value["model_says_authorized"] = True
        with self.assertRaisesRegex(ContractError, "unknown fields"):
            AuthorizationEnvelope.from_mapping(value)

    def test_missing_field_is_rejected(self) -> None:
        value = valid_authorization()
        del value["host_id"]
        with self.assertRaisesRegex(ContractError, "missing fields"):
            AuthorizationEnvelope.from_mapping(value)

    def test_operation_outside_phase_one_is_rejected(self) -> None:
        value = valid_authorization()
        value["operation"] = "RUN_COMMAND"
        with self.assertRaisesRegex(ContractError, "phase-one"):
            AuthorizationEnvelope.from_mapping(value)

    def test_authorization_cannot_exceed_one_hour(self) -> None:
        value = valid_authorization()
        value["expires_at"] = "2026-08-01T21:00:01Z"
        with self.assertRaisesRegex(ContractError, "one hour"):
            AuthorizationEnvelope.from_mapping(value)

    def test_changed_meaning_field_changes_digest(self) -> None:
        first = AuthorizationEnvelope.from_mapping(valid_authorization())
        changed = valid_authorization()
        changed["host_revocation_epoch"] = 1
        second = AuthorizationEnvelope.from_mapping(changed)
        self.assertNotEqual(first.digest(), second.digest())

    def test_boolean_is_not_accepted_as_integer(self) -> None:
        value = valid_authorization()
        value["max_attempts"] = True
        with self.assertRaisesRegex(ContractError, "integer"):
            AuthorizationEnvelope.from_mapping(value)


class ArtifactManifestTests(unittest.TestCase):
    def test_valid_manifest_binds_bytes_and_chunks(self) -> None:
        manifest = ArtifactManifest.from_mapping(valid_artifact())
        self.assertEqual(manifest.chunk_count, 2)
        self.assertEqual(len(manifest.digest()), 64)

    def test_content_id_mismatch_is_rejected(self) -> None:
        value = valid_artifact()
        value["content_id"] = f"sha256:{'b' * 64}:{value['byte_length']}"
        with self.assertRaisesRegex(ContractError, "content_id"):
            ArtifactManifest.from_mapping(value)

    def test_path_separator_is_rejected(self) -> None:
        value = valid_artifact()
        value["filename"] = r"..\escape.json"
        with self.assertRaisesRegex(ContractError, "basename"):
            ArtifactManifest.from_mapping(value)

    def test_reserved_device_name_is_rejected(self) -> None:
        value = valid_artifact()
        value["filename"] = "CON.txt"
        with self.assertRaisesRegex(ContractError, "reserved"):
            ArtifactManifest.from_mapping(value)

    def test_executable_artifact_is_rejected(self) -> None:
        value = valid_artifact()
        value["executable"] = True
        with self.assertRaisesRegex(ContractError, "executable"):
            ArtifactManifest.from_mapping(value)

    def test_chunk_count_mismatch_is_rejected(self) -> None:
        value = valid_artifact()
        value["chunk_count"] = 1
        with self.assertRaisesRegex(ContractError, "chunk_count"):
            ArtifactManifest.from_mapping(value)

    def test_unknown_manifest_field_is_rejected(self) -> None:
        value = valid_artifact()
        value["provider_says_safe"] = True
        with self.assertRaisesRegex(ContractError, "unknown fields"):
            ArtifactManifest.from_mapping(value)


if __name__ == "__main__":
    unittest.main()
