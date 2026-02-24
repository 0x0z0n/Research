import warnings
from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Modern sklearn imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, accuracy_score

# Tkinter for GUI
from tkinter import *

warnings.filterwarnings('ignore')

# 1. Setup dynamic Linux-safe pathing
BASE_DIR = Path(__file__).parent.resolve()
INPUT_CSV = BASE_DIR / 'new_features.csv'
OUTPUT_CSV = BASE_DIR / 'new_final.csv'

print(f"Loading data from {INPUT_CSV}...")
features_db = pd.read_csv(INPUT_CSV, header=None)

# 2. Extract and map labels
class_mapping = {label: idx for idx, label in enumerate(np.unique(features_db[48]))}
print("Class Mapping:", class_mapping)

features_db[48] = features_db[48].map(class_mapping)
features_db.to_csv(OUTPUT_CSV, index=False)
print(f"Saved mapped data to {OUTPUT_CSV}")

# 3. Split features (X) and target (Y)
X = features_db.loc[:, 0:47]
Y = features_db.loc[:, 48]

# 4. Train/Test Split (Modernized, no distutils version checking needed)
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=0)

# 5. Scale features
print("Scaling features...")
sc = StandardScaler()
sc.fit(X_train)
X_train_std = sc.transform(X_train)
X_test_std = sc.transform(X_test)

# 6. Train Logistic Regression Model (Added max_iter to prevent convergence warnings)
print("Training Logistic Regression Classifier...")
lm = LogisticRegression(max_iter=1000)
lm.fit(X_train_std, y_train)

# 7. Make predictions and calculate accuracy
y_pred = lm.predict(X_test_std)
accuracy1 = lm.score(X_test_std, y_test)
accuracy1 = round(accuracy1 * 100, 2)

print(f"Logistic Regression Accuracy: {accuracy1}%")

# 8. GUI Window for Accuracy
root = Tk()
root.configure(background="white")
root.title("Logistic Regression Accuracy")

Label(root, text=f"LR Accuracy: {accuracy1}%", font=("times new roman", 15), fg="white",
      bg="#000000", height=2).grid(row=0, columnspan=2, sticky=N + E + W + S, padx=75, pady=15)

# This will pause the script and show the window until the user closes it
root.mainloop()

# 9. Confusion Matrix GUI Plot
print("Generating Confusion Matrix...")
cm = confusion_matrix(y_test, y_pred)
print(cm)

plt.figure(figsize=(10, 8))
sns.heatmap(cm, cmap=plt.cm.Blues, annot=True, fmt='g')
plt.title(f'Logistic Regression Confusion Matrix (Accuracy: {accuracy1}%)')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()

# Show the interactive Matplotlib window
plt.show()