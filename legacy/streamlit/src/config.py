"""Central configuration and analysis thresholds."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
BOT_SIMILARITY = 0.92
BOT_MIN_NEIGHBORS = 5
BOT_MAX_LIKES = 5
BOT_MAX_FOLLOWERS = 50
SHIFT_DROP = 0.20
MAX_WORKERS = 8
SEED = 42
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
BOT_CHUNK_SIZE = 128
PROMPT_VERSION = '2-unicode-tokenization'
