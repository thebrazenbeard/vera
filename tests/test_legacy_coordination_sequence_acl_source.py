from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260919162500_revoke_legacy_coordination_sequence_client_privileges.sql"
VALIDATION = ROOT / "supabase" / "tests" / "validate_legacy_coordination_sequence_privileges.sql"
TARGET = "public.vera_coordination_events_event_sequence_seq"


class LegacyCoordinationSequenceAclSourceTests(unittest.TestCase):
    def test_migration_exists_and_is_transactional(self):
        self.assertTrue(MIGRATION.is_file())
        text = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertTrue(text.strip().startswith("begin;"))
        self.assertTrue(text.strip().endswith("commit;"))

    def test_migration_revokes_only_unnecessary_client_sequence_privileges(self):
        text = MIGRATION.read_text(encoding="utf-8").lower()
        normalized = " ".join(text.split())
        self.assertIn(f"revoke all privileges on sequence {TARGET}", normalized)
        self.assertIn("from public, anon, authenticated;", normalized)
        self.assertNotIn("from service_role", normalized)
        self.assertNotIn("from postgres", normalized)
    def test_migration_does_not_grant_or_mutate_table_data(self):
        text = MIGRATION.read_text(encoding="utf-8").lower()
        self.assertNotIn("grant ", text)
        self.assertNotIn("insert ", text)
        self.assertNotIn("update ", text)
        self.assertNotIn("delete ", text)
        self.assertNotIn("drop ", text)
        self.assertNotIn("alter table", text)

    def test_validation_query_checks_client_roles_and_preserves_service_role(self):
        self.assertTrue(VALIDATION.is_file())
        text = VALIDATION.read_text(encoding="utf-8").lower()
        self.assertIn(TARGET, text)
        for role in ("anon", "authenticated", "service_role"):
            self.assertIn(role, text)
        for privilege in ("usage", "select", "update"):
            self.assertIn(privilege, text)
        self.assertIn("expected_client_privileges_revoked", text)
        self.assertIn("expected_service_role_preserved", text)


if __name__ == "__main__":
    unittest.main()
