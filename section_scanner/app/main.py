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
    grade_answer
)



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

app = Flask(__name__) #create_app()
CORS(app, resources={r"/*": {"origins": "*"}})
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
            
        process_id = get_random_id()
        
        image_string = request.json.get("Base64Image")
        
        output = scan_page(process_id, image_string=image_string, model=model, transcribe_text=transcribe_text)
        
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
        if ("provider" in request.json):
            provider = request.json.get("provider")
        else:
            provider = False
        if ("model" in request.json):
            model = request.json.get("model")
        else:
            model = False
            
            
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = question_selector_info(
            process_id, 
            image_string,
            provider=provider,
            model=model
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
                
        output_image = stack_answer_sections(process_id, image_strings)

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
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        # base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = transcribe_answer(process_id, image_string, provider, model, transcribe_text)

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
        if ("requestText" in request.json):
            request_text = request.json.get("requestText")
        else:
            request_text = False
            

        if ("studentImage" in request.json):
            student_image = request.json.get("studentImage")
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

        
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))