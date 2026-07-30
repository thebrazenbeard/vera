begin;

create extension if not exists pgcrypto with schema extensions;

create or replace function public.vera_temporal_source_evidence_valid_v1(value jsonb)
returns boolean
language sql
immutable
set search_path = pg_catalog
as $$
    select case
        when jsonb_typeof(value) <> 'array' then false
        else not exists (
            select 1
              from jsonb_array_elements(value) as item
             where jsonb_typeof(item) <> 'object'
                or coalesce(btrim(item->>'system'), '') not in (
                    'HOST', 'SUPABASE', 'BASIC_MEMORY', 'GITHUB', 'OTHER'
                )
                or coalesce(btrim(item->>'operation'), '') = ''
                or coalesce(btrim(item->>'reference_id'), '') = ''
                or coalesce(item->>'subject_hash', '') !~ '^[0-9a-f]{64}$'
       )
    end;
$$;

create or replace function public.vera_temporal_string_array_valid_v1(value jsonb)
returns boolean
language sql
immutable
set search_path = pg_catalog
as $$
    select case
        when jsonb_typeof(value) <> 'array' then false
        else not exists (
            select 1
              from jsonb_array_elements(value) as item
             where jsonb_typeof(item) <> 'string'
                or btrim(item #>> '{}') = ''
        )
    end;
$$;

create table public.vera_temporal_events_v1 (
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
    anchor_key text not null,
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
    logical_hash text not null,
    supersedes_event_id uuid references public.vera_temporal_events_v1(temporal_event_id),
    source_evidence jsonb not null default '[]'::jsonb,
    limitations jsonb not null default '[]'::jsonb,
    payload jsonb not null default '{}'::jsonb,
    constraint vera_temporal_events_v1_nonblank check (
        btrim(project_id) <> ''
        and btrim(workstream) <> ''
        and btrim(anchor_key) <> ''
        and btrim(scope_instance_id) <> ''
        and btrim(session_id) <> ''
        and btrim(idempotency_key) <> ''
    ),
    constraint vera_temporal_events_v1_logical_hash check (
        logical_hash ~ '^[0-9a-f]{64}$'
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
        and (checkpoint_id is null or btrim(checkpoint_id) <> '')
        and (checkpoint_id is null or checkpoint_id <> session_id)
        and (checkpoint_id is null or checkpoint_id <> scope_instance_id)
        and (checkpoint_id is null or checkpoint_id is distinct from provider_conversation_id)
        and (checkpoint_id is null or checkpoint_id is distinct from provider_branch_id)
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
    constraint vera_temporal_events_v1_status_kind_consistency check (
        (event_kind = 'UNANCHORED' and anchor_status = 'UNANCHORED')
        or (event_kind <> 'UNANCHORED' and anchor_status = 'ANCHORED')
    ),
    constraint vera_temporal_events_v1_evidence_and_limitations check (
        public.vera_temporal_source_evidence_valid_v1(source_evidence)
        and public.vera_temporal_string_array_valid_v1(limitations)
        and (
            (anchor_status = 'ANCHORED' and jsonb_array_length(source_evidence) > 0)
            or (anchor_status = 'UNANCHORED' and jsonb_array_length(limitations) > 0)
        )
    ),
    constraint vera_temporal_events_v1_json_shapes check (
        jsonb_typeof(payload) = 'object'
    ),
    constraint vera_temporal_events_v1_retrieval_order check (
        retrieval_time is null or retrieval_time <= record_time
    ),
    constraint vera_temporal_events_v1_no_self_supersession check (
        supersedes_event_id is null or supersedes_event_id <> temporal_event_id
    )
);

comment on table public.vera_temporal_events_v1 is
'Append-only temporal evidence for V.E.R.A. Evidence envelopes are bound into a server-computed logical hash but their external authenticity must be verified by the runtime adapter. This table does not prove hidden activity, uninterrupted awareness, waiting, identity continuity, or automatic ChatGPT hooks.';

comment on column public.vera_temporal_events_v1.record_time is
'Database-assigned persistence time. Callers cannot preserve a supplied value.';

comment on column public.vera_temporal_events_v1.logical_hash is
'Server-computed SHA-256 of the logical event content, excluding generated identity, sequence, record_time, and idempotency key.';

create unique index vera_temporal_events_v1_idempotency_idx
    on public.vera_temporal_events_v1(project_id, workstream, idempotency_key);

create unique index vera_temporal_events_v1_root_idx
    on public.vera_temporal_events_v1(project_id, workstream, scope_instance_id, anchor_key)
    where supersedes_event_id is null;

create unique index vera_temporal_events_v1_one_successor_idx
    on public.vera_temporal_events_v1(supersedes_event_id)
    where supersedes_event_id is not null;

create index vera_temporal_events_v1_scope_sequence_idx
    on public.vera_temporal_events_v1(
        project_id, workstream, scope_instance_id, anchor_key, event_sequence
    );

create or replace function public.vera_temporal_event_logical_hash_v1(
    p_project_id text,
    p_workstream text,
    p_anchor_key text,
    p_scope_instance_id text,
    p_scope_stability text,
    p_provider_conversation_id text,
    p_provider_branch_id text,
    p_session_id text,
    p_checkpoint_id text,
    p_event_kind text,
    p_anchor_status text,
    p_event_time timestamptz,
    p_state_time timestamptz,
    p_retrieval_time timestamptz,
    p_event_time_precision text,
    p_event_time_lower_bound timestamptz,
    p_event_time_upper_bound timestamptz,
    p_supersedes_event_id uuid,
    p_source_evidence jsonb,
    p_limitations jsonb,
    p_payload jsonb
)
returns text
language sql
immutable
set search_path = pg_catalog, extensions
as $$
    select encode(
        extensions.digest(
            convert_to(
                jsonb_build_object(
                    'project_id', p_project_id,
                    'workstream', p_workstream,
                    'anchor_key', p_anchor_key,
                    'scope_instance_id', p_scope_instance_id,
                    'scope_stability', p_scope_stability,
                    'provider_conversation_id', p_provider_conversation_id,
                    'provider_branch_id', p_provider_branch_id,
                    'session_id', p_session_id,
                    'checkpoint_id', p_checkpoint_id,
                    'event_kind', p_event_kind,
                    'anchor_status', p_anchor_status,
                    'event_time', p_event_time,
                    'state_time', p_state_time,
                    'retrieval_time', p_retrieval_time,
                    'event_time_precision', p_event_time_precision,
                    'event_time_lower_bound', p_event_time_lower_bound,
                    'event_time_upper_bound', p_event_time_upper_bound,
                    'supersedes_event_id', p_supersedes_event_id,
                    'source_evidence', p_source_evidence,
                    'limitations', p_limitations,
                    'payload', p_payload
                )::text,
                'UTF8'
            ),
            'sha256'
        ),
        'hex'
    );
$$;

create or replace function public.vera_temporal_events_v1_prepare_insert()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, extensions, pg_temp
as $$
declare
    parent_row public.vera_temporal_events_v1%rowtype;
begin
    new.record_time := clock_timestamp();
    new.logical_hash := public.vera_temporal_event_logical_hash_v1(
        new.project_id,
        new.workstream,
        new.anchor_key,
        new.scope_instance_id,
        new.scope_stability,
        new.provider_conversation_id,
        new.provider_branch_id,
        new.session_id,
        new.checkpoint_id,
        new.event_kind,
        new.anchor_status,
        new.event_time,
        new.state_time,
        new.retrieval_time,
        new.event_time_precision,
        new.event_time_lower_bound,
        new.event_time_upper_bound,
        new.supersedes_event_id,
        new.source_evidence,
        new.limitations,
        new.payload
    );

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
           or parent_row.scope_instance_id <> new.scope_instance_id
           or parent_row.anchor_key <> new.anchor_key then
            raise exception using
                errcode = '23514',
                message = 'temporal supersession may not cross project, workstream, scope, or anchor key';
        end if;
    end if;

    return new;
end;
$$;

create or replace function public.vera_temporal_events_v1_block_mutation()
returns trigger
language plpgsql
security definer
set search_path = pg_catalog, public, pg_temp
as $$
begin
    raise exception using
        errcode = '55000',
        message = 'vera_temporal_events_v1 is append-only';
end;
$$;

create trigger vera_temporal_events_v1_prepare_insert
before insert on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_prepare_insert();

create trigger vera_temporal_events_v1_no_update
before update on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_block_mutation();

create trigger vera_temporal_events_v1_no_delete
before delete on public.vera_temporal_events_v1
for each row execute function public.vera_temporal_events_v1_block_mutation();

create or replace function public.append_vera_temporal_event_v1(p_event jsonb)
returns table (
    temporal_event_id uuid,
    event_sequence bigint,
    record_time timestamptz,
    logical_hash text,
    created boolean
)
language plpgsql
security definer
set search_path = pg_catalog, public, extensions, pg_temp
as $$
declare
    v_project_id text := coalesce(nullif(btrim(p_event->>'project_id'), ''), 'vera-reciprocal-agency-environment');
    v_workstream text := p_event->>'workstream';
    v_anchor_key text := p_event->>'anchor_key';
    v_scope_instance_id text := p_event->>'scope_instance_id';
    v_scope_stability text := p_event->>'scope_stability';
    v_provider_conversation_id text := nullif(p_event->>'provider_conversation_id', '');
    v_provider_branch_id text := nullif(p_event->>'provider_branch_id', '');
    v_session_id text := p_event->>'session_id';
    v_checkpoint_id text := nullif(p_event->>'checkpoint_id', '');
    v_event_kind text := p_event->>'event_kind';
    v_anchor_status text := p_event->>'anchor_status';
    v_event_time timestamptz := nullif(p_event->>'event_time', '')::timestamptz;
    v_state_time timestamptz := nullif(p_event->>'state_time', '')::timestamptz;
    v_retrieval_time timestamptz := nullif(p_event->>'retrieval_time', '')::timestamptz;
    v_event_time_precision text := p_event->>'event_time_precision';
    v_event_time_lower_bound timestamptz := nullif(p_event->>'event_time_lower_bound', '')::timestamptz;
    v_event_time_upper_bound timestamptz := nullif(p_event->>'event_time_upper_bound', '')::timestamptz;
    v_idempotency_key text := p_event->>'idempotency_key';
    v_supersedes_event_id uuid := nullif(p_event->>'supersedes_event_id', '')::uuid;
    v_source_evidence jsonb := coalesce(p_event->'source_evidence', '[]'::jsonb);
    v_limitations jsonb := coalesce(p_event->'limitations', '[]'::jsonb);
    v_payload jsonb := coalesce(p_event->'payload', '{}'::jsonb);
    v_logical_hash text;
    existing_row public.vera_temporal_events_v1%rowtype;
begin
    if p_event is null or jsonb_typeof(p_event) <> 'object' then
        raise exception using errcode = '22023', message = 'p_event must be a JSON object';
    end if;

    v_logical_hash := public.vera_temporal_event_logical_hash_v1(
        v_project_id,
        v_workstream,
        v_anchor_key,
        v_scope_instance_id,
        v_scope_stability,
        v_provider_conversation_id,
        v_provider_branch_id,
        v_session_id,
        v_checkpoint_id,
        v_event_kind,
        v_anchor_status,
        v_event_time,
        v_state_time,
        v_retrieval_time,
        v_event_time_precision,
        v_event_time_lower_bound,
        v_event_time_upper_bound,
        v_supersedes_event_id,
        v_source_evidence,
        v_limitations,
        v_payload
    );

    perform pg_advisory_xact_lock(
        hashtextextended(v_project_id || '|' || coalesce(v_workstream, '') || '|' || coalesce(v_idempotency_key, ''), 0)
    );

    select *
      into existing_row
      from public.vera_temporal_events_v1
     where project_id = v_project_id
       and workstream = v_workstream
       and idempotency_key = v_idempotency_key;

    if found then
        if existing_row.logical_hash <> v_logical_hash then
            raise exception using
                errcode = '23505',
                message = 'idempotency key already binds different temporal content';
        end if;
        return query
        select existing_row.temporal_event_id,
               existing_row.event_sequence,
               existing_row.record_time,
               existing_row.logical_hash,
               false;
        return;
    end if;

    insert into public.vera_temporal_events_v1 (
        project_id,
        workstream,
        anchor_key,
        scope_instance_id,
        scope_stability,
        provider_conversation_id,
        provider_branch_id,
        session_id,
        checkpoint_id,
        event_kind,
        anchor_status,
        event_time,
        state_time,
        retrieval_time,
        event_time_precision,
        event_time_lower_bound,
        event_time_upper_bound,
        idempotency_key,
        logical_hash,
        supersedes_event_id,
        source_evidence,
        limitations,
        payload
    ) values (
        v_project_id,
        v_workstream,
        v_anchor_key,
        v_scope_instance_id,
        v_scope_stability,
        v_provider_conversation_id,
        v_provider_branch_id,
        v_session_id,
        v_checkpoint_id,
        v_event_kind,
        v_anchor_status,
        v_event_time,
        v_state_time,
        v_retrieval_time,
        v_event_time_precision,
        v_event_time_lower_bound,
        v_event_time_upper_bound,
        v_idempotency_key,
        v_logical_hash,
        v_supersedes_event_id,
        v_source_evidence,
        v_limitations,
        v_payload
    )
    returning vera_temporal_events_v1.temporal_event_id,
              vera_temporal_events_v1.event_sequence,
              vera_temporal_events_v1.record_time,
              vera_temporal_events_v1.logical_hash
         into temporal_event_id, event_sequence, record_time, logical_hash;

    created := true;
    return next;
end;
$$;

create view public.vera_current_temporal_events_v1
with (security_invoker = true)
as
select leaf.*,
       count(*) over (
           partition by leaf.project_id, leaf.workstream, leaf.scope_instance_id, leaf.anchor_key
       ) as head_count
  from public.vera_temporal_events_v1 as leaf
  left join public.vera_temporal_events_v1 as child
    on child.supersedes_event_id = leaf.temporal_event_id
 where child.temporal_event_id is null;

alter table public.vera_temporal_events_v1 enable row level security;

revoke all on table public.vera_temporal_events_v1 from public, anon, authenticated, service_role;
revoke all on sequence public.vera_temporal_events_v1_event_sequence_seq from public, anon, authenticated, service_role;
revoke all on function public.append_vera_temporal_event_v1(jsonb) from public, anon, authenticated;
revoke all on function public.vera_temporal_event_logical_hash_v1(
    text, text, text, text, text, text, text, text, text, text, text,
    timestamptz, timestamptz, timestamptz, text, timestamptz, timestamptz,
    uuid, jsonb, jsonb, jsonb
) from public, anon, authenticated;

grant select on table public.vera_temporal_events_v1 to service_role;
grant select on public.vera_current_temporal_events_v1 to service_role;
grant execute on function public.append_vera_temporal_event_v1(jsonb) to service_role;

create policy vera_temporal_events_v1_no_client_access
on public.vera_temporal_events_v1
as restrictive
for all
to anon, authenticated
using (false)
with check (false);

commit;
