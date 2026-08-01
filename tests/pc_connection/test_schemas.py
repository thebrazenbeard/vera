from __future__ import annotations

import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError

from tests.pc_connection.test_contracts import (
    valid_artifact,
    valid_authorization,
)

ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION_SCHEMA = (
    ROOT / "schemas" / "vera_pc_connection_authorization_v1.schema.json"
)
ARTIFACT_SCHEMA = (
    ROOT / "schemas" / "vera_pc_connection_artifact_manifest_v1.schema.json"
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class PcConnectionSchemaTests(unittest.TestCase):
    def test_schemas_are_valid_draft_2020_12(self) -> None:
        for path in (AUTHORIZATION_SCHEMA, ARTIFACT_SCHEMA):
            with self.subTest(path=path):
                Draft202012Validator.check_schema(load(path))

    def test_valid_contracts_pass_schema(self) -> None:
        Draft202012Validator(load(AUTHORIZATION_SCHEMA)).validate(
            valid_authorization()
        )
        Draft202012Validator(load(ARTIFACT_SCHEMA)).validate(valid_artifact())

    def test_authorization_unknown_field_fails(self) -> None:
        value = valid_authorization()
        value["unexpected"] = "nope"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load(AUTHORIZATION_SCHEMA)).validate(value)

    def test_authorization_command_execution_fails(self) -> None:
        value = valid_authorization()
        value["operation"] = "RUN_COMMAND"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load(AUTHORIZATION_SCHEMA)).validate(value)

    def test_artifact_executable_promotion_fails(self) -> None:
        value = valid_artifact()
        value["executable"] = True
        with self.assertRaises(ValidationError):
            Draft202012Validator(load(ARTIFACT_SCHEMA)).validate(value)

    def test_artifact_path_escape_fails(self) -> None:
        value = valid_artifact()
        value["filename"] = "../escape.zip"
        with self.assertRaises(ValidationError):
            Draft202012Validator(load(ARTIFACT_SCHEMA)).validate(value)


if __name__ == "__main__":
    unittest.main()
