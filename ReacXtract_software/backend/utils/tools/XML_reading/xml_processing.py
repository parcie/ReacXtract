'''
Patent_XML
 │
 ├── find_all_headings
 ├── find_candidate_headings
 ├── get_heading_intervals
 ├── get_paragraphs_in_interval
 │
 └── select_reaction_paragraphs

'''

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lxml import etree
from py2opsin import py2opsin
import warnings
from utils.tools.AI_interaction.AIChemist import AIChemist_gpt as AIC

class Patent_XML:

    def __init__(self, file_name):

        tree = etree.parse(file_name)
        root = tree.getroot()

        texts = {}
        tags = {}
        attributes = {}

        i = 0
        for element in root.iter():
            texts[i] = element.text
            tags[i] = element.tag
            attributes[i] = element.attrib
            i += 1

        self.texts = texts
        self.tags = tags
        self.attributes = attributes

    # -----------------------------
    # basic search tools
    # -----------------------------

    def search_from_tag(self, keyword_tag):

        keyword_tag = keyword_tag.lower()
        result = []

        for key, tag in self.tags.items():

            try:
                if tag.lower() == keyword_tag:
                    result.append(key)
            except:
                pass

        return result

    def search_from_text(self, input_dict, keyword_text):

        keyword_text = keyword_text.lower()
        result = []

        for key, text in input_dict.items():

            if text is None:
                continue

            try:
                if keyword_text in text.lower():
                    result.append(key)
            except:
                pass

        return result

    # -----------------------------
    # chemical name detection
    # -----------------------------

    @staticmethod
    def judgement_of_chemicals(input_string):

        if input_string is None:
            return '0'

        words_list = input_string.split()
        smiles_string = ''

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            for word in words_list:

                temp_smiles = py2opsin(
                    chemical_name=word,
                    output_format="SMILES"
                )

                if temp_smiles != "":
                    smiles_string = temp_smiles
                    break

        if smiles_string != "":
            return smiles_string
        else:
            return '0'

    # -----------------------------
    # find all headings
    # -----------------------------

    def find_all_headings(self):

        texts = self.texts

        heading_idx = (
            self.search_from_tag("heading") +
            self.search_from_tag("h")
        )

        headings = {}

        for idx in heading_idx:
            headings[idx] = texts[idx]

        return headings

    # -----------------------------
    # find candidate headings
    # -----------------------------

    def find_candidate_headings(self):

        headings = self.find_all_headings()

        example_headings = self.search_from_text(
            headings,
            "example"
        )

        chemical_headings = []

        for idx, text in headings.items():

            if text is None:
                continue

            result = self.judgement_of_chemicals(text)

            if result != '0':
                chemical_headings.append(idx)

        candidate = list(set(example_headings + chemical_headings))
        candidate.sort()

        return candidate

    # -----------------------------
    # heading intervals
    # -----------------------------

    def get_heading_intervals(self):

        headings = self.find_all_headings()

        heading_indices = sorted(headings.keys())

        intervals = []

        for i in range(len(heading_indices) - 1):

            start = heading_indices[i]
            end = heading_indices[i + 1]

            intervals.append((start, end))

        return intervals

    # -----------------------------
    # get paragraphs under heading
    # -----------------------------

    def get_paragraphs_in_interval(self, start, end):

        paragraphs = []

        for i in range(start + 1, end):

            tag = self.tags.get(i)
            text = self.texts.get(i)

            if tag == "p" and text:

                text = text.strip()

                if len(text) > 40:  # remove short fragments
                    paragraphs.append(text)

        return paragraphs

    # -----------------------------
    # AI judgement
    # -----------------------------

    @staticmethod
    def paragraph_ai_judgement(paragraph):

        AIC1 = AIC.AIChemists()

        judgement = AIC1.paragraph_is_reaction(paragraph)

        return judgement

    # -----------------------------
    # main function
    # -----------------------------

    def select_reaction_paragraphs(self):

        candidate_headings = self.find_candidate_headings()

        intervals = self.get_heading_intervals()

        reaction_paragraphs = []

        for start, end in intervals:

            if start not in candidate_headings:
                continue

            paragraphs = self.get_paragraphs_in_interval(start, end)

            for paragraph in paragraphs:

                result = self.paragraph_ai_judgement(paragraph)

                if "YES" in result.upper():

                    reaction_paragraphs.append(paragraph)

        return reaction_paragraphs


'''
xml = Patent_XML("patent.xml")

reaction_paragraphs = xml.select_reaction_paragraphs()

print(len(reaction_paragraphs))

for p in reaction_paragraphs[:5]:
    print(p)
'''