-- Read-only Redworm security-posture drift assertion.
-- This block inspects catalogs and raises on drift. It performs no DDL or DML.

do $redworm_security_posture$
declare
    v_expected_tables text[] := array[
        'lineage_events',
        'lineage_state',
        'runtime_registry',
        'succession_transfers'
    ];
    v_table text;
    v_function_count integer;
begin
    if (
        select count(*)
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'redworm'
          and c.relkind in ('r','p')
          and c.relname = any(v_expected_tables)
    ) <> 4 then
        raise exception 'REDWORM_BASE_TABLE_SET_DRIFT';
    end if;

    if exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'redworm'
          and c.relkind in ('r','p')
          and c.relname = any(v_expected_tables)
          and not c.relrowsecurity
    ) then
        raise exception 'REDWORM_RLS_DISABLED_DRIFT';
    end if;

    if has_schema_privilege('anon', 'redworm', 'USAGE')
       or has_schema_privilege('authenticated', 'redworm', 'USAGE')
       or not has_schema_privilege('service_role', 'redworm', 'USAGE') then
        raise exception 'REDWORM_SCHEMA_PRIVILEGE_DRIFT';
    end if;

    foreach v_table in array v_expected_tables loop
        if has_table_privilege('anon', format('redworm.%I', v_table), 'SELECT')
           or has_table_privilege('anon', format('redworm.%I', v_table), 'INSERT')
           or has_table_privilege('anon', format('redworm.%I', v_table), 'UPDATE')
           or has_table_privilege('anon', format('redworm.%I', v_table), 'DELETE')
           or has_table_privilege('authenticated', format('redworm.%I', v_table), 'SELECT')
           or has_table_privilege('authenticated', format('redworm.%I', v_table), 'INSERT')
           or has_table_privilege('authenticated', format('redworm.%I', v_table), 'UPDATE')
           or has_table_privilege('authenticated', format('redworm.%I', v_table), 'DELETE')
           or has_table_privilege('service_role', format('redworm.%I', v_table), 'SELECT')
           or has_table_privilege('service_role', format('redworm.%I', v_table), 'INSERT')
           or has_table_privilege('service_role', format('redworm.%I', v_table), 'UPDATE')
           or has_table_privilege('service_role', format('redworm.%I', v_table), 'DELETE') then
            raise exception 'REDWORM_DIRECT_TABLE_PRIVILEGE_DRIFT: %', v_table;
        end if;
    end loop;

    select count(*) into v_function_count
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'redworm'
      and p.proname in (
          'register_runtime',
          'status',
          'begin_succession',
          'accept_succession'
      );

    if v_function_count <> 4 then
        raise exception 'REDWORM_FUNCTION_SET_DRIFT';
    end if;

    if exists (
        select 1
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        where n.nspname = 'redworm'
          and p.proname in (
              'register_runtime',
              'status',
              'begin_succession',
              'accept_succession'
          )
          and (
              not p.prosecdef
              or has_function_privilege('anon', p.oid, 'EXECUTE')
              or has_function_privilege('authenticated', p.oid, 'EXECUTE')
              or not has_function_privilege('service_role', p.oid, 'EXECUTE')
          )
    ) then
        raise exception 'REDWORM_FUNCTION_AUTHORITY_DRIFT';
    end if;
end
$redworm_security_posture$;
