from flask import Flask, jsonify, request, send_file
from rembg import remove
from PIL import Image, ImageEnhance
from pdf2docx import Converter
import fitz
import pytesseract
import io

app = Flask(__name__)

# Sample route
@app.route('/api', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, World!"})

# Sample POST route
@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.get_json()
    return jsonify({"received": data}), 201


@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    input_image = file.read()

    # Remove background
    output_image = remove(input_image)

    # Convert to PIL image
    image = Image.open(io.BytesIO(output_image))
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='no_bg.png')

# --- Route for enhancing photo ---
@app.route('/api/enhance-photo', methods=['POST'])
def enhance_photo():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    input_image = Image.open(file.stream).convert("RGB")

    # Apply enhancements
    sharpness = ImageEnhance.Sharpness(input_image).enhance(2.0)
    contrast = ImageEnhance.Contrast(sharpness).enhance(1.5)
    brightness = ImageEnhance.Brightness(contrast).enhance(1.2)

    # Save to BytesIO
    img_io = io.BytesIO()
    brightness.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='enhanced.jpg')

@app.route('/api/pdf-to-html', methods=['POST'])
def pdf_to_html():
    if 'file' not in request.files:
        return {'error': 'No PDF uploaded'}, 400

    file = request.files['file']
    input_pdf = file.read()

    # Save the PDF to a temporary file
    pdf_path = 'temp.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(input_pdf)

    # Open the PDF using PyMuPDF
    doc = fitz.open(pdf_path)
    
    # Convert the PDF to HTML
    html_output = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        html_output += page.get_text("html")

    # Save the HTML output to a file
    html_output_path = 'output.html'
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Send the resulting HTML file
    return send_file(html_output_path, mimetype='text/html', as_attachment=True, download_name='output.html')

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.route('/api/image-to-text', methods=['POST'])
def image_to_text():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    input_image = file.read()

    # Open the image using Pillow
    image = Image.open(io.BytesIO(input_image))

    # Use pytesseract to convert the image to text
    text = pytesseract.image_to_string(image)

    # Return the extracted text as a response
    return jsonify({'extracted_text': text})

@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    if 'file' not in request.files:
        return {'error': 'No PDF uploaded'}, 400

    file = request.files['file']
    input_pdf = file.read()

    # Save the uploaded PDF to a temporary file
    pdf_path = 'temp.pdf'
    with open(pdf_path, 'wb') as f:
        f.write(input_pdf)

    # Convert PDF to DOCX
    docx_path = 'output.docx'
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)  # You can specify pages with start and end
    cv.close()

    # Send the resulting DOCX file
    return send_file(docx_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name='output.docx')


if __name__ == '__main__':
    app.run(debug=True)
