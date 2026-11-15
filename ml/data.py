"""Download published data with provenance; never synthesize missing examples."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/downloaded'
LABELS = ['Negative', 'Neutral', 'Positive']
CARDIFF_REV = 'main'
SENTIMIX_REV = '205f0391fc1f10320ec3c10708eaa27e88db04c7'


def normalize(text):
    text = unicodedata.normalize('NFKC', str(text)).lower()
    text = re.sub(r'https?://\S+|www\.\S+', ' URL ', text)
    text = re.sub(r'@\w+', ' USER ', text)
    return re.sub(r'\s+', ' ', text).strip()


def download(url, filename, manifest):
    path = DATA/filename
    if not path.exists():
        response = requests.get(url,timeout=90)
        response.raise_for_status()
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_bytes(response.content)
        temporary.replace(path)
    manifest.append({'url':url,'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    return path


def conll(path, split, labels=None):
    rows=[]
    for block in re.split(r'\n\s*\n',path.read_text().strip()):
        lines=block.splitlines(); header=lines[0].split('\t')
        if header[0]!='meta':
            raise ValueError('Unexpected SentiMix format')
        text=' '.join(line.split('\t')[0] for line in lines[1:] if line.strip())
        sentiment=header[2] if len(header)>2 else labels[header[1]]
        rows.append({'id':'sentimix_'+header[1],'text':text,'label':LABELS.index(sentiment.title()),'lang':'hi-en','split':split,'dataset':'SentiMix 2020'})
    return rows


def prepare():
    DATA.mkdir(exist_ok=True,parents=True)
    manifest=[]; rows=[]
    # Resolve and record immutable Cardiff revision before downloads.
    revision_file=DATA/'cardiff_revision.txt'
    if revision_file.exists():
        revision=revision_file.read_text().strip()
    else:
        response=requests.get('https://huggingface.co/api/datasets/cardiffnlp/tweet_sentiment_multilingual',timeout=30)
        response.raise_for_status();revision=response.json()['sha'];revision_file.write_text(revision)
    for language,lang in [('english','en'),('hindi','hi')]:
        for split in ['train','validation','test']:
            name=f'cardiff_{language}_{split}.jsonl'
            path=download(f'https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_multilingual/resolve/{revision}/data/{language}/{split}.jsonl',name,manifest)
            for i,line in enumerate(path.read_text().splitlines()):
                row=json.loads(line)
                if int(row['label']) not in [0,1,2]: raise ValueError('Invalid label')
                rows.append({'id':f'cardiff_{lang}_{split}_{i}','text':row['text'],'label':int(row['label']),'lang':lang,'split':split,'dataset':'Cardiff multilingual tweets'})
    base=f'https://huggingface.co/datasets/RTT1/SentiMix/resolve/{SENTIMIX_REV}/'
    files={name:download(base+name,name,manifest) for name in ['train_14k_split_conll.txt','dev_3k_split_conll.txt','Hindi_test_unalbelled_conll_updated.txt','test_labels_hinglish.txt']}
    labels=pd.read_csv(files['test_labels_hinglish.txt'],dtype=str).set_index('Uid').Sentiment.to_dict()
    rows+=conll(files['train_14k_split_conll.txt'],'train')
    rows+=conll(files['dev_3k_split_conll.txt'],'validation')
    rows+=conll(files['Hindi_test_unalbelled_conll_updated.txt'],'test',labels)
    df=pd.DataFrame(rows);before=len(df)
    df['normalized']=df.text.map(normalize)
    df['text_hash']=df.normalized.map(lambda x:hashlib.sha256(x.encode()).hexdigest())
    # Hold out test first; remove exact normalized-text overlaps from train/validation.
    df['priority']=df.split.map({'test':0,'validation':1,'train':2})
    df=df.sort_values('priority',kind='stable').drop_duplicates('text_hash').drop(columns='priority')
    df=df[df.normalized.str.len()>2].reset_index(drop=True)
    df.to_parquet(DATA/'corpus.parquet',index=False)
    report={'sources':manifest,'rows_before_dedup':before,'rows_after_dedup':len(df),'removed':before-len(df),'split_counts':df.groupby(['split','lang']).size().unstack(fill_value=0).to_dict('index'),'policy':'Published splits; normalized exact duplicates reserved for test, then validation, then train. No generated samples or metadata. Near-duplicate leakage remains a limitation.'}
    (DATA/'manifest.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report['split_counts']),flush=True)
    return df

if __name__=='__main__': prepare()
