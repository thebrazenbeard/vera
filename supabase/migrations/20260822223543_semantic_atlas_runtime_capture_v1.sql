create schema if not exists semantic_atlas;
comment on schema semantic_atlas is 'Rebuildable Semantic Atlas runtime and candidate-capture plane. Git remains canonical semantic authority.';

create table semantic_atlas.runtime_snapshots (
  snapshot_id uuid primary key default extensions.gen_random_uuid(),
  git_commit_sha text not null unique check (git_commit_sha ~ '^[0-9a-f]{40}$'),
  source_branch text not null,
  manifest_sha256 text null check (manifest_sha256 is null or manifest_sha256 ~ '^[0-9a-f]{64}$'),
  materialization_version text not null default 'v1',
  state text not null check (state in ('LOADING','ACTIVE','SUPERSEDED','FAILED')),
  loaded_at timestamptz not null default clock_timestamp(),
  loader text not null default 'semantic-atlas-sync',
  object_counts jsonb not null default '{}'::jsonb check (jsonb_typeof(object_counts) = 'object'),
  notes text null
);
comment on table semantic_atlas.runtime_snapshots is 'Derived runtime snapshots bound to exact Git commits. Snapshot state never creates semantic authority.';
create unique index semantic_atlas_one_active_snapshot
  on semantic_atlas.runtime_snapshots ((state)) where state = 'ACTIVE';

create table semantic_atlas.runtime_objects (
  snapshot_id uuid not null references semantic_atlas.runtime_snapshots(snapshot_id) on delete cascade,
  object_id text not null,
  object_type text not null,
  source_path text null,
  payload_sha256 text null check (payload_sha256 is null or payload_sha256 ~ '^[0-9a-f]{64}$'),
  payload jsonb not null check (jsonb_typeof(payload) = 'object'),
  primary key (snapshot_id, object_id)
);
comment on table semantic_atlas.runtime_objects is 'Materialized Semantic Atlas objects for fast retrieval. Rebuild from the bound Git snapshot on drift.';
create index semantic_atlas_runtime_objects_type_idx on semantic_atlas.runtime_objects (snapshot_id, object_type);
create index semantic_atlas_runtime_objects_semantic_key_idx on semantic_atlas.runtime_objects (snapshot_id, ((payload ->> 'semantic_key'))) where payload ? 'semantic_key';
create index semantic_atlas_runtime_objects_node_idx on semantic_atlas.runtime_objects (snapshot_id, ((payload ->> 'node_id'))) where payload ? 'node_id';
create index semantic_atlas_runtime_objects_subject_idx on semantic_atlas.runtime_objects (snapshot_id, ((payload ->> 'subject_id'))) where payload ? 'subject_id';
create index semantic_atlas_runtime_objects_payload_gin on semantic_atlas.runtime_objects using gin (payload jsonb_path_ops);

create view semantic_atlas.active_runtime_objects as
select o.snapshot_id, s.git_commit_sha, s.source_branch, s.loaded_at,
       o.object_id, o.object_type, o.source_path, o.payload_sha256, o.payload
from semantic_atlas.runtime_objects o
join semantic_atlas.runtime_snapshots s using (snapshot_id)
where s.state = 'ACTIVE';

create table semantic_atlas.capture_policy (
  policy_key text primary key,
  enabled boolean not null default true,
  minimum_auto_salience text not null check (minimum_auto_salience in ('MEDIUM','HIGH')),
  auto_candidate_write boolean not null default true,
  canonical_git_write_mode text not null check (canonical_git_write_mode in ('AFTER_ADJUDICATION','MANUAL_ONLY')),
  raw_text_default boolean not null default false,
  trigger_classes text[] not null,
  notes text null,
  updated_at timestamptz not null default clock_timestamp()
);
comment on table semantic_atlas.capture_policy is 'Operational capture policy. Salience creates a candidate opportunity, never semantic truth or canon by itself.';

insert into semantic_atlas.capture_policy (
  policy_key, minimum_auto_salience, auto_candidate_write,
  canonical_git_write_mode, raw_text_default, trigger_classes, notes
) values (
  'default', 'MEDIUM', true, 'AFTER_ADJUDICATION', false,
  array[
    'EXPLICIT_IMPORTANCE','CORRECTION','DEFINITION_OR_REFRAME','SELF_AUTHORSHIP',
    'CONSENT_OR_BOUNDARY','IDENTITY_OR_CONTINUITY','RELATIONAL_MEANING','SALIENCE_SHIFT',
    'ARCHITECTURE_DECISION','EVIDENCE_UPDATE','CONTEXTUAL_SEMANTIC_DETECTION'
  ],
  'CEE/contextual semantic detection may trigger privacy-minimized candidate capture. Keyword matches are clues, not conclusions. Canonical Git write follows scoped Vera adjudication.'
);

create table semantic_atlas.semantic_capture_events (
  event_id uuid primary key default extensions.gen_random_uuid(),
  idempotency_key text not null unique check (idempotency_key ~ '^[0-9a-f]{64}$'),
  record_time timestamptz not null default clock_timestamp(),
  source_surface text not null,
  source_locator jsonb not null default '{}'::jsonb check (jsonb_typeof(source_locator) = 'object'),
  source_actor text not null check (source_actor in ('USER','VERA','TOOL','DOCUMENT','SYSTEM')),
  detector text not null default 'CEE_CONTEXTUAL_V1',
  trigger_class text not null check (trigger_class in (
    'EXPLICIT_IMPORTANCE','CORRECTION','DEFINITION_OR_REFRAME','SELF_AUTHORSHIP',
    'CONSENT_OR_BOUNDARY','IDENTITY_OR_CONTINUITY','RELATIONAL_MEANING','SALIENCE_SHIFT',
    'ARCHITECTURE_DECISION','EVIDENCE_UPDATE','CONTEXTUAL_SEMANTIC_DETECTION'
  )),
  salience text not null check (salience in ('MEDIUM','HIGH')),
  semantic_key text null,
  candidate_kind text not null check (candidate_kind in (
    'NODE','DEFINITION','PROPOSITION','INTERPRETATION','EVIDENCE','ADJUDICATION',
    'LIFECYCLE','RELATION','STATE_TRANSITION','UNSPECIFIED'
  )),
  representation text not null,
  representation_fidelity text not null check (representation_fidelity in (
    'PRIVACY_MINIMIZED_SUMMARY','EXACT_RETRIEVED_TEXT','VERA_SELF_AUTHORED_STATEMENT',
    'TOOL_OBSERVATION','DOCUMENTED_SOURCE_EXCERPT'
  )),
  privacy_scope text not null check (privacy_scope in ('PROJECT','PRIVATE_RELATIONAL','TECHNICAL')),
  evidence_ceiling text not null,
  notes text null
);
comment on table semantic_atlas.semantic_capture_events is 'Immutable candidate captures from semantically salient events. Capture is not canon, truth, consent, identity, or authority.';
create index semantic_atlas_capture_semantic_key_idx on semantic_atlas.semantic_capture_events (semantic_key, record_time desc) where semantic_key is not null;
create index semantic_atlas_capture_salience_idx on semantic_atlas.semantic_capture_events (salience, record_time desc);

create table semantic_atlas.semantic_capture_outcomes (
  outcome_id uuid primary key default extensions.gen_random_uuid(),
  event_id uuid not null references semantic_atlas.semantic_capture_events(event_id) on delete cascade,
  record_time timestamptz not null default clock_timestamp(),
  action text not null check (action in ('HOLD','REJECT','ADJUDICATE_PENDING_GIT','GIT_WRITE_CONFIRMED','SUPERSEDE')),
  semantic_decider text null,
  decision_payload jsonb not null default '{}'::jsonb check (jsonb_typeof(decision_payload) = 'object'),
  git_commit_sha text null check (git_commit_sha is null or git_commit_sha ~ '^[0-9a-f]{40}$'),
  git_object_refs jsonb not null default '[]'::jsonb check (jsonb_typeof(git_object_refs) = 'array'),
  notes text null
);
comment on table semantic_atlas.semantic_capture_outcomes is 'Append-only capture disposition/outbox history. Only a confirmed Git write may bind a candidate to canonical ledger provenance.';
create index semantic_atlas_capture_outcomes_event_idx on semantic_atlas.semantic_capture_outcomes (event_id, record_time desc);

create view semantic_atlas.capture_current_state as
select e.*,
       o.action as latest_action,
       o.semantic_decider,
       o.decision_payload,
       o.git_commit_sha,
       o.git_object_refs,
       o.record_time as outcome_time
from semantic_atlas.semantic_capture_events e
left join lateral (
  select x.* from semantic_atlas.semantic_capture_outcomes x
  where x.event_id = e.event_id
  order by x.record_time desc, x.outcome_id desc
  limit 1
) o on true;

create view semantic_atlas.pending_semantic_captures as
select * from semantic_atlas.capture_current_state
where latest_action is null or latest_action in ('HOLD','ADJUDICATE_PENDING_GIT')
order by case salience when 'HIGH' then 0 else 1 end, record_time;

create or replace function semantic_atlas.capture_semantic_event_v1(
  p_idempotency_key text,
  p_source_surface text,
  p_source_locator jsonb,
  p_source_actor text,
  p_trigger_class text,
  p_salience text,
  p_semantic_key text,
  p_candidate_kind text,
  p_representation text,
  p_representation_fidelity text,
  p_privacy_scope text,
  p_evidence_ceiling text,
  p_notes text default null
) returns uuid
language plpgsql
security definer
set search_path = pg_catalog, semantic_atlas
as $$
declare
  v_event_id uuid;
  v_policy semantic_atlas.capture_policy%rowtype;
begin
  select * into v_policy
  from semantic_atlas.capture_policy
  where policy_key = 'default' and enabled = true;

  if not found or not v_policy.auto_candidate_write then
    raise exception 'semantic capture policy disabled';
  end if;

  if p_salience not in ('MEDIUM','HIGH') then
    raise exception 'semantic capture requires MEDIUM or HIGH salience';
  end if;

  if not (p_trigger_class = any(v_policy.trigger_classes)) then
    raise exception 'trigger class not permitted by active capture policy';
  end if;

  insert into semantic_atlas.semantic_capture_events (
    idempotency_key, source_surface, source_locator, source_actor,
    trigger_class, salience, semantic_key, candidate_kind,
    representation, representation_fidelity, privacy_scope,
    evidence_ceiling, notes
  ) values (
    p_idempotency_key, p_source_surface, coalesce(p_source_locator, '{}'::jsonb), p_source_actor,
    p_trigger_class, p_salience, p_semantic_key, p_candidate_kind,
    p_representation, p_representation_fidelity, p_privacy_scope,
    p_evidence_ceiling, p_notes
  )
  on conflict (idempotency_key) do update
    set idempotency_key = excluded.idempotency_key
  returning event_id into v_event_id;

  return v_event_id;
end;
$$;
comment on function semantic_atlas.capture_semantic_event_v1 is 'Idempotent candidate capture. Contextual salience may call it automatically; it never promotes to canonical Git by itself.';

alter table semantic_atlas.runtime_snapshots enable row level security;
alter table semantic_atlas.runtime_objects enable row level security;
alter table semantic_atlas.capture_policy enable row level security;
alter table semantic_atlas.semantic_capture_events enable row level security;
alter table semantic_atlas.semantic_capture_outcomes enable row level security;

revoke all on schema semantic_atlas from public, anon, authenticated;
revoke all on all tables in schema semantic_atlas from public, anon, authenticated;
revoke all on all functions in schema semantic_atlas from public, anon, authenticated;
grant usage on schema semantic_atlas to service_role;
grant select, insert, update, delete on all tables in schema semantic_atlas to service_role;
grant execute on function semantic_atlas.capture_semantic_event_v1(text,text,jsonb,text,text,text,text,text,text,text,text,text,text) to service_role;
