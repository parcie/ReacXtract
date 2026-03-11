import os
import re
from docx import Document
from bert_score import score

# Folder paths
folder_gt = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_ground_truth"
folder_extracted = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_output"

# Function to extract page number from filenames
def extract_page_number(filename, prefix):
    match = re.match(rf"{prefix}_(\d+)\.docx", filename)
    return int(match.group(1)) if match else None

# Read all text from a .docx file
def read_docx_text(filepath):
    doc = Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

# Build maps: page number -> file path
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

# Get only common pages
common_pages = sorted(set(gt_files.keys()) & set(ex_files.keys()))

# Compare with BERTScore
for page_num in common_pages:
    gt_text = read_docx_text(gt_files[page_num])
    ex_text = read_docx_text(ex_files[page_num])

    # BERTScore expects list of references and list of candidates
    P, R, F1 = score([ex_text], [gt_text], lang="en", verbose=False)

    print(f"Page {page_num} BERTScore P: {P.item():.4f}")
    print(f"Page {page_num} BERTScore R: {R.item():.4f}")
    print(f"Page {page_num} BERTScore F1: {F1.item():.4f}")
