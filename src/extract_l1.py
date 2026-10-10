import json
import logging
import tempfile
import os
from PIL import Image, ImageOps, ImageEnhance
from src.llm import generate_json
from src.prompts import LEVEL_1_PROMPT
from src.validate import normalize, check, EXPECTED_FIELDS

logger = logging.getLogger(__name__)

def preprocess_image(image_path: str) -> str:
    """Auto-orient, upscale 2x, and improve contrast of the image, returning a temp file path."""
    try:
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        
        # Upscale 2x
        new_size = (img.width * 2, img.height * 2)
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Increase contrast slightly
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(temp_path, format="PNG")
        return temp_path
    except Exception as e:
        logger.warning(f"Image preprocessing failed: {e}. Using original image.")
        return image_path

def _get_all_null_obj() -> dict:
    """Returns an all-null object with every field present so the pipeline never crashes."""
    obj = {field: None for field in EXPECTED_FIELDS}
    obj["charges"] = []
    obj["taxes"] = []
    return obj

def _parse_llm_json(response_text: str) -> dict:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return json.loads(response_text.strip())

def extract_level_1(image_path: str) -> dict:
    """
    Extract Level 1 JSON fields from a bill image using the LLM.
    If internal math checks fail, it re-prompts the model once with a hint.
    """
    processed_image_path = preprocess_image(image_path)
    
    try:
        # First attempt
        response_text_1 = generate_json(LEVEL_1_PROMPT, processed_image_path)
        data_1 = _parse_llm_json(response_text_1)
        norm_1 = normalize(data_1)
        warnings_1 = check(norm_1)
        
        if not warnings_1:
            if processed_image_path != image_path:
                os.remove(processed_image_path)
            return norm_1
            
        logger.warning(f"Validation warnings on first attempt: {warnings_1}")
        
        # Second attempt with hint
        hint = f"\n\nYOUR PREVIOUS EXTRACTION GENERATED THESE WARNINGS:\n"
        hint += "\n".join(warnings_1)
        hint += "\n\nOn a blurry digit, re-read that field zoomed in. total_taxes is the printed Taxes amount, and a printed percentage helps double-check it. Please re-read the digits for the fields with warnings, do not recalculate, and never overwrite a printed value with a computed one. Only extract exactly what is printed."
        
        prompt_2 = LEVEL_1_PROMPT + hint
        
        try:
            response_text_2 = generate_json(prompt_2, processed_image_path)
            data_2 = _parse_llm_json(response_text_2)
            norm_2 = normalize(data_2)
            warnings_2 = check(norm_2)
            
            if warnings_2:
                logger.warning(f"Final validation warnings after retry: {warnings_2}")
            
            if len(warnings_2) < len(warnings_1):
                logger.info("Second attempt improved the result.")
                if processed_image_path != image_path:
                    os.remove(processed_image_path)
                return norm_2
            else:
                logger.info("Second attempt did not improve the result. Returning first attempt.")
                if processed_image_path != image_path:
                    os.remove(processed_image_path)
                return norm_1
                
        except Exception as e:
            logger.error(f"Second attempt failed entirely: {e}. Returning first attempt.")
            if processed_image_path != image_path:
                os.remove(processed_image_path)
            return norm_1

    except Exception as e:
        logger.error(f"First attempt failed entirely: {e}. Returning all-null fallback.")
        if processed_image_path != image_path:
            os.remove(processed_image_path)
        return _get_all_null_obj()
