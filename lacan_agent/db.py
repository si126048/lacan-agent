from __future__ import annotations
import hashlib, json, logging, os, sqlite3, threading, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .models import *

logger = logging.getLogger(__name__)

class Store:
    SCHEMA_VERSION = 0

    MIGRATIONS: list[tuple[int, str, str]] = []

    def __init__(self, path: str | None = None):
        self.path = Path(path or os.getenv('LACAN_DB_PATH','./data/lacan.db'))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS participants(id TEXT, project_id TEXT, data TEXT NOT NULL, PRIMARY KEY(id,project_id));
        CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, project_id TEXT, participant_id TEXT, kind TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS spans(id TEXT PRIMARY KEY, document_id TEXT, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS concepts(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, project_id TEXT, participant_id TEXT, idem TEXT, data TEXT NOT NULL, UNIQUE(project_id,idem));
        CREATE VIRTUAL TABLE IF NOT EXISTS document_fts USING fts5(document_id UNINDEXED, text);
        CREATE TABLE IF NOT EXISTS _migrations(version INTEGER PRIMARY KEY, description TEXT NOT NULL, applied_at TEXT NOT NULL);
        '''); self.conn.commit()
        self.migrate()

    def migrate(self) -> list[int]:
        applied: list[int] = []
        existing = {r['version'] for r in self.conn.execute('SELECT version FROM _migrations').fetchall()}
        for version, description, sql in sorted(self.MIGRATIONS, key=lambda m: m[0]):
            if version in existing:
                continue
            logger.info("applying migration %d: %s", version, description)
            self.conn.executescript(sql)
            self.conn.execute(
                'INSERT INTO _migrations(version, description, applied_at) VALUES(?,?,?)',
                (version, description, datetime.now(timezone.utc).isoformat()),
            )
            self.conn.commit()
            applied.append(version)
        if applied:
            logger.info("applied %d migration(s): %s", len(applied), applied)
        return applied
    def create_project(self, p: Project):
        self.conn.execute('INSERT OR REPLACE INTO projects VALUES(?,?)',(p.id,p.model_dump_json())); self.conn.commit(); return p
    def get_project(self, pid):
        r=self.conn.execute('SELECT data FROM projects WHERE id=?',(pid,)).fetchone(); return Project.model_validate_json(r['data']) if r else None
    def put_participant(self,p):
        self.conn.execute('INSERT OR REPLACE INTO participants VALUES(?,?,?)',(p.id,p.project_id,p.model_dump_json())); self.conn.commit(); return p
    def get_participant(self,project_id,pid):
        r=self.conn.execute('SELECT data FROM participants WHERE project_id=? AND id=?',(project_id,pid)).fetchone(); return Participant.model_validate_json(r['data']) if r else None
    def put_document(self,d: SourceDocument):
        self.conn.execute('INSERT OR REPLACE INTO documents VALUES(?,?,?,?,?)',(d.id,d.project_id,d.participant_id,d.type,d.model_dump_json()))
        self.conn.execute('DELETE FROM document_fts WHERE document_id=?',(d.id,))
        self.conn.execute('INSERT INTO document_fts(document_id,text) VALUES(?,?)',(d.id,d.text))
        self.conn.commit(); return d
    def get_document(self,did):
        r=self.conn.execute('SELECT data FROM documents WHERE id=?',(did,)).fetchone(); return SourceDocument.model_validate_json(r['data']) if r else None
    def list_documents(self,project_id,participant_id=None):
        q='SELECT data FROM documents WHERE project_id=?'; args=[project_id]
        if participant_id is not None: q+=' AND participant_id=?'; args.append(participant_id)
        return [SourceDocument.model_validate_json(r['data']) for r in self.conn.execute(q,args)]
    def list_spans_for_document(self, document_id: str) -> list[EvidenceSpan]:
        rows=self.conn.execute('SELECT data FROM spans WHERE document_id=?',(document_id,)).fetchall()
        return [EvidenceSpan.model_validate_json(r['data']) for r in rows]
    def list_theory_spans(self, project_id: str) -> list[EvidenceSpan]:
        rows=self.conn.execute('SELECT data FROM spans WHERE document_id IN (SELECT id FROM documents WHERE project_id=? AND participant_id IS NULL)',(project_id,)).fetchall()
        return [EvidenceSpan.model_validate_json(r['data']) for r in rows]
    def put_span(self,s): self.conn.execute('INSERT OR REPLACE INTO spans VALUES(?,?,?)',(s.id,s.document_id,s.model_dump_json())); self.conn.commit(); return s
    def put_spans(self, spans):
        self.conn.executemany('INSERT OR REPLACE INTO spans VALUES(?,?,?)',
                              [(s.id, s.document_id, s.model_dump_json()) for s in spans])
        self.conn.commit()
        return spans
    def get_span(self,sid):
        r=self.conn.execute('SELECT data FROM spans WHERE id=?',(sid,)).fetchone(); return EvidenceSpan.model_validate_json(r['data']) if r else None
    def put_concept(self,c): self.conn.execute('INSERT OR REPLACE INTO concepts VALUES(?,?)',(c.id,c.model_dump_json())); self.conn.commit(); return c
    def get_concept(self,cid):
        r=self.conn.execute('SELECT data FROM concepts WHERE id=?',(cid,)).fetchone(); return ConceptCard.model_validate_json(r['data']) if r else None
    def search(self,q,limit=5):
        rows=self.conn.execute('SELECT d.data FROM document_fts f JOIN documents d ON d.id=f.document_id WHERE document_fts MATCH ? LIMIT ?',(q,limit)).fetchall(); return [SourceDocument.model_validate_json(r['data']) for r in rows]
    def put_run(self,r: AnalysisRun):
        self.conn.execute('INSERT OR REPLACE INTO runs VALUES(?,?,?,?,?)',(r.id,r.project_id,r.participant_id,r.idempotency_key,r.model_dump_json())); self.conn.commit(); return r
    def get_run(self,rid):
        r=self.conn.execute('SELECT data FROM runs WHERE id=?',(rid,)).fetchone(); return AnalysisRun.model_validate_json(r['data']) if r else None
    def get_run_by_idem(self,project_id,idem):
        r=self.conn.execute('SELECT data FROM runs WHERE project_id=? AND idem=?',(project_id,idem)).fetchone(); return AnalysisRun.model_validate_json(r['data']) if r else None
    def audit(self,run,actor,reason):
        run.audit.append({'actor':actor,'timestamp':datetime.now(timezone.utc).isoformat(),'state':run.state,'reason':reason}); return self.put_run(run)
    def withdraw(self,project_id,pid):
        p=self.get_participant(project_id,pid)
        if not p:return None
        p.withdrawn_at=datetime.now(timezone.utc).isoformat(); p.consent_scope.withdrawn_at=p.withdrawn_at; self.put_participant(p)
        return p

def checksum(text): return hashlib.sha256(text.encode('utf-8')).hexdigest()
def new_id(prefix): return f'{prefix}_{uuid.uuid4().hex[:12]}'
