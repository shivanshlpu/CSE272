"""Cached multilingual Hugging Face ingestion with explicit synthetic fallback."""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.config import DATA_DIR
from src.ingestion import generate_synthetic_benchmark
from src.schema import validate_schema


def load_corpus(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Stream available corpus rows; preserve provenance for fallback portions."""
    from datasets import load_dataset
    import json
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f'corpus_v2_{n_samples}_{seed}.parquet'
    meta = path.with_suffix('.json')
    if path.exists() and meta.exists():
        result = validate_schema(pd.read_parquet(path))
        result.attrs['messages'] = json.loads(meta.read_text())
        return result
    rng = np.random.default_rng(seed)
    rows, messages = [], []
    sources = [('cardiffnlp/tweet_sentiment_multilingual', 'english', 'en'), ('cardiffnlp/tweet_sentiment_multilingual', 'hindi', 'hi'), ('Abhishek4896/hindi-english-code-mixed-tweets-sentiment', None, 'hi-en')]
    for dataset, config, lang in sources:
        quota = n_samples // 3 + (n_samples % 3 if lang == 'hi-en' else 0)
        count = 0
        try:
            stream = load_dataset(dataset, config, split='train', streaming=True)
            for row in stream:
                if count >= quota:
                    break
                label = row.get('label', row.get('sentiment'))
                if isinstance(label, str):
                    label = {'negative':0,'neutral':1,'positive':2}.get(label.lower(), -1)
                if not isinstance(label, int) or label not in [0, 1, 2]:
                    raise ValueError('Unverified dataset label mapping')
                rows.append(dict(post_id=f'HF_{lang}_{count}', timestamp=(datetime.utcnow()-timedelta(seconds=int(rng.integers(604800)))).strftime('%Y-%m-%d %H:%M:%S'), author=f'@anonymous_{lang}_{count}', text=str(row.get('text', row.get('tweet', ''))), lang=lang, likes=int(rng.lognormal(3, 1)), replies=int(rng.lognormal(1, 1)), author_followers=max(1, int(rng.lognormal(5, 1))), state=None, lat=np.nan, lon=np.nan, source='HuggingFace', ground_truth=['Negative','Neutral','Positive'][label]))
                count += 1
            messages.append(f'{dataset}: {count} real rows')
        except Exception as exc:
            messages.append(f'{dataset}: unavailable ({type(exc).__name__}); synthetic replacement')
        if count < quota:
            messages.append(f'{lang}: {quota-count} synthetic rows added because source was unavailable or exhausted')
            fallback = generate_synthetic_benchmark(max(quota-count, 30), seed)
            choices = fallback[(fallback.lang == lang) & ~fallback.true_is_bot]
            for i in range(quota-count):
                record = choices.iloc[i % len(choices)].to_dict()
                record['post_id'] = f'FALLBACK_{lang}_{i}'
                rows.append(record)
    result = validate_schema(pd.DataFrame(rows))
    result.to_parquet(path, index=False)
    meta.write_text(json.dumps(messages))
    result.attrs['messages'] = messages
    return result
