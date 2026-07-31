begin;
select plan(38);
select has_table('public','vera_portable_bootstrap_requests','request table');
select has_table('public','vera_portable_bootstrap_events','event table');
select has_table('public','vera_portable_bootstrap_bindings','binding table');
select has_function('public','claim_vera_portable_bootstrap_request','claim function');
select has_function('public','append_vera_portable_bootstrap_event','append function');
select has_function('public','commit_vera_portable_bootstrap_binding','commit function');
select has_function('public','read_vera_portable_bootstrap_binding','read-back function');

create temporary table f as select
  repeat('a',64)::text manifest,
  gen_random_uuid() attempt,
  jsonb_build_object('target_class','CHATGPT_PROJECT','target_locator_digest',repeat('b',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z') target,
  jsonb_build_object('target_class','CHATGPT_PROJECT','target_locator_digest',repeat('c',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z') target2,
  jsonb_build_object(
    'event_time',jsonb_build_object('precision','UNKNOWN','value',null,'lower',null,'upper',null),
    'state_time',jsonb_build_object('precision','EXACT','value','2026-07-31T16:00:00Z','lower',null,'upper',null),
    'effective_time',jsonb_build_object('precision','BOUNDED','value',null,'lower','2026-07-31T16:00:00Z','upper','2026-07-31T16:00:05Z'),
    'observed_time',jsonb_build_object('precision','EXACT','value','2026-07-31T16:00:06Z','lower',null,'upper',null)) temporal,
  jsonb_build_array(jsonb_build_object('verifier_role','workstream/project-architecture','lease_id','LEASE-TEST-V1','repository','thebrazenbeard/vera','branch','feature/portable-project-bootstrap-v1','base_sha','fc761beab263f2fab010cde2fab424b2b8358bb7','observed_at','2026-07-31T16:00:06Z','operation','VERIFY_BOOTSTRAP_BINDING')) authority,
  jsonb_build_array(jsonb_build_object('release_commit',repeat('1',40),'path_set_sha256',repeat('d',64),'package_sha256',repeat('e',64),'validation_run_id','TEST-RUN-1','observed_at','2026-07-31T16:00:06Z')) source;

select request_claim_id,request_key,input_digest,project_instance_id from public.claim_vera_portable_bootstrap_request(
 'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target from f),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera','fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY') \gset c_
select ok(:'c_request_claim_id'::uuid is not null,'claim id');
select like(:'c_request_key','^[0-9a-f]{64}$','server request key');
select like(:'c_input_digest','^[0-9a-f]{64}$','server input digest');
select is(substring(:'c_project_instance_id' from 15 for 1),'7','server UUIDv7');
select request_claim_id,project_instance_id from public.claim_vera_portable_bootstrap_request(
 'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target from f),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera','fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY') \gset r_
select is(:'r_request_claim_id',:'c_request_claim_id','identical replay claim');
select is(:'r_project_instance_id',:'c_project_instance_id','identical replay instance');
select throws_ok($$select public.claim_vera_portable_bootstrap_request('V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',repeat('f',64),'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',jsonb_build_object('target_class','CHATGPT_PROJECT','target_locator_digest',repeat('b',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z'),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera','fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY')$$,'23505','REQUEST_ID_REUSE_CONFLICT','changed immutable conflict');
select request_claim_id,project_instance_id from public.claim_vera_portable_bootstrap_request(
 'V1','VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select manifest from f),'urn:vera:template:VERA_PORTABLE_BOOTSTRAP_R7A1_20260731_V1',(select target2 from f),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera','fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY') \gset x_
select isnt(:'x_request_claim_id',:'c_request_claim_id','copied target distinct claim');
select isnt(:'x_project_instance_id',:'c_project_instance_id','copied target distinct instance');
select throws_ok($$insert into public.vera_portable_bootstrap_requests(request_key,input_digest,command_version,release_id,manifest_digest,project_template_id,target_fingerprint,target_evidence,canonical_request,source_repository,source_base_commit,requested_mode,project_instance_id) values(repeat('1',64),repeat('2',64),'V1','R',repeat('3',64),'T',repeat('4',64),jsonb_build_object('target_class','X','target_locator_digest',repeat('5',64),'verifier_role','workstream/project-architecture','observed_at','2026-07-31T16:00:00Z'),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','thebrazenbeard/vera','fc761beab263f2fab010cde2fab424b2b8358bb7','CREATE_OR_VERIFY','00000000-0000-4000-8000-000000000000')$$,'23514',null,'UUIDv4 rejected');
select ok(public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":null,"lower":null,"upper":null}'),'UNKNOWN empty valid');
select ok(not public.vera_valid_temporal_point('{"precision":"UNKNOWN","value":"2026-07-31T16:00:00Z","lower":null,"upper":null}'),'UNKNOWN value rejected');
select ok(not public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":null,"upper":null}'),'BOUNDED needs bounds');
select ok(public.vera_valid_temporal_point('{"precision":"BOUNDED","value":null,"lower":"2026-07-31T16:00:00Z","upper":"2026-07-31T16:00:01Z"}'),'BOUNDED valid');

select event_id from public.append_vera_portable_bootstrap_event(:'c_request_claim_id',(select attempt from f),null,'REQUEST_CLAIMED','UNISSUED','CLAIMED',(select temporal from f),'[]','[]','{}') \gset e1_
select event_id from public.append_vera_portable_bootstrap_event(:'c_request_claim_id',(select attempt from f),:'e1_event_id','BINDING_STARTED','CLAIMED','BINDING_PENDING',(select temporal from f),'[]','[]','{}') \gset e2_
select is_empty($$select * from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'$$,'pending absent from durable view');
select throws_ok(format($$select public.append_vera_portable_bootstrap_event(%L,gen_random_uuid(),%L,'BAD','CLAIMED','BINDING_VERIFIED',%L,'[]','[]','{}')$$,:'c_request_claim_id',:'e2_event_id',(select temporal::text from f)),'22023','PRIOR_STATE_MISMATCH','prior mismatch');
select throws_ok(format($$select public.append_vera_portable_bootstrap_event(%L,gen_random_uuid(),%L,'SKIP','BINDING_PENDING','BINDING_COMMITTED',%L,%L,%L,'{}')$$,:'c_request_claim_id',:'e2_event_id',(select temporal::text from f),(select authority::text from f),(select source::text from f)),'22023','ILLEGAL_BOOTSTRAP_TRANSITION','direct durable commit rejected');
select throws_ok(format($$select public.append_vera_portable_bootstrap_event(%L,gen_random_uuid(),%L,'BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',%L,'[]','[]','{}')$$,:'c_request_claim_id',:'e2_event_id',(select temporal::text from f)),'22023','VERIFIER_EVIDENCE_REQUIRED','evidence required');
select event_id from public.append_vera_portable_bootstrap_event(:'c_request_claim_id',(select attempt from f),:'e2_event_id','BINDING_EVIDENCE_VERIFIED','BINDING_PENDING','BINDING_VERIFIED',(select temporal from f),(select authority from f),(select source from f),'{}') \gset e3_
select is_empty($$select * from public.read_vera_portable_bootstrap_binding(:'c_request_key',:'c_input_digest',:'c_project_instance_id')$$,'no precommit read-back');
select binding_id,binding_event_id from public.commit_vera_portable_bootstrap_binding(:'c_request_claim_id',(select attempt from f),:'e3_event_id') \gset b_
select isnt_empty($$select * from public.read_vera_portable_bootstrap_binding(:'c_request_key',:'c_input_digest',:'c_project_instance_id')$$,'exact read-back');
select is_empty($$select * from public.read_vera_portable_bootstrap_binding(:'c_request_key',repeat('0',64),:'c_project_instance_id')$$,'digest mismatch read-back');
select is((select current_state from public.vera_portable_bootstrap_current where request_claim_id=:'c_request_claim_id'),'DURABLY_BOUND','durable view committed only');
select throws_ok(format('update public.vera_portable_bootstrap_requests set release_id=%L where request_claim_id=%L','changed',:'c_request_claim_id'),'55000','portable bootstrap registry is append-only','requests append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_events where event_id=%L',:'e3_event_id'),'55000','portable bootstrap registry is append-only','events append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_bindings where binding_id=%L',:'b_binding_id'),'55000','portable bootstrap registry is append-only','bindings append-only');
do $r$ begin if not exists(select 1 from pg_roles where rolname='anon') then execute 'create role anon nologin'; end if; if not exists(select 1 from pg_roles where rolname='authenticated') then execute 'create role authenticated nologin'; end if; end $r$;
select ok(not has_table_privilege('anon','public.vera_portable_bootstrap_requests','select'),'anon no table');
select ok(not has_table_privilege('authenticated','public.vera_portable_bootstrap_bindings','select'),'authenticated no table');
select ok(not has_function_privilege('anon','public.read_vera_portable_bootstrap_binding(text,text,uuid)','execute'),'anon no read-back');
select ok(to_regclass('public.vera_save_state_events') is null,'no save-state table');
select ok(to_regclass('public.vera_coordination_events') is null,'no coordination table');
select ok(not exists(select 1 from information_schema.columns where table_schema='public' and table_name like 'vera_portable_bootstrap_%' and coalesce(column_default,'') ilike '%chatgpt-project-current%'),'no fixed chat alias');
select * from finish();
rollback;
