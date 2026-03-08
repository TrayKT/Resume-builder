from flask import Flask, render_template, request, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from textwrap import wrap
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Helper function to wrap text
def wrap_text(text, width):
    lines = []
    for line in text.split('\n'):
        lines.extend(wrap(line.strip(), width))
    return lines

@app.route('/', methods=['GET', 'POST'])
def resume_form():
    if request.method == 'POST':
        data = request.form.to_dict()
        template = request.form.get("template", "minimal")
        file = request.files.get('photo')
        photo_path = None

        # Save uploaded photo if exists
        if file and file.filename:
            filename = secure_filename(file.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(photo_path)

        # Generate PDF
        file_path = generate_pdf(data, photo_path)
        return send_file(file_path, as_attachment=True)

    return render_template('form.html')


def generate_pdf(data, photo_path):
    file_name = f"{data.get('name','resume')}_Resume.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4
    margin_bottom = 50
    sidebar_width = width * 0.3
    content_x = sidebar_width + 10
    y = height - 60
    page_number = 1

    # Draw sidebar with photo and other info
    def draw_sidebar():
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.rect(0, 0, sidebar_width, height, fill=1)

        if photo_path:
            c.drawImage(photo_path, 40, height - 120, width=80, height=80, mask='auto')

        sidebar_y = height - 140
        for title, content in [
            ("SKILLS", data.get('skills','')),
            ("LANGUAGES", data.get('languages','')),
            ("CERTIFICATES", data.get('certificates','')),
            ("HONOR AWARDS", data.get('awards','')),
            ("INTERESTS", data.get('interests',''))
        ]:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColor(colors.white)
            c.drawString(40, sidebar_y, f"• {title}")
            sidebar_y -= 18
            c.setFont("Helvetica", 10)
            for line in wrap_text(content, 32):
                c.drawString(50, sidebar_y, f"- {line}")
                sidebar_y -= 14
            sidebar_y -= 10

    # Draw header with name & contact
    def draw_header():
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, data.get('name',''))
        y -= 20
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#7F8C8D"))
        contact_info = f"Email: {data.get('email','')} | Phone: {data.get('phone','')}"
        c.drawString(content_x, y, contact_info)
        y -= 30

    # Draw footer with page number
    def draw_footer(page_num):
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#7F8C8D"))
        footer_text = f"Page {page_num}"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((width - text_width) / 2, 20, footer_text)

    # Check if we need a page break
    def check_page_break(extra_space=60):
        nonlocal y, page_number
        if y < margin_bottom + extra_space:
            draw_footer(page_number)
            c.showPage()
            page_number += 1
            y = height - 60
            draw_sidebar()
            draw_header()

    # Draw a block of text
    def draw_main_block(title, content):
        nonlocal y
        check_page_break()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, f"• {title}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        for line in wrap_text(content, 75):
            check_page_break()
            c.drawString(content_x + 10, y, line)
            y -= 12
        y -= 10

    # Draw detailed sections like Experience or Education
    def draw_main_section(title, content):
        nonlocal y
        check_page_break()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawString(content_x, y, f"• {title}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        for line in content.split('\n'):
            check_page_break()
            if '|' in line:
                parts = line.split('|')
                job_title = parts[0].strip()
                company = parts[1].strip()
                location = parts[2].strip() if len(parts) > 2 else ''
                duration = parts[3].strip() if len(parts) > 3 else ''
                c.setFont("Helvetica-Bold", 10)
                c.drawString(content_x + 10, y, job_title)
                y -= 12
                c.setFont("Helvetica", 9)
                for wrapped_line in wrap(f"{company}, {location} ({duration})", 75):
                    check_page_break()
                    c.drawString(content_x + 12, y, wrapped_line)
                    y -= 12
            else:
                for wrapped_line in wrap_text(line.strip(), 75):
                    check_page_break()
                    c.drawString(content_x + 10, y, f"- {wrapped_line}")
                    y -= 12
        y -= 10

    # Build PDF
    draw_sidebar()
    draw_header()
    draw_main_block("PROFILE SUMMARY", data.get('summary',''))
    draw_main_section("WORK EXPERIENCE", data.get('experience',''))
    draw_main_section("EDUCATION", data.get('education',''))
    draw_footer(page_number)
    c.save()

    return file_name


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
