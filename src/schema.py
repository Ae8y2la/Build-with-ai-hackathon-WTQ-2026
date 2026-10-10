from typing import TypedDict, List, Optional

ALLOWED_CHARGE_TYPES = {
    "energy", "fixed", "fpa", "quarterly_adjustment",
    "surcharge", "meter_rent", "subsidy", "other"
}

ALLOWED_TAX_TYPES = {
    "gst", "electricity_duty", "income_tax",
    "municipal_tax", "other_tax"
}

class Charge(TypedDict):
    type: str
    amount: float

class Tax(TypedDict):
    type: str
    amount: float

class Level1Bill(TypedDict):
    provider: Optional[str]
    tariff: Optional[str]
    sanctioned_load_kw: Optional[float]
    bill_month: Optional[str]
    reading_date: Optional[str]
    issue_date: Optional[str]
    due_date: Optional[str]
    previous_reading: Optional[float]
    current_reading: Optional[float]
    units_consumed: Optional[float]
    charges: List[Charge]
    total_charges: Optional[float]
    taxes: List[Tax]
    total_taxes: Optional[float]
    current_bill: Optional[float]
    arrears: Optional[float]
    payable_within_due_date: Optional[float]
    payable_after_due_date: Optional[float]
