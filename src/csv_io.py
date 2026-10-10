import csv
import json

def read_level1(csv_path: str):
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    return header, rows

def read_level2(csv_path: str):
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    return header, rows

def write_level1(out_path: str, header: list, rows: list, results: dict):
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            bill_id = row[0]
            j_data = results.get(bill_id, {})
            # Dump safely onto one line without spaces if possible
            j_str = json.dumps(j_data, separators=(',', ':')) if j_data else "{}"
            writer.writerow([bill_id, j_str])

def write_level2(out_path: str, header: list, rows: list, results: dict):
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            bill_id = row[0]
            question_id = row[1]
            question = row[2]
            
            ans = results.get(bill_id, {}).get(question_id)
            if not ans or not str(ans).strip():
                ans = "The bill lacks this information or it could not be extracted."
                
            writer.writerow([bill_id, question_id, question, ans])
