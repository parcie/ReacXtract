import os
import subprocess
import xml.etree.ElementTree as ET
from rdkit import Chem
from rdkit.Chem import AllChem

import requests
from rdkit import Chem

import re



class ReactionJSONBuilder:

    def __init__(self):
        pass

    ########################################
    # PubChem name lookup
    ########################################

    def smiles_to_name(self, smiles):

        if smiles is None:
            return None

        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{smiles}/property/IUPACName/JSON"

        try:

            r = requests.get(url, timeout=3)

            data = r.json()

            return data["PropertyTable"]["Properties"][0]["IUPACName"]

        except:
            return None

    ########################################
    # Default dosage template
    ########################################

    def empty_dosage(self):

        return {
            "purity": None,
            "volume": None,
            "concentration": None,
            "mass": None
        }

    ########################################
    # Build reactant entry
    ########################################

    def build_reactant(self, smiles):

        name = self.smiles_to_name(smiles)

        return {
            "name": name if name else "unknown",
            "label": None,
            "SMILES": smiles,
            "dosage": self.empty_dosage(),
            "mols": None,
            "equivalence": None
        }

    ########################################
    # Build product entry
    ########################################

    def build_product(self, smiles):

        name = self.smiles_to_name(smiles)

        return {
            "name": name if name else "unknown",
            "label": None,
            "SMILES": smiles,
            "dosage": {
                "mass": None,
                "purity": None
            },
            "mols": None,
            "yield": None
        }

    ########################################
    # Full reaction JSON
    ########################################

    def build_reaction_json(self, reactants, products):

        reactant_entries = [
            self.build_reactant(s) for s in reactants
        ]

        product_entries = [
            self.build_product(s) for s in products
        ]

        result = {

            "reactants": reactant_entries,

            "products": product_entries,

            "catalysts": [],

            "solvents": [],

            "other_chemicals": [],

            "gas": [
                {
                    "name": None,
                    "label": None,
                    "SMILES": None,
                    "dosage": None,
                    "mols": None
                }
            ],

            "time": [],

            "temperature": [],

            "yield": None,

            "post_processing": None,

            "notes": None
        }

        return result


class CDXReactionExtractor:

    def __init__(self, chemdraw_path=None):
        """
        chemdraw_path : ChemDraw executable path
        """
        self.chemdraw_path = chemdraw_path

    ############################################
    # 1 CDX → CDXML
    ############################################

    def convert_cdx_to_cdxml(self, cdx_path, cdxml_path=None):
        """
        Convert CDX to CDXML using ChemDraw
        """

        if cdxml_path is None:
            cdxml_path = cdx_path.replace(".cdx", ".cdxml")

        if os.path.exists(cdxml_path):
            return cdxml_path

        if self.chemdraw_path is None:
            raise RuntimeError("ChemDraw path required for CDX conversion")

        cmd = [
            self.chemdraw_path,
            "/convert",
            cdx_path,
            cdxml_path
        ]

        subprocess.run(cmd)

        return cdxml_path

    ############################################
    # 2 Parse CDXML
    ############################################

    def parse_cdxml(self, cdxml_path):

        tree = ET.parse(cdxml_path)
        root = tree.getroot()

        fragments = []
        arrows = []
        texts = []

        for elem in root.iter():

            tag = elem.tag.lower()

            if "fragment" in tag:
                fragments.append(elem)

            if "arrow" in tag:
                arrows.append(elem)

            if tag.endswith("t"):
                if elem.text:
                    texts.append(elem.text.strip())

        return fragments, arrows, texts

    ############################################
    # 3 Fragment → RDKit Mol
    ############################################

    def fragment_to_mol(self, fragment):

        atoms = []
        bonds = []

        atom_map = {}

        for atom in fragment.iter():

            if "atom" in atom.tag.lower():

                atom_id = atom.attrib.get("id")
                element = atom.attrib.get("element", "C")

                atom_map[atom_id] = len(atoms)

                atoms.append(element)

        for bond in fragment.iter():

            if "bond" in bond.tag.lower():

                begin = bond.attrib.get("b")
                end = bond.attrib.get("e")

                if begin in atom_map and end in atom_map:
                    bonds.append((atom_map[begin], atom_map[end]))

        mol = Chem.RWMol()

        atom_indices = []

        for element in atoms:

            rd_atom = Chem.Atom(element)
            atom_indices.append(mol.AddAtom(rd_atom))

        for a, b in bonds:
            mol.AddBond(a, b, Chem.BondType.SINGLE)

        mol = mol.GetMol()

        try:
            Chem.SanitizeMol(mol)
        except:
            return None

        return mol

    ############################################
    # 4 Mol → SMILES
    ############################################

    def mol_to_smiles(self, mol):

        if mol is None:
            return None

        try:
            return Chem.MolToSmiles(mol)
        except:
            return None

    ############################################
    # 5 获取fragment坐标
    ############################################

    def get_fragment_center(self, fragment):

        xs = []
        ys = []

        for atom in fragment.iter():

            if "atom" in atom.tag.lower():

                x = atom.attrib.get("p", None)

                if x:
                    try:
                        coords = x.split()
                        xs.append(float(coords[0]))
                        ys.append(float(coords[1]))
                    except:
                        pass

        if len(xs) == 0:
            return None

        return sum(xs) / len(xs), sum(ys) / len(ys)

    ############################################
    # 6 arrow 坐标
    ############################################

    def get_arrow_center(self, arrow):

        bbox = arrow.attrib.get("boundingbox")

        if bbox is None:
            return None

        nums = bbox.split()

        if len(nums) != 4:
            return None

        x1, y1, x2, y2 = map(float, nums)

        return (x1 + x2) / 2, (y1 + y2) / 2

    ############################################
    # 7 Reaction reconstruction
    ############################################

    def reconstruct_reaction(self, fragments, arrows):

        reactants = []
        products = []

        if len(arrows) == 0:
            return reactants, products

        arrow_center = self.get_arrow_center(arrows[0])

        if arrow_center is None:
            return reactants, products

        arrow_x = arrow_center[0]

        for frag in fragments:

            center = self.get_fragment_center(frag)

            if center is None:
                continue

            mol = self.fragment_to_mol(frag)

            smiles = self.mol_to_smiles(mol)

            if smiles is None:
                continue

            if center[0] < arrow_x:
                reactants.append(smiles)
            else:
                products.append(smiles)

        return reactants, products

    ############################################
    # 8 主函数
    ############################################

    def extract(self, cdx_path):

        if cdx_path.endswith(".cdx"):

            cdxml_path = self.convert_cdx_to_cdxml(cdx_path)

        else:
            cdxml_path = cdx_path

        fragments, arrows, texts = self.parse_cdxml(cdxml_path)

        reactants, products = self.reconstruct_reaction(
            fragments,
            arrows
        )

        builder = ReactionJSONBuilder()

        reaction_json = builder.build_reaction_json(
            reactants,
            products
        )

        return reaction_json

'''
extractor = CDXReactionExtractor(
    chemdraw_path=r"C:\Program Files\ChemDraw\ChemDraw.exe"
)

result = extractor.extract("reaction.cdx")

print(result)

{
  "reactants": [
    "c1ccccc1B(O)O",
    "Clc1ccccc1"
  ],
  "products": [
    "c1ccc(-c2ccccc2)cc1"
  ],
  "conditions": [
    "Pd(OAc)2",
    "K2CO3",
    "80 °C"
  ]
}
'''

