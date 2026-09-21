create table bug_ops.role_registry(
  role_key text primary key check(role_key=upper(role_key) and length(role_key)>0),
  active boolean not null default true,
  registry_revision bigint not null default 1 check(registry_revision>=1),
  created_at timestamptz not null default clock_timestamp(),
  updated_at timestamptz not null default clock_timestamp()
);
insert into bug_ops.role_registry(role_key) values('MUNE'),('MASA'),('VOSS'),('ONE');

alter table bug_ops.system_config
  add column active_queue_name text not null default 'bug_dispatch',
  add column active_dispatch_ledger text not null default 'dispatch_events_v2',
  add column role_registry_revision bigint not null default 1,
  add column pgmq_contract_version text not null default '1.5.1',
  add column pgmq_read_signature text not null default 'pgmq.read(text,integer,integer,jsonb)',
  add column pgmq_read_definition_sha256 text not null default '98ccde1cd0b2887b986b09d40e68cfba56bd0281aff8607308af05cde7067a55',
  add column initial_install_artifacts_state text not null default 'DEPRECATED_INACTIVE_V1_INITIAL_INSTALL';

alter table bug_ops.bug_reports
  add column dispatch_revision bigint not null default 1 check(dispatch_revision>=1),
  add constraint bug_reports_no_steady_reopened check(status<>'REOPENED');

alter table bug_ops.bug_events
  add column dispatch_revision bigint not null default 1 check(dispatch_revision>=1),
  add column dispatch_id uuid,
  add column dispatch_snapshot jsonb,
  add column dispatch_payload_digest text,
  add constraint bug_events_dispatch_bundle_v2_check check(
    (dispatch_id is null and dispatch_snapshot is null and dispatch_payload_digest is null)
    or
    (dispatch_id is not null and jsonb_typeof(dispatch_snapshot)='object' and dispatch_payload_digest ~ '^[0-9a-f]{64}$')
  );
create unique index bug_events_dispatch_id_v2_idx on bug_ops.bug_events(dispatch_id) where dispatch_id is not null;

create table bug_ops.dispatch_events_v2(
  dispatch_event_id uuid primary key default gen_random_uuid(),
  dispatch_id uuid,
  queue_name text not null,
  msg_id bigint not null,
  event_type text not null check(event_type in ('ENQUEUED','HANDLED','STALE','POISON','CLOSED','WRONG_TARGET','UNKNOWN_TARGET_ROLE')),
  bug_id uuid,
  bug_event_id uuid,
  handled_event_id uuid,
  target_role text,
  payload_digest text,
  observed_message jsonb not null,
  note text,
  created_at timestamptz not null default clock_timestamp(),
  check(payload_digest is null or payload_digest ~ '^[0-9a-f]{64}$')
);
create unique index dispatch_events_v2_enqueued_idx on bug_ops.dispatch_events_v2(dispatch_id) where dispatch_id is not null and event_type='ENQUEUED';
create unique index dispatch_events_v2_terminal_idx on bug_ops.dispatch_events_v2(dispatch_id) where dispatch_id is not null and event_type<>'ENQUEUED';
create unique index dispatch_events_v2_carrier_idx on bug_ops.dispatch_events_v2(queue_name,msg_id,event_type);
create trigger dispatch_events_v2_immutable before update or delete on bug_ops.dispatch_events_v2 for each row execute function bug_ops.block_immutable_mutation();

do $$ begin
  if not exists(select 1 from pgmq.meta where queue_name='bug_dispatch') then
    perform pgmq.create('bug_dispatch');
  end if;
end $$;

alter function bug_ops.report_bug(uuid,text,text,text,text,text,text,text,jsonb) rename to report_bug_deprecated_initial_v1;
alter function bug_ops.route_bug(uuid,uuid,bigint,bigint,text,text,text) rename to route_bug_deprecated_initial_v1;
alter function bug_ops.update_bug_status(uuid,uuid,bigint,text,text,text) rename to update_bug_status_deprecated_initial_v1;
alter function bug_ops.claim_work(text,integer,integer) rename to claim_work_deprecated_initial_v1;
alter function bug_ops.ack_work(text,bigint,uuid,text) rename to ack_work_deprecated_initial_v1;
alter function bug_ops.archive_dispatch_internal(text,bigint,text,jsonb,uuid,uuid,uuid,text) rename to archive_dispatch_internal_deprecated_initial_v1;

create or replace function bug_ops.queue_for_role(p_role text) returns text
language plpgsql stable set search_path=''
as $$
declare r text:=upper(btrim(p_role)); ok boolean;
begin
  select active into ok from bug_ops.role_registry where role_key=r;
  if coalesce(ok,false) then return 'bug_dispatch'; end if;
  return null;
end $$;

create function bug_ops.assert_queue_filter_contract() returns void
language plpgsql stable set search_path=''
as $$
declare cfg bug_ops.system_config%rowtype; actual_version text; actual_sig text; actual_digest text;
begin
  select * into cfg from bug_ops.system_config where singleton=true;
  select extversion into actual_version from pg_extension where extname='pgmq';
  select p.oid::regprocedure::text,
         encode(extensions.digest(convert_to(pg_get_functiondef(p.oid),'UTF8'),'sha256'),'hex')
    into actual_sig,actual_digest
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='pgmq' and p.oid::regprocedure::text=cfg.pgmq_read_signature;
  if actual_version is distinct from cfg.pgmq_contract_version
     or actual_sig is distinct from cfg.pgmq_read_signature
     or actual_digest is distinct from cfg.pgmq_read_definition_sha256 then
    raise exception 'QUEUE_FILTER_CONTRACT_REVALIDATE_REQUIRED';
  end if;
end $$;

create function bug_ops.report_bug(
 p_operation_id uuid,p_intake_key text,p_title text,p_description text default '',p_severity text default 'MEDIUM',p_component text default null,p_reported_by text default null,p_assigned_role text default null,p_evidence jsonb default '{}'::jsonb
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_dispatch_revision bigint,out_dispatch_id uuid,out_queue_msg_id bigint,idempotent_replay boolean)
language plpgsql set search_path=''
as $$
declare cfg bug_ops.system_config%rowtype; v_role text; v_payload jsonb; v_digest text; ev bug_ops.bug_events%rowtype; br bug_ops.bug_reports%rowtype; v_bug uuid:=gen_random_uuid(); v_event uuid:=gen_random_uuid(); v_dispatch uuid:=gen_random_uuid(); v_msg bigint; v_snapshot jsonb; v_pdigest text; v_sev text:=upper(btrim(p_severity)); v_key text:=btrim(p_intake_key); v_title text:=btrim(p_title); inserted_id uuid;
begin
 perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));
 select * into cfg from bug_ops.system_config where singleton=true;
 v_role:=coalesce(upper(nullif(btrim(p_assigned_role),'')),cfg.coordinator_role);
 if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_TARGET_ROLE'; end if;
 if v_key is null or length(v_key)=0 then raise exception 'INVALID_INTAKE_KEY'; end if;
 if v_title is null or length(v_title)=0 then raise exception 'INVALID_TITLE'; end if;
 if v_sev not in ('LOW','MEDIUM','HIGH','CRITICAL') then raise exception 'INVALID_SEVERITY'; end if;
 if jsonb_typeof(coalesce(p_evidence,'{}'::jsonb))<>'object' then raise exception 'INVALID_EVIDENCE'; end if;
 v_payload:=jsonb_build_object('kind','REPORT','home_project',cfg.project_key,'intake_key',v_key,'title',v_title,'description',coalesce(p_description,''),'severity',v_sev,'component',p_component,'reported_by',p_reported_by,'assigned_role',v_role,'evidence',coalesce(p_evidence,'{}'::jsonb));
 v_digest:=bug_ops.sha256_jsonb(v_payload);
 select * into ev from bug_ops.bug_events e where e.operation_id=p_operation_id;
 if found then
   if ev.request_digest<>v_digest then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
   return query select ev.bug_id,ev.event_id,ev.state_version,ev.dispatch_revision,ev.dispatch_id,null::bigint,true; return;
 end if;
 insert into bug_ops.bug_reports(bug_id,home_project,intake_key,intake_digest,title,description,severity,status,component,reported_by,assigned_role,state_version,routing_revision,dispatch_revision,evidence)
 values(v_bug,cfg.project_key,v_key,v_digest,v_title,coalesce(p_description,''),v_sev,'NEW',p_component,p_reported_by,v_role,1,1,1,coalesce(p_evidence,'{}'::jsonb))
 on conflict(intake_key) do nothing returning bug_id into inserted_id;
 if inserted_id is null then
   select * into br from bug_ops.bug_reports where intake_key=v_key;
   if br.intake_digest<>v_digest then raise exception 'INTAKE_KEY_REUSE_CONFLICT'; end if;
   select * into ev from bug_ops.bug_events e where e.bug_id=br.bug_id and e.event_type='REPORTED' order by e.state_version limit 1;
   return query select br.bug_id,ev.event_id,br.state_version,br.dispatch_revision,ev.dispatch_id,null::bigint,true; return;
 end if;
 v_snapshot:=jsonb_build_object('dispatch_id',v_dispatch,'bug_id',v_bug,'home_project',cfg.project_key,'event_id',v_event,'state_version',1,'dispatch_revision',1,'target_role',v_role,'action','BUG_REPORTED','operation_id',p_operation_id);
 v_pdigest:=bug_ops.sha256_jsonb(v_snapshot);
 insert into bug_ops.bug_events(event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,operation_id,request_digest,request_payload,details,dispatch_id,dispatch_snapshot,dispatch_payload_digest)
 values(v_event,v_bug,1,1,1,'REPORTED',p_reported_by,p_operation_id,v_digest,v_payload,jsonb_build_object('assigned_role',v_role),v_dispatch,v_snapshot,v_pdigest);
 select s into v_msg from pgmq.send('bug_dispatch',v_snapshot,0) s limit 1;
 insert into bug_ops.dispatch_events_v2(dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,target_role,payload_digest,observed_message)
 values(v_dispatch,'bug_dispatch',v_msg,'ENQUEUED',v_bug,v_event,v_role,v_pdigest,v_snapshot);
 return query select v_bug,v_event,1::bigint,1::bigint,v_dispatch,v_msg,false;
end $$;

create function bug_ops.route_bug(
 p_operation_id uuid,p_bug_id uuid,p_expected_state_version bigint,p_expected_dispatch_revision bigint,p_target_role text,p_actor text default null,p_reason text default null
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_dispatch_revision bigint,out_dispatch_id uuid,out_queue_msg_id bigint,idempotent_replay boolean)
language plpgsql set search_path=''
as $$
declare br bug_ops.bug_reports%rowtype; ev bug_ops.bug_events%rowtype; cfg bug_ops.system_config%rowtype; v_role text:=upper(btrim(p_target_role)); v_payload jsonb; v_digest text; v_event uuid:=gen_random_uuid(); v_dispatch uuid:=gen_random_uuid(); v_msg bigint; v_state bigint; v_dispatch_rev bigint; v_routing bigint; v_snapshot jsonb; v_pdigest text;
begin
 perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));
 select * into cfg from bug_ops.system_config where singleton=true;
 if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_TARGET_ROLE'; end if;
 v_payload:=jsonb_build_object('kind','ROUTE','home_project',cfg.project_key,'bug_id',p_bug_id,'expected_state_version',p_expected_state_version,'expected_dispatch_revision',p_expected_dispatch_revision,'target_role',v_role,'actor',p_actor,'reason',p_reason);
 v_digest:=bug_ops.sha256_jsonb(v_payload);
 select * into ev from bug_ops.bug_events e where e.operation_id=p_operation_id;
 if found then
   if ev.request_digest<>v_digest then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
   return query select ev.bug_id,ev.event_id,ev.state_version,ev.dispatch_revision,ev.dispatch_id,null::bigint,true; return;
 end if;
 select * into br from bug_ops.bug_reports b where b.bug_id=p_bug_id for update;
 if not found then raise exception 'BUG_NOT_FOUND'; end if;
 if br.state_version<>p_expected_state_version then raise exception 'STALE_STATE_VERSION expected %, actual %',p_expected_state_version,br.state_version; end if;
 if br.dispatch_revision<>p_expected_dispatch_revision then raise exception 'STALE_DISPATCH_REVISION expected %, actual %',p_expected_dispatch_revision,br.dispatch_revision; end if;
 if br.status='CLOSED' then raise exception 'BUG_CLOSED'; end if;
 v_state:=br.state_version+1; v_dispatch_rev:=br.dispatch_revision+1; v_routing:=br.routing_revision+1;
 v_snapshot:=jsonb_build_object('dispatch_id',v_dispatch,'bug_id',p_bug_id,'home_project',br.home_project,'event_id',v_event,'state_version',v_state,'dispatch_revision',v_dispatch_rev,'target_role',v_role,'action','ROUTE','operation_id',p_operation_id);
 v_pdigest:=bug_ops.sha256_jsonb(v_snapshot);
 insert into bug_ops.bug_events(event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,operation_id,request_digest,request_payload,details,dispatch_id,dispatch_snapshot,dispatch_payload_digest)
 values(v_event,p_bug_id,v_state,v_routing,v_dispatch_rev,'ROUTED',p_actor,p_operation_id,v_digest,v_payload,jsonb_build_object('from_role',br.assigned_role,'to_role',v_role,'reason',p_reason),v_dispatch,v_snapshot,v_pdigest);
 select s into v_msg from pgmq.send('bug_dispatch',v_snapshot,0) s limit 1;
 insert into bug_ops.dispatch_events_v2(dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,target_role,payload_digest,observed_message)
 values(v_dispatch,'bug_dispatch',v_msg,'ENQUEUED',p_bug_id,v_event,v_role,v_pdigest,v_snapshot);
 update bug_ops.bug_reports set assigned_role=v_role,state_version=v_state,routing_revision=v_routing,dispatch_revision=v_dispatch_rev,updated_at=clock_timestamp() where bug_id=p_bug_id;
 return query select p_bug_id,v_event,v_state,v_dispatch_rev,v_dispatch,v_msg,false;
end $$;

create function bug_ops.update_bug_status(
 p_operation_id uuid,p_bug_id uuid,p_expected_state_version bigint,p_status text,p_actor text default null,p_note text default null
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_dispatch_revision bigint,idempotent_replay boolean)
language plpgsql set search_path=''
as $$
declare br bug_ops.bug_reports%rowtype; ev bug_ops.bug_events%rowtype; cfg bug_ops.system_config%rowtype; v_requested text:=upper(btrim(p_status)); v_current text; v_payload jsonb; v_digest text; v_event uuid:=gen_random_uuid(); v_state bigint; v_dispatch bigint; v_type text;
begin
 perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));
 select * into cfg from bug_ops.system_config where singleton=true;
 v_payload:=jsonb_build_object('kind','STATUS','home_project',cfg.project_key,'bug_id',p_bug_id,'expected_state_version',p_expected_state_version,'status',v_requested,'actor',p_actor,'note',p_note);
 v_digest:=bug_ops.sha256_jsonb(v_payload);
 select * into ev from bug_ops.bug_events e where e.operation_id=p_operation_id;
 if found then
   if ev.request_digest<>v_digest then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
   return query select ev.bug_id,ev.event_id,ev.state_version,ev.dispatch_revision,true; return;
 end if;
 if v_requested not in ('NEW','TRIAGED','IN_PROGRESS','BLOCKED','FIXED','VERIFYING','CLOSED','REOPENED') then raise exception 'INVALID_STATUS'; end if;
 select * into br from bug_ops.bug_reports b where b.bug_id=p_bug_id for update;
 if not found then raise exception 'BUG_NOT_FOUND'; end if;
 if br.state_version<>p_expected_state_version then raise exception 'STALE_STATE_VERSION expected %, actual %',p_expected_state_version,br.state_version; end if;
 if v_requested='REOPENED' and br.status<>'CLOSED' then raise exception 'REOPEN_REQUIRES_CLOSED'; end if;
 if br.status='CLOSED' and v_requested<>'REOPENED' then raise exception 'BUG_CLOSED_REQUIRES_REOPEN'; end if;
 v_state:=br.state_version+1;
 v_dispatch:=br.dispatch_revision + case when v_requested in ('CLOSED','REOPENED') then 1 else 0 end;
 v_type:=case when v_requested='REOPENED' then 'REOPENED' else 'STATUS_CHANGED' end;
 v_current:=case when v_requested='REOPENED' then 'NEW' else v_requested end;
 update bug_ops.bug_reports set status=v_current,state_version=v_state,dispatch_revision=v_dispatch,updated_at=clock_timestamp(),closed_at=case when v_current='CLOSED' then clock_timestamp() else null end where bug_id=p_bug_id;
 insert into bug_ops.bug_events(event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,operation_id,request_digest,request_payload,details)
 values(v_event,p_bug_id,v_state,br.routing_revision,v_dispatch,v_type,p_actor,p_operation_id,v_digest,v_payload,jsonb_build_object('from_status',br.status,'to_status',v_current,'note',p_note));
 return query select p_bug_id,v_event,v_state,v_dispatch,false;
end $$;

create function bug_ops.archive_dispatch_internal_v2(p_msg_id bigint,p_event_type text,p_message jsonb,p_dispatch_id uuid,p_bug_id uuid,p_bug_event_id uuid,p_handled_event_id uuid,p_target_role text,p_note text) returns uuid
language plpgsql set search_path=''
as $$
declare d bug_ops.dispatch_events_v2%rowtype; v_id uuid:=gen_random_uuid(); ok boolean; v_digest text;
begin
 if p_event_type not in ('HANDLED','STALE','POISON','CLOSED','WRONG_TARGET','UNKNOWN_TARGET_ROLE') then raise exception 'INVALID_DISPATCH_EVENT_TYPE'; end if;
 select * into d from bug_ops.dispatch_events_v2 x where x.queue_name='bug_dispatch' and x.msg_id=p_msg_id and x.event_type<>'ENQUEUED' order by x.created_at limit 1;
 if found then
   if d.event_type<>p_event_type then raise exception 'DISPATCH_EVENT_CONFLICT'; end if;
   return d.dispatch_event_id;
 end if;
 select pgmq.archive('bug_dispatch',p_msg_id) into ok;
 if not coalesce(ok,false) then raise exception 'QUEUE_MESSAGE_NOT_ACTIVE'; end if;
 v_digest:=case when p_message is null then null else bug_ops.sha256_jsonb(p_message) end;
 insert into bug_ops.dispatch_events_v2(dispatch_event_id,dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,handled_event_id,target_role,payload_digest,observed_message,note)
 values(v_id,p_dispatch_id,'bug_dispatch',p_msg_id,p_event_type,p_bug_id,p_bug_event_id,p_handled_event_id,p_target_role,v_digest,coalesce(p_message,'null'::jsonb),p_note);
 return v_id;
end $$;

create function bug_ops.claim_work(p_role text,p_visibility_seconds integer default 300,p_qty integer default 10)
returns table(msg_id bigint,read_ct integer,enqueued_at timestamptz,vt timestamptz,message jsonb,headers jsonb,dispatch_id uuid,bug_id uuid,state_version bigint,dispatch_revision bigint,target_role text)
language plpgsql set search_path=''
as $$
declare v_role text:=upper(btrim(p_role)); cfg bug_ops.system_config%rowtype; r pgmq.message_record; br bug_ops.bug_reports%rowtype; ev bug_ops.bug_events%rowtype; enq bug_ops.dispatch_events_v2%rowtype; v_dispatch uuid; v_bug uuid; v_event uuid; v_state bigint; v_rev bigint; v_target text; v_home text; v_digest text;
begin
 perform bug_ops.assert_queue_filter_contract();
 if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_ROLE'; end if;
 if p_visibility_seconds<1 or p_visibility_seconds>86400 then raise exception 'INVALID_VISIBILITY'; end if;
 if p_qty<1 or p_qty>20 then raise exception 'INVALID_QTY'; end if;
 select * into cfg from bug_ops.system_config where singleton=true;
 for r in select * from pgmq.read('bug_dispatch',p_visibility_seconds,p_qty,jsonb_build_object('target_role',v_role)) loop
   begin
     if jsonb_typeof(r.message)<>'object' or not (r.message ?& array['dispatch_id','bug_id','home_project','event_id','state_version','dispatch_revision','target_role','action','operation_id']) then raise exception 'MALFORMED'; end if;
     v_dispatch:=(r.message->>'dispatch_id')::uuid; v_bug:=(r.message->>'bug_id')::uuid; v_event:=(r.message->>'event_id')::uuid; v_state:=(r.message->>'state_version')::bigint; v_rev:=(r.message->>'dispatch_revision')::bigint; v_target:=upper(btrim(r.message->>'target_role')); v_home:=r.message->>'home_project';
   exception when others then
     perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,null,null,null,null,v_role,'malformed envelope'); continue;
   end;
   if v_home<>cfg.project_key then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,v_dispatch,v_bug,v_event,null,v_role,'wrong home_project'); continue; end if;
   if v_target<>v_role then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'WRONG_TARGET',r.message,v_dispatch,v_bug,v_event,null,v_role,'target mismatch'); continue; end if;
   v_digest:=bug_ops.sha256_jsonb(r.message);
   select * into enq from bug_ops.dispatch_events_v2 d where d.dispatch_id=v_dispatch and d.event_type='ENQUEUED';
   if not found or enq.queue_name<>'bug_dispatch' or enq.msg_id<>r.msg_id or enq.bug_id is distinct from v_bug or enq.bug_event_id is distinct from v_event or enq.target_role is distinct from v_role or enq.payload_digest is distinct from v_digest then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,v_dispatch,v_bug,v_event,null,v_role,'dispatch custody mismatch'); continue; end if;
   select * into ev from bug_ops.bug_events e where e.event_id=v_event;
   if not found or ev.bug_id<>v_bug or ev.dispatch_id is distinct from v_dispatch or ev.state_version<>v_state or ev.dispatch_revision<>v_rev or ev.dispatch_payload_digest is distinct from v_digest then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,v_dispatch,v_bug,v_event,null,v_role,'bug event binding mismatch'); continue; end if;
   select b.* into br from bug_ops.bug_reports b where b.bug_id=v_bug;
   if not found then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,v_dispatch,v_bug,v_event,null,v_role,'unknown bug'); continue; end if;
   if br.status='CLOSED' then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'CLOSED',r.message,v_dispatch,v_bug,v_event,null,v_role,'bug closed'); continue; end if;
   if br.assigned_role is distinct from v_role or br.dispatch_revision<>v_rev then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'STALE',r.message,v_dispatch,v_bug,v_event,null,v_role,'dispatch no longer current'); continue; end if;
   if v_state>br.state_version then perform bug_ops.archive_dispatch_internal_v2(r.msg_id,'POISON',r.message,v_dispatch,v_bug,v_event,null,v_role,'future state version'); continue; end if;
   return query select r.msg_id,r.read_ct,r.enqueued_at,r.vt,r.message,r.headers,v_dispatch,v_bug,br.state_version,br.dispatch_revision,v_role;
 end loop;
end $$;

create function bug_ops.ack_work(p_role text,p_msg_id bigint,p_dispatch_id uuid,p_handled_event_id uuid,p_note text default null) returns uuid
language plpgsql set search_path=''
as $$
declare v_role text:=upper(btrim(p_role)); v_message jsonb; enq bug_ops.dispatch_events_v2%rowtype; src bug_ops.bug_events%rowtype; handled bug_ops.bug_events%rowtype; v_digest text;
begin
 if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_ROLE'; end if;
 select * into enq from bug_ops.dispatch_events_v2 d where d.dispatch_id=p_dispatch_id and d.event_type='ENQUEUED';
 if not found or enq.queue_name<>'bug_dispatch' or enq.msg_id<>p_msg_id or enq.target_role is distinct from v_role then raise exception 'ACK_DISPATCH_BINDING_MISMATCH'; end if;
 select message into v_message from pgmq.q_bug_dispatch where msg_id=p_msg_id;
 if v_message is null then raise exception 'QUEUE_MESSAGE_NOT_ACTIVE'; end if;
 v_digest:=bug_ops.sha256_jsonb(v_message);
 if enq.payload_digest is distinct from v_digest then raise exception 'ACK_PAYLOAD_DIGEST_MISMATCH'; end if;
 select * into src from bug_ops.bug_events e where e.event_id=enq.bug_event_id;
 if not found or src.bug_id is distinct from enq.bug_id or src.dispatch_id is distinct from p_dispatch_id then raise exception 'ACK_SOURCE_BINDING_MISMATCH'; end if;
 select * into handled from bug_ops.bug_events e where e.event_id=p_handled_event_id;
 if not found or handled.bug_id<>src.bug_id or handled.state_version<=src.state_version then raise exception 'ACK_REQUIRES_LATER_BUG_EVENT'; end if;
 return bug_ops.archive_dispatch_internal_v2(p_msg_id,'HANDLED',v_message,p_dispatch_id,src.bug_id,src.event_id,p_handled_event_id,v_role,p_note);
end $$;

create function bug_ops.janitor_dispatch(p_qty integer default 20) returns table(msg_id bigint,event_type text)
language plpgsql set search_path=''
as $$
declare r record; v_target text; v_type text;
begin
 if p_qty<1 or p_qty>100 then raise exception 'INVALID_QTY'; end if;
 for r in
   select q.msg_id,q.message from pgmq.q_bug_dispatch q
   where q.vt<=clock_timestamp()
     and (jsonb_typeof(q.message)<>'object' or not(q.message?'target_role') or not exists(select 1 from bug_ops.role_registry rr where rr.role_key=upper(btrim(q.message->>'target_role')) and rr.active))
   order by q.msg_id limit p_qty for update skip locked
 loop
   v_target:=case when jsonb_typeof(r.message)='object' then upper(btrim(r.message->>'target_role')) else null end;
   v_type:=case when v_target is null or length(v_target)=0 then 'POISON' else 'UNKNOWN_TARGET_ROLE' end;
   perform bug_ops.archive_dispatch_internal_v2(r.msg_id,v_type,r.message,null,null,null,null,v_target,case when v_type='POISON' then 'missing/malformed target_role' else 'unknown target_role' end);
   return query select r.msg_id,v_type;
 end loop;
end $$;

revoke all on bug_ops.role_registry,bug_ops.dispatch_events_v2 from public,anon,authenticated,service_role,authenticator;
revoke execute on function bug_ops.report_bug(uuid,text,text,text,text,text,text,text,jsonb),bug_ops.route_bug(uuid,uuid,bigint,bigint,text,text,text),bug_ops.update_bug_status(uuid,uuid,bigint,text,text,text),bug_ops.claim_work(text,integer,integer),bug_ops.ack_work(text,bigint,uuid,uuid,text),bug_ops.janitor_dispatch(integer),bug_ops.archive_dispatch_internal_v2(bigint,text,jsonb,uuid,uuid,uuid,uuid,text,text),bug_ops.assert_queue_filter_contract() from public,anon,authenticated,service_role,authenticator;