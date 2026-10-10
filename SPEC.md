# Electricity Bill Extractor Specification

## Task
Read electricity bill images (K-Electric, LESCO, IESCO; may be tilted, partly Urdu, with grey boxes over identifiers) from the 	rain folder and output Level 1 JSON and Level 2 answers.

## Level 1 JSON
- All fields must be present. If missing, set to 
ull.
- **Fields:**
  - provider: KE | LESCO | IESCO (Note: KESC files = KE).
  - 	ariff: Exact string.
  - sanctioned_load_kw: Number.
  - ill_month: YYYY-MM.
  - eading_date: YYYY-MM-DD.
  - issue_date: YYYY-MM-DD.
  - due_date: YYYY-MM-DD.
  - previous_reading: Number.
  - current_reading: Number.
  - units_consumed: Number.
  - charges: Array of objects {type: string, amount: number}.
  - 	otal_charges: Number.
  - 	axes: Array of objects {type: string, amount: number}.
  - 	otal_taxes: Number.
  - current_bill: Number.
  - rrears: Number (keeps printed sign).
  - payable_within_due_date: Number.
  - payable_after_due_date: Number (highest late amount).

### Charge Types
energy, ixed, pa (FPA and FCA), quarterly_adjustment, surcharge, meter_rent, subsidy (negative), other.

### Tax Types
gst (incl. GST on FPA), electricity_duty, income_tax, municipal_tax, other_tax.

### Extraction Rules
- Values as printed, never recalculate/round/correct.
- Numbers not strings, no commas.
- Credits ("CR") are negative.
- Skip zero/blank charge lines.
- Same type may repeat.
- Classify lines by printed section not name.
- If only a combined tax is printed use 	axes=[] and 	otal_taxes = that amount.
- payable_after_due_date = highest late amount.
- 
ull if unreadable/covered/unprinted, never guess.
- **NO personal identifiers**: names, addresses, CNIC, account/reference/consumer/meter numbers.

## Level 2 Answers
- Answer customer questions in English using only the bill.
- Use code for any math.
- Label estimates and explain how calculated.
- State the interpretation used if ambiguous.
- Say clearly when the bill lacks the info.
- **NO personal identifiers**.

## CSV Output
- Keep column names, row order, ill_id/question_id/question unchanged.
- UTF-8 encoding.
- Use the csv module.
- Level 1 JSON on one line per row.
- No empty cells.
- level1.csv: ill_id,json (10 rows).
- level2.csv: ill_id,question_id,question,answer (120 rows, Q1-Q12 per bill).

## Technology Constraints
- **Only allowed runtime LLMs**: claude-haiku-4-5, gemini-3.5-flash-lite, gemini-3.1-flash-lite, gpt-4.1-mini, gpt-5-mini.
- **No invoice/receipt extractors** (e.g., Azure prebuilt-invoice, Textract AnalyzeExpense, Mindee).
- **Never hardcode API keys**.

### Field Meanings & Additional Rules
- `sanctioned_load_kw`: Labelled "Sanc Load", "S.Load", or "San Load".
- `due_date`: The last date to pay without late surcharge.
- `current_bill`: The printed amount for this month's bill.
- `units_consumed`: The billed units as printed.
- `total_charges` / `total_taxes`: Set to `null` if no subtotal is printed.
- Date conversion: Convert any printed date format to ISO YYYY-MM-DD (check day-first vs month-first on the training bills).

## Additional Hard Rules
- Read questions only from the CSV template.
- No per-bill special cases and no stored answers.
- No LLM, SDK, or OCR service outside the allowed list (use only `google-genai`).
- Every env var the code reads must be listed in `.env.example`.
