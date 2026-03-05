import os
import sys
import signal
import subprocess
import uuid
import io
from pathlib import Path
import numpy as np
import tensorflow as tf
import webbrowser
from threading import Timer

from PIL import Image, UnidentifiedImageError
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from flask import Flask, request, render_template

def revoke_previous_sessions(port):
    try:
        pid = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if pid:
            os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass
    except Exception:
        pass

if "LD_LIBRARY_PATH" not in os.environ:
    os.environ["LD_LIBRARY_PATH"] = "/usr/local/cuda/lib64"

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError:
        pass

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_image(file_stream):
    try:
        header = file_stream.read(512)
        file_stream.seek(0)
        
        img = Image.open(io.BytesIO(header))
        
        if img.format.lower() not in ALLOWED_EXTENSIONS:
            return False
        return True
    except (UnidentifiedImageError, Exception):
        return False

BASE_DIR = Path(__file__).parent.resolve()
MODEL_PATH = BASE_DIR / 'tomato_disease48.h5'

if not MODEL_PATH.exists():
    print("Initialization error.")
    sys.exit(1)

model = load_model(str(MODEL_PATH), compile=False)

CLASSES = [
    "Bacterial_spot", "Early_blight", "Late_blight", "Leaf_Mold",
    "Septoria_leaf_spot", "Spider_mites Two-spotted_spider_mite",
    "Target_Spot", "Tomato_Yellow_Leaf_Curl_Virus", "mosaic_virus", "Healthy"
]

def model_predict(img_path, model):
    img = image.load_img(img_path, target_size=(48, 48))
    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0)
    preds = model.predict(x)
    pred_class_index = np.argmax(preds, axis=1)[0]
    return CLASSES[pred_class_index] if pred_class_index < len(CLASSES) else "Unknown"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "Invalid request.", 400
    
    f = request.files['file']
    
    if f.filename == '':
        return "Invalid request.", 400

    if not allowed_extension(f.filename):
        return "Invalid file.", 400

    if not is_valid_image(f):
        return "Invalid file.", 400

    uploads_dir = BASE_DIR / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    ext = f.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = uploads_dir / unique_filename
    
    try:
        f.save(str(file_path))
        result = model_predict(str(file_path), model)
        return result
    except Exception:
        return "Internal server error.", 500
    finally:
        if file_path.exists():
            file_path.unlink()

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5001/')

if __name__ == '__main__':
    revoke_previous_sessions(5001)
    Timer(1.5, open_browser).start()
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)