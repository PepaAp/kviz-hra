import sys
import tkinter as tk

from pathlib import Path

# Přidej src do path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui import WelcomeUI

def main():
    root = tk.Tk()
    root.title("Odhalování obrázku a tajenky")
    root.geometry("1100x950")
    root.configure(bg="#ecf0f1")
    root.resizable(True, True)

    app = WelcomeUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

