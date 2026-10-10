import os
import json
import logging
from src.extract_l1 import extract_level_1
from src.validate import check

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def compare_fields(actual, expected, path=""):
    mismatches = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            mismatches.append(f"{path}: expected dict, got {type(actual)}")
            return mismatches
        for k, v in expected.items():
            mismatches.extend(compare_fields(actual.get(k), v, path=f"{path}.{k}" if path else k))
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            mismatches.append(f"{path}: expected list, got {type(actual)}")
        elif len(actual) != len(expected):
            mismatches.append(f"{path}: expected length {len(expected)}, got {len(actual)}")
        else:
            # Sort arrays of dicts for safe comparison (assuming charge/tax schema)
            try:
                sorted_act = sorted(actual, key=lambda x: (str(x.get('type', '')), float(x.get('amount', 0) or 0)))
                sorted_exp = sorted(expected, key=lambda x: (str(x.get('type', '')), float(x.get('amount', 0) or 0)))
                for i, (a, e) in enumerate(zip(sorted_act, sorted_exp)):
                    mismatches.extend(compare_fields(a, e, path=f"{path}[{i}]"))
            except Exception:
                # If sorting fails, just zip them as is
                for i, (a, e) in enumerate(zip(actual, expected)):
                    mismatches.extend(compare_fields(a, e, path=f"{path}[{i}]"))
    elif isinstance(expected, (int, float)) and expected is not True and expected is not False:
        if not isinstance(actual, (int, float)) or actual is True or actual is False:
            mismatches.append(f"{path}: expected number {expected}, got {actual}")
        elif abs(actual - expected) > 1.0:
            mismatches.append(f"{path}: expected {expected}, got {actual} (diff > 1.0)")
    else:
        if actual != expected:
            mismatches.append(f"{path}: expected '{expected}', got '{actual}'")
            
    return mismatches

def main():
    bills_dir = os.path.join("train-20261010T061909Z-1-001", "train", "bills")
    expected_path = os.path.join("tests", "expected", "KESC_0008.json")
    
    with open(expected_path, "r", encoding="utf-8") as f:
        expected_k8 = json.load(f)

    test_bills = ["IESCO_0004.jpg", "KESC_0004.png", "KESC_0008.png", "LESCO_0005.png", "LESCO_0006.png"]
    
    for filename in test_bills:
        print("\n" + "="*50)
        print(f"EVALUATING: {filename}")
        print("="*50)
        
        img_path = os.path.join(bills_dir, filename)
        if not os.path.exists(img_path):
            print(f"Skipped {filename}: File not found.")
            continue
            
        actual_json = extract_level_1(img_path)
        warnings = check(actual_json)
        
        if filename == "KESC_0008.png":
            print("\n--- COMPARISON REPORT (KESC_0008) ---")
            mismatches = compare_fields(actual_json, expected_k8)
            if not mismatches:
                print("SUCCESS: All fields match within acceptable tolerance!")
            else:
                print("MISMATCHES FOUND:")
                for m in mismatches:
                    print(f"  - {m}")
                    
        else:
            print("\n--- EXTRACTED JSON ---")
            print(json.dumps(actual_json, indent=2))
            
            if warnings:
                print("\n--- VALIDATION WARNINGS ---")
                for w in warnings:
                    print(f"  * {w}")
            else:
                print("\n--- VALIDATION WARNINGS ---")
                print("  * None (Math checks perfectly!)")

if __name__ == "__main__":
    main()
