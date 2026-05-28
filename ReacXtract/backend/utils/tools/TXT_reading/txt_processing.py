import os
import re
import unicodedata
from utils.tools.PDF_reading.pdf_text_processing import PDF_text
from utils.tools.PDF_reading.pdf_text_processing import subtitle_module
from utils.tools.PDF_reading.pdf_text_processing import paragraph

import re
import unicodedata


class TXT_text:

    def __init__(self, txt_path):

        self.txt_path = txt_path
        self.is_digital = True

        # Step 1: read txt
        raw_para_in_pages = self.txt_direct_reading(txt_path)

        self.raw_para_in_pages = raw_para_in_pages

        # Step 2: reuse digital pdf cleaning
        cleaned_para_in_pages, subtitle_indices_in_pages, subtitle_text_in_pages = \
            PDF_text.digital_pdf_para_cleaning(self, raw_para_in_pages)

        self.cleaned_para_in_pages = cleaned_para_in_pages

        # Step 3: reuse cross page solver
        subtitle_module_object_list, all_subtitles_string, para_object_list = \
            PDF_text.cross_page_solving(
                self,
                cleaned_para_in_pages,
                subtitle_indices_in_pages,
                subtitle_text_in_pages
            )

        self.subtitle_string_list = all_subtitles_string
        self.sub_module_number = len(all_subtitles_string)
        self.sub_module = subtitle_module_object_list
        self.para_objects = para_object_list

    # -----------------------
    # properties (same as PDF_text)
    # -----------------------

    @property
    def subtitle_list(self):
        return self.subtitle_string_list

    @property
    def para_list(self):
        para_text_list = []
        for para in self.para_objects:
            para_text_list.append(para.contents)
        return para_text_list

    # -----------------------
    # txt reader
    # -----------------------

    @staticmethod
    def txt_direct_reading(txt_path):
        """
        Read txt file and split into paragraphs.

        Returns
        -------
        List[List[str]]
            same structure as PDF_text.raw_para_in_pages
        """

        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()

        # normalize unicode
        text = unicodedata.normalize("NFKD", text)
        text = re.sub(r'(?<!-)\n', ' ', text)

        # split paragraphs
        paragraphs = re.split(r'\n\s*\n', text)

        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # wrap as one page
        return [paragraphs]


def is_reaction_paragraph(text):

    reaction_keywords = [
        "synthesis", "prepared", "afforded", "yield",
        "reaction", "stirred", "heated", "reflux",
        "added", "dissolved", "treated", "mixture"
    ]

    reagent_patterns = [
        r"\bmmol\b",
        r"\bmg\b",
        r"\bml\b",
        r"\bmol\b",
        r"\bPd\(",
        r"\bNa[A-Z]",
        r"\bK[A-Z]",
        r"\bCu[A-Z]",
        r"\bNi[A-Z]"
    ]

    score = 0

    text_lower = text.lower()

    for k in reaction_keywords:
        if k in text_lower:
            score += 1

    for p in reagent_patterns:
        if re.search(p, text):
            score += 1

    if len(text) < 80:
        return False

    return score >= 3

import re

def txt_to_paragraphs(txt_path):

    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = re.sub(r'(?<!-)\n', ' ', text)

    paragraphs = re.split(r'\n\s*\n', text)

    paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 30]

    return paragraphs