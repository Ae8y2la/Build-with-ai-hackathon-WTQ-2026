import os
import csv
import json
import re
import sys

def check_submission():
    errors = []
    
    l1_path = os.path.join("output", "level1.csv")
    l2_path = os.path.join("output", "level2.csv")
    
    EXPECTED_FIELDS = {
        "provider": str, "tariff": str, "sanctioned_load_kw": float, "bill_month": str,
        "reading_date": str, "issue_date": str, "due_date": str, "previous_reading": float,
        "current_reading": float, "units_consumed": float, "charges": list, "total_charges": float,
        "taxes": list, "total_taxes": float, "current_bill": float, "arrears": float,
        "payable_within_due_date": float, "payable_after_due_date": float
    }

    if not os.path.exists(l1_path):
        errors.append(f"Missing {l1_path}")
    else:
        with open(l1_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            if len(reader) - 1 != 10:
                errors.append(f"level1.csv has {len(reader)-1} rows, expected 10.")
            for i, row in enumerate(reader[1:], 2):
                if len(row) < 2 or not row[1].strip():
                    errors.append(f"level1.csv Row {i}: Empty json cell.")
                    continue
                try:
                    data = json.loads(row[1])
                    for field, ftype in EXPECTED_FIELDS.items():
                        if field not in data:
                            errors.append(f"level1.csv Row {i}: Missing field '{field}'.")
                        else:
                            val = data[field]
                            if val is not None and ftype == float and not isinstance(val, (int, float)):
                                errors.append(f"level1.csv Row {i}: Field '{field}' expected numeric type, got {type(val)}.")
                except json.JSONDecodeError:
                    errors.append(f"level1.csv Row {i}: Invalid JSON.")

    if not os.path.exists(l2_path):
        errors.append(f"Missing {l2_path}")
    else:
        with open(l2_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            if len(reader) - 1 != 120:
                errors.append(f"level2.csv has {len(reader)-1} rows, expected 120.")
            for i, row in enumerate(reader[1:], 2):
                if len(row) < 4 or not row[3].strip():
                    errors.append(f"level2.csv Row {i}: Empty answer cell.")

    # Template matching check (if templates are available)
    template_dir = "test/csv" if os.path.exists(os.path.join("test/csv", "level1.csv")) else "template"
    if os.path.exists(os.path.join(template_dir, "level1.csv")):
        with open(os.path.join(template_dir, "level1.csv"), 'r', encoding='utf-8-sig') as f1:
            template_ids = [r[0] for r in list(csv.reader(f1))[1:]]
        with open(l1_path, 'r', encoding='utf-8') as f2:
            out_ids = [r[0] for r in list(csv.reader(f2))[1:]]
        if out_ids != template_ids:
            errors.append("level1.csv bill_ids do not match the template.")

    if os.path.exists(os.path.join(template_dir, "level2.csv")):
        with open(os.path.join(template_dir, "level2.csv"), 'r', encoding='utf-8-sig') as f1:
            t_rows = [[r[0], r[1], r[2]] for r in list(csv.reader(f1))[1:]]
        with open(l2_path, 'r', encoding='utf-8') as f2:
            o_rows = [[r[0], r[1], r[2]] for r in list(csv.reader(f2))[1:]]
        if t_rows != o_rows:
            errors.append("level2.csv bill_id, question_id, or questions do not match the template exactly.")

    # Check for secrets/keys
    api_key_regex = re.compile(r"AIzaSy[A-Za-z0-9_-]{33}")
    for root, dirs, files in os.walk("."):
        if ".env" in files and (root == ".\src" or root == "./src" or root == "src"): 
            errors.append(f".env file incorrectly placed inside {root}")
            
        for file in files:
            if file.endswith(".py"):
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if api_key_regex.search(content):
                            errors.append(f"API Key pattern found hardcoded in {fpath}")
                except Exception:
                    pass

    if errors:
        print("Submission check failed:")
        for e in errors:
            print(f" - {e}")
        sys.exit(1)
    else:
        print("Submission check passed! All criteria met.")
        sys.exit(0)

if __name__ == "__main__":
    check_submission()
