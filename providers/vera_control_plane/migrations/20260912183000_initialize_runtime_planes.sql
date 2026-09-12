-- Vera Control Plane provider substrate: runtime-owned logical planes.
-- Source owner: thebrazenbeard/vera. Deployment/current-route authority remains separate.
-- This migration creates no application tables and grants no runtime data-plane capability.

DO $$
DECLARE
    role_name text;
BEGIN
    FOREACH role_name IN ARRAY ARRAY[
        'vera_runtime_evidence_reader',
        'vera_runtime_state_proposer',
        'vera_cohesion_admitter',
        'vera_effect_executor',
        'vera_control_verifier',
        'vera_migration_operator',
        'vera_runtime_schema_owner'
    ]
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
            EXECUTE format(
                'CREATE ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS',
                role_name
            );
        ELSE
            EXECUTE format(
                'ALTER ROLE %I NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS',
                role_name
            );
        END IF;
    END LOOP;
END
$$;

ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner
    REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner
    REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner
    REVOKE USAGE ON TYPES FROM PUBLIC, anon, authenticated, service_role;

DO $$
DECLARE
    schema_name text;
BEGIN
    FOREACH schema_name IN ARRAY ARRAY[
        'vera_evidence',
        'vera_state',
        'vera_receipts',
        'vera_sync'
    ]
    LOOP
        EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I AUTHORIZATION vera_runtime_schema_owner', schema_name);
        EXECUTE format(
            'REVOKE ALL ON SCHEMA %I FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'REVOKE ALL ON ALL TABLES IN SCHEMA %I FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'REVOKE ALL ON ALL SEQUENCES IN SCHEMA %I FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'REVOKE ALL ON ALL FUNCTIONS IN SCHEMA %I FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner IN SCHEMA %I REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner IN SCHEMA %I REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner IN SCHEMA %I REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES FOR ROLE vera_runtime_schema_owner IN SCHEMA %I REVOKE USAGE ON TYPES FROM PUBLIC, anon, authenticated, service_role',
            schema_name
        );
    END LOOP;
END
$$;
