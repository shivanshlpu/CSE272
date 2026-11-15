"""Strict canonical boundary validation for public social records."""
import pandas as pd
from pandas.api.types import is_integer_dtype

COLUMNS = ['post_id', 'timestamp', 'author', 'text', 'lang', 'likes', 'replies',
           'author_followers', 'state', 'lat', 'lon', 'source']
SOURCES = {'HuggingFace', 'Reddit', 'YouTube', 'Google News RSS', 'Synthetic'}


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Return the input unchanged or raise ValueError on an invalid contract."""
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    for col in ['post_id', 'timestamp', 'author', 'text', 'lang', 'source']:
        if not df[col].map(lambda x: isinstance(x, str)).all():
            raise ValueError(f'{col} must contain strings')
    if df.post_id.duplicated().any() or df.post_id.eq('').any():
        raise ValueError('post_id must be nonempty and unique')
    if not df.lang.isin(['en', 'hi', 'hi-en']).all() or not df.source.isin(SOURCES).all():
        raise ValueError('Invalid language or source')
    if not df.timestamp.str.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}').all():
        raise ValueError('Invalid timestamp format')
    pd.to_datetime(df.timestamp, format='%Y-%m-%d %H:%M:%S', errors='raise')
    for col, minimum in [('likes', 0), ('replies', 0), ('author_followers', 1)]:
        if not is_integer_dtype(df[col]) or (df[col] < minimum).any():
            raise ValueError(f'Invalid {col}')
    for col, bound in [('lat', 90), ('lon', 180)]:
        values = pd.to_numeric(df[col], errors='raise').dropna()
        if not values.between(-bound, bound).all():
            raise ValueError(f'Invalid {col}')
    if not df.state.map(lambda x: pd.isna(x) or isinstance(x, str)).all():
        raise ValueError('state must be nullable text')
    if 'ground_truth' in df and not df.ground_truth.dropna().isin(['Positive', 'Negative', 'Neutral']).all():
        raise ValueError('Invalid ground_truth')
    return df
