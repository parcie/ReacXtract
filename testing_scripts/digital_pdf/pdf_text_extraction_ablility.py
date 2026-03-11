from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# evaluate
def evaluate_text_extraction(gt_paras, rec_paras):
    gt_text = ' '.join(gt_paras).strip()
    rec_text = ' '.join(rec_paras).strip()

    vectorizer = TfidfVectorizer().fit([gt_text, rec_text])
    vecs = vectorizer.transform([gt_text, rec_text])
    sim = cosine_similarity(vecs[0], vecs[1])[0, 0]

    return {
        "cosine_similarity": round(sim, 4),
        "gt_length": len(gt_text),
        "rec_length": len(rec_text)
    }

pdf_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JOC-10\JOC6\ding-et-al-2025-amine-controlled-transition-metal-catalyzed-hydrodefluorination-and-defluoroamination-of-fluoroarenes.pdf"
extracted_para_list = get_pdf_para_text(pdf_file)


docx_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\nature_synthesis\ns_5\ground_truth.docx"
gt_para_list = read_paragraphs_from_docx(docx_file)

result = evaluate_text_extraction(gt_para_list, extracted_para_list)
print(result)