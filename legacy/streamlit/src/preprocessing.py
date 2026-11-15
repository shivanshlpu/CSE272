"""Tone-preserving normalization and bounded-memory duplicate detection."""
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from src import config
from src.schema import validate_schema

HINDI = set('bhai yaar nahi kya hai paisa bekar mast accha bohot karo sarkar loot gaya desh banao hain tha thi the ho hum tum aap main mein mera meri mere tera teri uska uski apna apni ka ki ke ko se par aur ya lekin magar toh to bhi hi na mat kar karke karna karte karta karti hua hui hue hoga hogi hote hota hoti ab aaj kal kab jab tab sab kuch koi kahan kyun kaise kitna kitni bahut bahot acha achha acchi acchhi bura buri naya nayi purana purani bada badi chota choti sahi galat bas bus chalo chalta chalti raha rahi rahe phir fir abhi kabhi hamesha sirf tak bina saath liye diya diye diya lena dena lo do mil mila mili gaya gayi gaye jaldi der zyada kam mehenga mehengi muft band kharab dhanyavad shukriya wah'.split())
GEO = {
 'Maharashtra': (19.75,75.71,['mumbai','pune','maharashtra','मुंबई','महाराष्ट्र']),
 'Karnataka': (15.32,75.71,['bengaluru','bangalore','karnataka','बेंगलुरु']),
 'Delhi': (28.61,77.21,['delhi','दिल्ली']),
 'Punjab': (31.15,75.34,['punjab','पंजाब','amritsar']),
 'Tamil Nadu': (11.13,78.66,['chennai','tamil nadu','चेन्नई']),
 'Uttar Pradesh': (26.85,80.95,['lucknow','uttar pradesh','लखनऊ','उत्तर प्रदेश']),
 'Gujarat': (22.26,71.19,['gujarat','ahmedabad','गुजरात']),
 'West Bengal': (22.99,87.85,['kolkata','west bengal','कोलकाता']),
 'Telangana': (18.11,79.02,['hyderabad','telangana','हैदराबाद']),
 'Rajasthan': (27.02,74.22,['jaipur','rajasthan','जयपुर'])}


def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'https?://\S+|www\.\S+', '', text)).strip()


def tag_language(text: str) -> str:
    if re.search(r'[\u0900-\u097f]', text):
        return 'hi'
    return 'hi-en' if len(set(re.findall(r'[a-z]+', text.lower())) & HINDI) >= 2 else 'en'


def geo_map(text: str) -> tuple:
    for state, (lat, lon, aliases) in GEO.items():
        if any(re.search(r'(?<!\w)'+re.escape(a)+r'(?!\w)', text.lower()) for a in aliases):
            return state, lat, lon
    return None, np.nan, np.nan


def detect_bots(df: pd.DataFrame) -> np.ndarray:
    """Sparse chunks bound memory; count other posts, excluding self."""
    result = np.zeros(len(df), dtype=bool)
    if len(df) < config.BOT_MIN_NEIGHBORS + 1:
        return result
    try:
        matrix = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b').fit_transform(df.clean_text)
    except ValueError:
        return result
    candidates = np.flatnonzero((df.likes <= config.BOT_MAX_LIKES) & (df.author_followers <= config.BOT_MAX_FOLLOWERS))
    for start in range(0, len(candidates), config.BOT_CHUNK_SIZE):
        ids = candidates[start:start+config.BOT_CHUNK_SIZE]
        similarity = (matrix[ids] @ matrix.T).tocsr()
        similarity.data = (similarity.data >= config.BOT_SIMILARITY).astype(float)
        counts = np.asarray(similarity.sum(axis=1)).ravel()-1
        result[ids] = counts >= config.BOT_MIN_NEIGHBORS
    return result


def preprocess(df: pd.DataFrame, bot_filter: bool = True) -> pd.DataFrame:
    validate_schema(df)
    result = df.copy()
    result['clean_text'] = result.text.map(clean_text)
    result['lang'] = result.clean_text.map(tag_language)
    result[['state','lat','lon']] = pd.DataFrame(result.clean_text.map(geo_map).tolist(), index=result.index)
    result['is_bot'] = detect_bots(result) if bot_filter else False
    return validate_schema(result)
