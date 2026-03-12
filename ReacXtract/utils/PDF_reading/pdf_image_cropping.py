import os
import re
from pdf2image import convert_from_path
import cv2
import numpy as np
import PIL.Image as Image
from PIL import PngImagePlugin
from molscribe import MolScribe
import torch
from huggingface_hub import hf_hub_download
from rdkit import Chem
import easyocr


class inserted_image:
    def __init__(self, image):
        '''

        :param image:
        '''
        image_name = os.path.basename(image)
        match1 = re.search(r'page_(\d+)', image_name)
        if match1:
            page_number = int(match1.group(1))
        else:
            page_number = None
        self.page_number = page_number

        match2 = re.search(r'molecule_(\d+)', image_name)
        if match2:
            molecule_order = int(match2.group(1))
        else:
            molecule_order = None
        self.molecule_order = molecule_order

        molecule_smiles = PDF_image.read_SMILES_metadata(image)
        self.molecule_smiles = molecule_smiles
        molecule_label_list = PDF_image.read_label_metadata(image)
        self.molecule_label_list = molecule_label_list
        return None


class PDF_image:
    '''
    below is the folder structure
    ---.PDF
    ---[png_pages]---page_1.PNG
                  ---page_2.PNG
    ---[assigned_page_images]---annotated_page_1.PNG
                             ---annotated_page_2.PNG
    ---[cropped_images]---molecule_1_from_page_1.PNG
                       ---molecule_X_from_page_1.PNG
                       ---molecule_1_from_page_2.PNG

    png's metadata are the SMILES of the molecule structure, those without molecules would be deleted
    '''
    def __init__(self,pdf_file_name):
        self.whole_pdf_file_name = pdf_file_name
        first_folder = os.path.dirname(os.path.abspath(pdf_file_name))
        self.raw_pdf_folder  = first_folder

        page_images_folder = self.pdf_to_images()
        self.page_images_folder = page_images_folder

        for filename in os.listdir(page_images_folder):
            if filename.lower().endswith(".png"):
                pagei_png = os.path.join(page_images_folder, filename)
                cropped_image_folder = self.cropping_image(pagei_png)
        self.cropped_image_folder = cropped_image_folder
        self.molecule_selection_and_labeling(cropped_image_folder)

        image_object_list = []
        for file in os.listdir(cropped_image_folder):
            full_file_name = os.path.join(cropped_image_folder, file)
            image_object = inserted_image(full_file_name)
            image_object_list.append(image_object)

        self.image_list = image_object_list
        return image_object_list

    def pdf_to_images(self):
        '''
        pages are saved as page_i.png in png_pages folder that in the same folder of raw pdf
        :return: the image's folder path
        '''
        pdf_path = self.whole_pdf_file_name
        raw_pdf_folder = self.raw_pdf_folder
        page_image_folder = os.path.join(raw_pdf_folder, 'png_pages')
        os.makedirs(page_image_folder, exist_ok=True)
        images = convert_from_path(pdf_path, 900)

        for i, img in enumerate(images,start=1):
            image_path = os.path.join(page_image_folder, f"page_{i}.png")
            img.save(image_path)
        return page_image_folder

    @staticmethod
    def cropping_image(page_image):
        '''
        inpuut a image of a page and cropped the insert images in it, save in folder[cropped_images]
        :param page_image:
        :return:
        '''

        image = cv2.imread(page_image, cv2.IMREAD_GRAYSCALE)
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = np.ones((3, 3), np.uint8)
        binary_cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(binary_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Determine the approximate height of a text line
        line_heights = []
        for contour in contours:
            _, _, _, h = cv2.boundingRect(contour)
            line_heights.append(h)

        if line_heights:
            avg_line_height = int(np.median(line_heights))  # Median line height for text
        else:
            avg_line_height = 20  # Fallback value if no text is detected

        filtered_contours = []
        min_area = 1000  # Adjust this based on molecule size
        min_height = avg_line_height * 2 # Ensure the height is at least twice a text line height

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if cv2.contourArea(contour) > min_area and h > min_height:
                filtered_contours.append((x, y, w, h))

        page_image_dir = os.path.dirname(page_image)
        parent_folder = os.path.dirname(page_image_dir)
        assigned_folder = os.path.join(parent_folder, 'assigned_page_images')
        os.makedirs(assigned_folder, exist_ok=True)
        page_name = os.path.basename(page_image)

        annotated_image = cv2.imread(page_image)
        for (x, y, w, h) in filtered_contours:
            cv2.rectangle(annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2) # Draw as green boxes
        annotated_path = os.path.join(assigned_folder, f'annotated_{page_name}')
        cv2.imwrite(annotated_path, annotated_image)

        page_name_no_extension = os.path.splitext(page_name)[0]
        cropped_folder = os.path.join(parent_folder, 'cropped_images')

        if not os.path.exists(cropped_folder):
            os.makedirs(cropped_folder)

        pil_image = Image.open(page_image)
        for idx, (x, y, w, h) in enumerate(filtered_contours):
            padding = 10  # Adjust padding if needed
            x, y = max(0, x - padding), max(0, y - padding)
            w, h = min(pil_image.width - x, w + 2 * padding), min(pil_image.height - y, h + 2 * padding)

            cropped_image = pil_image.crop((x, y, x + w, y + h))
            output_path = os.path.join(cropped_folder, f"molecule_{idx + 1}_from_{page_name_no_extension}.png")
            cropped_image.save(output_path)
        pil_image.close()
        return cropped_folder

    @staticmethod
    def molecule_selection_and_labeling(folder):
        '''
        :param folder: the folder that contains single molecule images
        :return:
        '''

        def extracting_molecular_notation(image):

            reader = easyocr.Reader(['en'])
            text_result = reader.readtext(image)

            # text_result is a list of [bbox, text, confidence]
            texts = [item[1] for item in text_result]
            string_result = '/'.join(texts)
            print("Extracted:", string_result)
            return string_result

        def get_main_mol(smiles):
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            frags = Chem.GetMolFrags(mol,asMols=True)
            largest = max(frags, key=lambda m: m.GetNumAtoms())
            return largest

        ckpt_path = hf_hub_download('yujieq/MolScribe', 'swin_base_char_aux_1m.pth')
        model = MolScribe(ckpt_path, device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

        image_to_delete_path = []
        for filename in os.listdir(folder):
            if filename.lower().endswith(".png"):
                image_i = os.path.join(folder, filename)
                smiles_result = model.predict_image_file(image_i)
                output_smiles = smiles_result['smiles'] # should check for molecule number
                output_mol = get_main_mol(output_smiles)
                if output_mol is not None:
                    img_for_note = Image.open(image_i)
                    string_label = extracting_molecular_notation(image_i)
                    metadata = PngImagePlugin.PngInfo()
                    metadata.add_text("SMILES",output_smiles)
                    metadata.add_text("label", string_label)
                    img_for_note.save(image_i, pnginfo=metadata) # add SMILES as metadata of the png

                else:
                    image_to_delete_path.append(image_i)

        for filename in image_to_delete_path:
            if os.path.exists(filename):
                os.remove(filename)
        return None

    @staticmethod
    def read_SMILES_metadata(image):
        '''
        get note from a png's metadata
        :param image:
        :return:
        '''
        image_with_note = Image.open(image)
        note = image_with_note.info.get("SMILES","None")
        return note

    @staticmethod
    def read_label_metadata(image):
        '''
        get note from a png's metadata
        :param image:
        :return: a list of extracted label from image
        '''
        image_with_note = Image.open(image)
        note = image_with_note.info.get("label","None")
        note_list = note.split("/")
        return note_list


file_path = r"D:\All_self_files\info_extract_examples\621 pdf test\digital\JOC-10\JOC6-selected\ding-et-al-2025-amine-controlled-transition-metal-catalyzed-hydrodefluorination-and-defluoroamination-of-fluoroarenes.pdf"
image_object_list = PDF_image(file_path)

'''


'''