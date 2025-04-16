from flask import Flask, request, send_file
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)

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

# Required for Vercel to recognize handler
def handler(environ, start_response):
    return app(environ, start_response)
