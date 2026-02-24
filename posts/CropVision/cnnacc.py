import os
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay, accuracy_score

# Force Matplotlib to run in headless mode for Linux
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Setup Paths
BASE_DIR = Path(__file__).parent.resolve()
MODEL_PATH = BASE_DIR / "tomato_disease48.h5"
VAL_DIR = BASE_DIR / "val" # Ensure this folder exists parallel to this script

print(f"Loading model from {MODEL_PATH}...")
# compile=False is safer for purely evaluating legacy models in newer TF versions
model = tf.keras.models.load_model(MODEL_PATH, compile=False)
print("Model loaded successfully.")

# Initialize image data generator
# NOTE: Removed shear, zoom, and flip. Validation data should NEVER be augmented during evaluation.
test_data_gen = ImageDataGenerator(rescale=1./255)

print("Preparing validation data...")
validation_generator = test_data_gen.flow_from_directory(
    directory=str(VAL_DIR),
    target_size=(48, 48),
    batch_size=32,
    class_mode='categorical',
    shuffle=False # Crucial: Must be False to match predictions with true labels
)

# Do prediction on test data (predict_generator is deprecated in TF 2.x)
print("Running predictions... This may take a moment.")
predictions = model.predict(validation_generator)

# Calculate true vs predicted labels
true_classes = validation_generator.classes
predicted_classes = np.argmax(predictions, axis=1)
class_labels = list(validation_generator.class_indices.keys())

# --- Evaluation Metrics ---
print("-" * 65)
actual_accuracy = accuracy_score(true_classes, predicted_classes)
print(f"ACTUAL CNN ACCURACY: {actual_accuracy * 100:.2f}%")
print("-" * 65)

# Generate Classification Report
report = classification_report(true_classes, predicted_classes, target_names=class_labels)
print("Classification Report:\n")
print(report)

# Save the report to a text file for easy viewing on Linux
report_path = BASE_DIR / "evaluation_report.txt"
with open(report_path, "w") as f:
    f.write(f"CNN Model Evaluation Report\n")
    f.write(f"===========================\n")
    f.write(f"Accuracy: {actual_accuracy * 100:.2f}%\n\n")
    f.write(f"Classification Report:\n{report}\n")
print(f"Saved text report to: {report_path}")

# --- Confusion Matrix ---
c_matrix = confusion_matrix(true_classes, predicted_classes)

# Save Confusion Matrix as an image
plt.figure(figsize=(10, 8))
cm_display = ConfusionMatrixDisplay(confusion_matrix=c_matrix, display_labels=class_labels)
# Rotate x-labels if class names are long
cm_display.plot(cmap=plt.cm.Blues, xticks_rotation='vertical')
plt.title('Confusion Matrix')
plt.tight_layout()

cm_path = BASE_DIR / "confusion_matrix.png"
plt.savefig(cm_path)
plt.close()
print(f"Saved confusion matrix plot to: {cm_path}")