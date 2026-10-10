import json
import logging
from src.llm import generate_text

logger = logging.getLogger(__name__)

L2_PROMPT_TEMPLATE = """You are a helpful assistant answering customer questions about their electricity bill.
You have been provided with pre-extracted Level 1 Data, Context Data, and Computed Statistics.
Use ONLY this data and the bill image to answer the questions. Do NOT recompute numbers from memory.

Rules for answering:
1. Label estimates clearly and show the method used.
2. State the interpretation if something is ambiguous.
3. Say clearly when the bill lacks the info (e.g., "The bill lacks this information.") instead of guessing.
4. Write in English only.
5. Include NO personal identifiers (names, addresses, CNIC, account/reference/consumer/meter numbers).
6. Be concise and focus on key figures.
7. Q1 (net-metered?): say standard unless the bill shows net-metering or export lines, and explain what you checked.
8. State whether the current month is included in any history calculation. KE shows 13 months, IESCO/LESCO show 12.
9. Q7: give both total and per-month average for summer (Jun-Aug) and winter (Dec-Feb), using only months shown, and say if any are missing.
10. Q8: compare billed vs paid for each month shown, flag unpaid or partial months, and note that KE's billing history shows only 3 months.
11. Q10, Q11, Q12: label as estimates and show the method using only bill data (for example the average of the last 3 months or the same month last year, the average billed amount, or the current cost per unit).

Level 1 Data:
{l1}

Context Data:
{ctx}

Computed Stats:
{stats}

QUESTIONS:
{questions}

Respond ONLY with a valid JSON object where keys are the question_id (string) and values are the answer (string).
Example format:
{{
    "Q1": "Your answer here...",
    "Q2": "Your answer here..."
}}
"""

L2_RETRY_PROMPT = """You are a helpful assistant answering a single customer question about their electricity bill.
Rules: Use only the bill and provided data. Label estimates. No personal info. English only. If missing, answer exactly: "The bill lacks this information" instead of guessing.
- Q1: say standard unless the bill shows net-metering/export, and explain.
- State whether the current month is included in history calculations (KE: 13 mos, LESCO/IESCO: 12).
- Q7: both total & per-month average for summer (Jun-Aug) & winter (Dec-Feb) using only months shown. Say if missing.
- Q8: compare billed vs paid for each month shown, flag unpaid/partial, note KE history is 3 months.
- Q10, Q11, Q12: label as estimates and show method using only bill data.

Level 1: {l1}
Context: {ctx}
Stats: {stats}

Question ID: {qid}
Question: {qtext}

Return ONLY a valid JSON object:
{{
    "{qid}": "your answer here"
}}
"""

def _extract_json_block(text: str) -> dict:
    """Robustly extract a JSON dictionary from a raw string, ignoring surrounding text/markdown."""
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
            
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    return {}

def answer_l2_questions(image_path: str, l1_json: dict, ctx_json: dict, stats_json: dict, questions: list) -> dict:
    """
    Answers L2 questions using a single prompt (without function calling or JSON mode).
    Retries any missing questions individually.
    questions is expected to be a list of dicts: [{"question_id": "...", "question": "..."}]
    """
    q_strings = []
    for q in questions:
        q_strings.append(f"{q['question_id']}: {q['question']}")
        
    prompt = L2_PROMPT_TEMPLATE.format(
        l1=json.dumps(l1_json, indent=2),
        ctx=json.dumps(ctx_json, indent=2),
        stats=json.dumps(stats_json, indent=2),
        questions="\n".join(q_strings)
    )

    answers = {}
    try:
        # Use generate_text as requested (no JSON mode enforcement via SDK)
        response_text = generate_text(prompt, image_path)
        answers = _extract_json_block(response_text)
    except Exception as e:
        logger.error(f"Failed L2 bulk call: {e}")

    final_answers = {}
    for q in questions:
        qid = q["question_id"]
        if qid in answers and str(answers[qid]).strip():
            final_answers[qid] = str(answers[qid]).strip()
        else:
            logger.warning(f"Missing answer for {qid}, retrying individually...")
            retry_prompt = L2_RETRY_PROMPT.format(
                l1=json.dumps(l1_json),
                ctx=json.dumps(ctx_json),
                stats=json.dumps(stats_json),
                qid=qid,
                qtext=q["question"]
            )
            try:
                retry_resp = generate_text(retry_prompt, image_path)
                retry_ans = _extract_json_block(retry_resp)
                if qid in retry_ans and str(retry_ans[qid]).strip():
                    final_answers[qid] = str(retry_ans[qid]).strip()
                else:
                    final_answers[qid] = "The bill lacks this information or it could not be extracted."
            except Exception as e:
                logger.error(f"Retry failed for {qid}: {e}")
                final_answers[qid] = "The bill lacks this information or it could not be extracted."
                
    return final_answers
