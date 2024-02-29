from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import subprocess
import datetime
import shutil

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi'}
DETECT_OP_FOLDER = "DetectOP"
IMAGE_FILE_PATH = ''  # This will be dynamically updated

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_content_type(file_path):
    """Determine the content type based on the file extension."""
    file_extension = os.path.splitext(file_path)[1].lower()
    return "video/mp4" if file_extension in ['.mp4', '.avi'] else "image/jpeg"

def run_command(file_path):
    """Run a command to process the file and update the global IMAGE_FILE_PATH."""
    global IMAGE_FILE_PATH
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    temp_output_name = 'temp_output'

    file_extension = os.path.splitext(file_path)[1].lower()

    # Decide which command to run based on file type
    if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:  # Image files
        command = [
            "python", "yolov5/detect.py",
            "--weights", "yolov5s.pt",
            "--source", file_path,
            "--project", DETECT_OP_FOLDER,
            "--name", temp_output_name,
        ]
    else:  # Video files
        command = [
            "python3", "track.py",
            "--source", file_path,
            "--output", f"{DETECT_OP_FOLDER}/{temp_output_name}",
            "--save-vid",
            "--save-txt",
        ]


    try:
        subprocess.run(command, check=True)
        temp_output_path = os.path.join(DETECT_OP_FOLDER, temp_output_name)
        output_files = os.listdir(temp_output_path)
        final_output_path = move_and_rename_output_files(temp_output_path, output_files, timestamp)
        IMAGE_FILE_PATH = final_output_path
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {str(e)}")

def move_and_rename_output_files(temp_output_path, output_files, timestamp):
    """Move and rename output files from the temporary directory to the final destination."""
    for original_file_name in output_files:
        original_file_path = os.path.join(temp_output_path, original_file_name)
        file_extension = os.path.splitext(original_file_name)[1]
        final_output_name = f"{timestamp}{file_extension}"
        final_output_path = os.path.join(DETECT_OP_FOLDER, final_output_name)
        shutil.move(original_file_path, final_output_path)
    shutil.rmtree(temp_output_path)
    return final_output_path

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or file type not allowed'})

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    run_command(file_path)
    return jsonify({'message': 'File uploaded successfully', 'filename': filename})

@app.route('/get-media', methods=['GET'])
def get_media():
    if not IMAGE_FILE_PATH:
        return jsonify({'error': 'No media available'})
    content_type = get_content_type(IMAGE_FILE_PATH)
    response = send_file(IMAGE_FILE_PATH, conditional=True)
    response.headers['Content-Type'] = content_type  # Correct way to set header
    return response

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=5050)
