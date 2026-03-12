import json
from utils.TXT_reading.txt_processing import TXT_text
from utils.TXT_reading.txt_processing import txt_to_paragraphs
from utils.TXT_reading.txt_processing import is_reaction_paragraph
from utils.paragraph_reading.para_to_table import ReactionExtractor
from utils.paragraph_reading.para_to_table import ReactionValidator
from utils.AI_interaction.AIChemist import  Transfering_tools

def txt_full_pipeline(
        txt_path,
        model_name,
        api_key,
        ):

    paragraphs = txt_to_paragraphs(txt_path)

    reaction_paragraphs = [
        p for p in paragraphs if is_reaction_paragraph(p)
    ]

    extractor = ReactionExtractor(
        model_name=model_name,
        api_key=api_key,
        transfer_tool= Transfering_tools
    )

    results = []

    for para in reaction_paragraphs:

        try:

            reaction_obj = extractor.build_reaction(para)

            validator = ReactionValidator(
                reaction_obj,
                model_name,
                api_key
            )

            issues = validator.validate_minimal()

            corrected_json = validator.reflect_with_llm()

            results.append(corrected_json)

        except Exception as e:

            print("Reaction parsing failed:", e)

    return results

'''
model_name = "gpt-4.1"
api_key = "your_api_key"

reaction_json_list = txt_full_pipeline()
    "paper.txt",
    model_name,
    api_key
)


'''