"""Persistent stdin/stdout JSON worker behind Node; no model API calls."""
import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD, NMF
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from ml.data import DATA
from ml.model import LocalModel

TAGALOG_MARKERS = {'nung', 'sakin', 'ano', 'bang', 'nam', 'puntahan', 'mga', 'ako', 'ikaw', 'kami'}

POSITIVE_WORDS = {
    'good', 'great', 'superb', 'excellent', 'fast', 'love', 'loved', 'awesome', 'best',
    'badhiya', 'badiya', 'shandaar', 'mast', 'sahi', 'zabardast', 'sundar', 'acha', 'achha',
    'dhanyawad', 'thank', 'thanks', 'instant', 'helpful', 'happy', 'blessed'
}

NEGATIVE_WORDS = {
    'bad', 'worst', 'poor', 'terrible', 'horrible', 'delay', 'delayed', 'cancel', 'cancelled',
    'bekar', 'ghatiya', 'fraud', 'loot', 'nuksaan', 'pareshan', 'bakwaas', 'faltu', 'chor',
    'galti', 'problem', 'issue', 'fail', 'failed', 'scam', 'gussa', 'shame', 'shirminda'
}

SARCASM_MARKERS = {'wah', 'shabaash', 'congrats', 'great job', 'superb job', 'waah'}


def clean_display_text(text):
    """Repair windows-1252 / latin-1 mojibake, clean broken URLs, and trim whitespace."""
    if not isinstance(text, str):
        return ""
    # 1. Fix common mojibake sequences (e.g. ðŸ¤£ -> 🤣, â€¦ -> …)
    try:
        if any(c in text for c in ('â', 'ð', 'à', 'ã', '©', '™', '®')):
            text = text.encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
    except Exception:
        pass
    
    # 2. Fix broken t.co twitter urls with spaces: "https // t . co / xyz"
    text = re.sub(r'https?\s*//\s*t\s*\.\s*co\s*/\s*[A-Za-z0-9_]+', '', text)
    text = re.sub(r'https?://\S+', '', text)
    
    # 3. Clean consecutive punctuation and normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_keywords(text):
    """Identify key lexical driver terms for transparent model explainability."""
    words = re.findall(r'[A-Za-z0-9_\u0900-\u097F]+', text.lower())
    found_pos = [w for w in words if w in POSITIVE_WORDS]
    found_neg = [w for w in words if w in NEGATIVE_WORDS]
    found_sarcasm = [w for w in words if w in SARCASM_MARKERS]
    return {
        'positive_terms': list(dict.fromkeys(found_pos)),
        'negative_terms': list(dict.fromkeys(found_neg)),
        'sarcasm_indicators': list(dict.fromkeys(found_sarcasm))
    }


def compute_post_enrichment(text, prediction, likes=15, replies=2, followers=500, is_bot=False):
    """Compute PRD Impact-Weight, Bot-status, and Pragmatic Emotion."""
    # PRD equation: W = ln(1 + Likes + 2*Replies + 0.01*Followers)
    weight = float(np.log(1 + likes + 2 * replies + 0.01 * followers))
    effective_weight = 0.0 if is_bot else max(weight, 0.1)
    
    polarity = prediction.get('polarity', 0.0)
    low_text = text.lower()
    
    # Pragmatic Emotion assignment
    if any(m in low_text for m in SARCASM_MARKERS) and polarity < 0.2:
        emotion = "Sarcasm"
    elif polarity < -0.35:
        emotion = "Outrage" if ('!' in text or 'chor' in low_text or 'fraud' in low_text) else "Concern"
    elif polarity > 0.35:
        emotion = "Praise"
    elif '?' in text or 'why' in low_text or 'kya' in low_text:
        emotion = "Concern"
    else:
        emotion = "Informative"

    return {
        'weight': round(weight, 2),
        'effective_weight': round(effective_weight, 2),
        'emotion': emotion,
        'is_bot': bool(is_bot)
    }


def run():
    model = None
    corpus = None
    for line in sys.stdin:
        request = None
        try:
            request = json.loads(line)
            if model is None:
                model = LocalModel()
            if corpus is None:
                corpus = pd.read_parquet(DATA / 'corpus.parquet')
            
            action = request['action']
            payload = request.get('payload', {})
            
            # ---------------- 1. PREDICT (Single / Batch Tester) ----------------
            if action == 'predict':
                texts = payload.get('texts', [])
                cleaned_texts = [clean_display_text(t) for t in texts]
                start_time = time.perf_counter()
                raw_preds = model.predict(cleaned_texts)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                
                predictions = []
                for orig, cleaned, p in zip(texts, cleaned_texts, raw_preds):
                    keywords = extract_keywords(cleaned)
                    enrichment = compute_post_enrichment(cleaned, p)
                    p['original_text'] = orig
                    p['cleaned_text'] = cleaned
                    p['keywords'] = keywords
                    p['emotion'] = enrichment['emotion']
                    p['latency_ms'] = latency_ms
                    predictions.append(p)
                
                result = {
                    'predictions': predictions,
                    'latency_ms': latency_ms,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'engine': 'Local PyTorch Hybrid MiniLM + TF-IDF (On-Device, 0 Cloud Calls)'
                }
            
            # ---------------- 2. EXPLORE (Monitor Feed & Topic Clustering) ----------------
            elif action == 'explore':
                selected = corpus[corpus.split == 'test']
                lang = payload.get('lang', 'all')
                query = payload.get('query', '').strip()
                
                if lang != 'all':
                    selected = selected[selected.lang == lang]
                
                # Filter out noisy Tagalog rows from SemEval SentiMix
                if lang in ('all', 'hi-en'):
                    selected = selected[~selected.text.apply(
                        lambda t: any(w in set(str(t).lower().split()) for w in TAGALOG_MARKERS)
                    )]
                
                if query:
                    selected = selected[selected.text.str.contains(query, case=False, regex=False)]
                
                total = len(selected)
                selected = selected.sample(min(total, 90), random_state=42).reset_index(drop=True)
                
                # Clean up display text for each row
                records = []
                for _, row in selected[['id', 'text', 'lang', 'dataset', 'label']].iterrows():
                    cleaned_t = clean_display_text(str(row['text']))
                    records.append({
                        'id': str(row['id']),
                        'text': cleaned_t,
                        'lang': str(row['lang']),
                        'dataset': str(row['dataset']),
                        'truth': str(row['label'])
                    })
                
                predictions = model.predict([r['text'] for r in records]) if len(records) else []
                for row, prediction in zip(records, predictions):
                    row.update(prediction)
                    # Assign synthetic but deterministic engagement based on hash
                    seed_val = (sum(ord(c) for c in row['id']) + len(row['text'])) % 100
                    likes = seed_val * 4 + 5
                    replies = max(1, int(seed_val * 0.4))
                    followers = 18500 if seed_val > 88 else (seed_val * 60 + 50)
                    is_bot = seed_val < 7 and (len(row['text']) < 40 or row.get('uncertain', False))
                    
                    enrichment = compute_post_enrichment(row['text'], prediction, likes, replies, followers, is_bot)
                    row.update(enrichment)
                    row['likes'] = likes
                    row['replies'] = replies
                    row['followers'] = followers
                    row['author'] = f"user_{row['id'][:7]}"
                
                topics = []
                if len(selected) >= 5:
                    stop_words = sorted(set(ENGLISH_STOP_WORDS) | set(
                        'user url https http co t rt ke ki ka ko se hai hain ho hi na nahi toh to aur aap hum tum ye yeh woh is us bhi mein me le ab liye par apne apni jo kyunki kaise'.split()
                    ))
                    vectorizer = TfidfVectorizer(max_features=4000, min_df=2, ngram_range=(1, 2), stop_words=stop_words)
                    try:
                        matrix = vectorizer.fit_transform(selected.normalized)
                        k = min(5, matrix.shape[1], len(selected) - 1)
                        topic_model = NMF(n_components=k, random_state=42, max_iter=300, init='nndsvda')
                        weights = topic_model.fit_transform(matrix)
                        terms = vectorizer.get_feature_names_out()
                        coords = TruncatedSVD(n_components=min(2, matrix.shape[1]), random_state=42).fit_transform(matrix)
                        for j, component in enumerate(topic_model.components_):
                            topics.append({
                                'id': j,
                                'title': ' · '.join(terms[component.argsort()[-3:][::-1]]),
                                'count': int((weights.argmax(axis=1) == j).sum())
                            })
                        for i, row in enumerate(records):
                            row.update(
                                topic=int(weights[i].argmax()),
                                x=float(coords[i, 0]),
                                y=float(coords[i, 1]) if coords.shape[1] > 1 else 0.0
                            )
                    except ValueError:
                        pass
                
                result = {
                    'records': records,
                    'topics': topics,
                    'matched': total,
                    'shown': len(records),
                    'projection': 'TF-IDF / SVD projection; NMF exploratory topics'
                }
            
            # ---------------- 3. INGEST (Real-Time Ingestion Endpoint) ----------------
            elif action == 'ingest':
                posts = payload.get('posts', [])
                if not isinstance(posts, list) or len(posts) == 0:
                    raise ValueError('Expected a non-empty list of post objects.')
                
                results = []
                texts = [clean_display_text(p.get('text', '')) for p in posts]
                preds = model.predict(texts)
                
                for p, cleaned, pred in zip(posts, texts, preds):
                    likes = int(p.get('likes', 15))
                    replies = int(p.get('replies', 2))
                    followers = int(p.get('followers', 650))
                    author = str(p.get('author', 'live_contributor')).lstrip('@')
                    lang = str(p.get('lang', 'en'))
                    source = str(p.get('source', 'API Ingestion'))
                    
                    is_bot = bool(p.get('is_bot', False) or (followers < 10 and likes > 500))
                    enrichment = compute_post_enrichment(cleaned, pred, likes, replies, followers, is_bot)
                    
                    post_id = f"live_{int(time.time()*1000)}_{len(results)}"
                    item = {
                        'id': post_id,
                        'text': cleaned,
                        'author': f"@{author}",
                        'lang': lang,
                        'likes': likes,
                        'replies': replies,
                        'followers': followers,
                        'source': source,
                        'dataset': 'Live Ingestion Stream',
                        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'truth': 'Unlabelled (Live)',
                        'x': float(np.random.normal(0, 0.5)),
                        'y': float(np.random.normal(0, 0.5)),
                        'topic': 0
                    }
                    item.update(pred)
                    item.update(enrichment)
                    results.append(item)
                
                result = {'ingested_posts': results, 'count': len(results)}

            # ---------------- 4. RANDOM SAMPLE (Unseen Tester Prompt) ----------------
            elif action == 'random_sample':
                lang = payload.get('lang', 'all')
                pool = corpus[corpus.split == 'test']
                if lang != 'all':
                    pool = pool[pool.lang == lang]
                pool = pool[~pool.text.apply(lambda t: any(w in set(str(t).lower().split()) for w in TAGALOG_MARKERS))]
                sample = pool.sample(1).iloc[0]
                cleaned = clean_display_text(str(sample['text']))
                result = {
                    'text': cleaned,
                    'lang': str(sample['lang']),
                    'dataset': str(sample['dataset']),
                    'ground_truth': str(sample['label'])
                }

            else:
                raise ValueError(f"Unknown action: {action}")
            
            print(json.dumps({'id': request['id'], 'result': result}, ensure_ascii=False), flush=True)
        
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            print(json.dumps({'id': request.get('id') if request else None, 'error': type(exc).__name__ + ': ' + str(exc)}), flush=True)


if __name__ == '__main__':
    run()
