from Cropper.Structure.getConfig import config_
from Cropper.DocScanner import Scanner
from Cropper.Utils import *
import pathlib
import os

def process_image(file_path: str, output_path: str) -> bool:
    """
    Returns if the image was processed successfully
    """
    try:
        success = True

        current_dir = os.path.dirname(__file__)
        scanner_path = os.path.join(current_dir, "Structure/Scanner-Detector.pth")
        scanner = Scanner(scanner_path, config_)

        # image_path = pathlib.Path(file_path)
        paper, org = ScannSavedImage(file_path, scanner, True)

        # if org == None:
        #     success = False
        print('hi')
        paper = EnhancePaper(paper)

        # save_path = pathlib.Path(os.path.join(image_path.parent, "Resaults")); save_path.mkdir(exist_ok = True)
        # image_path = os.path.join(str(save_path), image_path.stem+"_det.jpg")
        SaveCompImage(output_path, org, paper)
        
        return success
    
    except Exception as e:
        # raise Exception(e)
        print(f"Error: {e}")
        return False
    
