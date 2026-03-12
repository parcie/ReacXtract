import openai
from sympy.codegen.ast import continue_

from PDF_full_process import pdf_full_pipeline
from XML_full_process import xml_full_pipeline
from TXT_full_process import txt_full_pipeline
from IMAGE_full_process import ReactionImageLinker
from IMAGE_full_process import collect_valid_molecules
import os
from utils.CDX_reading.cdx_json_processing import CDXReactionExtractor


def classify_files(file_list):
    """
    Classify files into categories based on file extension.

    Parameters
    ----------
    file_list : list[str]
        List of file names or file paths.

    Returns
    -------
    dict
        {
            "pdf": [],
            "xml": [],
            "txt": [],
            "cdx": [],
            "image": [],
            "other": []
        }
    """

    image_ext = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

    result = {
        "pdf": [],
        "xml": [],
        "txt": [],
        "cdx": [],
        "image": [],
        "other": []
    }

    for file in file_list:
        ext = os.path.splitext(file)[1].lower()

        if ext == ".pdf":
            result["pdf"].append(file)

        elif ext == ".xml":
            result["xml"].append(file)

        elif ext == ".txt":
            result["txt"].append(file)

        elif ext == ".cdx":
            result["cdx"].append(file)

        elif ext in image_ext:
            result["image"].append(file)

        else:
            result["other"].append(file)

    return result

def whole_pipeline(api_key, model_name, list_of_files):
    openai.api_key = api_key
    openai.base_url = "https://api.openai.com/v1/"

    file_classify_results = classify_files(list_of_files)
    pdf_files = file_classify_results["pdf"]
    xml_files = file_classify_results["xml"]
    txt_files = file_classify_results["txt"]
    cdx_files = file_classify_results["cdx"]
    image_files = file_classify_results["image"]
    other_files = file_classify_results["other"]

    if len(other_files) != 0:
        print("there is a file that cannot be recognized")
        for f in other_files:
            print(f)

    pdf_jsons = []
    xml_jsons = []
    txt_jsons = []
    cdx_jsons = []
    for f in pdf_files:
        pdf_jsons.extend(pdf_full_pipeline(f,model_name,api_key))
    for f in xml_files:
        xml_jsons.extend(xml_full_pipeline(f,model_name,api_key))
    for f in txt_files:
        txt_jsons.extend(txt_full_pipeline(f,model_name,api_key))

    non_figure_jsons = pdf_jsons + xml_jsons + txt_jsons

    for f in cdx_files:
        extractor = CDXReactionExtractor(
            chemdraw_path=r"C:\Program Files\ChemDraw\ChemDraw.exe"
        )
        result = extractor.extract(f)
        cdx_jsons.append(result['reactions'])

    image_results = collect_valid_molecules(image_files)
    if len(image_files) != 0:
        linker = ReactionImageLinker()
        updated_json_objects = []
        for j in non_figure_jsons:
            completed_json = linker.link(j,image_results)
            updated_json_objects.append(completed_json)
            updated_json_objects = updated_json_objects+cdx_jsons
    else:
        updated_json_objects = non_figure_jsons+cdx_jsons
    return updated_json_objects







