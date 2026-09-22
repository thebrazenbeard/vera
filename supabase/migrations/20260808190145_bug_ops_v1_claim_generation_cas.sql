alter function bug_ops.ack_work(text,bigint,uuid,uuid,text) rename to ack_work_pre_claim_generation_cas;

create function bug_ops.ack_work(
  p_role text,
  p_msg_id bigint,
  p_dispatch_id uuid,
  p_expected_read_ct integer,
  p_handled_event_id uuid,
  p_note text default null
) returns uuid
language plpgsql set search_path=''
as $$
declare
  v_role text:=upper(btrim(p_role));
  v_message jsonb;
  v_read_ct integer;
  enq bug_ops.dispatch_events_v2%rowtype;
  src bug_ops.bug_events%rowtype;
  handled bug_ops.bug_events%rowtype;
  v_digest text;
begin
  perform bug_ops.assert_queue_filter_contract();
  if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_ROLE'; end if;
  if p_expected_read_ct < 1 then raise exception 'INVALID_READ_CT'; end if;

  select q.message,q.read_ct
    into v_message,v_read_ct
  from pgmq.q_bug_dispatch q
  where q.msg_id=p_msg_id
  for update;

  if v_message is null then raise exception 'QUEUE_MESSAGE_NOT_ACTIVE'; end if;
  if v_read_ct <> p_expected_read_ct then raise exception 'STALE_CLAIM expected %, actual %',p_expected_read_ct,v_read_ct; end if;

  select * into enq
  from bug_ops.dispatch_events_v2 d
  where d.dispatch_id=p_dispatch_id and d.event_type='ENQUEUED';
  if not found or enq.queue_name<>'bug_dispatch' or enq.msg_id<>p_msg_id or enq.target_role is distinct from v_role then
    raise exception 'ACK_DISPATCH_BINDING_MISMATCH';
  end if;

  v_digest:=bug_ops.sha256_jsonb(v_message);
  if enq.payload_digest is distinct from v_digest then raise exception 'ACK_PAYLOAD_DIGEST_MISMATCH'; end if;

  select * into src from bug_ops.bug_events e where e.event_id=enq.bug_event_id;
  if not found or src.bug_id is distinct from enq.bug_id or src.dispatch_id is distinct from p_dispatch_id then
    raise exception 'ACK_SOURCE_BINDING_MISMATCH';
  end if;

  select * into handled from bug_ops.bug_events e where e.event_id=p_handled_event_id;
  if not found or handled.bug_id<>src.bug_id or handled.state_version<=src.state_version then
    raise exception 'ACK_REQUIRES_LATER_BUG_EVENT';
  end if;

  return bug_ops.archive_dispatch_internal_v2(p_msg_id,'HANDLED',v_message,p_dispatch_id,src.bug_id,src.event_id,p_handled_event_id,v_role,p_note);
end $$;

revoke execute on function bug_ops.ack_work(text,bigint,uuid,integer,uuid,text) from public,anon,authenticated,service_role,authenticator;