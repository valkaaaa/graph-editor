try:
    import tkinter as tk
    import imageio_ffmpeg
    import matplotlib as mpl
    from tkinter import messagebox
    from tkinterdnd2 import TkinterDnD

    from translator import (tr, INTERNAL_TYPES, INTERNAL_ANIM_TYPES,
                            TRANSLATIONS)
    from ui import UIMixin
    from plots import PlotsMixin
    from animations import AnimationsMixin
    from templates import TemplatesMixin
    from themes import ThemesMixin, THEMES
    from config import load_config, save_config
    from autosave import AutosaveMixin
    from documents import DocumentsMixin

    from palettes import PalettesMixin
    from code_export import CodeExportMixin
    from pdf_export import PdfExportMixin
    from clipboard import ClipboardMixin
    from shortcuts import ShortcutsMixin
    from autotheme import AutoThemeMixin
    from sounds import SoundMixin
    from plugins import load_plugins
except ImportError as e:
    from tkinter import messagebox
    messagebox.showerror("ImportError", str(e))
    raise
except Exception as e:
    from tkinter import messagebox
    messagebox.showerror("Error", str(e))
    raise


# Языки, которые есть в TRANSLATIONS — для автоопределения
_TRANSLATIONS_KEYS = set(TRANSLATIONS.keys())

_LANG_ALIASES = {
    'ua': 'ua',
    'by': 'by',
    'kz': 'kz',
    'ja': 'ja',
    'kr': 'kr',
    'zh': 'zh',
    'ru': 'ru'
}


def _detect_system_language():
    """Пытается определить язык системы для первого запуска."""
    try:
        import locale
        sys_lang = (locale.getdefaultlocale()[0] or 'en')[:2].lower()
        sys_lang = _LANG_ALIASES.get(sys_lang, sys_lang)
        if sys_lang in _TRANSLATIONS_KEYS:
            return sys_lang
    except Exception:
        pass
    return None


class AdvancedGraphEditorApp(
    UIMixin,
    PlotsMixin,
    AnimationsMixin,
    TemplatesMixin,
    ThemesMixin,
    DocumentsMixin,
    AutosaveMixin,
    PalettesMixin,
    CodeExportMixin,
    PdfExportMixin,
    ClipboardMixin,
    ShortcutsMixin,
    AutoThemeMixin,
    SoundMixin,
):
    def __init__(self, root, geometry="1250x1250",
                 title="GraphEditor Pro v1.5.0"):
        self.root = root
        self.root.title(title)
        self.root.geometry(geometry)

        # ---------- Данные ----------
        self.graphs_data = []
        self.line_counter = 0
        self._clipboard = []

        # ---------- Subplots ----------
        self.subplot_rows = 1
        self.subplot_cols = 1
        self.axes = []
        self.axes_secondary = {}
        self.ax = None

        # ---------- Анимация ----------
        self.current_animation = None
        self.anim_paused = False
        self.anim_frame = 0
        self.anim_frames_total = 200
        self.anim_params = {
            'particles_n': 200,
            'heatmap_size': 40,
            'heatmap_alpha': 0.25,
            'cellular_size': 50,
            'cellular_density': 0.3,
        }

        # ---------- Undo / Redo ----------
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo = 50

        # ---------- Папки ----------
        self.folders = [""]
        self.hidden_folders = set()

        # ---------- Настройки ----------
        self.settings = {
            'smooth_window': 5,
            'default_color': 'blue',
            'default_lw': 2.0,
            'default_marker': 'o',
            'font_family': 'DejaVu Sans',
            'font_base': 10,
            'font_title': 12,
            'font_labels': 10,
            'font_legend': 9,
            'font_ticks': 9,
            'axis_lw': 1.0,
            'language': 'ru',
            'theme': 'light',
            'show_tour_on_start': False,
            # ---- новые ключи ----
            'hotkeys': {},                  # action_id -> seq
            'auto_theme_by_time': False,
            'theme_day_start': 7,
            'theme_day_end': 19,
            'theme_day': 'light',
            'theme_night': 'dark',
        }

        self.tooltip_annot = None
        self._crosshair_v = None
        self._crosshair_h = None
        self._history_after_id = None
        self._i18n_widgets = []
        self._onboarding_step = 0
        self._onboarding_widgets = []
        self._console_window = None

        # ---------- Drag ----------
        self._drag_active = False
        self._drag_obj_idx = None
        self._drag_point_idx = None
        self._drag_count_in_session = 0

        # ---------- Переменные Tk ----------
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.show_axes_var = tk.BooleanVar(value=True)
        self.show_tooltip_var = tk.BooleanVar(value=True)
        self.crosshair_enabled = tk.BooleanVar(value=True)
        self.drag_points_enabled = tk.BooleanVar(value=False)
        self.smooth_var = tk.BooleanVar(value=False)
        self.show_settings_var = tk.BooleanVar(value=True)
        self.show_limits_var = tk.BooleanVar(value=True)
        self.show_anim_var = tk.BooleanVar(value=True)
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.live_preview_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value='light')

        self.plot_title_var = tk.StringVar(value="График")
        self.plot_xlabel_var = tk.StringVar(value="X")
        self.plot_ylabel_var = tk.StringVar(value="Y")
        self.history_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value=tr.t('status.ready'))
        self.type_var = tk.StringVar(value=tr.type_name("Линия"))
        self.anim_type_var = tk.StringVar(value=tr.anim_name("Нет"))
        self.subplot_grid_var = tk.StringVar(value='1x1')
        self.subplot_index_var = tk.IntVar(value=0)

        # ---------- Конфиг ----------
        saved = load_config()
        if isinstance(saved.get('settings'), dict):
            self.settings.update(saved['settings'])
        self._recent_files = saved.get('recent', [])
        self._saved_geometry = saved.get('geometry')

        # ---------- Автоопределение языка при первом запуске ----------
        if 'language' not in saved.get('settings', {}):
            detected = _detect_system_language()
            if detected:
                self.settings['language'] = detected

        # ---------- Текущая тема ----------
        self.current_theme = self.settings.get('theme', 'light')

        tr.set_lang(self.settings.get('language', 'ru'))

        # ---------- Плагины ----------
        self.plugin_registry = load_plugins(self)

        # ---------- Звуки ------------
        self._init_sounds()

        # ---------- Сборка ----------
        self._build_ui()
        self._init_documents()          # создаёт первую вкладку + _setup_plot
        self._apply_font_settings()

        self.root.drop_target_register('DND_Files')
        self.root.dnd_bind('<<Drop>>', self._on_drop)

        self._build_menu()
        self._bind_hotkeys()            # ShortcutsMixin

        try:
            self._set_window_icon()
        except Exception:
            pass

        self._apply_theme(self.current_theme)
        self._init_auto_theme()         # AutoThemeMixin

        if self._saved_geometry:
            try:
                self.root.geometry(self._saved_geometry)
            except Exception:
                pass

        self.root.after(500, self._maybe_start_onboarding)

        # ---------- Автосохранение ----------
        self._init_autosave(interval_ms=60_000)
        self.root.after(800, self._check_autosave_on_start)

        # ---------- Закрытие окна ----------
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        mpl.rcParams['animation.ffmpeg_path'] = \
            imageio_ffmpeg.get_ffmpeg_exe()

    # ---------------------------------------------------------------
    def _on_close(self):
        # Спросить про несохранённые документы
        for i, d in enumerate(list(self.documents)):
            if getattr(d, 'modified', False):
                ans = messagebox.askyesnocancel(
                    "Выход",
                    f"Документ «{d.name}» изменён.\n"
                    f"Сохранить перед выходом?",
                    parent=self.root)
                if ans is None:
                    return
                if ans is True:
                    self._switch_document(i)
                    self._save_json()
        try:
            self._save_config()
        except Exception:
            pass
        self.root.destroy()

    def _save_config(self):
        save_config({
            'settings': self.settings,
            'recent': getattr(self, '_recent_files', [])[:15],
            'geometry': self.root.geometry(),
        })

    def _save_json_as(self):
        from tkinter import filedialog
        import json
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = [{k: v for k, v in d.items() if k != 'artist'}
                for d in self.graphs_data]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4,
                          default=lambda o: o.tolist()
                          if hasattr(o, 'tolist') else o)
            if self.current_doc_idx >= 0:
                self.documents[self.current_doc_idx].path = path
                self.documents[self.current_doc_idx].modified = False
            self._show_history(f"Сохранено: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


def main():
    import sys
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "GraphEditorPro.1.5.0")
        except Exception as e:
            print(e)

    root = TkinterDnD.Tk()
    app = AdvancedGraphEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()