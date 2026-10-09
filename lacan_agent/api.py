from __future__ import annotations
import os, tempfile, uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from .db import Store
from .models import *
from .rag import ingest, search
from .workflow import Workflow
from .concurrent import ConcurrentAnalyzer, AnalysisTask
app=FastAPI(title='Lacan-Agent',version='1.0.0')
store=Store(); flow=Workflow(store)
class ProjectIn(BaseModel): id:str; owner_id:str='local-user'; policy_version:str='1.0'
class ParticipantIn(BaseModel): id:str; project_id:str; pseudonym:str|None=None; consent_scope:ConsentScope=ConsentScope()
class RunIn(BaseModel): project_id:str; participant_id:str; source_ids:list[str]; mode:str='evidence_first'; idempotency_key:str

MAX_UPLOAD_BYTES = int(os.getenv('LACAN_MAX_UPLOAD_BYTES', str(10 * 1024 * 1024)))
UPLOAD_SUFFIXES = {'.txt', '.md', '.pdf'}
UPLOAD_ROOT = Path(os.getenv('LACAN_STORAGE_PATH', '.api/uploads')).resolve()

def _ingest_upload(file: UploadFile, project_id: str, participant_id: str | None = None, consent=None):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in UPLOAD_SUFFIXES:
        raise ValueError('UNSUPPORTED_SOURCE_TYPE')
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError('SOURCE_TOO_LARGE')
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=UPLOAD_ROOT, suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            temp_path = Path(tmp.name)
        return ingest(store, str(temp_path), project_id, participant_id, consent)
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)

def _consent_active(scope: ConsentScope) -> bool:
    if scope.withdrawn_at or not scope.research_analysis:
        return False
    if not scope.expires_at:
        return True
    try:
        expiry = datetime.fromisoformat(scope.expires_at.replace('Z', '+00:00'))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > datetime.now(timezone.utc)
    except ValueError:
        return False

def err(status,code,msg):
    rid='req_'+uuid.uuid4().hex[:10]
    body=ErrorResponse(error=ErrorBody(code=code,message=msg,request_id=rid))
    return JSONResponse(status_code=status,content=body.model_dump())
@app.exception_handler(PermissionError)
async def perm(_,e): return err(403,str(e), '授权或对象访问被拒绝')
@app.exception_handler(KeyError)
async def missing(_,e): return err(404,str(e), '资源不存在')
@app.get('/health')
def health(): return {'status':'ok'}
@app.post('/api/v1/projects',status_code=201)
def project(x:ProjectIn):
    if store.get_project(x.id): raise HTTPException(400,'PROJECT_EXISTS')
    return store.create_project(Project(**x.model_dump())).model_dump()
@app.post('/api/v1/theory/sources',status_code=202)
def theory(project_id: str = Form(...), file: UploadFile = File(...)):
    if not store.get_project(project_id): raise HTTPException(404,'PROJECT_NOT_FOUND')
    try:return _ingest_upload(file, project_id).model_dump(exclude={'text'})
    except ValueError as e: raise HTTPException(422,str(e))
@app.get('/api/v1/theory/search')
def theory_search(project_id:str,q:str,limit:int=5): return {'items':search(store,q,min(limit,5))}
@app.post('/api/v1/participants',status_code=201)
def participant(x:ParticipantIn):
    if not store.get_project(x.project_id):raise HTTPException(404,'PROJECT_NOT_FOUND')
    return store.put_participant(Participant(id=x.id,project_id=x.project_id,pseudonym=x.pseudonym or x.id,consent_scope=x.consent_scope)).model_dump()
@app.post('/api/v1/participants/{pid}/sources',status_code=202)
def source(pid:str, project_id: str = Form(...), file: UploadFile = File(...)):
    p=store.get_participant(project_id,pid)
    if not p:raise HTTPException(404,'PARTICIPANT_NOT_FOUND')
    if p.withdrawn_at or not _consent_active(p.consent_scope):return err(403,'CONSENT_REQUIRED','授权不足')
    try:return _ingest_upload(file, project_id, pid, p.consent_scope).model_dump(exclude={'text'})
    except ValueError as e: raise HTTPException(422,str(e))
@app.post('/api/v1/analysis-runs',status_code=202)
def analysis(x:RunIn):
    try:r=flow.run(x.project_id,x.participant_id,x.source_ids,x.idempotency_key); return {'run_id':r.id,'state':r.state}
    except ValueError as e: raise HTTPException(422,str(e))
@app.get('/api/v1/analysis-runs/{rid}')
def run(rid):return store.get_run(rid).model_dump(mode='json') if store.get_run(rid) else err(404,'RUN_NOT_FOUND','资源不存在')
@app.post('/api/v1/analysis-runs/{rid}/reviews')
def review(rid:str,x:ReviewRequest):return flow.review(rid,x).model_dump(mode='json')
@app.get('/api/v1/analysis-runs/{rid}/packet')
def packet(rid):
    r=store.get_run(rid)
    if not r:return err(404,'RUN_NOT_FOUND','资源不存在')
    if not r.packet or r.state not in (RunState.APPROVED,RunState.COMPILED):return err(409,'NOT_APPROVED','尚未通过人工审核')
    return r.packet.model_dump(mode='json')
@app.get('/api/v1/analysis-runs/{rid}/graph')
def graph(rid):
    try:return flow.export(rid)['graph']
    except PermissionError as e:return err(409,str(e),'尚未通过人工审核或授权不足')
@app.post('/api/v1/participants/{pid}/withdraw',status_code=202)
def withdraw(pid:str,project_id:str):
    p=store.withdraw(project_id,pid)
    if not p:raise HTTPException(404,'PARTICIPANT_NOT_FOUND')
    return {'participant_id':pid,'state':'WITHDRAWAL_REQUESTED'}
class BatchTaskIn(BaseModel): project_id:str; participant_id:str; source_ids:list[str]; idempotency_key:str
class BatchIn(BaseModel): tasks:list[BatchTaskIn]; max_concurrent:int=Field(default=4, ge=1, le=16)
@app.post('/api/v1/analysis-runs/batch',status_code=202)
async def batch_analysis(x:BatchIn):
    analyzer=ConcurrentAnalyzer(store,max_concurrent=x.max_concurrent)
    atasks=[AnalysisTask(project_id=t.project_id,participant_id=t.participant_id,source_ids=t.source_ids,idempotency_key=t.idempotency_key) for t in x.tasks]
    results=await analyzer.analyze_batch(atasks)
    return {'results':[{'participant_id':r.task.participant_id,'run_id':r.run.id if r.run else None,'state':r.run.state if r.run else None,'error':r.error} for r in results]}
