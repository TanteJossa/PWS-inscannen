import os
import time
from flask import Flask, request

from helpers import (
    png_to_base64, 
    base64_to_png, 
    get_random_id
)
from scan_module import (
    extract_red_pen,
    detect_squares,
    sectionize,
    section_question
)

app = Flask(__name__)


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
        base64_to_png(image_string, './temp_image/'+process_id+'.png')
        
        # crop()
        
        output_string = png_to_base64('./temp_image_output/'+process_id+'.png')
        end_time = time.time()

        return {
            "start_time": start_time,
            "end_time": end_time,
            "output": output_string,
            "id": id
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
        base64_to_png(image_string, './temp_image/'+process_id+'.png')
        
        extract_red_pen(process_id)
        
        clean_output_string = png_to_base64('./temp_image_output/'+process_id+'/original.png')
        red_pen_output_string = png_to_base64('./temp_image_output/'+process_id+'/red_pen.png')
        end_time = time.time()



        return {
            "id": id,
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
        base64_to_png(image_string, './temp_image/'+process_id+'.png')
        
        square_data = request.args.get("square_data")
        
        data = detect_squares(process_id, square_data)
                
        output_image = png_to_base64('./temp_image_output/'+process_id+'.png')
        
        end_time = time.time()



        return {
            "id": id,
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
        base64_to_png(image_string, './temp_image/'+process_id+'.png')
        
        square_data = request.args.get("square_data")
        
        sectionize(process_id, square_data)
        
        sections = []
        
        for name in os.listdir('./temp_image_output/'+process_id):
            section_output_string = png_to_base64('./temp_image_output/'+process_id+'/'+name+'.png')
            sections.append(section_output_string)
        
        end_time = time.time()



        return {
            "id": id,
            "start_time": start_time,
            "end_time": end_time,
            "output": sections
        }
    except Exception as e:    
        return {"error": e}

@app.route('/section_question')
def question_data_from_question():
    try:
        start_time = time.time()
        if ("id" in request.args):
            id = request.args.get("id")
        else:
            id = "No ID found"
        process_id = get_random_id()
        image_string = request.args.get("Base64Image")
        base64_to_png(image_string, './temp_image/'+process_id+'.png')
                
        data = section_question(id)
        
        return {
            "id": id,
            "start_time": start_time,
            "end_time": end_time,
            "output": data
        }
    except Exception as e:    
        return {"error": e}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))