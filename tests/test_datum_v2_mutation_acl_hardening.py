from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260921234500_harden_datum_v2_mutation_function_acls.sql"

MUTATORS = {
    "vera_register_datum_v2",
    "vera_mark_datum_referenced_v2",
    "vera_mark_datum_verified_v2",
    "vera_mark_datum_rejected_v2",
    "vera_mark_datum_unverifiable_v2",
}

READ_ONLY = {
    "vera_get_verified_datum_v2",
    "vera_validate_datum_v2",
}


class DatumV2MutationAclHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_every_mutator_revokes_client_execute_and_grants_service_role(self):
        for name in MUTATORS:
            self.assertIn(name, self.sql)
        self.assertEqual(5, self.sql.count("from public, anon, authenticated;"))
        self.assertEqual(5, self.sql.count("to service_role;"))

    def test_read_only_rpcs_are_outside_this_repair(self):
        for name in READ_ONLY:
            self.assertNotIn(name, self.sql)

    def test_no_broad_schema_or_table_grants(self):
        self.assertNotIn("grant usage on schema", self.sql)
        self.assertNotIn("grant select", self.sql)
        self.assertNotIn("grant insert", self.sql)
        self.assertNotIn("grant update", self.sql)
        self.assertNotIn("grant delete", self.sql)


if __name__ == "__main__":
    unittest.main()
