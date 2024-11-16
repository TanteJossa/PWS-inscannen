from PIL import Image, ImageEnhance, ImageFont, ImageDraw                                                           
import sys
import os
import copy
import cv2
import json
from pydantic import BaseModel

from helpers import (
    cm_to_px, 
    clamp,
    scan_qrcode_from_image,
    get_black_square_data,
    png_to_base64,
    stack_images_vertically,
    create_qr,
)

from open_ai_wrapper import (
    num_tokens_from_messages,
    single_request
)

# from Cropper.process_image import process_image
from Cropper.other import scan

input_dir = "temp_image/"
output_dir = "temp_image_output/"


# def crop(id):
#     current_dir = os.getcwd()
#     process_image(current_dir+'/'+input_dir+id+'.png', current_dir+'/'+output_dir+id+'.png')


def create_qr_section(id, data, width=cm_to_px(19), height=cm_to_px(8)):
    margin = 5
    
    
    qr_code = create_qr(data, 1)
    qr_size = cm_to_px(1.5)

    img = Image.new("RGB", (width, height), color='white')
    
    p1 = margin, margin
    p1_rect = qr_size + 2*margin, margin
    p2 = img.size[0] - qr_size - margin , height - qr_size - margin
    p2_rect = img.size[0] - qr_size - 2*margin, height - margin

    qr_code = qr_code.resize((qr_size, qr_size))

    img.paste(qr_code, p1)
    img.paste(qr_code, p2)
    
    draw = ImageDraw.Draw(img)
    draw.rectangle([p1_rect, p2_rect], width=5, outline='black')
    
    img.save(output_dir+id+'.png')
    base_64_image = png_to_base64(output_dir+id+'.png')
    
    return base_64_image
    



def crop(id):
    image = cv2.imread(input_dir+id+'.png')
    image = scan(image)
    cv2.imwrite(output_dir+id+'.png', image)



def extract_red_pen(id):
    # remove .png
    
    img = Image.open(input_dir + id + '.png')
    img = img.convert("RGBA")


    clean_pixdata = img.load()
    clean_pixdata2 = img.copy().load()
    red_pen_image = Image.new('RGBA', (img.width, img.height), color=(0,0,0,0))
    red_pen_pixdata = red_pen_image.load()

    # Clean the background noise, if color != white, then set to black.

    radius = 2

    # REMOVE RED PEN
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = clean_pixdata[x, y]

            
            # REMOVE RED PEN
            if (r - g > 20 and
                r - b > 20 and
                r > 200) :
                

                for i in range(2*radius):
                    for j in range(2*radius):
                        try:
                            red_pen_pixdata[x + i - radius, y + j - radius] = clean_pixdata2[x + i - radius, y + j - radius]

                            # copy the old red pen values
                            clean_pixdata[x + i - radius, y + j - radius] = (255, 255, 255)
                        except:
                            pass

    # img.convert("L")

    # SHARPEN
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(10)

    try:
        os.makedirs(output_dir+id)
    except:
        pass

    img.save(output_dir + id +'/original.png')

    red_pen_image.save(output_dir+id+'/red_pen.png')

class TekstInBox(BaseModel):
    tekst: str
    other_possibility: str

def get_student_id(id):
    img = Image.open(input_dir + id + '.png')
    
    # student id in topleft section
    crop = (0,0, int(img.width * (5/21)), int(img.height * (5/29.5)))
    
    cropped = img.crop(crop)
    
    cropped.save(output_dir+id+'.png')
    
    base64_image = png_to_base64(output_dir+id+'.png')
    
    
    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": """Your job is to recognize the number in the black box next to the words Leerling ID and 'schrijf NETJES!'
                        return -1 if the box is empty
                    """,
                    
                                # de vraagnummers moeten getallen zijn
                                # als een vraagnummer een letter heeft, bijvoorbeeld 1a of 2c
                                # noteer dat dan al volgt: 1.a en 2.c dus, {getal}.{letter}
                },
                {
                    "type": "text",
                    "text": "Give you result in JSON like in the given schema"    
                },
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{base64_image}"
                    }
                }
            ]
        }
    ]
    
    result = single_request(messages, TekstInBox)
    result_data = result["result_data"]
    request_data = result["request_data"]

    response = {
        "student_id": result_data["tekst"],
        "other_possibility": result_data["other_possibility"],

        "tokens_used": request_data["total_tokens"],

        "model_used": result["model_used"],
        "model_version": result["model_version"],
        
        "timestamp":  result["timestamp"],
        "delta_time_s":  result["delta_time_s"],
    }
    
    return response["student_id"]

def get_qr_sections(id):
    img = Image.open(input_dir + id + '.png')
    cv2_img = cv2.imread(input_dir + id + '.png')

    data, scanned_image = scan_qrcode_from_image(img.copy())
    
    try:
        os.mkdir(output_dir+id)
    except:
        pass
    
    scanned_image.save(output_dir+id+'/scanned.png')
    
    base64_full = png_to_base64(output_dir+id+'/scanned.png')
    
    sections = []
    
    for index, qr_data in enumerate(data):
        top_left, bottom_right = qr_data["coords"]
        
        section_img = cv2_img[top_left[1]:bottom_right[1] , top_left[0]:bottom_right[0]]
        cv2.imwrite(output_dir+id+'/'+str(index)+'.png', section_img)
        
        base64_section = png_to_base64(output_dir+id+'/'+str(index)+'.png')
        
        sections.append({
            "section_image": base64_section,
            "data": qr_data["data"]
        })
    
    return {
        "image": base64_full,
        "sections": sections
    }
        
        

def detect_squares(id):

    img = Image.open(input_dir + id + '.png')


    # Get the heights and start positions of the black squares
    black_square_info, gray_img, contour_image = get_black_square_data(img)
    # gray_img.save(output_dir+image_dir+'_bw.png')
    # contour_image.save(output_dir+image_dir+'_countors.png')
    
    # filter too high
    black_square_info = [x for x in black_square_info if x[3] - x[2] > 10]

    # sort
    black_square_info.sort(key=lambda x: x[0])

    
    # Load the original image
    draw = ImageDraw.Draw(img)
    
    # Define the box color and text color
    box_color = (255, 0, 0)  # Red color
    text_color = (255, 0, 0) # Red text
    
    
    # Load a font for the height labels
    # Using default font as PIL may not always have a specific font path on the system
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    # Get image width (to make the box span across the image width)
    img_width, img_height = img.size

    # Overlay each square with a red box and label it with its height
    for start, height,x_min,x_max in black_square_info:
        # Draw a red rectangle around each black square
        draw.rectangle([x_min, start, x_max, start + height], outline=box_color, width=2)
        
        # Add the height label next to the square
        draw.text((img_width - 50, start - 15), f"{start}px", fill=text_color, font=font)
    
    # Save the resulting image
    img.save(output_dir+id+'.png')
    
    return black_square_info



def sectionize(id,square_data):
    
    image = Image.open(input_dir+id+ '.png')
    
    square_heights = [square[0] for square in square_data]
    square_x_max = [square[3] for square in square_data]
    square_heights.append(image.height)

    for index, h_break in enumerate(square_heights):
        
        if (index >= len(square_heights) - 1 ):
            continue
        
        y = clamp(h_break - 7, 0, image.height - 1)
        next_y = clamp(square_heights[index+1] - 5, 0, image.height - 1)
        
        # min height and fix
        if (next_y < y or next_y - y < 30):
            continue
        


        # section_image.show()
        # section_file_name = filenameify(h_break["description"])+".png"
        
        sections_output_dir = output_dir + id + '/'
        try:
            os.makedirs(sections_output_dir)
        except:
            pass
        
        section_output_dir = sections_output_dir + str(index) + '/'
        try:
            os.makedirs(section_output_dir)
        except:
            pass
        
        # kantlijn, boven, einde van pagina, beneden grens
        crop = (0, y, image.width, next_y)
        
        section_image = image.copy()
        
        full = section_image.crop(crop)        

        section_name = "full"
        full.save(section_output_dir+'full.png')
        
        section_finder_end = int(full.width * (1.45/21))

        section_finder_crop = (0, 0, section_finder_end+5, full.height)
        section_finder_image = full.copy().crop(section_finder_crop)
        section_finder_image.save(section_output_dir+'section_finder.png')

        question_selector_end = int(full.width * (2.8/21))

        question_selector_crop = (section_finder_end, 0, question_selector_end, full.height)
        question_selector_image = full.copy().crop(question_selector_crop)
        question_selector_image.save(section_output_dir+'question_selector.png')
        
        answer_crop = (question_selector_end-5, 0, full.width, full.height)
        answer_image = full.copy().crop(answer_crop)
        answer_image.save(section_output_dir+'answer.png')

# first tried microsoft azure, but chapGPT worked better
# from azure.core.credentials import AzureKeyCredential
# from azure.ai.formrecognizer import DocumentAnalysisClient

# with open("creds/microsoft.json", "r") as f:
#     data = json.load(f)
#     azure_endpoint = data["endpoint"]
#     azure_credential = AzureKeyCredential(data["subscription_key"])
#     azure_document_intelligence_client = DocumentAnalysisClient(endpoint, credential)

# def question_selector_info(id):

#     with open(input_dir+id+'.png', 'rb') as f:

#         poller = document_intelligence_client.begin_analyze_document(model_id="prebuilt-document", document=f)

#     result = poller.result().to_dict()
#     return result
class Checkbox(BaseModel):
    number: int
    checked_chance: float
    percentage_filled: float
    certainty: float


class CheckboxSelection(BaseModel):
    checkboxes: list[Checkbox]
    most_certain_checked_number: int
    certainty: float


def question_selector_info(id):
    base64_image = png_to_base64(input_dir+id+ '.png')

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": """
                            You'll get a picture of checkboxes that a student used to select an answer
                            your job is to see which check box is most likly the one to be ment to be checked
                            only 1 can be chosen
                            pick zero if no boxes are checked 
                            take into account the arrows that point to a chosen box, or crossed out boxes
                                """
                                # de vraagnummers moeten getallen zijn
                                # als een vraagnummer een letter heeft, bijvoorbeeld 1a of 2c
                                # noteer dat dan al volgt: 1.a en 2.c dus, {getal}.{letter}
                },
                {
                    "type": "text",
                    "text": "Give you result in JSON like in the given schema"    
                },
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "extract checked checkbox number. pick zero if no boxes are checked "    
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{base64_image}"
                    }
                }
            ]
        }
    ]
    
    result = single_request(messages, CheckboxSelection)
    result_data = result["result_data"]
    request_data = result["request_data"]

    response = {
        "checkboxes": result_data["checkboxes"],
        "selected_question": result_data["most_certain_checked_number"],

        "tokens_used": request_data["total_tokens"],

        "model_used": result["model_used"],
        "model_version": result["model_version"],
        
        "timestamp":  result["timestamp"],
        "delta_time_s":  result["delta_time_s"],
    }
    
    return response
    
    
def stack_answer_sections(id, images: list[str]):
    input_path = input_dir+id+'/'
    
    sections_output_dir = output_dir + id + '/'
    try:
        os.makedirs(sections_output_dir)
    except:
        pass
    
    
    image = Image.open(input_path + images[0] + '.png')
    output_image_path = output_dir+id+'.png'
    image.save(output_image_path)
    
    for image_id in images[1::]:
        image = Image.open(output_image_path)
        new_image = Image.open(input_path+image_id+'.png')

        stacked_image = stack_images_vertically(image, new_image)
        stacked_image.save(output_image_path)
        
    


# schema classes
class SpellingCorrection(BaseModel):
    original: str
    changes: str

# answer class schema
class QuestionAnswer(BaseModel):
    # let openai reasses the question number (they are better than google )
    certainty: float 
    student_handwriting_percent: float
    # get the unchanged raw tekst
    raw_text: str
    # get the spel corrected tekst that should be graded
    correctly_spelled_text: str
    # get the spelling changes the model made
    spelling_corrections: list[SpellingCorrection]
    
def transcribe_answer(id):
    base64_image = png_to_base64(input_dir+id+ '.png')

    messages = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": """Je krijgt een foto van een Nederlandse toetsantwoord. 
                                Je moet deze omzetten in tekst. 
                                Deze toets moet nog worden nagekeken je. 
                                Verander niets aan de inhoud. 
                                Bedenk geen nieuwe woorden of woordonderdelen. 
                                Verander alleen kleine spelfoutjes.
                                houd in het antwoord ook rekening met meerdere regels en geeft die aan met een '\\n'
                                probeer zo veel mogelijk tekst te extraheren 
                                negeer uitgekrasde letters of woorden
                                """
                                # de vraagnummers moeten getallen zijn
                                # als een vraagnummer een letter heeft, bijvoorbeeld 1a of 2c
                                # noteer dat dan al volgt: 1.a en 2.c dus, {getal}.{letter}
                },
                {
                    "type": "text",
                    "text": "Geef antwoord in JSON zoals in een aangegeven schema staat"    
                },
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "extraheer de tekst"    
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{base64_image}"
                    }
                }
            ]
        }
    ]
    
    result = single_request(messages, QuestionAnswer)
    result_data = result["result_data"]
    request_data = result["request_data"]
    response = {
        "raw_text": result_data["raw_text"],
        "correctly_spelled_text": result_data["correctly_spelled_text"],
        "spelling_corrections": result_data["spelling_corrections"],
        
        "tokens_used": request_data["total_tokens"],

        "model_used": result["model_used"],
        "model_version": result["model_version"],
        
        "timestamp":  result["timestamp"],
        "delta_time_s":  result["delta_time_s"],
    }
    
    return response

    