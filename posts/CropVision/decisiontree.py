import os
from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns

# Force Matplotlib to run in headless mode for Linux servers
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Modern sklearn imports (distutils and version checking removed)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, accuracy_score

# Setup Paths
BASE_DIR = Path(__file__).parent.resolve()
INPUT_CSV = BASE_DIR / 'new_features.csv'
OUTPUT_CSV = BASE_DIR / 'new_final.csv'

print(f"Loading data from {INPUT_CSV}...")
features_db = pd.read_csv(INPUT_CSV, header=None)

# Extract unique labels from the 48th column
class_mapping = {label: idx for idx, label in enumerate(np.unique(features_db[48]))}
print("Class Mapping:", class_mapping)

# Map string labels to integer indices
features_db[48] = features_db[48].map(class_mapping)
features_db.to_csv(OUTPUT_CSV, index=False)
print(f"Saved mapped data to {OUTPUT_CSV}")

# Split features (X) and target (Y)
X = features_db.loc[:, 0:47]
Y = features_db.loc[:, 48]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, random_state=0)

# Scale features
print("Scaling features...")
sc = StandardScaler()
sc.fit(X_train)
X_train_std = sc.transform(X_train)
X_test_std = sc.transform(X_test)

# Train Decision Tree Classifier
print("Training Decision Tree Classifier...")
classifier = DecisionTreeClassifier(criterion='entropy', random_state=0)
classifier.fit(X_train_std, y_train)

# Make predictions and calculate accuracy
y_pred = classifier.predict(X_test_std)
accuracy = accuracy_score(y_test, y_pred)
accuracy_pct = round(accuracy * 100, 2)

print("="*40)
print(f"DECISION TREE ACCURACY: {accuracy_pct}%")
print("="*40)

# Create and save a Confusion Matrix heatmap
print("Generating Confusion Matrix...")
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix Data:")
print(cm)

plt.figure(figsize=(10, 8))
sns.heatmap(cm, cmap=plt.cm.Blues, annot=True, fmt='g')
plt.title(f'Decision Tree Confusion Matrix (Accuracy: {accuracy_pct}%)')
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.tight_layout()

cm_path = BASE_DIR / "DT_Confusion_Matrix.png"
plt.savefig(cm_path, dpi=300)
plt.close()
print(f"Saved Decision Tree confusion matrix plot to: {cm_path}")