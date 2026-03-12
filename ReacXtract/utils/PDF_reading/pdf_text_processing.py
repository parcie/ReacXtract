import fitz
import string
import re
import os
import doc2text
import time
from nltk.corpus import wordnet as wn
import unicodedata
from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # disables the decompression bomb protection

## this part is draft for scanned pdf
def para_in_page_len_counting(para_in_pages):
    """
    Count total character length across all paragraphs in all pages.
    Useful for comparing raw vs. cleaned text size.
    """
    all_text = ''
    for page in para_in_pages:
        for paragraph in page:
            all_text += paragraph
    return len(all_text)

def para_in_page_sum_counting(para_in_pages):
    """
    Count total number of paragraphs across all pages.
    Provides statistics to check effects of cleaning/merging.
    """
    para_number = 0
    for page in para_in_pages:
        for paragraph in page:
            para_number += 1
    return para_number

class paragraph:  # contents, page number, whether_cross_page
    """
    Represents a single paragraph of text.
    Attributes:
        contents (str): the actual text of the paragraph
        page (int): page number (1-based index)
        cross_page (bool): True if merged across page boundaries
    """
    def __init__(self, paragraph,page1,is_cross_page):
        self.contents = paragraph
        self.page = page1
        if is_cross_page is False:
            self.cross_page = False
        else:
            self.cross_page = True
        return None

class subtitle_module: #title, paragraph,all contents
    """
    Represents a document section defined by a subtitle/heading.

    Attributes:
        subtitle (str): section heading
        para_objects (list[paragraph]): paragraphs belonging to this section
        module_contents (list[str]): raw text of all paragraphs
        page_range (list[int]): list of unique page numbers spanned by this section
    """

    def __init__(self, subtitle,paragraphs):
        self.subtitle = subtitle
        self.para_objects = paragraphs
        contents = []
        pages = []
        for para in paragraphs:
            para_contents = para.contents
            contents.append(para_contents)
            page = para.page
            pages.append(page)

        page_range = list(dict.fromkeys(pages))
        self.module_contents = contents
        self.page_range = page_range
        return None

class PDF_text:
    def __init__(self, pdf_path):
        '''
        :param pdf_path: the abosolute path of the PDF file

        '''
        self.pdf_path = pdf_path
        parent_folder = os.path.dirname(os.path.abspath(pdf_path))

        is_digital = self.pdf_classification(pdf_path)
        self.is_digital = is_digital
        print(f'this pdf format is digital readable?{is_digital}')
        # get paras in pages without and  fixation
        if is_digital is True:
            raw_para_in_pages = self.digital_pdf_direct_reading(pdf_path)
        else:
            raw_para_in_pages  = self.scanned_pdf_direct_reading()

        self.raw_para_in_pages = raw_para_in_pages
        # do para cleaning and reforming
        if is_digital is True:
            cleaned_para_in_pages, subtitle_indices_in_pages, subtitle_text_in_pages = self.digital_pdf_para_cleaning(raw_para_in_pages)
        else:
            cleaned_para_in_pages, subtitle_indices_in_pages, subtitle_text_in_pages = self.scanned_pdf_para_cleaning(raw_para_in_pages)


        self.cleaned_para_in_pages = cleaned_para_in_pages

        #solving cross-page problem and create objects
        subtitle_module_oject_list, all_subtitles_string, para_object_list = self.cross_page_solving(cleaned_para_in_pages,subtitle_indices_in_pages,subtitle_text_in_pages)

        sub_module_number = len(all_subtitles_string)
        self.subtitle_string_list = all_subtitles_string
        self.sub_module_number = sub_module_number
        self.sub_module = subtitle_module_oject_list
        self.para_objects = para_object_list
        return None


    @property
    def subtitle_list(self):
        return self.subtitle_string_list

    @property
    def para_list(self):
        para_object_list = self.para_objects
        para_text_list = []
        for i in range(len(para_object_list)):
            para = para_object_list[i]
            para_text = para.contents
            para_text_list.append(para_text)
        return para_text_list

    @staticmethod
    def normalize_nested_strings(nested_list):
        """
        Normalize Unicode characters (e.g., ligatures) in a list of lists of strings.

        Parameters:
        - nested_list: List[List[str]] — a nested list containing strings

        Returns:
        - List[List[str]] — cleaned nested list with normalized strings
        """
        return [
            [unicodedata.normalize("NFKD", s) for s in sublist]
            for sublist in nested_list
        ]

    def get_page_contents(self,page_index):
        para_in_pages = self.cleaned_para_in_pages
        this_page = para_in_pages[page_index-1]
        return this_page

    def cross_page_solving(self,cleaned_para_in_pages,subtitle_indices_in_pages,subtitle_text_in_pages):
        '''solve cross page problem and create subtitle_module object and paragraph object'''
        page_number = len(cleaned_para_in_pages)
        self.page_number = page_number
        # firstly solve cross page paragraph problems
        # then create paragraph object list, label subtitle

        page_number = len(cleaned_para_in_pages)
        self.page_number = page_number

        para_object_list = []
        subtitle_points = []
        all_subtitles_string = []

        for i in range(page_number - 1):
            page = cleaned_para_in_pages[i]
            if not page:
                continue

            next_page = cleaned_para_in_pages[i + 1]
            if not next_page:
                continue

            subtitle_indices = subtitle_indices_in_pages[i]
            subtitle_texts = subtitle_text_in_pages[i]

            if i==0:
                subtitle_indices.append(0)
                subtitle_texts.append(page[0])

            # Check if last paragraph of this page continues on next page
            last_para = page[-1]
            first_next_para = next_page[0]

            legal_end = bool(re.search(r'[\.\!\?]["\')\]]?$', last_para))
            improper_start = not self.is_uppercase(first_next_para)
            needs_merge = not legal_end and improper_start

            if needs_merge:
                merged_para = f"{last_para} {first_next_para}"
                page[-1] = merged_para
                cleaned_para_in_pages[i] = page
                cleaned_para_in_pages[i + 1] = next_page[1:]  # remove first para of next page
            else:
                cleaned_para_in_pages[i] = page

            # Create paragraph objects for current page
            for j, para_content in enumerate(page):
                is_cross_page = (j == len(page) - 1 and needs_merge)
                if para_content != "":
                    para_obj = paragraph(para_content, page1=i + 1, is_cross_page=is_cross_page)
                    para_object_list.append(para_obj)

                # Subtitle detection
                if para_content in subtitle_texts:
                    subtitle_points.append(len(para_object_list) - 1)
                    all_subtitles_string.append(para_content)

        # Process last page separately
        last_page = cleaned_para_in_pages[-1]
        last_indices = subtitle_indices_in_pages[-1]
        last_texts = subtitle_text_in_pages[-1]

        for j, para_content in enumerate(last_page):
            para_obj = paragraph(para_content, page1=page_number, is_cross_page=False)
            para_object_list.append(para_obj)
            if j in last_indices and para_content in last_texts:
                subtitle_points.append(len(para_object_list) - 1)
                all_subtitles_string.append(para_content)

        # Ensure at least one subtitle starts at beginning
        if 0 not in subtitle_points:
            subtitle_points.insert(0, 0)
            all_subtitles_string.insert(0, "")

        # Create subtitle_module objects
        subtitle_modules = []
        for i in range(len(subtitle_points) - 1):
            start, end = subtitle_points[i], subtitle_points[i + 1]
            subtitle_text = all_subtitles_string[i]
            module_paragraphs = para_object_list[start+1:end]
            subtitle_modules.append(subtitle_module(subtitle_text, module_paragraphs))

        # Last subtitle module
        last_start = subtitle_points[-1]
        last_text = all_subtitles_string[-1]
        last_paragraphs = para_object_list[last_start + 1:]
        subtitle_modules.append(subtitle_module(last_text, last_paragraphs))

        return subtitle_modules, all_subtitles_string, para_object_list

    def digital_pdf_para_cleaning(self,raw_para_in_pages):
        '''do all digital pdf processings '''
        # remove footer by keyword matching
        raw_text_len = para_in_page_len_counting(raw_para_in_pages)

        no_footer_para_in_pages1 = []
        for page in raw_para_in_pages:
            not_footer_page = self.remove_footer(page)
            no_footer_para_in_pages1.append(not_footer_page)

        no_footer_para_in_pages = self.remove_repeated_header_footer(no_footer_para_in_pages1)
        #####
        # merge   wrongly separated paras in one page
        merged_para_in_pages = []
        for page in no_footer_para_in_pages:
            merged_para_in_page = self.merge_paragraph(page)
            merged_para_in_pages.append(merged_para_in_page)

        no_figure_para_in_pages = []
        for page in merged_para_in_pages:
            no_figure_para = self.figure_notes_cleaning(page)
            no_figure_para_in_pages.append(no_figure_para)

        subtitle_split_para_in_pages = []
        for page in no_figure_para_in_pages:
            splited_para_in_page = []
            for para in page:
                splited_para = self.split_by_all_caps_sections(para) # return sections in list
                splited_para_in_page.extend(splited_para)
            subtitle_split_para_in_pages.append(splited_para_in_page)

        blank_subtitle_list = ['',' ',',','()','(',')','.']
        # to clean and find all subtitles

        cleaned_para_in_pages = []
        title_indices_in_page = []
        title_text_in_page = []

        for i in range(len(subtitle_split_para_in_pages)):
            this_page = subtitle_split_para_in_pages[i]
            cleaned_para_this_page = []
            title_indices_this_page = []
            title_text_this_page = []
            for j in range(len(this_page)):
                section_j = this_page[j]
                subtitle_j = section_j[0]
                para_j = section_j[1]
                if subtitle_j not in blank_subtitle_list:
                    cleaned_para_this_page.append(subtitle_j)
                    title_indices_this_page.append(j)
                    title_text_this_page.append(subtitle_j)
                cleaned_para_this_page.append(para_j)
            cleaned_para_in_pages.append(cleaned_para_this_page)
            title_indices_in_page.append(title_indices_this_page)
            title_text_in_page.append(title_text_this_page)

        for i in range(len(subtitle_split_para_in_pages)):
            this_page = subtitle_split_para_in_pages[i]
            cleaned_para_this_page = []
            title_indices_this_page = []
            title_text_this_page = []
            for j in range(len(this_page)):
                section_j = this_page[j]
                subtitle_j = section_j[0]
                para_j = section_j[1]
                if subtitle_j not in blank_subtitle_list:
                    cleaned_para_this_page.append(subtitle_j)
                    title_indices_this_page.append(j)
                    title_text_this_page.append(subtitle_j)
                cleaned_para_this_page.append(para_j)
            cleaned_para_in_pages.append(cleaned_para_this_page)
            title_indices_in_page.append(title_indices_this_page)
            title_text_in_page.append(title_text_this_page)

        return cleaned_para_in_pages, title_indices_in_page, title_text_in_page

    def scanned_pdf_para_cleaning(self, raw_para_in_pages):
        '''
        :param raw_para_in_pages:
        :return: para_in pages, title_index_in_page, title_text_in_page
        '''
        # first clean footers? scanned pdf do not need?

        no_line_break_para_in_pages = []
        for page in raw_para_in_pages:
            no_line_break_page = self.remove_line_breaks(page)
            no_line_break_para_in_pages.append(no_line_break_page)

        # clean figure and table?
        no_figure_para_in_pages = []
        for page in no_line_break_para_in_pages:
            no_figure_para = self.figure_notes_cleaning(page)
            no_figure_para_in_pages.append(no_figure_para)

        # clean and find all subtitles
        merged_para_in_pages = []
        title_indices_in_pages = []
        title_text_in_pages = []
        for page in no_figure_para_in_pages:
            merged_para_in_page, title_indices_this_page, title_text_this_page = self.paragraph_in_scanned_page_cleaning(
                page)

            merged_para_in_pages.append(merged_para_in_page)
            title_indices_in_pages.append(title_indices_this_page)
            title_text_in_pages.append(title_text_this_page)

        return merged_para_in_pages, title_indices_in_pages, title_text_in_pages

    @staticmethod
    def remove_line_breaks(list):
        cleaned_list = []
        for text in list:
            cleaned_text1 = re.sub(r'(?<!-)\n', ' ', text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text1)
            cleaned_list.append(cleaned_text)
        return cleaned_list

    @staticmethod
    def figure_notes_cleaning(list_strings):
        '''to remove image notes'''
        notes_list = ['Fig.1', 'Fig.2', 'Fig.3', 'Fig.4','Fig.5','Fig.6', 'Fig.7', 'Fig.8', 'Fig.9','Fig.10',
                     'Fig. 1', 'Fig. 2', 'Fig. 3', 'Fig. 4', 'Fig. 5', 'Fig. 6', 'Fig. 7', 'Fig. 8', 'Fig. 9', 'Fig. 10',
                     'Figure 1', 'Figure 2', 'Figure 3', 'Figure 4','Figure 5', 'Figure 6', 'Figure 7', 'Figure 8','Figure 9', 'Figure 10',
                     'Table 1','Table 2','Table 3','Table 4','Table 5','Table 6','Table 7','Table 8','Table 9','Table 10','©',
                      'FIG. 1','FIG. 2','FIG. 3','FIG. 4','FIG. 5','FIG. 6','FIG. 7','FIG. 8','FIG. 9','FIG. 10']
        kept = []
        deleted= []
        for s in list_strings:
            if any(s.startswith(prefix) for prefix in notes_list):
                deleted.append(s)
            else:
                kept.append(s)

        return kept

    @staticmethod
    def pdf_classification(file_name):
        with fitz.open(file_name) as doc:
            raw_text = ""
            for page in doc:
                raw_text += page.get_text("text") + "\n"
        if raw_text.strip():
            contents = raw_text.strip()
            if len(contents) < 100:  #
                is_digital = False
            else:
                is_digital = True
        else:
            is_digital = False
        return is_digital

    @staticmethod
    def single_scanned_page_processing(page):
        '''
        input a singgle page and return its paragraph in list,should do page separation first
        '''
        doc = doc2text.Document(lang="eng")
        start = time.time()
        doc.read(page)
        doc.process()
        doc.extract_text()
        raw_text = doc.get_text()
        paragraphs_page = re.split(r'\n\s*\n', raw_text.strip())
        end = time.time()
        #file_execution_time = end - start
        #print(f"Execution time: {end - start:.4f} seconds")
        return paragraphs_page


    @staticmethod
    def scanned_pdf_separation(pdf_path, poppler_path="D:/poppler-24.08.0/Library/bin"):
        """
        Split scanned PDF into single-page PDFs, detect column layout,
        and replace two-column pages with two separate cropped PDFs.

        Returns:
            str: Path to folder containing all output single-page or split-column PDFs.
        """

        def detect_and_split_columns(img_cv):
            """
            Detects if the image has two columns and returns list of cropped images.
            Returns:
                List of NumPy arrays (1 or 2), cropped images.
            """
            _, thresh = cv2.threshold(img_cv, 200, 255, cv2.THRESH_BINARY_INV)
            vertical_sum = np.sum(thresh, axis=0)
            vertical_sum = vertical_sum / np.max(vertical_sum)
            middle = len(vertical_sum) // 2
            gap_threshold = 0.05
            left_max = np.max(vertical_sum[:middle])
            right_max = np.max(vertical_sum[middle:])
            center_gap = np.min(vertical_sum[middle - 50:middle + 50])
            is_two_column = center_gap < gap_threshold and left_max > gap_threshold and right_max > gap_threshold

            height, width = img_cv.shape

            if is_two_column:
                left = img_cv[:, :width // 2]
                right = img_cv[:, width // 2:]
                return [left, right]
            else:
                return [img_cv]

        # Prepare output folder
        pdf_folder = os.path.dirname(os.path.abspath(pdf_path))
        page_pdf_folder = os.path.join(pdf_folder, 'pdf_pages')
        os.makedirs(page_pdf_folder, exist_ok=True)

        # Load original PDF
        doc = fitz.open(pdf_path)

        for page_number in range(len(doc)):
            # Save original single-page PDF temporarily
            temp_pdf = fitz.open()
            temp_pdf.insert_pdf(doc, from_page=page_number, to_page=page_number)
            temp_pdf_path = os.path.join(page_pdf_folder, f"_temp_page_{page_number + 1}.pdf")
            temp_pdf.save(temp_pdf_path)
            temp_pdf.close()

            # Convert to image for column detection
            images = convert_from_path(temp_pdf_path, dpi=300, poppler_path=poppler_path)
            img_pil = images[0]
            img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2GRAY)

            # Detect and split
            cropped_images = detect_and_split_columns(img_cv)

            # Save cropped parts as new PDFs (replace original)
            if len(cropped_images) == 2:
                for idx, cropped in enumerate(cropped_images):
                    img_rgb = Image.fromarray(cropped).convert("RGB")
                    output_pdf_path = os.path.join(page_pdf_folder,
                                                   f"page_{page_number + 1}_{'left' if idx == 0 else 'right'}.pdf")
                    img_rgb.save(output_pdf_path)
            else:
                img_rgb = Image.fromarray(cropped_images[0]).convert("RGB")
                output_pdf_path = os.path.join(page_pdf_folder, f"page_{page_number + 1}.pdf")
                img_rgb.save(output_pdf_path)

            # Remove temporary file
            os.remove(temp_pdf_path)

        return page_pdf_folder
    def scanned_pdf_direct_reading(self):
        ''' return paragraph in pages(list of lists)'''

        def extract_page_number(path): # get the total number of pages
            import re
            match = re.search(r'page_(\d+)\.pdf', os.path.basename(path))
            return int(match.group(1)) if match else -1

        file_path = self.pdf_path
        page_pdf_folder = self.scanned_pdf_separation(file_path)

        all_pdf_files = []
        for filename in os.listdir(page_pdf_folder):
            if filename.endswith(".pdf"):
                page_pdf_path = os.path.join(page_pdf_folder, filename)
                all_pdf_files.append(page_pdf_path)
        file_path = self.pdf_path
        page_pdf_folder = self.scanned_pdf_separation(file_path)

        all_pdf_files = []
        for filename in os.listdir(page_pdf_folder):
            if filename.endswith(".pdf"):
                page_pdf_path = os.path.join(page_pdf_folder, filename)
                all_pdf_files.append(page_pdf_path)

        num_processes = min(os.cpu_count() or 12, len(all_pdf_files))

        sorted_page_pdf_paths = sorted(all_pdf_files, key=extract_page_number)
        start = time.time()

        paragraphs_list_in_pages = []
        for i in range(len(sorted_page_pdf_paths)):
            args = sorted_page_pdf_paths[i]
            pagei = self.single_scanned_page_processing(args)
            paragraphs_list_in_pages.append(pagei)

        end = time.time()

        return paragraphs_list_in_pages

    @staticmethod
    def digital_pdf_direct_reading(file_name):
        '''for digital pdf, return paragraphs in pages , list of lists'''
        doc = fitz.open(file_name)
        paragraphs_in_pages = []
        for page in doc:
            paragraph_this_page = []
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                block_text = []
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            block_text.append(text)
                    if block_text:
                        paragraph = ' '.join(block_text).strip()
                paragraph_this_page.append(paragraph)
            paragraphs_in_pages.append(paragraph_this_page)
        doc.close()
        return paragraphs_in_pages

    @staticmethod
    def remove_footer(page):
        '''to remove potential footer strings in a list'''
        key_words_list = [
            'pubs.', 'Pubs.','Received:','Accepted:','Published online:'
            'Received: Jan', 'Received: Feb', 'Received: Mar', 'Received: Apr', 'Received: May',
            'Received: Jun','Received: Jul', 'Received: Aug', 'Received: Sep', 'Received: Oct', 'Received: Nov', 'Received: Dec',
            'Received:Jan', 'Received:Feb', 'Received:Mar', 'Received:Apr', 'Received:May', 'Received:Jun',
            'Received:Jul','Received:Aug', 'Received:Sep', 'Received:Oct', 'Received:Nov', 'Received:Dec',
            'Res. Dev.', 'Res. Nov.', 'Res. Oct.', 'Res. Sep.', 'Res.Sept.','Res. Aug.', 'Res. Jul.', 'Res. Jun.', 'Res. May',
            'Res. Apr.', 'Res. Mar.', 'Res. Feb.', 'Res. Jan.',
            'Res.Dev.', 'Res.Nov.', 'Res.Oct.', 'Res.Sep.','Res.Sept.', 'Res.Aug.', 'Res.Jul.', 'Res.Jun.', 'Res.May', 'Res.Apr.',
            'Res.Mar.', 'Res.Feb.', 'Res.Jan.',
            'Received: January', 'Received: February', 'Received: March', 'Received: April', 'Received: May',
            'Received: June', 'Received: July', 'Received: August', 'Received: September', 'Received: October', 'Received: November',
            'Received: December',
            'https://doi.org', 'https://doi.', 'Downloaded via', 'DOI:', 'Vol.','©',
            'Nature Synthesis | Volume','Cite This:'
        ]
        removed = [s for s in page if any(piece in s for piece in key_words_list)]
        kept = [s for s in page if not any(piece in s for piece in key_words_list)]
        return kept

    @staticmethod
    def remove_repeated_header_footer(article_pages,check_last=2,threshold=0.8):
        matched_count = 0
        num_pages = len(article_pages)

        def looks_like_footer(text):
            return bool(re.search(r'\d{4}.*\d{4}\s*$', text))

        # Step 1: Count how many pages end with a footer-looking line
        for page in article_pages:
            for para in page[-check_last:]:  # check last 2 lines max
                if looks_like_footer(para):
                    matched_count += 1
                    break

        # Step 2: Only proceed if enough pages match the pattern
        if matched_count < threshold * num_pages:
            return article_pages  # Do not remove

        # Step 3: Remove footer-looking paragraph(s)
        cleaned = []
        for page in article_pages:
            new_page = page[:]
            for i in range(1, check_last + 1):
                if len(new_page) >= i and looks_like_footer(new_page[-i]):
                    new_page.pop(-i)
                    break
            cleaned.append(new_page)
        return cleaned


    @staticmethod
    def merge_paragraph(lines):
        '''
        to  merge paragraphs that wrongly separated within a page
        :param lines:
        :return:
        '''
        merged = []
        i = 0
        while i < len(lines):
            current = lines[i].strip()
            while (i + 1 < len(lines)):
                next_line = lines[i + 1].strip()
                # Check if current line does not end with punctuation
                # and next line does not start with capital letter or punctuation
                if (current and current[-1] not in '.!?;:' and
                        next_line and next_line[0] not in string.ascii_uppercase + string.punctuation):
                    current += ' ' + next_line
                    i += 1
                else:
                    break
            merged.append(current)
            i += 1
        return merged

    @staticmethod
    def split_by_all_caps_sections(text,meaningful_threshold=0.5, min_alpha_len=7):
        '''return section in tuple,[(title, contents)，(title,contents)]   '''
        text_len = len(text)
        def is_meaningful_word(word):  # the word must be meaninggful
            return len(wn.synsets(word.lower())) > 0

        def is_meaningful_phrase(phrase, threshold=0.5):
            tokens = [w.strip('-–—') for w in phrase.split()]
            words = [w for w in tokens if w.isalpha()]
            if not words:
                return False
            meaningful_count = sum(is_meaningful_word(w) for w in words)
            return meaningful_count / len(words) >= threshold

        special_sections = ['Introduction', 'Results and Discussion', 'Conclusion', 'Conclusions','References',
                            'Acknowledgements', 'Acknowledgement', 'Computational Methods', 'Abstract',
                            'Experimental Section', 'Experimental Sections', 'Result','Experimental section',
                            'Methods','Data availability','Results and discussion','Author contributions','Funding',
                            'Additional information','Competing interests','Computational Methods'
                            ]

        pattern = r'(?<!\w)([■●\-–—\s]*[A-Z][A-Z\s\-–—&]{2,})(?!\w)'
        all_caps_matches = list(re.finditer(pattern, text))

        filtered_matches = []

        # Step 1: From ALL CAPS
        for match in all_caps_matches:
            phrase = match.group(1).strip()
            alpha_count = sum(c.isalpha() for c in phrase)

            # Split into words and check length of first and last word
            words = phrase.split()
            if len(words) >= 2:
                first_word_len = sum(c.isalpha() for c in words[0])
                last_word_len = sum(c.isalpha() for c in words[-1])
            else:
                first_word_len = last_word_len = 0

            if (
                    alpha_count >= min_alpha_len and
                    is_meaningful_phrase(phrase, threshold=meaningful_threshold) and
                    first_word_len > 5 and
                    last_word_len > 5
            ):
                filtered_matches.append(match)

        # Step 2: From special sections (longer first, to avoid substring overlaps)
        matched_ranges = []
        for title in sorted(special_sections, key=len, reverse=True):
            for m in re.finditer(rf'\b{re.escape(title)}\b', text):
                start, end = m.start(), m.end()

                # Skip if this overlaps with any already matched section
                if any(s <= start < e or s < end <= e for s, e in matched_ranges):
                    continue

                # Only accept matches very close to the start or end
                if start <= 10 or end >= text_len - 10:
                    class SimpleMatch:
                        def __init__(self, start, end, group):
                            self._start = start
                            self._end = end
                            self._group = group

                        def start(self):
                            return self._start

                        def end(self):
                            return self._end

                        def group(self, idx=0):
                            return self._group

                    filtered_matches.append(SimpleMatch(start, end, m.group()))
                    matched_ranges.append((start, end))

        # Step 3: Normalize heading for deduplication
        def normalize_heading_text(text):
            return re.sub(r'[■●\-–—\s]+', '', text.upper())

        # Step 4: Keep only the FIRST occurrence of each unique heading
        seen_headings = set()
        deduped_matches = []
        for m in sorted(filtered_matches, key=lambda x: x.start()):
            norm_heading = normalize_heading_text(m.group())
            if norm_heading not in seen_headings:
                seen_headings.add(norm_heading)
                deduped_matches.append(m)

        filtered_matches = deduped_matches

        if not filtered_matches:
            return [('', text.strip())]

        # Step 5: Create sections
        sections = []
        for idx, match in enumerate(filtered_matches):
            heading = re.sub(r'^[■●\-–—\s]+', '', match.group().strip())  # clean symbols
            start = match.start()
            end = filtered_matches[idx + 1].start() if idx + 1 < len(filtered_matches) else len(text)
            if idx == 0 and start > 0:
                sections.append(('', text[:start].strip()))
            content = text[match.end():end].strip()
            sections.append((heading, content))

        return sections
        pattern = r'(?<!\w)([■●\-–—\s]*[A-Z][A-Z\s\-]{2,})(?!\w)'
        matches = list(re.finditer(pattern, text))
        sections = []

        filtered_matches = []
        for match in matches:
            phrase = match.group(1).strip()
            alpha_count = sum(c.isalpha() for c in phrase)
            if alpha_count >= min_alpha_len:
                filtered_matches.append(match)
        if not filtered_matches:
            return [('', text.strip())]

        for idx, match in enumerate(filtered_matches):
            heading = match.group(1).strip()
            start = match.start()
            end = filtered_matches[idx + 1].start() if idx + 1 < len(filtered_matches) else len(text)
            if idx == 0 and start > 0:
                sections.append(('', text[:start].strip()))
            content = text[match.end():end].strip()
            sections.append((heading, content))
        return sections

    @staticmethod
    def is_uppercase(s):
        for char in s:
            if char.isalpha():  # Check if it's an alphabet character
                return char.isupper()
        return False

    @staticmethod
    def paragraph_in_scanned_page_cleaning(strings):
        '''
        to merge wrongly separated para strings in scanned pdf page
        firstly merged and then find subtitles?
        :param strings:  a list of strings in a page
        :return:
        '''
        non_meaningful_words = {
            'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'by', 'with',
            'of', 'and', 'or', 'but', 'as', 'from', 'over', 'under','via'
        }

        def is_meaningful(word):
            return word.lower() not in non_meaningful_words

        def get_type(text):
            # when starts with step, synthesis

            words = text.split()

            # Check if the entire text is all uppercase and contains letters
            if text.isupper() and any(c.isalpha() for c in text):
                # New filter: skip short all-uppercase words like "OH"
                if len(text) < 6:
                    return 'type3'
                return 'type2'

            # Check if all meaningful words are title-cased
            all_title_case = all(
                not is_meaningful(word) or word[0].isupper()
                for word in words
            )
            if all_title_case:
                return 'type1'

            keyword_list = ['EXAMPLE','Example','EXAMPLES','Examples']
            if text.startswith(tuple(keyword_list)):
                return 'type2'

            return 'type3'

        def ends_with_punctuation(text):
            return text.rstrip()[-1] in '.!?'

        def starts_with_upper(text):
            return text.lstrip()[:1].isupper()

        merged = []
        title_indices = []
        title_texts = []

        i = 0
        while i < len(strings):
            current = strings[i]
            current_type = get_type(current)

            if current_type in {'type1', 'type2'}:
                title_indices.append(i)
                title_texts.append(current)
                combined = [current]
                j = i + 1
                while j < len(strings) and get_type(strings[j]) == current_type:
                    title_indices.append(j)
                    title_texts.append(strings[j])
                    combined.append(strings[j])
                    j += 1
                merged.append(' '.join(combined))
                i = j

            elif current_type == 'type3':
                combined = [current]
                j = i + 1
                while (
                        j < len(strings)
                        and get_type(strings[j]) == 'type3'
                        and not ends_with_punctuation(combined[-1])
                        and not starts_with_upper(strings[j])
                ):
                    combined.append(strings[j])
                    j += 1
                merged.append(' '.join(combined))
                i = j
            else:
                merged.append(current)
                i += 1

        return merged, title_indices, title_texts


'''
#digital_pdf_test

digital_pdf = 
digital_pdf_object = 
para_list = 
para_object_list = 
subtitle_string_list=      3
subtitle_object_list =         #
'''

'''
#scanned_pdf_test
scanned_pdf = 

scanned_pdf_object = 
para_list = scanned_pdf_object.para_list

subtitles = scanned_pdf_object.subtitles_list
raw_para_in_pages = scanned_pdf_object.raw_para_in_pages
'''

'''
pdf procedure
#generate pdf objects in list
# to judge whether 
# get paragraph object list: pdf_object.para_list
#get subtitle objct list: pdf_object.

'''





