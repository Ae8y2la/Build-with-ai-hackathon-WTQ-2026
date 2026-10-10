import os
import sys
import io
import csv
import tempfile
import streamlit as st
from PIL import Image
import json
import pandas as pd

# Make scripts/ importable so we can reuse check_submission logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from check_submission import check_submission

def _run_submission_check():
    """Run check_submission() and return its errors list."""
    errors: list[str] = []
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    old_exit = sys.exit
    try:
        sys.exit = lambda *_a, **_kw: None  # type: ignore[assignment]
        check_submission()
    except SystemExit:
        pass
    finally:
        captured = sys.stdout.getvalue()
        sys.stdout = old_stdout
        sys.exit = old_exit  # type: ignore[assignment]

    for line in captured.splitlines():
        line = line.strip()
        if line.startswith("- "):
            errors.append(line[2:])
    return errors

from src.extract_l1 import extract_level_1
from src.extract_ctx import extract_context
from src.stats import compute_stats
from src.answer_l2 import answer_l2_questions
from src.csv_io import read_level1, read_level2, write_level1, write_level2
from src.pipeline import run_pipeline

st.set_page_config(page_title="Utility Bill Decoder", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 16px !important;
    color: #2B2A28;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Fraunces', serif !important;
    color: #2B2A28;
}
.block-container {
    max-width: 900px !important;
    padding-top: 3rem;
    padding-bottom: 3rem;
    text-align: left;
}
.answer-card {
    background-color: #FFFFFF;
    border: 1px solid #E6E1D8;
    border-radius: 10px;
    padding: 1.5rem;
    margin-top: 1rem;
    color: #2B2A28;
}
.key-label {
    color: #737373;
    font-size: 0.9rem;
    margin-bottom: 0.1rem;
}
.val-label {
    font-size: 1rem;
    font-weight: 500;
    margin-bottom: 0.8rem;
    color: #2B2A28;
}
.warning-text {
    color: #B7791F;
}
.success-text {
    color: #3C7A52;
}
</style>
""", unsafe_allow_html=True)

st.title("Utility Bill Decoder")
st.markdown("Upload an electricity bill and get a plain-language breakdown.")

tab1, tab2 = st.tabs(["Explain a bill", "Process a folder"])

with tab1:
    uploaded_file = st.file_uploader("Upload Bill Image", type=["png", "jpg", "jpeg"], help="Select a scanned or downloaded bill image.")
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
            
        col1, col2 = st.columns([1, 1.2], gap="large")
        with col1:
            st.image(Image.open(tmp_path), caption="Uploaded Bill", use_container_width=True)
            
        with col2:
            if st.button("Read this bill", type="primary"):
                with st.spinner("Reading your bill..."):
                    l1 = extract_level_1(tmp_path)
                    st.session_state['l1'] = l1
                    st.session_state['tmp_path'] = tmp_path
                    st.session_state.pop('ctx', None)
                    st.session_state.pop('stats', None)
                    
            if 'l1' in st.session_state:
                l1_data = st.session_state['l1']

                st.subheader("Bill Details")
                
                k_cols = st.columns(2)
                idx = 0
                for key, val in l1_data.items():
                    if key in ("charges", "taxes"):
                        continue
                    display_val = val if val is not None else "—"
                    with k_cols[idx % 2]:
                        st.markdown(f'<div class="key-label">{key}</div><div class="val-label">{display_val}</div>', unsafe_allow_html=True)
                    idx += 1
                
                st.write("")
                charges = l1_data.get("charges", [])
                taxes = l1_data.get("taxes", [])
                
                if charges:
                    st.markdown("**Charges**")
                    st.dataframe(pd.DataFrame(charges), use_container_width=True, hide_index=True)
                if taxes:
                    st.markdown("**Taxes**")
                    st.dataframe(pd.DataFrame(taxes), use_container_width=True, hide_index=True)

                with st.expander("Raw JSON"):
                    st.json(l1_data)

                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("Ask about this bill")

                default_questions = [
                    "What is the billing month?",
                    "What is the total amount due before the due date?",
                    "What are the total charges?",
                    "What is the total tax amount?",
                    "How many units were consumed?",
                    "What is the sanctioned load?",
                    "What is the tariff type?",
                    "What is the due date for this bill?",
                    "What are the arrears on this bill?",
                    "What is the amount payable after the due date?",
                    "What is the electricity provider?",
                    "What is the current meter reading?",
                ]
                q_choice = st.selectbox("Choose a question", ["— Type your own —"] + default_questions)
                q_custom = st.text_input("Or type your own question", help="Type any question about your bill here.")
                
                final_q = q_custom.strip() if q_custom.strip() else (
                    q_choice if q_choice != "— Type your own —" else ""
                )

                if final_q and st.button("Answer Question", type="primary"):
                    with st.spinner("Finding the answer..."):
                        if 'ctx' not in st.session_state:
                            st.session_state['ctx'] = extract_context(st.session_state['tmp_path'])
                        if 'stats' not in st.session_state:
                            st.session_state['stats'] = compute_stats(l1_data, st.session_state['ctx'])

                        q_list = [{"question_id": "Q_user", "question": final_q}]
                        ans = answer_l2_questions(
                            st.session_state['tmp_path'],
                            l1_data,
                            st.session_state['ctx'],
                            st.session_state['stats'],
                            q_list,
                        )
                        answer_text = ans.get("Q_user", "Could not find an answer.")
                        
                        st.markdown(f'<div class="answer-card"><strong>{final_q}</strong><br><br>{answer_text}</div>', unsafe_allow_html=True)

with tab2:
    st.subheader("Process a folder of bills")
    
    bills_dir = st.text_input("Bills Directory", value=r"train-20261010T061909Z-1-001\train\bills", help="Folder containing bill images.")
    csv_dir = st.text_input("Templates Directory", value="template", help="Folder containing level1.csv and level2.csv templates.")
    out_dir = st.text_input("Output Directory", value="output", help="Where to save the processed CSVs.")
    
    if st.button("Process Folder", type="primary"):
        if not os.path.exists(bills_dir):
            st.error(f"Bills directory not found: {bills_dir}")
        elif not os.path.exists(csv_dir):
            st.error(f"Templates directory not found: {csv_dir}")
        else:
            os.makedirs(out_dir, exist_ok=True)
            
            l1_header, l1_rows = read_level1(os.path.join(csv_dir, "level1.csv"))
            l2_header, l2_rows = read_level2(os.path.join(csv_dir, "level2.csv"))
            
            bill_questions = {}
            for row in l2_rows:
                b_id, q_id, q_text = row[0], row[1], row[2]
                if b_id not in bill_questions: bill_questions[b_id] = []
                bill_questions[b_id].append({"question_id": q_id, "question": q_text})
                
            bill_ids = [row[0] for row in l1_rows]
            l1_results = {}
            l2_results = {}
            bill_status = {}
            
            st.markdown(f"Processing {len(bill_ids)} bills...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, b_id in enumerate(bill_ids):
                status_text.text(f"Reading {b_id}...")
                
                img_path = os.path.join(bills_dir, f"{b_id}.png")
                if not os.path.exists(img_path):
                    img_path = os.path.join(bills_dir, f"{b_id}.jpg")
                    
                if not os.path.exists(img_path):
                    bill_status[b_id] = {"status": "skipped", "error": "Image not found"}
                else:
                    qs = bill_questions.get(b_id, [])
                    try:
                        r1, r2 = run_pipeline(b_id, img_path, qs)
                        l1_results[b_id] = r1
                        l2_results[b_id] = r2
                        bill_status[b_id] = {"status": "ok", "error": None}
                    except Exception as e:
                        bill_status[b_id] = {"status": "failed", "error": str(e)}
                        
                progress_bar.progress((i + 1) / len(bill_ids))
                
            write_level1(os.path.join(out_dir, "level1.csv"), l1_header, l1_rows, l1_results)
            write_level2(os.path.join(out_dir, "level2.csv"), l2_header, l2_rows, l2_results)
            
            status_text.text("Done!")
            
            st.markdown("### Summary")
            
            l1_path = os.path.join(out_dir, "level1.csv")
            l2_path = os.path.join(out_dir, "level2.csv")

            with open(l1_path, "r", encoding="utf-8") as f:
                l1_all = list(csv.reader(f))
            with open(l2_path, "r", encoding="utf-8") as f:
                l2_all = list(csv.reader(f))

            l1_data_rows = l1_all[1:]
            l2_data_rows = l2_all[1:]

            l1_count = len(l1_data_rows)
            l2_count = len(l2_data_rows)
            
            l1_msg = f"level1.csv — {l1_count} rows (expected 10)"
            l2_msg = f"level2.csv — {l2_count} rows (expected 120)"
            
            st.markdown(f'<div class="{"success-text" if l1_count == 10 else "warning-text"}">{l1_msg}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="{"success-text" if l2_count == 120 else "warning-text"}">{l2_msg}</div>', unsafe_allow_html=True)

            empty_l1_json = sum(1 for row in l1_data_rows if len(row) < 2 or not row[1].strip())
            empty_l2_ans = sum(1 for row in l2_data_rows if len(row) < 4 or not row[3].strip())
            
            e1_msg = f"level1.csv — {empty_l1_json} empty JSON cell(s)"
            e2_msg = f"level2.csv — {empty_l2_ans} empty answer cell(s)"
            
            st.markdown(f'<div class="{"success-text" if empty_l1_json == 0 else "warning-text"}">{e1_msg}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="{"success-text" if empty_l2_ans == 0 else "warning-text"}">{e2_msg}</div>', unsafe_allow_html=True)

            st.write("")
            st.markdown("### Previews")
            preview_tab_l1, preview_tab_l2 = st.tabs(["level1.csv", "level2.csv"])
            with preview_tab_l1:
                df_l1 = pd.read_csv(l1_path, encoding="utf-8", nrows=10)
                st.dataframe(df_l1, use_container_width=True)
            with preview_tab_l2:
                df_l2 = pd.read_csv(l2_path, encoding="utf-8", nrows=10)
                st.dataframe(df_l2, use_container_width=True)

            st.write("")
            st.markdown("### Per-Bill Status")
            for b_id in bill_ids:
                info = bill_status.get(b_id, {"status": "unknown", "error": None})
                if info["status"] == "ok":
                    st.markdown(f"<span style='color: #737373;'>{b_id}:</span> OK", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #737373;'>{b_id}:</span> <span class='warning-text'>{info['status']} ({info['error']})</span>", unsafe_allow_html=True)

            checker_errors = _run_submission_check()
            if checker_errors:
                st.markdown("<br><strong>Checker Issues</strong>", unsafe_allow_html=True)
                for err in checker_errors:
                    st.markdown(f'<div class="warning-text">{err}</div>', unsafe_allow_html=True)

            st.write("")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                with open(l1_path, "rb") as f:
                    st.download_button("Download level1.csv", data=f, file_name="level1.csv", mime="text/csv")
            with dl_col2:
                with open(l2_path, "rb") as f:
                    st.download_button("Download level2.csv", data=f, file_name="level2.csv", mime="text/csv")
