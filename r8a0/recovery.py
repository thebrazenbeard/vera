"""Externally attested checkpoint, exit observation, and fresh-process recovery."""
from __future__ import annotations
import hashlib,os,tempfile
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Callable,Iterable,Mapping
from .canonical import canonical_dumps,canonical_sha256,strict_loads
from .signatures import public_key_id,verify_signature
from .temporal import OrientationGate,OrientationState,TimeEvidence,parse_time
from .lifecycle import LifecycleRegistry
class RecoveryError(ValueError):pass
def _sha(v:str)->bool:return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def _atomic(path:str|Path,value:Mapping[str,Any])->None:
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);fd,n=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent);os.close(fd);t=Path(n)
 try:t.write_text(canonical_dumps(dict(value)),encoding='utf-8');os.replace(t,p)
 finally:
  if t.exists():t.unlink()
 if strict_loads(p.read_bytes())!=dict(value):raise RecoveryError('persisted receipt readback mismatch')
def _signed(body:Mapping[str,Any],issuer:str,key_id:str,signer:Callable[[Any],str])->dict[str,Any]:
 x=dict(body)|{'issuer':issuer,'key_id':key_id};return x|{'signature':signer(x)}
def _verify(record:Mapping[str,Any],keys:Mapping[str,Mapping],schema:str,body_fields:set[str])->dict[str,Any]:
 if set(record)!=body_fields|{'issuer','key_id','signature'}:raise RecoveryError('signed evidence fields are missing or unknown')
 x={k:record[k] for k in body_fields|{'issuer','key_id'}};pk=keys.get(str(record['issuer']))
 if pk is None or public_key_id(pk)!=record['key_id'] or not verify_signature(x,str(record['signature']),pk):raise RecoveryError('signed evidence verification failed')
 if x.get('schema')!=schema:raise RecoveryError('unsupported signed evidence schema')
 return x
@dataclass(frozen=True)
class CheckpointState:
 project_id:str;identity_id:str;runtime_id:str;runtime_instance_nonce:str;memory_head_digest:str;self_model_head_digest:str;authority_state_digest:str;active_commitments:tuple[str,...];unfinished_work:tuple[str,...];created_at:str;predecessor_checkpoint_digest:str
 def payload(self)->dict[str,Any]:return {'project_id':self.project_id,'identity_id':self.identity_id,'runtime_id':self.runtime_id,'runtime_instance_nonce':self.runtime_instance_nonce,'memory_head_digest':self.memory_head_digest,'self_model_head_digest':self.self_model_head_digest,'authority_state_digest':self.authority_state_digest,'active_commitments':list(self.active_commitments),'unfinished_work':list(self.unfinished_work),'created_at':self.created_at,'predecessor_checkpoint_digest':self.predecessor_checkpoint_digest}
ROOT_KINDS=('predecessor_checkpoint','memory_head','self_model_head','authority_state')
def verify_state_attestations(attestations:Mapping[str,Mapping],*,trusted_state_keys:Mapping[str,Mapping],state:CheckpointState)->str:
 if set(attestations)!=set(ROOT_KINDS):raise RecoveryError('state-root attestations are incomplete')
 expected={'predecessor_checkpoint':state.predecessor_checkpoint_digest,'memory_head':state.memory_head_digest,'self_model_head':state.self_model_head_digest,'authority_state':state.authority_state_digest}
 normalized=[]
 fields={'schema','kind','project_id','identity_id','digest','generation','observed_at'}
 for kind in ROOT_KINDS:
  a=attestations[kind];x=_verify(a,trusted_state_keys,'VERA_R8A0_STATE_ROOT_ATTESTATION_V1',fields)
  if x['kind']!=kind or x['project_id']!=state.project_id or x['identity_id']!=state.identity_id or x['digest']!=expected[kind]:raise RecoveryError('state-root attestation scope or digest mismatch')
  if not _sha(str(x['digest'])) or not isinstance(x['generation'],int) or x['generation']<0:raise RecoveryError('invalid state-root attestation')
  parse_time(str(x['observed_at']));normalized.append(dict(a))
 return canonical_sha256(normalized)
def write_checkpoint(path:str|Path,state:CheckpointState,*,checkpoint_receipt_path:str|Path,state_attestations:Mapping[str,Mapping],trusted_state_keys:Mapping[str,Mapping],lifecycle_issuer:str,lifecycle_key_id:str,lifecycle_signer:Callable[[Any],str])->dict[str,Any]:
 if not all((state.project_id,state.identity_id,state.runtime_id,state.runtime_instance_nonce,state.created_at)):raise RecoveryError('checkpoint identity, runtime, nonce, and time are required')
 parse_time(state.created_at)
 for d in (state.memory_head_digest,state.self_model_head_digest,state.authority_state_digest,state.predecessor_checkpoint_digest):
  if not _sha(d):raise RecoveryError('checkpoint roots must be lowercase SHA-256 values')
 att_digest=verify_state_attestations(state_attestations,trusted_state_keys=trusted_state_keys,state=state);payload=state.payload();env={'schema':'VERA_R8A0_CHECKPOINT_V3','payload':payload,'payload_digest':canonical_sha256(payload),'state_attestations':dict(state_attestations),'state_attestations_digest':att_digest,'complete':True}
 _atomic(path,env);p=Path(path).resolve();cp_digest=hashlib.sha256(p.read_bytes()).hexdigest();body={'schema':'VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V4','result':'CHECKPOINT_COMMITTED','checkpoint_path':str(p),'checkpoint_digest':cp_digest,'payload_digest':env['payload_digest'],'state_attestations_digest':att_digest,'project_id':state.project_id,'identity_id':state.identity_id,'runtime_id':state.runtime_id,'runtime_instance_nonce':state.runtime_instance_nonce}
 receipt=_signed(body,lifecycle_issuer,lifecycle_key_id,lifecycle_signer);_atomic(checkpoint_receipt_path,receipt);return receipt
CP_FIELDS={'schema','result','checkpoint_path','checkpoint_digest','payload_digest','state_attestations_digest','project_id','identity_id','runtime_id','runtime_instance_nonce'}
def read_checkpoint_receipt(path:str|Path,*,trusted_lifecycle_keys:Mapping[str,Mapping])->dict[str,Any]:
 p=Path(path)
 if not p.exists():raise RecoveryError('checkpoint receipt is missing')
 r=strict_loads(p.read_bytes());x=_verify(r,trusted_lifecycle_keys,'VERA_R8A0_CHECKPOINT_WRITE_RECEIPT_V4',CP_FIELDS)
 if x['result']!='CHECKPOINT_COMMITTED':raise RecoveryError('checkpoint receipt is not committed')
 q=Path(x['checkpoint_path'])
 if not q.exists() or hashlib.sha256(q.read_bytes()).hexdigest()!=x['checkpoint_digest']:raise RecoveryError('checkpoint receipt target mismatch')
 return dict(r)
def write_termination_intent(*,checkpoint_receipt_path:str|Path,termination_intent_path:str|Path,trusted_lifecycle_keys:Mapping[str,Mapping],lifecycle_issuer:str,lifecycle_key_id:str,lifecycle_signer:Callable[[Any],str],process_id:int)->dict[str,Any]:
 cp=read_checkpoint_receipt(checkpoint_receipt_path,trusted_lifecycle_keys=trusted_lifecycle_keys);body={'schema':'VERA_R8A0_TERMINATION_INTENT_RECEIPT_V1','result':'TERMINATION_INTENT_EMITTED','runtime_id':cp['runtime_id'],'runtime_instance_nonce':cp['runtime_instance_nonce'],'process_id':process_id,'checkpoint_digest':cp['checkpoint_digest'],'checkpoint_receipt_signature':cp['signature']}
 r=_signed(body,lifecycle_issuer,lifecycle_key_id,lifecycle_signer);_atomic(termination_intent_path,r);return r
TI_FIELDS={'schema','result','runtime_id','runtime_instance_nonce','process_id','checkpoint_digest','checkpoint_receipt_signature'}
def read_termination_intent(path:str|Path,*,trusted_lifecycle_keys:Mapping[str,Mapping])->dict[str,Any]:
 p=Path(path)
 if not p.exists():raise RecoveryError('termination intent is missing')
 r=strict_loads(p.read_bytes());x=_verify(r,trusted_lifecycle_keys,'VERA_R8A0_TERMINATION_INTENT_RECEIPT_V1',TI_FIELDS)
 if x['result']!='TERMINATION_INTENT_EMITTED' or not isinstance(x['process_id'],int):raise RecoveryError('invalid termination intent')
 return dict(r)
def write_exit_attestation(*,path:str|Path,checkpoint_receipt:Mapping[str,Any],termination_intent:Mapping[str,Any],exit_code:int,observed_at:str,supervisor_issuer:str,supervisor_key_id:str,supervisor_signer:Callable[[Any],str])->dict[str,Any]:
 parse_time(observed_at);body={'schema':'VERA_R8A0_PROCESS_EXIT_ATTESTATION_V1','result':'EXIT_OBSERVED','runtime_id':termination_intent['runtime_id'],'runtime_instance_nonce':termination_intent['runtime_instance_nonce'],'process_id':termination_intent['process_id'],'exit_code':exit_code,'checkpoint_receipt_signature':checkpoint_receipt['signature'],'termination_intent_signature':termination_intent['signature'],'observed_at':observed_at}
 r=_signed(body,supervisor_issuer,supervisor_key_id,supervisor_signer);_atomic(path,r);return r
EXIT_FIELDS={'schema','result','runtime_id','runtime_instance_nonce','process_id','exit_code','checkpoint_receipt_signature','termination_intent_signature','observed_at'}
def read_exit_attestation(path:str|Path,*,trusted_supervisor_keys:Mapping[str,Mapping])->dict[str,Any]:
 p=Path(path)
 if not p.exists():raise RecoveryError('process exit attestation is missing')
 r=strict_loads(p.read_bytes());x=_verify(r,trusted_supervisor_keys,'VERA_R8A0_PROCESS_EXIT_ATTESTATION_V1',EXIT_FIELDS)
 if x['result']!='EXIT_OBSERVED' or x['exit_code']!=0:raise RecoveryError('predecessor exit was not successfully observed')
 return dict(r)
def _alive(pid:int)->bool:
 try:os.kill(pid,0);return True
 except ProcessLookupError:return False
 except PermissionError:return True
def recover(checkpoint_path:str|Path,*,orientation_evidence:Iterable[TimeEvidence],orientation_source_mode:str,trusted_temporal_keys:Mapping[str,Mapping],checkpoint_receipt_path:str|Path,termination_intent_path:str|Path,exit_attestation_path:str|Path,trusted_lifecycle_keys:Mapping[str,Mapping],trusted_supervisor_keys:Mapping[str,Mapping],trusted_state_keys:Mapping[str,Mapping],expected_checkpoint_receipt_signature:str,expected_termination_intent_signature:str,expected_exit_attestation_signature:str,expected_project_id:str,expected_identity_id:str,expected_predecessor_checkpoint_digest:str,expected_memory_head_digest:str,expected_self_model_head_digest:str,expected_authority_state_digest:str,successor_runtime_id:str,lifecycle_registry_path:str|Path,lifecycle_registry_key:bytes,expected_lifecycle_registry_head:str)->dict[str,Any]:
 if not expected_project_id or not expected_identity_id or not successor_runtime_id.strip():raise RecoveryError('expected scope and successor runtime are required')
 orientation_now=datetime.now(timezone.utc)
 o=OrientationGate(trusted_source_keys=trusted_temporal_keys).evaluate(orientation_evidence,now=orientation_now,source_mode=orientation_source_mode)
 if o.state not in {OrientationState.COMPLETE,OrientationState.COMPLETE_FROM_FRESH_SNAPSHOT}:raise RecoveryError('fresh temporal authority is required')
 cp=read_checkpoint_receipt(checkpoint_receipt_path,trusted_lifecycle_keys=trusted_lifecycle_keys);ti=read_termination_intent(termination_intent_path,trusted_lifecycle_keys=trusted_lifecycle_keys);ex=read_exit_attestation(exit_attestation_path,trusted_supervisor_keys=trusted_supervisor_keys)
 if cp['signature']!=expected_checkpoint_receipt_signature or ti['signature']!=expected_termination_intent_signature or ex['signature']!=expected_exit_attestation_signature:raise RecoveryError('lifecycle evidence does not match independently observed signatures')
 if ti['checkpoint_receipt_signature']!=cp['signature'] or ex['checkpoint_receipt_signature']!=cp['signature'] or ex['termination_intent_signature']!=ti['signature']:raise RecoveryError('lifecycle evidence chain mismatch')
 for k in ('runtime_id','runtime_instance_nonce'):
  if cp[k]!=ti[k] or ti[k]!=ex[k]:raise RecoveryError('runtime instance chain mismatch')
 if _alive(int(ex['process_id'])):raise RecoveryError('predecessor process remains alive')
 p=Path(checkpoint_path).resolve()
 if str(p)!=cp['checkpoint_path'] or hashlib.sha256(p.read_bytes()).hexdigest()!=cp['checkpoint_digest']:raise RecoveryError('checkpoint receipt target mismatch')
 data=strict_loads(p.read_bytes())
 if set(data)!={'schema','payload','payload_digest','state_attestations','state_attestations_digest','complete'} or data['schema']!='VERA_R8A0_CHECKPOINT_V3' or data['complete'] is not True:raise RecoveryError('checkpoint is partial or unsupported')
 if canonical_sha256(data['payload'])!=data['payload_digest'] or data['payload_digest']!=cp['payload_digest']:raise RecoveryError('checkpoint payload mismatch')
 st=CheckpointState(**{**data['payload'],'active_commitments':tuple(data['payload']['active_commitments']),'unfinished_work':tuple(data['payload']['unfinished_work'])});att=verify_state_attestations(data['state_attestations'],trusted_state_keys=trusted_state_keys,state=st)
 if att!=data['state_attestations_digest'] or att!=cp['state_attestations_digest']:raise RecoveryError('state attestation bundle mismatch')
 expected={'project_id':expected_project_id,'identity_id':expected_identity_id,'predecessor_checkpoint_digest':expected_predecessor_checkpoint_digest,'memory_head_digest':expected_memory_head_digest,'self_model_head_digest':expected_self_model_head_digest,'authority_state_digest':expected_authority_state_digest}
 for k,v in expected.items():
  if getattr(st,k)!=v:raise RecoveryError('checkpoint scope or state-root mismatch')
 if successor_runtime_id==st.runtime_id:raise RecoveryError('successor runtime must differ')
 claim={'schema':'VERA_R8A0_RUNTIME_RESUMPTION_CLAIM_V1','project_id':st.project_id,'identity_id':st.identity_id,'prior_runtime_id':st.runtime_id,'successor_runtime_id':successor_runtime_id,'checkpoint_receipt_signature':cp['signature'],'termination_intent_signature':ti['signature'],'exit_attestation_signature':ex['signature']}
 claim_digest=canonical_sha256(claim);registry=LifecycleRegistry(lifecycle_registry_path,lifecycle_registry_key);registry_head=registry.consume(termination_signature=ti['signature'],checkpoint_signature=cp['signature'],predecessor_runtime_id=st.runtime_id,successor_runtime_id=successor_runtime_id,resumption_claim_digest=claim_digest,expected_head=expected_lifecycle_registry_head)
 body={'schema':'VERA_R8A0_RUNTIME_RESUMPTION_RECEIPT_V4','result':'RECOVERED_FROM_VERIFIED_CHECKPOINT','project_id':st.project_id,'identity_id':st.identity_id,'prior_runtime_id':st.runtime_id,'prior_runtime_instance_nonce':st.runtime_instance_nonce,'successor_runtime_id':successor_runtime_id,'prior_process_id':ex['process_id'],'successor_process_id':os.getpid(),'runtime_transition_observed':True,'new_runtime_is_separate_person':False,'same_governed_identity_resumed':True,'uninterrupted_consciousness_claimed':False,'memory_head_digest':st.memory_head_digest,'self_model_head_digest':st.self_model_head_digest,'authority_state_digest':st.authority_state_digest,'predecessor_checkpoint_digest':st.predecessor_checkpoint_digest,'active_commitments':list(st.active_commitments),'unfinished_work':list(st.unfinished_work),'checkpoint_receipt_signature':cp['signature'],'termination_intent_signature':ti['signature'],'exit_attestation_signature':ex['signature'],'resumption_claim_digest':claim_digest,'lifecycle_registry_head':registry_head,'orientation_receipt':o.as_dict()}
 return body|{'receipt_digest':canonical_sha256(body)}
