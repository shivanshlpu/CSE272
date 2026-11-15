import pandas as pd
import pytest
from src.ingestion import generate_synthetic_benchmark
from src.schema import validate_schema


def test_determinism_and_attack_contract():
    a = generate_synthetic_benchmark(100)
    pd.testing.assert_frame_equal(a, generate_synthetic_benchmark(100))
    assert len(a) == 135 and a.true_is_bot.sum() == 35
    assert set(a.lang) == {'en', 'hi', 'hi-en'}
    assert (a.loc[a.true_is_bot, 'likes'] <= 5).all()


def test_reject_duplicate_and_negative_engagement():
    a = generate_synthetic_benchmark(10)
    a.loc[1, 'post_id'] = a.loc[0, 'post_id']
    with pytest.raises(ValueError):
        validate_schema(a)
    a = generate_synthetic_benchmark(10)
    a.loc[0, 'likes'] = -1
    with pytest.raises(ValueError):
        validate_schema(a)
