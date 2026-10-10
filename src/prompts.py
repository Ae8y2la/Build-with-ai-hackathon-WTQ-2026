import os

_EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "expected", "KESC_0008.json")
try:
    with open(_EXAMPLE_PATH, "r") as f:
        _EXAMPLE_JSON = f.read().strip()
except FileNotFoundError:
    _EXAMPLE_JSON = "{}"

LEVEL_1_PROMPT = f"""You are an expert data extractor. Extract the following information from the provided electricity bill image.
Return ONLY valid JSON, with numbers not strings. All fields must be present. If a field is missing, unreadable, covered, or unprinted, set it to `null`. Do not guess.

# Output Schema & Field Meanings
provider: string (KE | LESCO | IESCO). Note: KESC files = KE.
tariff: string (exact string)
sanctioned_load_kw: number (labelled "Sanc Load", "S.Load", or "San Load")
bill_month: string (YYYY-MM)
reading_date: string (YYYY-MM-DD, convert any printed date format to ISO, checking day-first vs month-first)
issue_date: string (YYYY-MM-DD, convert any printed date format to ISO)
due_date: string (YYYY-MM-DD, convert any printed date format to ISO). This is the last date to pay without late surcharge.
previous_reading: number
current_reading: number
units_consumed: number (billed units as printed)
charges: array of objects {{type: string, amount: number}}
total_charges: number (null if no subtotal is printed)
taxes: array of objects {{type: string, amount: number}}
total_taxes: number (null if no subtotal is printed)
current_bill: number (the printed amount for this month's bill)
arrears: number (keeps printed sign)
payable_within_due_date: number
payable_after_due_date: number (highest late amount)

# Allowed Types
Charge types: energy, fixed, fpa (includes FPA and FCA), quarterly_adjustment, surcharge, meter_rent, subsidy (negative), other
Tax types: gst (incl. GST on FPA), electricity_duty, income_tax, municipal_tax, other_tax

# Extraction Rules
- Copy every amount exactly as printed. Never adjust a value to make totals add up; some bills' printed totals do not add up.
- current_bill is the amount printed next to "Current Bill", never Grand Total or Payable.
- Read sanctioned load from the Sanc Load / S. Load / San Load label only.
- Previous reading is smaller than present reading. Never swap them. previous_reading is under "Previous", present/current under "Present".
- Meters with separate Off Peak and Peak rows: sum the registers for previous_reading and current_reading.
- Skip any charge line printed as 0. Do not add zero entries.
- "ED on FPA" is electricity_duty; "GST on FPA" is gst; "Income Tax on FPA" is income_tax only if it has an amount.
- On a blurry digit, re-read that field zoomed in. total_taxes is the printed Taxes amount, and a printed percentage helps double-check it. Where printed percentages exist (for example Net Electricity Charges % and Taxes %), use them to double-check hard-to-read digits.
- Use printed values only. Ignore handwriting, stamps and annotations on photos.
- Newer IESCO/LESCO layout (summary lines): charges = [energy = Total Electricity Charges, subsidy = negative of Subsidies (omit if 0)], total_charges = Net Electricity Charges, taxes = [], total_taxes = the printed Taxes amount, current_bill = Current Bill. Total FPA is already inside the charges, so do not add it as a separate line.
- Older LESCO layout and KE: follow the printed sections. Keep repeated lines (for example two Uniform Quarterly Adjustment lines) with their printed signs. FCA/FPA lines are type fpa. Additional Surcharge (PHL) is surcharge. MUCT (KMC) is municipal_tax.
- arrears: keep the printed sign (previous dues of -0.41 stays -0.41); null if blank. payable_after_due_date is the highest late amount printed.
- Credits ("CR") are negative.
- Same type may repeat.
- Classify lines by printed section not name.
- If only a combined tax is printed use taxes=[] and total_taxes=that amount.
- null if unreadable/covered/unprinted, never guess.
- NO personal identifiers: names, addresses, CNIC, account/reference/consumer/meter numbers.

# FORMAT EXAMPLE ONLY
The following is an example of the EXPECTED JSON FORMAT ONLY. This is from a completely different bill. YOU MUST NEVER COPY THESE VALUES. Extract the true values from the provided image.

{_EXAMPLE_JSON}
"""
