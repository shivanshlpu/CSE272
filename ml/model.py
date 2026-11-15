"""Locally trained hybrid classifier: lexical model plus multilingual neural head."""
import os
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
from pathlib import Path
import joblib
import numpy as np
import torch
from torch import nn
from ml.data import ROOT, LABELS, normalize

ENCODER = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
ENCODER_REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'

class SentimentHead(nn.Module):
    def __init__(self):
        super().__init__()
        self.network=nn.Sequential(nn.Linear(384,128),nn.ReLU(),nn.Dropout(.25),nn.Linear(128,3))
    def forward(self,x): return self.network(x)

class LocalModel:
    def __init__(self):
        torch.set_num_threads(4)
        self.bundle=joblib.load(ROOT/'artifacts/model.joblib')
        self.head=SentimentHead()
        self.head.load_state_dict(torch.load(ROOT/'artifacts/neural.pt',map_location='cpu',weights_only=True));self.head.eval()
        self.encoder=None
    def embeddings(self,texts):
        if self.encoder is None:
            from sentence_transformers import SentenceTransformer
            self.encoder=SentenceTransformer(ENCODER,revision=ENCODER_REVISION,local_files_only=True,device='cpu')
            self.encoder.max_seq_length=128
        return self.encoder.encode(texts,batch_size=64,show_progress_bar=False,normalize_embeddings=True)
    def predict(self,texts):
        cleaned=[normalize(t) for t in texts]
        lexical=self.bundle['lexical'].predict_proba(cleaned)
        alpha=self.bundle['alpha']
        if alpha > 0:
            with torch.no_grad(): neural=torch.softmax(self.head(torch.tensor(self.embeddings(texts))),dim=1).numpy()
            probs=(1-alpha)*lexical+alpha*neural
        else: probs=lexical
        outputs=[]
        for text,p in zip(texts,probs):
            winner=int(p.argmax())
            outputs.append({'text':text,'label':LABELS[winner],'probabilities':{label:float(p[i]) for i,label in enumerate(LABELS)},'confidence':float(p.max()),'uncertain':bool(p.max()<self.bundle['review_threshold']),'polarity':float(p[2]-p[0])})
        return outputs
