from utils.tools.PDF_reading.pdf_text_processing import PDF_text
from utils.tools.PDF_reading.pdf_paragraph_selection import ReactionParagraphPipeline
from openai import OpenAI

# 替换成你自己的 API Key
client = OpenAI(api_key='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')

pdf_object = PDF_text( r"D:\All_self_files\info_extract_examples\621 pdf test\extracting_estimation\3\ja6b12386_si_001.pdf")

print(f"总段落数: {len(pdf_object.para_list)}")
print(f"检测到的标题: {pdf_object.subtitle_list}")

# 测试反应段落筛选
pipeline = ReactionParagraphPipeline(client)
reaction_paragraphs = pipeline.select_from_pdf(pdf_object)

print(f"\n筛选出的潜在反应段落数量: {len(reaction_paragraphs)}")
for i, p in enumerate(reaction_paragraphs[:5]):
    print(f"\n--- Reaction Para {i+1} (Page {p.page}) ---")
    print(p.contents[:300] + "..." if len(p.contents) > 300 else p.contents)

from utils.tools.PDF_reading.pdf_text_processing import PDF_text

pdf_object = PDF_text(r"D:\All_self_files\info_extract_examples\621 pdf test\extracting_estimation\3\ja6b12386_si_001.pdf")

print("Pages:", len(pdf_object.cleaned_para_in_pages))
print("Final Subtitles Count:", len(pdf_object.subtitle_list))
print("\nCleaned Subtitles:")
for title in pdf_object.subtitle_list:
    print("   →", title)