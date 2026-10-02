# app.pyw — точка входа GraphEditor Pro
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PKG  = os.path.join(ROOT, 'grapheditor')

for p in (ROOT, PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(ROOT)


def main():
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "GraphEditorPro.1.2.0")
        except Exception:
            pass

    import tkinter as tk
    from tkinterdnd2 import TkinterDnD
    import main as app_module
    AdvancedGraphEditorApp = app_module.AdvancedGraphEditorApp

    root = TkinterDnD.Tk()

    # ---------- Иконка ----------
    ico_path = os.path.join(ROOT, 'assets', 'icon.ico')
    png_path = os.path.join(ROOT, 'assets', 'icon.png')

    if sys.platform == 'win32' and os.path.exists(ico_path):
        try:
            root.iconbitmap(ico_path)
        except Exception as e: pass
        try:
            root.iconbitmap(default=ico_path)
        except Exception as e: pass
    elif os.path.exists(png_path):
        try:
            _icon = tk.PhotoImage(file=png_path)
            root.iconphoto(True, _icon)
            root._icon_ref = _icon
        except Exception as e: pass
    else:
        print(f"[icon] файл не найден")

    app = AdvancedGraphEditorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()