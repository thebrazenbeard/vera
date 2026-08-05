"""Governed memory admission with authenticated policy and storage records."""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_bytes, canonical_dumps, canonical_sha256, strict_loads


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


def _validated_key(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) < 16:
        raise MemoryAdmissionError("memory integrity key must contain at least 16 bytes")
    return value


def _mac(key: bytes, value: Any) -> str:
    return hmac.new(key, canonical_bytes(value), hashlib.sha256).hexdigest()


def signed_policy_binding(
    *,
    binding_id: str,
    request_digest: str,
    source: str,
    source_digest: str,
    decision: str,
    kind: str,
    integrity_key: bytes,
) -> dict[str, Any]:
    key = _validated_key(integrity_key)
    body = {
        "binding_id": binding_id,
        "request_digest": request_digest,
        "source": source,
        "source_digest": source_digest,
        "decision": decision,
        "kind": kind,
    }
    return body | {"binding_mac": _mac(key, body)}


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
    def __init__(
        self,
        path: str | Path,
        *,
        authority_registry: Mapping[str, Mapping[str, Any]],
        privacy_registry: Mapping[str, Mapping[str, Any]],
        integrity_key: bytes,
    ) -> None:
        self.path = Path(path)
        self.authority_registry = dict(authority_registry)
        self.privacy_registry = dict(privacy_registry)
        self.integrity_key = _validated_key(integrity_key)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema": "VERA_R8A0_GOVERNED_MEMORY_STORE_V2", "records": [], "operations": {}}
        data = strict_loads(self.path.read_bytes())
        if set(data) != {"schema", "records", "operations"}:
            raise MemoryAdmissionError("unknown or missing store fields")
        if data["schema"] != "VERA_R8A0_GOVERNED_MEMORY_STORE_V2":
            raise MemoryAdmissionError("unsupported memory store schema")
        if not isinstance(data["records"], list) or not isinstance(data["operations"], dict):
            raise MemoryAdmissionError("invalid memory store containers")
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(canonical_dumps(data), encoding="utf-8")
        os.replace(temp, self.path)
        if strict_loads(self.path.read_bytes()) != data:
            raise MemoryAdmissionError("persistent-memory write readback mismatch")

    def _validated_binding(
        self,
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
        required = {
            "binding_id",
            "request_digest",
            "source",
            "source_digest",
            "decision",
            "kind",
            "binding_mac",
        }
        if set(binding) != required:
            raise MemoryAdmissionError(f"invalid {kind} binding fields")
        supplied_mac = binding.pop("binding_mac")
        if not hmac.compare_digest(str(supplied_mac), _mac(self.integrity_key, binding)):
            raise MemoryAdmissionError(f"invalid {kind} binding authentication")
        if binding["kind"] != kind:
            raise MemoryAdmissionError(f"{kind} binding kind mismatch")
        if binding["binding_id"] != binding_id or binding["request_digest"] != request_digest:
            raise MemoryAdmissionError(f"{kind} binding does not match the exact request")
        source_digest = str(binding["source_digest"])
        if len(source_digest) != 64 or any(c not in "0123456789abcdef" for c in source_digest):
            raise MemoryAdmissionError(f"invalid {kind} source digest")
        expected_decision = "AUTHORIZED" if kind == "authority" else "ELIGIBLE"
        if binding["decision"] != expected_decision:
            raise MemoryAdmissionError(f"{kind} binding denies admission")
        return binding

    @staticmethod
    def _without(mapping: Mapping[str, Any], *keys: str) -> dict[str, Any]:
        excluded = set(keys)
        return {key: value for key, value in mapping.items() if key not in excluded}

    @classmethod
    def _admission_material(cls, record: Mapping[str, Any]) -> dict[str, Any]:
        return cls._without(
            record,
            "status",
            "superseded_by",
            "admission_digest",
            "record_digest",
            "record_mac",
        )

    def _seal_record(self, record_body: Mapping[str, Any]) -> dict[str, Any]:
        body = dict(record_body)
        expected_admission_digest = canonical_sha256(self._admission_material(body))
        supplied_admission_digest = body.get("admission_digest")
        if supplied_admission_digest not in (None, expected_admission_digest):
            raise MemoryAdmissionError("persistent-memory admission digest mismatch")
        body["admission_digest"] = expected_admission_digest
        record_digest = canonical_sha256(body)
        authenticated = body | {"record_digest": record_digest}
        return authenticated | {"record_mac": _mac(self.integrity_key, authenticated)}

    def _verify_record(self, record: Mapping[str, Any]) -> None:
        expected_keys = {
            "record_id",
            "text",
            "memory_class",
            "source_actor",
            "provenance",
            "operation_id",
            "authority_binding_id",
            "privacy_binding_id",
            "supersedes",
            "status",
            "identity_owner",
            "runtime_owner",
            "request_digest",
            "authority_source",
            "authority_source_digest",
            "privacy_source",
            "privacy_source_digest",
            "superseded_by",
            "admission_digest",
            "record_digest",
            "record_mac",
        }
        if set(record) != expected_keys:
            raise MemoryAdmissionError("persistent-memory record fields are missing or unknown")
        authenticated = self._without(record, "record_mac")
        if not hmac.compare_digest(str(record["record_mac"]), _mac(self.integrity_key, authenticated)):
            raise MemoryAdmissionError("persistent-memory record authentication mismatch")
        body = self._without(record, "record_digest", "record_mac")
        if record["record_digest"] != canonical_sha256(body):
            raise MemoryAdmissionError("persistent-memory record digest mismatch")
        if record["admission_digest"] != canonical_sha256(self._admission_material(record)):
            raise MemoryAdmissionError("persistent-memory admission digest mismatch")
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
        if record["request_digest"] != request_digest:
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
            record["authority_source"] != authority["source"]
            or record["authority_source_digest"] != authority["source_digest"]
            or record["privacy_source"] != privacy["source"]
            or record["privacy_source_digest"] != privacy["source_digest"]
        ):
            raise MemoryAdmissionError("persistent-memory binding provenance mismatch")

    def _seal_receipt(self, body: Mapping[str, Any]) -> dict[str, Any]:
        receipt_body = dict(body)
        return receipt_body | {"receipt_mac": _mac(self.integrity_key, receipt_body)}

    def _verify_receipt(self, receipt: Mapping[str, Any], request_digest: str, operation_id: str) -> None:
        required = {
            "schema",
            "operation_id",
            "record_id",
            "memory_class",
            "identity_owner",
            "runtime_owner",
            "request_digest",
            "admission_digest",
            "authority_binding_id",
            "privacy_binding_id",
            "result",
            "receipt_mac",
        }
        if set(receipt) != required:
            raise MemoryAdmissionError("admission receipt fields are missing or unknown")
        body = self._without(receipt, "receipt_mac")
        if not hmac.compare_digest(str(receipt["receipt_mac"]), _mac(self.integrity_key, body)):
            raise MemoryAdmissionError("admission receipt authentication mismatch")
        if receipt["schema"] != "VERA_R8A0_AUTOBIOGRAPHICAL_ADMISSION_RECEIPT_V3":
            raise MemoryAdmissionError("unsupported admission receipt schema")
        if receipt["operation_id"] != operation_id or receipt["request_digest"] != request_digest:
            raise MemoryAdmissionError("admission receipt does not bind the replayed request")
        if receipt["result"] != "ADMITTED" or receipt["runtime_owner"] is not False:
            raise MemoryAdmissionError("invalid admission receipt result")
        MemoryClass(receipt["memory_class"])

    def _seal_operation(self, request_digest: str, receipt: Mapping[str, Any]) -> dict[str, Any]:
        body = {"request_digest": request_digest, "receipt": dict(receipt)}
        return body | {"operation_mac": _mac(self.integrity_key, body)}

    def _verify_operation(
        self,
        operation_id: str,
        operation: Mapping[str, Any],
        request_digest: str,
        records: list[Mapping[str, Any]],
        *,
        require_current: bool = True,
    ) -> dict[str, Any]:
        if set(operation) != {"request_digest", "receipt", "operation_mac"}:
            raise MemoryAdmissionError("operation replay fields are missing or unknown")
        body = self._without(operation, "operation_mac")
        if not hmac.compare_digest(str(operation["operation_mac"]), _mac(self.integrity_key, body)):
            raise MemoryAdmissionError("operation replay authentication mismatch")
        if operation["request_digest"] != request_digest:
            raise MemoryAdmissionError("operation replay payload mismatch")
        receipt = dict(operation["receipt"])
        self._verify_receipt(receipt, request_digest, operation_id)

        record = next((item for item in records if item.get("record_id") == receipt["record_id"]), None)
        if record is None:
            raise MemoryAdmissionError("operation replay record is missing")
        self._verify_record(record)
        if require_current and record["status"] != "CURRENT":
            raise MemoryAdmissionError("operation replay record is not current")
        if (
            record["operation_id"] != operation_id
            or record["request_digest"] != receipt["request_digest"]
            or record["admission_digest"] != receipt["admission_digest"]
            or record["memory_class"] != receipt["memory_class"]
            or record["identity_owner"] != receipt["identity_owner"]
            or record["runtime_owner"] != receipt["runtime_owner"]
        ):
            raise MemoryAdmissionError("operation replay receipt-to-record binding mismatch")
        return receipt

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
        if existing_operation is not None:
            return self._verify_operation(
                request.operation_id,
                existing_operation,
                request_digest,
                data["records"],
            )

        by_id = {record["record_id"]: record for record in data["records"]}
        if request.record_id in by_id:
            raise MemoryAdmissionError("record ID already exists")
        if request.supersedes:
            predecessor = by_id.get(request.supersedes)
            if not predecessor or predecessor["status"] != "CURRENT":
                raise MemoryAdmissionError("supersession predecessor missing or non-current")
            self._verify_record(predecessor)
            predecessor_body = self._without(predecessor, "record_digest", "record_mac")
            predecessor_body["status"] = "SUPERSEDED"
            predecessor_body["superseded_by"] = request.record_id
            predecessor.clear()
            predecessor.update(self._seal_record(predecessor_body))

        identity_owner = "VERA" if request.memory_class is MemoryClass.AUTOBIOGRAPHICAL else "PROJECT_RECORD"
        record_body = request.payload() | {
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
        record = self._seal_record(record_body)
        data["records"].append(record)
        receipt = self._seal_receipt(
            {
                "schema": "VERA_R8A0_AUTOBIOGRAPHICAL_ADMISSION_RECEIPT_V3",
                "operation_id": request.operation_id,
                "record_id": request.record_id,
                "memory_class": request.memory_class.value,
                "identity_owner": identity_owner,
                "runtime_owner": False,
                "request_digest": request_digest,
                "admission_digest": record["admission_digest"],
                "authority_binding_id": request.authority_binding_id,
                "privacy_binding_id": request.privacy_binding_id,
                "result": "ADMITTED",
            }
        )
        data["operations"][request.operation_id] = self._seal_operation(request_digest, receipt)
        self._write(data)
        return receipt

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
        for operation_id, operation in data["operations"].items():
            self._verify_operation(
                operation_id,
                operation,
                operation["request_digest"],
                data["records"],
                require_current=False,
            )
        return canonical_sha256(data)
