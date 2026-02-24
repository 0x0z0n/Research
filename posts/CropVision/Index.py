import sys
import subprocess
from tkinter import *
from tkinter import messagebox

# Get the current Python interpreter path (Linux safe)
PYTHON_CMD = sys.executable

def run_script(script_name):
    print(f"Launching {script_name}...")
    try:
        # Popen runs the script in the background so the GUI doesn't freeze
        subprocess.Popen([PYTHON_CMD, script_name])
    except Exception as e:
        messagebox.showerror("Execution Error", f"Failed to run {script_name}\nError: {str(e)}")

def datapreprocessing():
    run_script("fe.py")

def svm():
    run_script("svm.py")

def dtree():
    run_script("decisiontree.py")

def plotloss():
    run_script("comparison.py")

def lr():
    run_script("logisticregression.py")

def cnn():
    run_script("cnn.py")

def appopen():
    run_script("app.py")

def exit_app():
    root.destroy()

# Setting title for the window
root = Tk()
root.configure(background="white")
root.title("Leaf Disease Prediction System")

# Creating a text label
Label(root, text="Leaf Disease Prediction System", font=("times new roman", 20), fg="white", bg="#795548",
      height=2).grid(row=0, rowspan=2, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

# Creating buttons
Button(root, text="Data Preprocessing", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=datapreprocessing).grid(
    row=5, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Decision Tree", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=dtree).grid(
    row=6, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="SVM", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=svm).grid(
    row=7, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Logistic Regression", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=lr).grid(
    row=8, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Model Training using CNN", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=cnn).grid(
    row=9, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Accuracy Comparison", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=plotloss).grid(
    row=10, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Leaf Disease Prediction Web App", font=('times new roman', 20), bg="#bcaaa4", fg="#3e2723", command=appopen).grid(
    row=11, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

Button(root, text="Exit", font=('times new roman', 20), bg="#795548", fg="white", command=exit_app).grid(
    row=12, columnspan=2, sticky=N + E + W + S, padx=5, pady=5)

if __name__ == '__main__':
    root.mainloop()