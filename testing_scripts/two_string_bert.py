from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from bert_score import score
import numpy as np


from docx import Document

def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

from bert_score import score
gt = read_docx(r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JACS\jacs3_selected\refernce_gt.docx")
test = read_docx(r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JACS\jacs3_selected\refernce_test.docx")

P, R, F1 = score([test], [gt], lang="en", verbose=True)
print(f"Precision: {P.item():.4f}")
print(f"Recall:    {R.item():.4f}")
print(f"F1 Score:  {F1.item():.4f}")