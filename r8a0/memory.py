"""Governed memory admission and class-specific readback."""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .canonical import canonical_dumps, canonical_sha256, strict_loads


class MemoryAdmissionError(ValueError):
    pass


class MemoryClass(str, Enum):
    AUTOBIOGRAPHICAL = "AUTOBIOGRAPHICAL"
    WORKING_PROJECT = "WORKING_PROJECT"
    HISTORICAL_AUDIT = "HISTORICAL_AUDIT"


READBACK_PREFIX = {
    MemoryClass.AUTOBIOGRAPHICAL: "Governed autobiographical memory:",
    MemoryClass.WORKING_PROJECT: "Working project memory:",
    MemoryClass.HISTORICAL_AUDIT: "Historical audit record:",
}


@dataclass(frozen=True)
class AdmissionRequest:
    record_id: str
    text: str
    memory_class: MemoryClass
    source_actor: str
    provenance: str
    privacy_eligible: bool
    authority: str
    operation_id: str
    status: str = "CURRENT"
    supersedes: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "text": self.text,
            "memory_class": self.memory_class.value,
            "source_actor": self.source_actor,
            "provenance": self.provenance,
            "privacy_eligible": self.privacy_eligible,
            "authority": self.authority,
            "operation_id": self.operation_id,
            "status": self.status,
            "supersedes": self.supersedes,
        }


class GovernedMemoryStore:
    AUTOBIOGRAPHICAL_AUTHORITIES = {"PATRICK_OWNER", "VERA_GOVERNED_ADMISSION"}

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

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

    def admit(self, request: AdmissionRequest) -> dict[str, Any]:
        if not all((request.record_id, request.text, request.source_actor, request.provenance, request.operation_id)):
            raise MemoryAdmissionError("record, text, source, provenance, and operation ID are required")
        if not request.privacy_eligible:
            raise MemoryAdmissionError("privacy-ineligible record")
        if request.status != "CURRENT":
            raise MemoryAdmissionError("only CURRENT records may be admitted")
        if request.memory_class is MemoryClass.AUTOBIOGRAPHICAL and request.authority not in self.AUTOBIOGRAPHICAL_AUTHORITIES:
            raise MemoryAdmissionError("autobiographical admission is default-deny")

        data = self._read()
        request_digest = canonical_sha256(request.payload())
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
            predecessor["status"] = "SUPERSEDED"
            predecessor["superseded_by"] = request.record_id

        identity_owner = "VERA" if request.memory_class is MemoryClass.AUTOBIOGRAPHICAL else "PROJECT_RECORD"
        record = request.payload() | {
            "identity_owner": identity_owner,
            "runtime_owner": False,
            "record_digest": request_digest,
            "superseded_by": None,
        }
        data["records"].append(record)
        receipt = {
            "schema": "VERA_R8A0_AUTOBIOGRAPHICAL_ADMISSION_RECEIPT_V1",
            "operation_id": request.operation_id,
            "record_id": request.record_id,
            "memory_class": request.memory_class.value,
            "identity_owner": identity_owner,
            "runtime_owner": False,
            "record_digest": request_digest,
            "result": "ADMITTED",
        }
        data["operations"][request.operation_id] = {
            "request_digest": request_digest,
            "receipt": receipt,
        }
        self._write(data)
        return receipt

    def readback(self, record_id: str) -> str:
        data = self._read()
        record = next((item for item in data["records"] if item["record_id"] == record_id), None)
        if not record:
            raise KeyError(record_id)
        if record["status"] != "CURRENT":
            raise MemoryAdmissionError("record is not current")
        if not record["privacy_eligible"]:
            raise MemoryAdmissionError("record is not privacy eligible")
        memory_class = MemoryClass(record["memory_class"])
        return f"{READBACK_PREFIX[memory_class]} {record['text']}"

    def head_digest(self) -> str:
        return canonical_sha256(self._read())
