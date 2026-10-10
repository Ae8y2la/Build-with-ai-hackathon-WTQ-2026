import re
from src.schema import ALLOWED_CHARGE_TYPES, ALLOWED_TAX_TYPES

EXPECTED_FIELDS = [
    "provider", "tariff", "sanctioned_load_kw", "bill_month", "reading_date",
    "issue_date", "due_date", "previous_reading", "current_reading",
    "units_consumed", "charges", "total_charges", "taxes", "total_taxes",
    "current_bill", "arrears", "payable_within_due_date", "payable_after_due_date"
]

def normalize(bill_json: dict) -> dict:
    """Normalize extracted json to ensure safe types, proper dates, and remove bad fields."""
    cleaned = {}
    
    # 1. Ensure all fields exist and remove any unexpected identifier-like fields
    for key in EXPECTED_FIELDS:
        cleaned[key] = bill_json.get(key, None)
        
    # 2. Ensure numbers are numeric (float)
    number_fields = [
        "sanctioned_load_kw", "previous_reading", "current_reading",
        "units_consumed", "total_charges", "total_taxes", "current_bill",
        "arrears", "payable_within_due_date", "payable_after_due_date"
    ]
    for key in number_fields:
        val = cleaned.get(key)
        if val is not None:
            try:
                if isinstance(val, str):
                    val = val.replace(",", "")
                cleaned[key] = float(val)
            except (ValueError, TypeError):
                cleaned[key] = None
                
    # 3. Ensure date formats match YYYY-MM and YYYY-MM-DD
    if cleaned.get("bill_month"):
        if not re.match(r"^\d{4}-\d{2}$", str(cleaned["bill_month"])):
            cleaned["bill_month"] = None
            
    date_fields = ["reading_date", "issue_date", "due_date"]
    for key in date_fields:
        if cleaned.get(key):
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(cleaned[key])):
                cleaned[key] = None

    # 4. Normalize charges types and amounts
    charges = cleaned.get("charges")
    if isinstance(charges, list):
        valid_charges = []
        for c in charges:
            if not isinstance(c, dict): continue
            
            t = str(c.get("type", "other")).lower().strip()
            if t not in ALLOWED_CHARGE_TYPES:
                t = "other"
                
            amt = c.get("amount")
            if amt is not None:
                try:
                    if isinstance(amt, str):
                        amt = amt.replace(",", "")
                    amt = float(amt)
                    valid_charges.append({"type": t, "amount": amt})
                except (ValueError, TypeError):
                    pass
        cleaned["charges"] = valid_charges
    else:
        cleaned["charges"] = []

    # 5. Normalize taxes types and amounts
    taxes = cleaned.get("taxes")
    if isinstance(taxes, list):
        valid_taxes = []
        for t in taxes:
            if not isinstance(t, dict): continue
            
            ctype = str(t.get("type", "other_tax")).lower().strip()
            if ctype not in ALLOWED_TAX_TYPES:
                ctype = "other_tax"
                
            amt = t.get("amount")
            if amt is not None:
                try:
                    if isinstance(amt, str):
                        amt = amt.replace(",", "")
                    amt = float(amt)
                    valid_taxes.append({"type": ctype, "amount": amt})
                except (ValueError, TypeError):
                    pass
        cleaned["taxes"] = valid_taxes
    else:
        cleaned["taxes"] = []

    return cleaned


def check(bill_json: dict) -> list[str]:
    """Flag internal inconsistencies in printed values (> 1 unit delta). Never mutate."""
    errors = []
    
    # sum(charges) vs total_charges
    charges = bill_json.get("charges") or []
    sum_charges = sum(c.get("amount", 0.0) for c in charges)
    total_charges = bill_json.get("total_charges")
    
    if total_charges is not None:
        if abs(sum_charges - total_charges) > 1.0:
            errors.append(f"sum(charges) ({sum_charges}) differs from total_charges ({total_charges}) by > 1")
            
    # sum(taxes) vs total_taxes
    taxes = bill_json.get("taxes") or []
    sum_taxes = sum(t.get("amount", 0.0) for t in taxes)
    total_taxes = bill_json.get("total_taxes")
    
    if total_taxes is not None:
        if abs(sum_taxes - total_taxes) > 1.0:
            errors.append(f"sum(taxes) ({sum_taxes}) differs from total_taxes ({total_taxes}) by > 1")
            
    # current_bill vs total_charges + total_taxes
    current_bill = bill_json.get("current_bill")
    if current_bill is not None and total_charges is not None and total_taxes is not None:
        calc_bill = total_charges + total_taxes
        if abs(current_bill - calc_bill) > 1.0:
            errors.append(f"current_bill ({current_bill}) differs from total_charges + total_taxes ({calc_bill}) by > 1")
            
    return errors
