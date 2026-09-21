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
    v_actual_tables text[];
    v_expected_functions text[] := array[
        'redworm.accept_succession(uuid,uuid,integer,text)',
        'redworm.begin_succession(uuid,integer,text,text,text)',
        'redworm.register_runtime(text,jsonb)',
        'redworm.status(uuid)'
    ];
    v_actual_functions text[];
    v_table text;
begin
    select coalesce(array_agg(c.relname order by c.relname), array[]::text[])
      into v_actual_tables
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'redworm'
      and c.relkind in ('r','p');

    if v_actual_tables is distinct from v_expected_tables then
        raise exception 'REDWORM_BASE_TABLE_SET_DRIFT: actual=% expected=%',
            v_actual_tables, v_expected_tables;
    end if;

    if exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'redworm'
          and c.relkind in ('r','p')
          and not c.relrowsecurity
    ) then
        raise exception 'REDWORM_RLS_DISABLED_DRIFT';
    end if;

    if has_schema_privilege('anon', 'redworm', 'USAGE')
       or has_schema_privilege('authenticated', 'redworm', 'USAGE')
       or not has_schema_privilege('service_role', 'redworm', 'USAGE') then
        raise exception 'REDWORM_SCHEMA_PRIVILEGE_DRIFT';
    end if;

    foreach v_table in array v_actual_tables loop
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

    select coalesce(array_agg(p.oid::regprocedure::text order by p.oid::regprocedure::text), array[]::text[])
      into v_actual_functions
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'redworm';

    if v_actual_functions is distinct from v_expected_functions then
        raise exception 'REDWORM_FUNCTION_SET_DRIFT: actual=% expected=%',
            v_actual_functions, v_expected_functions;
    end if;

    if exists (
        select 1
        from pg_proc p
        join pg_namespace n on n.oid = p.pronamespace
        join pg_roles r on r.oid = p.proowner
        where n.nspname = 'redworm'
          and (
              r.rolname <> 'postgres'
              or not p.prosecdef
              or p.proconfig is distinct from array['search_path=redworm, pg_temp']::text[]
              or md5(pg_get_functiondef(p.oid)) is distinct from
                case p.oid::regprocedure::text
                  when 'redworm.accept_succession(uuid,uuid,integer,text)'
                    then '6b088196ca443f7a7419ed2f08c2bf4a'
                  when 'redworm.begin_succession(uuid,integer,text,text,text)'
                    then 'c9ad15a7d8a1dbf574a5eb17d5901c10'
                  when 'redworm.register_runtime(text,jsonb)'
                    then '75ec870dc6e49177fcd7d13afbe55d2b'
                  when 'redworm.status(uuid)'
                    then '94c02a394bf2df80b1bc40f8e692f9d0'
                  else null
                end
              or has_function_privilege('anon', p.oid, 'EXECUTE')
              or has_function_privilege('authenticated', p.oid, 'EXECUTE')
              or not has_function_privilege('service_role', p.oid, 'EXECUTE')
          )
    ) then
        raise exception 'REDWORM_FUNCTION_AUTHORITY_DRIFT';
    end if;
end
$redworm_security_posture$;
