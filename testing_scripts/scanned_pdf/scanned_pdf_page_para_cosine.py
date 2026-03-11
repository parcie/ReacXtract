import os
import re
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# === CONFIGURATION ===
folder_gt = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_ground_truth"
folder_extracted = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_output"

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
    return paragraphs

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

# === PARAGRAPH SIMILARITY SCORING ===

for page_num in common_pages:
    gt_paragraphs = read_docx_paragraphs(gt_files[page_num])
    ex_paragraphs = read_docx_paragraphs(ex_files[page_num])

    if not gt_paragraphs or not ex_paragraphs:
        print(f"Page {page_num}: Empty document!")
        continue

    # Combine all paragraphs for TF-IDF vectorization
    all_paragraphs = gt_paragraphs + ex_paragraphs
    vectorizer = TfidfVectorizer().fit(all_paragraphs)
    gt_vectors = vectorizer.transform(gt_paragraphs)
    ex_vectors = vectorizer.transform(ex_paragraphs)

    # For each ground truth paragraph, find the most similar extracted paragraph
    scores = []
    for gt_vec in gt_vectors:
        similarities = cosine_similarity(gt_vec, ex_vectors)[0]
        best_score = max(similarities)
        scores.append(best_score)

    # Average similarity score for this page
    avg_score = sum(scores) / len(scores)
    print(f"Page {page_num} GT-anchored paragraph-match score: {avg_score:.4f}")
