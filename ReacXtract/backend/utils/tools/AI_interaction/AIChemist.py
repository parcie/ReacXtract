import pubchempy as pcp
import openai
from openai import OpenAI
import json
import re
from py2opsin import py2opsin



# for GPT models include [4.1, 4.1-mini, 4o,4.1-preview],[3.5, 4,3.5-turbo],[5]
class AIChemist_gpt:

    def __init__(self,model_name,api_key):
        self.model_name = model_name
        self.api_key = api_key
        openai.base_url = 'https://kapkey.chatgptapi.org.cn/v1/'
        self.client = OpenAI(api_key=self.api_key)
        return None

    # add a paragraph judgement

    # Generic chemist Q&A template with JSON enforcement
    def chemist_template(self, question, reaction_description, requires, max_tokens: int = 300):
        '''
        give a template for chemical questions to fix model parameters
        Args:
            question(string)
            reaction_description(string)
            requires(string)
            max_tokens(int), if needed
        Returns:
            dict: return the dict
        '''
        api_key = self.api_key
        def type1_format(client,question,reaction_description,requires,max_tokens: int=300):
        # for gpt-4.1, gpt-4.1-mini,gpt-4o
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert chemist. You must only extract exact words/phrases that are explicitly present in the given description. Do not infer, expand, or guess chemical names. If nothing is found, return unknown.Return ONLY valid JSON."},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": reaction_description},
                    {"role": "user", "content": f"Return ONLY valid JSON. {requires}"}
                ],
                n=1,
                max_tokens=max_tokens,
                top_p=0.5,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                response_format={"type": "json_object"}  #  enforce JSON
            )

            # Parse JSON safely
            try:
                answer = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                answer = {"error": "Invalid JSON returned"}
            return answer

        def type2_format(client,question,reaction_description,requires,max_tokens: int=300):
            # for gpt4 gpt-3.5-turbo
            model_name = self.model_name
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": "You are an expert chemist. ALWAYS respond in strict JSON. No extra text."},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": reaction_description},
                    {"role": "user", "content": f"Return ONLY valid JSON. {requires}"}
                ],
                n=1,
                max_tokens=max_tokens,
                top_p=0.5,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )

            content = response.choices[0].message.content.strip()
            # --- post-process: extract JSON safely
            try:
                return json.loads(content)
            except:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        return {}

        def type3_format(client,question,reaction_description,requires,max_tokens: int=300):
            # for gpt5 model
            model_name = self.model_name
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=model_name,
                input=[
                    {"role": "system",
                     "content": "You are an expert chemist. ALWAYS respond in strict JSON. No extra text."},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": reaction_description},
                    {"role": "user", "content": f"Return ONLY valid JSON. {requires}"}
                ],
                n=1,
                reasoning = {"effort":"minimal"},
                text = {"verbosity": "low"},
                max_output_tokens = max_tokens,
                response_format={"type": "json"},
                stop=None
            )
            content = response.output_text.strip()
            try:
                return json.loads(content)
            except:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        return {}

        model_name = self.model_name
        client = OpenAI(api_key=api_key)
        former_models = ['gpt-3.5', 'gpt-4', 'gpt-3.5-turbo']
        latest_models = ['gpt-4.1', 'gpt-4.1-min', 'gpt-4o','gpt-5','gpt-4.1-preview']
        gpt5 = ['gpt-5']

        if model_name in former_models:
            answer = type2_format(client,question,reaction_description,requires)
            return answer
        elif model_name in latest_models:
            answer = type1_format(client,question,reaction_description,requires)
            return answer
        elif model_name in gpt5:
            answer = type3_format(client,question,reaction_description,requires)
            return answer
        else:
            return({'error':"model not found"})


    def extract_product_from_para(self, reaction_description):
        '''
        Args:
            reaction_description(string)
        Returns:
            list: products names(string) in list
        '''
        question_product = (
            "Here is a chemical reaction procedure description. "
            "Please identify the product(s). Exclude catalysts, solvents, and reactants."
        )
        requires_product = (
            'Return JSON in the format: {"products": ["A", "B", "C"]}. '
            'If unknown, return {"products": ["unknown"]}.'
        )

        product_json = self.chemist_template(question_product, reaction_description, requires_product)

        # Always return a list of product names
        return product_json.get("products", ["unknown"])

    def extract_reactants_from_para(self, reaction_description):
        question_reactants = (
            "Here is a chemical reaction procedure description. "
            "Please identify the reactant(s). Exclude catalysts, solvents, and products."
        )
        requires_reactants = (
            'Return JSON in the format: {"reactants": ["A", "B", "C"]}. '
            'If unknown, return {"reactants": ["unknown"]}.'
        )

        reactants_json = self.chemist_template(question_reactants, reaction_description, requires_reactants)

        return reactants_json.get("reactants", ["unknown"])

    def extract_catalyst_from_para(self, reaction_description):
        question_catalyst = (
            "Here is a chemical reaction procedure description. "
            "Please identify the catalyst(s). Exclude reactants, solvents, and products."
        )
        requires_catalyst = (
            'Return JSON in the format: {"catalyst": ["A", "B", "C"]}. '
            'If unknown, return {"catalyst": ["unknown"]}.'
        )

        catalyst_json = self.chemist_template(question_catalyst, reaction_description, requires_catalyst)

        return catalyst_json.get("catalyst", ["unknown"])

    def extract_other_reagents_from_para(self, reaction_description):
        question_other_reagents = (
            "Here is a chemical reaction procedure description. "
            "Please identify the other reagent(s) participate in this reaction , be careful to exclude reactants, solvents, catalyst, gas environment ,products."
        )
        requires_other_reagents = (
            'Return JSON in the format: {"other_reagents": ["A", "B", "C"]}. '
            'If unknown, return {"other_reagents": ["unknown"]}.'
        )
        other_reagents_json = self.chemist_template(question_other_reagents, reaction_description, requires_other_reagents)

        return other_reagents_json.get("other_reagents", ["unknown"])

    def extract_solvent_from_para(self, reaction_description):
        question_solvent = (
            "Here is a chemical reaction procedure description. "
            "Please identify the solvent(s) when the reaction react, exclude reactants, solvents, catalyst, and products.if the solvent is a mixture, return the related description words or strings"
        )
        requires_solvent = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"solvent": "DCM"} or {"solvent":"ethanol and water(5:1)"} or {""solvent:"related string"}\n\n'
            "If the solvent is not mentioned, return:\n"
            '{"yield": "unknown"}\n\n'
        )
        solvent_json = self.chemist_template(question_solvent, reaction_description, requires_solvent)

        return solvent_json.get("solvent", ["unknown"])

    def extract_gas_environ_from_para(self, reaction_description):
        question_gas = (
            "Here is a chemical reaction procedure description. "
            "Please identify the gas environment, exclude reactants, solvents, catalyst, products and other reagents."
        )
        requires_gas = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"gas": "nitrogen"}\n\n'
            "If the gas environment is not mentioned, return:\n"
            '{"gas": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )
        gas_json = self.chemist_template(question_gas, reaction_description, requires_gas)
        gas_value = gas_json.get("gas", ["unknown"])
        if isinstance(gas_value, str):
            gas_value = gas_value.replace("atmosphere", "").strip()
        return gas_value if gas_value else "unknown"

    def extract_reacting_temperature_from_para(self, reaction_description):
        question_T = (
            "Here is a chemical reaction procedure description. "
            "Please identify the reacting temperature, if there are stages with different temperature, all returned.please return with units.if the temperature is room temperature, return 298.15K."
        )
        requires_T = (
            'Return JSON in the format: {"temperature": ["180K", "298K", "330K"]}. '
            'If unknown, return {"temperature": ["unknown"]}.'
        )
        T_json = self.chemist_template(question_T, reaction_description, requires_T)
        return T_json.get("temperature", ["unknown"])

    def extract_reacting_time_from_para(self, reaction_description):
        question_time = (
            "Here is a chemical reaction procedure description. "
            "Please identify the reacting time,if there are multi-steps, all time returned by stage. please return with units.if the time is by TLC,just return by TLC."
        )
        requires_time = (
            'Return JSON in the format: {"time": ["A", "B", "C"]}. '
            'If unknown, return {"time": ["unknown"]}.'
        )
        time_json = self.chemist_template(question_time, reaction_description, requires_time)
        return time_json.get("time", ["unknown"])

    def extract_yield(self, reaction_description):
        question_yield = (
            "Here is a chemical reaction procedure description. "
            "Please identify the reaction yield as reported in the text."
        )
        requires_yield = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"yield": "64%"}\n\n'
            "If the yield is not mentioned, return:\n"
            '{"yield": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        yield_json = self.chemist_template(question_yield, reaction_description, requires_yield)
        return yield_json.get("yield", "unknown")

    def extract_mol(self, compound_name, reaction_description):
        question_mol = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me the number of moles of {compound_name} in this reaction."
        )
        requires_mol = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            f'{{"mol": "15 mmol"}}\n\n'
            "If the moles are not mentioned in this text, return:\n"
            '{"mol": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        mol_json = self.chemist_template(question_mol, reaction_description, requires_mol)
        if isinstance(mol_json, dict):
            return mol_json.get("mol", "unknown")
        try:
            return json.loads(mol_json).get("mol", "unknown")
        except:
            match = re.search(r"\{.*\}", str(mol_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("mol", "unknown")
                except:
                    return "unknown"
            return "unknown"



    def extract_chemical_conditions(self, compound_name, reaction_description):
        valid_states = ['solid', 'solution', 'liquid', 'gas']

        question_cond = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell if {compound_name} is solid, pure liquid, solution, or gas."
        )
        requires_cond = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"state": "solid"}\n\n'
            "If the state is not mentioned, return:\n"
            '{"state": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        cond_json = self.chemist_template(question_cond, reaction_description, requires_cond)

        # Try to parse the JSON
        state = "unknown"
        if isinstance(cond_json, dict):
            state = cond_json.get("state", "unknown")
        else:
            try:
                state = json.loads(cond_json).get("state", "unknown")
            except:
                match = re.search(r"\{.*\}", str(cond_json), re.DOTALL)
                if match:
                    try:
                        state = json.loads(match.group(0)).get("state", "unknown")
                    except:
                        state = "unknown"

        # Normalize output: lowercase and remove whitespace
        if isinstance(state, str):
            state = state.strip().lower()
        # Strictly enforce valid states
        if state not in valid_states:
            state = "unknown"
        return state

    def extract_mass(self, compound_name, reaction_description):
        question_mass = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me the mass of {compound_name}."
        )
        requires_mass = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"mass": "5 g"}\n\n'
            "If the mass is not mentioned in the text, return:\n"
            '{"mass": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        mass_json = self.chemist_template(question_mass, reaction_description, requires_mass)
        if isinstance(mass_json, dict):
            return mass_json.get("mass", "unknown")
        try:
            return json.loads(mass_json).get("mass", "unknown")
        except:
            match = re.search(r"\{.*\}", str(mass_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("mass", "unknown")
                except:
                    return "unknown"
            return "unknown"

    def extract_mass_purity(self, compound_name, reaction_description):
        question_purity = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me if {compound_name} is pure or impure. "
            "If pure, return 100%. If impure, return the content value (e.g., 58%, 7 mol/g)."
        )
        requires_purity = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"purity": "100%"}\n\n'
            "If impure with known concentration, return e.g.:\n"
            '{"purity": "58%"} or {"purity":58w%}\n\n'
            "If impure without concentration mentioned in the given text, return:\n"
            '{"purity": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        purity_json = self.chemist_template(question_purity, reaction_description, requires_purity)
        if isinstance(purity_json, dict):
            return purity_json.get("purity", "unknown")
        try:
            return json.loads(purity_json).get("purity", "unknown")
        except:
            match = re.search(r"\{.*\}", str(purity_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("purity", "unknown")
                except:
                    return "unknown"
            return "unknown"

    def extract_solution_concentration(self, compound_name, reaction_description):
        question_conc = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me the concentration of {compound_name}. "
            "Return with unit (e.g., 1.5 mol/L, 0.3 g/mL, 55%)."
        )
        requires_conc = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"concentration": "1.5 mol/L"}\n\n'
            "If the concentration is not mentioned, return:\n"
            '{"concentration": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        conc_json = self.chemist_template(question_conc, reaction_description, requires_conc)
        if isinstance(conc_json, dict):
            return conc_json.get("concentration", "unknown")
        try:
            return json.loads(conc_json).get("concentration", "unknown")
        except:
            match = re.search(r"\{.*\}", str(conc_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("concentration", "unknown")
                except:
                    return "unknown"
            return "unknown"

    def extract_volume(self, compound_name, reaction_description):
        question_vol = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me the volume of {compound_name}."
        )
        requires_vol = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"volume": "5.2 mL"}\n\n'
            "If the volume is not mentioned in the given text, return:\n"
            '{"volume": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        vol_json = self.chemist_template(question_vol, reaction_description, requires_vol)
        if isinstance(vol_json, dict):
            return vol_json.get("volume", "unknown")
        try:
            return json.loads(vol_json).get("volume", "unknown")
        except:
            match = re.search(r"\{.*\}", str(vol_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("volume", "unknown")
                except:
                    return "unknown"
            return "unknown"

    def extract_equiv(self, compound_name, reaction_description):
        question_equiv = (
            f"Here is a chemical reaction procedure description. "
            f"Please tell me the reacting equivalence of {compound_name}."
        )
        requires_equiv = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"equiv": "1.2"}\n\n'
            "If the volume is not mentioned in the given text, return:\n"
            '{"equiv.": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        equiv_json = self.chemist_template(question_equiv, reaction_description, requires_equiv)
        if isinstance(equiv_json, dict):
            return equiv_json.get("equiv", "unknown")
        try:
            return json.loads(equiv_json).get("equiv", "unknown")
        except:
            match = re.search(r"\{.*\}", str(equiv_json), re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0)).get("equiv", "unknown")
                except:
                    return "unknown"
            return "unknown"

    def extract_post_processing(self, reaction_description):
        question_postproc = (
            "Here is a chemical reaction procedure description. "
            "Please extract ONLY the post-processing (workup and purification) steps. "
            "Exclude reaction setup and conditions (temperature, atmosphere, stirring, solvents used for reaction, etc.). "
            "Include steps such as quenching, extraction, washing, drying, filtration, evaporation, chromatography, recrystallization, and any other purification operations."
        )

        requires_postproc = (
            "Return ONLY valid JSON. Strictly follow this format:\n"
            '{"post_processing": "extracted text of post-processing steps"}\n\n'
            "If post-processing is not described, return:\n"
            '{"post_processing": "unknown"}\n\n'
            "Do not include any explanation, text, or sentences outside of the JSON."
        )

        postproc_json = self.chemist_template(question_postproc, reaction_description, requires_postproc)
        return postproc_json.get("post_processing", "unknown")


    def reflect_reaction(self, raw_json: dict, detected_issues: list, max_tokens: int = 800):
        """
        Perform semantic re-evaluation and correction of reaction JSON.

        Parameters
        ----------
        raw_json : dict
            Original extracted reaction JSON.
        detected_issues : list
            Rule-based validation issues.
        max_tokens : int
            Max tokens for response.

        Returns
        -------
        dict
            Corrected reaction JSON (guaranteed dict or error object).
        """

        system_prompt = """
You are an expert synthetic chemist performing semantic validation
and correction of structured reaction JSON data.

Rules:
- A chemical species must appear in only ONE role.
- Remove duplicated species across roles.
- Fix obvious role misclassification.
- Catalyst loading above 20 mol% is suspicious unless justified.
- Preserve original information unless clearly incorrect.
- Do NOT invent new chemicals.
- Return ONLY valid JSON.
- Do NOT include explanations or commentary.
"""

        user_prompt = f"""
RAW REACTION JSON:
{json.dumps(raw_json, indent=2)}

DETECTED RULE-BASED ISSUES:
{json.dumps(detected_issues, indent=2)}

Return the FULL corrected reaction JSON.
The output MUST contain all original top-level fields.
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        # Defensive JSON parsing
        try:
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2)

        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {"error": "Invalid JSON returned by LLM"}



'''
    def extract_multi_procedures(self, reaction_description):
        question_multi_proc =

    def is_one_pot(self,reaction_description):
'''


class Transfering_tools:

    def __init__(self):
        return None

    @staticmethod
    def is_chemical(entity):
        try:
            compounds = pcp.get_compounds(entity, 'name')  # search by name or synonym
            return len(compounds) > 0
        except Exception as e:
            return False

    # below are name-iupac-smiles transfer functions
    @staticmethod
    def common_name_to_iupac(common_name):
        try:
            compounds = pcp.get_compounds(common_name, 'name')
            if compounds and compounds[0].iupac_name:
                return compounds[0].iupac_name
            else:
                return "unknown"
        except Exception:
            return "unknown"

    @staticmethod
    def name_to_smiles(compound_name):
        # Try OPSIN first
        smiles = py2opsin(chemical_name=compound_name, output_format="SMILES")
        if smiles:
            return smiles

        # Try PubChem fallback
        else:
            is_iupac = Transfering_tools.is_iupac(compound_name)
            if is_iupac:
                try:
                    compounds = pcp.get_compounds(compound_name, 'name')
                    if compounds and compounds[0].canonical_smiles:
                        return compounds[0].canonical_smiles
                except Exception:
                    pass
            else:
                iupac_name = Transfering_tools.common_name_to_iupac(compound_name)
                if iupac_name == "unknown":
                    return "unknown"
                else:
                    try:
                        compounds = pcp.get_compounds(iupac_name, 'name')
                        if compounds and compounds[0].canonical_smiles:
                            return compounds[0].canonical_smiles
                    except Exception:
                        pass
        return "unknown"

    @staticmethod
    def smiles_to_name(compound_smiles):
        '''
        SMILES TO IUPAC name,return string
        '''
        result = pcp.get_compounds(compound_smiles, 'smiles')
        if result:
            molecule = result[0]
            iupac_name = molecule.iupac_name
        else:
            iupac_name=''
        return iupac_name

    @staticmethod
    def is_iupac(name: str) -> bool:
        """
        Judge whether a chemical name is an IUPAC name.
        Returns True if the name looks like IUPAC, else False.
        """
        # 1. Try OPSIN parsing (only IUPAC names succeed)
        try:
            smiles = py2opsin(name, output_format="SMILES")
            if smiles:  # OPSIN only understands IUPAC
                return True
        except Exception:
            pass

        # 2. Try PubChem lookup and compare
        try:
            compounds = pcp.get_compounds(name, 'name')
            if compounds and compounds[0].iupac_name:
                if compounds[0].iupac_name.lower() == name.lower():
                    return True
        except Exception:
            pass

        return False


