import pubchempy as pcp
import warnings
import openai
from openai import OpenAI
import tiktoken

# need test

# for gpt-4.1
import tiktoken

class ReactionParagraphSelector:
    # run ReactionParagraphSelector. select_reaction_paragraphs to get a dict {subtitle:reaction_paragraph_list}
    # should input a got client object
    def __init__(self, client, model="gpt-4.1", batch_size=None, safety_margin=0.9):
        self.client = client
        self.model = model
        self.safety_margin = safety_margin
        self.batch_size = batch_size  # if None, auto-calculated later

        # Few-shot examples for subtitle-level classification
        self.subtitle_few_shot = """
                                    You are an expert chemist. 
                                    Determine if the following subtitle and its leading paragraph suggest that this section may contain chemical reaction descriptions. 
                                    Answer strictly with "Yes" or "No".

                                    Example 1:
                                    Subtitle: "Example 1: Synthesis of aspirin"
                                    Paragraph: "A mixture of salicylic acid and acetic anhydride was heated under reflux..."
                                    Answer: Yes

                                    Example 2:
                                    Subtitle: "Background of catalytic processes"
                                    Paragraph: "The role of catalysts in accelerating reactions has been studied extensively."
                                    Answer: No

                                    Example 3:
                                    Subtitle: "Experimental Section: Preparation of compound B"
                                    Paragraph: "Compound B was obtained by reacting benzaldehyde with ammonia under pressure..."
                                    Answer: Yes

                                    Example 4:
                                    Subtitle: "History of chemical thermodynamics"
                                    Paragraph: "The first and second laws of thermodynamics were formulated in the 19th century."
                                    Answer: No
                                """

        # Few-shot examples for paragraph-level classification
        self.paragraph_few_shot = """
                                    You are an expert chemist.
                                    Determine if each paragraph below is a detailed chemical reaction description. 
                                    Answer strictly with "Yes" or "No".

                                    Example 1:
                                    Paragraph: "A mixture of benzaldehyde and acetone was stirred under reflux for 5 hours, then cooled and crystallized."
                                    Answer: Yes

                                    Example 2:
                                    Paragraph: "The mechanism of aldol condensation has been studied extensively in textbooks."
                                    Answer: No
                                """

    # ---------------------------
    # Token counting utilities
    # ---------------------------
    @staticmethod
    def count_tokens(text, model="gpt-4"):
        """Estimate token count for a text string."""
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))

    def suggest_batch_size(self, items, few_shot, model=None):
        """Suggest max safe batch size for classification."""
        MODEL_CONTEXT = {
            "gpt-4": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16384, "gpt-3.5-turbo-16k": 16384,
        }
        if model is None:
            model = self.model
        if model not in MODEL_CONTEXT:
            raise ValueError(f"Unknown model: {model}")

        base_tokens = self.count_tokens(few_shot, model)

        avg_tokens = (
            sum(self.count_tokens(x, model) for x in items) / len(items)
            if items else 50
        )
        avg_tokens += 15  # overhead for numbering + labels

        context_limit = MODEL_CONTEXT[model]
        usable_limit = int(context_limit * self.safety_margin)

        max_batch = int((usable_limit - base_tokens) / (avg_tokens + 10))  # +10 for output
        return max(1, min(max_batch, len(items)))

    # ---------------------------
    # Step 1: Keyword filter
    # ---------------------------
    def keyword_filter(self, subtitle_modules, keywords=None):
        if keywords is None:
            keywords = ["synthesis", "example", "method", 'reaction', 'experiment', 'experimental'
                                                                                    'examples', 'methods', 'Synthesis',
                        'Example', 'Method', 'Reaction', 'Experiment', 'Experimental',
                        'Examples', 'Methods', 'Reaction']

        return [
            sm for sm in subtitle_modules
            if any(kw.lower() in sm.subtitle.lower() for kw in keywords)
        ]

    # ---------------------------
    # Step 2: AI filter subtitles
    # ---------------------------
    def ai_filter_subtitles(self, subtitle_modules, exclude_modules=None):
        """Run AI subtitle filter on modules, skipping exclude_modules if provided."""
        if exclude_modules is None:
            exclude_modules = []

        exclude_set = set(exclude_modules)
        kept_modules = []

        # Work only on subtitle_modules not in exclude_modules
        for sm in subtitle_modules:
            if sm in exclude_set:
                continue

            leading_para = sm.para_objects[0].contents if sm.para_objects else ""
            prompt = (
                    self.subtitle_few_shot
                    + f"""

    Now analyze the following case:

    Subtitle: "{sm.subtitle}"
    Paragraph: "{leading_para}"
    Answer:
    """
            )
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip()
            if answer.lower().startswith("yes"):
                kept_modules.append(sm)
        return kept_modules

    # ---------------------------
    # Step 3: AI filter paragraphs
    # ---------------------------
    def ai_filter_paragraphs(self, subtitle_module):
        paragraphs = subtitle_module.para_objects
        selected_paragraphs = []

        # auto-batch size if not set manually
        batch_size = self.batch_size or self.suggest_batch_size(
            [p.contents for p in paragraphs],
            self.paragraph_few_shot,
            model=self.model
        )

        for i in range(0, len(paragraphs), batch_size):
            batch = paragraphs[i:i + batch_size]

            # Build query
            query = self.paragraph_few_shot + "\nNow analyze these paragraphs:\n\n"
            for idx, para in enumerate(batch, start=1):
                query += f"{idx}. Paragraph: \"{para.contents}\"\n"
            query += "\nProvide answers in the format:\n1. Yes\n2. No\n..."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": query}]
            )

            outputs = response.choices[0].message.content.strip().splitlines()
            answers = [line.split(".")[-1].strip() for line in outputs if line.strip()]

            for para, ans in zip(batch, answers):
                if ans.lower().startswith("yes"):
                    selected_paragraphs.append(para)

        return selected_paragraphs

    # ---------------------------
    # Master pipeline run this
    # ---------------------------
    def select_reaction_paragraphs(self, subtitle_modules):
        # Step 1: keyword filter
        step1_modules = self.keyword_filter(subtitle_modules)

        keywords_subtitle_names = []
        for sm in subtitle_modules:
            keywords_subtitle_names.append(sm.subtitle)
        print('keywords_subtitle_names:', keywords_subtitle_names)

        # Step 2: AI filter, applied only on the rest
        step2_modules = self.ai_filter_subtitles(subtitle_modules, exclude_modules=step1_modules)

        # Combine both sets
        combined_modules = step1_modules + step2_modules
        all_selected_subtitle_names = []
        for sm in combined_modules:
            all_selected_subtitle_names.append(sm.subtitle)
            print('all_selected_subtitle_names:', all_selected_subtitle_names)

        results = {}
        for sm in combined_modules:
            paras = self.ai_filter_paragraphs(sm)
            if paras:
                results[sm.subtitle] = paras

        return results  # the returning is  dict {subtitle:reaction_paragraph_list}
