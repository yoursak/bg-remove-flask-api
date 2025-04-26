import uuid
from flask import Flask, jsonify, request, send_file
from PIL import Image, ImageEnhance
from rembg import remove  # type: ignore
from pdf2docx import Converter
import fitz  # For PDF to HTML
import pytesseract  # type: ignore
from flask import after_this_request
from docx import Document
import io
import os

app = Flask(__name__)

# Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25MB max size

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Hello route
@app.route('/api', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, World!"})

# Echo back JSON
@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.get_json()
    return jsonify({"received": data}), 201

# Remove image background
@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type, only image files allowed'}), 400

    input_image = file.read()
    output_image = remove(input_image)

    image = Image.open(io.BytesIO(output_image))
    img_io = io.BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='no_bg.png')

# Enhance photo
@app.route('/api/enhance-photo', methods=['POST'])
def enhance_photo():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type, only image files allowed'}), 400

    input_image = Image.open(file.stream).convert("RGB")
    enhanced = ImageEnhance.Brightness(
        ImageEnhance.Contrast(
            ImageEnhance.Sharpness(input_image).enhance(2.0)
        ).enhance(1.5)
    ).enhance(1.2)

    img_io = io.BytesIO()
    enhanced.save(img_io, 'JPEG', quality=95)
    img_io.seek(0)

    return send_file(img_io, mimetype='image/jpeg', as_attachment=True, download_name='enhanced.jpg')

# Convert PDF to HTML
@app.route('/api/pdf-to-html', methods=['POST'])
def pdf_to_html():
    if 'file' not in request.files:
        return {'error': 'No PDF uploaded'}, 400

    input_pdf = request.files['file'].read()

    # Ensure the folder exists for saving both PDF and HTML output
    pdf_folder = 'pdf_files'
    html_folder = 'html_con'
    
    # Create the folders if they don't exist
    os.makedirs(pdf_folder, exist_ok=True)
    os.makedirs(html_folder, exist_ok=True)

    # Save the uploaded PDF to a temporary file inside the `pdf_files` folder
    pdf_path = os.path.join(pdf_folder, 'temp.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(input_pdf)

    # Open the PDF using PyMuPDF
    doc = fitz.open(pdf_path)
    
    # Convert the PDF to HTML
    html_output = ''.join([doc.load_page(i).get_text("html") for i in range(doc.page_count)])

    # Save the HTML output to a file inside the `html_con` folder
    html_output_path = os.path.join(html_folder, 'output.html')
    with open(html_output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    # Send the resulting HTML file as download
    return send_file(html_output_path, mimetype='text/html', as_attachment=True, download_name='output.html')

# Convert image to text
@app.route('/api/image-to-text', methods=['POST'])
def image_to_text():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type, only image files allowed'}), 400

    image = Image.open(io.BytesIO(file.read()))
    text = pytesseract.image_to_string(image)
    return jsonify({'extracted_text': text})

# Convert PDF to Word
@app.route('/api/pdf-to-word', methods=['POST'])
def pdf_to_word():
    if 'file' not in request.files:
        return {'error': 'No PDF uploaded'}, 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type, only PDF files allowed'}), 400

    doc_folder = 'doc_files'
    os.makedirs(doc_folder, exist_ok=True)

    unique_id = str(uuid.uuid4())
    pdf_path = os.path.join(doc_folder, f'{unique_id}.pdf')
    docx_path = os.path.join(doc_folder, f'{unique_id}.docx')

    # Save uploaded PDF
    with open(pdf_path, 'wb') as f:
        f.write(file.read())

    # Convert PDF to DOCX
    converter = Converter(pdf_path)
    converter.convert(docx_path, start=0, end=None)
    converter.close()

    # Read DOCX into memory
    with open(docx_path, 'rb') as f:
        docx_content = f.read()

    @after_this_request
    def cleanup(response):
        try:
            os.remove(pdf_path)
            os.remove(docx_path)
        except Exception as e:
            app.logger.error(f'Error deleting temp files: {e}')
        return response

    return send_file(
        io.BytesIO(docx_content),
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name='output.docx'
    )

# Convert image to Word
@app.route('/api/image-to-word', methods=['POST'])
def image_to_word():
    if 'file' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type, only image files allowed'}), 400

    # Read the image and extract text using pytesseract
    image = Image.open(io.BytesIO(file.read()))
    text = pytesseract.image_to_string(image)

    # Create a Word document and add the extracted text
    doc = Document()
    doc.add_paragraph(text)

    # Save the Word document to a temporary location
    unique_id = str(uuid.uuid4())  # Generate a unique ID for the file
    word_file_path = os.path.join('word_files', f'{unique_id}.docx')

    # Ensure the folder exists
    os.makedirs(os.path.dirname(word_file_path), exist_ok=True)

    # Save the document
    doc.save(word_file_path)

    # Send the resulting Word file as a download
    return send_file(word_file_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name=f'{unique_id}.docx')

if __name__ == '__main__':
    app.run(debug=True)
