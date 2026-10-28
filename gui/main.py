
"""RainfallDigitizer GUI launcher."""

import os
import sys
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.app import ReviewApp


def main():
    root = tk.Tk()
    app = ReviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
