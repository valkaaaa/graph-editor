import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(ROOT, 'grapheditor')

for p in (ROOT, PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(ROOT)


def main():
    import tkinter as tk
    from tkinterdnd2 import TkinterDnD
    from grapheditor.main import AdvancedGraphEditorApp

    root = TkinterDnD.Tk()
    app = AdvancedGraphEditorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()