"""Train baselines, refine hyperparameters, early-stop a neural head and test once."""
import argparse
import copy
import hashlib
import json
import time
import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report, log_loss
from torch.utils.data import DataLoader, TensorDataset
from ml.data import ROOT, DATA, LABELS
from ml.model import ENCODER, ENCODER_REVISION, SentimentHead


def scores(y,probs):
    pred=probs.argmax(axis=1)
    return {'accuracy':float(accuracy_score(y,pred)),'macro_f1':float(f1_score(y,pred,average='macro')),'log_loss':float(log_loss(y,probs,labels=[0,1,2]))}


def train():
    parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=25);args=parser.parse_args()
    torch.manual_seed(42);np.random.seed(42);torch.set_num_threads(4)
    root=ROOT/'artifacts';root.mkdir(exist_ok=True)
    df=pd.read_parquet(DATA/'corpus.parquet');groups={s:df[df.split==s].reset_index(drop=True) for s in ['train','validation','test']}
    tr,va,te=[groups[s] for s in ['train','validation','test']]
    assert not set(tr.text_hash)&set(va.text_hash) and not set(tr.text_hash)&set(te.text_hash)
    trials=[];start=time.perf_counter()
    baseline=Pipeline([('tfidf',TfidfVectorizer(max_features=30000,sublinear_tf=True)),('classifier',LogisticRegression(C=1,max_iter=400,class_weight='balanced'))])
    baseline.fit(tr.normalized,tr.label);base_val=baseline.predict_proba(va.normalized)
    trials.append({'name':'Word unigram baseline','validation':scores(va.label,base_val)})
    print('Baseline',trials[-1],flush=True)
    features=FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2),max_features=45000,min_df=2,sublinear_tf=True)),('character',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=3,max_features=60000,sublinear_tf=True))])
    xtr=features.fit_transform(tr.normalized);xva=features.transform(va.normalized)
    best=None;best_score=-1
    for c in [.5,2.,8.]:
        classifier=LogisticRegression(C=c,max_iter=500,class_weight='balanced',solver='liblinear')
        classifier.fit(xtr,tr.label);probs=classifier.predict_proba(xva);metric=scores(va.label,probs)
        trials.append({'name':f'Word + character / C={c}','validation':metric});print(trials[-1],flush=True)
        if metric['macro_f1']>best_score: best_score=metric['macro_f1'];best=classifier
    lexical=Pipeline([('features',features),('classifier',best)])
    from sentence_transformers import SentenceTransformer
    encoder=SentenceTransformer(ENCODER,revision=ENCODER_REVISION,local_files_only=True,device='cpu');encoder.max_seq_length=128
    embeddings={}
    for split,part in groups.items():
        key=hashlib.sha256(('maxlen128-normalized|'+''.join(part.text_hash)).encode()).hexdigest()[:16]
        path=root/f'embeddings_{key}.npy'
        if path.exists(): emb=np.load(path)
        else:
            print(f'Encoding {split}: {len(part)} downloaded posts',flush=True)
            emb=encoder.encode(part.text.tolist(),batch_size=64,normalize_embeddings=True,show_progress_bar=True);np.save(path,emb)
        embeddings[split]=torch.tensor(emb,dtype=torch.float32)
    head=SentimentHead();optimizer=torch.optim.AdamW(head.parameters(),lr=.001,weight_decay=.01)
    counts=np.bincount(tr.label,minlength=3);loss_fn=torch.nn.CrossEntropyLoss(weight=torch.tensor(len(tr)/(3*counts),dtype=torch.float32))
    loader=DataLoader(TensorDataset(embeddings['train'],torch.tensor(tr.label.to_numpy(),dtype=torch.long)),batch_size=128,shuffle=True,generator=torch.Generator().manual_seed(42))
    history=[];best_f1=-1;best_state=None;patience=0
    for epoch in range(args.epochs):
        head.train();total=0
        for x,y in loader:
            optimizer.zero_grad();loss=loss_fn(head(x),y);loss.backward();torch.nn.utils.clip_grad_norm_(head.parameters(),1.);optimizer.step();total+=loss.item()*len(y)
        head.eval()
        with torch.no_grad(): val_probs=torch.softmax(head(embeddings['validation']),dim=1).numpy()
        metric=scores(va.label,val_probs);history.append({'epoch':epoch+1,'train_loss':total/len(tr),**metric});print('Neural',history[-1],flush=True)
        if metric['macro_f1']>best_f1+1e-4: best_f1=metric['macro_f1'];best_state=copy.deepcopy(head.state_dict());patience=0
        else: patience+=1
        if patience>=5: break
    head.load_state_dict(best_state);head.eval();torch.save(head.state_dict(),root/'neural.pt')
    with torch.no_grad(): neural_val=torch.softmax(head(embeddings['validation']),dim=1).numpy()
    lexical_val=lexical.predict_proba(va.normalized)
    chosen_alpha=0;selection_score=-1
    for alpha in [0,.25,.5,.75,1.]:
        metrics=scores(va.label,(1-alpha)*lexical_val+alpha*neural_val)
        trials.append({'name':f'Hybrid / neural weight {alpha}','validation':metrics})
        if metrics['macro_f1']>selection_score: selection_score=metrics['macro_f1'];chosen_alpha=alpha
    # Test labels are first used here, after all model and blend choices are fixed.
    with torch.no_grad(): neural_test=torch.softmax(head(embeddings['test']),dim=1).numpy()
    test_probs=(1-chosen_alpha)*lexical.predict_proba(te.normalized)+chosen_alpha*neural_test
    base_test=baseline.predict_proba(te.normalized)
    threshold=.60
    bundle={'lexical':lexical,'alpha':chosen_alpha,'review_threshold':threshold,'labels':LABELS}
    joblib.dump(bundle,root/'model.joblib');joblib.dump(baseline,root/'baseline.joblib')
    report={'model':'Multilingual lexical + neural ensemble','version':'2.0','seed':42,'encoder':ENCODER,'encoder_revision':ENCODER_REVISION,'encoder_training':'Frozen pretrained encoder; 49,667-parameter neural head trained locally with AdamW and early stopping. Encoder weights are NOT fine-tuned.','training_rows':len(tr),'validation_rows':len(va),'test_rows':len(te),'selected_neural_weight':chosen_alpha,'review_threshold':threshold,'baseline_test':scores(te.label,base_test),'test':scores(te.label,test_probs),'per_language':{lang:scores(te.loc[te.lang==lang,'label'],test_probs[te.lang.to_numpy()==lang]) for lang in sorted(te.lang.unique())},'confusion_matrix':confusion_matrix(te.label,test_probs.argmax(axis=1),labels=[0,1,2]).tolist(),'labels':LABELS,'classification_report':classification_report(te.label,test_probs.argmax(axis=1),target_names=LABELS,output_dict=True),'trials':trials,'neural_history':history,'seconds':time.perf_counter()-start,'provenance':json.loads((DATA/'manifest.json').read_text()),'limitations':['No sarcasm/emotion labels; these capabilities are not claimed.','Dataset cards and upstream rights govern reuse; downloaded social text may contain offensive content.','No post timestamps or engagement available: no invented trend timeline or reach weighting.','Frozen encoder pretraining overlap is unknown; exact normalized duplicates removed, near-duplicates not fully audited.','Probabilities are uncalibrated estimates; review threshold is a fixed heuristic, not a guaranteed error bound.']}
    report['artifacts_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['model.joblib','neural.pt']}
    (root/'metrics.json').write_text(json.dumps(report,indent=2))
    print('TEST',json.dumps(report['test']), 'BASELINE',json.dumps(report['baseline_test']),flush=True)

if __name__=='__main__': train()
