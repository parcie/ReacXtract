from utils.tools.IMAGE_reading.singe_image_processing import SingleMoleculeRecognizer

def collect_valid_molecules(image_files):
    recognizer = SingleMoleculeRecognizer()
    results = []

    for img in image_files:
        result = recognizer.process(img)

        if result and result.get("valid"):
            result.pop("valid", None)   # 可选
            results.append(result)

    return results


'''
[
    {
        'smiles': 'CC1=CC=CC=C1',
        'labels': ['7a'],
        'mol': <rdkit mol object>
    }
]

'''


# below are image-json  linker
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

class ReactionImageLinker:

    def __init__(self, similarity_threshold=0.85):
        """
        Parameters
        ----------
        similarity_threshold : float
            RDKit similarity threshold for fallback matching
        """
        self.similarity_threshold = similarity_threshold

    # -----------------------------
    # label normalization
    # -----------------------------
    def normalize_label(self, label):

        if not label:
            return None

        label = str(label).lower().strip()

        if label in ["unknown", "na", "none"]:
            return None

        label = label.replace("compound", "")
        label = label.replace("-", "")
        label = label.replace(" ", "")

        return label

    # -----------------------------
    # build label index
    # -----------------------------
    def build_label_index(self, image_results):

        label_index = {}

        for item in image_results:

            smiles = item.get("smiles")
            labels = item.get("labels", [])

            if not smiles:
                continue

            mol = Chem.MolFromSmiles(smiles)

            for label in labels:

                norm = self.normalize_label(label)

                if norm:
                    label_index[norm] = {
                        "smiles": smiles,
                        "mol": mol
                    }

        return label_index

    # -----------------------------
    # RDKit similarity
    # -----------------------------
    def mol_similarity(self, mol1, mol2):

        if mol1 is None or mol2 is None:
            return 0

        fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, 2)
        fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, 2)

        return DataStructs.TanimotoSimilarity(fp1, fp2)

    # -----------------------------
    # fill smiles by label
    # -----------------------------
    def fill_by_label(self, chem, label_index):

        label = chem.get("label")
        smiles = chem.get("SMILES")

        norm = self.normalize_label(label)

        if not norm:
            return chem

        if norm not in label_index:
            return chem

        if smiles and smiles not in ["unknown", ""]:
            return chem

        chem["SMILES"] = label_index[norm]["smiles"]

        return chem

    # -----------------------------
    # RDKit fallback matching
    # -----------------------------
    def rdkit_fallback(self, chem, image_results):

        smiles = chem.get("SMILES")

        if not smiles or smiles == "unknown":
            return chem

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return chem

        best_sim = 0
        best_smiles = None

        for img in image_results:

            img_mol = img.get("mol")

            if img_mol is None:
                continue

            sim = self.mol_similarity(mol, img_mol)

            if sim > best_sim:
                best_sim = sim
                best_smiles = img.get("smiles")

        if best_sim >= self.similarity_threshold:
            chem["SMILES"] = best_smiles

        return chem

    # -----------------------------
    # main linking function
    # -----------------------------
    def link(self, reaction_json, image_results):

        label_index = self.build_label_index(image_results)

        chemical_roles = [
            "reactants",
            "products",
            "catalysts",
            "other_chemicals"
        ]

        for role in chemical_roles:

            if role not in reaction_json:
                continue

            for i, chem in enumerate(reaction_json[role]):

                chem = self.fill_by_label(chem, label_index)

                chem = self.rdkit_fallback(chem, image_results)

                reaction_json[role][i] = chem

        return reaction_json