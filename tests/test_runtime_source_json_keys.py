from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.validate_runtime_source_json_keys import (
    load_unambiguous_json,
    validate_source_syntax,
)


ROOT = Path(__file__).resolve().parents[1]


class RuntimeSourceJsonUniqueKeyTests(unittest.TestCase):
    def _load_fixture(self, contents: str):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "candidate.json"
            path.write_text(contents, encoding="utf-8")
            return load_unambiguous_json(path)

    def test_real_current_source_artifacts_are_unambiguous(self):
        self.assertEqual(len(validate_source_syntax(ROOT)), 7)

    def test_reject_duplicate_status_claim(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key: 'status'"):
            self._load_fixture('{"status":"INSTALLED", "status":"SOURCE_ONLY"}')

    def test_reject_nested_duplicate_keys(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key: 'runtime_consumed'"):
            self._load_fixture('{"lifecycle":{"runtime_consumed":true,"runtime_consumed":false}}')

    def test_reject_escaped_duplicate_keys(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key: 'status'"):
            self._load_fixture('{"status":"UNKNOWN", "st\\u0061tus":"INSTALLED"}')

    def test_reject_nonstandard_numeric(self):
        with self.assertRaisesRegex(ValueError, "non-standard JSON constant: NaN"):
            self._load_fixture('{"status":NaN}')

    def test_allow_literal_nested_objects(self):
        self.assertEqual(self._load_fixture('{"s":{"a":1,"b":2}}'), {"s": {"a": 1, "b": 2}})

    def test_allow_key_like_text_inside_string(self):
        document = self._load_fixture('{"note":"BOUND=YES; BOUND=CONFLICT", "BOUND":"CONFLICT"}')
        self.assertEqual(document["BOUND"], "CONFLICT")

    def test_reject_non_object_root(self):
        with self.assertRaisesRegex(ValueError, "top-level runtime-cohesion source"):
            self._load_fixture('[1,2,3]')


if __name__ == "__main__":
    unittest.main()
