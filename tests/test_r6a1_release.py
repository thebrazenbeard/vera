from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_r6a1_release import ROOT, TOKEN, validate


class R6A1ReleaseTests(unittest.TestCase):
    def copy(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "architecture" / "releases").mkdir(parents=True)
        shutil.copytree(
            ROOT / "architecture" / "releases" / TOKEN,
            root / "architecture" / "releases" / TOKEN,
        )
        (root / "docs").mkdir()
        shutil.copy2(
            ROOT / "docs" / "MAIN_MERGE_AUTHORITY_AUDIT_20260731.md",
            root / "docs" / "MAIN_MERGE_AUTHORITY_AUDIT_20260731.md",
        )
        return temporary, root

    def rehash(self, root: Path) -> None:
        release_dir = root / "architecture" / "releases" / TOKEN
        checksum_path = release_dir / "CHECKSUMS.sha256"
        lines = []
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            _, name = line.split(maxsplit=1)
            digest = hashlib.sha256((release_dir / name).read_bytes()).hexdigest()
            lines.append(f"{digest}  {name}")
        checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_valid(self):
        validate()

    def test_checksum_mutation(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / "README.md"
            path.write_text(path.read_text(encoding="utf-8") + "x", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_missing_file(self):
        temporary, root = self.copy()
        try:
            (root / "architecture" / "releases" / TOKEN / f"VERA_STATE_{TOKEN}.md").unlink()
            with self.assertRaisesRegex(ValueError, "checksum inventory"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_duplicate_json(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_SOURCE_BINDINGS_{TOKEN}.json"
            text = path.read_text(encoding="utf-8").replace(
                "{", '{"release_id":"duplicate",', 1
            )
            path.write_text(text, encoding="utf-8")
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_install_authority_promotion(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_SOURCE_BINDINGS_{TOKEN}.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["project_file_replacement_authorized"] = True
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "project_file_replacement_authorized"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_authority_provenance_promotion(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_SOURCE_BINDINGS_{TOKEN}.json"
            document = json.loads(path.read_text(encoding="utf-8"))
            document["authority_provenance"] = "VERIFIED"
            path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "authority provenance"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_stale_supabase_coordination_count_rejected(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_SUPABASE_PRESERVATION_{TOKEN}.md"
            text = path.read_text(encoding="utf-8").replace(
                "`public.vera_coordination_events`: 329 append-only rows",
                "`public.vera_coordination_events`: 20 append-only rows",
            )
            path.write_text(text, encoding="utf-8")
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "Supabase coordination count"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_stale_supabase_sequence_rejected(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_STATE_{TOKEN}.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "through sequence `351`", "through sequence `345`"
                ),
                encoding="utf-8",
            )
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "state authority audit sequence"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_missing_exact_main_assurance_rejected(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_STATE_{TOKEN}.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace("30629869594", "UNAVAILABLE"),
                encoding="utf-8",
            )
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "exact-main Integration Assurance"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_nonexistent_accompanying_sql_claim_rejected(self):
        temporary, root = self.copy()
        try:
            path = root / "architecture" / "releases" / TOKEN / f"VERA_SUPABASE_PRESERVATION_{TOKEN}.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nThe accompanying SQL file is a draft only.\n",
                encoding="utf-8",
            )
            self.rehash(root)
            with self.assertRaisesRegex(ValueError, "nonexistent accompanying SQL"):
                validate(root)
        finally:
            temporary.cleanup()

    def test_stale_external_authority_audit_rejected(self):
        temporary, root = self.copy()
        try:
            path = root / "docs" / "MAIN_MERGE_AUTHORITY_AUDIT_20260731.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "through sequence `351`", "through sequence `345`"
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "main merge authority audit sequence"):
                validate(root)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
