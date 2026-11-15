import hashlib
import json
import numpy as np
import pandas as pd
from ml.data import DATA, ROOT, normalize
from ml.model import LocalModel


def test_published_data_and_disjoint_splits():
    df=pd.read_parquet(DATA/'corpus.parquet')
    assert set(df.dataset)=={'Cardiff multilingual tweets','SentiMix 2020'}
    assert not df.text_hash.duplicated().any()
    assert set(df.split)=={'train','validation','test'}
    assert set(df.lang)=={'en','hi','hi-en'}
    assert len(df)>25000


def test_download_hashes_and_model_artifacts():
    manifest=json.loads((DATA/'manifest.json').read_text())
    for source in manifest['sources']:
        assert hashlib.sha256((DATA/source['file']).read_bytes()).hexdigest()==source['sha256']
    report=json.loads((ROOT/'artifacts/metrics.json').read_text())
    for name,sha in report['artifacts_sha256'].items():
        assert hashlib.sha256((ROOT/'artifacts'/name).read_bytes()).hexdigest()==sha
    assert len(report['trials'])>=9
    assert len(report['neural_history'])>1


def test_saved_model_predicts_real_test_rows():
    corpus=pd.read_parquet(DATA/'corpus.parquet')
    texts=corpus[corpus.split=='test'].groupby('lang').head(2).text.tolist()
    model=LocalModel();first=model.predict(texts);second=model.predict(texts)
    assert len(first)==6
    for a,b in zip(first,second):
        values=list(a['probabilities'].values())
        assert np.isclose(sum(values),1.,atol=1e-6)
        assert np.allclose(values,list(b['probabilities'].values()),atol=1e-6)
        assert -1<=a['polarity']<=1


def test_normalization_preserves_hindi_and_tone():
    assert normalize('बहुत अच्छा! 😀')=='बहुत अच्छा! 😀'
    assert 'http' not in normalize('Read https://example.org/a')
