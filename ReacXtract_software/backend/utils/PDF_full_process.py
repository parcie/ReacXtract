'''
PDF
 │
 ├── Step1  ReactionParagraphPipeline
 │        ↓
 │   selected_paragraphs
 │
 ├── Step2  PDF_image
 │        ↓
 │   image_object_list
 │
 ├── Step3  ReactionExtractor
 │        ↓
 │   reaction_json_list
 │
 └── Step4  Label Resolver
          ↓
   completed_reaction_json_list
'''

from utils.tools.PDF_reading.pdf_image_cropping import inserted_image
from utils.tools.PDF_reading.pdf_image_cropping import PDF_image
from utils.tools.PDF_reading.pdf_text_processing import paragraph
from utils.tools.PDF_reading.pdf_text_processing import subtitle_module
from utils.tools.PDF_reading.pdf_text_processing import PDF_text
from utils.tools.PDF_reading.pdf_paragraph_selection import ReactionRegexDetector
from utils.tools.paragraph_reading.para_to_table import Reaction
from utils.tools.paragraph_reading.para_to_table import ReactionExtractor
from utils.tools.paragraph_reading.para_to_table import ReactionValidator
from utils.tools.PDF_reading.pdf_paragraph_selection import ReactionParagraphPipeline
from utils.tools.AI_interaction.AIChemist import Transfering_tools
import openai
from openai import OpenAI
import json
import sys
sys.setrecursionlimit(5000)

def build_label_smiles_map_for_paragraph(image_object_list, paragraph_page):

    nearby_images = filter_images_by_page(image_object_list, paragraph_page)

    label_map = {}

    for img in nearby_images:

        smiles = img.molecule_smiles

        for label in img.molecule_label_list:

            label = label.strip()

            label_map[label] = smiles

    return label_map

def fill_missing_smiles(reaction_json, label_map):

    roles = ["reactants", "products", "catalysts", "reagents"]

    for role in roles:

        if role not in reaction_json:
            continue

        for compound in reaction_json[role]:

            name = compound.get("name")
            smiles = compound.get("smiles")
            label = compound.get("label")

            if (not name) and (not smiles) and label:

                if label in label_map:

                    compound["smiles"] = label_map[label]
                    compound["name"] = label

    return reaction_json


def filter_images_by_page(image_object_list, paragraph_page, window=1):

    nearby_images = []

    for img in image_object_list:

        if abs(img.page_number - paragraph_page) <= window:
            nearby_images.append(img)

    return nearby_images

def resolve_labels_with_page_filter(
        reaction_json,
        paragraph_page,
        image_object_list
):

    label_map = build_label_smiles_map_for_paragraph(
        image_object_list,
        paragraph_page
    )

    reaction_json = fill_missing_smiles(
        reaction_json,
        label_map
    )

    return reaction_json

# PDF file name to jsons(json objects)

def pdf_full_pipeline(pdf_path,model_name,api_key):
    pdf_object = PDF_text(pdf_path)

    # STEP1 paragraph detection
    client = OpenAI(api_key=api_key)
    pipeline = ReactionParagraphPipeline(client)

    reaction_paragraphs = pipeline.select_from_pdf(pdf_object)


    # STEP2 image extraction
    image_object_list = PDF_image(pdf_path)


    # STEP3 paragraph → reaction json

    reaction_json_list = []

    for p in reaction_paragraphs:

        reaction_description = p.contents

        extractor = ReactionExtractor(
            model_name=model_name,
            api_key=api_key,
            transfer_tool=Transfering_tools
        )

        reaction_obj = extractor.build_reaction(reaction_description)

        validator = ReactionValidator(reaction_obj, model_name, api_key)

        validator.validate_minimal()

        corrected_json = validator.reflect_with_llm()

        reaction_json_list.append(corrected_json)

    completed_json_list = []

    for p, reaction_json in zip(reaction_paragraphs, reaction_json_list):
        new_json = resolve_labels_with_page_filter(
            reaction_json,
            p.page,
            image_object_list
        )

        completed_json_list.append(new_json)

    return completed_json_list

