import json
import numpy as np
import pytest
from src.ingestion import generate_synthetic_benchmark
from src.preprocessing import preprocess, clean_text, tag_language, geo_map
from src.llm_engine import analyze, parse_result, weighted_sentiment, sentiment_timeline
from src.llm_bertopic import fit_topics, representative_posts


def test_clean_language_geo():
    assert clean_text('वाह! https://x.test 😀  ठीक') == 'वाह! 😀 ठीक'
    assert tag_language('bhai service mast hai') == 'hi-en'
    assert tag_language('नमस्ते') == 'hi'
    assert geo_map('Mumbai service')[0] == 'Maharashtra'
    assert geo_map('unknown')[0] is None


def test_bots_weights_and_ranker():
    raw = generate_synthetic_benchmark(150)
    data = preprocess(raw)
    assert np.array_equal(data.is_bot, raw.true_is_bot)
    inferred = analyze(data, use_cache=False)
    assert inferred.loc[inferred.is_bot,'effective_weight'].eq(0).all()
    expected = np.log1p(inferred.likes+2*inferred.replies+.01*inferred.author_followers)
    assert np.allclose(inferred.weight,expected)
    topics = fit_topics(inferred)
    assert topics[['umap_x','umap_y']].notna().all().all()
    assert all(len(p) <= 3 for p in representative_posts(topics).values())
    assert all(4 <= len(t.split()) <= 5 for t in topics.loc[topics.topic_id >= 0,'topic_title'])


def test_shift_and_json_validation():
    data = analyze(preprocess(generate_synthetic_benchmark(10)), use_cache=False).iloc[:2].copy()
    data['timestamp'] = ['2026-01-01 00:00:00','2026-01-02 00:00:00']
    data['polarity'] = [.8,-.8]
    data['effective_weight'] = [1.,1.]
    assert weighted_sentiment(data) == 0
    assert sentiment_timeline(data)['shift'].tolist() == [False,True]
    with pytest.raises(ValueError):
        parse_result(json.dumps(dict(polarity=2,label='Positive')))
    with pytest.raises(ValueError):
        parse_result(json.dumps(dict(polarity=0,label='Neutral',emotion='Informative',is_sarcastic='false',reason='x')))


def test_hindi_combining_marks_remain_in_sentiment_tokens():
    from src.llm_engine import lexicon_baseline
    assert lexicon_baseline('सेवा अच्छी है।') == 'Positive'
    assert lexicon_baseline('सेवा खराब है।') == 'Negative'
