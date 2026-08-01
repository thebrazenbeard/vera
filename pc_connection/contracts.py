from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Any, Mapping
from uuid import UUID

from pc_connection import PHASE_ONE_OPERATIONS
from pc_connection.canonical import sha256_text_tuple

AUTHORIZATION_SCHEMA = "VERA_PCCC_AUTHORIZATION_ENVELOPE_V1"
ARTIFACT_SCHEMA = "VERA_PCCC_ARTIFACT_MANIFEST_V1"
AUTHORIZATION_DOMAIN = "VERA-PCCC-AUTHORIZATION-V1"
ARTIFACT_DOMAIN = "VERA-PCCC-ARTIFACT-MANIFEST-V1"
WRITE_ROOT_ID = "PCCC_WRITE_ROOT_V1"
CHUNK_SIZE_BYTES = 8 * 1024 * 1024

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")
_RFC3339_SECONDS_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
_SAFE_FILENAME = re.compile(r"^[^<>:\"/\\|?*\x00-\x1f]+$")

_RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class ContractError(ValueError):
    """Raised when a closed PCCC contract fails validation."""


def _closed_fields(
    value: Mapping[str, Any],
    required: tuple[str, ...],
    contract: str,
) -> None:
    actual = set(value)
    expected = set(required)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        raise ContractError(f"{contract} missing fields: {missing}")
    if unknown:
        raise ContractError(f"{contract} unknown fields: {unknown}")


def _uuid(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{field} must be a UUID string")
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise ContractError(f"{field} must be a canonical UUID") from exc


def _token(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise ContractError(f"{field} must be a bounded identifier")
    if "*" in value:
        raise ContractError(f"{field} may not contain a wildcard")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContractError(f"{field} must be lowercase SHA-256 hex")
    return value


def _positive_int(value: Any, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{field} must be an integer")
    if value < 1 or value > maximum:
        raise ContractError(f"{field} must be between 1 and {maximum}")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError(f"{field} must be a nonnegative integer")
    return value


def _utc_seconds(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not _RFC3339_SECONDS_UTC.fullmatch(value):
        raise ContractError(f"{field} must use UTC RFC3339 second precision")
    parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )
    return parsed


def _version(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise ContractError(f"{field} must be a semantic version")
    return value


def _canonical_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass(frozen=True)
class AuthorizationEnvelope:
    schema_version: str
    envelope_id: str
    job_id: str
    issuer_id: str
    issuer_key_id: str
    subject_user_id: str
    host_id: str
    operation: str
    operation_version: str
    parameters_digest: str
    artifact_manifest_digest: str
    read_roots_digest: str
    write_root_id: str
    authorization_id: str
    authorization_revision: int
    issued_at: str
    not_before: str
    expires_at: str
    nonce: str
    max_attempts: int
    lease_ttl_seconds: int
    protocol_min_version: str
    agent_min_version: str
    issuer_revocation_epoch: int
    host_revocation_epoch: int

    FIELDS = (
        "schema_version",
        "envelope_id",
        "job_id",
        "issuer_id",
        "issuer_key_id",
        "subject_user_id",
        "host_id",
        "operation",
        "operation_version",
        "parameters_digest",
        "artifact_manifest_digest",
        "read_roots_digest",
        "write_root_id",
        "authorization_id",
        "authorization_revision",
        "issued_at",
        "not_before",
        "expires_at",
        "nonce",
        "max_attempts",
        "lease_ttl_seconds",
        "protocol_min_version",
        "agent_min_version",
        "issuer_revocation_epoch",
        "host_revocation_epoch",
    )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AuthorizationEnvelope":
        if not isinstance(value, Mapping):
            raise ContractError("authorization envelope must be an object")
        _closed_fields(value, cls.FIELDS, "authorization envelope")
        envelope = cls(**{field: value[field] for field in cls.FIELDS})
        envelope.validate()
        return envelope

    def validate(self) -> None:
        if self.schema_version != AUTHORIZATION_SCHEMA:
            raise ContractError("unsupported authorization schema")
        _uuid(self.envelope_id, "envelope_id")
        _uuid(self.job_id, "job_id")
        _uuid(self.authorization_id, "authorization_id")
        for field in (
            "issuer_id",
            "issuer_key_id",
            "subject_user_id",
            "host_id",
            "nonce",
        ):
            _token(getattr(self, field), field)
        if len(self.nonce) < 16:
            raise ContractError("nonce must contain at least 16 characters")
        if self.operation not in PHASE_ONE_OPERATIONS:
            raise ContractError("operation is not in the phase-one allowlist")
        _version(self.operation_version, "operation_version")
        for field in (
            "parameters_digest",
            "artifact_manifest_digest",
            "read_roots_digest",
        ):
            _sha256(getattr(self, field), field)
        if self.write_root_id != WRITE_ROOT_ID:
            raise ContractError("write_root_id is not the authorized root alias")
        _positive_int(
            self.authorization_revision,
            "authorization_revision",
            2_147_483_647,
        )
        issued = _utc_seconds(self.issued_at, "issued_at")
        not_before = _utc_seconds(self.not_before, "not_before")
        expires = _utc_seconds(self.expires_at, "expires_at")
        if not issued <= not_before < expires:
            raise ContractError(
                "authorization timestamps must satisfy issued_at <= "
                "not_before < expires_at"
            )
        if (expires - issued).total_seconds() > 3600:
            raise ContractError("authorization lifetime exceeds one hour")
        _positive_int(self.max_attempts, "max_attempts", 5)
        _positive_int(self.lease_ttl_seconds, "lease_ttl_seconds", 300)
        if self.lease_ttl_seconds < 30:
            raise ContractError("lease_ttl_seconds must be at least 30")
        _version(self.protocol_min_version, "protocol_min_version")
        _version(self.agent_min_version, "agent_min_version")
        _nonnegative_int(
            self.issuer_revocation_epoch,
            "issuer_revocation_epoch",
        )
        _nonnegative_int(
            self.host_revocation_epoch,
            "host_revocation_epoch",
        )

    def signing_fields(self) -> tuple[str, ...]:
        return (
            AUTHORIZATION_DOMAIN,
            *(_canonical_scalar(getattr(self, field)) for field in self.FIELDS),
        )

    def digest(self) -> str:
        self.validate()
        return sha256_text_tuple(self.signing_fields())


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: str
    manifest_id: str
    artifact_id: str
    filename: str
    byte_length: int
    sha256: str
    content_id: str
    media_type: str
    content_class: str
    privacy: str
    source_store: str
    target_store: str
    created_at: str
    chunk_size_bytes: int
    chunk_count: int
    executable: bool
    archive: bool
    retention_class: str

    FIELDS = (
        "schema_version",
        "manifest_id",
        "artifact_id",
        "filename",
        "byte_length",
        "sha256",
        "content_id",
        "media_type",
        "content_class",
        "privacy",
        "source_store",
        "target_store",
        "created_at",
        "chunk_size_bytes",
        "chunk_count",
        "executable",
        "archive",
        "retention_class",
    )

    CONTENT_CLASSES = {
        "SOURCE",
        "LOG",
        "REPORT",
        "MODEL",
        "DATASET",
        "CHECKPOINT",
        "ARCHIVE",
        "OTHER",
    }
    PRIVACY_CLASSES = {"PUBLIC", "PROJECT", "PRIVATE"}
    STORES = {
        "LOCAL_ONLY",
        "SUPABASE_STORAGE",
        "GOOGLE_DRIVE",
        "GITHUB",
    }
    RETENTION_CLASSES = {
        "EPHEMERAL",
        "PROJECT",
        "RELEASE",
        "LEGAL_HOLD",
    }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ArtifactManifest":
        if not isinstance(value, Mapping):
            raise ContractError("artifact manifest must be an object")
        _closed_fields(value, cls.FIELDS, "artifact manifest")
        manifest = cls(**{field: value[field] for field in cls.FIELDS})
        manifest.validate()
        return manifest

    def validate(self) -> None:
        if self.schema_version != ARTIFACT_SCHEMA:
            raise ContractError("unsupported artifact manifest schema")
        _uuid(self.manifest_id, "manifest_id")
        _uuid(self.artifact_id, "artifact_id")
        if (
            not isinstance(self.filename, str)
            or not self.filename
            or self.filename in {".", ".."}
            or not _SAFE_FILENAME.fullmatch(self.filename)
            or self.filename[-1] in {" ", "."}
        ):
            raise ContractError("filename is not a safe Windows basename")
        stem = self.filename.split(".", 1)[0].upper()
        if stem in _RESERVED_WINDOWS_NAMES:
            raise ContractError("filename uses a reserved Windows device name")
        _nonnegative_int(self.byte_length, "byte_length")
        digest = _sha256(self.sha256, "sha256")
        expected_content_id = f"sha256:{digest}:{self.byte_length}"
        if self.content_id != expected_content_id:
            raise ContractError("content_id does not bind digest and byte length")
        if (
            not isinstance(self.media_type, str)
            or not self.media_type
            or len(self.media_type) > 127
            or "/" not in self.media_type
        ):
            raise ContractError("media_type must be a bounded MIME type")
        if self.content_class not in self.CONTENT_CLASSES:
            raise ContractError("unsupported content_class")
        if self.privacy not in self.PRIVACY_CLASSES:
            raise ContractError("unsupported privacy")
        if self.source_store not in self.STORES:
            raise ContractError("unsupported source_store")
        if self.target_store not in self.STORES:
            raise ContractError("unsupported target_store")
        _utc_seconds(self.created_at, "created_at")
        if self.chunk_size_bytes != CHUNK_SIZE_BYTES:
            raise ContractError("chunk_size_bytes must be exactly 8 MiB")
        expected_chunks = (
            0 if self.byte_length == 0
            else math.ceil(self.byte_length / CHUNK_SIZE_BYTES)
        )
        if self.chunk_count != expected_chunks:
            raise ContractError("chunk_count does not match byte_length")
        if not isinstance(self.executable, bool):
            raise ContractError("executable must be boolean")
        if self.executable:
            raise ContractError("phase-one artifacts may not be executable")
        if not isinstance(self.archive, bool):
            raise ContractError("archive must be boolean")
        if self.retention_class not in self.RETENTION_CLASSES:
            raise ContractError("unsupported retention_class")

    def digest_fields(self) -> tuple[str, ...]:
        return (
            ARTIFACT_DOMAIN,
            *(_canonical_scalar(getattr(self, field)) for field in self.FIELDS),
        )

    def digest(self) -> str:
        self.validate()
        return sha256_text_tuple(self.digest_fields())


__all__ = [
    "ARTIFACT_SCHEMA",
    "AUTHORIZATION_SCHEMA",
    "ArtifactManifest",
    "AuthorizationEnvelope",
    "CHUNK_SIZE_BYTES",
    "ContractError",
    "WRITE_ROOT_ID",
]
