from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import unicodedata
from pdf_toolkits.pdf_text_processing import PDF_text

def get_pdf_para_text(pdf_fle):
    '''to transfer defined pdf object into module and para to estimate'''
    pdf_object = PDF_text(pdf_fle)
    pdf_sub_modules = pdf_object.sub_module
    para_list = pdf_object.para_list
    return para_list

def get_section_contents(pdf_fle,subtitle_name):
    pdf_object = PDF_text(pdf_fle)
    sub_modules = pdf_object.sub_module
    print('submodule numbers################################################')
    print(len(sub_modules))
    for sub_module in sub_modules:
        subtitle = sub_module.subtitle
        if subtitle_name == subtitle:
            print('&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&')
            print('subtitle_name:',subtitle_name)
            contents = sub_module.module_contents
            contents.insert(0,subtitle)
    return contents

def read_sections_from_docx(file_path):
    doc = Document(file_path)

    sections = []  # List of sections
    current_section = []  # Current section (list of paragraphs)
    blank_line_count = 0

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            blank_line_count += 1
            continue
        else:
            if blank_line_count >= 2:
                # Two or more blank lines = new section
                if current_section:
                    sections.append(current_section)
                    current_section = []
            blank_line_count = 0  # reset counter on actual text
            current_section.append(text)

    # Append last section if exists
    if current_section:
        sections.append(current_section)

    return sections

# TF-IDF
from docx import Document
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

'''
pdf_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\kutatel\kutateladze-novitskiy-2022-peculiar-reaction-products-and-mechanisms-revisited-with-machine-learning-augmented.pdf"
subtitle_name = "Peculiar Reaction Products and Mechanisms Revisited with Machine Learning-Augmented Computational NMR"
contents = get_section_contents(pdf_file,subtitle_name)
print(contents)
'''
gt_file =r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JACS\jacs1\ground_truth2.docx"
sections = read_sections_from_docx(gt_file) #from doc files

pdf_file = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JACS\jacs1\kaneeda-et-al-2000-enantioselective-protonation-of-silyl-enol-ethers-and-ketene-disilyl-acetals-with-lewis-acid.pdf"
title_section = sections[6]

subtitle_name = title_section[0]
print('subtitle_name',subtitle_name)

contents = get_section_contents(pdf_file,subtitle_name)
print('ground_truth',title_section)
print('test',contents)
result = evaluate_text_extraction(title_section,contents)
print(result)
