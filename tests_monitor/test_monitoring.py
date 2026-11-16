"""Isolated fixtures for behavior verification; never used as training or live data."""
from datetime import datetime,timezone,timedelta
import json
import hashlib
import pytest
from ml.monitor_store import MonitorStore
from ml.monitor_analysis import summarize
from ml.data import ROOT

def fixture_post(id='comment-1',published='2026-11-16T10:00:00+00:00'):
    return dict(id=id,text='Fixture comment for storage tests',video_id='CswOUBuokjo',url='https://www.youtube.com/watch?v=CswOUBuokjo&lc='+id,published_at=published,updated_at=published,likes=3,language='unverified',sentiment={'label':'Negative'},stance={'label':'Agree','confidence':.7})
def setup(tmp_path):
    store=MonitorStore(tmp_path/'test.sqlite');m=store.create(dict(name='Fixture monitor',target='A specific fixture claim',videos=['CswOUBuokjo'],interval_seconds=300));return store,m['id']
def test_idempotence_review_persistence_and_edit_invalidation(tmp_path):
    s,id=setup(tmp_path);p=fixture_post();s.upsert(id,[p]);s.review(id,p['id'],'Disagree');s.upsert(id,[p]);assert len(s.posts(id))==1;assert s.posts(id)[0]['review_label']=='Disagree'
    reopened=MonitorStore(tmp_path/'test.sqlite');assert reopened.posts(id)[0]['review_label']=='Disagree'
    p['text']='Edited fixture comment';s.upsert(id,[p]);assert s.posts(id)[0]['review_label'] is None
    s.delete(id);assert s.posts(id)==[]
def test_retention_and_budget_survive_restart(tmp_path):
    s,id=setup(tmp_path);s.upsert(id,[fixture_post()])
    with s.db:s.db.execute("UPDATE posts SET refreshed_at='2020-01-01T00:00:00+00:00'")
    s.prune();assert s.posts(id)==[]
    s.reserve_quota(2,3);s2=MonitorStore(tmp_path/'test.sqlite');assert s2.quota()==2
    with pytest.raises(ValueError):s2.reserve_quota(2,3)
    assert s2.quota()==2

def test_stance_not_conflated_with_sentiment_and_review_takes_precedence():
    p=fixture_post();p['review_label']='Disagree'
    summary=summarize([p],at=datetime(2026,11,16,12,tzinfo=timezone.utc))
    assert summary['sentiment']['Negative']==1;assert summary['stance']['Disagree']==1;assert summary['stance']['Agree']==0
    assert summary['negative_shift_pp'] is None;assert summary['timeline'][0]['reviewed']==1

def test_real_timestamp_windows_and_minimum_support():
    now=datetime(2026,11,16,12,tzinfo=timezone.utc);posts=[]
    for i in range(20):
        p=fixture_post(str(i),(now-timedelta(hours=2 if i<10 else 26)).isoformat());p['review_label']=None
        p['sentiment']['label']='Negative' if i<10 else 'Positive';posts.append(p)
    result=summarize(posts,at=now);assert result['negative_shift_pp']==100;assert result['recent_count']==10;assert result['previous_count']==10

def test_downloaded_stance_splits_and_model_provenance():
    import pandas as pd
    df=pd.read_parquet(ROOT/'data/stance/corpus.parquet')
    a,b,c=[set(df[df.split==s].hash) for s in ['train','val','test']]
    assert not(a&b or a&c or b&c)
    report=json.loads((ROOT/'artifacts/stance_metrics.json').read_text())
    assert report['artifact_sha256']==hashlib.sha256((ROOT/'artifacts/stance.joblib').read_bytes()).hexdigest()
    assert report['test']['macro_f1']>report['baseline_test']['macro_f1']
    for source in report['provenance']['files']:
        assert hashlib.sha256((ROOT/'data/stance'/source['file']).read_bytes()).hexdigest()==source['sha256']

def test_trained_models_through_worker_storage_and_analytics(tmp_path):
    import subprocess,sys,os
    import pandas as pd
    # Real benchmark text, with clearly isolated test-only source metadata.
    texts=pd.read_parquet(ROOT/'data/stance/corpus.parquet').query("split == 'test'").head(8).text.tolist()
    env={**os.environ,'MONITOR_DB':str(tmp_path/'worker.sqlite'),'HF_HUB_OFFLINE':'1'}
    proc=subprocess.Popen([sys.executable,'-u','-m','ml.monitor_worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,env=env,cwd=ROOT)
    def call(action,payload):
        proc.stdin.write(json.dumps({'id':'test','action':action,'payload':payload})+'\n');proc.stdin.flush()
        answer=json.loads(proc.stdout.readline());assert 'error' not in answer,answer;return answer['result']
    try:
        m=call('create',dict(name='Isolated worker test',target='Climate Change is a Real Concern',videos=['CswOUBuokjo'],interval_seconds=300))
        posts=[]
        for i,text in enumerate(texts):
            p=fixture_post(str(i));p['text']=text;p.pop('sentiment');p.pop('stance');posts.append(p)
        assert call('ingest',{'id':m['id'],'posts':posts})['processed']==8
        summary=call('analysis',{'id':m['id']});assert summary['count']==8;assert len(summary['themes'])>=1;assert sum(summary['stance'].values())==8
        assert all(p['stance']['review_required'] for p in summary['records'])
        call('review',{'id':m['id'],'post_id':'0','label':'Agree'})
        assert call('analysis',{'id':m['id']})['reviewed']==1
    finally:proc.terminate();proc.wait(timeout=10)
