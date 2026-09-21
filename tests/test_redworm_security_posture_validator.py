from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "supabase" / "tests" / "validate_redworm_security_posture.sql"


class RedwormSecurityPostureValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = VALIDATOR.read_text(encoding="utf-8").lower()

    def test_extra_base_table_cannot_hide_outside_expected_names(self):
        self.assertIn("array_agg(c.relname order by c.relname)", self.text)
        self.assertIn("v_actual_tables is distinct from v_expected_tables", self.text)
        self.assertIn("foreach v_table in array v_actual_tables", self.text)
        self.assertNotIn("c.relname = any(v_expected_tables)", self.text)

    def test_exact_callable_surface_is_signature_bound(self):
        for signature in (
            "redworm.accept_succession(uuid,uuid,integer,text)",
            "redworm.begin_succession(uuid,integer,text,text,text)",
            "redworm.register_runtime(text,jsonb)",
            "redworm.status(uuid)",
        ):
            self.assertIn(signature, self.text)
        self.assertIn("p.oid::regprocedure::text", self.text)
        self.assertIn("v_actual_functions is distinct from v_expected_functions", self.text)
        self.assertNotIn("p.proname in", self.text)

    def test_security_definer_owner_search_path_and_body_are_bound(self):
        self.assertIn("r.rolname <> 'postgres'", self.text)
        self.assertIn("not p.prosecdef", self.text)
        self.assertIn(
            "p.proconfig is distinct from array['search_path=redworm, pg_temp']::text[]",
            self.text,
        )
        self.assertIn("md5(pg_get_functiondef(p.oid))", self.text)
        for digest in (
            "6b088196ca443f7a7419ed2f08c2bf4a",
            "c9ad15a7d8a1dbf574a5eb17d5901c10",
            "75ec870dc6e49177fcd7d13afbe55d2b",
            "94c02a394bf2df80b1bc40f8e692f9d0",
        ):
            self.assertIn(digest, self.text)

    def test_client_and_backend_direct_table_grants_are_checked(self):
        for role in ("anon", "authenticated", "service_role"):
            for privilege in ("select", "insert", "update", "delete"):
                self.assertIn(
                    f"has_table_privilege('{role}'",
                    self.text,
                )
                self.assertIn(f"'{privilege.upper()}'".lower(), self.text)

    def test_validator_remains_read_only(self):
        for token in (
            "\ninsert ",
            "\nupdate ",
            "\ndelete ",
            "\nalter ",
            "\ncreate ",
            "\ndrop ",
            "\ngrant ",
            "\nrevoke ",
        ):
            self.assertNotIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
