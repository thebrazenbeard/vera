begin;
select plan(10);
select has_table('public','vera_portable_bootstrap_requests','request table exists');
select has_table('public','vera_portable_bootstrap_events','event table exists');
select has_function('public','claim_vera_portable_bootstrap_request','claim function exists');
select has_function('public','append_vera_portable_bootstrap_event','append function exists');

create temporary table values_v1 as select
 repeat('a',64) request_key, repeat('b',64) input_digest, repeat('c',64) manifest_digest,
 repeat('d',64) target_fingerprint, '0198f4d2-8a6d-7b10-8abc-1234567890ab'::uuid project_instance_id,
 gen_random_uuid() attempt_id;

select request_claim_id first_claim from public.claim_vera_portable_bootstrap_request(
 (select request_key from values_v1),(select input_digest from values_v1),'V1','R7A1',
 (select manifest_digest from values_v1),'urn:vera:template:r7a1',(select target_fingerprint from values_v1),
 'VERA::INITIALIZE::PORTABLE_PROJECT_V1',(select project_instance_id from values_v1),'CANDIDATE_UNPERSISTED') \gset
select is((select request_claim_id::text from public.claim_vera_portable_bootstrap_request(
 (select request_key from values_v1),(select input_digest from values_v1),'V1','R7A1',
 (select manifest_digest from values_v1),'urn:vera:template:r7a1',(select target_fingerprint from values_v1),
 'VERA::INITIALIZE::PORTABLE_PROJECT_V1',(select project_instance_id from values_v1),'CANDIDATE_UNPERSISTED')),
 :'first_claim','same request replays original claim');
select throws_ok($$select public.claim_vera_portable_bootstrap_request(repeat('a',64),repeat('e',64),'V1','R7A1',repeat('c',64),'urn:vera:template:r7a1',repeat('d',64),'VERA::INITIALIZE::PORTABLE_PROJECT_V1','0198f4d2-8a6d-7b10-8abc-1234567890ab','CANDIDATE_UNPERSISTED')$$,'23505','REQUEST_ID_REUSE_CONFLICT','changed digest conflicts');

select event_id first_event from public.append_vera_portable_bootstrap_event(
 :'first_claim',(select attempt_id from values_v1),null,'REQUEST_CLAIMED','CANDIDATE_UNPERSISTED','BINDING_PENDING',
 null,null,null,clock_timestamp(),'UNKNOWN','[]','[]','{}') \gset
select throws_ok($$select public.append_vera_portable_bootstrap_event(:'first_claim',gen_random_uuid(),null,'FORK','BINDING_PENDING','DURABLY_BOUND',null,null,null,clock_timestamp(),'UNKNOWN','[]','[]','{}')$$,'40001','STALE_OR_CONFLICTING_PREDECESSOR','stale predecessor rejected');
select throws_ok(format('update public.vera_portable_bootstrap_requests set release_id=%L where request_claim_id=%L::uuid','changed',:'first_claim'),'P0001','portable bootstrap registry is append-only','requests append-only');
select throws_ok(format('delete from public.vera_portable_bootstrap_events where event_id=%L::uuid',:'first_event'),'P0001','portable bootstrap registry is append-only','events append-only');
select is((select current_state from public.vera_portable_bootstrap_current where request_claim_id=:'first_claim'),'BINDING_PENDING','current view returns leaf');
select ok(not exists(select 1 from information_schema.columns where table_schema='public' and table_name='vera_portable_bootstrap_requests' and coalesce(column_default,'') ilike '%chatgpt-project-current%'),'no legacy branch alias default');
select ok(not exists(select 1 from information_schema.columns where table_schema='public' and table_name='vera_portable_bootstrap_requests' and coalesce(column_default,'') ilike '%vera-chatgpt-instance%'),'no legacy project alias default');
select * from finish();
rollback;
