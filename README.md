# Utility Bill Decoder

## Overview
This project tackles the **Utility Bill Decoder** challenge. It is designed to accurately extract and analyze data from physical electricity bills (K-Electric, LESCO, and IESCO). 
The solution is divided into two primary stages:
1. **Level 1 Extraction:** Parsing structured tabular data directly from the bill images into a robust JSON schema (e.g., provider, meter readings, exact charges, taxes, and totals).
2. **Level 2 Q&A:** Synthesizing extracted data and deeper context to answer specific user questions regarding historical usage, net-metering status, and estimated historical averages.

## Architecture
### `src/` Modules
*   **`config.py`**: Loads environment variables and manages rate-limiting rules.
*   **`llm.py`**: Wraps the `google-genai` SDK, offering unified synchronous retry logic (via `tenacity`) for text and JSON generation.
*   **`prompts.py`**: Central repository for all system prompts and extraction rules, enforcing strict compliance for edge cases.
*   **`schema.py`**: Defines standard schemas and allowed taxonomy for charge and tax types.
*   **`extract_l1.py`**: Handles Level 1 image preprocessing and extraction, incorporating the self-correcting validation loop.
*   **`validate.py`**: Performs deterministic mathematical checks to ensure totals perfectly sum up without hallucination.
*   **`extract_ctx.py`**: Extracts expanded unstructured context from the bill (e.g., billing history tables, net-metering flags).
*   **`stats.py`**: Computes deterministic statistics natively in Python (such as summer/winter averages) based on the extracted context.
*   **`answer_l2.py`**: Synthesizes L1 JSON, Context, and Stats to answer dynamically provided questions cleanly.
*   **`csv_io.py`**: Handles strict reading and writing of `utf-8-sig` CSV templates.
*   **`pipeline.py`**: Orchestrates the per-bill execution of L1, context, stats, and L2, providing cache management and fault isolation.
*   **`run.py`**: The CLI entry point for executing the batch pipeline against directories.

### `scripts/`
*   **`check_submission.py`**: Evaluates the output CSVs against the expected template length and enforces strict schema, data type, and completeness criteria.
*   **`package_zip.py`**: Bundles the repository into a submission-compliant ZIP file under 15 MB, explicitly excluding secrets and cache directories.

### `app.py`
A minimal, human-friendly Streamlit web application acting as a dashboard for interacting with single bills or running the batch pipeline.

### Pipeline Text Diagram
```text
[Bill Image] 
   │
   ├─> (extract_l1.py) ──> LLM (JSON) ──> (validate.py) ─[Fail]─> Preprocess/Retry 
   │                                           │
   │                                        [Pass]
   │                                           │
   ├─> (extract_ctx.py) ──> LLM (Text)         ├──> Level 1 JSON 
   │                           │               │
   │                           v               │
   └─> (stats.py) ───────> Python Math         │
                               │               │
                               v               v
           [Level 2 Questions] + [L1, Ctx, Stats] ──> (answer_l2.py) ──> Level 2 JSON
```

## How It Works
1. **Vision LLM Reads the Bill**: The system passes the image and a strictly typed JSON schema to Gemini.
2. **Validation Checks**: Python parses the LLM output and validates printed subtotals against the sum of line items. If a mismatch of >1 occurs, it triggers a retry.
3. **Validation Re-read**: On retry, the image undergoes light preprocessing (upscaling 2x, contrast enhancement) and the model is explicitly told what to double-check without recalculating figures.
4. **Extended Context & Stats**: A separate call extracts unformatted context (e.g., historical billing), and native Python calculates statistics, protecting against LLM math hallucinations.
5. **One Level 2 Call Per Bill**: All questions from the CSV for a single bill are bundled into a single LLM prompt, reducing latency and cost.
6. **CSV Writer**: Extracted JSONs and L2 answers are securely mapped back to their original IDs and written to `level1.csv` and `level2.csv`.

## Setup
**Python Version**: Tested on `Python 3.13.2`.

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**:
   Copy the example file and add your actual API key:
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` to include your valid `GEMINI_API_KEY`)*

## Run
**Batch Run**:
```bash
python -m src.run --bills test/bills --csv test/csv --out output
```

**Validate Submission**:
```bash
python scripts/check_submission.py
```

**Package ZIP**:
```bash
python scripts/package_zip.py
```

**Streamlit Dashboard**:
```bash
streamlit run app.py
```

## Configuration
The following variables are available (and documented in `.env.example`):
*   `MODEL_PROVIDER`: Defines the provider (e.g., `google`).
*   `MODEL_NAME`: The specific model tier to use (e.g., `gemini-3.5-flash-lite`).
*   `REQUESTS_PER_MIN`: Integer regulating the local rate limiter (e.g., `15`).
*   `GEMINI_API_KEY`: Your authentication key for Google GenAI.

## Design Decisions
*   **Validation Re-read**: To solve OCR limitations on blurry images, the system relies strictly on printed totals and forces a focused re-read (with image enhancements) if math checks fail, preventing hallucinated additions.
*   **Nothing Hardcoded Per Bill**: All extraction guidelines in `src/prompts.py` are strictly general-purpose and layout-based.
*   **Questions from CSV**: L2 questions are read dynamically from the provided templates.
*   **Caching**: Bill extractions are written to `.cache/` to make local iterations and recoveries instantaneous.
*   **Retries and Rate Limiting**: Exponential backoff (`tenacity`) and a token bucket rate limiter strictly enforce API limits without crashing the batch.
*   **Fallbacks**: A safe all-null dictionary fallback guarantees that no cell is ever completely missing from the CSV, preserving structural integrity for the auto-grader.

## Limitations
*   **Blurry Photos**: Low-megapixel images or heavy glare can still disrupt reading, though upscaling and contrast preprocessing mitigates this significantly.
*   **Multi-register Meters**: While rules exist to sum Peak and Off-Peak, highly complex anomalous layouts might occasionally require fallback reasoning.
*   **Estimates Labelled**: The LLM might occasionally struggle to natively format explanations for estimates perfectly identically across all bill types, relying on the prompt to append warnings like "The bill lacks this information".

## AI Usage
*   **Models/APIs**: Only `google-genai` SDK is invoked (calling Gemini models as defined in `.env`).
*   **Services**: None. No external OCR APIs, Textract, or document parsing services are utilized.
*   **AI tools used to write the code**: 
    *   Antigravity with Gemini 3.1 Pro Low
    *   Claude chat for planning
