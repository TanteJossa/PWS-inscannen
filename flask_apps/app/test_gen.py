import pdfkit
import base64
import markdown
from markdown_katex import KatexExtension
import re

def convert_math_delimiters_markdown(text):
    """Converts inline and display math delimiters to Markdown-style fenced blocks."""
    def replace_inline(match):
        return f" \n```math\n{match.group(1)}\n```\n "
    def replace_display(match):
        return f" \n```math\n{match.group(1)}\n```\n "
    text = re.sub(r'\$\$([^\$]+?)\$\$', replace_display, text)
    text = re.sub(r'\$([^\$]+?)\$', replace_inline, text)
    return text

def get_base64_test_pdf(process_id=False, test_data=False):
    md = markdown.Markdown(extensions=[KatexExtension(), 'tables'])  # Attempting with default or inline SVG

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Toets</title>
        <style>
            body { font-family: sans-serif; }
            h1 { text-align: center; }
            h2 { border-bottom: 1px solid #000; padding-bottom: 5px; }
            .question { margin-bottom: 20px; }
            .question-context { font-style: italic; margin-bottom: 10px; }
            .points-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .points-table th, .points-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .points-table th { background-color: #f0f0f0; }
            .target-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .target-table th, .target-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .target-table th { background-color: #e0e0e0; }
            .page-break { page-break-after: always; }
            pre { background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; overflow-x: auto; }
        </style>
    </head>
    <body>
    """

    if test_data:
        settings = test_data.get('settings', {})
        test_name = settings.get('test_name', 'Naamloze Toets')
        show_answers = settings.get('show_answers', True)
        show_targets = settings.get('show_targets', True)

        html_content += f"<h1>{test_name}</h1>"

        # Targets Section
        targets = test_data.get('targets', [])
        if targets and show_targets:
            html_content += "<h2>Leerdoelen</h2>"
            html_content += "<table class='target-table'>"
            html_content += "<thead><tr><th>Leerdoel</th><th>Uitleg</th></tr></thead><tbody>"
            for target in targets:
                target_name_md = target.get('target_name', '')
                target_explanation_md = target.get('explanation', '')
                html_content += f"<tr><td>{md.convert(target_name_md)}</td><td>{md.convert(convert_math_delimiters_markdown(target_explanation_md))}</td></tr>"
            html_content += "</tbody></table>"

        # Questions Section
        questions = test_data.get('questions', [])
        if questions:
            html_content += "<h2>Vragen</h2>"
            for i, question in enumerate(questions):
                html_content += "<div class='question'>"
                if question.get('question_context'):
                    question_context_md = question.get('question_context', '')
                    html_content += f"<div class='question-context'>{md.convert(convert_math_delimiters_markdown(question_context_md))}</div>"
                question_text_md = question.get('question_text', '')
                html_content += f"<strong>Vraag {question.get('question_number', '')}:</strong> {md.convert(convert_math_delimiters_markdown(question_text_md))}"

                points = question.get('points', [])
                if show_answers and points:
                    html_content += "<table class='points-table'>"
                    html_content += "<thead><tr><th>Onderdeel</th><th>Uitleg</th></tr></thead><tbody>"
                    for point in points:
                        point_name_md = point.get('point_name', '')
                        point_text_md = point.get('point_text', '')
                        html_content += f"<tr><td>{md.convert(point_name_md)}</td><td>{md.convert(point_text_md)}</td></tr>"
                    html_content += "</tbody></table>"
                html_content += "</div>"
                if i < len(questions) - 1:
                    html_content += "<hr>"

        else:
            html_content += "<p>Geen vragen gevonden voor deze toets.</p>"
    else:
        html_content += "<p>Geen testgegevens beschikbaar.</p>"

    html_content += """
    </body>
    </html>
    """

    pdf_bytes = pdfkit.from_string(html_content, False)
    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    return pdf_base64

if __name__ == "__main__":
    test_data_input = {
        "questions": [
            {
                "question_number": "1",
                "question_text": "De afgeleide van $e^x$ is $e^x$.",
                "question_context": "De exponentiële functie.",
                "answer_text": "",
                "points": [
                    {"point_name": "Formule", "point_text": "De correcte weergave is $e^x$."}
                ]
            },
            {
                "question_number": "2",
                "question_text": "Bekijk de volgende tabel:\n\n| Functie | Afgeleide |\n|---|---|\n| $x^2$ | $2x$ |\n| $e^x$ | $e^x$ |",
                "question_context": "Tabel met afgeleiden.",
                "answer_text": "",
                "points": []
            }
        ],
        "targets": [
            {"target_name": "Afgeleiden", "explanation": "Kent de afgeleide van $e^x$."}
        ],
        "settings": {
            "test_name": "Math Delimiter Test",
            "show_answers": True,
            "show_targets": True
        }
    }

    pdf_base64 = get_base64_test_pdf(test_data=test_data_input)

    with open("pdfkit_math_delimiter_test.pdf", "wb") as f:
        f.write(base64.b64decode(pdf_base64))

    print("PDF generated and saved as pdfkit_math_delimiter_test.pdf")