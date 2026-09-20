from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "architecture"
    / "discovery_attestations"
    / "SECOND_EFFECT_OBSERVER_V1.json"
)


def canonical(value) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class SecondObserverPrivateReceiptTests(unittest.TestCase):
    def test_public_attestation_recomputes_from_private_receipt(self):
        data = json.loads(RECEIPT.read_text(encoding="utf-8"))
        core = data["receipt_core"]
        public = data["public_attestation"]
        nonce = core["nonce_hex"]

        consumer = hashlib.sha256(
            canonical(
                {
                    "domain": "DISCOVERY_PRIVATE_SECOND_OBSERVER_ID_V1",
                    "nonce": nonce,
                    "observer_role": core["observer_role"],
                }
            )
        ).hexdigest()
        subject = hashlib.sha256(
            canonical(
                {
                    "domain": "DISCOVERY_PRIVATE_SECOND_OBSERVER_SUBJECT_V1",
                    "nonce": nonce,
                    "subject": core["subject"],
                }
            )
        ).hexdigest()
        receipt = hashlib.sha256(canonical(core)).hexdigest()

        self.assertEqual(public["consumer_commitment_sha256"], consumer)
        self.assertEqual(public["subject_commitment_sha256"], subject)
        self.assertEqual(public["receipt_sha256"], receipt)
        self.assertEqual(
            public["opaque_handle"],
            f"PRIVATE_OPAQUE_{consumer[:16]}",
        )
        self.assertEqual(len({consumer, subject, receipt}), 3)

    def test_hosted_ci_is_not_promoted(self):
        data = json.loads(RECEIPT.read_text(encoding="utf-8"))
        verification = data["receipt_core"]["verification"]
        self.assertEqual(verification["hosted_ci"], "NOT_EXECUTED")
        self.assertEqual(verification["source_behavior_check"], "PASS")

    def test_public_surface_excludes_private_subject_preimage(self):
        data = json.loads(RECEIPT.read_text(encoding="utf-8"))
        allowed = set(data["privacy"]["public_surface_may_publish"])
        forbidden = set(data["privacy"]["public_surface_must_not_publish"])
        self.assertTrue(allowed)
        self.assertTrue(forbidden)
        self.assertTrue(allowed.isdisjoint(forbidden))
        self.assertIn("receipt_core.subject.ref", forbidden)


if __name__ == "__main__":
    unittest.main()
