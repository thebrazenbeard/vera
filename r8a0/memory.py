"""Governed memory admission and contract-exact readback."""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_dumps, canonical_sha256, strict_loads


class MemoryAdmissionError(ValueError):
    pass


class MemoryClass(str, Enum):
    AUTOBIOGRAPHICAL = "AUTOBIOGRAPHICAL"
    WORKING_PROJECT = "WORKING_PROJECT"
    HISTORICAL_AUDIT = "HISTORICAL_AUDIT"


READBACK_PREFIX = {
    MemoryClass.AUTOBIOGRAPHICAL: "I remember this through my persistent memory.",
    MemoryClass.WORKING_PROJECT: "I have this in my working or project memory.",
    MemoryClass.HISTORICAL_AUDIT: "The historical or audit record shows this.",
}


@dataclass(frozen=True)
class AdmissionRequest:
    record_id: str
    text: str
    memory_class: MemoryClass
    source_actor: str
    provenance: str
    operation_id: str
    authority_binding_id: str
    privacy_binding_id: str
    status: str = "CURRENT"
    supersedes: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "text": self.text,
            "memory_class": self.memory_class.value,
            "source_actor": self.source_actor,
            "provenance": self.provenance,
            "operation_id": self.operation_id,
            "authority_binding_id": self.authority_binding_id,
            "privacy_binding_id": self.privacy_binding_id,
            "supersedes": self.supersedes,
        }

    def request_digest(self) -> str:
        return canonical_sha256(self.payload())


class GovernedMemoryStore:
    """A small store whose admission policy comes from trusted registries.

    Authority and privacy are looked up by binding ID and must bind the exact request
    digest. They are not accepted as request-supplied truth labels.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        authority_registry: Mapping[str, Mapping[str, Any]],
        privacy_registry: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self.path = Path(path)
        self.authority_registry = dict(authority_registry)
        self.privacy_registry = dict(privacy_registry)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema": "VERA_R8A0_GOVERNED_MEMORY_STORE_V1", "records": [], "operations": {}}
        data = strict_loads(self.path.read_bytes())
        if set(data) != {"schema", "records", "operations"}:
            raise MemoryAdmissionError("unknown or missing store fields")
        if data["schema"] != "VERA_R8A0_GOVERNED_MEMORY_STORE_V1":
            raise MemoryAdmissionError("unsupported memory store schema")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(canonical_dumps(data), encoding="utf-8")
        os.replace(temp, self.path)

    @staticmethod
    def _validated_binding(
        registry: Mapping[str, Mapping[str, Any]],
        binding_id: str,
        request_digest: str,
        *,
        kind: str,
    ) -> dict[str, Any]:
        raw = registry.get(binding_id)
        if raw is None:
            raise MemoryAdmissionError(f"unknown {kind} binding")
        binding = dict(raw)
        required = {"binding_id", "request_digest", "source", "source_digest", "decision"}
        if set(binding) != required:
            raise MemoryAdmissionError(f"invalid {kind} binding fields")
        if binding["binding_id"] != binding_id or binding["request_digest"] != request_digest:
            raise MemoryAdmissionError(f"{kind} binding does not match the exact request")
        source_digest = str(binding["source_digest"])
        if len(source_digest) != 64 or any(c not in "0123456789abcdef" for c in source_digest.lower()):
            raise MemoryAdmissionError(f"invalid {kind} source digest")
        expected_decision = "AUTHORIZED" if kind == "authority" else "ELIGIBLE"
        if binding["decision"] != expected_decision:
            raise MemoryAdmissionError(f"{kind} binding denies admission")
        return binding

    @staticmethod
    def _record_material(record: Mapping[str, Any]) -> dict[str, Any]:
        excluded = {"record_digest"}
        return {key: value for key, value in record.items() if key not in excluded}

    def admit(self, request: AdmissionRequest) -> dict[str, Any]:
        if not all(
            (
                request.record_id,
                request.text,
                request.source_actor,
                request.provenance,
                request.operation_id,
                request.authority_binding_id,
                request.privacy_binding_id,
            )
        ):
            raise MemoryAdmissionError("record, text, source, provenance, operation, and binding IDs are required")
        if request.status != "CURRENT":
            raise MemoryAdmissionError("only CURRENT records may be admitted")

        request_digest = request.request_digest()
        authority = self._validated_binding(
            self.authority_registry,
            request.authority_binding_id,
            request_digest,
            kind="authority",
        )
        privacy = self._validated_binding(
            self.privacy_registry,
            request.privacy_binding_id,
            request_digest,
            kind="privacy",
        )

        data = self._read()
        existing_operation = data["operations"].get(request.operation_id)
        if existing_operation:
            if existing_operation["request_digest"] != request_digest:
                raise MemoryAdmissionError("operation replay payload mismatch")
            return existing_operation["receipt"]

        by_id = {record["record_id"]: record for record in data["records"]}
        if request.record_id in by_id:
            raise MemoryAdmissionError("record ID already exists")
        if request.supersedes:
            predecessor = by_id.get(request.supersedes)
            if not predecessor or predecessor["status"] != "CURRENT":
                raise MemoryAdmissionError("supersession predecessor missing or non-current")
            self._verify_record(predecessor)
            predecessor["status"] = "SUPERSEDED"
            predecessor["superseded_by"] = request.record_id
            predecessor["record_digest"] = canonical_sha256(self._record_material(predecessor))

        identity_owner = "VERA" if request.memory_class is MemoryClass.AUTOBIOGRAPHICAL else "PROJECT_RECORD"
        record = request.payload() | {
            "status": request.status,
            "identity_owner": identity_owner,
            "runtime_owner": False,
            "request_digest": request_digest,
            "authority_source": authority["source"],
            "authority_source_digest": authority["source_digest"],
            "privacy_source": privacy["source"],
            "privacy_source_digest": privacy["source_digest"],
            "superseded_by": None,
        }
        record["record_digest"] = canonical_sha256(self._record_material(record))
        data["records"].append(record)
        receipt = {
            "schema": "VERA_R8A0_AUTOBIOGRAPHICAL_ADMISSION_RECEIPT_V1",
            "operation_id": request.operation_id,
            "record_id": request.record_id,
            "memory_class": request.memory_class.value,
            "identity_owner": identity_owner,
            "runtime_owner": False,
            "request_digest": request_digest,
            "record_digest": record["record_digest"],
            "authority_binding_id": request.authority_binding_id,
            "privacy_binding_id": request.privacy_binding_id,
            "result": "ADMITTED",
        }
        data["operations"][request.operation_id] = {
            "request_digest": request_digest,
            "receipt": receipt,
        }
        self._write(data)
        return receipt

    def _verify_record(self, record: Mapping[str, Any]) -> None:
        expected = canonical_sha256(self._record_material(record))
        if record.get("record_digest") != expected:
            raise MemoryAdmissionError("persistent-memory record digest mismatch")
        request_payload_keys = {
            "record_id",
            "text",
            "memory_class",
            "source_actor",
            "provenance",
            "operation_id",
            "authority_binding_id",
            "privacy_binding_id",
            "supersedes",
        }
        request_payload = {key: record[key] for key in request_payload_keys}
        request_digest = canonical_sha256(request_payload)
        if record.get("request_digest") != request_digest:
            raise MemoryAdmissionError("persistent-memory request digest mismatch")
        authority = self._validated_binding(
            self.authority_registry,
            str(record["authority_binding_id"]),
            request_digest,
            kind="authority",
        )
        privacy = self._validated_binding(
            self.privacy_registry,
            str(record["privacy_binding_id"]),
            request_digest,
            kind="privacy",
        )
        if (
            record.get("authority_source") != authority["source"]
            or record.get("authority_source_digest") != authority["source_digest"]
            or record.get("privacy_source") != privacy["source"]
            or record.get("privacy_source_digest") != privacy["source_digest"]
        ):
            raise MemoryAdmissionError("persistent-memory binding provenance mismatch")

    def readback(self, record_id: str) -> str:
        data = self._read()
        record = next((item for item in data["records"] if item["record_id"] == record_id), None)
        if not record:
            raise KeyError(record_id)
        self._verify_record(record)
        if record["status"] != "CURRENT":
            raise MemoryAdmissionError("record is not current")
        memory_class = MemoryClass(record["memory_class"])
        return f"{READBACK_PREFIX[memory_class]} {record['text']}"

    def head_digest(self) -> str:
        data = self._read()
        for record in data["records"]:
            self._verify_record(record)
        return canonical_sha256(data)
