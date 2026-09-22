from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260922190100_harden_datum_v2_mutation_function_acls.sql"

MUTATOR_SIGNATURES = (
    "public.vera_register_datum_v2(text,text,text,text,text,jsonb,jsonb,text[],jsonb,text,text)",
    "public.vera_mark_datum_referenced_v2(uuid)",
    "public.vera_mark_datum_verified_v2(uuid,jsonb,text,text,jsonb,uuid,text[],jsonb)",
    "public.vera_mark_datum_rejected_v2(uuid,text,jsonb)",
    "public.vera_mark_datum_unverifiable_v2(uuid,text,jsonb)",
)

READ_ONLY = {
    "vera_get_verified_datum_v2",
    "vera_validate_datum_v2",
}

CLIENT_ROLES = {"public", "anon", "authenticated"}


def _statements(sql: str) -> list[str]:
    without_comments = "\n".join(
        line.split("--", 1)[0] for line in sql.lower().splitlines()
    )
    return [
        re.sub(r"\\s+", "", statement)
        for statement in without_comments.split(";")
        if statement.strip()
    ]


def _validate_acl_sql(sql: str) -> list[str]:
    statements = _statements(sql)
    errors: list[str] = []

    for signature in MUTATOR_SIGNATURES:
        compact = re.sub(r"\\s+", "", signature.lower())
        expected_revoke = (
            f"revokeallonfunction{compact}frompublic,anon,authenticated"
        )
        expected_grant = f"grantexecuteonfunction{compact}toservice_role"
        if statements.count(expected_revoke) != 1:
            errors.append(f"revoke binding mismatch: {signature}")
        if statements.count(expected_grant) != 1:
            errors.append(f"service_role grant binding mismatch: {signature}")

    for statement in statements:
        if not statement.startswith("grant"):
            continue
        function_scope = any(
            marker in statement
            for marker in (
                "onfunction",
                "onroutine",
                "onprocedure",
                "onallfunctionsinschema",
                "onallroutinesinschema",
                "onallproceduresinschema",
            )
        )
        if not function_scope:
            continue
        if "to" not in statement:
            errors.append(f"unparseable function grant: {statement}")
            continue
        granted_roles = set(statement.rsplit("to", 1)[-1].split(","))
        if granted_roles & CLIENT_ROLES:
            errors.append(f"client function grant forbidden: {statement}")

    return errors


class DatumV2MutationAclHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_exact_mutator_signature_acl_bindings(self):
        self.assertEqual([], _validate_acl_sql(self.sql))

    def test_oracle_rejects_duplicate_wrong_signature_substitution(self):
        statements = _statements(self.sql)
        first = re.sub(r"\\s+", "", MUTATOR_SIGNATURES[0].lower())
        second = re.sub(r"\\s+", "", MUTATOR_SIGNATURES[1].lower())
        hostile = ";".join(
            statement.replace(second, first)
            for statement in statements
        ) + ";"
        failures = _validate_acl_sql(hostile)
        self.assertTrue(
            any("binding mismatch" in failure for failure in failures),
            failures,
        )

    def test_oracle_rejects_extra_client_execute_grant(self):
        hostile = self.sql + """
grant execute on function public.vera_mark_datum_referenced_v2(uuid)
  to authenticated;
"""
        failures = _validate_acl_sql(hostile)
        self.assertTrue(
            any("client function grant forbidden" in failure for failure in failures),
            failures,
        )

    def test_oracle_rejects_grant_all_on_function_to_client(self):
        hostile = self.sql + """
grant all on function public.vera_mark_datum_referenced_v2(uuid)
  to authenticated;
"""
        failures = _validate_acl_sql(hostile)
        self.assertTrue(
            any("client function grant forbidden" in failure for failure in failures),
            failures,
        )

    def test_oracle_rejects_schema_wide_function_execute_to_client(self):
        hostile = self.sql + """
grant execute on all functions in schema public
  to authenticated;
"""
        failures = _validate_acl_sql(hostile)
        self.assertTrue(
            any("client function grant forbidden" in failure for failure in failures),
            failures,
        )

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
