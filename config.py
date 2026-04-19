import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "llama-3.1-8b-instant"

CHROMA_PATH = "data/chromadb"

# QA thresholds — content re-generates if below these
BRAND_SCORE_THRESHOLD = 0.75
GEO_SCORE_THRESHOLD = 0.75
COMPETITOR_DIFF_THRESHOLD = 0.70

MAX_RETRIES = 3
