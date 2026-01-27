from py2opsin import py2opsin
import pubchempy as pcp
import warnings
from warnings import catch_warnings
from rdkit import Chem
from rdkit.Chem import Descriptors
import openai

openai.api_key = 'sk-aztnCaBvBNFtaM5pF10aFcEc7e714b42969dFeFf29074a3d'
openai.base_url = 'https://kapkey.chatgptapi.org.cn/v1/'

class AIChemists:

    def __init__(self):
        return

    def answer_template(self, question: str, reaction_description: str="", requires: str="", max_tokens: int = 100):
        """
        :type reaction_description: string
        """
        completion = openai.chat.completions.create(model="gpt-4",
        message=[
        {"role":"system","content":"You are an expert chemist and your task is to respond to the question. "},
        {"role":"user","content":question},
        {"role":"assistant","content":reaction_description},
        {"role":"user","content":f"please try you best! {requires}"}],
        temperature=0,
        max_tokens=max_tokens,
        top_p=0.5,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None)
        answer=completion.choices[0].message.content
        return answer