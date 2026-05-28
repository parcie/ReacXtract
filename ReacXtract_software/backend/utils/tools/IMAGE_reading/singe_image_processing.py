import os
from PIL import Image, PngImagePlugin
import torch
import easyocr
from molscribe import MolScribe
from huggingface_hub import hf_hub_download
from rdkit import Chem


class SingleMoleculeRecognizer:
    """
    Recognize molecule structure from a single image and convert to SMILES
    """

    def __init__(self, device=None):

        if device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.device = device

        # load MolScribe model
        ckpt_path = hf_hub_download(
            "yujieq/MolScribe",
            "swin_base_char_aux_1m.pth"
        )

        self.model = MolScribe(ckpt_path, device=self.device)

        # OCR reader
        self.reader = easyocr.Reader(['en'])

    @staticmethod
    def get_main_mol(smiles):
        """
        keep the largest fragment
        """

        mol = Chem.MolFromSmiles(smiles)

        if mol is None:
            return None

        frags = Chem.GetMolFrags(mol, asMols=True)

        largest = max(frags, key=lambda m: m.GetNumAtoms())

        return largest

    def recognize_smiles(self, image_path):
        """
        predict smiles from image
        """

        result = self.model.predict_image_file(image_path)

        smiles = result["smiles"]

        mol = self.get_main_mol(smiles)

        return smiles, mol

    def extract_labels(self, image_path):
        """
        OCR label extraction
        """

        text_result = self.reader.readtext(image_path)

        labels = [item[1] for item in text_result]

        return labels

    def analyze_image(self, image_path):
        """
        full pipeline for one image
        """

        smiles, mol = self.recognize_smiles(image_path)

        if mol is None:
            return {
                "valid": False,
                "smiles": None,
                "labels": None
            }

        labels = self.extract_labels(image_path)

        return {
            "valid": True,
            "smiles": smiles,
            "labels": labels,
            "mol": mol
        }

    def save_metadata(self, image_path, smiles, labels):
        """
        write result into PNG metadata
        """

        img = Image.open(image_path)

        metadata = PngImagePlugin.PngInfo()

        metadata.add_text("SMILES", smiles)

        metadata.add_text("label", "/".join(labels))

        img.save(image_path, pnginfo=metadata)

    def process(self, image_path, write_metadata=True):
        """
        complete workflow
        """

        result = self.analyze_image(image_path)

        if result["valid"] and write_metadata:

            self.save_metadata(
                image_path,
                result["smiles"],
                result["labels"]
            )

        return result

'''
recognizer = SingleMoleculeRecognizer()

result = recognizer.process("molecule.png")

print(result["smiles"])
print(result["labels"])


result:
{
    'valid': True,
    'smiles': 'CC1=CC=CC=C1',
    'labels': ['7a'],
    'mol': <rdkit mol object>
}
'''