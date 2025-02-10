import json
import os
import time
import shutil
from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
import random

# from firebase_functions import https_fn
# from firebase_admin import initialize_app, db


from gpt_manager import (
    single_request
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
     return "pong GPT"
  
  return app

concurrent_limit = 30
request_semaphore = threading.Semaphore(concurrent_limit)

app = Flask(__name__) #create_app()
CORS(app, resources={r"/*": {"origins": "*"}})
# CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'

    
@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}! GPT"


@app.route('/gpt', methods = ['GET', 'POST'])
def get_test_pdf():
    # try:
    start_time = time.time()
    
    if (request.content_type != None and request.content_type == 'application/json'):
        data = request.get_json(silent=True)
    else:
        data = request.args.to_dict()
    
    if ("id" in data):
        id = data.get("id")
    else:
        id = "No ID found"

        
    if ("data" in data):
        input_data = data.get("data")
    else:
        input_data = False

    if ("provider" in data):
        provider = data.get("provider")
    else:
        provider = False
        
    if ("model" in data):
        model = data.get("model")
    else:
        model = False
        
    if ("schema_string" in data):
        schema_string = data.get("schema_string")
    else:
        schema_string = False
        
    if ("temperature" in data):
        temperature = data.get("temperature")
    else:
        temperature = False
        
    data = single_request(
        input_data,
        provider,
        model,
        schema_string,
        temperature,
    )

    # cleanup_files(process_id)
    end_time = time.time()

    return {
        "id": id,
        "start_time": start_time,
        "end_time": end_time,
        "output": data
    }
    # except Exception as e:    
        # return {"error": str(e)}       


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))