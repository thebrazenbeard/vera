from __future__ import annotations

import hashlib
from collections.abc import Iterable

ENCODING_ID = "LENGTH_PREFIXED_UTF8_TEXT_TUPLE_V1"


def encode_text_tuple(fields: Iterable[str]) -> bytes:
    """Encode an ordered text tuple using the repository's T1 contract.

    Format:
      T1|<field-count>|<byte-length>:<value>...

    Lengths are UTF-8 byte lengths, not Python character counts.
    """

    materialized = tuple(fields)
    for index, field in enumerate(materialized):
        if not isinstance(field, str):
            raise TypeError(f"field {index} must be str")

    chunks = [f"T1|{len(materialized)}|".encode("ascii")]
    for field in materialized:
        encoded = field.encode("utf-8", errors="strict")
        chunks.append(str(len(encoded)).encode("ascii"))
        chunks.append(b":")
        chunks.append(encoded)
    return b"".join(chunks)


def sha256_text_tuple(fields: Iterable[str]) -> str:
    """Return lowercase SHA-256 for the canonical encoded tuple."""

    return hashlib.sha256(encode_text_tuple(fields)).hexdigest()


__all__ = ["ENCODING_ID", "encode_text_tuple", "sha256_text_tuple"]
