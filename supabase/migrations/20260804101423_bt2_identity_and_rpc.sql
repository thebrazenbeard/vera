alter table build_team_2.collectives
    add column if not exists abbreviation text not null default 'BT2',
    add column if not exists version_number integer not null default 2,
    add column if not exists designation_meaning text not null
        default 'Version 2 of the Build Team system; not the second of two build teams.';

alter table build_team_2.facets
    add column if not exists permanent_role text;

update build_team_2.collectives
set display_name = 'Build Team Two',
    abbreviation = 'BT2',
    version_number = 2,
    designation_meaning = 'Version 2 of the Build Team system; not the second of two build teams.',
    updated_at = now()
where slug = 'build-team-2';

update build_team_2.facets
set permanent_role = case when name = 'One' then 'BT2 Coordinator' else null end
where collective_id = (select id from build_team_2.collectives where slug = 'build-team-2');

alter table build_team_2.facets
    drop constraint if exists one_is_bt2_coordinator;

alter table build_team_2.facets
    add constraint one_is_bt2_coordinator check (
        (name = 'One' and permanent_role = 'BT2 Coordinator')
        or (name <> 'One' and permanent_role is null)
    );

create or replace function public.bt2_require_service_role()
returns void
language plpgsql
security definer
set search_path = pg_catalog
as $$
begin
    if coalesce(current_setting('request.jwt.claim.role', true), '') <> 'service_role' then
        raise exception 'BT2 RPC requires service_role' using errcode = '42501';
    end if;
end;
$$;

create or replace function public.bt2_load_recent_memory(p_slug text, p_limit integer default 40)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, build_team_2
as $$
declare
    result jsonb;
begin
    perform public.bt2_require_service_role();
    select coalesce(jsonb_agg(to_jsonb(x) order by x.created_at asc), '[]'::jsonb)
    into result
    from (
        select m.event_type, m.content, m.source_facets, m.authority_class, m.provenance, m.created_at
        from build_team_2.memory_events m
        join build_team_2.collectives c on c.id = m.collective_id
        where c.slug = p_slug
        order by m.created_at desc
        limit greatest(0, least(coalesce(p_limit, 40), 200))
    ) x;
    return result;
end;
$$;

create or replace function public.bt2_create_task(p_snapshot jsonb)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, build_team_2
as $$
declare
    collective uuid;
begin
    perform public.bt2_require_service_role();
    select id into strict collective from build_team_2.collectives
    where slug = p_snapshot->>'collective_slug';
    insert into build_team_2.tasks (id, collective_id, objective, snapshot_digest, snapshot, status)
    values (
        (p_snapshot->>'task_id')::uuid,
        collective,
        p_snapshot->>'objective',
        p_snapshot->>'snapshot_digest',
        p_snapshot->'snapshot',
        'analyzing'
    );
end;
$$;

create or replace function public.bt2_save_perspective(p_task_id uuid, p_perspective jsonb)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, build_team_2
as $$
begin
    perform public.bt2_require_service_role();
    insert into build_team_2.perspectives (task_id, facet_name, snapshot_digest, perspective)
    values (p_task_id, p_perspective->>'facet', p_perspective->>'snapshot_digest', p_perspective);
end;
$$;

create or replace function public.bt2_save_decision(p_task_id uuid, p_decision jsonb)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, build_team_2
as $$
begin
    perform public.bt2_require_service_role();
    insert into build_team_2.decisions (task_id, snapshot_digest, decision)
    values (p_task_id, p_decision->>'snapshot_digest', p_decision);
    update build_team_2.tasks
    set status = 'decided', final_output = p_decision, updated_at = now()
    where id = p_task_id;
end;
$$;

create or replace function public.bt2_append_memory(p_task_id uuid, p_event jsonb)
returns void
language plpgsql
security definer
set search_path = pg_catalog, public, build_team_2
as $$
declare
    collective uuid;
begin
    perform public.bt2_require_service_role();
    select collective_id into strict collective from build_team_2.tasks where id = p_task_id;
    insert into build_team_2.memory_events (
        collective_id, task_id, event_type, content, source_facets, authority_class, provenance, created_at
    ) values (
        collective, p_task_id, p_event->>'event_type', p_event->'content',
        coalesce(array(select jsonb_array_elements_text(p_event->'source_facets')), '{}'::text[]),
        p_event->>'authority_class', coalesce(p_event->'provenance', '{}'::jsonb),
        coalesce((p_event->>'created_at')::timestamptz, now())
    );
end;
$$;

revoke all on function public.bt2_require_service_role() from public, anon, authenticated;
revoke all on function public.bt2_load_recent_memory(text, integer) from public, anon, authenticated;
revoke all on function public.bt2_create_task(jsonb) from public, anon, authenticated;
revoke all on function public.bt2_save_perspective(uuid, jsonb) from public, anon, authenticated;
revoke all on function public.bt2_save_decision(uuid, jsonb) from public, anon, authenticated;
revoke all on function public.bt2_append_memory(uuid, jsonb) from public, anon, authenticated;

grant execute on function public.bt2_require_service_role() to service_role;
grant execute on function public.bt2_load_recent_memory(text, integer) to service_role;
grant execute on function public.bt2_create_task(jsonb) to service_role;
grant execute on function public.bt2_save_perspective(uuid, jsonb) to service_role;
grant execute on function public.bt2_save_decision(uuid, jsonb) to service_role;
grant execute on function public.bt2_append_memory(uuid, jsonb) to service_role;