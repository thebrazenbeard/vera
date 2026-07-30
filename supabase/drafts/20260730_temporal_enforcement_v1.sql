begin;

create table if not exists public.vera_temporal_events_v1 (
    temporal_event_id uuid primary key default gen_random_uuid(),
    event_sequence bigint generated always as identity unique,
    project_id text not null default 'vera-reciprocal-agency-environment',
    workstream text not null check (
        workstream in (
            'workstream/time',
            'workstream/memory',
            'workstream/initiatives',
            'workstream/integration'
        )
    ),
    scope_instance_id text not null,
    scope_stability text not null check (scope_stability in ('STABLE', 'EPHEMERAL')),
    provider_conversation_id text,
    provider_branch_id text,
    session_id text not null,
    checkpoint_id text,
    event_kind text not null check (
        event_kind in (
            'ENTRY',
            'RETRIEVAL',
            'MATERIAL_TRANSITION',
            'HANDOFF',
            'UNANCHORED'
        )
    ),
    anchor_status text not null check (anchor_status in ('ANCHORED', 'UNANCHORED')),
    event_time timestamptz,
    state_time timestamptz,
    record_time timestamptz not null default clock_timestamp(),
    retrieval_time timestamptz,
    event_time_precision text not null check (
        event_time_precision in ('EXACT', 'BOUNDED', 'APPROXIMATE', 'UNKNOWN')
    ),
    event_time_lower_bound timestamptz,
    event_time_upper_bound timestamptz,
    idempotency_key text not null,
    supersedes_event_id uuid references public.vera_temporal_events_v1(temporal_event_id),
    source_evidence jsonb not null default '[]'::jsonb,
    limitations jsonb not null default '[]'::jsonb,
    payload jsonb not null default '{}'::jsonb,
    constraint vera_temporal_events_v1_nonblank check (
        btrim(project_id) <> ''
        and btrim(workstream) <> ''
        and btrim(scope_instance_id) <> ''
        and btrim(session_id) <> ''
        and btrim(idempotency_key) <> ''
    ),
    constraint vera_temporal_events_v1_scope_identity check (
        (
            scope_stability = 'STABLE'
            and provider_conversation_id is not null
            and btrim(provider_conversation_id) <> ''
            and provider_branch_id is not null
            and btrim(provider_branch_id) <> ''
        )
        or
        (
            scope_stability = 'EPHEMERAL'
            and provider_conversation_id is null
            and provider_branch_id is null
        )
    ),
    constraint vera_temporal_events_v1_identity_distinctness check (
        session_id <> scope_instance_id
        and (checkpoint_id is null or checkpoint_id <> '')
        and (checkpoint_id is null or checkpoint_id <> session_id)
        and (checkpoint_id is null or checkpoint_id <> scope_instance_id)
    ),
    constraint vera_temporal_events_v1_precision_shape check (
        (
            event_time_precision = 'EXACT'
            and event_time is not null
            and event_time_lower_bound is null
            and event_time_upper_bound is null
        )
        or
        (
            event_time_precision = 'BOUNDED'
            and event_time is not null
            and event_time_lower_bound is not null
            and event_time_upper_bound is not null
            and event_time_lower_bound <= event_time
            and event_time <= event_time_upper_bound
        )
        or
        (
            event_time_precision = 'APPROXIMATE'
            and event_time is not null
            and event_time_lower_bound is null
            and event_time_upper_bound is null
        )
        or
        (
            event_time_precision = 'UNKNOWN'
            and event_time is null
            and event_time_lower_bound is null
            and event_time_upper_bound is null
        )
    ),
    constraint vera_temporal_events_v1_json_shapes check (
        jsonb_typeof(source_evidence) = 'array'
        and jsonb_typeof(limitations) = 'array'
        and jsonb_typeof(payload) = 'object'
    ),
    constraint vera_temporal_events_v1_unanchored_has_reason check (
        anchor_status = 'ANCHORED'
        or jsonb_array_length(limitations) > 0
    ),
    constraint vera_temporal_events_v1_no_self_supersession check (
        supersedes_event_id is null or supersedes_event_id <> temporal_event_id
    )
);

comment on table public.vera_temporal_events_v1 is
'Append-only temporal evidence for V.E.R.A. This table records exposed external evidence and explicit UNANCHORED failures. It does not prove hidden activity, uninterrupted awareness, waiting, identity continuity, or automatic ChatGPT hooks.';

comment on column public.vera_temporal_events_v1.record_time is
'Database-assigned persistence time. Callers cannot preserve a supplied value.';

create unique index if not exists vera_temporal_events_v1_idempotency_idx
    on public.vera_temporal_events_v1(project_id, workstream, idempotency_key);

create unique index if not exists vera_temporal_events_v1_one_successor_idx
    on public.vera_temporal_events_v1(supersedes_event_id)
    where supersedes_event_id is not null;

create index if not exists vera_temporal_events_v1_scope_sequence_idx
    on public.vera_temporal_events_v1(project_id, workstream, scope_instance_id, event_sequence);

create or replace function public.vera_temporal_events_v1_prepare_insert()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    parent_row public.vera_temporal_events_v1%rowtype;
begin
    new.record_time := clock_timestamp();

    if new.supersedes_event_id is not null then
        select *
          into parent_row
          from public.vera_temporal_events_v1
         where temporal_event_id = new.supersedes_event_id
         for update;

        if not found then
            raise exception using
                errcode = '23503',
                message = 'superseded temporal event does not exist';
        end if;

        if parent_row.project_id <> new.project_id
           or parent_row.workstream <> new.workstream
           or parent_row.scope_instance_id <> new.scope_instance_id then
            raise exception using
                errcode = '23514',
                message = 'temporal supersession may not cross project, workstream, or scope';
        end if;
    end if;

    return new;
end;
$$;

create or replace function public.vera_temporal_events_v1_block_mutation()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
    raise exception using
        errcode = '55000',
        message = 'vera_temporal_events_v1 is append-only';
end;
$$;

drop trigger if exists vera_temporal_events_v1_prepare_insert on public.vera_temporal_events_v1;
create trigger vera_temporal_events_v1_prepare_insert
before insert on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_prepare_insert();

drop trigger if exists vera_temporal_events_v1_no_update on public.vera_temporal_events_v1;
create trigger vera_temporal_events_v1_no_update
before update on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_block_mutation();

drop trigger if exists vera_temporal_events_v1_no_delete on public.vera_temporal_events_v1;
create trigger vera_temporal_events_v1_no_delete
before delete on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_block_mutation();

alter table public.vera_temporal_events_v1 enable row level security;

revoke all on table public.vera_temporal_events_v1 from public, anon, authenticated;
revoke all on sequence public.vera_temporal_events_v1_event_sequence_seq from public, anon, authenticated;

grant select, insert on table public.vera_temporal_events_v1 to service_role;
grant usage, select on sequence public.vera_temporal_events_v1_event_sequence_seq to service_role;
revoke update, delete, truncate, references, trigger on table public.vera_temporal_events_v1 from service_role;

drop policy if exists vera_temporal_events_v1_no_client_access on public.vera_temporal_events_v1;
create policy vera_temporal_events_v1_no_client_access
on public.vera_temporal_events_v1
as restrictive
for all
to anon, authenticated
using (false)
with check (false);

commit;
