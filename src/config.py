import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "google")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY and MODEL_PROVIDER == "google":
    raise ValueError("GEMINI_API_KEY must be set in .env when using google provider")

GEMINI_MODEL = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")

REQUESTS_PER_MIN = float(os.getenv("REQUESTS_PER_MIN", "15"))
REQUEST_DELAY_SECONDS = 60.0 / REQUESTS_PER_MIN
