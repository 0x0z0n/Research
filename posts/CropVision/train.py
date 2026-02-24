import os
from pathlib import Path
import numpy as np
import tensorflow as tf

from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.applications.inception_v3 import InceptionV3
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Force Matplotlib to run in headless mode for Linux servers
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 1. Dynamic Linux-compatible Paths
BASE_DIR = Path(__file__).parent.resolve()
TRAIN_DIR = BASE_DIR / 'train'

# Define Constants
IMAGE_SIZE = [256, 256]
BATCH_SIZE = 32

print("Loading InceptionV3 base model...")
# Import the InceptionV3 model using imagenet weights
inception = InceptionV3(input_shape=IMAGE_SIZE + [3], weights='imagenet', include_top=False)

# Freeze existing weights
for layer in inception.layers:
    layer.trainable = False

# 2. Proper Train/Validation Split (80/20)
print(f"Preparing data from: {TRAIN_DIR}")

# Training Generator (With Data Augmentation)
train_datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    validation_split=0.2  # Set aside 20% of data for validation
)

# Validation Generator (Strictly NO augmentation, only rescaling)
test_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2
)

# Load Training Set
training_set = train_datagen.flow_from_directory(
    directory=str(TRAIN_DIR),
    target_size=tuple(IMAGE_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training'
)

# Load Validation Set
test_set = test_datagen.flow_from_directory(
    directory=str(TRAIN_DIR),
    target_size=tuple(IMAGE_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation'
)

# Dynamically get the number of output classes based on subfolders
num_classes = len(training_set.class_indices)
print(f"Detected {num_classes} distinct classes.")

# Build the custom head for our specific classes
x = Flatten()(inception.output)
prediction = Dense(num_classes, activation='softmax')(x)

# Create the final model object
model = Model(inputs=inception.input, outputs=prediction)

# Compile model
model.compile(
    loss='categorical_crossentropy',
    optimizer='adam',
    metrics=['accuracy']
)

# 3. Train the model using modern .fit() instead of .fit_generator()
print("Starting model training...")
r = model.fit(
    training_set,
    validation_data=test_set,
    epochs=10,
    steps_per_epoch=len(training_set),
    validation_steps=len(test_set)
)

# Save the trained model
model_path = BASE_DIR / 'model_inception.h5'
model.save(model_path)
print(f"Model saved successfully to {model_path}")

# 4. Save Plots safely on headless Linux
print("Generating loss and accuracy plots...")

# Plot Loss
plt.figure()
plt.plot(r.history['loss'], label='train loss')
plt.plot(r.history['val_loss'], label='val loss')
plt.title('InceptionV3 Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
loss_path = BASE_DIR / 'LossVal_loss.png'
plt.savefig(loss_path)
plt.close()

# Plot Accuracy
plt.figure()
plt.plot(r.history['accuracy'], label='train acc')
plt.plot(r.history['val_accuracy'], label='val acc')
plt.title('InceptionV3 Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
acc_path = BASE_DIR / 'AccVal_acc.png'
plt.savefig(acc_path)
plt.close()

print("Training script execution complete.")