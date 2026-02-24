import os
from pathlib import Path
import numpy as np
import tensorflow as tf
from tensorflow.keras import Sequential, Input
from tensorflow.keras.layers import Dense, Flatten, Conv2D, BatchNormalization, MaxPool2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# 1. Force Matplotlib to run in headless mode for Linux servers (prevents crashes)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 2. Dynamic Linux-compatible Paths
BASE_DIR = Path(__file__).parent.resolve()
TRAIN_DIR = BASE_DIR / 'train'

# NOTE: Make sure you have a 'val' folder parallel to 'train',
# or adjust this if your validation data is structured differently.
VAL_DIR = BASE_DIR / 'val'

img_width = 48
img_height = 48

datagen = ImageDataGenerator(
    rescale=1./255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True
)
test_datagen = ImageDataGenerator(rescale=1./255)

print("Loading Training Data...")
train_data_gen = datagen.flow_from_directory(
    directory=str(TRAIN_DIR),
    target_size=(img_width, img_height),
    class_mode='categorical'
)

print("Loading Validation Data...")
vali_data_gen = test_datagen.flow_from_directory(
    directory=str(VAL_DIR),
    target_size=(img_width, img_height),
    class_mode='categorical'
)

print('\nLabels:', np.unique(train_data_gen.labels))
print('Total Labels:', len(np.unique(train_data_gen.labels)))

model = Sequential()

# 3. Modern Keras requires an explicit Input layer
model.add(Input(shape=(img_width, img_height, 3)))

# Convolution
model.add(Conv2D(32, (3, 3), activation='relu', padding='same'))
model.add(MaxPool2D(2, 2))

model.add(Conv2D(64, (3, 3), activation='relu', padding='same'))
model.add(MaxPool2D(2, 2))

model.add(Conv2D(128, (3, 3), activation='relu', padding='same'))
model.add(MaxPool2D(2, 2))

model.add(Conv2D(192, (3, 3), activation='relu', padding='same'))
model.add(MaxPool2D(2, 2))

# Dense
model.add(Flatten())

model.add(Dense(128, activation='relu'))
model.add(Dropout(0.4))

model.add(Dense(228, activation='relu'))
model.add(Dropout(0.3))

model.add(Dense(10, activation='softmax'))

model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])

# 4. fit_generator is deprecated. Use standard .fit()
print("Starting training...")
r = model.fit(
    train_data_gen,
    epochs=10,
    validation_data=vali_data_gen
)

# 5. Fix plot saving (must save BEFORE showing/clearing, skipped show for Linux)
print("Saving loss and accuracy plots...")

plt.figure()
plt.title('Loss')
plt.plot(r.history['loss'], label='train_loss')
plt.plot(r.history['val_loss'], label='val_loss')
plt.legend()
plt.savefig(BASE_DIR / 'Loss.png')
plt.close() # Free up memory

plt.figure()
plt.title('Accuracy')
plt.plot(r.history['accuracy'], label='train_acc')
plt.plot(r.history['val_accuracy'], label='val_acc')
plt.legend()
plt.savefig(BASE_DIR / 'Accuracy.png')
plt.close()

# 6. Save model (The .keras extension is the modern standard, but .h5 is retained for your app compatibility)
model_path = BASE_DIR / 'tomato_disease48.h5'
model.save(model_path)
print(f"Model saved to {model_path}")