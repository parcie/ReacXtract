from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import re
from docx import Document

# compre single page similarity

folder_gt = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_ground_truth"
folder_extracted = r"D:\All_self_files\info_extract_examples\621 pdf test\scanned\US20230357173A1\each_page_output"

# Function to extract page number from filenames like "page_12.docx" or "file_12.docx"
def extract_page_number(filename, prefix):
    match = re.match(rf"{prefix}_(\d+)\.docx", filename)
    return int(match.group(1)) if match else None

# Function to read .docx file content as a single string
def read_docx_text(filepath):
    doc = Document(filepath)
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

# Build maps: page number -> file path
gt_files = {
    extract_page_number(f, "page"): os.path.join(folder_gt, f)
    for f in os.listdir(folder_gt)
    if f.startswith("page_") and f.endswith(".docx") and extract_page_number(f, "page") is not None
}

ex_files = {
    extract_page_number(f, "file"): os.path.join(folder_extracted, f)
    for f in os.listdir(folder_extracted)
    if f.startswith("file_") and f.endswith(".docx") and extract_page_number(f, "file") is not None
}

# Find common pages present in both folders
common_pages = sorted(set(gt_files.keys()) & set(ex_files.keys()))

# Compare each matching pair
for page_num in common_pages:
    gt_text = read_docx_text(gt_files[page_num])
    ex_text = read_docx_text(ex_files[page_num])

    # Compute cosine similarity
    vectorizer = TfidfVectorizer().fit([gt_text, ex_text])
    vectors = vectorizer.transform([gt_text, ex_text])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    print(f"Page {page_num} similarity: {similarity:.4f}")

