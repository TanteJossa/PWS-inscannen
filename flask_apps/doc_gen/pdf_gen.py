# pdf_gen.py

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import base64
import pdfkit
import markdown
from markdown_katex import KatexExtension
import re


def get_base64_student_result_pdf(process_id=False, student_results=[], add_student_feedback=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.5*72, rightMargin=0.5*72,
        topMargin=0.5*72, bottomMargin=0.5*72,
        authort="ToetsPWS-JKK-JKW",
        title="LeerlingResultatenToetsPWS",
        subject="Automatisch nakijken"
    )
    styles = getSampleStyleSheet()

    normal_style = styles['Normal']
    normal_bold_style = ParagraphStyle(
        name='NormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
    )

    story = []

    for student in student_results:
        student_elements = []  # List to hold elements for the current student


        student_id = student.get('student_id')
        question_results = student.get('question_results', [])
        targets = student.get('targets', [])

        # Title
        title_text = f"Leerling: {student_id}"
        student_elements.append(Paragraph(title_text, styles['h1']))
        student_elements.append(Spacer(1, 12))

        # Question Table
        if question_results:
            # Prepare table data
            question_table_data = []
            # Header row
            if question_results:
                header_row = ["Vraag", "Antwoord", "Score", "Feedback", "Points"]  # Feedback always present
                if add_student_feedback:
                    header_row.append("Student Feedback")
                question_table_data.append([Paragraph(col, normal_bold_style) for col in header_row])

                # Data rows
                for result in question_results:
                    row_data = []
                    row_data.append(Paragraph(str(result.get('question_number', '')), normal_style))
                    row_data.append(Paragraph(str(result.get('student_answer', '')), normal_style))
                    row_data.append(Paragraph(str(result.get('score', '')), normal_style))
                    row_data.append(Paragraph(str(result.get('feedback', '')), normal_style))

                    point_table_data = []
                    for point in result.get('points', []):
                        point_table_data.append([
                            Paragraph(str(point.get('point_name', '')), normal_style),
                            Paragraph(str(point.get('points', '')), normal_style),
                            Paragraph(str(point.get('feedback', '')), normal_style)
                        ])
                    col_widths = [1 * 72, 0.2 * 72, None]
                    point_table = Table(point_table_data, colWidths=col_widths)
                    point_table.setStyle(TableStyle([
                        # ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        # ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                        # ('TOPPADDING', (0, 0), (-1, -1), 0),
                        # ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        # ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ]))
                    row_data.append(point_table)

                    if add_student_feedback:
                        row_data.append("") # Empty cell for student feedback

                    question_table_data.append(row_data)

                # Create the table
                col_widths = [0.5 * 72, None, 0.5 * 72, None, None] # Example: 0.5 inch for Question Number and Score
                if (add_student_feedback):
                    col_widths.append(None)
                question_table = Table(question_table_data, colWidths=col_widths)
                point_column_index = 4
                question_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LEFTPADDING', (point_column_index, 0), (point_column_index, -1), 0), # Points column
                    ('RIGHTPADDING', (point_column_index, 0), (point_column_index, -1), 0), # Points column
                    ('TOPPADDING', (point_column_index, 0), (point_column_index, -1), 0),   # Points column
                    ('BOTTOMPADDING', (point_column_index, 0), (point_column_index, -1), 0),# Points column
                    ('LEFTPADDING', (0, 0), (2, -1), 2), # Add padding back to other columns
                    ('RIGHTPADDING', (0, 0), (2, -1), 2),
                ]))
                if col_widths:
                    question_table.colWidths = col_widths
                student_elements.append(question_table)
            else:
                student_elements.append(Paragraph("No question results available for this student.", styles['Italic']))

        student_elements.append(Spacer(1, 12))

        # Target Table
        if targets:
            student_elements.append(Paragraph("<b>Leerdoelen</b>", styles['h2']))
            target_table_data = []
            if targets:
                target_header_row = ["Leerdoel", "Uitleg", "Score", "%"]
                target_table_data.append([Paragraph(col, normal_bold_style) for col in target_header_row])

                for target in targets:
                    row_data = []

                    row_data.append(Paragraph(str(target.get('target_name', '')), normal_style))
                    row_data.append(Paragraph(str(target.get('explanation', '')), normal_style))
                    row_data.append(Paragraph(str(target.get('score', '')), normal_style))
                    row_data.append(Paragraph(str(target.get('percent', '')), normal_style))

                    target_table_data.append(row_data)

                column_widths = [1.2 * 72, None, 0.6 * 72, 0.7 * 72]
                target_table = Table(target_table_data, colWidths=column_widths)
                target_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                student_elements.append(target_table)
            else:
                student_elements.append(Paragraph("Geen leerdoelen gevonden", styles['Italic']))
        else:
            student_elements.append(Paragraph("Geen leerdoelen gevonden", styles['Italic']))


        # Add a KeepTogether to try and keep the student's content on as few pages as possible
        story.append(KeepTogether(student_elements))

        # Ensure even number of pages per student
        if len(story) % 2 != 0:
            story.append(PageBreak())

    doc.build(story)

    pdf_value = buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_value).decode('utf-8')
    buffer.close()
    return pdf_base64




def convert_math_delimiters_markdown(text):
    """Converts inline and display math delimiters to Markdown-style fenced blocks."""
    def replace_inline(match):
        return f"$`{match.group(1)}`$"  # Add extra spaces for markdown

    def replace_display(match):
        return f"\n```math\n{match.group(1)}\n```\n" # Add extra spaces for markdown

    text = re.sub(r'\$\$([^\$]+?)\$\$', replace_display, text)
    text = re.sub(r'\$([^\$]+?)\$', replace_inline, text)
    return text


def generate_pdf_base64(test_data):
    md = markdown.Markdown(
        extensions=[KatexExtension(), 'tables'],
        extension_configs={'markdown_katex': {'insert_as_tag': True, 'no_inline_svg': True,}}
    )
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
            .question { margin-bottom: 20px; page-break-inside: avoid; } /* Added page-break-inside: avoid; */
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
                target_name_md = convert_math_delimiters_markdown(target.get('target_name', ''))
                target_explanation_md = convert_math_delimiters_markdown(target.get('explanation', ''))
                html_content += f"<tr><td>{md.convert(target_name_md)}</td><td>{md.convert(target_explanation_md)}</td></tr>"
            html_content += "</tbody></table>"

        # Questions Section
        questions = test_data.get('questions', [])
        if questions:
            html_content += "<h2>Vragen</h2>"
            for i, question in enumerate(questions):
                html_content += "<div class='question'>"
                if question.get('question_context'):
                    question_context_md = convert_math_delimiters_markdown(question.get('question_context', ''))
                    html_content += f"<div class='question-context'>{md.convert(question_context_md)}</div>"
                question_text_md = convert_math_delimiters_markdown(question.get('question_text', ''))
                html_content += f"<strong>Vraag {question.get('question_number', '')}:</strong> {md.convert(question_text_md)}"

                points = question.get('points', [])
                if show_answers and points:
                    html_content += "<table class='points-table'>"
                    html_content += "<thead><tr><th>Onderdeel</th><th>Uitleg</th></tr></thead><tbody>"
                    for point in points:
                        point_name_md = convert_math_delimiters_markdown(point.get('point_name', ''))
                        point_text_md = convert_math_delimiters_markdown(point.get('point_text', ''))
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
    base64_output = base64.b64encode(pdf_bytes).decode('utf-8')


    return base64_output



# --- Modules to Install (for pdf_gen.py) ---
# pip install reportlab pdfkit markdown markdown-katex beautifulsoup4 lxml