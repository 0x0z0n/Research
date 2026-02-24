import os
from pathlib import Path
import csv
import numpy as np
import pywt
import cv2
import pandas as pd

# Modern scikit-image (>0.19) uses 'gray' instead of 'grey'
from skimage.feature import graycomatrix, graycoprops

# Setup dynamic Linux-safe pathing
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'train'
OUTPUT_CSV = BASE_DIR / 'new_features.csv'

files = []
labels = []

print(f"Scanning directory: {DATA_DIR}")

# robustly search for .jpg and .JPG using pathlib
for img_path in DATA_DIR.rglob('*.[jJ][pP][gG]'):
    files.append(str(img_path))
    # In pathlib, .parent.name gets the folder name (e.g. 'Bacterial_spot') reliably
    labels.append(img_path.parent.name)

print(f"Total images found: {len(files)}")
print(f"Starting feature extraction. Writing to {OUTPUT_CSV}...")

# Use 'w' mode to overwrite. 'a+' would cause duplicate rows if the script is run multiple times
with open(OUTPUT_CSV, "w", newline="") as wr:
    writer = csv.writer(wr)

    for i, f in enumerate(files):
        img = cv2.imread(f)

        # Protect against corrupted images crashing the entire loop
        if img is None:
            print(f"Warning: Could not read image {f}. Skipping.")
            continue

        coeffs2 = pywt.dwt2(img, 'db2')
        LL, (LH, HL, HH) = coeffs2

        g = []
        con = []
        enr = []
        dis = []
        hom = []

        # Updated to modern 'graycomatrix'
        g.append(graycomatrix(np.uint8(LL[:, :, 0]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(LL[:, :, 1]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(LL[:, :, 2]), [1], [0], levels=256, normed=True, symmetric=True))

        g.append(graycomatrix(np.uint8(LH[:, :, 0]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(LH[:, :, 1]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(LH[:, :, 2]), [1], [0], levels=256, normed=True, symmetric=True))

        g.append(graycomatrix(np.uint8(HL[:, :, 0]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(HL[:, :, 1]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(HL[:, :, 2]), [1], [0], levels=256, normed=True, symmetric=True))

        g.append(graycomatrix(np.uint8(HH[:, :, 0]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(HH[:, :, 1]), [1], [0], levels=256, normed=True, symmetric=True))
        g.append(graycomatrix(np.uint8(HH[:, :, 2]), [1], [0], levels=256, normed=True, symmetric=True))

        for t in range(0, len(g)):
            # Updated to modern 'graycoprops'
            con.append(graycoprops(np.array(g[t]), 'contrast'))
            enr.append(graycoprops(np.array(g[t]), 'energy'))
            dis.append(graycoprops(np.array(g[t]), 'dissimilarity'))
            hom.append(graycoprops(np.array(g[t]), 'homogeneity'))

        con_features = np.reshape(np.array(con).ravel(), (1, len(np.array(con).ravel())))
        enr_features = np.reshape(np.array(enr).ravel(), (1, len(np.array(enr).ravel())))
        dis_features = np.reshape(np.array(dis).ravel(), (1, len(np.array(dis).ravel())))
        hom_features = np.reshape(np.array(hom).ravel(), (1, len(np.array(hom).ravel())))

        features = np.concatenate((con_features, enr_features, dis_features, hom_features), axis=1)
        ff = features[0].tolist()

        writer.writerow(ff + [labels[i]])

        # Give progress update every 1000 images
        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1} / {len(files)} images...")

print("Feature extraction complete.")

# --- Mapping Step ---
print(f"Loading {OUTPUT_CSV} for class mapping...")
features_db = pd.read_csv(OUTPUT_CSV, header=None)

print("\nData Tail:")
print(features_db.tail())

# Create dictionary of class mappings
class_mapping = {label: idx for idx, label in enumerate(np.unique(features_db[48]))}
print("\nClass Mapping:")
print(class_mapping)

# Map string labels to integer indices
features_db[48] = features_db[48].map(class_mapping)

print("\nMapped Data Head:")
print(features_db.head())

# Overwriting the mapped data to final output
FINAL_CSV = BASE_DIR / 'new_final.csv'
features_db.to_csv(FINAL_CSV, index=False, header=None)
print(f"\nFinal mapped dataset saved to {FINAL_CSV}")