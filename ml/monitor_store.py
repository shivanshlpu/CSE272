"""Durable, parameterized SQLite storage for a single monitoring-service instance."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from ml.data import ROOT

def now():return datetime.now(timezone.utc).isoformat()

class MonitorStore:
    def __init__(self,path=None):
        path=Path(path or os.getenv('MONITOR_DB',str(ROOT/'data/monitoring.sqlite')))
        path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path);self.db.row_factory=sqlite3.Row
        os.chmod(path,0o600)
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS monitors(id TEXT PRIMARY KEY,name TEXT NOT NULL,target TEXT NOT NULL,videos TEXT NOT NULL,interval_seconds INTEGER NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL,last_attempt TEXT,last_success TEXT,error TEXT,coverage TEXT);
        CREATE TABLE IF NOT EXISTS posts(monitor_id TEXT NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,id TEXT NOT NULL,text TEXT NOT NULL,video_id TEXT NOT NULL,url TEXT NOT NULL,published_at TEXT NOT NULL,updated_at TEXT NOT NULL,refreshed_at TEXT NOT NULL,likes INTEGER NOT NULL,language TEXT NOT NULL,sentiment TEXT NOT NULL,stance TEXT NOT NULL,review_label TEXT,reviewed_at TEXT,PRIMARY KEY(monitor_id,id));
        CREATE INDEX IF NOT EXISTS posts_time ON posts(monitor_id,published_at);
        CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,monitor_id TEXT NOT NULL REFERENCES monitors(id) ON DELETE CASCADE,started_at TEXT NOT NULL,finished_at TEXT,status TEXT NOT NULL,details TEXT);
        CREATE TABLE IF NOT EXISTS quota(day TEXT PRIMARY KEY,units INTEGER NOT NULL);
        ''');self.db.commit();self.prune()
    def monitor(self,row):
        if not row:return None
        d=dict(row);d['videos']=json.loads(d['videos']);d['enabled']=bool(d['enabled']);d['coverage']=json.loads(d['coverage'] or '{}');return d
    def list(self):return [self.monitor(r) for r in self.db.execute('SELECT * FROM monitors ORDER BY created_at')]
    def get(self,id):return self.monitor(self.db.execute('SELECT * FROM monitors WHERE id=?',(id,)).fetchone())
    def create(self,p):
        id=uuid.uuid4().hex
        with self.db:self.db.execute('INSERT INTO monitors(id,name,target,videos,interval_seconds,enabled,created_at) VALUES(?,?,?,?,?,?,?)',(id,p['name'],p['target'],json.dumps(p['videos']),p['interval_seconds'],1,now()))
        return self.get(id)
    def toggle(self,id,enabled):
        with self.db:self.db.execute('UPDATE monitors SET enabled=? WHERE id=?',(int(enabled),id))
        return self.get(id)
    def delete(self,id):
        with self.db:self.db.execute('DELETE FROM monitors WHERE id=?',(id,))
        return {'deleted':True}
    def prune(self):
        cutoff=(datetime.now(timezone.utc)-timedelta(days=29)).isoformat()
        with self.db:
            removed=self.db.execute('DELETE FROM posts WHERE refreshed_at < ?',(cutoff,)).rowcount
            self.db.execute('DELETE FROM runs WHERE started_at < ?',(cutoff,))
            self.db.execute('DELETE FROM quota WHERE day < ?',(cutoff[:10],))
        return removed
    def reserve_quota(self,units,budget):
        day=now()[:10]
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO quota VALUES(?,0)',(day,))
            used=self.db.execute('SELECT units FROM quota WHERE day=?',(day,)).fetchone()[0]
            if used+units>budget:raise ValueError('Configured daily YouTube request budget exhausted')
            self.db.execute('UPDATE quota SET units=units+? WHERE day=?',(units,day))
        return {'used':used+units,'budget':budget}
    def quota(self):
        row=self.db.execute('SELECT units FROM quota WHERE day=?',(now()[:10],)).fetchone();return row[0] if row else 0
    def run_start(self,id):
        run=uuid.uuid4().hex
        with self.db:
            self.db.execute('INSERT INTO runs VALUES(?,?,?,?,?,?)',(run,id,now(),None,'running',None))
            self.db.execute('UPDATE monitors SET last_attempt=?,error=NULL WHERE id=?',(now(),id))
        return {'id':run}
    def run_finish(self,id,run,status,details):
        with self.db:
            self.db.execute('UPDATE runs SET finished_at=?,status=?,details=? WHERE id=?',(now(),status,json.dumps(details),run))
            self.db.execute('UPDATE monitors SET error=?,coverage=? WHERE id=?',(details.get('error'),json.dumps(details),id))
            if status in ['success','partial']:self.db.execute('UPDATE monitors SET last_success=? WHERE id=?',(now(),id))
        return {'status':status}
    def upsert(self,id,posts):
        if not self.get(id):raise ValueError('Monitor not found')
        with self.db:
            for p in posts:
                self.db.execute('''INSERT INTO posts(monitor_id,id,text,video_id,url,published_at,updated_at,refreshed_at,likes,language,sentiment,stance) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(monitor_id,id) DO UPDATE SET text=excluded.text,likes=excluded.likes,updated_at=excluded.updated_at,refreshed_at=excluded.refreshed_at,language=excluded.language,sentiment=excluded.sentiment,stance=excluded.stance,review_label=CASE WHEN posts.text=excluded.text THEN posts.review_label ELSE NULL END,reviewed_at=CASE WHEN posts.text=excluded.text THEN posts.reviewed_at ELSE NULL END''',
                (id,p['id'],p['text'],p['video_id'],p['url'],p['published_at'],p['updated_at'],now(),p['likes'],p['language'],json.dumps(p['sentiment']),json.dumps(p['stance'])))
            self.db.execute('DELETE FROM posts WHERE monitor_id=? AND id NOT IN (SELECT id FROM posts WHERE monitor_id=? ORDER BY published_at DESC LIMIT 10000)',(id,id))
        return {'processed':len(posts)}
    def posts(self,id,limit=2000):
        rows=self.db.execute('SELECT * FROM posts WHERE monitor_id=? ORDER BY published_at DESC LIMIT ?',(id,limit)).fetchall()
        data=[]
        for r in rows:
            p=dict(r);p['sentiment']=json.loads(p['sentiment']);p['stance']=json.loads(p['stance']);data.append(p)
        return data
    def review(self,id,post,label):
        with self.db:
            cur=self.db.execute('UPDATE posts SET review_label=?,reviewed_at=? WHERE monitor_id=? AND id=?',(label,now() if label else None,id,post))
        if not cur.rowcount:raise ValueError('Comment not found')
        return {'saved':True}
    def runs(self,id):return [dict(r) for r in self.db.execute('SELECT * FROM runs WHERE monitor_id=? ORDER BY started_at DESC LIMIT 10',(id,))]
