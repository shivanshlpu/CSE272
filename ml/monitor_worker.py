"""Single-process durable storage and trained-model worker behind the API."""
import json
import sys
import re
import traceback
from ml.data import ROOT
from ml.monitor_store import MonitorStore
from ml.monitor_analysis import summarize
from ml.model import LocalModel
from ml.stance import StanceModel,LABELS

store=MonitorStore();model=None;stance=None;cache={}
def models():
    global model,stance
    if model is None:model=LocalModel()
    if stance is None:stance=StanceModel(model)
    return model,stance

def language(text):
    # Script identification only; Roman-script Hindi cannot be reliably identified here.
    return 'Devanagari / mixed' if re.search(r'[\u0900-\u097f]',text) else 'Latin / other (language unverified)'

def handle(action,p):
    if action=='list':return store.list()
    if action=='create':return store.create(p)
    if action=='get':return store.get(p['id'])
    if action=='toggle':return store.toggle(p['id'],p['enabled'])
    if action=='delete':cache.pop(p['id'],None);return store.delete(p['id'])
    if action=='quota':return store.reserve_quota(p['units'],p['budget'])
    if action=='status':return {'quota_used':store.quota(),'model_ready':(ROOT/'artifacts/stance.joblib').exists() and (ROOT/'artifacts/model.joblib').exists()}
    if action=='start':return store.run_start(p['id'])
    if action=='finish':cache.pop(p['id'],None);return store.run_finish(p['id'],p['run'],p['status'],p['details'])
    if action=='prune':
        removed=store.prune()
        if removed:cache.clear()
        return {'removed':removed}
    if action=='review':cache.pop(p['id'],None);return store.review(p['id'],p['post_id'],p['label'])
    if action=='ingest':
        monitor=store.get(p['id'])
        if not monitor:raise ValueError('Monitor not found')
        rows=p['posts'];sent,st=models()
        for offset in range(0,len(rows),64):
            batch=rows[offset:offset+64];texts=[r['text'] for r in batch]
            for row,sm,stance_pred in zip(batch,sent.predict(texts),st.predict(texts,monitor['target'])):
                row.update(sentiment=sm,stance=stance_pred,language=language(row['text']))
        cache.pop(p['id'],None);return store.upsert(p['id'],rows)
    if action=='analysis':
        id=p['id'];store.prune();posts=store.posts(id)
        # Includes source refresh/edit/review in the key; ages across time windows expire each minute.
        import time
        key=(int(time.time()/60),tuple((r['id'],r['updated_at'],r['refreshed_at'],r['reviewed_at']) for r in posts))
        if id not in cache or cache[id][0]!=key:
            enc=models()[0] if posts else None
            summary=summarize(posts,enc)
            summary.update(records=posts[:100],record_limit=100,analysis_limit=2000,total_stored=store.db.execute('SELECT count(*) FROM posts WHERE monitor_id=?',(id,)).fetchone()[0])
            cache[id]=(key,summary)
        return {**cache[id][1],'runs':store.runs(id)}
    if action=='predict':
        sent,st=models();texts=p['texts'];a=sent.predict(texts);b=st.predict(texts,p['target'])
        return {'predictions':[{'text':t,'sentiment':s,'stance':v} for t,s,v in zip(texts,a,b)]}
    raise ValueError('Unknown worker action')

if __name__=='__main__':
    # Mark interrupted collection jobs rather than silently leaving them running after restart.
    with store.db:store.db.execute("UPDATE runs SET status='interrupted',finished_at=datetime('now') WHERE status='running'")
    for line in sys.stdin:
        req=None
        try:
            req=json.loads(line);result=handle(req['action'],req.get('payload',{}))
            print(json.dumps({'id':req['id'],'result':result},ensure_ascii=False),flush=True)
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            print(json.dumps({'id':req.get('id') if req else None,'error':str(exc)}),flush=True)
