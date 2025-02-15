# app.py

import os
import time
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json

# Import the document generation functions
from pdf_gen import get_base64_student_result_pdf, generate_pdf_base64
from docx_gen import generate_docx_base64

def create_app():  # Keep the create_app function. Good practice.
    app = Flask(__name__)

    # Error 404 handler
    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify(error=str(e)), 404

    # Error 405 handler
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error=str(e)), 405

    # Error 401 handler
    @app.errorhandler(401)
    def unauthorized(e):  # More descriptive name
        return Response("API Key required.", 401)  # Or a JSON response

    @app.route("/ping")
    def pong():
        return "pong GPT"

    return app

concurrent_limit = 30
request_semaphore = threading.Semaphore(concurrent_limit)

app = create_app()  # Use the factory function
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}! DOC GEN"

@app.route('/student-result-pdf', methods=['GET', 'POST'])
def get_result_pdf():
    with request_semaphore: # Apply concurrency limit
        start_time = time.time()
        data = request.get_json() if request.is_json else request.args.to_dict()

        student_results = data.get("studentResults", [])
        add_student_feedback = data.get("addStudentFeedback", False)
        process_id = data.get("id", "No ID found") # Use .get() for safety.

        try:
            pdf_data = get_base64_student_result_pdf(process_id, student_results, add_student_feedback)
            end_time = time.time()
            return jsonify({
                "id": process_id,
                "start_time": start_time,
                "end_time": end_time,
                "output": pdf_data
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500  # Return 500 for server errors


@app.route('/test-pdf', methods=['GET', 'POST'])
def get_test_pdf():
    with request_semaphore:
        start_time = time.time()
        data = request.get_json() if request.is_json else request.args.to_dict()

        test_data = data.get("testData")
        process_id = data.get("id", "No ID found")
        if not test_data:  # Important:  Handle missing test_data.
            return jsonify({"error": "No test data provided"}), 400

        try:
        # if True:
            output_type = test_data.get('settings', {}).get('output_type', 'pdf')

            if output_type == 'docx':
                result = generate_docx_base64(test_data)
            else:  # Default to PDF
                result = generate_pdf_base64(test_data)

            end_time = time.time()
            return jsonify({
                "id": process_id,
                "start_time": start_time,
                "end_time": end_time,
                "output": result
            })
        except Exception as e:
            print(str(e))
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8082)))