import json
import logging
from src.llm import generate_json

logger = logging.getLogger(__name__)

CTX_PROMPT = """Extract the following contextual information from the electricity bill. 
Return ONLY valid JSON. If a field or piece of information is absent or unprinted, use `null`.

Fields required:
- "usage_history": array of objects {{"month": "YYYY-MM", "units": number}} (up to 13 months)
- "payment_history": array of objects {{"month": "YYYY-MM", "billed": number, "pay_date": "YYYY-MM-DD", "paid_amount": number}}
- "message_board": string (any notification text or messages from the company to the consumer)
- "energy_tax_split": string (the printed percentage split or ratio of energy vs taxes, if available)
- "rate_slab_lines": array of strings (lines showing the slab rates, tariff blocks, or unit pricing breakdown)

Never guess or calculate values. Output exactly what is printed.
"""

def extract_context(image_path: str) -> dict:
    """Extracts supplementary bill context (history, messages, slabs) into a JSON dictionary."""
    fallback = {
        "usage_history": None,
        "payment_history": None,
        "message_board": None,
        "energy_tax_split": None,
        "rate_slab_lines": None
    }
    
    try:
        response_text = generate_json(CTX_PROMPT, image_path).strip()
        
        # Clean markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        
        # Ensure all expected keys are present
        for k in fallback.keys():
            if k not in data:
                data[k] = None
        return data
        
    except Exception as e:
        logger.error(f"Context extraction failed: {e}")
        return fallback
