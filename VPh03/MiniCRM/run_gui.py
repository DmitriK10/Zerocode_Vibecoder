# run_gui.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk
print("sys.path:", sys.path)

from gui.main_window import MainWindow

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()