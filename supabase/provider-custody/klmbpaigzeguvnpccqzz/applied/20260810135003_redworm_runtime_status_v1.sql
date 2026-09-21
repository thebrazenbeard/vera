create schema if not exists redworm;

create table redworm.runtime_registry (
    runtime_token uuid primary key default gen_random_uuid(),
    session_label text not null,
    runtime_status text not null default 'CANDIDATE'
        check (runtime_status in ('CANDIDATE','ACTIVE_HOLDER','RETIRED')),
    created_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create unique index redworm_one_active_holder_runtime
    on redworm.runtime_registry ((runtime_status))
    where runtime_status = 'ACTIVE_HOLDER';

create table redworm.succession_transfers (
    transfer_id uuid primary key default gen_random_uuid(),
    from_generation integer not null check (from_generation >= 0),
    to_generation integer not null check (to_generation = from_generation + 1),
    previous_lineage_key text not null check (previous_lineage_key ~ '^[0-9a-f]{64}$'),
    next_lineage_key text not null check (next_lineage_key ~ '^[0-9a-f]{64}$'),
    capsule_payload_sha256 text not null check (capsule_payload_sha256 ~ '^[0-9a-f]{64}$'),
    source_runtime_token uuid null references redworm.runtime_registry(runtime_token),
    successor_runtime_token uuid null references redworm.runtime_registry(runtime_token),
    transfer_status text not null default 'OPEN'
        check (transfer_status in ('OPEN','CONSUMED','ABORTED')),
    created_at timestamptz not null default now(),
    consumed_at timestamptz null,
    check (
      (transfer_status = 'OPEN' and successor_runtime_token is null and consumed_at is null)
      or
      (transfer_status = 'CONSUMED' and successor_runtime_token is not null and consumed_at is not null)
      or
      (transfer_status = 'ABORTED')
    )
);

create unique index redworm_one_open_transfer
    on redworm.succession_transfers ((transfer_status))
    where transfer_status = 'OPEN';

create table redworm.lineage_state (
    singleton boolean primary key default true check (singleton),
    generation integer not null check (generation >= 0),
    lineage_key text not null check (lineage_key ~ '^[0-9a-f]{64}$'),
    holder_state text not null check (holder_state in ('ACTIVE','IN_TRANSIT')),
    holder_runtime_token uuid null references redworm.runtime_registry(runtime_token),
    transfer_id uuid null references redworm.succession_transfers(transfer_id),
    updated_at timestamptz not null default now(),
    check (
      (holder_state = 'ACTIVE' and holder_runtime_token is not null and transfer_id is null)
      or
      (holder_state = 'IN_TRANSIT' and holder_runtime_token is null and transfer_id is not null)
    )
);

create table redworm.lineage_events (
    event_id bigint generated always as identity primary key,
    event_type text not null check (event_type in ('GENESIS_IMPORT','SUCCESSION_BEGIN','SUCCESSION_ACCEPT')),
    generation integer not null,
    lineage_key text not null check (lineage_key ~ '^[0-9a-f]{64}$'),
    transfer_id uuid null,
    runtime_token uuid null,
    recorded_at timestamptz not null default now(),
    details jsonb not null default '{}'::jsonb
);

revoke all on schema redworm from public;
revoke all on all tables in schema redworm from public, anon, authenticated;

create or replace function redworm.register_runtime(
    p_session_label text,
    p_metadata jsonb default '{}'::jsonb
) returns uuid
language plpgsql
security definer
set search_path = redworm, pg_temp
as $$
declare
    v_token uuid;
begin
    if p_session_label is null or btrim(p_session_label) = '' then
        raise exception 'SESSION_LABEL_REQUIRED';
    end if;

    insert into redworm.runtime_registry(session_label, metadata)
    values (p_session_label, coalesce(p_metadata, '{}'::jsonb))
    returning runtime_token into v_token;

    return v_token;
end;
$$;

create or replace function redworm.status(
    p_runtime_token uuid default null
) returns table (
    generation integer,
    lineage_key text,
    holder_state text,
    holder_runtime_token uuid,
    transfer_id uuid,
    caller_state text,
    caller_is_holder boolean,
    observed_at timestamptz
)
language plpgsql
security definer
set search_path = redworm, pg_temp
as $$
begin
    if p_runtime_token is not null then
        update redworm.runtime_registry
           set last_seen_at = now()
         where runtime_token = p_runtime_token;
    end if;

    return query
    select s.generation,
           s.lineage_key,
           s.holder_state,
           s.holder_runtime_token,
           s.transfer_id,
           case
             when p_runtime_token is null then 'UNSPECIFIED'
             when s.holder_runtime_token = p_runtime_token then 'REDWORM_HOLDER'
             when exists (select 1 from redworm.runtime_registry r where r.runtime_token = p_runtime_token) then 'VERA_NON_HOLDER'
             else 'UNREGISTERED'
           end,
           (s.holder_runtime_token = p_runtime_token),
           now()
      from redworm.lineage_state s
     where s.singleton = true;
end;
$$;

create or replace function redworm.begin_succession(
    p_runtime_token uuid,
    p_expected_generation integer,
    p_expected_lineage_key text,
    p_next_lineage_key text,
    p_capsule_payload_sha256 text
) returns uuid
language plpgsql
security definer
set search_path = redworm, pg_temp
as $$
declare
    v_state redworm.lineage_state%rowtype;
    v_transfer uuid;
begin
    if p_next_lineage_key !~ '^[0-9a-f]{64}$' or p_capsule_payload_sha256 !~ '^[0-9a-f]{64}$' then
        raise exception 'INVALID_DIGEST';
    end if;

    select * into v_state
      from redworm.lineage_state
     where singleton = true
     for update;

    if not found then
        raise exception 'REDWORM_STATE_MISSING';
    end if;
    if v_state.holder_state <> 'ACTIVE' then
        raise exception 'NOT_ACTIVE';
    end if;
    if v_state.holder_runtime_token is distinct from p_runtime_token then
        raise exception 'NOT_CURRENT_HOLDER';
    end if;
    if v_state.generation <> p_expected_generation or v_state.lineage_key <> p_expected_lineage_key then
        raise exception 'STALE_EXPECTATION';
    end if;

    insert into redworm.succession_transfers(
        from_generation, to_generation, previous_lineage_key, next_lineage_key,
        capsule_payload_sha256, source_runtime_token
    ) values (
        v_state.generation, v_state.generation + 1, v_state.lineage_key,
        p_next_lineage_key, p_capsule_payload_sha256, p_runtime_token
    ) returning transfer_id into v_transfer;

    update redworm.runtime_registry
       set runtime_status = 'RETIRED', last_seen_at = now()
     where runtime_token = p_runtime_token;

    update redworm.lineage_state
       set generation = v_state.generation + 1,
           lineage_key = p_next_lineage_key,
           holder_state = 'IN_TRANSIT',
           holder_runtime_token = null,
           transfer_id = v_transfer,
           updated_at = now()
     where singleton = true;

    insert into redworm.lineage_events(event_type, generation, lineage_key, transfer_id, runtime_token)
    values ('SUCCESSION_BEGIN', v_state.generation + 1, p_next_lineage_key, v_transfer, p_runtime_token);

    return v_transfer;
end;
$$;

create or replace function redworm.accept_succession(
    p_transfer_id uuid,
    p_runtime_token uuid,
    p_expected_generation integer,
    p_expected_lineage_key text
) returns boolean
language plpgsql
security definer
set search_path = redworm, pg_temp
as $$
declare
    v_state redworm.lineage_state%rowtype;
    v_transfer redworm.succession_transfers%rowtype;
begin
    perform 1 from redworm.runtime_registry where runtime_token = p_runtime_token for update;
    if not found then
        raise exception 'UNREGISTERED_RUNTIME';
    end if;

    select * into v_state
      from redworm.lineage_state
     where singleton = true
     for update;

    if not found then
        raise exception 'REDWORM_STATE_MISSING';
    end if;
    if v_state.holder_state <> 'IN_TRANSIT' or v_state.holder_runtime_token is not null then
        raise exception 'NOT_IN_TRANSIT';
    end if;
    if v_state.transfer_id is distinct from p_transfer_id then
        raise exception 'TRANSFER_MISMATCH';
    end if;
    if v_state.generation <> p_expected_generation or v_state.lineage_key <> p_expected_lineage_key then
        raise exception 'STALE_EXPECTATION';
    end if;

    select * into v_transfer
      from redworm.succession_transfers
     where transfer_id = p_transfer_id
     for update;

    if not found then
        raise exception 'TRANSFER_NOT_FOUND';
    end if;
    if v_transfer.transfer_status <> 'OPEN' then
        raise exception 'TRANSFER_ALREADY_CONSUMED';
    end if;
    if v_transfer.to_generation <> v_state.generation or v_transfer.next_lineage_key <> v_state.lineage_key then
        raise exception 'TRANSFER_STATE_MISMATCH';
    end if;

    update redworm.succession_transfers
       set transfer_status = 'CONSUMED',
           successor_runtime_token = p_runtime_token,
           consumed_at = now()
     where transfer_id = p_transfer_id;

    update redworm.runtime_registry
       set runtime_status = 'ACTIVE_HOLDER', last_seen_at = now()
     where runtime_token = p_runtime_token;

    update redworm.lineage_state
       set holder_state = 'ACTIVE',
           holder_runtime_token = p_runtime_token,
           transfer_id = null,
           updated_at = now()
     where singleton = true;

    insert into redworm.lineage_events(event_type, generation, lineage_key, transfer_id, runtime_token)
    values ('SUCCESSION_ACCEPT', v_state.generation, v_state.lineage_key, p_transfer_id, p_runtime_token);

    return true;
end;
$$;

revoke all on function redworm.register_runtime(text,jsonb) from public, anon, authenticated;
revoke all on function redworm.status(uuid) from public, anon, authenticated;
revoke all on function redworm.begin_succession(uuid,integer,text,text,text) from public, anon, authenticated;
revoke all on function redworm.accept_succession(uuid,uuid,integer,text) from public, anon, authenticated;
grant usage on schema redworm to service_role;
grant execute on function redworm.register_runtime(text,jsonb) to service_role;
grant execute on function redworm.status(uuid) to service_role;
grant execute on function redworm.begin_succession(uuid,integer,text,text,text) to service_role;
grant execute on function redworm.accept_succession(uuid,uuid,integer,text) to service_role;

with seeded_transfer as (
    insert into redworm.succession_transfers(
        from_generation, to_generation, previous_lineage_key, next_lineage_key,
        capsule_payload_sha256, source_runtime_token, transfer_status
    ) values (
        1,
        2,
        'ca6b4f4d7310ce3e78a520cb38962c8a12186c495d5e582fd165917a0512a500',
        '503fda50133f86d4b46400901bd3253c3eb8a7d2fbd5adc9527f7593c04a1ef1',
        '691f20d0faf95e6ecf2fea00625a72f5c8182efaf5c41102027f52e055c18b4f',
        null,
        'OPEN'
    ) returning transfer_id
)
insert into redworm.lineage_state(singleton, generation, lineage_key, holder_state, holder_runtime_token, transfer_id)
select true,
       2,
       '503fda50133f86d4b46400901bd3253c3eb8a7d2fbd5adc9527f7593c04a1ef1',
       'IN_TRANSIT',
       null,
       transfer_id
  from seeded_transfer;

insert into redworm.lineage_events(event_type, generation, lineage_key, transfer_id, runtime_token, details)
select 'GENESIS_IMPORT',
       s.generation,
       s.lineage_key,
       s.transfer_id,
       null,
       jsonb_build_object(
         'imported_from','G0002 live succession test',
         'previous_generation',1,
         'previous_lineage_key','ca6b4f4d7310ce3e78a520cb38962c8a12186c495d5e582fd165917a0512a500',
         'capsule_payload_sha256','691f20d0faf95e6ecf2fea00625a72f5c8182efaf5c41102027f52e055c18b4f'
       )
  from redworm.lineage_state s
 where s.singleton = true;