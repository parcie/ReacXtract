from utils.XML_reading.xml_processing import Patent_XML
from utils.paragraph_reading.para_to_table import ReactionExtractor
from utils.paragraph_reading.para_to_table import ReactionValidator
from utils.PDF_reading.pdf_paragraph_selection import ReactionParagraphPipeline
from utils.AI_interaction.AIChemist import Transfering_tools

def xml_full_pipeline(xml_file, model_name, api_key):

    # -------------------------
    # STEP 1 读取 XML
    # -------------------------

    xml = Patent_XML(xml_file)

    reaction_paragraphs = xml.select_reaction_paragraphs()

    print("Detected reaction paragraphs:", len(reaction_paragraphs))

    # -------------------------
    # STEP 2 初始化 extractor
    # -------------------------

    extractor = ReactionExtractor(
        model_name=model_name,
        api_key=api_key,
        transfer_tool=Transfering_tools
    )

    reaction_json_list = []

    # -------------------------
    # STEP 3 paragraph → reaction JSON
    # -------------------------

    for i, paragraph in enumerate(reaction_paragraphs):

        print(f"\nProcessing paragraph {i+1}")

        try:

            # build reaction
            reaction_obj = extractor.build_reaction(paragraph)

            # validation
            validator = ReactionValidator(
                reaction_obj,
                model_name,
                api_key
            )

            issues = validator.validate_minimal()

            print("Detected issues:", issues)

            # optional reflection
            corrected_json = validator.reflect_with_llm()

            reaction_json_list.append(corrected_json)

        except Exception as e:

            print("Error processing paragraph:", e)
            continue

    return reaction_json_list