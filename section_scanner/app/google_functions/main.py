import os
import time
from flask import Flask, request

from helpers import (
    png_to_base64, 
    base64_to_png, 
    get_random_id,
)
from scan_module import (
    input_dir,
    output_dir,
    
    extract_red_pen,
    detect_squares,
    sectionize,
    question_selector_info,
    stack_answer_sections,
    transcribe_answer
)

app = Flask(__name__)

def cleanup_files(id):
    # input
    try:
        os.rmdir(input_dir+id)
    except: 
        pass
    try:
        os.rmdir(input_dir+id+'.png')
    except: 
        pass
    
    # output
    try:
        os.rmdir(output_dir+id)
    except: 
        pass
    try:
        os.rmdir(output_dir+id+'.png')
    except: 
        pass
@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"

@app.route("/crop")
def crop_page():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        # crop()
        
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
        return {"error": e}

@app.route("/extract_red_pen")
def colcor_page():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
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
        return {"error": e}


@app.route("/detect_squares")
def detect_squares_on_page():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        square_data = request.args.get("square_data")
        
        data = detect_squares(process_id, square_data)
                
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
        return {"error": e}


@app.route("/extract_sections")
def sectionize_page():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
        
        square_data = request.args.get("square_data")
        
        sectionize(process_id, square_data)
        
        sections = []
        
        for name in os.listdir(output_dir+process_id):
            section_data = {}
            for section_name in os.listdir(output_dir+process_id+'/'+name):
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
            "output": sections
        }
    except Exception as e:    
        return {"error": e}

@app.route('/question_selector_info')
def question_section_from_question_selector():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = question_selector_info(id)

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
        return {"error": e}

@app.route('/link_answer_sections')
def link_answer_sections():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_strings = request.args.get("sections")
        try:
            os.makedirs(input_dir+process_id)
        except:
            pass
        for image_string in image_strings:
            image_id = get_random_id()
            base64_to_png(image_string, input_dir+process_id+'/'+image_id+'.png')
                
        stack_answer_sections(id)

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
        return {"error": e}

@app.route('/extract_text')
def extract_text_from_answer():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, input_dir+process_id+'.png')
                
        data = transcribe_answer(id)

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
        return {"error": e}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))