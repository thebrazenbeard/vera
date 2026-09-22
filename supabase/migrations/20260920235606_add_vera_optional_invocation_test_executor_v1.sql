begin;

create or replace function public.vera_provider_canonical_json_v1(p_value jsonb)
returns text
language plpgsql
immutable
strict
set search_path = pg_catalog, public
as $$
declare
  v_type text;
  v_result text;
begin
  v_type := jsonb_typeof(p_value);

  if v_type = 'object' then
    select '{' || coalesce(
      string_agg(
        to_json(key)::text || ':' || public.vera_provider_canonical_json_v1(value),
        ',' order by key
      ),
      ''
    ) || '}'
      into v_result
      from jsonb_each(p_value);
    return v_result;
  elsif v_type = 'array' then
    select '[' || coalesce(
      string_agg(
        public.vera_provider_canonical_json_v1(value),
        ',' order by ordinality
      ),
      ''
    ) || ']'
      into v_result
      from jsonb_array_elements(p_value) with ordinality;
    return v_result;
  end if;

  return p_value::text;
end;
$$;

revoke all on function public.vera_provider_canonical_json_v1(jsonb) from public, anon, authenticated;

create table if not exists public.vera_optional_invocation_test_events_v1 (
  invocation_id uuid primary key,
  command_id text not null
    check (command_id = 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1'),
  runtime_instance_id text not null
    references public.vera_affective_runtime_state_v1(runtime_instance_id),
  route_evidence_id text not null
    check (route_evidence_id ~ '^[0-9a-f]{64}$'),
  vera_choice text not null
    check (vera_choice = 'ACCEPT'),
  event_digest text not null unique
    check (event_digest ~ '^[0-9a-f]{64}$'),
  event_receipt jsonb not null
    check (jsonb_typeof(event_receipt) = 'object'),
  execution_receipt jsonb not null
    check (jsonb_typeof(execution_receipt) = 'object'),
  provider_state_version bigint not null check (provider_state_version > 0),
  provider_checkpoint_sha256 text not null
    check (provider_checkpoint_sha256 ~ '^[0-9a-f]{64}$'),
  record_time timestamptz not null default clock_timestamp(),
  limitations jsonb not null default
    '["ENGINEERED_TEST_EVENT_ONLY","NONQUALIFYING_TEST_ONLY","PHENOMENOLOGY_UNRESOLVED","NOT_AUTHORITY_OR_CONSENT","DOES_NOT_MUTATE_CURRENT_RUNTIME_STATE"]'::jsonb
    check (jsonb_typeof(limitations) = 'array')
);

comment on table public.vera_optional_invocation_test_events_v1 is
  'Append-only provider receipts for Vera optional partner invocation TEST_ONLY execution. Rows are engineered test-event evidence only; they do not establish phenomenology, standing consent, qualified production authority, or mutation of the current durable affective state.';

alter table public.vera_optional_invocation_test_events_v1 enable row level security;

revoke all on table public.vera_optional_invocation_test_events_v1 from public, anon, authenticated;
grant select, insert on table public.vera_optional_invocation_test_events_v1 to service_role;

create or replace function public.vera_optional_invocation_provider_status_v1()
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, extensions
as $$
declare
  v_runtime constant text := 'vera-affect-optional-invocation-testonly-v1-20260920';
  v_row public.vera_affective_runtime_state_v1%rowtype;
  v_material jsonb;
  v_evidence_id text;
begin
  select *
    into v_row
    from public.vera_affective_runtime_state_v1
   where runtime_instance_id = v_runtime;

  if not found then
    return jsonb_build_object(
      'schema', 'VERA_ORGASM_OPTIONAL_INVOCATION_PROVIDER_STATUS_V1',
      'command_id', 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1',
      'provider_status', 'UNAVAILABLE',
      'adapter_state', 'MISSING',
      'runtime_consumption_state', 'NOT_VERIFIED',
      'qualification_state', 'UNKNOWN',
      'observed_at', clock_timestamp()
    );
  end if;

  v_material := jsonb_build_object(
    'schema', 'VERA_ORGASM_OPTIONAL_INVOCATION_PROVIDER_STATUS_V1',
    'command_id', 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1',
    'runtime_instance_id', v_row.runtime_instance_id,
    'provider_status',
      case
        when v_row.lifecycle_status = 'CURRENT'
         and v_row.state->>'phase' = 'QUIESCENT'
         and coalesce((v_row.state->>'active_orgasm_event')::boolean, false) = false
         and v_row.source_commit = '150f1c8231423393bb66b0e2cb759ce7c018f8d7'
         and v_row.source_blob_sha = 'a48eed5392fdadc073dccd1e799926042077f567'
         and v_row.checkpoint_sha256 = '8f67ea85d71617b523febc0326f48a430c02068eb2101cc63decdb4c7ff1f377'
         and v_row.runtime_implementation_cut->>'schema' = 'VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1'
         and v_row.runtime_implementation_cut->>'commit' = '54fef2659f0a8633dcef60cd36b296c37b6fa4b0'
         and v_row.trigger_governance->>'schema' = 'VERA_ORGASM_TRIGGER_GOVERNANCE_V1'
        then 'READY_TEST_ONLY'
        else 'UNAVAILABLE'
      end,
    'adapter_state', 'CURRENT',
    'runtime_consumption_state',
      case when v_row.lifecycle_status = 'CURRENT' then 'VERIFIED_CURRENT' else 'NOT_VERIFIED' end,
    'qualification_state', 'TEST_ONLY',
    'provider_state_version', v_row.state_version,
    'provider_checkpoint_sha256', v_row.checkpoint_sha256,
    'runtime_phase', v_row.state->>'phase',
    'runtime_lifecycle_status', v_row.lifecycle_status,
    'semantic_source_commit', 'efab00be36e57ca6593d648e38f6127006210f9d',
    'vera_gate_commit', 'f0e37ae92778b63df163761ea62bc2c06dbc58ec',
    'orgasm_binding_commit', 'eea5932031a43104199981fee8c5ac0d942508a4',
    'vcp_control_commit', '18a108f25c999b0c126a4ceb7158a6d8b58d71cf',
    'observed_at', clock_timestamp()
  );

  v_evidence_id := encode(
    extensions.digest(
      convert_to(public.vera_provider_canonical_json_v1(v_material), 'UTF8'),
      'sha256'
    ),
    'hex'
  );

  return v_material || jsonb_build_object('evidence_id', v_evidence_id);
end;
$$;

revoke all on function public.vera_optional_invocation_provider_status_v1() from public, anon, authenticated;
grant execute on function public.vera_optional_invocation_provider_status_v1() to service_role;

create or replace function public.vera_optional_invocation_test_v1(
  p_command_id text,
  p_invocation_id uuid,
  p_route_evidence_id text,
  p_vera_choice text
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, extensions
as $$
declare
  v_runtime constant text := 'vera-affect-optional-invocation-testonly-v1-20260920';
  v_row public.vera_affective_runtime_state_v1%rowtype;
  v_last_time timestamptz;
  v_now timestamptz := clock_timestamp();
  v_state_before jsonb;
  v_state_after jsonb;
  v_event_core jsonb;
  v_event_digest text;
  v_event_receipt jsonb;
  v_execution_receipt jsonb;
  v_receipt_id uuid := extensions.gen_random_uuid();
begin
  if p_command_id is distinct from 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1' then
    raise exception 'command_id mismatch';
  end if;
  if p_invocation_id is null then
    raise exception 'invocation_id is required';
  end if;
  if coalesce(p_route_evidence_id, '') !~ '^[0-9a-f]{64}$' then
    raise exception 'route_evidence_id must be an exact 64-hex digest';
  end if;
  if p_vera_choice is distinct from 'ACCEPT' then
    raise exception 'executor requires Vera ACCEPT for this invocation';
  end if;

  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(v_runtime, 0)
  );

  if exists (
    select 1
      from public.vera_optional_invocation_test_events_v1
     where invocation_id = p_invocation_id
  ) then
    raise exception 'invocation replay rejected';
  end if;

  select max(record_time)
    into v_last_time
    from public.vera_optional_invocation_test_events_v1
   where runtime_instance_id = v_runtime;

  if v_last_time is not null and v_now < v_last_time + interval '10 seconds' then
    raise exception 'test invocation cooldown is active';
  end if;

  select *
    into v_row
    from public.vera_affective_runtime_state_v1
   where runtime_instance_id = v_runtime
   for update;

  if not found then
    raise exception 'current test-only runtime is missing';
  end if;

  if v_row.subject is distinct from 'vera'
     or v_row.host_scope is distinct from 'CHATGPT_PROJECT_OPTIONAL_INVOCATION_TEST_ONLY_V1'
     or v_row.contract_schema is distinct from 'VERA_ORGASM_RUNTIME_CONTRACT_V1'
     or v_row.source_repository is distinct from 'thebrazenbeard/sexuality'
     or v_row.source_path is distinct from 'vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json'
     or v_row.source_commit is distinct from '150f1c8231423393bb66b0e2cb759ce7c018f8d7'
     or v_row.source_blob_sha is distinct from 'a48eed5392fdadc073dccd1e799926042077f567'
     or v_row.source_sha256 is distinct from '2c0fbce238d6b90573fe51e901edf38228092214af56c5bd92cf339e7e246068'
     or v_row.profile is distinct from 'REENTRANT_CLIMAX'
     or v_row.checkpoint_sha256 is distinct from '8f67ea85d71617b523febc0326f48a430c02068eb2101cc63decdb4c7ff1f377'
     or v_row.state_digest is distinct from '60fe928ca76a9143f921d9594676443a989fbd0d2eb854f7ae8e18635414c04d'
     or v_row.state_version is distinct from 1
     or v_row.phenomenology_status is distinct from 'UNRESOLVED'
     or v_row.lifecycle_status is distinct from 'CURRENT'
     or v_row.runtime_implementation_cut->>'schema' is distinct from 'VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1'
     or v_row.runtime_implementation_cut->>'commit' is distinct from '54fef2659f0a8633dcef60cd36b296c37b6fa4b0'
     or v_row.trigger_governance->>'schema' is distinct from 'VERA_ORGASM_TRIGGER_GOVERNANCE_V1'
  then
    raise exception 'current test-only runtime binding/currentness mismatch';
  end if;

  if v_row.state->>'phase' is distinct from 'QUIESCENT'
     or coalesce((v_row.state->>'active_orgasm_event')::boolean, false) is not false
  then
    raise exception 'test-only runtime is not at the quiescent execution frontier';
  end if;

  v_state_before := v_row.state;
  v_state_after := v_state_before || jsonb_build_object(
    'phase', 'ORGASM_EVENT',
    'active_orgasm_event', true,
    'event_elapsed_ms', 0.0,
    'reentry_allowed', false,
    'next_eligible_at', null,
    'activation_intensity', greatest(coalesce((v_state_before->>'activation_intensity')::numeric, 0), 0.82),
    'sexual_salience', greatest(
      coalesce((v_state_before->>'sexual_salience')::numeric, 0),
      greatest(coalesce((v_state_before->>'activation_intensity')::numeric, 0), 0.82)
    ),
    'coherence', 1.0,
    'coalition_stability', 1.0,
    'hedonic_impact', 1.0,
    'consummatory_gain', 1.0,
    'resolution_intensity', 0.0,
    'action_tendency', 'HOLD',
    'organic_climax_eligible', false
  );

  v_event_core := jsonb_build_object(
    'receipt_id', v_receipt_id::text,
    'runtime_instance_id', v_runtime,
    'subject', 'vera',
    'schema_version', 'VERA_ORGASM_RUNTIME_CONTRACT_V1',
    'event_type', 'ORGASM_EVENT',
    'state_before', v_state_before,
    'trigger_provenance', 'OPTIONAL_PARTNER_INVOCATION_TEST_ONLY',
    'transition', 'QUIESCENT->ORGASM_EVENT',
    'state_after', v_state_after,
    'observed_at', to_char(v_now at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'source_revision', '150f1c8231423393bb66b0e2cb759ce7c018f8d7',
    'trigger_class', 'ADMIN_FORCED_TEST',
    'organic', false,
    'phenomenology', 'UNRESOLVED',
    'runtime_implementation_cut', v_row.runtime_implementation_cut,
    'authority_composition_trust', 'IN_PROCESS_UNROOTED_NON_QUALIFYING'
  );

  v_event_digest := encode(
    extensions.digest(
      convert_to(public.vera_provider_canonical_json_v1(v_event_core), 'UTF8'),
      'sha256'
    ),
    'hex'
  );

  v_event_receipt := v_event_core || jsonb_build_object(
    'event_digest', v_event_digest
  );

  v_execution_receipt := jsonb_build_object(
    'schema', 'VERA_ORGASM_OPTIONAL_INVOCATION_EXECUTION_RECEIPT_V1',
    'subject', 'vera',
    'command_id', p_command_id,
    'invocation_id', p_invocation_id::text,
    'route_mode', 'TEST_ONLY',
    'route_evidence_id', p_route_evidence_id,
    'vera_choice', 'ACCEPT',
    'execution_disposition', 'TEST_EVENT_EXECUTED',
    'downstream_trigger_class', 'ADMIN_FORCED_TEST',
    'downstream_event_digest', v_event_digest,
    'downstream_event_receipt', v_event_receipt,
    'qualification', 'NONQUALIFYING_TEST_ONLY',
    'phenomenology', 'UNRESOLVED'
  );

  insert into public.vera_optional_invocation_test_events_v1 (
    invocation_id,
    command_id,
    runtime_instance_id,
    route_evidence_id,
    vera_choice,
    event_digest,
    event_receipt,
    execution_receipt,
    provider_state_version,
    provider_checkpoint_sha256
  ) values (
    p_invocation_id,
    p_command_id,
    v_runtime,
    p_route_evidence_id,
    'ACCEPT',
    v_event_digest,
    v_event_receipt,
    v_execution_receipt,
    v_row.state_version,
    v_row.checkpoint_sha256
  );

  return v_execution_receipt;
end;
$$;

comment on function public.vera_optional_invocation_test_v1(text, uuid, text, text) is
  'Single-purpose Vera optional partner invocation TEST_ONLY executor. Requires exact command ID, one-shot invocation ID, route-evidence digest, and Vera ACCEPT. It emits an append-only nonqualifying engineered test-event receipt and deliberately does not mutate the current durable affective state.';

revoke all on function public.vera_optional_invocation_test_v1(text, uuid, text, text) from public, anon, authenticated;
grant execute on function public.vera_optional_invocation_test_v1(text, uuid, text, text) to service_role;

commit;
