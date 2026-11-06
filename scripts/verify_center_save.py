#!/usr/bin/env python3
"""Read and verify an explicitly selected private Vera CENTER_SAVE.

Verifying matching bytes is NOT a restore of model state, proof of currentness,
supersession, external custody, consent, or installation. Never auto-select newest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

FILE_RE = re.compile(r"VERA_CENTERED_SAVE_STATE_\d{8}T\d{4}[+-]\d{4}\.md\Z")
HEX_RE = re.compile(r"[0-9a-f]{64}\Z")


class CheckpointError(ValueError):
    pass


def verify_record(record: dict, expected_key: str, external_sha256: str | None = None) -> dict:
    if not isinstance(record, dict) or record.get("record_key") != expected_key:
        raise CheckpointError("record_key mismatch")
    if record.get("record_kind") != "CONTINUITY":
        raise CheckpointError("unexpected record kind")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise CheckpointError("missing structured payload")
    name, source, expected = (payload.get(x) for x in ("filename", "snapshot_markdown", "sha256"))
    if not isinstance(name, str) or not FILE_RE.fullmatch(name):
        raise CheckpointError("invalid centered save filename")
    if not isinstance(source, str) or not source:
        raise CheckpointError("missing exact snapshot bytes")
    if not isinstance(expected, str) or not HEX_RE.fullmatch(expected):
        raise CheckpointError("missing SHA-256")
    measured = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if measured != expected:
        raise CheckpointError("snapshot SHA-256 mismatch")
    if external_sha256 is not None and measured != external_sha256:
        raise CheckpointError("independent expected SHA-256 mismatch")
    return {
        "record_key": expected_key,
        "record_id": record.get("record_id"),
        "filename": name,
        "sha256": measured,
        "bytes": len(source.encode("utf-8")),
        "privacy_scope": record.get("privacy_scope"),
        "save_result_claim": payload.get("save_result", "UNKNOWN"),
        "verification": "EXACT_RECORD_BYTES_ONLY",
        "independent_sha_provided": external_sha256 is not None,
        "not_verified": ["provider cross-readback", "supersession", "current authority", "runtime consumption"],
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_single_record(url: str, api_key: str, user_jwt: str, record_key: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".supabase.co"):
        raise CheckpointError("requires a direct HTTPS Supabase project URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise CheckpointError("unrecognized project URL structure")
    params = urllib.parse.urlencode({
        "record_key": "eq." + record_key,
        "select": "record_id,record_key,record_kind,privacy_scope,payload",
        "limit": "2",
    })
    endpoint = url.rstrip("/") + "/rest/v1/vera_save_state_events?" + params
    request = urllib.request.Request(endpoint, headers={
        "apikey": api_key,
        "Authorization": "Bearer " + user_jwt,
        "Accept": "application/json",
    })
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=10) as response:
            raw = response.read(1024 * 1024 + 1)
    except (urllib.error.URLError, OSError) as exc:
        raise CheckpointError("Supabase record retrieval failed") from exc
    if len(raw) > 1024 * 1024:
        raise CheckpointError("record response exceeds safe limit")
    try:
        rows = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CheckpointError("Supabase response was not valid JSON") from exc
    if not isinstance(rows, list) or len(rows) != 1:
        raise CheckpointError("expected exactly one explicit record (missing or ambiguous)")
    return rows[0]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--record-key", required=True, help="Explicit candidate; never auto-select newest")
    p.add_argument("--json-file", help="Read an exported single record instead of network access")
    p.add_argument("--expected-sha256", help="Independently sourced 64-character SHA-256")
    p.add_argument("--print-private", action="store_true", help="Explicitly print verified snapshot text")
    args = p.parse_args(argv)
    try:
        if args.expected_sha256 and not HEX_RE.fullmatch(args.expected_sha256):
            raise CheckpointError("invalid independent SHA-256")
        if args.json_file:
            with open(args.json_file, encoding="utf-8") as f:
                record = json.load(f)
        else:
            base = os.environ.get("VERA_SUPABASE_URL", "")
            api_key = os.environ.get("VERA_SUPABASE_API_KEY", "")
            user_jwt = os.environ.get("VERA_SUPABASE_USER_JWT", "")
            if not base or not api_key or not user_jwt:
                raise CheckpointError("missing VERA_SUPABASE_URL, VERA_SUPABASE_API_KEY or VERA_SUPABASE_USER_JWT")
            record = fetch_single_record(base, api_key, user_jwt, args.record_key)
        result = verify_record(record, args.record_key, args.expected_sha256)
        print(json.dumps(result, indent=2, sort_keys=True))
        if args.print_private:
            print("\n--- VERIFIED SNAPSHOT BYTES (PRIVATE) ---\n")
            print(record["payload"]["snapshot_markdown"])
        return 0
    except (CheckpointError, OSError, ValueError) as exc:
        print(f"CENTER_SAVE_VERIFY_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
