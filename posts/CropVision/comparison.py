import os
from pathlib import Path
import matplotlib

# Force Matplotlib to run in headless mode for Linux servers (prevents X11/Display crashes)
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Dynamic Linux-compatible pathing
BASE_DIR = Path(__file__).parent.resolve()

# Data
accuracies = [82.4, 70.5, 78.3, 87.0]
models = ["SVM", "DT", "LR", "CNN"]

# Create figure
plt.figure(figsize=(8, 6))

# Plot bars
bars = plt.bar(models, accuracies, width=0.4, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'], label="Accuracy Comparison")

# Formatting
plt.xlabel('Machine Learning Models', fontsize=12, fontweight='bold')
plt.ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
plt.title('Tomato Disease Prediction: Model Comparison', fontsize=14, fontweight='bold')
plt.ylim(0, 100)  # Scale y-axis from 0 to 100 for proper percentage representation
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add exact percentage labels on top of the bars for readability
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1.5, f'{yval}%',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.legend()
plt.tight_layout()

# Save the plot instead of trying to show it
save_path = BASE_DIR / 'Accuracy_Comparison_Chart.png'
plt.savefig(save_path, dpi=300)
plt.close() # Free up memory

print(f"Chart successfully generated and saved to: {save_path}")