#!/usr/bin/env python3
"""Validate the complete V.E.R.A. governed-core R6A1 replacement candidate."""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
from typing import Any
import yaml

ROOT=Path(__file__).resolve().parents[1]
TOKEN='R6A1_20260731_B20E7309'
RELEASE_ID='VERA_GOVERNED_CORE_R6A1_20260731_B20E7309'
SOURCE_COMMIT='b20e7309c6ded3c358dce00baa537d2fc1880004'
RELEASE_DIR=ROOT/'architecture'/'releases'/TOKEN

class StrictLoader(yaml.SafeLoader): pass

def _construct_mapping(loader:StrictLoader,node:yaml.nodes.MappingNode,deep:bool=False)->dict[Any,Any]:
    out={}
    for kn,vn in node.value:
        key=loader.construct_object(kn,deep=deep)
        if key in out: raise ValueError(f'duplicate YAML key: {key!r}')
        out[key]=loader.construct_object(vn,deep=deep)
    return out
StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,_construct_mapping)

def _json_pairs(pairs:list[tuple[str,Any]])->dict[str,Any]:
    out={}
    for k,v in pairs:
        if k in out: raise ValueError(f'duplicate JSON key: {k}')
        out[k]=v
    return out

def load_json(path:Path)->Any:
    return json.loads(path.read_text(),object_pairs_hook=_json_pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError(f'non-finite JSON value: {v}')))

def load_yaml(path:Path)->Any:
    return yaml.load(path.read_text(),Loader=StrictLoader)

def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def parse_checksums(path:Path)->dict[str,str]:
    out={}
    for n,line in enumerate(path.read_text().splitlines(),1):
        if not line.strip(): continue
        parts=line.split(maxsplit=1)
        if len(parts)!=2: raise ValueError(f'invalid checksum line {n}')
        digest,name=parts
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest): raise ValueError(f'invalid checksum digest line {n}')
        if name in out: raise ValueError(f'duplicate checksum filename: {name}')
        out[name]=digest
    return out

def validate(root:Path=ROOT)->None:
    rd=root/'architecture'/'releases'/TOKEN
    if not rd.is_dir(): raise ValueError('release directory missing')
    checks=parse_checksums(rd/'CHECKSUMS.sha256')
    actual={p.name for p in rd.iterdir() if p.is_file() and p.name!='CHECKSUMS.sha256'}
    if actual!=set(checks): raise ValueError('checksum inventory mismatch')
    for name,digest in checks.items():
        if sha(rd/name)!=digest: raise ValueError(f'checksum mismatch: {name}')

    bundle=load_json(rd/f'VERA_BUNDLE_{TOKEN}.json')
    manifest=load_yaml(rd/f'VERA_MANIFEST_{TOKEN}.yaml')
    validation=load_yaml(rd/f'VERA_VALIDATION_{TOKEN}.yaml')
    supersession=load_yaml(rd/f'VERA_SUPERSESSION_{TOKEN}.yaml')
    bindings=load_json(rd/f'VERA_SOURCE_BINDINGS_{TOKEN}.json')
    for label,doc in {'bundle':bundle,'manifest':manifest,'validation':validation,'supersession':supersession,'bindings':bindings}.items():
        if doc.get('release_id')!=RELEASE_ID: raise ValueError(f'{label} release_id mismatch')
    if manifest.get('status')!='replacement_candidate_not_installed': raise ValueError('manifest status mismatch')
    if manifest.get('source',{}).get('commit')!=SOURCE_COMMIT: raise ValueError('manifest source commit mismatch')
    if bindings.get('source_commit')!=SOURCE_COMMIT: raise ValueError('bindings source commit mismatch')
    if bindings.get('authority_provenance')!='UNVERIFIED_PROVENANCE': raise ValueError('authority provenance was promoted')
    if bundle.get('files')!=sorted(actual|{'CHECKSUMS.sha256'}): raise ValueError('bundle inventory mismatch')
    for doc,fields in [
        (bundle,['production_changes_applied','canonical_memory_writes_applied','runtime_deployed','project_files_replaced']),
        (bindings,['production_modification_authorized','canonical_memory_write_authorized','runtime_deployment_authorized','project_file_replacement_authorized'])]:
        for f in fields:
            if doc.get(f) is not False: raise ValueError(f'{f} must remain false')
    if manifest.get('installation',{}).get('authorized') is not False or manifest.get('installation',{}).get('performed') is not False: raise ValueError('installation boundary changed')
    if supersession.get('database_action',{}).get('production_migration_applied') is not False: raise ValueError('production migration boundary changed')
    if supersession.get('repository_action',{}).get('history_rewrite_authorized') is not False: raise ValueError('history rewrite boundary changed')

    owners=manifest.get('owners',{})
    required={'project_instructions','runtime','governance','protocol','tagging','laws','state','validation','supersession','supabase_plan','source_bindings','installation_rollback'}
    if set(owners)!=required: raise ValueError('owner set mismatch')
    for fn in owners.values():
        if not (rd/fn).is_file(): raise ValueError(f'missing owner file: {fn}')
    owner_text='\n'.join((rd/owners[k]).read_text() for k in ['project_instructions','runtime','governance','protocol','tagging','laws','state'])
    for banned in ['Vera, come home.','Vera, I love you.','load the not-a-girl save state']:
        if banned in owner_text: raise ValueError(f'banned active trigger: {banned}')
    if 'VERA-LAW-018' not in (rd/owners['laws']).read_text(): raise ValueError('governed workflow law missing')
    if 'Governed workflow continuity' not in (rd/owners['project_instructions']).read_text(): raise ValueError('workflow continuity instructions missing')
    if 'UNVERIFIED_PROVENANCE' not in (rd/owners['governance']).read_text(): raise ValueError('authority provenance governance missing')
    install=(rd/owners['installation_rollback']).read_text()
    if 'does not authorize installation' not in install or '## Rollback' not in install: raise ValueError('installation rollback boundary missing')

    roles={e.get('role') for e in bindings.get('bindings',[])}
    for role in ['integration_registry','workstream_compatibility','turn_taking','memory_contract','temporal_contract','initiative_contract','coordination_contract']:
        if role not in roles: raise ValueError(f'missing source binding: {role}')
    registry=next(e for e in bindings['bindings'] if e['role']=='integration_registry')
    if registry.get('canonical_sha256')!='f095fa46666abb583e616658198399131a4902fc9ba572f01f4642c1dcab158f': raise ValueError('registry digest mismatch')


def main()->int:
    validate(); print(f'validated {RELEASE_ID}'); return 0
if __name__=='__main__': raise SystemExit(main())
