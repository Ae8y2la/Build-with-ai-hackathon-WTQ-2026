import time
import logging
from typing import Optional

from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt
)
from google import genai
from google.genai import types
from PIL import Image

import src.config as config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize client using the API key from config
client = genai.Client(api_key=config.GEMINI_API_KEY)

# Global tracker for rate limiting
_last_request_time = 0.0

def _respect_rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < config.REQUEST_DELAY_SECONDS:
        sleep_time = config.REQUEST_DELAY_SECONDS - elapsed
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
    _last_request_time = time.time()

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying request after error: {retry_state.outcome.exception()}"
    )
)
def generate_json(prompt: str, image_path: Optional[str] = None) -> str:
    """
    Generate JSON output using Gemini with an optional image input.
    """
    _respect_rate_limit()
    
    contents = []
    if image_path:
        img = Image.open(image_path)
        contents.append(img)
    contents.append(prompt)
    
    logger.info(f"Generating JSON response with {config.GEMINI_MODEL}")
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    return response.text

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
    before_sleep=lambda retry_state: logger.warning(
        f"Retrying request after error: {retry_state.outcome.exception()}"
    )
)
def generate_text(prompt: str, image_path: Optional[str] = None) -> str:
    """
    Generate plain text response using Gemini with an optional image input.
    """
    _respect_rate_limit()
    
    contents = []
    if image_path:
        img = Image.open(image_path)
        contents.append(img)
    contents.append(prompt)
    
    logger.info(f"Generating text response with {config.GEMINI_MODEL}")
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=0.0
        )
    )
    return response.text
