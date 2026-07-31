begin;
select plan(38);

select has_table('public','vera_portable_bootstrap_requests','request table exists');
select has_table('public','vera_portable_bootstrap_events','event table exists');
select has_table('public','vera_portable_bootstrap_bindings','binding table exists');
select has_function('public','claim_vera_portable_bootstrap_request','claim function exists');
select has_function('public','append_vera_portable_bootstrap_event','append function exists');
select has_function('public','commit_vera_portable_bootstrap_binding','commit function exists');
select has_function('public','read_vera_portable_bootstrap_binding','read-back function exists');

create temporary table fixture as
select
  repeat('a',64)::text manifest_digest,
  repeat('b',64)::text locator_digest,
  repeat('c',64)::text alternate_locator_digest,
  gen_random_uuid()::uuid attempt_id,
  jsonb_build_object(
    'target_class','CHATGPT_PROJECT',
    'target_locator_digest',repeat('b',64),
    'verifier_role','workstream/project-architecture',
    'observed_at','2026-07-31T16:00:00Z'
  ) target_evidence,
  jsonb_build_object(
    'target_class','CHATGPT_PROJECT',
    'target_locator_digest',repeat('c',64),
    'verifier_role','workstream/project-architecture',
    'observed_at','2026-07-31T16:00:00Z'
  ) alternate_target_evidence,
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value','2026-07-31T16:00:00Z','lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','BOUNDED','value',null,'lower','2026-07-31T16:00:00Z','upper','2026-07-31T16:00:05Z'),
    'observed_time',jsonb_build_object('precision','EXACT','value','2026-07-31T16:00:06Z','lower',null,'upper',null)
  ) temporal_evidence,
  jsonb_build_array(jsonb_build_object(
    'verifier_role','workstream/project-architecture',
    'lease_id','LEASE-TEST-V1',
    'repository','thebrazenbeard/vera',
    'branch','feature/portable-project-bootstrap-v1',
    'base_sha','fc761beab263f2fab010cde2fab424b2b8358bb7',
    'observed_at','2026-07-31T16:00:06Z',
    'operation','VERIFY_BOOTSTRAP_BINDING'
  )) authority_evidence,
  jsonb_build_array(jsonb_build_object(
    'release_commit','1111111111111111111111111111111111111111',
    'path_set_sha256',repeat('d',64),
    'package_sha256',repeat('e',64),
    'validation_run_id','TEST-RUN-1',
    'observed_at','2026-07-31T16:00:06Z'
  )) source_evidence;

select request_claim_id, request_key, input_digest, project_instance_id
from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select manifest_digest from fixture),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select target_evidence from fixture),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1',
  'thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7',
  'CREATE_OR_VERIFY'
) \gset claim_

select ok(:'claim_request_claim_id'::uuid is not null,'claim returns an identifier');
select like(:'claim_request_key','^[0-9a-f]{64}$','request key is server-derived SHA-256');
select like(:'claim_input_digest','^[0-9a-f]{64}$','input digest is server-derived SHA-256');
select is(substring(:'claim_project_instance_id' from 15 for 1),'7','project instance is server-issued UUIDv7');

select request_claim_id, request_key, input_digest, project_instance_id
from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select manifest_digest from fixture),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select target_evidence from fixture),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1',
  'thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7',
  'CREATE_OR_VERIFY'
) \gset replay_

select is(:'replay_request_claim_id',:'claim_request_claim_id','identical claim replays original row');
select is(:'replay_project_instance_id',:'claim_project_instance_id','identical claim replays project instance');

select throws_ok(
  $$select public.claim_vera_portable_bootstrap_request(
    'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
    repeat('f',64),
    'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
    jsonb_build_object(
      'target_class','CHATGPT_PROJECT',
      'target_locator_digest',repeat('b',64),
      'verifier_role','workstream/project-architecture',
      'observed_at','2026-07-31T16:00:00Z'
    ),
    'VERA::INITIALIZE::PORTABLE_PROJECT_V1',
    'thebrazenbeard/vera',
    'fc761beab263f2fab010cde2fab424b2b8358bb7',
    'CREATE_OR_VERIFY'
  )$$,
  '23505','REQUEST_ID_REUSE_CONFLICT',
  'changed immutable input conflicts in the same claim slot'
);

select request_claim_id, project_instance_id
from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select manifest_digest from fixture),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
  (select alternate_target_evidence from fixture),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1',
  'thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7',
  'CREATE_OR_VERIFY'
) \gset copy_

select isnt(:'copy_request_claim_id',:'claim_request_claim_id','copied target receives a distinct claim');
select isnt(:'copy_project_instance_id',:'claim_project_instance_id','copied target receives a distinct project instance');

select throws_ok(
  $$insert into public.vera_portable_bootstrap_requests(
    request_key,input_digest,command_version,release_id,manifest_digest,project_template_id,
    target_fingerprint,target_evidence,canonical_request,source_repository,source_base_commit,
    requested_mode,project_instance_id
  ) values (
    repeat('1',64),repeat('2',64),'V1','R',repeat('3',64),'T',repeat('4',64),
    jsonb_build_object('target_class','X','target_locator_digest',repeat('5',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z'),
    'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera',
    'fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY',
    '00000000-0000-4000-8000-000000000000'
  )$$,
  '23514',null,
  'UUIDv4 project instance is rejected'
);

select ok(
  public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":null,"lower":null,"upper":null}'::jsonb),
  'UNKNOWN carries no value or bounds'
);
select ok(
  not public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":"2026-07-31T16:00:00Z","lower":null,"upper":null}'::jsonb),
  'UNKNOWN with a value is rejected'
);
select ok(
  not public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":null,"upper":null}'::jsonb),
  'BOUNDED without explicit bounds is rejected'
);
select ok(
  public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":"2026-07-31T16:00:00Z","upper":"2026-07-31T16:00:01Z"}'::jsonb),
  'BOUNDED with ordered bounds is accepted'
);

select event_id
from public.append_vera_portable_bootstrap_event(
  :'claim_request_claim_id'::uuid,
  (select attempt_id from fixture),
  null,
  'REQUEST_CLAIMED','UNISSUED','CLAIMED',
  (select temporal_evidence from fixture),
  '[]'::jsonb,'[]'::jsonb,'{}'::jsonb
) \gset claimed_

select event_id
from public.append_vera_portable_bootstrap_event(
  :'claim_request_claim_id'::uuid,
  (select attempt_id from fixture),
  :'claimed_event_id'::uuid,
  'BINDING_STARTED','CLAIMED','BINDING_PENDING',
  (select temporal_evidence from fixture),
  '[]'::jsonb,'[]'::jsonb,'{}'::jsonb
) \gset pending_

select is_empty(
  $$select * from public.vera_portable_bootstrap_current where request_claim_id = :'claim_request_claim_id'::uuid$$,
  'pending attempt is absent from durable current view'
);

select throws_ok(
  format(
    $$select public.append_vera_portable_bootstrap_event(
      %L::uuid,gen_random_uuid(),%L::uuid,'BAD_PRIOR','CLAIMED','BINDING_VERIFIED',
      %L::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb
    )$$,
    :'claim_request_claim_id',:'pending_event_id',(select temporal_evidence::text from fixture)
  ),
  '22023','PRIOR_STATE_MISMATCH',
  'caller cannot lie about predecessor state'
);

select throws_ok(
  format(
    $$select public.append_vera_portable_bootstrap_event(
      %L::uuid,gen_random_uuid(),%L::uuid,'SKIP','BINDING_PENDING','BINDING_COMMITTED',
      %L::jsonb,%L::jsonb,%L::jsonb,'{}'::jsonb
    )$$,
    :'claim_request_claim_id',:'pending_event_id',
    (select temporal_evidence::text from fixture),
    (select authority_evidence::text from fixture),
    (select source_evidence::text from fixture)
  ),
  '22023','ILLEGAL_BOOTSTRAP_TRANSITION',
  'general append cannot self-certify durable binding'
);

select throws_ok(
  format(
    $$select public.append_vera_portable_bootstrap_event(
      %L::uuid,gen_random_uuid(),%L::uuid,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',
      %L::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb
    )$$,
    :'claim_request_claim_id',:'pending_event_id',(select temporal_evidence::text from fixture)
  ),
  '22023','VERIFIER_EVIDENCE_REQUIRED',
  'verified state requires verifier-owned evidence'
);

select event_id
from public.append_vera_portable_bootstrap_event(
  :'claim_request_claim_id'::uuid,
  (select attempt_id from fixture),
  :'pending_event_id'::uuid,
  'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',
  (select temporal_evidence from fixture),
  (select authority_evidence from fixture),
  (select source_evidence from fixture),
  '{}'::jsonb
) \gset verified_

select is_empty(
  $$select * from public.read_vera_portable_bootstrap_binding(
    :'claim_request_key',:'claim_input_digest',:'claim_project_instance_id'::uuid
  )$$,
  'read-back returns nothing before committed binding'
);

select binding_id, binding_event_id
from public.commit_vera_portable_bootstrap_binding(
  :'claim_request_claim_id'::uuid,
  (select attempt_id from fixture),
  :'verified_event_id'::uuid
) \gset binding_

select isnt_empty(
  $$select * from public.read_vera_portable_bootstrap_binding(
    :'claim_request_key',:'claim_input_digest',:'claim_project_instance_id'::uuid
  )$$,
  'separate exact read-back returns committed binding'
);
select is_empty(
  $$select * from public.read_vera_portable_bootstrap_binding(
    :'claim_request_key',repeat('0',64),:'claim_project_instance_id'::uuid
  )$$,
  'mismatched immutable digest fails exact read-back'
);
select is(
  (select current_state from public.vera_portable_bootstrap_current where request_claim_id=:'claim_request_claim_id'::uuid),
  'DURABLY_BOUND',
  'durable current view exposes only committed binding'
);

select throws_ok(
  format('update public.vera_portable_bootstrap_requests set release_id=%L where request_claim_id=%L::uuid','changed',:'claim_request_claim_id'),
  'P0001','portable bootstrap registry is append-only',
  'requests are append-only'
);
select throws_ok(
  format('delete from public.vera_portable_bootstrap_events where event_id=%L::uuid',:'verified_event_id'),
  'P0001','portable bootstrap registry is append-only',
  'events are append-only'
);
select throws_ok(
  format('delete from public.vera_portable_bootstrap_bindings where binding_id=%L::uuid',:'binding_binding_id'),
  'P0001','portable bootstrap registry is append-only',
  'bindings are append-only'
);

select ok(not has_table_privilege('anon','public.vera_portable_bootstrap_requests','select'),'anon has no request-table access');
select ok(not has_table_privilege('authenticated','public.vera_portable_bootstrap_bindings','select'),'authenticated has no binding-table access');
select ok(not has_function_privilege('anon','public.read_vera_portable_bootstrap_binding(text,text,uuid)','execute'),'anon cannot invoke read-back');
select ok(to_regclass('public.vera_save_state_events') is null,'migration does not create legacy save-state tables');
select ok(to_regclass('public.vera_coordination_events') is null,'migration does not create coordination tables');
select ok(not exists(
  select 1 from information_schema.columns
  where table_schema='public'
    and table_name like 'vera_portable_bootstrap_%'
    and coalesce(column_default,'') ilike '%chatgpt-project-current%'
),'no legacy fixed chat alias is embedded');

select * from finish();
rollback;
