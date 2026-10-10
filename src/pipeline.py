import os
import json
import logging
from src.extract_l1 import extract_level_1, _get_all_null_obj
from src.extract_ctx import extract_context
from src.stats import compute_stats
from src.answer_l2 import answer_l2_questions

logger = logging.getLogger(__name__)

CACHE_DIR = ".cache"

def run_pipeline(bill_id: str, image_path: str, questions: list) -> tuple:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{bill_id}.json")
    
    if os.path.exists(cache_file):
        logger.info(f"[{bill_id}] Using cached results.")
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("level1", _get_all_null_obj()), data.get("level2", {})
        except Exception as e:
            logger.warning(f"[{bill_id}] Cache read failed, recalculating: {e}")

    logger.info(f"[{bill_id}] Running full extraction pipeline...")
    level1 = _get_all_null_obj()
    level2 = {}
    
    try:
        # Step 1: Level 1 extraction and internal validation
        level1 = extract_level_1(image_path)
        
        # Step 2: Context Extraction
        try:
            ctx = extract_context(image_path)
        except Exception as e:
            logger.error(f"[{bill_id}] Context extraction failed: {e}")
            ctx = {}
            
        # Step 3: Compute Stats
        try:
            stats = compute_stats(level1, ctx)
        except Exception as e:
            logger.error(f"[{bill_id}] Stats computation failed: {e}")
            stats = {}
            
        # Step 4: Level 2 Answers
        if questions:
            try:
                level2 = answer_l2_questions(image_path, level1, ctx, stats, questions)
            except Exception as e:
                logger.error(f"[{bill_id}] L2 answering failed entirely: {e}")
                level2 = {q["question_id"]: "Failed to process question." for q in questions}

        # Cache results safely
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({"level1": level1, "level2": level2}, f, separators=(',', ':'))

    except Exception as e:
        logger.error(f"[{bill_id}] Pipeline experienced a total crash: {e}")
        level2 = {q["question_id"]: "Pipeline failed." for q in questions}
        
    return level1, level2
