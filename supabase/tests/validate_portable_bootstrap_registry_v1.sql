begin;
select no_plan();

select has_table('public','vera_portable_bootstrap_requests','request table');
select has_table('public','vera_portable_bootstrap_events','event table');
select has_table('public','vera_portable_bootstrap_bindings','binding table');
select has_table('public','vera_portable_bootstrap_readback_confirmations','read-back confirmation table');
select has_function('public','claim_vera_portable_bootstrap_request','claim function');
select has_function('public','append_vera_portable_bootstrap_event','append function');
select has_function('public','commit_vera_portable_bootstrap_binding','commit function');
select has_function('public','read_vera_portable_bootstrap_binding','read-back function');
select has_function('public','confirm_vera_portable_bootstrap_readback','confirmation function');

create temporary table f as
select
  repeat('a',64)::text as manifest,
  gen_random_uuid() as attempt,
  gen_random_uuid() as other_attempt,
  jsonb_build_object(
    'target_class','CHATGPT_PROJECT',
    'target_locator_digest',repeat('b',64),
    'verifier_role','workstream/project-architecture',
    'observed_at','2026-07-31T16:00:00Z'
  ) as target,
  jsonb_build_object(
    'target_class','CHATGPT_PROJECT',
    'target_locator_digest',repeat('c',64),
    'verifier_role','workstream/project-architecture',
    'observed_at','2026-07-31T16:00:00Z'
  ) as target2,
  jsonb_build_array(jsonb_build_object(
    'verifier_role','workstream/project-architecture',
    'lease_id','LEASE-TEST-V1',
    'repository','thebrazenbeard/vera',
    'branch','feature/portable-project-bootstrap-v1',
    'base_sha','fc761beab263f2fab010cde2fab424b2b8358bb7',
    'observed_at','2026-07-31T16:00:06Z',
    'operation','VERIFY_BOOTSTRAP_BINDING'
  )) as authority,
  jsonb_build_array(jsonb_build_object(
    'release_commit',repeat('1',40),
    'path_set_sha256',repeat('d',64),
    'package_sha256',repeat('e',64),
    'validation_run_id','TEST-RUN-1',
    'observed_at','2026-07-31T16:00:06Z'
  )) as source,
  clock_timestamp() - interval '4 seconds' as t1,
  clock_timestamp() - interval '3 seconds' as t2,
  clock_timestamp() - interval '2 seconds' as t3,
  clock_timestamp() - interval '1 second' as t4;

select is(
  public.vera_authority_evidence_digest((select authority from f))::text,
  '44861f81ab53f0c965d260119b43856da21c0e3e88f31698a6458a2b4fd3efea'::text,
  'authority evidence SQL/Python known vector'::text
);
select is(
  public.vera_source_evidence_digest((select source from f))::text,
  '31a00cdfa13149b44a70977236478a2a9c57b9f2f2a169317883cf68ef6a9e37'::text,
  'source evidence SQL/Python known vector'::text
);
select ok(public.vera_valid_authority_evidence((select authority from f)),'authority evidence valid');
select ok(public.vera_valid_source_evidence((select source from f)),'source evidence valid');
select ok(not public.vera_valid_authority_evidence((select authority || authority from f)),'duplicate authority tuple rejected');
select ok(not public.vera_valid_source_evidence((select source || source from f)),'duplicate source tuple rejected');

select request_claim_id,request_key,input_digest,project_instance_id from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target from f),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY'
) \gset c_
select ok(:'c_request_claim_id'::uuid is not null,'claim id');
select matches(:'c_request_key'::text,'^[0-9a-f]{64}$'::text,'server request key'::text);
select matches(:'c_input_digest'::text,'^[0-9a-f]{64}$'::text,'server input digest'::text);
select is(substring(:'c_project_instance_id'::text from 15 for 1)::text,'7'::text,'server UUIDv7'::text);

select request_claim_id,request_key,input_digest,project_instance_id from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target from f),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY'
) \gset r_
select is(:'r_request_claim_id'::uuid,:'c_request_claim_id'::uuid,'identical replay claim'::text);
select is(:'r_project_instance_id'::uuid,:'c_project_instance_id'::uuid,'identical replay instance'::text);
select is(:'r_request_key'::text,:'c_request_key'::text,'identical replay request key'::text);
select is(:'r_input_digest'::text,:'c_input_digest'::text,'identical replay input digest'::text);

select throws_ok(
  $$select public.claim_vera_portable_bootstrap_request(
    'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',repeat('f',64),
    'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',
    jsonb_build_object('target_class','CHATGPT_PROJECT','target_locator_digest',repeat('b',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z'),
    'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera',
    'fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY')$$,
  '23505','REQUEST_ID_REUSE_CONFLICT','changed immutable conflict'
);

select request_claim_id,project_instance_id from public.claim_vera_portable_bootstrap_request(
  'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),
  'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target2 from f),
  'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera',
  'fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY'
) \gset x_
select isnt(:'x_request_claim_id'::uuid,:'c_request_claim_id'::uuid,'copied target distinct claim'::text);
select isnt(:'x_project_instance_id'::uuid,:'c_project_instance_id'::uuid,'copied target distinct instance'::text);

select ok(public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":null,"lower":null,"upper":null}'),'UNKNOWN empty valid');
select ok(not public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":"2026-07-31T16:00:00Z","lower":null,"upper":null}'),'UNKNOWN value rejected');
select ok(not public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":null,"upper":null}'),'BOUNDED needs bounds');
select ok(public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":"2026-07-31T16:00:00Z","upper":"2026-07-31T16:00:01Z"}'),'BOUNDED valid');

select event_id from public.append_vera_portable_bootstrap_event(
  :'c_request_claim_id'::uuid,(select attempt from f),null,'REQUEST_CLAIMED','UNISSUED','CLAIMED',
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value',(select t1 from f),'lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'observed_time',jsonb_build_object('precision','EXACT','value',(select t1 from f),'lower',null,'upper',null)
  ),'[]','[]','{}'
) \gset e1_

select event_id from public.append_vera_portable_bootstrap_event(
  :'c_request_claim_id'::uuid,(select attempt from f),:'e1_event_id'::uuid,'BINDING_STARTED','CLAIMED','BINDING_PENDING',
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value',(select t2 from f),'lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'observed_time',jsonb_build_object('precision','EXACT','value',(select t2 from f),'lower',null,'upper',null)
  ),'[]','[]','{}'
) \gset e2_

select is_empty($$select * from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'::uuid$$,'pending absent from durable view');

select throws_ok(format(
  $$select public.append_vera_portable_bootstrap_event(%L::uuid,%L::uuid,%L::uuid,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',%L::jsonb,%L::jsonb,%L::jsonb,'{}'::jsonb)$$,
  :'c_request_claim_id',(select other_attempt::text from f),:'e2_event_id',
  jsonb_build_object('event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'state_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null),'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'observed_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null))::text,
  (select authority::text from f),(select source::text from f)
),'40001','STALE_OR_CONFLICTING_PREDECESSOR','cross-attempt predecessor rejected');

select throws_ok(format(
  $$select public.append_vera_portable_bootstrap_event(%L::uuid,%L::uuid,%L::uuid,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',%L::jsonb,%L::jsonb,%L::jsonb,'{}'::jsonb)$$,
  :'c_request_claim_id',(select attempt::text from f),:'e2_event_id',
  (select temporal_evidence::text from public.vera_portable_bootstrap_events where event_id=:'e2_event_id'::uuid),
  (select authority::text from f),(select source::text from f)
),'22023','NON_MONOTONIC_OR_REUSED_TEMPORAL_EVIDENCE','reused temporal evidence rejected');

select throws_ok(format(
  $$select public.append_vera_portable_bootstrap_event(%L::uuid,%L::uuid,%L::uuid,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',%L::jsonb,'[]'::jsonb,'[]'::jsonb,'{}'::jsonb)$$,
  :'c_request_claim_id',(select attempt::text from f),:'e2_event_id',
  jsonb_build_object('event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'state_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null),'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'observed_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null))::text
),'22023','VERIFIER_EVIDENCE_REQUIRED','verified state requires evidence');

select event_id from public.append_vera_portable_bootstrap_event(
  :'c_request_claim_id'::uuid,(select attempt from f),:'e2_event_id'::uuid,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'observed_time',jsonb_build_object('precision','EXACT','value',(select t3 from f),'lower',null,'upper',null)
  ),(select authority from f),(select source from f),'{}'
) \gset e3_

select is_empty($$select * from public.read_vera_portable_bootstrap_binding(:'c_request_key'::text,:'c_input_digest'::text,:'c_project_instance_id'::uuid)$$,'no precommit read-back');

select throws_ok(format(
  $$select public.commit_vera_portable_bootstrap_binding(%L::uuid,%L::uuid,%L::uuid,%L::jsonb)$$,
  :'c_request_claim_id',(select other_attempt::text from f),:'e3_event_id',
  jsonb_build_object('event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'state_time',jsonb_build_object('precision','EXACT','value',(select t4 from f),'lower',null,'upper',null),'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),'observed_time',jsonb_build_object('precision','EXACT','value',(select t4 from f),'lower',null,'upper',null))::text
),'22023','UNVERIFIED_BINDING_CANNOT_COMMIT','cross-attempt commit rejected');

select throws_ok(format(
  $$select public.commit_vera_portable_bootstrap_binding(%L::uuid,%L::uuid,%L::uuid,%L::jsonb)$$,
  :'c_request_claim_id',(select attempt::text from f),:'e3_event_id',
  (select temporal_evidence::text from public.vera_portable_bootstrap_events where event_id=:'e3_event_id'::uuid)
),'22023','NON_MONOTONIC_OR_REUSED_TEMPORAL_EVIDENCE','commit cannot reuse verification time');

select binding_id,binding_event_id,binding_record_time,authority_evidence_digest,source_evidence_digest
from public.commit_vera_portable_bootstrap_binding(
  :'c_request_claim_id'::uuid,(select attempt from f),:'e3_event_id'::uuid,
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value',(select t4 from f),'lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'observed_time',jsonb_build_object('precision','EXACT','value',(select t4 from f),'lower',null,'upper',null)
  )
) \gset b_

select is_empty($$select * from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'::uuid$$,'commit alone is not durable');

select * from public.read_vera_portable_bootstrap_binding(
  :'c_request_key'::text,:'c_input_digest'::text,:'c_project_instance_id'::uuid
) \gset rb_
select is(:'rb_command_version'::text,'V1'::text,'read-back command version');
select is(:'rb_project_template_id'::text,'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1'::text,'read-back project template');
select is(:'rb_manifest_digest'::text,(select manifest from f)::text,'read-back manifest digest');
select is(:'rb_authority_evidence_digest'::text,:'b_authority_evidence_digest'::text,'read-back authority digest');
select is(:'rb_source_evidence_digest'::text,:'b_source_evidence_digest'::text,'read-back source digest');
select is_empty($$select * from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'::uuid$$,'read alone is not durable');

select throws_ok(format(
  $$select public.confirm_vera_portable_bootstrap_readback(%L::text,%L::text,%L::uuid,%L::uuid,%L::timestamptz,%L::text,%L::text,%L::timestamptz,%L::uuid,'workstream/project-architecture')$$,
  :'c_request_key',:'c_input_digest',:'c_project_instance_id',:'rb_binding_event_id',:'rb_binding_record_time',
  repeat('0',64),:'rb_source_evidence_digest',:'rb_retrieval_time',:'rb_readback_nonce'
),'22023','READBACK_CONFIRMATION_MISMATCH','mismatched confirmation rejected');

select confirmation_id,confirmation_record_time from public.confirm_vera_portable_bootstrap_readback(
  :'c_request_key'::text,:'c_input_digest'::text,:'c_project_instance_id'::uuid,
  :'rb_binding_event_id'::uuid,:'rb_binding_record_time'::timestamptz,
  :'rb_authority_evidence_digest'::text,:'rb_source_evidence_digest'::text,
  :'rb_retrieval_time'::timestamptz,:'rb_readback_nonce'::uuid,
  'workstream/project-architecture'
) \gset cf_
select ok(:'cf_confirmation_id'::uuid is not null,'exact confirmation persisted');
select is((select current_state from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'::uuid)::text,'DURABLY_BOUND'::text,'exact confirmation exposes durable view');

select throws_ok(format(
  $$select public.confirm_vera_portable_bootstrap_readback(%L::text,%L::text,%L::uuid,%L::uuid,%L::timestamptz,%L::text,%L::text,%L::timestamptz,%L::uuid,'workstream/project-architecture')$$,
  :'c_request_key',:'c_input_digest',:'c_project_instance_id',:'rb_binding_event_id',:'rb_binding_record_time',
  :'rb_authority_evidence_digest',repeat('9',64),:'rb_retrieval_time',gen_random_uuid()::text
),'23505','READBACK_ALREADY_CONFIRMED','duplicate or divergent confirmation fails closed');

select throws_ok(format('update public.vera_portable_bootstrap_requests set release_id=%L where request_claim_id=%L::uuid','changed',:'c_request_claim_id'),'55000','portable bootstrap registry is append-only','requests append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_events where event_id=%L::uuid',:'e3_event_id'),'55000','portable bootstrap registry is append-only','events append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_bindings where binding_id=%L::uuid',:'b_binding_id'),'55000','portable bootstrap registry is append-only','bindings append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_readback_confirmations where confirmation_id=%L::uuid',:'cf_confirmation_id'),'55000','portable bootstrap registry is append-only','confirmations append-only');

select ok(not has_table_privilege('anon','public.vera_portable_bootstrap_requests','select'),'anon no request table');
select ok(not has_table_privilege('authenticated','public.vera_portable_bootstrap_bindings','select'),'authenticated no binding table');
select ok(not has_table_privilege('anon','public.vera_portable_bootstrap_readback_confirmations','select'),'anon no confirmation table');
select ok(not has_function_privilege('anon','public.read_vera_portable_bootstrap_binding(text,text,uuid)','execute'),'anon no read-back');
select ok(not has_function_privilege('authenticated','public.confirm_vera_portable_bootstrap_readback(text,text,uuid,uuid,timestamptz,text,text,timestamptz,uuid,text)','execute'),'authenticated no confirmation');
select ok(to_regclass('public.vera_save_state_events') is null,'no save-state table');
select ok(to_regclass('public.vera_coordination_events') is null,'no coordination table');
select ok(not exists(
  select 1 from information_schema.columns
  where table_schema='public' and table_name like 'vera_portable_bootstrap_%'
    and coalesce(column_default,'') ilike '%chatgpt-project-current%'
),'no fixed chat alias');

select * from finish();
rollback;
