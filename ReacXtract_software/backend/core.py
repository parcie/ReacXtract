"""
Core processing module - One-click processing of multiple files and output complete JSON
"""

from utils.tools.CDX_reading.cdx_json_processing import CDXReactionExtractor
from utils.tools.AI_interaction.AIChemist import Transfering_tools

from utils.PDF_full_process import pdf_full_pipeline
from utils.XML_full_process import xml_full_pipeline
from utils.TXT_full_process import txt_full_pipeline

import openai
import os
import json
from collections import defaultdict
from utils.IMAGE_full_process import collect_valid_molecules
from utils.IMAGE_full_process import ReactionImageLinker



def classify_files(file_list):
    """
    根据文件扩展名对输入文件进行分类
    """
    image_ext = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

    result = {
        "pdf": [], "xml": [], "txt": [], "cdx": [], "image": [], "other": []
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


def build_global_compound_registry(reaction_jsons):
    """
    构建全局化合物注册表，实现跨文件 SMILES 和名称补充
    """
    registry = defaultdict(dict)  # label or name -> best SMILES

    for rxn in reaction_jsons:
        for role in ["reactants", "products", "catalysts", "other_chemicals"]:
            for compound in rxn.get(role, []):
                label = compound.get("label") or compound.get("name")
                smiles = compound.get("SMILES")

                if not label or label in ("unknown", "", None):
                    continue

                label = str(label).strip().lower()

                if smiles and smiles not in ("unknown", "", None):
                    if label not in registry or len(smiles) > len(registry[label].get("smiles", "")):
                        registry[label]["smiles"] = smiles
                        registry[label]["name"] = compound.get("name")

    return registry


def apply_global_registry(reaction_jsons, registry):
    """
    使用全局注册表补充所有反应中的 SMILES
    """
    for rxn in reaction_jsons:
        for role in ["reactants", "products", "catalysts", "other_chemicals"]:
            for compound in rxn.get(role, []):
                label = compound.get("label") or compound.get("name")
                if not label:
                    continue
                label = str(label).strip().lower()

                if label in registry and registry[label].get("smiles"):
                    if not compound.get("SMILES") or compound.get("SMILES") in ("unknown", ""):
                        compound["SMILES"] = registry[label]["smiles"]
    return reaction_jsons


def whole_pipeline(api_key, model_name, list_of_files):
    """
    主流程：支持多文件输入，实现全面信息相互补充
    """
    print(f"开始处理 {len(list_of_files)} 个文件...")

    # 文件分类
    file_classify_results = classify_files(list_of_files)
    pdf_files = file_classify_results["pdf"]
    xml_files = file_classify_results["xml"]
    txt_files = file_classify_results["txt"]
    cdx_files = file_classify_results["cdx"]
    image_files = file_classify_results["image"]
    other_files = file_classify_results["other"]

    if other_files:
        print("⚠️  以下文件无法识别：")
        for f in other_files:
            print(f"   {f}")

    # ==================== 1. 处理各类文件 ====================
    all_reaction_jsons = []

    # PDF
    for f in pdf_files:
        print(f"正在处理 PDF: {f}")
        try:
            all_reaction_jsons.extend(pdf_full_pipeline(f, model_name, api_key))
        except Exception as e:
            print(f"❌ PDF 处理失败 {f}: {e}")

    # XML
    for f in xml_files:
        print(f"正在处理 XML: {f}")
        try:
            all_reaction_jsons.extend(xml_full_pipeline(f, model_name, api_key))
        except Exception as e:
            print(f"❌ XML 处理失败 {f}: {e}")

    # TXT
    for f in txt_files:
        print(f"正在处理 TXT: {f}")
        try:
            all_reaction_jsons.extend(txt_full_pipeline(f, model_name, api_key))
        except Exception as e:
            print(f"❌ TXT 处理失败 {f}: {e}")

    # CDX
    for f in cdx_files:
        print(f"正在处理 CDX: {f}")
        try:
            extractor = CDXReactionExtractor(
                chemdraw_path=r"C:\Program Files\ChemDraw\ChemDraw.exe"
            )
            result = extractor.extract(f)
            # 根据实际返回结构适配
            if isinstance(result, dict) and 'reactions' in result:
                all_reaction_jsons.extend(result['reactions'])
            else:
                all_reaction_jsons.append(result)
        except Exception as e:
            print(f"❌ CDX 处理失败 {f}: {e}")

    print(f"共提取到 {len(all_reaction_jsons)} 个反应记录")

    # ==================== 2. 全局图片补充 ====================
    if image_files:
        print(f"正在处理 {len(image_files)} 个图片文件...")
        image_results = collect_valid_molecules(image_files)
        if image_results:
            linker = ReactionImageLinker(similarity_threshold=0.85)
            for i, rxn in enumerate(all_reaction_jsons):
                all_reaction_jsons[i] = linker.link(rxn, image_results)
            print(f"✅ 已完成图片结构补充（{len(image_results)} 个有效分子）")

    # ==================== 3. 全局化合物注册表补充（跨文件增强） ====================
    print("正在进行全局化合物信息归一化...")
    registry = build_global_compound_registry(all_reaction_jsons)
    all_reaction_jsons = apply_global_registry(all_reaction_jsons, registry)

    print(f"处理完成！最终输出 {len(all_reaction_jsons)} 个反应 JSON")
    return all_reaction_jsons

'''
# ====================== Example Usage ======================
if __name__ == "__main__":
    API_KEY ='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'

    files = [
        r"D:\All_self_files\info_extract_examples\621 pdf test\extracting_estimation\3\ja6b12386_si_001.pdf"
    ]

    result = whole_pipeline(
        api_key=API_KEY,
        model_name="gpt-4.1",
        file_list=files,
        output_file=r"D:\All_self_files\info_extract_examples\621 pdf test\extracting_estimation\3\ja6b12386_si_001_reaction.json"
    )

    print(f"\n📄 JSON output file: my_reactions.json")
'''
if __name__ == "__main__":
    api_key = "your_api_key"
    model_name = "gpt-4.1"

    files = [
        "paper1.pdf",
        "reaction2.xml",
        "molecule_images/*.png",
        "scheme.cdx"
    ]

    results = whole_pipeline(api_key, model_name, files)
    print(results)

    # 保存结果
    with open("all_reactions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)