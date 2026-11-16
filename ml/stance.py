"""Target-conditioned stance training on published TweetEval/SemEval data.
NONE is no clear stance, not proof of neutrality. Never infer author affiliations.
"""
import hashlib
import json
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from ml.data import ROOT, normalize
from ml.model import LocalModel

REVISION = '4fbd22cd78421f05b1ecdb4fc5725bc7a7bd8f66'
TARGETS = {'abortion': 'Legalization of Abortion', 'atheism': 'Atheism', 'climate': 'Climate Change is a Real Concern', 'feminist': 'Feminist Movement', 'hillary': 'Hillary Clinton'}
LABELS = ['No clear stance', 'Disagree', 'Agree']
OUT = ROOT / 'artifacts'
DATA = ROOT / 'data/stance'

def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1, status_forcelist=[429,500,502,503,504])))
    rows, manifest = [], []
    for slug, target in TARGETS.items():
        for name in ['mapping.txt'] + [f'{split}_{part}.txt' for split in ['train','val','test'] for part in ['text','labels']]:
            suffix = name if name == 'mapping.txt' else f'{slug}/{name}'
            url=f'https://raw.githubusercontent.com/cardiffnlp/tweeteval/{REVISION}/datasets/stance/{suffix}'
            dest=DATA/f'{slug}_{name}'
            if not dest.exists():
                response=session.get(url, timeout=60); response.raise_for_status()
                dest.write_bytes(response.content)
            manifest.append({'url':url,'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        mapping=(DATA/f'{slug}_mapping.txt').read_text().lower().replace('\\t', '\t')
        assert '0\tnone' in mapping and '1\tagainst' in mapping and '2\tfavor' in mapping, mapping
        for split in ['train','val','test']:
            texts=(DATA/f'{slug}_{split}_text.txt').read_text().splitlines()
            labels=(DATA/f'{slug}_{split}_labels.txt').read_text().splitlines()
            assert len(texts)==len(labels)
            for text,label in zip(texts,labels):
                text=text.replace('#SemST','').replace('#semst','').strip()
                rows.append({'text':text,'target':target,'target_id':slug,'label':int(label),'split':split,'hash':hashlib.sha256(normalize(text).encode()).hexdigest()})
    frame=pd.DataFrame(rows); before=len(frame)
    frame['priority']=frame.split.map({'test':0,'val':1,'train':2})
    frame=frame.sort_values('priority',kind='stable').drop_duplicates('hash').drop(columns='priority')
    frame.to_parquet(DATA/'corpus.parquet',index=False)
    provenance={'revision':REVISION,'files':manifest,'rows_before':before,'rows_after':len(frame),'policy':'Published partitions; normalized text duplicates reserved for test then validation. No generated training examples.'}
    (DATA/'manifest.json').write_text(json.dumps(provenance,indent=2))
    return frame,provenance

def features(encoder,texts,targets):
    # Explicit target/comment interaction instead of re-labelling sentiment.
    a=encoder.embeddings(texts)
    unique=list(dict.fromkeys(targets)); lookup=dict(zip(unique,encoder.embeddings(unique)))
    b=np.asarray([lookup[t] for t in targets])
    pair=encoder.embeddings([f'Target: {t}. Comment: {x}' for t,x in zip(targets,texts)])
    return np.concatenate([a,b,a*b,np.abs(a-b),pair],axis=1)

def scores(y,pred):
    return {'accuracy':float(accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,average='macro',labels=[0,1,2],zero_division=0)),'confusion_matrix':confusion_matrix(y,pred,labels=[0,1,2]).tolist()}

def train():
    start=time.perf_counter();frame,provenance=prepare(); encoder=LocalModel()
    groups={s:frame[frame.split==s].reset_index(drop=True) for s in ['train','val','test']}
    xs={}
    for s,g in groups.items():
        print('Encoding stance',s,len(g),flush=True)
        key=hashlib.sha256(('stance-v1'+''.join(g.hash)+''.join(g.target)).encode()).hexdigest()[:16]
        cache=OUT/f'stance_{key}.npy'
        if cache.exists():xs[s]=np.load(cache)
        else:
            xs[s]=features(encoder,g.text.tolist(),g.target.tolist());np.save(cache,xs[s])
    tr,va,te=[groups[s] for s in ['train','val','test']]
    vector=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,max_features=25000)
    baseline=LogisticRegression(C=1,class_weight='balanced',max_iter=700)
    baseline.fit(vector.fit_transform(tr.target+' '+tr.text),tr.label)
    trials=[];best=None;best_score=-1
    for c in [.1,1,10]:
        classifier=LogisticRegression(C=c,max_iter=1200,class_weight='balanced',random_state=42)
        classifier.fit(xs['train'],tr.label);m=scores(va.label,classifier.predict(xs['val']))
        trials.append({'C':c,'validation':m});print(trials[-1],flush=True)
        if m['macro_f1']>best_score:best_score=m['macro_f1'];best=classifier;selected=c
    # Fixed held-out topic audit, never used to choose hyperparameters.
    mask=tr.target_id!='hillary';testmask=te.target_id=='hillary'
    transfer=LogisticRegression(C=selected,max_iter=1200,class_weight='balanced',random_state=42)
    transfer.fit(xs['train'][mask],tr.label[mask])
    report={'version':'stance-1','labels':LABELS,'model':'Target and comment multilingual embeddings with learned interaction classifier','encoder_training':'Frozen; target-conditioned classifier fitted locally','languages_evaluated':['English'],'training_targets':list(TARGETS.values()),'splits':{s:len(g) for s,g in groups.items()},'selected_C':selected,'validation_trials':trials,'test':scores(te.label,best.predict(xs['test'])),'baseline_test':scores(te.label,baseline.predict(vector.transform(te.target+' '+te.text))),'unseen_target_audit':{'target':'Hillary Clinton','test_rows':int(testmask.sum()),**scores(te.label[testmask],transfer.predict(xs['test'][testmask]))},'per_target':{t:scores(te.label[te.target==t],best.predict(xs['test'][te.target==t])) for t in te.target.unique()},'provenance':provenance,'seconds':time.perf_counter()-start,'limitations':['English benchmark only: Hindi/Hinglish transfer is unvalidated.','New policies, videos and brands differ from the training targets; analyst review required.','NONE means no clear stance, including off-target text, not verified neutrality.','Probabilities are not calibrated; no population-level opinion estimates.']}
    joblib.dump({'classifier':best,'labels':LABELS},OUT/'stance.joblib')
    report['artifact_sha256']=hashlib.sha256((OUT/'stance.joblib').read_bytes()).hexdigest()
    (OUT/'stance_metrics.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:report[k] for k in ['test','baseline_test','unseen_target_audit','seconds']}),flush=True)

class StanceModel:
    def __init__(self,encoder):
        self.encoder=encoder;self.bundle=joblib.load(OUT/'stance.joblib')
    def predict(self,texts,target):
        probabilities=self.bundle['classifier'].predict_proba(features(self.encoder,texts,[target]*len(texts)))
        return [{'label':LABELS[int(p.argmax())],'confidence':float(p.max()),'probabilities':dict(zip(LABELS,map(float,p))),'review_required':True,'reason':'New-topic and multilingual transfer requires analyst validation.'} for p in probabilities]

if __name__=='__main__':train()
