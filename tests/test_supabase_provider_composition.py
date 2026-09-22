from scripts.validate_supabase_provider_composition import validate


def test_supabase_provider_composition_is_exact() -> None:
    report = validate()
    assert report["status"] == "PASS"
    assert report["provider_migrations"] == 97
    assert report["pending_migrations"] == 0
    assert report["last_provider_version"] == "20260921202237"
