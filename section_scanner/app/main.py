import json
import os
import time
import shutil
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import random

# from firebase_functions import https_fn
# from firebase_admin import initialize_app, db

from helpers import (
    png_to_base64, 
    base64_to_png, 
    get_random_id,
)
from scan_module import (
    input_dir,
    output_dir,
    
    create_qr_section,
    
    crop,
    extract_red_pen,
    get_student_id,
    get_qr_sections,
    detect_squares,
    sectionize,
    question_selector_info,
    stack_answer_sections,
    transcribe_answer,
    scan_page,
    grade_answer,
    get_test_structure,
    get_base64_student_result_pdf,
    get_gpt_test,
    get_gpt_test_question,
    get_base64_test_pdf
)
import threading



def create_app():
  app = Flask(__name__)
  # Error 404 handler
  @app.errorhandler(404)
  def resource_not_found(e):
    return jsonify(error=str(e)), 404
  # Error 405 handler
  @app.errorhandler(405)
  def resource_not_found(e):
    return jsonify(error=str(e)), 405
  # Error 401 handler
  @app.errorhandler(401)
  def custom_401(error):
    return Response("API Key required.", 401)
  
  @app.route("/ping")
  def pong():
     return "pong"
  
  return app

concurrent_limit = 30
request_semaphore = threading.Semaphore(concurrent_limit)

app = Flask(__name__) #create_app()
CORS(app, resources={r"/*": {"origins": "*"}})
# CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'

def cleanup_files(id):
    # input
    try:
        shutil.rmtree(input_dir+id)
    except: 
        pass
    try:
        os.remove(input_dir+id+'.png')
    except: 
        pass
    
    # output
    try:
        shutil.rmtree(output_dir+id)
    except: 
        pass
    try:
        os.remove(output_dir+id+'.png')
    except: 
        pass
    
@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"

@app.route("/create_qr_section", methods = ['GET', 'POST'])

def get_qr_section():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        data = request.json.get("data")
                
        base64_image = create_qr_section(process_id, data)
                        
        cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": base64_image
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route("/scan_page", methods = ['GET', 'POST'])
def scan_fullpage():
    request_semaphore.acquire()

    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
            
        if ("gpt_text" in request.json):
            transcribe_text = request.json.get("gpt_text")
        else:
            transcribe_text = False
            
        if ("model" in request.json):
            model = request.json.get("model")
        else:
            model = False
            
        if ("questions" in request.json):
            questions = request.json.get("questions")
        else:
            questions = False
            
        if ("rubrics" in request.json):
            rubrics = request.json.get("rubrics")
        else:
            rubrics = False
            
        if ("contexts" in request.json):
            contexts = request.json.get("contexts")
        else:
            contexts = False
        
            
        
        
        process_id = get_random_id()
        
        image_string = request.json.get("Base64Image")
        
        output = scan_page(
            process_id, 
            image_string=image_string, 
            model=model, 
            transcribe_text=transcribe_text,
            questions=questions,
            rubrics=rubrics,
            contexts=contexts
        )
        
        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": output,
        }
    except Exception as e:    
         return {"error": str(e)}
    finally:
        request_semaphore.release()
    

@app.route("/crop", methods = ['GET', 'POST'])
def crop_page():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
        print(image_string)
        output_string = crop(process_id, image_string)
        # output_string = png_to_base64(output_dir+process_id+'.png')
        
        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": output_string,
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route("/extract_red_pen", methods = ['GET', 'POST'])
def colcor_page():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
        
        print(image_string)
        
        color_correction_result = extract_red_pen(process_id, image_string)
        
        clean_output_string = color_correction_result["original"] #png_to_base64(output_dir+process_id+'/original.png')
        red_pen_output_string = color_correction_result["red_pen"] #png_to_base64(output_dir+process_id+'/red_pen.png')
        
        
        # cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": {
                "clean": clean_output_string,
                "red_pen": red_pen_output_string,
            }
        }
    except Exception as e:    
        return {"error": str(e)}


@app.route("/get_student_id", methods = ['GET', 'POST'])
def extract_student_id():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = get_student_id(process_id, image_string)
                
        
        # cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route("/get_qr_sections", methods = ['GET', 'POST'])
def cut_qr_sections():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = get_qr_sections(process_id, image_string)
                
        
        # cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route("/detect_squares", methods = ['GET', 'POST'])
def detect_squares_on_page():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = detect_squares(process_id, image_string)
        
        black_square_info = data["black_square_info"]
        image = data["image"]
                
        # output_image = png_to_base64(output_dir+process_id+'.png')
        
        # cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": {
                "image": image,
                "data": black_square_info
            }
        }
    except Exception as e:    
        return {"error": str(e)}


@app.route("/extract_sections", methods = ['GET', 'POST'])
def sectionize_page():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
        
        square_data = request.json.get("square_data")
        
        base64_sections = sectionize(process_id, square_data, image_string)
        
        # sections = []
        
        # for name in os.listdir(output_dir+process_id):
        #     section_data = {}
        #     for section_name in os.listdir(output_dir+process_id+'/'+name):
        #         # 'full' | 'section_finder' | 'question_selector' | 'answer'
        #         section_name:str
                
        #         section_data[section_name.replace('.png', '')] = png_to_base64(output_dir+process_id+'/'+name+'/'+section_name)
            
        #     sections.append(section_data)
        
        # cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": {
                "sections": base64_sections
            }
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route('/question_selector_info', methods = ['GET', 'POST'])
def question_section_from_question_selector():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
            
        if ("base64Images" in request.json):
            image_strings = json.loads(request.json.get("base64Images"))
        else:
            image_strings = []
            
        if ("checkbox_count" in request.json):
            checkbox_count = json.loads(request.json.get("checkbox_count"))
        else:
            checkbox_count = 7
            
        # if ("provider" in request.json):
        #     provider = request.json.get("provider")
        # else:
        #     provider = False
        # if ("model" in request.json):
        #     model = request.json.get("model")
        # else:
        #     model = False
            
            
        process_id = get_random_id()
        # base64_to_png(image_string, input_dir+process_id+'.png')
        data = question_selector_info(
            process_id, 
            image_strings,
            checkbox_count=checkbox_count
        )

        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route('/link_answer_sections', methods = ['GET', 'POST'])
def link_answer_sections():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_strings = request.json.get("sections")
        # try:
        #     os.makedirs(input_dir+process_id)
        # except:
        #     pass
        # image_ids = []
        # for image_string in image_strings:
        #     image_id = get_random_id()
        #     image_ids.append(image_id)
        #     base64_to_png(image_string, input_dir+process_id+'/'+image_id+'.png')
        if (len(image_strings) > 0):
            output_image = stack_answer_sections(process_id, image_strings)
        else:
            output_image = ""
        
        # output_image = png_to_base64(output_dir+process_id+'.png')
        
        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": output_image
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route('/extract_text', methods = ['GET', 'POST'])
def extract_text_from_answer():
    try:
        start_time = time.time()
        if ("id" in request.json):
            id = request.json.get("id")
        else:
            id = "No ID found"
        if ("provider" in request.json):
            provider = request.json.get("provider")
        else:
            provider = False
        if ("model" in request.json):
            model = request.json.get("model")
        else:
            model = False
        if ("transcribeText" in request.json):
            transcribe_text = request.json.get("transcribeText")
        else:
            transcribe_text = False
           
           



        if ("questionText" in request.json):
            question_text = request.json.get("questionText")
        else:
            question_text = False
        if ("rubricText" in request.json):
            rubric_text = request.json.get("rubricText")
        else:
            rubric_text = False
        if ("contextText" in request.json):
            context_text = request.json.get("contextText")
        else:
            context_text = False
            
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = transcribe_answer(
            process_id, 
            image_string, 
            provider, 
            model, 
            transcribe_text,
            question_text,
            rubric_text,
            context_text,
        )

        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": str(e)}

@app.route('/grade', methods = ['GET', 'POST'])
def grade_with_answer():
    try:
        start_time = time.time()
        
        if (request.content_type != None and request.content_type == 'application/json'):
            data = request.get_json(silent=True)
        else:
            data = request.args.to_dict()
            print(data)
        
        if ("id" in data):
            id = data.get("id")
        else:
            id = "No ID found"
        if ("provider" in data):
            provider = data.get("provider")
        else:
            provider = False
        if ("model" in data):
            model = data.get("model")
        else:
            model = False
        if ("requestText" in data):
            request_text = data.get("requestText")
        else:
            if ("rubric" in data):
                rubric = data.get("rubric")
            else:
                rubric = "Klopt dit"
                
            if ("question" in data):
                question = data.get("question")
            else:
                question = "Geen vraag gevonden"
                
            if ("answer" in data):
                answer = data.get("answer")
            else:
                answer = "Geen antwoord gevonden"
                
            request_text = f"""
                Kijk deze toetsvraag van een leerling zo goed mogelijk na en geef korte feedback en het puntnummer bij elk punt, point_index is 0 voor het eerste punt. Geef ook een totale feedback met daarin een zo kort mogelijke uitleg over of iemand slodig is of het waarschijnlijk niet begrijpt en misschien tip als je denkt dat iemand ergens HEEL veel aan heeft. Spreek in de totale feedback de leerling aan en maximaal 1-2 zinnen. 
                Let op een feedback op een punt is 1 zin. en de totale feedback is maximaal 20-35 woorden. Spreek de leerling aan in de 2e persoon.
                Het is heel belangrijk dat de has_point key in elk punt staat, vergeet dit niet, dus: {{punten: [{{has_point: bool}}]}}
                
                Vraag: {question}
                
                Rubriek: {rubric}
                
                <Begin Antwoord Leerling>
                {answer}
                
                </Einde Antwoord Leerling>
                
                Houdt je aan de gegeven schema en vergeet has_point niet toe te voegen.
                
            """


        if ("studentImage" in data):
            student_image = data.get("studentImage")
        else:
            student_image = False
            
        process_id = get_random_id()
        # base64_to_png(image_string, input_dir+process_id+'.png')
            
        data = grade_answer(process_id, request_text, student_image, provider, model)

        # cleanup_files(process_id)
        end_time = time.time()

        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": str(e)}


@app.route('/test-data', methods = ['GET', 'POST'])
def get_test_data():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
        print(data)
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

        
    if ("requestText" in data):
        request_text = data.get("requestText")
    else:
        request_text = False

    if ("testData" in data):
        test_data = data.get("testData")
    else:
        test_data = False
        
    process_id = get_random_id()
    # base64_to_png(image_string, input_dir+process_id+'.png')
        
    data = get_test_structure(process_id, request_text, test_data)

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "process_id": process_id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }
    # except Exception as e:    
        # return {"error": str(e)}       

@app.route('/gpt-test', methods = ['GET', 'POST'])
def generate_gpt_test_data():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
        print(data)
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

        
    if ("requestText" in data):
        request_text = data.get("requestText")
    else:
        request_text = False
    if ("provider" in data):
        provider = data.get("provider")
    else:
        provider = False
    if ("model" in data):
        model = data.get("model")
    else:
        model = False
    process_id = get_random_id()
    # base64_to_png(image_string, input_dir+process_id+'.png')
        
    data = get_gpt_test(process_id, request_text, provider,model)

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "process_id": process_id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }
@app.route('/gpt-test-question', methods = ['GET', 'POST'])
def get_test_question_data():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
        print(data)
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

    if ("provider" in data):
        provider = data.get("provider")
    else:
        provider = False
    if ("model" in data):
        model = data.get("model")
    else:
        model = False
        
    if ("requestText" in data):
        request_text = data.get("requestText")
    else:
        request_text = False
        
    process_id = get_random_id()
    # base64_to_png(image_string, input_dir+process_id+'.png')
        
    data = get_gpt_test_question(process_id, request_text, provider, model)

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "process_id": process_id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }

@app.route('/student-result-pdf', methods = ['GET', 'POST'])
def get_result_pdf():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
        print(data)
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

        
    if ("studentResults" in data):
        student_results = data.get("studentResults")
    else:
        student_results = False
        
    if ("addStudentFeedback" in data):
        add_student_feedback = data.get("addStudentFeedback")
    else:
        add_student_feedback = False
        
    process_id = get_random_id()
    # base64_to_png(image_string, input_dir+process_id+'.png')
        
    data = get_base64_student_result_pdf(process_id, student_results, add_student_feedback)

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "process_id": process_id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }
    # except Exception as e:    
        # return {"error": str(e)}       

@app.route('/test-pdf', methods = ['GET', 'POST'])
def get_test_pdf():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
        print(data)
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

        
    if ("testData" in data):
        test_data = data.get("testData")
    else:
        test_data = False
        
        
    process_id = get_random_id()
    # base64_to_png(image_string, input_dir+process_id+'.png')
        
    data = get_base64_test_pdf(process_id, test_data)

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "process_id": process_id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }
    # except Exception as e:    
        # return {"error": str(e)}       


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))