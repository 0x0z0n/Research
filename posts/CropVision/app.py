import os
import sys
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

# 1. Modern TF 2.x GPU Memory Configuration
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(f"GPU Config Error: {e}")

# Define a flask app
app = Flask(__name__)

# Absolute Path Setup
BASE_DIR = Path(__file__).parent.resolve()
MODEL_PATH = BASE_DIR / 'tomato_disease48.h5'  # Ensure this file name matches your actual saved model

# Load your trained model
if not MODEL_PATH.exists():
    print(f"CRITICAL ERROR: Model file not found at {MODEL_PATH}")
    sys.exit(1)

print(f"Loading model from {MODEL_PATH}...")
model = load_model(str(MODEL_PATH), compile=False)
print("Model loaded successfully.")

# Class mapping
CLASSES = [
    "Bacterial_spot",
    "Early_blight",
    "Late_blight",
    "Leaf_Mold",
    "Septoria_leaf_spot",
    "Spider_mites Two-spotted_spider_mite",
    "Target_Spot",
    "Tomato_Yellow_Leaf_Curl_Virus",
    "mosaic_virus",
    "Healthy"
]


def model_predict(img_path, model):
    # The tomato_disease48.h5 model was trained on 48x48 images
    img = image.load_img(img_path, target_size=(48, 48))

    # Preprocessing the image
    x = image.img_to_array(img)
    x = x / 255.0
    x = np.expand_dims(x, axis=0)

    # Predict
    preds = model.predict(x)
    pred_class_index = np.argmax(preds, axis=1)[0]

    if pred_class_index < len(CLASSES):
        return CLASSES[pred_class_index]
    else:
        return "Unknown/Healthy"


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def upload():
    if request.method == 'POST':
        try:
            # 1. Check if file is in request
            if 'file' not in request.files:
                return "No file uploaded", 400

            f = request.files['file']
            if f.filename == '':
                return "No selected file", 400

            # 2. Setup and create uploads directory
            uploads_dir = BASE_DIR / 'uploads'
            uploads_dir.mkdir(parents=True, exist_ok=True)

            file_path = uploads_dir / secure_filename(f.filename)

            # 3. Save the file
            f.save(str(file_path))

            # 4. Make prediction
            print(f"Running prediction on: {file_path}")
            result = model_predict(str(file_path), model)

            # 5. Cleanup: Delete file to save space on Linux
            if file_path.exists():
                file_path.unlink()

            return result

        except Exception as e:
            # This prints the REAL error in your terminal so we can debug it
            print(f"!!! SERVER ERROR: {str(e)}")
            return f"Server Error: {str(e)}", 500

    return None


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5001/')


if __name__ == '__main__':
    # Start browser auto-launch
    Timer(1, open_browser).start()

    # host='0.0.0.0' makes it accessible on your local network
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)