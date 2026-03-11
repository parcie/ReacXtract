
from pdf_toolkits.pdf_text_processing import PDF_text
from pdf_toolkits.pdf_text_processing import paragraph
from pdf_toolkits.pdf_text_processing import subtitle_module

def get_pdf_para_text(pdf_fle):
    '''to transfer defined pdf object into module and para to estimate'''
    pdf_object = PDF_text(pdf_fle)
    pdf_sub_modules = pdf_object.sub_module
    para_list = pdf_object.para_list
    return para_list

from docx import Document
def read_paragraphs_from_docx(file_path):
    doc = Document(file_path)
    paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return paragraphs


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def align_paragraphs(gt_paras, rec_paras):
    """Align recognized paragraphs to ground truth using cosine similarity."""
    vectorizer = TfidfVectorizer().fit(gt_paras + rec_paras)
    gt_vecs = vectorizer.transform(gt_paras)
    rec_vecs = vectorizer.transform(rec_paras)

    similarity_matrix = cosine_similarity(rec_vecs, gt_vecs)  # [n_rec x n_gt]

    # Greedy matching: for each recognized para, find the best-matching GT para
    rec_to_gt = np.argmax(similarity_matrix, axis=1)
    scores = np.max(similarity_matrix, axis=1)

    return rec_to_gt, scores, similarity_matrix


from collections import defaultdict

def evaluate_segmentation(gt_paras, rec_paras, sim_threshold=0.5):
    rec_to_gt, scores, sim_matrix = align_paragraphs(gt_paras, rec_paras)

    # Count how many GT paras were matched by at least one recognized para
    gt_coverage = defaultdict(list)
    for i, gt_idx in enumerate(rec_to_gt):
        if scores[i] >= sim_threshold:
            gt_coverage[gt_idx].append(i)

    matched_gt = sum([1 for lst in gt_coverage.values() if len(lst) >= 1])
    splitting_errors = sum([len(lst) - 1 for lst in gt_coverage.values() if len(lst) > 1])

    precision = matched_gt / len(rec_paras)
    recall = matched_gt / len(gt_paras)
    f1 = 2 * precision * recall / (precision + recall + 1e-8)

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "splitting_errors": splitting_errors,
        "coverage_map": gt_coverage
    }


pdf_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\kutatel\kutateladze-novitskiy-2022-peculiar-reaction-products-and-mechanisms-revisited-with-machine-learning-augmented.pdf"
extracted_para_list = get_pdf_para_text(pdf_file)


docx_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\kutatel\ground_truth.docx"
gt_para_list = read_paragraphs_from_docx(docx_file)

results = evaluate_segmentation(gt_para_list, extracted_para_list)
print(results)


