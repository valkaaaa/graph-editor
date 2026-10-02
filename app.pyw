import os, sys

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

    from tkinterdnd2 import TkinterDnD
    import main as app_module
    AdvancedGraphEditorApp = app_module.AdvancedGraphEditorApp

    root = TkinterDnD.Tk()
    app = AdvancedGraphEditorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()