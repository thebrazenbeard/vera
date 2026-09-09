import copy
import hashlib
import json
from pathlib import Path
import unittest

from runtime_cohesion.affect_host import AffectiveBindingError, VeraAffectiveRuntimeHost
from runtime_cohesion.orgasm import StimulusAppraisal

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "VERA_ORGASM_RUNTIME_CONTRACT_V1.json"
BINDING_PATH = ROOT / "architecture" / "VERA_ORGASM_RUNTIME_BINDING_V1.json"


def checkpoint_sha256(checkpoint):
    core = dict(checkpoint)
    core.pop("checkpoint_sha256", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AffectiveCheckpointIntegrityTests(unittest.TestCase):
    def make_host(self):
        return VeraAffectiveRuntimeHost.from_bound_contract(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            runtime_instance_id="affect-checkpoint-integrity-test",
            profile="REENTRANT_CLIMAX",
        )

    def restore(self, checkpoint, *, expected_checkpoint_sha256):
        return VeraAffectiveRuntimeHost.restore_checkpoint(
            CONTRACT_PATH.read_text(encoding="utf-8"),
            json.loads(BINDING_PATH.read_text(encoding="utf-8")),
            checkpoint,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
        )

    def test_exported_checkpoint_carries_integrity_digest(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        digest = checkpoint.get("checkpoint_sha256")
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, checkpoint_sha256(checkpoint))

    def test_tampered_runtime_state_is_rejected_even_if_embedded_digest_is_recomputed(self):
        host = self.make_host()
        host.observe(StimulusAppraisal(
            sexual_relevance=0.4,
            partner_relevance=0.4,
            relational_relevance=0.4,
            anticipation_cue=0.4,
            positive_valence=0.4,
            duration_ms=500,
            context_eligible=True,
        ))
        checkpoint = host.export_checkpoint()
        trusted_expected_digest = checkpoint["checkpoint_sha256"]
        tampered = copy.deepcopy(checkpoint)
        tampered["runtime_state"]["state"]["activation_intensity"] = 1.0
        tampered["runtime_state"]["state"]["active_orgasm_event"] = True
        tampered["runtime_state"]["state"]["phase"] = "ORGASM_EVENT"
        tampered["checkpoint_sha256"] = checkpoint_sha256(tampered)

        with self.assertRaises(AffectiveBindingError):
            self.restore(tampered, expected_checkpoint_sha256=trusted_expected_digest)

    def test_restore_requires_external_expected_digest(self):
        host = self.make_host()
        checkpoint = host.export_checkpoint()
        with self.assertRaises(AffectiveBindingError):
            VeraAffectiveRuntimeHost.restore_checkpoint(
                CONTRACT_PATH.read_text(encoding="utf-8"),
                json.loads(BINDING_PATH.read_text(encoding="utf-8")),
                checkpoint,
            )

    def test_untampered_checkpoint_roundtrips_against_external_expected_digest(self):
        host = self.make_host()
        host.observe(StimulusAppraisal(
            sexual_relevance=0.4,
            partner_relevance=0.4,
            relational_relevance=0.4,
            anticipation_cue=0.4,
            positive_valence=0.4,
            duration_ms=500,
            context_eligible=True,
        ))
        checkpoint = host.export_checkpoint()
        restored = self.restore(
            checkpoint,
            expected_checkpoint_sha256=checkpoint["checkpoint_sha256"],
        )
        self.assertEqual(
            restored.machine_interoception()["activation_intensity"],
            host.machine_interoception()["activation_intensity"],
        )
        self.assertEqual(restored.machine_interoception()["phenomenology"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
