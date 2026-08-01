from __future__ import annotations

import unittest

from pc_connection.canonical import (
    ENCODING_ID,
    encode_text_tuple,
    sha256_text_tuple,
)


class CanonicalTupleTests(unittest.TestCase):
    def test_encoding_identifier_is_stable(self):
        self.assertEqual(ENCODING_ID, "LENGTH_PREFIXED_UTF8_TEXT_TUPLE_V1")

    def test_empty_tuple_known_vector(self):
        self.assertEqual(encode_text_tuple(()), b"T1|0|")
        self.assertEqual(
            sha256_text_tuple(()),
            "7948c220414c5c6595bcca158f741923ddd6ba8d8dbbf113b7a11f776e632301",
        )

    def test_single_ascii_field_known_vector(self):
        self.assertEqual(encode_text_tuple(("a",)), b"T1|1|1:a")
        self.assertEqual(
            sha256_text_tuple(("a",)),
            "2c5e5755229ef153431ce2d68fc92782f15f512e415a42dc14642c32ac551dec",
        )

    def test_utf8_lengths_are_byte_lengths(self):
        fields = ("VERA-PCCC-JOB-V1", "job-123", "é")
        self.assertEqual(
            encode_text_tuple(fields),
            b"T1|3|16:VERA-PCCC-JOB-V17:job-1232:\xc3\xa9",
        )
        self.assertEqual(
            sha256_text_tuple(fields),
            "ac7277885c88ba043ba882f0c71a3c42415991f8bec0fb9c4761733c8cb4f462",
        )

    def test_field_order_changes_digest(self):
        self.assertNotEqual(
            sha256_text_tuple(("issuer", "host")),
            sha256_text_tuple(("host", "issuer")),
        )

    def test_non_text_field_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "field 1 must be str"):
            encode_text_tuple(("valid", 7))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
