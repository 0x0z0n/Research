import os
import sys
import signal
import subprocess
from pathlib import Path
import numpy as np
import tensorflow as tf
import webbrowser
from threading import Timer

# Keras
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

# Flask utils
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

# --- PORT CLEANUP LOGIC ---
def revoke_previous_sessions(port):
    """Finds and kills any process currently using the specified port."""
    try:
        # 'lsof -t' returns only the PID
        pid = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if pid:
            print(f"[!] Port {port} is occupied by PID {pid}. Revoking session...")
            # We kill the process group to ensure child processes are gone too
            os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        # No process found on that port, which is what we want
        pass
    except Exception as e:
        print(f"Cleanup Error: {e}")

# 1. Modern TF 2.x GPU Memory Configuration
# Attempting to help the Lenovo LOQ find CUDA libraries if they are in standard paths
if "LD_LIBRARY_PATH" not in os.environ:
    os.environ["LD_LIBRARY_PATH"] = "/usr/local/cuda/lib64"

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("GPU is available and memory growth is enabled.")
    except RuntimeError as e:
        print(f"GPU Config Error: {e}")
else:
    print("GPU not detected. TensorFlow will run on CPU.")

# Define a flask app
app = Flask(__name__)

# Absolute Path Setup
BASE_DIR = Path(__file__).parent.resolve()
MODEL_PATH = BASE_DIR / 'tomato_disease48.h5'

# Load your trained model
if not MODEL_PATH.exists():
    print(f"CRITICAL ERROR: Model file not found at {MODEL_PATH}")
    sys.exit(1)

print(f"Loading model from {MODEL_PATH}...")
model = load_model(str(MODEL_PATH), compile=False)
print("Model loaded successfully.")

# Class mapping
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
    return CLASSES[pred_class_index] if pred_class_index < len(CLASSES) else "Unknown/Healthy"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return "No file uploaded", 400
            f = request.files['file']
            if f.filename == '':
                return "No selected file", 400

            uploads_dir = BASE_DIR / 'uploads'
            uploads_dir.mkdir(parents=True, exist_ok=True)
            file_path = uploads_dir / secure_filename(f.filename)
            f.save(str(file_path))

            result = model_predict(str(file_path), model)

            if file_path.exists():
                file_path.unlink()
            return result
        except Exception as e:
            print(f"!!! SERVER ERROR: {str(e)}")
            return f"Server Error: {str(e)}", 500
    return None

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5001/')

if __name__ == '__main__':
    # Force kill any process already using 5001
    revoke_previous_sessions(5001)

    # Start browser auto-launch
    Timer(1.5, open_browser).start()

    # host='0.0.0.0' makes it accessible on your local network
    # use_reloader=False is critical to prevent ghost processes when manually stopping/starting
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)