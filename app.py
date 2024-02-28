# Flask server (app.py)
from flask import Flask, request, jsonify, render_template, send_file

import torch
from PIL import Image
import io

app = Flask(__name__)

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def index2():
    return 'Hello, World! This is Flask running on Ngrok.'


@app.route('/detect', methods=['POST'])
def detect():
    if request.method == 'POST':
        image_bytes = request.files['image'].read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Perform inference
        results = model(image, size=640)
        
        # Draw results on image
        results.render()  # Correctly draws the detections on the image
        
        # Save annotated image to a BytesIO buffer
        buf = io.BytesIO()
        img_base = results.render()[0]  # Correct way to access the rendered image
        im = Image.fromarray(img_base)
        im.save(buf, format="JPEG")
        buf.seek(0)  # Move to the beginning of the BytesIO buffer
        
        return send_file(buf, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(debug=True, port='5050')