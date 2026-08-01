from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping, Sequence
from uuid import RFC_4122, UUID

from pc_connection import (
    PHASE_ONE_OPERATIONS,
    PHASE_ONE_REMOTE_TRANSFER_ENABLED,
    REMOTE_TRANSFER_OPERATIONS,
)
from pc_connection.canonical import sha256_domain_text_tuple

JOB_SCHEMA = "VERA_PCCC_JOB_V1"
AUTHORIZATION_SCHEMA = "VERA_PCCC_AUTHORIZATION_V1"
ARTIFACT_SCHEMA = "VERA_PCCC_ARTIFACT_MANIFEST_V1"
JOB_DOMAIN = "VERA-PCCC-JOB-V1"
AUTHORIZATION_DOMAIN = "VERA-PCCC-AUTHORIZATION-V1"
ARTIFACT_DOMAIN = "VERA-PCCC-ARTIFACT-MANIFEST-V1"
WRITE_ROOT_IDS = frozenset({"PCCC_WRITE_ROOT", "NONE"})
CHUNK_SIZE_BYTES = 8 * 1024 * 1024
MAX_ARTIFACT_BYTES = 10 * 1024 * 1024 * 1024
ZERO_SHA256 = "0" * 64

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_VERSION = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$"
)
_RFC3339_MICRO_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
_SAFE_BASENAME = re.compile(r'^[^<>:"/\\|?*\x00-\x1f]+$')
_RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class ContractError(ValueError):
    """Raised when a closed PCCC contract fails validation."""


def _closed_fields(
    value: Mapping[str, Any],
    required: Sequence[str],
    contract: str,
    optional: Sequence[str] = (),
) -> None:
    if not isinstance(value, Mapping):
        raise ContractError(f"{contract} must be an object")
    actual = set(value)
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - actual)
    unknown = sorted(actual - allowed)
    if missing:
        raise ContractError(f"{contract} missing fields: {missing}")
    if unknown:
        raise ContractError(f"{contract} unknown fields: {unknown}")


def _uuid_v7(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ContractError(f"{field} must be a UUIDv7 string")
    try:
        parsed = UUID(value)
    except ValueError as exc:
        raise ContractError(f"{field} must be UUIDv7") from exc
    if (
        str(parsed) != value
        or parsed.version != 7
        or parsed.variant != RFC_4122
    ):
        raise ContractError(
            f"{field} must be canonical lowercase UUIDv7"
        )
    return value


def _bounded_text(
    value: Any,
    field: str,
    *,
    maximum: int = 1024,
) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > maximum
        or any(ord(char) < 32 for char in value)
    ):
        raise ContractError(f"{field} must be bounded UTF-8 text")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContractError(f"{field} must be lowercase SHA-256 hex")
    return value


def _uint(
    value: Any,
    field: str,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{field} must be an integer")
    if value < minimum or value > maximum:
        raise ContractError(
            f"{field} must be between {minimum} and {maximum}"
        )
    return value


def _utc_microseconds(value: Any, field: str) -> datetime:
    if (
        not isinstance(value, str)
        or not _RFC3339_MICRO_UTC.fullmatch(value)
    ):
        raise ContractError(
            f"{field} must use UTC RFC3339 with exactly six "
            "fractional digits"
        )
    return datetime.strptime(
        value,
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ).replace(tzinfo=timezone.utc)


def _semver(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _VERSION.fullmatch(value):
        raise ContractError(f"{field} must be semantic version text")
    return value


def _safe_basename(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or len(value.encode("utf-8")) > 255
        or not _SAFE_BASENAME.fullmatch(value)
        or value[-1] in {" ", "."}
    ):
        raise ContractError(f"{field} must be a safe Windows basename")
    if value.split(".", 1)[0].upper() in _RESERVED_WINDOWS_NAMES:
        raise ContractError(
            f"{field} uses a reserved Windows device name"
        )
    return value


def _canonical_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass(frozen=True)
class JobEnvelope:
    schema_version: str
    envelope_id: str
    request_id: str
    idempotency_key: str
    project_id: str
    requester_principal_id: str
    requester_principal_type: str
    host_id: str
    operation_id: str
    operation_version: int
    parameters_digest: str
    artifact_manifest_digest: str
    read_roots_digest: str
    write_root_id: str
    authorization_id: str
    authorization_revision: int
    not_before: str
    expires_at: str
    timeout_seconds: int
    max_attempts: int
    lease_ttl_seconds: int
    retry_class: str
    protocol_min_version: str
    agent_min_version: str
    required_local_policy_digest: str
    required_capability_digest: str
    issuer_revocation_epoch: int
    host_revocation_epoch: int
    nonce: str
    trace_correlation_id: str

    FIELDS = (
        "schema_version",
        "envelope_id",
        "request_id",
        "idempotency_key",
        "project_id",
        "requester_principal_id",
        "requester_principal_type",
        "host_id",
        "operation_id",
        "operation_version",
        "parameters_digest",
        "artifact_manifest_digest",
        "read_roots_digest",
        "write_root_id",
        "authorization_id",
        "authorization_revision",
        "not_before",
        "expires_at",
        "timeout_seconds",
        "max_attempts",
        "lease_ttl_seconds",
        "retry_class",
        "protocol_min_version",
        "agent_min_version",
        "required_local_policy_digest",
        "required_capability_digest",
        "issuer_revocation_epoch",
        "host_revocation_epoch",
        "nonce",
        "trace_correlation_id",
    )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "JobEnvelope":
        _closed_fields(value, cls.FIELDS, "job envelope")
        envelope = cls(**{field: value[field] for field in cls.FIELDS})
        envelope.validate()
        return envelope

    def validate(self) -> None:
        if self.schema_version != JOB_SCHEMA:
            raise ContractError("unsupported job schema")
        for field in (
            "envelope_id",
            "request_id",
            "host_id",
            "authorization_id",
            "nonce",
            "trace_correlation_id",
        ):
            _uuid_v7(getattr(self, field), field)
        _bounded_text(
            self.idempotency_key,
            "idempotency_key",
            maximum=128,
        )
        _bounded_text(self.project_id, "project_id", maximum=128)
        _bounded_text(
            self.requester_principal_id,
            "requester_principal_id",
            maximum=256,
        )
        if self.requester_principal_type not in {
            "USER",
            "SERVICE",
            "CONNECTOR",
        }:
            raise ContractError("unsupported requester_principal_type")
        if self.operation_id not in PHASE_ONE_OPERATIONS:
            raise ContractError("operation_id is not in phase one")
        _uint(
            self.operation_version,
            "operation_version",
            minimum=1,
            maximum=4_294_967_295,
        )
        for field in (
            "parameters_digest",
            "artifact_manifest_digest",
            "read_roots_digest",
            "required_local_policy_digest",
            "required_capability_digest",
        ):
            _sha256(getattr(self, field), field)
        if self.write_root_id not in WRITE_ROOT_IDS:
            raise ContractError("unsupported write_root_id")
        _uint(
            self.authorization_revision,
            "authorization_revision",
            minimum=1,
            maximum=18_446_744_073_709_551_615,
        )
        not_before = _utc_microseconds(
            self.not_before,
            "not_before",
        )
        expires = _utc_microseconds(self.expires_at, "expires_at")
        if (
            not_before >= expires
            or (expires - not_before).total_seconds() > 3600
        ):
            raise ContractError("job freshness window is invalid")
        _uint(
            self.timeout_seconds,
            "timeout_seconds",
            minimum=1,
            maximum=3600,
        )
        _uint(
            self.max_attempts,
            "max_attempts",
            minimum=1,
            maximum=5,
        )
        _uint(
            self.lease_ttl_seconds,
            "lease_ttl_seconds",
            minimum=30,
            maximum=300,
        )
        if self.retry_class not in {
            "PURE_READ",
            "CONTENT_ADDRESSED_WRITE",
            "AT_MOST_ONCE",
        }:
            raise ContractError("unsupported retry_class")
        _semver(self.protocol_min_version, "protocol_min_version")
        _semver(self.agent_min_version, "agent_min_version")
        _uint(
            self.issuer_revocation_epoch,
            "issuer_revocation_epoch",
            minimum=0,
            maximum=18_446_744_073_709_551_615,
        )
        _uint(
            self.host_revocation_epoch,
            "host_revocation_epoch",
            minimum=0,
            maximum=18_446_744_073_709_551_615,
        )

    def digest_fields(self) -> tuple[str, ...]:
        return tuple(
            _canonical_scalar(getattr(self, field))
            for field in self.FIELDS
        )

    def digest(self) -> str:
        self.validate()
        return sha256_domain_text_tuple(JOB_DOMAIN, self.digest_fields())


@dataclass(frozen=True)
class AuthorizationEnvelope:
    schema_version: str
    envelope_id: str
    job_id: str
    issuer_id: str
    subject_user_id: str
    host_id: str
    operation: str
    operation_version: int
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
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "AuthorizationEnvelope":
        _closed_fields(value, cls.FIELDS, "authorization envelope")
        envelope = cls(**{field: value[field] for field in cls.FIELDS})
        envelope.validate()
        return envelope

    def validate(self) -> None:
        if self.schema_version != AUTHORIZATION_SCHEMA:
            raise ContractError("unsupported authorization schema")
        for field in (
            "envelope_id",
            "job_id",
            "host_id",
            "authorization_id",
            "nonce",
        ):
            _uuid_v7(getattr(self, field), field)
        _bounded_text(self.issuer_id, "issuer_id", maximum=256)
        _bounded_text(
            self.subject_user_id,
            "subject_user_id",
            maximum=256,
        )
        if self.operation not in PHASE_ONE_OPERATIONS:
            raise ContractError("operation is not in phase one")
        _uint(
            self.operation_version,
            "operation_version",
            minimum=1,
            maximum=4_294_967_295,
        )
        for field in (
            "parameters_digest",
            "artifact_manifest_digest",
            "read_roots_digest",
        ):
            _sha256(getattr(self, field), field)
        if self.write_root_id not in WRITE_ROOT_IDS:
            raise ContractError("unsupported write_root_id")
        _uint(
            self.authorization_revision,
            "authorization_revision",
            minimum=1,
            maximum=18_446_744_073_709_551_615,
        )
        issued = _utc_microseconds(self.issued_at, "issued_at")
        not_before = _utc_microseconds(
            self.not_before,
            "not_before",
        )
        expires = _utc_microseconds(self.expires_at, "expires_at")
        if not issued <= not_before < expires:
            raise ContractError(
                "timestamps must satisfy issued_at <= not_before "
                "< expires_at"
            )
        if (expires - not_before).total_seconds() > 3600:
            raise ContractError(
                "authorization window exceeds one hour"
            )
        _uint(
            self.max_attempts,
            "max_attempts",
            minimum=1,
            maximum=5,
        )
        _uint(
            self.lease_ttl_seconds,
            "lease_ttl_seconds",
            minimum=30,
            maximum=300,
        )
        _semver(self.protocol_min_version, "protocol_min_version")
        _semver(self.agent_min_version, "agent_min_version")
        _uint(
            self.issuer_revocation_epoch,
            "issuer_revocation_epoch",
            minimum=0,
            maximum=18_446_744_073_709_551_615,
        )
        _uint(
            self.host_revocation_epoch,
            "host_revocation_epoch",
            minimum=0,
            maximum=18_446_744_073_709_551_615,
        )

    def digest_fields(self) -> tuple[str, ...]:
        return tuple(
            _canonical_scalar(getattr(self, field))
            for field in self.FIELDS
        )

    def digest(self) -> str:
        self.validate()
        return sha256_domain_text_tuple(
            AUTHORIZATION_DOMAIN,
            self.digest_fields(),
        )


@dataclass(frozen=True)
class ArtifactSource:
    store: str
    locator: str
    immutable_locator_version: str

    FIELDS = ("store", "locator", "immutable_locator_version")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ArtifactSource":
        _closed_fields(value, cls.FIELDS, "artifact source")
        source = cls(**{field: value[field] for field in cls.FIELDS})
        if source.store != "LOCAL_ONLY":
            raise ContractError(
                "phase one artifact source must be LOCAL_ONLY"
            )
        _bounded_text(source.locator, "source.locator", maximum=1024)
        if "://" in source.locator or ":" in source.locator:
            raise ContractError(
                "phase one source locator must not be a URL or ADS"
            )
        _bounded_text(
            source.immutable_locator_version,
            "source.immutable_locator_version",
            maximum=256,
        )
        return source


@dataclass(frozen=True)
class DestinationPolicy:
    store: str
    backend_profile_id: str
    backend_profile_digest: str
    remote_transfer_enabled: bool
    relative_path: str

    FIELDS = (
        "store",
        "backend_profile_id",
        "backend_profile_digest",
        "remote_transfer_enabled",
        "relative_path",
    )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "DestinationPolicy":
        _closed_fields(value, cls.FIELDS, "destination policy")
        policy = cls(**{field: value[field] for field in cls.FIELDS})
        if (
            policy.store != "LOCAL_ONLY"
            or policy.backend_profile_id != "LOCAL_ONLY"
        ):
            raise ContractError(
                "phase one destination backend must be LOCAL_ONLY"
            )
        _sha256(
            policy.backend_profile_digest,
            "backend_profile_digest",
        )
        if policy.remote_transfer_enabled is not False:
            raise ContractError("phase one remote transfer is disabled")
        _bounded_text(
            policy.relative_path,
            "destination relative_path",
            maximum=1024,
        )
        parts = policy.relative_path.replace("/", "\\").split("\\")
        if (
            policy.relative_path.startswith(("/", "\\"))
            or ":" in policy.relative_path
            or ".." in parts
        ):
            raise ContractError("destination relative_path is unsafe")
        return policy


@dataclass(frozen=True)
class ArtifactAuthorization:
    authorization_id: str
    revision: int
    allowed_host_id: str
    allowed_job_id: str
    allowed_operations: tuple[str, ...]
    max_bytes: int
    issued_at: str
    expires_at: str

    FIELDS = (
        "authorization_id",
        "revision",
        "allowed_host_id",
        "allowed_job_id",
        "allowed_operations",
        "max_bytes",
        "issued_at",
        "expires_at",
    )

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any],
    ) -> "ArtifactAuthorization":
        _closed_fields(value, cls.FIELDS, "artifact authorization")
        operations = value["allowed_operations"]
        if (
            not isinstance(operations, list)
            or not operations
            or any(not isinstance(item, str) for item in operations)
            or len(set(operations)) != len(operations)
            or operations != sorted(operations)
        ):
            raise ContractError(
                "allowed_operations must be a sorted unique "
                "nonempty list"
            )
        authorization = cls(
            authorization_id=value["authorization_id"],
            revision=value["revision"],
            allowed_host_id=value["allowed_host_id"],
            allowed_job_id=value["allowed_job_id"],
            allowed_operations=tuple(operations),
            max_bytes=value["max_bytes"],
            issued_at=value["issued_at"],
            expires_at=value["expires_at"],
        )
        for field in (
            "authorization_id",
            "allowed_host_id",
            "allowed_job_id",
        ):
            _uuid_v7(getattr(authorization, field), field)
        _uint(
            authorization.revision,
            "authorization revision",
            minimum=1,
            maximum=18_446_744_073_709_551_615,
        )
        if any(item not in PHASE_ONE_OPERATIONS for item in operations):
            raise ContractError("artifact operation is outside phase one")
        _uint(
            authorization.max_bytes,
            "authorization max_bytes",
            minimum=0,
            maximum=MAX_ARTIFACT_BYTES,
        )
        issued = _utc_microseconds(
            authorization.issued_at,
            "authorization issued_at",
        )
        expires = _utc_microseconds(
            authorization.expires_at,
            "authorization expires_at",
        )
        if (
            issued >= expires
            or (expires - issued).total_seconds() > 3600
        ):
            raise ContractError(
                "artifact authorization freshness is invalid"
            )
        return authorization


@dataclass(frozen=True)
class RetentionPolicy:
    retention_class: str
    retain_until: str

    FIELDS = ("class", "retain_until")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RetentionPolicy":
        _closed_fields(value, cls.FIELDS, "retention policy")
        policy = cls(
            retention_class=value["class"],
            retain_until=value["retain_until"],
        )
        if policy.retention_class not in {
            "EPHEMERAL",
            "PROJECT",
            "RELEASE",
            "LEGAL_HOLD",
        }:
            raise ContractError("unsupported retention class")
        _utc_microseconds(policy.retain_until, "retain_until")
        return policy


@dataclass(frozen=True)
class ArtifactManifest:
    schema_version: str
    manifest_id: str
    manifest_digest_algorithm: str
    manifest_sha256: str
    artifact_id: str
    content_id: str
    logical_name: str
    declared_filename: str
    byte_length: int
    sha256: str
    content_class: str
    privacy_class: str
    execution_class: str
    archive_class: str
    media_type_declared: str
    source: ArtifactSource
    destination_policy: DestinationPolicy
    authorization: ArtifactAuthorization
    retention: RetentionPolicy
    created_at: str

    FIELDS = (
        "schema_version",
        "manifest_id",
        "manifest_digest_algorithm",
        "manifest_sha256",
        "artifact_id",
        "content_id",
        "logical_name",
        "declared_filename",
        "byte_length",
        "sha256",
        "content_class",
        "privacy_class",
        "execution_class",
        "archive_class",
        "media_type_declared",
        "source",
        "destination_policy",
        "authorization",
        "retention",
        "created_at",
    )
    CONTENT_CLASSES = {
        "SOURCE",
        "CONFIG",
        "LOG",
        "RECEIPT",
        "TEST_EVIDENCE",
        "DATASET",
        "MODEL_WEIGHT",
        "CHECKPOINT",
        "ARCHIVE",
        "USER_DOCUMENT",
        "EXECUTABLE",
        "OTHER",
        "UNKNOWN",
    }
    PRIVACY_CLASSES = {
        "PUBLIC",
        "PROJECT",
        "PRIVATE",
        "SENSITIVE",
        "CREDENTIAL_PROHIBITED",
    }
    ARCHIVE_CLASSES = {
        "NOT_ARCHIVE",
        "ZIP",
        "TAR",
        "TAR_GZ",
        "UNKNOWN",
    }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ArtifactManifest":
        _closed_fields(value, cls.FIELDS, "artifact manifest")
        manifest = cls(
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
            source=ArtifactSource.from_mapping(value["source"]),
            destination_policy=DestinationPolicy.from_mapping(
                value["destination_policy"]
            ),
            authorization=ArtifactAuthorization.from_mapping(
                value["authorization"]
            ),
            retention=RetentionPolicy.from_mapping(value["retention"]),
            created_at=value["created_at"],
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        if self.schema_version != ARTIFACT_SCHEMA:
            raise ContractError("unsupported artifact manifest schema")
        if self.manifest_digest_algorithm != "SHA-256":
            raise ContractError("unsupported manifest digest algorithm")
        _uuid_v7(self.manifest_id, "manifest_id")
        _uuid_v7(self.artifact_id, "artifact_id")
        _sha256(self.manifest_sha256, "manifest_sha256")
        _bounded_text(self.logical_name, "logical_name", maximum=256)
        _safe_basename(self.declared_filename, "declared_filename")
        _uint(
            self.byte_length,
            "byte_length",
            minimum=0,
            maximum=MAX_ARTIFACT_BYTES,
        )
        digest = _sha256(self.sha256, "sha256")
        if self.content_id != (
            f"urn:sha256:{digest}:{self.byte_length}"
        ):
            raise ContractError(
                "content_id does not bind SHA-256 and byte length"
            )
        if self.content_class not in self.CONTENT_CLASSES:
            raise ContractError("unsupported content_class")
        if self.privacy_class not in self.PRIVACY_CLASSES:
            raise ContractError("unsupported privacy_class")
        if self.privacy_class == "CREDENTIAL_PROHIBITED":
            raise ContractError("credentials are prohibited artifacts")
        if self.execution_class != "NON_EXECUTABLE":
            raise ContractError(
                "phase one executable artifacts are denied"
            )
        if self.content_class == "EXECUTABLE":
            raise ContractError(
                "phase one executable content is denied"
            )
        if self.archive_class not in self.ARCHIVE_CLASSES:
            raise ContractError("unsupported archive_class")
        _bounded_text(
            self.media_type_declared,
            "media_type_declared",
            maximum=127,
        )
        if "/" not in self.media_type_declared:
            raise ContractError(
                "media_type_declared must be a MIME type"
            )
        if self.authorization.max_bytes < self.byte_length:
            raise ContractError(
                "authorization max_bytes is below byte_length"
            )
        created = _utc_microseconds(self.created_at, "created_at")
        retain_until = _utc_microseconds(
            self.retention.retain_until,
            "retain_until",
        )
        if retain_until < created:
            raise ContractError("retain_until precedes created_at")
        if (
            any(
                operation in REMOTE_TRANSFER_OPERATIONS
                for operation in self.authorization.allowed_operations
            )
            and not PHASE_ONE_REMOTE_TRANSFER_ENABLED
        ):
            raise ContractError(
                "remote transfer operations are capability-disabled "
                "in phase one"
            )
        if self.manifest_sha256 != self.computed_manifest_sha256():
            raise ContractError(
                "manifest_sha256 does not match canonical fields"
            )

    def digest_fields(self) -> tuple[str, ...]:
        """Fixed digest scope, excluding manifest_sha256 itself."""

        return (
            self.schema_version,
            self.manifest_id,
            self.manifest_digest_algorithm,
            self.artifact_id,
            self.content_id,
            self.logical_name,
            self.declared_filename,
            str(self.byte_length),
            self.sha256,
            self.content_class,
            self.privacy_class,
            self.execution_class,
            self.archive_class,
            self.media_type_declared,
            self.source.store,
            self.source.locator,
            self.source.immutable_locator_version,
            self.destination_policy.store,
            self.destination_policy.backend_profile_id,
            self.destination_policy.backend_profile_digest,
            _canonical_scalar(
                self.destination_policy.remote_transfer_enabled
            ),
            self.destination_policy.relative_path,
            self.authorization.authorization_id,
            str(self.authorization.revision),
            self.authorization.allowed_host_id,
            self.authorization.allowed_job_id,
            ",".join(self.authorization.allowed_operations),
            str(self.authorization.max_bytes),
            self.authorization.issued_at,
            self.authorization.expires_at,
            self.retention.retention_class,
            self.retention.retain_until,
            self.created_at,
        )

    def computed_manifest_sha256(self) -> str:
        return sha256_domain_text_tuple(
            ARTIFACT_DOMAIN,
            self.digest_fields(),
        )


__all__ = [
    "ARTIFACT_SCHEMA",
    "AUTHORIZATION_SCHEMA",
    "JOB_SCHEMA",
    "ARTIFACT_DOMAIN",
    "AUTHORIZATION_DOMAIN",
    "JOB_DOMAIN",
    "ArtifactAuthorization",
    "ArtifactManifest",
    "ArtifactSource",
    "AuthorizationEnvelope",
    "DestinationPolicy",
    "JobEnvelope",
    "RetentionPolicy",
    "CHUNK_SIZE_BYTES",
    "ContractError",
    "MAX_ARTIFACT_BYTES",
    "WRITE_ROOT_IDS",
    "ZERO_SHA256",
]
