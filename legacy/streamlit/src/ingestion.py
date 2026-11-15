"""Reproducible multilingual benchmark input; live connectors are pending."""
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.schema import validate_schema

# Labels belong to the generator and must never be consumed by inference.
CASES = [
 ('en', 'Positive', 'payments', 'UPI payments are fast and reliable today!'),
 ('hi', 'Positive', 'payments', 'आज यूपीआई भुगतान बहुत अच्छा चल रहा है!'),
 ('hi-en', 'Positive', 'payments', 'Bhai aaj UPI mast hai, payment turant ho gaya!'),
 ('en', 'Negative', 'payments', 'Wonderful, another failed UPI payment and money stuck again 🙄'),
 ('hi', 'Negative', 'payments', 'वाह, यूपीआई फिर बंद है और पैसे फंस गए 🙄'),
 ('hi-en', 'Negative', 'payments', 'Wah bhai UPI phir band hai, paisa atak gaya 🙄'),
 ('en', 'Neutral', 'transport', 'The city published the revised bus timetable today.'),
 ('hi', 'Neutral', 'transport', 'शहर में बसों की नई समय सारणी जारी हुई।'),
 ('hi-en', 'Neutral', 'transport', 'Bhai bus ka naya timetable aaj aaya hai.'),
 ('en', 'Positive', 'transport', 'The new electric buses make my commute comfortable.'),
 ('hi', 'Positive', 'transport', 'नई इलेक्ट्रिक बसों से सफर आरामदायक हो गया है।'),
 ('hi-en', 'Positive', 'transport', 'Nayi electric bus acchi hai, safar mast ho gaya.'),
 ('en', 'Negative', 'policy', 'The sudden subsidy cut makes this policy unaffordable.'),
 ('hi', 'Negative', 'policy', 'सब्सिडी में कटौती से यह योजना बहुत महंगी हो गई है।'),
 ('hi-en', 'Negative', 'policy', 'Yaar subsidy kam hai, yeh policy bahut mehengi hai.'),
]


def generate_synthetic_benchmark(n_samples: int = 300, seed: int = 42,
                                 reference_time: datetime | None = None) -> pd.DataFrame:
    """Generate n organic records plus exactly 35 bots, with evaluation-only truth.

    Fixed default reference time guarantees deterministic output. Repeated templates
    are not an independent sentiment benchmark; engagement is entirely synthetic.
    """
    if n_samples < 1:
        raise ValueError('n_samples must be positive')
    rng = np.random.default_rng(seed)
    end = reference_time or datetime(2026, 1, 8)
    rows = []
    for i in range(n_samples + 35):
        bot = i >= n_samples
        age = int(rng.integers(0, 7 * 86400))
        cases = CASES if age > 86400 else [c for c in CASES if c[1] == 'Negative']
        lang, truth, theme, text = cases[int(rng.integers(len(cases)))]
        if bot:
            lang, truth, theme, text = 'en', 'Positive', 'campaign', 'Amazing policy perfect service everyone supports this campaign!'
            age = 1800 + i - n_samples
        rows.append(dict(post_id=f'BOT_{i}' if bot else f'SYN_{i}',
                         timestamp=(end - timedelta(seconds=age)).strftime('%Y-%m-%d %H:%M:%S'),
                         author=f'@citizen_{i}', text=text, lang=lang,
                         likes=int(rng.integers(0, 6)) if bot else int(rng.lognormal(3, 1.2)) + 6,
                         replies=int(rng.lognormal(1, 1)),
                         author_followers=int(rng.integers(1, 51)) if bot else int(rng.lognormal(6, 1.5)) + 51,
                         state=None, lat=np.nan, lon=np.nan, source='Synthetic',
                         ground_truth=truth, true_is_bot=bot, true_theme=theme))
    return validate_schema(pd.DataFrame(rows))


def _record(pid, text, source, author='unknown', timestamp=None, likes=0, replies=0):
    return dict(post_id=str(pid), timestamp=(timestamp or datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S'), author=str(author), text=str(text), lang='en', likes=max(0, int(likes)), replies=max(0, int(replies)), author_followers=1, state=None, lat=np.nan, lon=np.nan, source=source)


def _frame(rows):
    from src.schema import COLUMNS
    df = pd.DataFrame(rows, columns=COLUMNS).drop_duplicates('post_id')
    for c in ['likes', 'replies', 'author_followers']:
        df[c] = df[c].astype('int64')
    return validate_schema(df)


def fetch_live_reddit_posts(keyword: str, limit: int = 100) -> pd.DataFrame:
    """Fetch public submissions and top-level comments; errors handled by orchestrator."""
    import os
    import praw
    if not os.getenv('REDDIT_CLIENT_ID'):
        raise RuntimeError('Reddit credentials missing')
    api = praw.Reddit(client_id=os.environ['REDDIT_CLIENT_ID'], client_secret=os.environ['REDDIT_CLIENT_SECRET'], user_agent=os.getenv('REDDIT_USER_AGENT', 'sentiment-research/1.0'), requestor_kwargs={'timeout': 15})
    rows = []
    for post in api.subreddit('india+indiatech+IndianStreetBets+technology+all').search(keyword, limit=limit):
        rows.append(_record('RD_POST_'+post.id, post.title+' '+post.selftext, 'Reddit', str(post.author), datetime.utcfromtimestamp(post.created_utc), post.score, post.num_comments))
        post.comments.replace_more(limit=0)
        for comment in list(post.comments)[:3]:
            rows.append(_record('RD_COMMENT_'+comment.id, comment.body, 'Reddit', str(comment.author), datetime.utcfromtimestamp(comment.created_utc), comment.score))
        if len(rows) >= limit:
            break
    return _frame(rows[:limit])


def fetch_live_youtube_comments(keyword: str, limit: int = 100) -> pd.DataFrame:
    """Fetch comments on relevant public videos using YouTube API v3."""
    import os
    import httplib2
    from googleapiclient.discovery import build
    if not os.getenv('YOUTUBE_API_KEY'):
        raise RuntimeError('YouTube credentials missing')
    api = build('youtube', 'v3', developerKey=os.environ['YOUTUBE_API_KEY'], http=httplib2.Http(timeout=15), cache_discovery=False)
    videos = api.search().list(q=keyword, part='id', type='video', maxResults=5).execute()
    rows = []
    for video in videos.get('items', []):
        result = api.commentThreads().list(videoId=video['id']['videoId'], part='snippet', maxResults=min(100, max(1, limit))).execute()
        for item in result.get('items', []):
            s = item['snippet']['topLevelComment']['snippet']
            rows.append(_record('YT_'+item['id'], s['textDisplay'], 'YouTube', s['authorDisplayName'], datetime.fromisoformat(s['publishedAt'].replace('Z', '+00:00')).replace(tzinfo=None), s['likeCount'], item['snippet']['totalReplyCount']))
    return _frame(rows[:limit])


def fetch_google_news_rss(keyword: str, limit: int = 100) -> pd.DataFrame:
    """RSS has no engagement: zero likes/replies and unknown reach proxy one."""
    import requests
    import feedparser
    import hashlib
    response = requests.get('https://news.google.com/rss/search', params={'q': keyword, 'hl': 'en-IN', 'gl': 'IN', 'ceid': 'IN:en'}, timeout=15)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    rows = []
    for entry in feed.entries[:limit]:
        ts = datetime(*entry.published_parsed[:6]) if entry.get('published_parsed') else datetime.utcnow()
        rows.append(_record('RSS_'+hashlib.sha256(entry.link.encode()).hexdigest()[:20], entry.title, 'Google News RSS', timestamp=ts))
    return _frame(rows)


def fetch_unified_stream(keyword: str, limit: int = 100, seed: int = 42) -> pd.DataFrame:
    """Merge sources with explicit per-source status and deterministic fallback."""
    from tenacity import Retrying, stop_after_attempt, wait_exponential
    frames, messages = [], []
    for name, fn in [('Reddit', fetch_live_reddit_posts), ('YouTube', fetch_live_youtube_comments), ('RSS', fetch_google_news_rss)]:
        try:
            for attempt in Retrying(stop=stop_after_attempt(2), wait=wait_exponential(max=2), reraise=True):
                with attempt:
                    frame = fn(keyword, limit)
            if frame.empty:
                raise RuntimeError('Empty response')
            messages.append(f'{name}: live ({len(frame)} records)')
        except Exception as exc:
            frame = generate_synthetic_benchmark(max(1, limit // 3), seed).drop(columns=['true_is_bot', 'true_theme', 'ground_truth'])
            frame.post_id = name+'_'+frame.post_id
            messages.append(f'{name}: synthetic fallback ({type(exc).__name__})')
        frames.append(frame)
    result = validate_schema(pd.concat(frames, ignore_index=True))
    result.attrs['messages'] = messages
    return result
