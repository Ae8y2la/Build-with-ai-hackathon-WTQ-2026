import os
import argparse
import logging
from src.csv_io import read_level1, read_level2, write_level1, write_level2
from src.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run the bill extraction pipeline.")
    parser.add_argument("--bills", required=True, help="Directory containing bill images")
    parser.add_argument("--csv", required=True, help="Directory with level1.csv and level2.csv templates")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    logger.info("Reading CSV templates...")
    l1_header, l1_rows = read_level1(os.path.join(args.csv, "level1.csv"))
    l2_header, l2_rows = read_level2(os.path.join(args.csv, "level2.csv"))

    # Map questions to bill_id
    bill_questions = {}
    for row in l2_rows:
        bill_id, q_id, q_text = row[0], row[1], row[2]
        if bill_id not in bill_questions:
            bill_questions[bill_id] = []
        bill_questions[bill_id].append({"question_id": q_id, "question": q_text})

    l1_results = {}
    l2_results = {}
    
    success_count = 0
    error_count = 0

    bill_ids = [row[0] for row in l1_rows]
    logger.info(f"Found {len(bill_ids)} bills in template.")
    
    for bill_id in bill_ids:
        # Resolve image path
        img_path = os.path.join(args.bills, f"{bill_id}.png")
        if not os.path.exists(img_path):
            img_path = os.path.join(args.bills, f"{bill_id}.jpg")
            if not os.path.exists(img_path):
                logger.error(f"[{bill_id}] Image not found! Expected .png or .jpg in {args.bills}")
                error_count += 1
                continue

        questions = bill_questions.get(bill_id, [])
        
        try:
            l1_res, l2_res = run_pipeline(bill_id, img_path, questions)
            l1_results[bill_id] = l1_res
            l2_results[bill_id] = l2_res
            success_count += 1
        except Exception as e:
            logger.error(f"[{bill_id}] Unexpected runner crash: {e}")
            error_count += 1

    logger.info("Writing output CSV files...")
    write_level1(os.path.join(args.out, "level1.csv"), l1_header, l1_rows, l1_results)
    write_level2(os.path.join(args.out, "level2.csv"), l2_header, l2_rows, l2_results)

    # Print Summary
    print("\n" + "="*40)
    print("PIPELINE SUMMARY")
    print("="*40)
    print(f"Total Bills Expected : {len(bill_ids)}")
    print(f"Successful Runs      : {success_count}")
    print(f"Failed/Missing       : {error_count}")
    print(f"Output Directory     : {args.out}")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
