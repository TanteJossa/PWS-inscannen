import os
import time
import shutil
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin

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
    get_qr_sections,
    detect_squares,
    sectionize,
    question_selector_info,
    stack_answer_sections,
    transcribe_answer
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
        image_string = request.json.get("Base64Image")
        data = request.json.get("data")
        base64_to_png(image_string, input_dir+process_id+'.png')
                
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
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        crop(process_id)
        
        output_string = png_to_base64(output_dir+process_id+'.png')
        
        
        cleanup_files(process_id)
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
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        extract_red_pen(process_id)
        
        clean_output_string = png_to_base64(output_dir+process_id+'/original.png')
        red_pen_output_string = png_to_base64(output_dir+process_id+'/red_pen.png')
        
        
        cleanup_files(process_id)
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
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = get_qr_sections(process_id)
                
        
        cleanup_files(process_id)
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
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = detect_squares(process_id)
                
        output_image = png_to_base64(output_dir+process_id+'.png')
        
        cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": {
                "image": output_image,
                "data": data
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
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        square_data = request.json.get("square_data")
        
        sectionize(process_id, square_data)
        
        sections = []
        
        for name in os.listdir(output_dir+process_id):
            section_data = {}
            for section_name in os.listdir(output_dir+process_id+'/'+name):
                # 'full' | 'section_finder' | 'question_selector' | 'answer'
                section_name:str
                
                section_data[section_name.replace('.png', '')] = png_to_base64(output_dir+process_id+'/'+name+'/'+section_name)
            
            sections.append(section_data)
        
        cleanup_files(process_id)
        end_time = time.time()



        return {
            "id": id,
            "process_id": process_id,
            "start_time": start_time,
            "end_time": end_time,
            "output": {
                "sections": sections
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
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = question_selector_info(process_id)

        cleanup_files(process_id)
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
        try:
            os.makedirs(input_dir+process_id)
        except:
            pass
        image_ids = []
        for image_string in image_strings:
            image_id = get_random_id()
            image_ids.append(image_id)
            base64_to_png(image_string, input_dir+process_id+'/'+image_id+'.png')
                
        stack_answer_sections(process_id, image_ids)

        output_image = png_to_base64(output_dir+process_id+'.png')
        
        cleanup_files(process_id)
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
        process_id = get_random_id()
        image_string = request.json.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = transcribe_answer(process_id)

        cleanup_files(process_id)
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