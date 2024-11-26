from PIL import Image, ImageEnhance, ImageFont, ImageDraw                                                           
import sys
import os
import copy
import cv2
import json
from pydantic import BaseModel
import typing_extensions as typing
from concurrent.futures import ThreadPoolExecutor


from helpers import (
    cm_to_px, 
    clamp,
    scan_qrcode_from_image,
    get_black_square_data,
    png_to_base64,
    stack_images_vertically,
    create_qr,
    pillow_to_base64,
    cv2_to_base64,
    base64_to_pillow,
    base64_to_cv2,
)

from gemini_wrapper import google_single_image_request

from gpt_manager import (
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
    
    # img.save(output_dir+id+'.png')
    # base_64_image = png_to_base64(output_dir+id+'.png')
    
    return pillow_to_base64(img)
    



def crop(id, base64_image):
    image = base64_to_cv2(base64_image)
    # image =) cv2.imread(input_dir+id+'.png')
    image = scan(image)
    # cv2.imwrite(output_dir+id+'.png', image)
    return cv2_to_base64(image)




def extract_red_pen(id, base64_image):
    # remove .png
    
    img = base64_to_pillow(base64_image)
    # img = Image.open(input_dir + id + '.png')
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
                            # clean_pixdata[x + i - radius, y + j - radius] = (255, 255, 255)
                        except:
                            pass

    # img.convert("L")

    # SHARPEN
    # enhancer = ImageEnhance.Sharpness(img)
    # img = enhancer.enhance(10)

    # try:
    #     os.makedirs(output_dir+id)
    # except:
    #     pass

    # img.save(output_dir + id +'/original.png')

    # red_pen_image.save(output_dir+id+'/red_pen.png')
    
    return {
        "original": pillow_to_base64(img),
        "red_pen": pillow_to_base64(red_pen_image)
    }

class TekstInBox(BaseModel):
    tekst: str
    other_possibility: str

class GoogleTekstInBox(typing.TypedDict):
    tekst: str
    other_possibility: str

def get_student_id(id, base64_image, provider=False, model=False, temperature=False, schema=False, text=False):
    if not provider:
        provider = "openai"    
    
    if not text:
        text = """Your job is to recognize the number in the black box next to the words Leerling ID and 'schrijf NETJES!'
            return -1 if the box is empty
        """
    
    
    img = base64_to_pillow(base64_image)
    # img = Image.open(input_dir + id + '.png')
    
    # student id in topleft section
    crop = (0,0, int(img.width * (5/21)), int(img.height * (5/29.5)))
    
    cropped = img.crop(crop)
    
    # cropped.save(output_dir+id+'.png')
    
    base64_image = pillow_to_base64(cropped)
    
    if (provider=="openai"):
        schema = TekstInBox
    if (provider=="google"):
        schema = GoogleTekstInBox
    

    result = single_request(provider=provider, model=model, temperature=temperature, schema=schema, text=text, image=base64_image)

    
    return result

def get_qr_sections(id, base64_image):
    img = base64_to_pillow(base64_image)
    # img = Image.open(input_dir + id + '.png')
    cv2_img = base64_to_cv2(base64_image)

    data, scanned_image = scan_qrcode_from_image(img.copy())
    
    # try:
    #     os.mkdir(output_dir+id)
    # except:
    #     pass
    
    # scanned_image.save(output_dir+id+'/scanned.png')
    
    base64_full = pillow_to_base64(scanned_image) 
    
    sections = []
    
    for index, qr_data in enumerate(data):
        top_left, bottom_right = qr_data["coords"]
        
        section_img = cv2_img[top_left[1]:bottom_right[1] , top_left[0]:bottom_right[0]]
        # cv2.imwrite(output_dir+id+'/'+str(index)+'.png', section_img)
        
        base64_section = cv2_to_base64(section_img)
        # png_to_base64(output_dir+id+'/'+str(index)+'.png')
        
        sections.append({
            "section_image": base64_section,
            "data": qr_data["data"]
        })
    
    return {
        "image": base64_full,
        "sections": sections
    }
        
        

def detect_squares(id, base64_image):

    img = base64_to_pillow(base64_image)
    # img = Image.open(input_dir + id + '.png')


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
    base64_detector_image = pillow_to_base64(img)
    
    
    return {
        "black_square_info": black_square_info,
        "image": base64_detector_image
    }



def sectionize(id,square_data, base64_image):
    
    image = base64_to_pillow(base64_image)
    # image = Image.open(input_dir+id+ '.png')
    
    square_heights = [square[0] for square in square_data]
    square_x_max = [square[3] for square in square_data]
    square_heights.append(image.height)

    base64_sections = []

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
        
        # sections_output_dir = output_dir + id + '/'
        # try:
        #     os.makedirs(sections_output_dir)
        # except:
        #     pass
        
        # section_output_dir = sections_output_dir + str(index) + '/'
        # try:
        #     os.makedirs(section_output_dir)
        # except:
        #     pass
        
        # kantlijn, boven, einde van pagina, beneden grens
        crop = (0, y, image.width, next_y)
        
        section_image = image.copy()
        
        full = section_image.crop(crop)        

        section_name = "full"
        # full.save(section_output_dir+'full.png')
        
        section_finder_end = square_x_max[index] #+ int(full.width * (1.45/21))

        section_finder_crop = (0, 0, section_finder_end+5, full.height)
        section_finder_image = full.copy().crop(section_finder_crop)
        # section_finder_image.save(section_output_dir+'section_finder.png')

        question_selector_end = section_finder_end + int(full.width * (1.3/21))

        question_selector_crop = (section_finder_end, 0, question_selector_end, full.height)
        question_selector_image = full.copy().crop(question_selector_crop)
        # question_selector_image.save(section_output_dir+'question_selector.png')
        
        answer_crop = (question_selector_end - int(full.width * (0.3/21)), 0, full.width, full.height)
        answer_image = full.copy().crop(answer_crop)
        # answer_image.save(section_output_dir+'answer.png')
        
        base64_sections.append({
            "full": pillow_to_base64(full),
            "section_finder": pillow_to_base64(section_finder_image),
            "question_selector": pillow_to_base64(question_selector_image),
            "answer": pillow_to_base64(answer_image),
        })
    
    return base64_sections
        
        
        

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
    
    
class GoogleCheckbox(typing.TypedDict):
    number: int
    checked_chance: float
    percentage_filled: float
    certainty: float


class GoogleCheckboxSelection(typing.TypedDict ):
    checkboxes: list[GoogleCheckbox]
    most_certain_checked_number: int
    certainty: float


def question_selector_info(id, base64_image, provider=False, model=False, scan_command_text=False, temperature=False):
    if not provider:
        provider = "openai"
        
    if not scan_command_text:
        scan_command_text = """
        You'll get a picture of checkboxes that a student used to select an answer
        your job is to see which check box is most likly the one to be ment to be checked
        only 1 can be chosen
        pick zero if no boxes are checked 
        take into account the arrows that point to a chosen box, or crossed out boxes
            """
            # de vraagnummers moeten getallen zijn
            # als een vraagnummer een letter heeft, bijvoorbeeld 1a of 2c
            # noteer dat dan al volgt: 1.a en 2.c dus, {getal}.{letter}


    # base64_image = base64_to_pillow(base64_image)
    # base64_image = png_to_base64(input_dir+id+ '.png')

    if not base64_image.startswith('data:image'):
        base64_image = "data:image/png;base64,"+ base64_image
    
    if(provider == 'google'):
        schema = GoogleCheckboxSelection
    elif(provider == 'openai'):
        schema = CheckboxSelection
        
    result = single_request(provider=provider,model=model, temperature=temperature, schema=schema, image=base64_image, text=scan_command_text)

    
    return result
    
    
def stack_answer_sections(id, images: list[str]):
    # input_path = input_dir+id+'/'
    
    # sections_output_dir = output_dir + id + '/'
    # try:
    #     os.makedirs(sections_output_dir)
    # except:
    #     pass
    
    
    image = base64_to_pillow(images[0])
    # image =) Image.open(input_path + images[0] + '.png')
    # output_image_path = output_dir+id+'.png'
    # image.save(output_image_path)
    
    for base_64_image in images[1::]:
        # image = base64_to_pillow(base)
        new_image = base64_to_pillow(base_64_image)
        # new_image = Image.open(input_path+image_id+'.png')

        image = stack_images_vertically(image, new_image)
        
    return pillow_to_base64(image)
    
    
    


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
    
# schema classes
class GoogleSpellingCorrection(typing.TypedDict):
    original: str
    changes: str

# answer class schema
class GoogleQuestionAnswer(typing.TypedDict):
    # let openai reasses the question number (they are better than google )
    certainty: float 
    student_handwriting_percent: float
    # get the unchanged raw tekst
    raw_text: str
    # get the spel corrected tekst that should be graded
    correctly_spelled_text: str
    # get the spelling changes the model made
    spelling_corrections: list[SpellingCorrection]
    

def transcribe_answer(id, base64_image, provider="openai", model=False, request_text=False, temperature=False):
    if not provider:
        provider = "openai"
        
    if not base64_image.startswith('data:image'):
        base64_image = "data:image/png;base64,"+ base64_image
    
    
    if not request_text:
        request_text = """Je krijgt een foto van een Nederlandse toetsantwoord. 
                    Je moet deze omzetten in tekst. 
                    Deze toets moet nog worden nagekeken je. 
                    Verander niets aan de inhoud. 
                    Bedenk geen nieuwe woorden of woordonderdelen. 
                    Verander alleen kleine spelfoutjes.
                    houd in het antwoord ook rekening met meerdere regels en geeft die aan met een '\\n'
                    probeer zo veel mogelijk tekst te extraheren 
                    negeer uitgekrasde letters of woorden
                    """
    if (provider == 'openai'):
        schema = QuestionAnswer
    elif (provider == 'google'):
        schema = GoogleQuestionAnswer

    result = single_request(text=request_text, provider=provider, model=model, schema=schema, temperature=temperature)

    return result

def scan_page(process_id, image_string, provider=False ,model=False,temperature=False, transcribe_text=False):
    if not provider:
        provider = "openai"
    # CROP
    print('Starting: ', 'CROP')
    # base64_to_png(image_string, input_dir+process_id+'.png')
    
    crop_output_string = crop(process_id, image_string)
    
    # crop_output_string = png_to_base64(output_dir+process_id+'.png')

    # COL COR
    print('Starting: ', 'COL COR')
    # base64_to_png(crop_output_string, input_dir+process_id+'.png')
    
    color_correction_result = extract_red_pen(process_id, crop_output_string)
    
    
    clean_output_string = color_correction_result["original"] #png_to_base64(output_dir+process_id+'/original.png')
    red_pen_output_string = color_correction_result["red_pen"] #png_to_base64(output_dir+process_id+'/red_pen.png')
    

    # STUDENT ID
    print('Starting: ', 'STUDENT ID')
    # base64_to_png(clean_output_string, input_dir+process_id+'.png')
    
    student_id_data = get_student_id(process_id, clean_output_string, provider=provider, model=model, temperature=temperature)
            
    
    # DETECT SQUARES
    print('Starting: ', 'DETECT SQUARES')
    
    square_data = detect_squares(process_id, clean_output_string)
    
    # SECTIONIZE       
    print('Starting: ', 'SECTIONIZE       ')
    
    image_sections = sectionize(process_id, square_data["black_square_info"], clean_output_string)

    # QUESTION SELECTOR
    print('Starting: ', 'QUESTION SELECTOR')
    

    sections = []
    
    def process_section(section):
        question_selector_info_result = question_selector_info(process_id, section["question_selector"])

        question_id = question_selector_info_result["selected_question"]

        section["question_id"] = question_id
        return section
            

    # Use ThreadPoolExecutor to process sections concurrently
    with ThreadPoolExecutor() as executor:
        results = executor.map(process_section, image_sections)

    # Collect results
    sections = list(results)        
    
    # for section in image_sections:
        
    #     question_selector_info_result = question_selector_info(process_id, section["question_selector"])

    #     question_id = question_selector_info_result["selected_question"]

    #     section["question_id"] = question_id
    #     sections.append(section)
    


    unique_questions = []
    [unique_questions.append(x["question_id"]) for x in sections if x["question_id"] not in unique_questions ]
    # print(len(sections))
    print('all: ',unique_questions, len(sections))
    questions = []
    
    # STACKING AND TRANSCRIBING
    print('Starting: ', 'STACKING AND TRANSCRIBING')
    
    def process_question(unique_question_id):
        question_sections = [x for x in sections if x["question_id"] == unique_question_id]

        if (len(question_sections) == 0):
            pass
        try:
            linked_image = stack_answer_sections(process_id, [x["answer"] for x in question_sections])

            extracted_text_result = transcribe_answer(process_id, linked_image, model=model, request_text=transcribe_text, temperature=temperature)

            return {
                "image": linked_image,
                "question_id": unique_question_id,
                "text_result": extracted_text_result
            }
        except:
            pass
        
    # Use ThreadPoolExecutor to process sections concurrently
    with ThreadPoolExecutor() as executor:
        results = executor.map(process_question, unique_questions)

    # Collect results
    questions = [question for question in results if question is not None]
    
    # for unique_question_id in unique_questions:
    #     question_sections = [x for x in sections if x["question_id"] == unique_question_id]

    #     if (len(question_sections) == 0):
    #         continue
    #     try:
    #         linked_image = stack_answer_sections(process_id, [x["answer"] for x in question_sections])

    #         extracted_text_result = transcribe_answer(process_id, linked_image, model=model, request_text=transribe_gpt_text)

    #         questions.append({
    #             "image": linked_image,
    #             "question_id": unique_question_id,
    #             "text_result": extracted_text_result
    #         })
    #     except:
    #         continue
    return {
        "cropped_base64": crop_output_string,
        "red_pen_base64": red_pen_output_string,
        "student_id_data": student_id_data,
        "questions": questions,
    }