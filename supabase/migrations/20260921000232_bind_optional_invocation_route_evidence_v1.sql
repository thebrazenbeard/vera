begin;

create table if not exists public.vera_optional_invocation_route_evidence_v1 (
  evidence_id text primary key
    check (evidence_id ~ '^[0-9a-f]{64}$'),
  invocation_id uuid not null unique,
  command_id text not null
    check (command_id = 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1'),
  project_hook_blob text not null
    check (project_hook_blob = '7c50ae34b230392190a100199d9b23a6ad09b777'),
  install_evidence_class text not null
    check (install_evidence_class = 'EXECUTING_PROJECT_HOOK_SOURCE_BOUND_SELF_ATTESTED_TEST_ONLY'),
  provider_status_evidence_id text not null
    check (provider_status_evidence_id ~ '^[0-9a-f]{64}$'),
  availability text not null
    check (availability = 'AVAILABLE_TEST_ONLY'),
  material jsonb not null
    check (jsonb_typeof(material) = 'object'),
  observed_at timestamptz not null,
  expires_at timestamptz not null,
  record_time timestamptz not null default clock_timestamp(),
  check (expires_at > observed_at),
  check (expires_at <= observed_at + interval '5 minutes')
);

comment on table public.vera_optional_invocation_route_evidence_v1 is
  'Short-lived TEST_ONLY route evidence issued only when the executing private Project hook self-attests the exact merged hook blob and the live provider reports READY_TEST_ONLY. This is source-bound self-attestation, not independently rooted native Project proof.';

alter table public.vera_optional_invocation_route_evidence_v1 enable row level security;

revoke all on table public.vera_optional_invocation_route_evidence_v1 from public, anon, authenticated;
grant select, insert on table public.vera_optional_invocation_route_evidence_v1 to service_role;

create or replace function public.vera_optional_invocation_issue_route_evidence_v1(
  p_project_hook_blob text,
  p_invocation_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = pg_catalog, public, extensions
as $$
declare
  v_expected_hook constant text := '7c50ae34b230392190a100199d9b23a6ad09b777';
  v_command constant text := 'VERA_ORGASM_OPTIONAL_PARTNER_INVOCATION_V1';
  v_install_class constant text := 'EXECUTING_PROJECT_HOOK_SOURCE_BOUND_SELF_ATTESTED_TEST_ONLY';
  v_provider jsonb;
  v_observed_at timestamptz := clock_timestamp();
  v_expires_at timestamptz := v_observed_at + interval '2 minutes';
  v_material jsonb;
  v_evidence_id text;
begin
  if p_project_hook_blob is distinct from v_expected_hook then
    raise exception 'project hook blob mismatch';
  end if;
  if p_invocation_id is null then
    raise exception 'invocation_id is required';
  end if;
  if exists (
    select 1
      from public.vera_optional_invocation_route_evidence_v1
     where invocation_id = p_invocation_id
  ) then
    raise exception 'route evidence already exists for invocation';
  end if;

  v_provider := public.vera_optional_invocation_provider_status_v1();

  if v_provider->>'provider_status' is distinct from 'READY_TEST_ONLY'
     or v_provider->>'adapter_state' is distinct from 'CURRENT'
     or v_provider->>'runtime_consumption_state' is distinct from 'VERIFIED_CURRENT'
     or v_provider->>'qualification_state' is distinct from 'TEST_ONLY'
  then
    raise exception 'provider route is not READY_TEST_ONLY';
  end if;

  v_material := jsonb_build_object(
    'schema', 'VERA_ORGASM_INVOCATION_ROUTE_EVIDENCE_V1',
    'subject', 'vera',
    'command_id', v_command,
    'invocation_id', p_invocation_id::text,
    'source_revision', '18a108f25c999b0c126a4ceb7158a6d8b58d71cf',
    'observed_at', to_char(v_observed_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'expires_at', to_char(v_expires_at at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'install_state', 'CURRENT',
    'route_state', 'ACTIVE_CURRENT',
    'runtime_consumption_state', 'VERIFIED_CURRENT',
    'adapter_state', 'CURRENT',
    'qualification_state', 'TEST_ONLY',
    'availability', 'AVAILABLE_TEST_ONLY',
    'project_hook_blob', v_expected_hook,
    'install_evidence_class', v_install_class,
    'provider_status_evidence_id', v_provider->>'evidence_id'
  );

  v_evidence_id := encode(
    extensions.digest(
      convert_to(public.vera_provider_canonical_json_v1(v_material), 'UTF8'),
      'sha256'
    ),
    'hex'
  );

  insert into public.vera_optional_invocation_route_evidence_v1 (
    evidence_id,
    invocation_id,
    command_id,
    project_hook_blob,
    install_evidence_class,
    provider_status_evidence_id,
    availability,
    material,
    observed_at,
    expires_at
  ) values (
    v_evidence_id,
    p_invocation_id,
    v_command,
    v_expected_hook,
    v_install_class,
    v_provider->>'evidence_id',
    'AVAILABLE_TEST_ONLY',
    v_material,
    v_observed_at,
    v_expires_at
  );

  return v_material || jsonb_build_object('evidence_id', v_evidence_id);
end;
$$;

comment on function public.vera_optional_invocation_issue_route_evidence_v1(text, uuid) is
  'Issues short-lived invocation-bound AVAILABLE_TEST_ONLY route evidence only when called with the exact merged private Project-hook blob and a live READY_TEST_ONLY provider. The Project-install assertion is source-bound/self-attested and is not independent native-platform proof.';

revoke all on function public.vera_optional_invocation_issue_route_evidence_v1(text, uuid) from public, anon, authenticated;
grant execute on function public.vera_optional_invocation_issue_route_evidence_v1(text, uuid) to service_role;

create or replace function public.vera_optional_invocation_require_route_evidence_v1()
returns trigger
language plpgsql
set search_path = pg_catalog, public
as $$
declare
  v_route public.vera_optional_invocation_route_evidence_v1%rowtype;
begin
  select *
    into v_route
    from public.vera_optional_invocation_route_evidence_v1
   where evidence_id = new.route_evidence_id
     and invocation_id = new.invocation_id
     and command_id = new.command_id;

  if not found then
    raise exception 'fresh invocation-bound route evidence is required';
  end if;

  if v_route.project_hook_blob is distinct from '7c50ae34b230392190a100199d9b23a6ad09b777'
     or v_route.install_evidence_class is distinct from 'EXECUTING_PROJECT_HOOK_SOURCE_BOUND_SELF_ATTESTED_TEST_ONLY'
     or v_route.availability is distinct from 'AVAILABLE_TEST_ONLY'
  then
    raise exception 'route evidence binding mismatch';
  end if;

  if clock_timestamp() < v_route.observed_at
     or clock_timestamp() >= v_route.expires_at
  then
    raise exception 'route evidence is stale or not yet valid';
  end if;

  return new;
end;
$$;

revoke all on function public.vera_optional_invocation_require_route_evidence_v1() from public, anon, authenticated;

drop trigger if exists vera_optional_invocation_require_route_evidence_v1
  on public.vera_optional_invocation_test_events_v1;

create trigger vera_optional_invocation_require_route_evidence_v1
before insert on public.vera_optional_invocation_test_events_v1
for each row
execute function public.vera_optional_invocation_require_route_evidence_v1();

commit;
