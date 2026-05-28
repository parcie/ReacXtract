import json
from utils.tools.AI_interaction.AIChemist import AIChemist_gpt
from utils.tools.AI_interaction.AIChemist import Transfering_tools
import pubchempy as pcp

# 输入文字段落输出反应json 完成测试！！！！！！！！！！！！！！

class Reaction:
    def __init__(self):
        """Initialize a blank reaction object."""
        self.data = {
            "reactants": [],
            "products": [],
            "catalysts": [],
            "solvents": [],
            "other_chemicals": [],
            "gas": [],
            "time": [],
            "temperature": [],
            "yield": None,
            "post_processing": None,
            "notes": None
        }

    # --- Add chemicals ---
    def add_reactant(self, name, dosage=None, mols=None, equivalence=None, smiles=None, label=None):
        self.data["reactants"].append({
            "name": name,
            "label": label,
            "SMILES": smiles,
            "dosage": dosage,
            "mols": mols,
            "equivalence": equivalence
        })

    def add_product(self, name, dosage=None, mols=None, yield_percent=None, smiles=None, label=None):
        self.data["products"].append({
            "name": name,
            "label": label,
            "SMILES": smiles,
            "dosage": dosage,
            "mols": mols,
            "yield": yield_percent
        })

    def add_catalyst(self, name, dosage=None, mols=None, smiles=None, label=None,equivalence=None):
        self.data["catalysts"].append({
            "name": name,
            "label": label,
            "SMILES": smiles,
            "dosage": dosage,
            "mols": mols,
            "equivalence": equivalence
        })

    def add_solvent(self, name, dosage=None, smiles=None):
        self.data["solvents"].append({
            "name": name,
            "SMILES": smiles,
            "dosage": dosage
        })

    def add_other_chemical(self, name, dosage=None, mols=None, smiles=None, label=None,equivalence=None):
        self.data["other_chemicals"].append({
            "name": name,
            "label": label,
            "SMILES": smiles,
            "dosage": dosage,
            "equivalence": equivalence,
            "mols": mols
        })
    def add_environment(self, name, dosage=None, mols=None, smiles=None, label=None):
        self.data["gas"].append({
            "name": name,
            "label": label,
            "SMILES": smiles,
            "dosage": dosage,
            "mols": mols
        })
    # --- Set metadata ---
    def set_conditions(self, time=None, temperature=None):
        self.data["time"] = time
        self.data["temperature"] = temperature


    def set_yield(self, yield_percent):
        self.data["yield"] = yield_percent

    def set_post_processing(self, description):
        self.data["post_processing"] = description

    def set_notes(self, notes):
        self.data["notes"] = notes

    # --- Getters ---
    def get_reactants(self, names_only=False):
        """Return all reactants. If names_only=True, return just their names."""
        if names_only:
            return [r["name"] for r in self.data["reactants"]]
        return self.data["reactants"]

    def get_products(self, names_only=False):
        """Return all products. If names_only=True, return just their names."""
        if names_only:
            return [p["name"] for p in self.data["products"]]
        return self.data["products"]

    def get_summary(self):
        """Return everything except reactants and products."""
        summary = self.data.copy()
        summary.pop("reactants", None)
        summary.pop("products", None)
        return summary

    # --- Utility ---
    def to_dict(self):
        """Return full reaction as dictionary (for JSON export)."""
        return self.data

    def __repr__(self):
        """Pretty representation for quick inspection."""
        import pprint
        return pprint.pformat(self.data, indent=2, width=80)


# this is without reflection and other fixation  RELECTION

class ReactionExtractor:
    def __init__(self, model_name, api_key, transfer_tool):
        self.chemist = AIChemist_gpt(model_name, api_key)
        self.transfer_tool = transfer_tool  # e.g. Transfering_tools

    # stage judgement for dosage units choices
    def get_dosgae(self, name,paragraph):
        state = self.chemist.extract_chemical_conditions(name, paragraph)

        if state == 'solid':
            mass = self.chemist.extract_mass(name, paragraph)
            purity = self.chemist.extract_mass_purity(name, paragraph)
            if purity == 'unknown':
                purity = 'pure'
                dosage = {'mass': mass, 'purity': purity}
            else:
                dosage = {'mass': mass, 'purity': purity}
        elif state == 'liquid':

            mass = self.chemist.extract_mass(name, paragraph)
            volume = self.chemist.extract_volume(name, paragraph)
            concentration = self.chemist.extract_solution_concentration(name, paragraph)
            if concentration == 'unknown':
                concentration = 'pure'
                dosage = {'volume': volume, 'concentration': concentration, 'mass': mass}
            else:
                dosage = {'volume': volume, 'concentration': concentration,'mass': mass}
        elif state == 'solution':

            mass = self.chemist.extract_mass(name, paragraph)
            volume = self.chemist.extract_volume(name, paragraph)
            concentration = self.chemist.extract_solution_concentration(name, paragraph)
            dosage = {'volume': volume, 'concentration': concentration,'mass': mass}
        elif state == 'gas':

            volume = self.chemist.extract_volume(name, paragraph)
            purity = self.chemist.extract_mass_purity(name, paragraph)
            if purity == 'unknown':
                purity = 'pure'
                dosage = {'volume': volume, 'purity': purity}
            else:
                dosage = {'volume': volume, 'purity': purity}
        else:

            mass = self.chemist.extract_mass(name, paragraph)
            volume = self.chemist.extract_volume(name, paragraph)
            concentration = self.chemist.extract_solution_concentration(name, paragraph)
            purity = self.chemist.extract_mass_purity(name, paragraph)
            dosage = {'purity':purity,'volume': volume, 'concentration': concentration,'mass': mass}
        return dosage

    #def chemical_info(self,para):
    # decided whether the  entity is chemical
    def build_reaction(self, paragraph: str) -> Reaction:
        """Extract reaction info from paragraph and build a Reaction object."""
        reaction = Reaction()

        # --- Extract species ---
        reactants = self.chemist.extract_reactants_from_para(paragraph)
        products = self.chemist.extract_product_from_para(paragraph)
        catalysts = self.chemist.extract_catalyst_from_para(paragraph)
        solvents = self.chemist.extract_solvent_from_para(paragraph)
        others = self.chemist.extract_other_reagents_from_para(paragraph)

        # --- Extract metadata ---
        gas = self.chemist.extract_gas_environ_from_para(paragraph)

        temperature = self.chemist.extract_reacting_temperature_from_para(paragraph)
        time = self.chemist.extract_reacting_time_from_para(paragraph)
        yield_percent = self.chemist.extract_yield(paragraph)
        post_proc = self.chemist.extract_post_processing(paragraph)

        # --- Fill reaction object ---
        # get reactants with name or label, SMILES, Dosage(mass/volume/c), moles, equuiv
        for r in reactants:
            chemical_judgement = self.transfer_tool.is_chemical(r)
            if chemical_judgement is False:
                label = r
                name = 'unknown'
                smiles = ''
            else:
                name = r
                iupac_name_judgement = self.transfer_tool.is_iupac(r)
                label = 'unknown'
                if iupac_name_judgement:
                    smiles = self.transfer_tool.name_to_smiles(r)
                else:
                    iupac_name = Transfering_tools.common_name_to_iupac(r)
                    smiles = self.transfer_tool.name_to_smiles(iupac_name)
            if name in ('unknown', '',' ') and label in ('unknown', '',' '):
                continue
            elif name is None and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            elif name in ('unknown', '',' ') and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            else:
                mols = self.chemist.extract_mol(r, paragraph)
                equiv = self.chemist.extract_equiv(r, paragraph)
                dosage = self.get_dosgae(r, paragraph)

            reaction.add_reactant(name=name,label=label, mols=mols, equivalence=equiv,
                                      smiles=smiles, dosage=dosage)

        for p in products:
            chemical_judgement = self.transfer_tool.is_chemical(p)
            if chemical_judgement is False:
                label = p
                name = 'unknown'
                smiles = ''
            else:
                name = p
                iupac_name_judgement = self.transfer_tool.is_iupac(p)
                label = 'unknown'
                if iupac_name_judgement:
                    smiles = self.transfer_tool.name_to_smiles(p)
                else:
                    iupac_name = Transfering_tools.common_name_to_iupac(p)
                    smiles = self.transfer_tool.name_to_smiles(iupac_name)

            mols = self.chemist.extract_mol(p, paragraph)
            dosage = self.get_dosgae(p, paragraph)
            reaction.add_product(name=name, label=label,smiles=smiles,mols=mols, yield_percent=yield_percent,dosage=dosage)

        # cata filling
        for c in catalysts:
            chemical_judgement = self.transfer_tool.is_chemical(c)
            if chemical_judgement is False:
                label = c
                name = 'unknown'
                smiles = ''
            else:
                name = c
                iupac_name_judgement = self.transfer_tool.is_iupac(c)
                label = 'unknown'
                if iupac_name_judgement:
                    smiles = self.transfer_tool.name_to_smiles(c)
                else:
                    iupac_name = Transfering_tools.common_name_to_iupac(c)
                    smiles = self.transfer_tool.name_to_smiles(iupac_name)
            if name in ('unknown', '',' ') and label in ('unknown', '',' '):
                continue
            elif name is None and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            elif name in ('unknown', '',' ') and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            else:
                mols = self.chemist.extract_mol(c, paragraph)
                equiv = self.chemist.extract_equiv(c, paragraph)
                dosage = self.get_dosgae(c, paragraph)
            reaction.add_catalyst(name=name,label=label,smiles=smiles,mols=mols, equivalence=equiv,dosage=dosage)

        #other reagent filling
        for o in others:
            chemical_judgement = self.transfer_tool.is_chemical(o)
            if chemical_judgement is False:
                label = o
                name = 'unknown'
                smiles = ''
            else:
                name = o
                iupac_name_judgement = self.transfer_tool.is_iupac(o)
                label = 'unknown'
                if iupac_name_judgement:
                    smiles = self.transfer_tool.name_to_smiles(o)
                else:
                    iupac_name = Transfering_tools.common_name_to_iupac(o)
                    smiles = self.transfer_tool.name_to_smiles(iupac_name)
            if name in ('unknown', '',' ') and label in ('unknown', '',' '):
                continue
            elif name is None and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            elif name in ('unknown', '',' ') and label is None:
                continue
            elif name is None and label in ('unknown', '',' '):
                continue
            else:
                mols = self.chemist.extract_mol(o, paragraph)
                equiv = self.chemist.extract_equiv(o, paragraph)
                dosage = self.get_dosgae(o, paragraph)
            reaction.add_other_chemical(name=name,label=label,smiles=smiles,mols=mols, equivalence=equiv,dosage=dosage)

        # solvent filling
        if solvents in ('unknown', '',' '):
            reaction.add_solvent(name=None)
        elif solvents is None:
            reaction.add_solvent(name=None)
        else:
            chemical_judgement = self.transfer_tool.is_chemical(solvents)
            if chemical_judgement:
                iupac_name = Transfering_tools.common_name_to_iupac(solvents)
                smiles_solvents = self.transfer_tool.name_to_smiles(iupac_name)
            else:
                smiles_solvents = ''
            mass_solvents = self.chemist.extract_mol(solvents, paragraph)
            vol_solvents = self.chemist.extract_volume(solvents, paragraph)
            dosage_solvents = {"mass": mass_solvents, "volume": vol_solvents}

            if smiles_solvents != "":
                reaction.add_solvent(name=solvents, smiles=smiles_solvents, dosage=dosage_solvents)
            else:
                reaction.add_solvent(name=solvents, smiles='', dosage=dosage_solvents)

        # add gas environment
        if gas in ('unknown', '',' '):
            reaction.add_environment(name=None)
        elif gas is None:
            reaction.add_environment(name=None)
        else:
            smiles_gas = self.transfer_tool.name_to_smiles(gas)
            vol_gas = self.chemist.extract_mol(gas, paragraph)
            dosage_gas = {'volume': vol_gas}
            if smiles_gas != "":
                reaction.add_environment(name=gas, smiles=smiles_gas,dosage=dosage_gas)
            else:
                reaction.add_environment(name=gas, smiles='',dosage=dosage_gas)

        # --- Set global conditions ---

        reaction.set_conditions(time=time, temperature=temperature)
        reaction.set_yield(yield_percent)
        reaction.set_post_processing(post_proc)

# condition checking and reflection

        return reaction

    def to_json(self, reaction: Reaction, filepath=None):
        """Export reaction as JSON string or file."""
        data = reaction.to_dict()
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        return json.dumps(data, indent=2, ensure_ascii=False)

from collections import defaultdict


class ReactionValidator:

    def __init__(self, reaction, model_name, api_key):
        """
        reaction: Reaction object
        chemist: optional AIChemist_gpt instance for deep semantic reflection
        """
        self.reaction = reaction
        self.chemist = AIChemist_gpt(model_name, api_key)
        self.issues = []

    # =========================================================
    # 1️⃣ Duplicate Species Check
    # =========================================================

    def validate_duplicates(self):
        seen = {}
        for role in ["reactants", "products", "catalysts", "other_chemicals"]:
            for item in self.reaction.data.get(role, []):
                key = item.get("SMILES") or item.get("name")

                if not key or key in ("unknown", "", None):
                    continue

                if key in seen:
                    self.issues.append({
                        "type": "duplicate_species",
                        "species": key,
                        "roles": [seen[key], role]
                    })
                else:
                    seen[key] = role

    # =========================================================
    # 2️⃣ Role Conflict Check
    # =========================================================

    def validate_role_conflicts(self):
        from collections import defaultdict

        role_map = defaultdict(list)

        for role in ["reactants", "products", "catalysts", "solvents", "other_chemicals"]:
            for item in self.reaction.data.get(role, []):
                name = item.get("name")

                if not name:
                    continue

                # Fix unhashable list issue
                if isinstance(name, list):
                    name = ", ".join(map(str, name))

                if name in ("unknown", "", None):
                    continue

                role_map[name].append(role)

        for name, roles in role_map.items():
            if len(set(roles)) > 1:
                self.issues.append({
                    "type": "role_conflict",
                    "species": name,
                    "roles": roles
                })

    # =========================================================
    # 3️⃣ Catalyst Loading Plausibility
    # =========================================================

    def validate_catalyst_loading(self, max_reasonable_loading=0.5):
        """
        Flags catalyst if loading > 50% of limiting reagent.
        """

        reactants = self.reaction.data.get("reactants", [])
        catalysts = self.reaction.data.get("catalysts", [])

        mol_values = []
        for r in reactants:
            if r.get("mols"):
                try:
                    mol_values.append(float(r["mols"]))
                except:
                    pass

        if not mol_values:
            return

        limiting = min(mol_values)

        for c in catalysts:
            if not c.get("mols"):
                continue

            try:
                loading = float(c["mols"]) / limiting
            except:
                continue

            if loading > max_reasonable_loading:
                self.issues.append({
                    "type": "suspicious_catalyst_loading",
                    "species": c.get("name"),
                    "loading_fraction": loading
                })

    # =========================================================
    # Run Minimal Validation
    # =========================================================

    def validate_minimal(self):
        self.issues = []

        self.validate_duplicates()
        self.validate_role_conflicts()
        self.validate_catalyst_loading()

        return self.issues

    # =========================================================
    # 4️⃣ Deep Semantic Re-evaluation (LLM Reflection)
    # =========================================================

    def reflect_with_llm(self):
        chemist = self.chemist
        reaction = self.reaction
        reaction_data = reaction.to_dict()
        reaction_json = json.dumps(reaction_data, indent=2, ensure_ascii=False)
        detected_issue = self.issues
        validated_json = chemist.reflect_reaction(reaction_json,detected_issue)
        return validated_json


#output data as json with reflection
'''
reaction_description = "Synthesis of 7j. According to general procedure. 6 (15 mg, 0.030 mmol), benzo[b]thien-2-ylboronic acid (10.9 mg, 0.060 mmol), Pd(OAc)2 (9.0 mg, 0.060 mmol), S-Phos (1.9 mg, 4.6x10-3 mmol), Na2CO3 (6.5 mg, 0.060 mmol). Reaction time 7 h; mp: 294-296 °C; Rf: 0.46 (AcOEt/Hexane, 1:3); 77% yield as orange solid; IR (KBr, cm-1): 3055 (C-HAR, w), 1720 (C=O, s), 1601 (w), 1545 (s), 1480 (m), 1411 (s), 1386 (s), 1352 (w), 1262 (C-O, s), 1202 (s), 1116 (s), 1080 (C-O, s), 993 (w), 948 (w), 906 (w), 828 (w), 780 (w), 746 (w), 727 (w), 687 (w), 647 (w), 583 (w); 1H NMR (500 MHz, CDCl3) δ. HRMS (ESI+) m/z calcd for C32H20BF2N2O2S [M+H]+ 545.1307. Found 545.1315."
model_name = "gpt-4.1"
api_key = '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'

extractor = ReactionExtractor(model_name=model_name, api_key=api_key, transfer_tool=Transfering_tools)


reaction_obj = extractor.build_reaction(reaction_description)

validator = ReactionValidator(reaction_obj, model_name, api_key)

issues = validator.validate_minimal()
print("Detected issues:", issues)

# Optional deep reflection
corrected_json = validator.reflect_with_llm()

print(corrected_json)
print('raw json:')
print(extractor.to_json(reaction_obj))
'''