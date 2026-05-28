from http import client

import re


class ReactionRegexDetector:

    def __init__(self):

        patterns = [

            # reagent patterns
            r"\bmixture of\b",
            r"\bsolution of\b",

            # reaction verbs
            r"\breacted with\b",
            r"\bstirred\b",
            r"\bheated\b",
            r"\breflux\b",
            r"\btreated with\b",
            r"\badded\b",

            # reaction conditions
            r"\b\d+\s*(°C|K)\b",
            r"\b\d+\s*(h|min)\b",
            r"\bund(er)? nitrogen\b",

            # workup
            r"\bwashed with\b",
            r"\bextracted with\b",
            r"\bdried over\b",
            r"\bcolumn chromatography\b",

            # yield
            r"\byield(ed)?\b",
            r"\bto give\b",
            r"\bobtained\b",
            r"\bafford(ed)?\b",

            # compound index
            r"\bcompound\s+\d+\b",

            # percent yield
            r"\b\d{1,3}\s*%\b",
        ]

        self.patterns = [re.compile(p, re.I) for p in patterns]

    def score(self, text):

        score = 0

        for p in self.patterns:
            if p.search(text):
                score += 1

        return score

    def is_reaction_candidate(self, text, threshold=2):

        return self.score(text) >= threshold

def keyword_filter(subtitle_modules):

    keywords = [
        "synthesis",
        "example",
        "examples",
        "method",
        "methods",
        "reaction",
        "experiment",
        "experimental",
        "preparation",
        "procedure"
    ]

    result = []

    for sm in subtitle_modules:

        title = sm.subtitle.lower()

        if any(k in title for k in keywords):
            result.append(sm)

    return result

class ReactionLLMVerifier:

    def __init__(self, client, model="gpt-4.1"):

        self.client = client
        self.model = model

        self.prompt = """
You are an expert organic chemist.

Determine whether the following paragraph describes an experimental chemical reaction procedure.

Answer strictly with "Yes" or "No".

Example:

Paragraph:
"A mixture of benzaldehyde and acetone was stirred under reflux for 5 hours."

Answer:
Yes

Paragraph:
"The mechanism of aldol condensation has been widely studied."

Answer:
No
"""

    def verify(self, paragraph_text):

        query = f"""
{self.prompt}

Paragraph:
{paragraph_text}

Answer:
"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": query}]
        )

        ans = resp.choices[0].message.content.strip().lower()

        return ans.startswith("yes")

class ReactionParagraphPipeline:

    def __init__(self, client, model="gpt-4.1"):

        self.regex_detector = ReactionRegexDetector()
        self.llm = ReactionLLMVerifier(client, model)

    def select_from_pdf(self, pdf_object):

        selected_paragraphs = []

        subtitle_modules = pdf_object.sub_module

        # Step1 keyword filter
        modules = keyword_filter(subtitle_modules)

        # Step2 regex detector
        regex_candidates = []

        for sm in modules:

            for para in sm.para_objects:

                if self.regex_detector.is_reaction_candidate(para.contents):
                    regex_candidates.append(para)

        # Step3 LLM confirmation
        for para in regex_candidates:

            if self.llm.verify(para.contents):
                selected_paragraphs.append(para)

        return selected_paragraphs
''''
#使用
pipeline = ReactionParagraphPipeline(client)
reaction_paragraphs = pipeline.select_from_pdf(pdf_object)
返回
[
 paragraph(),
 paragraph(),
 paragraph()
]
其中
paragraph.contents
paragraph.page
paragraph.cross_page

'''
