from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

from tests.pc_connection.test_contracts import (
    valid_artifact,
    valid_authorization,
    valid_job,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATHS = {
    "authorization": (
        ROOT
        / "schemas"
        / "vera_pc_connection_authorization_v1.schema.json"
    ),
    "job": (
        ROOT
        / "schemas"
        / "vera_pc_connection_job_v1.schema.json"
    ),
    "artifact": (
        ROOT
        / "schemas"
        / "vera_pc_connection_artifact_manifest_v1.schema.json"
    ),
}


def load(name: str) -> dict:
    return json.loads(
        SCHEMA_PATHS[name].read_text(encoding="utf-8")
    )


class PcConnectionSchemaTests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self) -> None:
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(name=name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                Draft202012Validator.check_schema(schema)

    def test_valid_contracts_pass_schema(self) -> None:
        Draft202012Validator(load("authorization")).validate(
            valid_authorization()
        )
        Draft202012Validator(load("job")).validate(valid_job())
        Draft202012Validator(load("artifact")).validate(
            valid_artifact()
        )

    def test_signature_fields_fail_authorization_schema(self) -> None:
        for field in (
            "signature",
            "issuer_key_id",
            "device_proof",
        ):
            value = valid_authorization()
            value[field] = "forbidden"
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    Draft202012Validator(
                        load("authorization")
                    ).validate(value)

    def test_uuidv4_and_second_precision_fail_schema(self) -> None:
        value = valid_job()
        value["host_id"] = (
            "22222222-2222-4222-8222-222222222222"
        )
        with self.assertRaises(ValidationError):
            Draft202012Validator(load("job")).validate(value)
        value = valid_authorization()
        value["issued_at"] = "2026-08-01T20:00:00Z"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load("authorization")).validate(value)

    def test_remote_artifact_backend_fails_schema(self) -> None:
        value = valid_artifact()
        value["destination_policy"]["store"] = "SUPABASE_STORAGE"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load("artifact")).validate(value)

    def test_artifact_oversize_and_executable_fail_schema(self) -> None:
        value = valid_artifact()
        value["byte_length"] = 10 * 1024 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            Draft202012Validator(load("artifact")).validate(value)
        value = valid_artifact()
        value["execution_class"] = "EXECUTABLE_UNTRUSTED"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load("artifact")).validate(value)


if __name__ == "__main__":
    unittest.main()
