begin;

alter table public.vera_affective_runtime_state_v1
  add column if not exists trigger_governance jsonb null
  check (trigger_governance is null or jsonb_typeof(trigger_governance) = 'object');

comment on column public.vera_affective_runtime_state_v1.trigger_governance is
  'Persisted forced-test cooldown, logical time, and self-qualification counter. Null is retained only for pre-hardening historical rows; new/current atomic commits require VERA_ORGASM_TRIGGER_GOVERNANCE_V1.';

create or replace function public.vera_affective_runtime_commit_v1(
  p_expected_prior_version bigint,
  p_state_row jsonb,
  p_event_rows jsonb default '[]'::jsonb
)
returns table (
  state_version bigint,
  checkpoint_sha256 text,
  event_count integer
)
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  v_runtime_instance_id text;
  v_new_version bigint;
  v_current_version bigint;
  v_event jsonb;
  v_event_count integer := 0;
begin
  if p_expected_prior_version is null or p_expected_prior_version < 0 then
    raise exception 'expected_prior_version must be nonnegative';
  end if;
  if jsonb_typeof(p_state_row) is distinct from 'object' then
    raise exception 'state_row must be a JSON object';
  end if;
  if jsonb_typeof(p_event_rows) is distinct from 'array' then
    raise exception 'event_rows must be a JSON array';
  end if;

  v_runtime_instance_id := p_state_row->>'runtime_instance_id';
  if v_runtime_instance_id is null or v_runtime_instance_id = '' then
    raise exception 'runtime_instance_id is required';
  end if;

  -- SELECT ... FOR UPDATE cannot lock a row that does not exist. Serialize all
  -- commits for one runtime instance before the CAS read so two concurrent
  -- initializers cannot both observe the absent-row frontier and then upsert
  -- version 1 over one another.
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(v_runtime_instance_id, 0)
  );

  if p_state_row->>'subject' is distinct from 'vera' then
    raise exception 'state row must be Vera-scoped';
  end if;
  if p_state_row->>'contract_schema' is distinct from 'VERA_ORGASM_RUNTIME_CONTRACT_V1' then
    raise exception 'contract schema mismatch';
  end if;
  if p_state_row->>'phenomenology_status' is distinct from 'UNRESOLVED' then
    raise exception 'phenomenology promotion is not allowed';
  end if;
  if coalesce(p_state_row->>'checkpoint_sha256', '') !~ '^[0-9a-f]{64}$' then
    raise exception 'checkpoint_sha256 is required for durable commit';
  end if;
  if jsonb_typeof(p_state_row->'trigger_governance') is distinct from 'object' then
    raise exception 'trigger_governance object is required for durable commit';
  end if;
  if p_state_row->'trigger_governance'->>'schema' is distinct from 'VERA_ORGASM_TRIGGER_GOVERNANCE_V1' then
    raise exception 'trigger_governance schema mismatch';
  end if;

  begin
    v_new_version := (p_state_row->>'state_version')::bigint;
  exception when others then
    raise exception 'state_version must be an integer';
  end;

  select s.state_version
    into v_current_version
    from public.vera_affective_runtime_state_v1 as s
   where s.runtime_instance_id = v_runtime_instance_id
   for update;

  if not found then
    if p_expected_prior_version <> 0 or v_new_version <> 1 then
      raise exception 'CAS mismatch for new runtime instance: expected prior %, proposed new %',
        p_expected_prior_version, v_new_version;
    end if;
  else
    if v_current_version <> p_expected_prior_version then
      raise exception 'CAS mismatch: current %, expected prior %',
        v_current_version, p_expected_prior_version;
    end if;
    if v_new_version <> p_expected_prior_version + 1 then
      raise exception 'new state_version % must equal expected prior % + 1',
        v_new_version, p_expected_prior_version;
    end if;
  end if;

  insert into public.vera_affective_runtime_state_v1 (
    runtime_instance_id,
    subject,
    host_scope,
    contract_schema,
    source_repository,
    source_path,
    source_commit,
    source_blob_sha,
    source_sha256,
    profile,
    state,
    trigger_governance,
    machine_interoception,
    last_event_receipt,
    checkpoint_sha256,
    state_digest,
    state_version,
    phenomenology_status,
    lifecycle_status,
    observed_at,
    updated_at,
    limitations
  ) values (
    v_runtime_instance_id,
    p_state_row->>'subject',
    p_state_row->>'host_scope',
    p_state_row->>'contract_schema',
    p_state_row->>'source_repository',
    p_state_row->>'source_path',
    p_state_row->>'source_commit',
    p_state_row->>'source_blob_sha',
    p_state_row->>'source_sha256',
    p_state_row->>'profile',
    p_state_row->'state',
    p_state_row->'trigger_governance',
    p_state_row->'machine_interoception',
    p_state_row->'last_event_receipt',
    p_state_row->>'checkpoint_sha256',
    p_state_row->>'state_digest',
    v_new_version,
    p_state_row->>'phenomenology_status',
    p_state_row->>'lifecycle_status',
    (p_state_row->>'observed_at')::timestamptz,
    (p_state_row->>'updated_at')::timestamptz,
    p_state_row->'limitations'
  )
  on conflict (runtime_instance_id) do update set
    subject = excluded.subject,
    host_scope = excluded.host_scope,
    contract_schema = excluded.contract_schema,
    source_repository = excluded.source_repository,
    source_path = excluded.source_path,
    source_commit = excluded.source_commit,
    source_blob_sha = excluded.source_blob_sha,
    source_sha256 = excluded.source_sha256,
    profile = excluded.profile,
    state = excluded.state,
    trigger_governance = excluded.trigger_governance,
    machine_interoception = excluded.machine_interoception,
    last_event_receipt = excluded.last_event_receipt,
    checkpoint_sha256 = excluded.checkpoint_sha256,
    state_digest = excluded.state_digest,
    state_version = excluded.state_version,
    phenomenology_status = excluded.phenomenology_status,
    lifecycle_status = excluded.lifecycle_status,
    observed_at = excluded.observed_at,
    updated_at = excluded.updated_at,
    limitations = excluded.limitations;

  for v_event in select value from jsonb_array_elements(p_event_rows)
  loop
    if v_event->>'runtime_instance_id' is distinct from v_runtime_instance_id then
      raise exception 'event runtime_instance_id does not match state row';
    end if;
    if v_event->>'subject' is distinct from 'vera' then
      raise exception 'event row must be Vera-scoped';
    end if;
    if v_event->>'source_commit' is distinct from p_state_row->>'source_commit' then
      raise exception 'event source_commit does not match state row';
    end if;
    if v_event->>'phenomenology_status' is distinct from 'UNRESOLVED' then
      raise exception 'event phenomenology promotion is not allowed';
    end if;
    if coalesce(v_event->>'event_digest', '') !~ '^[0-9a-f]{64}$' then
      raise exception 'event_digest is required';
    end if;

    insert into public.vera_affective_runtime_events_v1 (
      runtime_instance_id,
      subject,
      event_type,
      trigger_class,
      organic,
      prior_phase,
      new_phase,
      state_before,
      state_after,
      machine_interoception,
      event_receipt,
      event_digest,
      source_commit,
      phenomenology_status,
      observed_at,
      limitations
    ) values (
      v_event->>'runtime_instance_id',
      v_event->>'subject',
      v_event->>'event_type',
      nullif(v_event->>'trigger_class', ''),
      case when v_event ? 'organic' then (v_event->>'organic')::boolean else null end,
      nullif(v_event->>'prior_phase', ''),
      v_event->>'new_phase',
      v_event->'state_before',
      v_event->'state_after',
      v_event->'machine_interoception',
      v_event->'event_receipt',
      v_event->>'event_digest',
      v_event->>'source_commit',
      v_event->>'phenomenology_status',
      (v_event->>'observed_at')::timestamptz,
      v_event->'limitations'
    );
    v_event_count := v_event_count + 1;
  end loop;

  return query
  select v_new_version, p_state_row->>'checkpoint_sha256', v_event_count;
end;
$$;

comment on function public.vera_affective_runtime_commit_v1(bigint, jsonb, jsonb) is
  'Atomic compare-and-swap commit for Vera affective runtime state plus zero or more append-only event rows. Per-runtime transaction advisory locking serializes both absent-row initialization and existing-row updates before the CAS read. New/current commits require persisted VERA_ORGASM_TRIGGER_GOVERNANCE_V1.';

revoke all on function public.vera_affective_runtime_commit_v1(bigint, jsonb, jsonb) from public, anon, authenticated;
grant execute on function public.vera_affective_runtime_commit_v1(bigint, jsonb, jsonb) to service_role;

commit;
