import os
import re
from docx import Document
from bert_score import score
from statistics import mean  # for averaging
# === CONFIGURATION ===

folder_gt = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_ground_truth"
folder_extracted = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_output"

lang = "en"  # change to "zh" for Chinese or other ISO language code

# === HELPERS ===

def extract_page_number(filename, prefix):
    match = re.match(rf"{prefix}_(\d+)\.docx", filename)
    return int(match.group(1)) if match else None

def read_docx_paragraphs(filepath):
    """Return list of paragraph strings, separated by blank lines."""
    doc = Document(filepath)
    paragraphs = []
    current_para = []
    for p in doc.paragraphs:
        if p.text.strip() == "":
            if current_para:
                paragraphs.append(" ".join(current_para).strip())
                current_para = []
        else:
            current_para.append(p.text.strip())
    if current_para:
        paragraphs.append(" ".join(current_para).strip())
    return [p for p in paragraphs if p]  # remove empty ones

# === FILE INDEXING ===

gt_files = {
    extract_page_number(f, "page"): os.path.join(folder_gt, f)
    for f in os.listdir(folder_gt)
    if f.endswith(".docx") and extract_page_number(f, "page") is not None
}

ex_files = {
    extract_page_number(f, "file"): os.path.join(folder_extracted, f)
    for f in os.listdir(folder_extracted)
    if f.endswith(".docx") and extract_page_number(f, "file") is not None
}

common_pages = sorted(set(gt_files.keys()) & set(ex_files.keys()))

# === BERTScore Alignment Scoring ===

for page_num in common_pages:
    gt_paragraphs = read_docx_paragraphs(gt_files[page_num])
    ex_paragraphs = read_docx_paragraphs(ex_files[page_num])

    if not gt_paragraphs or not ex_paragraphs:
        print(f"Page {page_num}: Skipped (empty doc)")
        continue

    precision_scores = []
    recall_scores = []
    f1_scores = []

    for gt_para in gt_paragraphs:
        # Compare this GT paragraph against all extracted ones
        P, R, F1 = score([gt_para] * len(ex_paragraphs), ex_paragraphs, lang=lang, verbose=False)

        best_p = max(P).item()
        best_r = max(R).item()
        best_f1 = max(F1).item()

        precision_scores.append(best_p)
        recall_scores.append(best_r)
        f1_scores.append(best_f1)

    # Average of best matches for the page
    avg_p = mean(precision_scores)
    avg_r = mean(recall_scores)
    avg_f1 = mean(f1_scores)

    print(f"Page {page_num} BERTScore — P: {avg_p:.4f}, R: {avg_r:.4f}, F1: {avg_f1:.4f}")

