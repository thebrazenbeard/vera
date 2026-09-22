alter function build_team_2.prevent_memory_event_mutation()
    set search_path = pg_catalog;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'collectives',
        'facets',
        'tasks',
        'perspectives',
        'decisions',
        'memory_events'
    ]
    loop
        execute format('drop policy if exists deny_client_access on build_team_2.%I', table_name);
        execute format(
            'create policy deny_client_access on build_team_2.%I '
            'for all to anon, authenticated using (false) with check (false)',
            table_name
        );
    end loop;
end;
$$;