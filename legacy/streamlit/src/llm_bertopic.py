"""Multilingual BERTopic with explicit offline TF-IDF/SVD fallback."""
import hashlib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from src.config import DATA_DIR, SEED
from src.llm_engine import get_client


def fit_topics(df: pd.DataFrame, semantic: bool = False, provider: str = 'auto') -> pd.DataFrame:
    """Use cached multilingual embeddings when requested, otherwise offline lexical topics."""
    result = df.copy()
    result['topic_id'], result['topic_prob'] = -1, 0.
    result['umap_x'], result['umap_y'] = 0., 0.
    result['topic_title'] = 'Uncategorized'
    ids = result.index[~result.is_bot]
    texts = result.loc[ids, 'clean_text'].tolist()
    mode, warning = 'offline TF-IDF / SVD (not UMAP)', ''
    if len(texts) >= 3:
        model = None
        try:
            if not semantic:
                raise RuntimeError('Semantic mode not requested')
            from sentence_transformers import SentenceTransformer
            from bertopic import BERTopic
            from bertopic.representation import OpenAI
            from umap import UMAP
            from hdbscan import HDBSCAN
            DATA_DIR.mkdir(exist_ok=True)
            key = hashlib.sha256(('multilingual-MiniLM-L12-v2|'+'\n'.join(texts)).encode()).hexdigest()
            path = DATA_DIR / f'embeddings_{key}.npy'
            embeddings = np.load(path) if path.exists() else SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2').encode(texts, show_progress_bar=False)
            if not path.exists():
                np.save(path, embeddings)
            client, llm = get_client(provider)
            representation = OpenAI(client, model=llm, chat=True, prompt='Describe this topic in exactly four or five words. Documents: [DOCUMENTS] Keywords: [KEYWORDS]') if client else None
            neighbors = min(15, len(texts)-1)
            reducer = UMAP(n_components=2, n_neighbors=neighbors, random_state=SEED, init='random')
            coords = reducer.fit_transform(embeddings)
            model = BERTopic(umap_model=UMAP(n_components=min(5,len(texts)-2), n_neighbors=neighbors, random_state=SEED, init='random'), hdbscan_model=HDBSCAN(min_cluster_size=max(2,min(15,len(texts)//10)), prediction_data=True), representation_model=representation)
            labels, probs = model.fit_transform(texts, embeddings)
            probs = np.ones(len(texts)) if probs is None else np.asarray(probs)
            if probs.ndim > 1:
                probs = probs.max(axis=1)
            mode = 'Multilingual MiniLM + UMAP + HDBSCAN / BERTopic'
        except Exception as exc:
            warning = '' if not semantic else f'Semantic mode unavailable ({type(exc).__name__}); lexical fallback active.'
            try:
                vectorizer = TfidfVectorizer(max_features=10000, token_pattern=r'(?u)\b\w+\b')
                matrix = vectorizer.fit_transform(texts)
                dims = min(2, matrix.shape[1]-1)
                coords = TruncatedSVD(n_components=dims, random_state=SEED).fit_transform(matrix) if dims > 0 else np.zeros((len(texts),1))
                if coords.shape[1] < 2:
                    coords = np.pad(coords, ((0,0),(0,1)))
                k = min(8, max(2,int(np.sqrt(len(texts)/2))), len(set(texts)))
                cluster = KMeans(n_clusters=k, random_state=SEED, n_init=10).fit(matrix)
                labels = cluster.labels_
                distance = cluster.transform(matrix).min(axis=1)
                probs = 1/(1+distance)
            except ValueError:
                labels, probs, coords = np.full(len(texts),-1), np.zeros(len(texts)), np.zeros((len(texts),2))
        result.loc[ids,'topic_id'] = labels
        result.loc[ids,'topic_prob'] = probs
        result.loc[ids,['umap_x','umap_y']] = coords
        for topic in set(labels)-{-1}:
            topic_texts = result.loc[result.topic_id == topic,'clean_text']
            try:
                vec = TfidfVectorizer(max_features=1000)
                mat = vec.fit_transform(topic_texts)
                words = vec.get_feature_names_out()[np.argsort(np.asarray(mat.sum(axis=0)).ravel())[-3:][::-1]].tolist()
            except ValueError:
                words = ['public','discussion','topic']
            title_words = (words+['public','discussion','trend'])[:3]+['Discussion']
            if model:
                representation = model.get_topic(topic)
                if representation and 4 <= len(representation[0][0].split()) <= 5:
                    title_words = representation[0][0].split()
            result.loc[result.topic_id == topic,'topic_title'] = ' '.join(title_words).title()
    result['driver_score'] = result.topic_prob * result.effective_weight
    result.attrs.update(df.attrs)
    result.attrs['topic_mode'], result.attrs['topic_warning'] = mode, warning
    return result


def representative_posts(df: pd.DataFrame) -> dict:
    return {int(topic): group.nlargest(3,'driver_score') for topic, group in df[(df.topic_id >= 0) & ~df.is_bot].groupby('topic_id')}
