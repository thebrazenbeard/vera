from pathlib import Path
from hashlib import sha256
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260814143945_datum_lifecycle_v2_rebuild.sql"
RECORD = ROOT / "docs" / "DATUM_V2_PROVIDER_SOURCE_CUSTODY_20260919.md"
EXPECTED_BYTES = 21520
EXPECTED_SHA256 = "079c34aa9ca338d70172fea56cd5118859b9ed9820ed06789c046cff48afeae5"


class DatumV2ProviderSourceCustodyTests(unittest.TestCase):
    def test_exact_provider_statement_bytes_are_bound(self):
        data = MIGRATION.read_bytes()
        self.assertEqual(EXPECTED_BYTES, len(data))
        self.assertEqual(EXPECTED_SHA256, sha256(data).hexdigest())
        self.assertEqual(0, data.count(b"\r"))
    def test_recovered_source_contains_datum_v2_objects(self):
        text = MIGRATION.read_text(encoding="utf-8")
        required = (
            "create or replace function public.vera_validate_datum_v2()",
            "create or replace view public.vera_verified_datum_heads_v2 as",
            "create or replace view public.vera_active_datum_index_v2 as",
            "create or replace view public.vera_inactive_datum_archive_v2 as",
            "create or replace function public.vera_register_datum_v2(",
            "create or replace function public.vera_mark_datum_referenced_v2(",
            "create or replace function public.vera_mark_datum_verified_v2(",
            "create or replace function public.vera_get_verified_datum_v2(",
        )
        for marker in required:
            self.assertIn(marker, text)

    def test_source_record_preserves_provider_applied_vs_git_custody_distinction(self):
        text = RECORD.read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        self.assertIn("20260814143945", text)
        self.assertIn("datum_lifecycle_v2_rebuild", text)
        self.assertIn(str(EXPECTED_BYTES), text)
        self.assertIn(EXPECTED_SHA256, text)
        self.assertIn("PROVIDER_APPLIED_SOURCE_RECOVERED", text)
        self.assertIn("GIT_CUSTODY_ONLY", text)
        self.assertIn("does not authorize re-application", normalized.lower())
        self.assertIn("does not prove current runtime semantics", normalized.lower())

    def test_checkout_rule_preserves_provider_lf_bytes(self):
        attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "supabase/migrations/20260814143945_datum_lifecycle_v2_rebuild.sql text eol=lf",
            attrs,
        )


if __name__ == "__main__":
    unittest.main()
