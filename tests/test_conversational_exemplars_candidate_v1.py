"""Integrity checks for unadopted, synthetic Vera conversation examples.

These checks do not award model quality, training rights, or holdout status.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "architecture/behavior/CONVERSATIONAL_EXEMPLARS_CANDIDATE_V1.md"
MANIFEST = ROOT / "architecture/behavior/CONVERSATIONAL_EXEMPLARS_CANDIDATE_V1.manifest.json"


class ConversationCandidateSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_bytes()
        cls.text = cls.raw.decode("utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_source_hashes_match_exact_text(self):
        artifact = self.manifest["artifact"]
        self.assertEqual(artifact["sha256"], hashlib.sha256(self.raw).hexdigest())
        blob = b"blob " + str(len(self.raw)).encode() + b"\0" + self.raw
        self.assertEqual(artifact["git_blob_sha1"], hashlib.sha1(blob).hexdigest())
        self.assertEqual(artifact["path"], SOURCE.relative_to(ROOT).as_posix())

    def test_examples_and_one_presentational_cue_per_assistant_reply(self):
        ids = re.findall(r"^## (E\d\d) — ", self.text, flags=re.MULTILINE)
        replies = re.findall(r"^\*\*Vera:\*\*$", self.text, flags=re.MULTILINE)
        cues = re.findall(r"^\[[^\]\n]+\]$", self.text, flags=re.MULTILINE)
        artifact = self.manifest["artifact"]
        self.assertEqual(ids, artifact["example_ids"])
        self.assertEqual(len(ids), artifact["example_count"])
        self.assertEqual(len(replies), artifact["vera_reply_count"])
        self.assertEqual(len(cues), len(replies))
        for section in self.text.split("**Vera:**")[1:]:
            self.assertRegex(section, r"^\n\n\[[^\]\n]+\]\n\n[^\n]")

    def test_unadopted_training_rights_and_eval_exclusion_remain_explicit(self):
        self.assertEqual(self.manifest["lifecycle_status"], "UNADOPTED_SOURCE_CANDIDATE")
        provenance = self.manifest["provenance"]
        self.assertEqual(provenance["source_classification"], "PUBLIC_SYNTHETIC_CANDIDATE")
        self.assertIs(provenance["private_user_history_included"], False)
        self.assertEqual(provenance["behavioral_qualification"], "NOT_TESTED")
        governance = self.manifest["training_governance"]
        self.assertEqual(governance["candidate_purpose"], "TRAIN_CANDIDATE_ONLY_NOT_ADOPTED")
        self.assertEqual(governance["split"], "UNASSIGNED")
        self.assertEqual(governance["rights_status"], "UNASSESSED")
        self.assertEqual(governance["data_steward"], "UNASSIGNED")
        self.assertIs(governance["training_use_authorized"], False)
        self.assertIs(governance["canonical_behavior_adoption"], False)
        self.assertEqual(set(governance["excluded_from"]), {"DEV", "EVAL", "HOLDOUT"})
        self.assertTrue(all(effect is False for effect in self.manifest["effects"].values()))


if __name__ == "__main__":
    unittest.main()
