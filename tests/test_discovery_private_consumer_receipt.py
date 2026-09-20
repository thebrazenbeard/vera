from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "architecture"
    / "discovery_attestations"
    / "PORTFOLIO_CENSUS_CONSUMER_V1.json"
)


def canonical(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def test_private_discovery_consumer_receipt_recomputes_public_attestation():
    data = json.loads(RECEIPT.read_text(encoding="utf-8"))
    core = data["receipt_core"]
    public = data["public_attestation"]
    nonce = core["nonce_hex"]

    consumer_preimage = {
        "domain": "DISCOVERY_PRIVATE_CONSUMER_V1",
        "nonce": nonce,
        "consumer": core["consumer"],
    }
    subject_preimage = {
        "domain": "DISCOVERY_PRIVATE_SUBJECT_V1",
        "nonce": nonce,
        "subject": core["subject"],
    }

    consumer = hashlib.sha256(canonical(consumer_preimage)).hexdigest()
    subject = hashlib.sha256(canonical(subject_preimage)).hexdigest()
    receipt = hashlib.sha256(canonical(core)).hexdigest()

    assert len(nonce) == 64
    assert public["commitment_scheme"] == "SHA256_PRIVATE_NONCE_CANONICAL_V1"
    assert public["consumer_commitment_sha256"] == consumer
    assert public["subject_commitment_sha256"] == subject
    assert public["receipt_sha256"] == receipt
    assert public["opaque_handle"] == f"PRIVATE_OPAQUE_{consumer[:16]}"
    assert len({consumer, subject, receipt}) == 3
    assert public["status"] == "EXACT_PRIVATE_SUBJECT_ATTESTED"


def test_private_receipt_binds_exact_discovery_census_without_promoting_authority():
    data = json.loads(RECEIPT.read_text(encoding="utf-8"))
    core = data["receipt_core"]
    census = core["discovery_census"]

    assert census["git_blob_sha1"] == "34cd2ab55d46f5a1ecc2c894f3e8cfdb8afa41df"
    assert census["total_count"] == 57
    assert (
        census["all_names_sha256"]
        == "43dfda1fa3dd24dec39e2aa345d93ab192dbda777433feae384da632b3d008dd"
    )
    assert core["authority_ceiling"] == (
        "DISCOVERY_CENSUS_DRIFT_INPUT_ONLY_NOT_CONTROL_NOT_RUNTIME_REGISTRY"
    )


def test_public_surface_excludes_private_preimages():
    data = json.loads(RECEIPT.read_text(encoding="utf-8"))
    allowed = set(data["privacy"]["public_surface_may_publish"])
    forbidden = set(data["privacy"]["public_surface_must_not_publish"])

    assert allowed
    assert forbidden
    assert allowed.isdisjoint(forbidden)
    assert "receipt_core.nonce_hex" in forbidden
    assert "receipt_core.subject.ref" in forbidden
