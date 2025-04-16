from flask import Flask, request, send_file
from rembg import remove
from PIL import Image, ImageEnhance
import io

app = Flask(__name__)

# --- Route for removing background ---
@app.route('/api/remove-bg', methods=['POST'])
def remove_background():
    if 'image' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['image']
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
    if 'image' not in request.files:
        return {'error': 'No image uploaded'}, 400

    file = request.files['image']
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


# --- Required for Vercel (or WSGI platforms) ---
def handler(environ, start_response):
    return app(environ, start_response)
