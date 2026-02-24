import warnings
from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Modern sklearn imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
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

# 4. Train/Test Split
print("Splitting data into train and test sets...")
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=0)

# 5. Scale features
print("Scaling features...")
sc = StandardScaler()
sc.fit(X_train)
X_train_std = sc.transform(X_train)
X_test_std = sc.transform(X_test)

# 6. Train Support Vector Machine (SVM) Model
print("Training Support Vector Machine (SVM) Classifier...")
svm_model_linear = SVC(kernel='linear', C=1)
svm_model_linear.fit(X_train_std, y_train)

# 7. Make predictions and calculate accuracy
svm_predictions = svm_model_linear.predict(X_test_std)
accuracy = svm_model_linear.score(X_test_std, y_test)
accuracy1 = round(accuracy * 100, 2)

print(f"SVM Accuracy: {accuracy1}%")

# 8. GUI Window for Accuracy
root = Tk()
root.configure(background="white")
root.title("SVM Accuracy")

Label(root, text=f"SVM Accuracy: {accuracy1}%", font=("times new roman", 15), fg="white",
      bg="#000000", height=2).grid(row=0, columnspan=2, sticky=N + E + W + S, padx=75, pady=15)

print("Opening GUI window. (Close the window to view the confusion matrix plot)")
# This pauses the script until the user closes the Tkinter window
root.mainloop()

# 9. Confusion Matrix GUI Plot
print("Generating Confusion Matrix...")
cm = confusion_matrix(y_test, svm_predictions)
print("Confusion Matrix Data:")
print(cm)

plt.figure(figsize=(10, 8))
# fmt='g' prevents scientific notation in the heatmap
sns.heatmap(cm, cmap=plt.cm.Blues, annot=True, fmt='g')
plt.title(f'SVM Confusion Matrix (Accuracy: {accuracy1}%)')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()

# Show the interactive Matplotlib window
plt.show()