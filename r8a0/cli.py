"""Issuer, supervisor, and recovery entry points for bounded R8A0."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from .canonical import canonical_bytes,strict_loads
from .recovery import CheckpointState,read_checkpoint_receipt,read_termination_intent,recover,write_checkpoint,write_exit_attestation,write_termination_intent
from .temporal import evidence_from_mapping
_DER=bytes.fromhex('3031300d060960864801650304020105000420')
def _env(prefix:str)->tuple[str,str,int,int]:
 issuer=os.environ.get(prefix+'_ISSUER','');kid=os.environ.get(prefix+'_KEY_ID','');n=int(os.environ.get(prefix+'_N_HEX','0'),16);d=int(os.environ.get(prefix+'_D_HEX','0'),16)
 if not issuer or not kid or n.bit_length()<1024 or d<2:raise ValueError(prefix+' private signing material is incomplete')
 return issuer,kid,n,d
def _signer(prefix:str):
 issuer,kid,n,d=_env(prefix);k=(n.bit_length()+7)//8
 def sign(payload):
  tail=_DER+hashlib.sha256(canonical_bytes(payload)).digest();em=b'\x00\x01'+b'\xff'*(k-len(tail)-3)+b'\x00'+tail;return format(pow(int.from_bytes(em,'big'),d,n),'x')
 return issuer,kid,sign
def _worker(a):
 x=strict_loads(Path(a.input).read_bytes());s=x['state'];st=CheckpointState(s['project_id'],s['identity_id'],s['runtime_id'],s['runtime_instance_nonce'],s['memory_head_digest'],s['self_model_head_digest'],s['authority_state_digest'],tuple(s['active_commitments']),tuple(s['unfinished_work']),s['created_at'],s['predecessor_checkpoint_digest']);issuer,kid,sign=_signer('VERA_R8A0_LIFECYCLE');cp=write_checkpoint(a.checkpoint,st,checkpoint_receipt_path=a.checkpoint_receipt,state_attestations=x['state_attestations'],trusted_state_keys=x['trusted_state_keys'],lifecycle_issuer=issuer,lifecycle_key_id=kid,lifecycle_signer=sign);ti=write_termination_intent(checkpoint_receipt_path=a.checkpoint_receipt,termination_intent_path=a.termination_intent,trusted_lifecycle_keys=x['trusted_lifecycle_keys'],lifecycle_issuer=issuer,lifecycle_key_id=kid,lifecycle_signer=sign,process_id=os.getpid());print(json.dumps({'checkpoint_signature':cp['signature'],'termination_signature':ti['signature'],'process_id':os.getpid()}));return 0
def _supervise(a):
 cmd=[sys.executable,'-m','r8a0.cli','checkpoint-worker','--input',a.input,'--checkpoint',a.checkpoint,'--checkpoint-receipt',a.checkpoint_receipt,'--termination-intent',a.termination_intent];child_env=os.environ.copy()
 for key in tuple(child_env):
  if key.startswith('VERA_R8A0_SUPERVISOR_'):child_env.pop(key)
 p=subprocess.Popen(cmd,cwd=Path(__file__).resolve().parents[1],env=child_env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out,err=p.communicate();x=strict_loads(Path(a.input).read_bytes());cp=read_checkpoint_receipt(a.checkpoint_receipt,trusted_lifecycle_keys=x['trusted_lifecycle_keys']);ti=read_termination_intent(a.termination_intent,trusted_lifecycle_keys=x['trusted_lifecycle_keys']);issuer,kid,sign=_signer('VERA_R8A0_SUPERVISOR');ex=write_exit_attestation(path=a.exit_attestation,checkpoint_receipt=cp,termination_intent=ti,exit_code=p.returncode,observed_at=datetime.now(timezone.utc).isoformat(),supervisor_issuer=issuer,supervisor_key_id=kid,supervisor_signer=sign);print(json.dumps({'worker_stdout':out,'worker_stderr':err,'exit_signature':ex['signature'],'exit_code':p.returncode}));return 0 if p.returncode==0 else p.returncode
def _recover(a):
 x=strict_loads(Path(a.input).read_bytes());r=recover(a.checkpoint,orientation_evidence=evidence_from_mapping(x['orientation_evidence']),orientation_source_mode=x['orientation_source_mode'],trusted_temporal_keys=x['trusted_temporal_keys'],checkpoint_receipt_path=x['checkpoint_receipt_path'],termination_intent_path=x['termination_intent_path'],exit_attestation_path=x['exit_attestation_path'],trusted_lifecycle_keys=x['trusted_lifecycle_keys'],trusted_supervisor_keys=x['trusted_supervisor_keys'],trusted_state_keys=x['trusted_state_keys'],expected_checkpoint_receipt_signature=x['expected_checkpoint_receipt_signature'],expected_termination_intent_signature=x['expected_termination_intent_signature'],expected_exit_attestation_signature=x['expected_exit_attestation_signature'],expected_project_id=x['expected_project_id'],expected_identity_id=x['expected_identity_id'],expected_predecessor_checkpoint_digest=x['expected_predecessor_checkpoint_digest'],expected_memory_head_digest=x['expected_memory_head_digest'],expected_self_model_head_digest=x['expected_self_model_head_digest'],expected_authority_state_digest=x['expected_authority_state_digest'],successor_runtime_id=x['successor_runtime_id'],lifecycle_registry_path=x['lifecycle_registry_path'],lifecycle_registry_key=bytes.fromhex(os.environ['VERA_R8A0_REGISTRY_KEY_HEX']),expected_lifecycle_registry_head=x['expected_lifecycle_registry_head']);print(json.dumps(r,sort_keys=True));return 0
def main():
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 for name,fn in [('checkpoint-worker',_worker),('supervise',_supervise)]:
  q=s.add_parser(name);q.add_argument('--input',required=True);q.add_argument('--checkpoint',required=True);q.add_argument('--checkpoint-receipt',required=True);q.add_argument('--termination-intent',required=True)
  if name=='supervise':q.add_argument('--exit-attestation',required=True)
  q.set_defaults(fn=fn)
 q=s.add_parser('recover');q.add_argument('checkpoint');q.add_argument('--input',required=True);q.set_defaults(fn=_recover);a=p.parse_args();return a.fn(a)
if __name__=='__main__':raise SystemExit(main())
