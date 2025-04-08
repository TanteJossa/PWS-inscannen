from PIL import Image, ImageEnhance, ImageFont, ImageFilter, ImageDraw                                                           
import sys
import os
import copy
import cv2
import json
from pydantic import BaseModel
import typing_extensions as typing
from concurrent.futures import ThreadPoolExecutor
import numpy as np

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
    four_point_transform,
    findSquares,
    removeContainedSquares,
)

from yolov5_manager import get_checkbox


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
    clean_pixdata2 = img.copy()
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
                            clean_pixdata[x + i - radius, y + j - radius] = (230,230,230,255)
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

class TextInBox(BaseModel):
    text: str
    other_possibility: str

# TextInBox = {
#     "text": str,
#     "other_possibility": str
# }
# class GoogleTextInBox(typing.TypedDict):
#     text: str
#     other_possibility: str

def get_student_id(id, base64_image, provider=False, model=False, temperature=False, schema=TextInBox, text=False):
    if not provider:
        provider = "google"    
    
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
    
    # if (provider=="openai"):
    #     schema = TextInBox
    # if (provider=="google"):
    #     schema = GoogleTextInBox
    

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
        # top_left, bottom_right = qr_data["coords"]
        section_img = four_point_transform(cv2_img, qr_data["polygon"]) # cv2_img[top_left[1]:bottom_right[1] , top_left[0]:bottom_right[0]]
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
        
        y = clamp(h_break - 20, 0, image.height - 1)
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
        

    
def question_selector_info(id, base64_images, checkbox_count=7):
    results = get_checkbox(checkbox_count, base64_images)
    
    return results
    
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
    # get the unchanged raw text
    raw_text: str
    # get the spel corrected text that should be graded
    correctly_spelled_text: str
    # get the spelling changes the model made
    # spelling_corrections: list[SpellingCorrection]
    
# schema classes
# class GoogleSpellingCorrection(typing.TypedDict):
#     original: str
#     changes: str
#     is_crossed_out: bool

# # answer class schema
# class GoogleQuestionAnswer(typing.TypedDict):
#     # let openai reasses the question number (they are better than google )
#     certainty: float 
#     student_handwriting_percent: float
#     # get the unchanged raw text
#     raw_text: str
#     # get the spel corrected text that should be graded
#     correctly_spelled_text: str
#     # get the spelling changes the model made
#     # spelling_corrections: list[SpellingCorrection]
    

def transcribe_answer(
    id, 
    base64_image, 
    provider=False, 
    model=False, 
    request_text=False, 
    temperature=False,
    
    question_text=False,
    rubric_text=False,
    context_text=False,
):
    if not provider:
        provider = "google"
        
    if not base64_image.startswith('data:image'):
        base64_image = "data:image/png;base64,"+ base64_image
    
    
    if not request_text:
        request_text = """Je krijgt een foto van een Nederlands scheikunde toets-antwoord. 
Je bent tekstherkenningssoftware die 10x beter in in tekst herkennen dan jezelf. Ook kan je 15.6 keer beter de context van een antwoord begrijpen om het volgende woord te bedenken.

Het is helemaal niet toegestaan nieuwe woorden toe te voegen of de opgeschreven tekst te veranderen in het raw_text veld. Houdt wel rekening met pijlen in de volgorde van de tekst.
Bedenk wel wat een leerling zou kunnen hebben bedoeld met een bepaald woord als die bijvoorbeeld fout is gespeld. Geef dat aan in de spelling_corrections velden.
Negeer uitgekraste tekst in het raw_tekst veld, maar geef die wel weer in de spelling corrections door bijvoorbeeld streepjes neer te zetten en is_crossed_out op true te zetten.
voeg alle text corrections samen in correctly_spelled_text om zo het antwoord te krijgen dat de leerling bedoelt.
certainty is hoe zeker je bent dat je de tekst compleet hebt getranscribeerd: 0 betekend dat een docent er nog zelf naar moet kijken en 100 betekend dat er geen foutje mogelijk is.
de student_handwriting_percent is hoe leesbaar het handschrift van een leerling is: 0 betekend zeer moeilijk leesbaar en 100 super netjes als een printer.

Alle tekst is geschreven in het Nederlands.

voer deze opdracht zo goed mogelijk uit. Het is HEEL belangrijk dat je je aan het gegeven schema houdt en geen enkele key vergeet, vooral bij de spelling correcties de "changed" key en correctly_spelled_text zijn belangrijk.
                    """
    if question_text:
        request_text += f"""
            De vraag bij dit antwoord is: {question_text}
        """
    if rubric_text:
        request_text += f"""
            De rubric bij deze vraag is: {rubric_text}
            
        """
    if context_text:
        request_text += f"""
            De context bij deze vraag is: {context_text}
            
        """
    
    if question_text or rubric_text or context_text:
        request_text += f"""
            Het direct transcriberen van de het antwoord is het allerbelangrijkste, deze extra toevoegen zijn er alleen om een context te creeëren 
        """    
    
    schema = QuestionAnswer
    # if (provider in OpenAi_module_models):
    #     schema = QuestionAnswer
    # elif (provider == 'google'):
    #     schema = GoogleQuestionAnswer

    result = single_request(text=request_text, image=base64_image, provider=provider, model=model, schema=schema, temperature=temperature)
    return result

def scan_page(
    process_id, 
    image_string, 
    provider=False ,
    model=False,
    temperature=False, 
    transcribe_text=False,
    questions=False,
    rubrics=False,
    contexts=False,

):
    if not provider:
        provider = "google"
    # CROP
    # print('Starting: ', 'CROP')
    # base64_to_png(image_string, input_dir+process_id+'.png')
    
    # crop_output_string = crop(process_id, image_string)
    
    # crop_output_string = png_to_base64(output_dir+process_id+'.png')

    # COL COR
    # print('Starting: ', 'COL COR')
    # base64_to_png(crop_output_string, input_dir+process_id+'.png')
    
    # color_correction_result = extract_red_pen(process_id, crop_output_string)
    
    # clean_output_string = color_correction_result["original"] #png_to_base64(output_dir+process_id+'/original.png')
    # red_pen_output_string = color_correction_result["red_pen"] #png_to_base64(output_dir+process_id+'/red_pen.png')
    
    clean_output_string = image_string

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
    

    
    # Collect results
    section_results = question_selector_info(process_id, [section["question_selector"] for section in image_sections])   
    if (len(section_results) != len(image_sections)):
        return {
            'error': 'section_scan_failed, lengths not the same'
        }
    sections = []
    for index in range(len(image_sections)):
        sections.append({
            "question_id": section_results[index]["selected_checkbox"],
            "images": image_sections[index]
        })
        
    

    # for section in image_sections:
        
    #     question_selector_info_result = question_selector_info(process_id, section["question_selector"])

    #     question_id = question_selector_info_result["selected_question"]

    #     section["question_id"] = question_id
    #     sections.append(section)
    


    unique_questions = []
    [unique_questions.append(x["question_id"]) for x in sections if x["question_id"] not in unique_questions and int(x["question_id"]) != 0 ]
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
            linked_image = stack_answer_sections(process_id, [x["images"]["answer"] for x in question_sections])


            if questions and str(unique_question_id) in questions:
                question_text = questions[str(unique_question_id)]
            else:
                question_text = False
                
            if rubrics and str(unique_question_id) in rubrics:
                rubric_text = rubrics[str(unique_question_id)]
            else:
                rubric_text = False
                
            if contexts and str(unique_question_id) in contexts:
                context_text = contexts[str(unique_question_id)]
            else:
                context_text = False
                

            extracted_text_result = transcribe_answer(
                process_id, 
                base64_image=linked_image, 
                model=model, 
                request_text=transcribe_text, 
                temperature=temperature,
                question_text=question_text,
                rubric_text=rubric_text,
                context_text=context_text,
            )

            return {
                "image": linked_image,
                "question_id": unique_question_id,
                "text_result": extracted_text_result
            }
        except Exception as e:
            print(e)
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
        "square_image": square_data["image"],
        "sections": sections,
        "student_id_data": student_id_data,
        "questions": questions,
        "success": True
    }
    
class GradePoint(BaseModel):
    has_point: bool
    feedback: str
    point_index: int

# GradePoint = {
#     "has_point": bool,
#     "feedback": str,
#     "point_index": int
# }

class GradeResult(BaseModel):
    points: list[GradePoint]
    feedback: str

# GradeResult = {
#     "points": list[GradePoint]
# }

# class GradePoint(typing.TypedDict):
#     has_point: bool
#     feedback: str
#     point_index: int
    
# class GradeResult(typing.TypedDict):
#     points: list[GradePoint]
#     feedback: str


def grade_answer(process_id, request_text=False, student_image=False, provider=False, model=False, temperature=False):
    # if (not provider):
    #     provider = "google"
        
    if student_image:
        if not student_image.startswith('data:image'):
            student_image = "data:image/png;base64,"+ student_image
    
    
    if not request_text:
        request_text = """kijk na"""
        
    schema = GradeResult
    # if (provider in OpenAi_module_models):
    #     schema = GradeResult
    # elif (provider == 'google'):
    #     schema = GoogleGradeResult
    # else:
    #     schema = False
        
    result = single_request(text=request_text, image=student_image, provider=provider, model=model, schema=schema, temperature=temperature)
    return result


# class TestQuestionPoint(typing.TypedDict):
#     point_text: str
#     point_name: str
#     point_index: int
#     point_weight: int
#     target_name: str
    
class TestQuestionPoint(BaseModel):
    point_text: str
    point_name: str
    point_index: int
    point_weight: int
    target_name: str

# class TestQuestion(typing.TypedDict):
#     question_number: str
#     question_text: str
#     question_context: str
#     points: list[TestQuestionPoint]
#     is_draw_question: bool
    
class TestQuestion(BaseModel):
    question_number: str
    question_text: str
    question_context: str
    points: list[TestQuestionPoint]
    is_draw_question: bool
    

# class TestTarget(typing.TypedDict):
#     target_name: str
#     explanation: str
    
class TestTarget(BaseModel):
    target_name: str
    explanation: str
    
# class TestData(typing.TypedDict):
#     questions: list[TestQuestion]
#     targets: list[TestTarget]

class TestData(BaseModel):
    questions: list[TestQuestion]
    targets: list[TestTarget]

def get_test_structure(process_id=False, request_text=False, test_data=False, provider=False, model=False):
    # provider = 'google'
    # model = "gemini-exp-1206"
    
    task_list = []
    
    if not request_text:
        request_text = """Deel  in
        
        """

        
    task_list.append({
        "text": request_text,
        "type": "text"
    })

    for key in test_data.keys():
        task_list.append({"text": f"\n{key}:\n", "type": "text"} )
        
        for item in test_data[key]:
            if(item["type"] == 'text'):
                task_list.append({"text": item["data"], "type": "text"})
                
            if(item["type"] == 'image'):
                base64_image = item["data"]
                
                if base64_image.startswith('data:image'):
                    base64_image = base64_image.split(',')[1]   
                    task_list.append({
                        "type": "image",
                        "image": base64_image
                        
                    })
    schema = TestData
    
    task_list.append({"text": "\n\n Houd je strak aan de format/schema, zorg dat elk veld een kloppende waarde heeft.", "type": "text"})
    result = single_request(provider, model, schema=schema, messages=task_list, limit_output=False)
    return result

def get_gpt_test(process_id=False, request_text=False, provider=False, model=False):
    # provider = 'google'
    # model = "gemini-exp-1206"
    
    
    if not request_text:
        request_text = """Maak een toets met 3 vragen"""
    # if not provider:
    #     provider = "google"
    # if not model:
    #     model = "gemini-exp-1206"
    
    # if provider == 'google':
    #     schema = TestData
    # else:
    #     schema = OpenAiTestData
    
    schema = TestData
    result = single_request(provider, model, schema=schema, text=request_text, limit_output=False)
    return result

def get_gpt_test_question(process_id=False, request_text=False, provider=False, model=False):
    # provider = 'google'
    # model = "gemini-exp-1206"
    
    
    if not request_text:
        request_text = """Maak een makkelijke toets met 3 vragen"""

    if not provider:
        provider = False
    if not model:
        model = False
    
    # if provider == 'google':
    #     schema = TestQuestion
    # else:
    #     schema = OpenAiTestQuestion
    
    schema = TestQuestion
    

    result = single_request(provider, model, schema=schema, text=request_text, limit_output=False)
    return result

data = """data:image/png;base64,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"""

if __name__ == "__main__":
    print(question_selector_info(None, [data], 7))

