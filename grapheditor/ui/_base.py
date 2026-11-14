"""Базовая инфраструктура UI: ресурсы, i18n, история, шрифты,
недавние файлы, поиск, служебные методы.
"""
import os
import sys
import tkinter as tk
import matplotlib as mpl

from tkinter import ttk, messagebox

from translator import (tr, INTERNAL_TYPES, INTERNAL_ANIM_TYPES)
from settings import TOOLTIPS, attach_tooltip


# ============================================================================
# EMOJI ДЛЯ КНОПОК БЕЗ PNG-ИКОНОК
# ============================================================================
EMOJI_FALLBACK = {
    'toolbar.open_json':   '📂',
    'toolbar.save_json':   '💾',
    'toolbar.zip':         '🗜️',
    'toolbar.import_csv':  '⬇️',
    'toolbar.export_csv':  '⬆️',
    'toolbar.export_html': '🌐',
    'toolbar.save_image':  '🖼️',
    'toolbar.undo':        '↶',
    'toolbar.redo':        '↷',
    'create.create_btn':   '➕',
    'create.apply_btn':    '✓',
    'create.palette':      '🎨',
    'gen.generate_btn':    '⚙️',
    'gen.random_btn':      '🎲',
    'obj.load_btn':        '📥',
    'obj.duplicate_btn':   '📋',
    'obj.delete_btn':      '🗑️',
    'obj.clear_btn':       '🧹',
    'obj.add_trend':       '📈',
    'right.anim_start':    '▶',
    'right.anim_pause':    '⏸',
    'right.anim_stop':     '■',
    'right.anim_save':     '💾',
    'right.anim_save_file':'📦',
    'right.anim_load_file':'📂',
    'stats.fit_linear':    '📏',
    'stats.fit_log':       '📐',
    'stats.fit_exp':       '📉',
    'stats.fit_power':     '📊',
    'stats.find_peaks':    '🔍',
    'right.apply':         '✓',
}


class BaseUIMixin:

    # ========================================================================
    # НЕДАВНИЕ ФАЙЛЫ
    # ========================================================================
    def _push_recent(self, path):
        try:
            if not hasattr(self, '_recent_files'):
                self._recent_files = []
            path = os.path.abspath(path)
            if path in self._recent_files:
                self._recent_files.remove(path)
            self._recent_files.insert(0, path)
            self._recent_files = self._recent_files[:15]
            self._rebuild_recent_menu()
        except Exception:
            pass

    def _rebuild_recent_menu(self):
        if not hasattr(self, 'recent_menu'):
            return
        self.recent_menu.delete(0, 'end')
        valid = [p for p in getattr(self, '_recent_files', [])
                 if os.path.exists(p)]
        if not valid:
            self.recent_menu.add_command(
                label=tr.t('menu.file.recent_empty'), state='disabled')
            return
        for p in valid:
            self.recent_menu.add_command(
                label=os.path.basename(p),
                command=lambda path=p: self._open_recent(path))
        self.recent_menu.add_separator()
        self.recent_menu.add_command(
            label=tr.t('menu.file.recent_clear'),
            command=self._clear_recent)

    def _clear_recent(self):
        self._recent_files = []
        self._save_config()
        self._rebuild_recent_menu()

    def _open_recent(self, path):
        if not os.path.exists(path):
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('msg.file_not_found'))
            return
        ext = os.path.splitext(path)[1].lower()
        dispatch = {
            '.json':       self._load_json,
            '.zip':        self._load_zip,
            '.graphx':     self._load_graphx,
            '.csv':        self._import_csv,
            '.xlsx':       self._import_excel,
            '.xls':        self._import_excel,
            '.graphxtpl':  self._import_template_file,
            '.graphxanim': self._load_graphxanim,
            '.graphxtemp': lambda p: self._load_autosave(p),
        }
        fn = dispatch.get(ext)
        if fn:
            fn(path)

    # ========================================================================
    # ПОИСК В ДЕРЕВЕ
    # ПОИСК В ДЕРЕВЕ
    # ========================================================================
    def _focus_search(self):
        for w in self.notebook.winfo_children():
            for child in w.winfo_children():
                try:
                    if isinstance(child, ttk.Entry) and \
                            str(child.cget('textvariable')) == str(self.search_var):
                        child.focus_set()
                        return
                except Exception:
                    pass

    # ========================================================================
    # ИКОНКИ И РЕСУРСЫ
    # ========================================================================
    def _assets_dir(self):
        """Ищет папку assets в корне проекта или в PyInstaller bundle."""
        if getattr(sys, 'frozen', False):
            # PyInstaller: assets распаковываются в _MEIPASS
            base = getattr(sys, '_MEIPASS',
                           os.path.dirname(sys.executable))
            return os.path.join(base, 'assets')

        # Режим исходников:
        # grapheditor/ui/_base.py -> grapheditor/ui -> grapheditor
        here = os.path.dirname(os.path.abspath(__file__))
        pkg_root = os.path.dirname(os.path.dirname(here))
        project_root = os.path.dirname(pkg_root)

        # 1. Пробуем <project_root>/assets (обычный случай)
        project_assets = os.path.join(project_root, 'assets')
        if os.path.isdir(project_assets):
            return project_assets

        # 2. Fallback: <pkg_root>/assets (если assets перенесли внутрь пакета)
        pkg_assets = os.path.join(pkg_root, 'assets')
        if os.path.isdir(pkg_assets):
            return pkg_assets

        # 3. Последний вариант — вернуть project_assets (может не существовать)
        return project_assets

    def _set_window_icon(self):
        """Устанавливает иконку окна. Работает на Windows, Linux, macOS."""
        from grapheditor import __version__

        # Windows: AppUserModelID нужен для правильной группировки в панели задач
        if sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    f"GraphEditorPro.{__version__}")
            except Exception:
                pass

        assets = self._assets_dir()
        ico_path = os.path.join(assets, 'icon.ico')
        png_path = os.path.join(assets, 'icon.png')

        # Windows: сначала .ico (правильно масштабируется в панели задач)
        if sys.platform == 'win32' and os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
                self.root.iconbitmap(default=ico_path)
                return
            except Exception as e:
                print(f"[icon] ico failed: {e}")

        # Linux / macOS (и Windows как fallback): .png
        if os.path.exists(png_path):
            try:
                _icon = tk.PhotoImage(file=png_path)
                self.root.iconphoto(True, _icon)
                self._window_icon = _icon  # защита от GC
                return
            except Exception as e:
                print(f"[icon] png failed: {e}")

        # Нет ни .ico, ни .png — работаем без кастомной иконки

    def _load_icon(self, name, size=20):
        if not hasattr(self, '_icon_cache'):
            self._icon_cache = {}
        cache_key = (name, size)
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        path = os.path.join(self._assets_dir(), 'icons', f'{name}.png')
        if not os.path.exists(path):
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert('RGBA')
            img = img.resize((size, size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._icon_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    # ========================================================================
    # i18n
    # ========================================================================
    def _tr_label(self, parent, key, **kw):
        w = ttk.Label(parent, text=tr.t(key))
        self._i18n_widgets.append((w, 'text', key, {}))
        for k, v in kw.items():
            try:
                w.config(**{k: v})
            except tk.TclError:
                pass
        return w

    def _tr_button(self, parent, key, command, **kw):
        emoji = EMOJI_FALLBACK.get(key, '')
        text = f"{emoji} {tr.t(key)}".strip() if emoji else tr.t(key)
        wrapped = self._with_click_sound(command)
        w = ttk.Button(parent, text=text, command=wrapped, **kw)
        self._i18n_widgets.append((w, 'text', key, {}))
        tip = TOOLTIPS.get(key)
        if tip:
            attach_tooltip(w, tip)
        return w

    def _tr_button_icon(self, parent, key, icon_name, command,
                        icon_size=20, **kw):
        photo = self._load_icon(icon_name, icon_size)
        text = tr.t(key)
        if photo is None:
            return self._tr_button(parent, key, command, **kw)
        wrapped = self._with_click_sound(command)
        w = ttk.Button(parent, text=text, image=photo, compound='left',
                       command=wrapped, **kw)
        self._i18n_widgets.append((w, 'text', key, {}))
        tip = TOOLTIPS.get(key)
        if tip:
            attach_tooltip(w, tip)
        return w

    def _tr_checkbutton(self, parent, key, variable, command=None, **kw):
        w = ttk.Checkbutton(parent, text=tr.t(key),
                            variable=variable, command=command, **kw)
        self._i18n_widgets.append((w, 'text', key, {}))
        return w

    def _tr_labelframe(self, parent, key, **kw):
        w = ttk.LabelFrame(parent, text=tr.t(key), **kw)
        self._i18n_widgets.append((w, 'text', key, {}))
        return w

    def _switch_lang(self, lang):
        if lang == tr.lang:
            return
        tr.set_lang(lang)
        self.settings['language'] = lang
        new_lang_name = tr.t('settings.lang_' + lang)

        for widget, attr, key, kwargs in list(self._i18n_widgets):
            try:
                has_image = False
                try:
                    if isinstance(widget, ttk.Button):
                        has_image = bool(widget.cget('image'))
                except Exception:
                    pass
                if has_image:
                    widget.config(text=tr.t(key, **kwargs))
                else:
                    emoji = EMOJI_FALLBACK.get(key, '')
                    text = (f"{emoji} {tr.t(key, **kwargs)}".strip()
                            if emoji else tr.t(key, **kwargs))
                    widget.config(text=text)
            except tk.TclError:
                self._i18n_widgets.remove((widget, attr, key, kwargs))

        self._build_menu()

        self.type_combo['values'] = [tr.type_name(t)
                                     for t in INTERNAL_TYPES]
        current_internal = tr.find_type_by_display(self.type_var.get())
        self.type_var.set(tr.type_name(current_internal))
        if hasattr(self, 'type_btn'):
            self.type_btn.configure(textvariable=self.type_var)

        self.anim_combo['values'] = [tr.anim_name(a)
                                     for a in INTERNAL_ANIM_TYPES]
        current_anim = tr.find_anim_by_display(self.anim_type_var.get())
        self.anim_type_var.set(tr.anim_name(current_anim))

        self.notebook.tab(0, text=tr.t('tab.create'))
        self.notebook.tab(1, text=tr.t('tab.generator'))
        self.notebook.tab(2, text=tr.t('tab.objects'))
        self.notebook.tab(3, text=tr.t('tab.stats'))

        self.rnd_shape_combo['values'] = [
            tr.t('gen.rnd_shape_2d'),
            tr.t('gen.rnd_shape_3d'),
            tr.t('gen.rnd_shape_3d_grid')]

        self.status_var.set(tr.t('status.ready'))
        self._update_listbox()
        self._redraw()
        self._show_history(tr.t('hist.lang_changed', lang=new_lang_name))

    # ========================================================================
    # ИСТОРИЯ / ШРИФТЫ
    # ========================================================================
    def _show_history(self, text):
        self.history_var.set(f"🕐 {text}")
        if self._history_after_id:
            try:
                self.root.after_cancel(self._history_after_id)
            except Exception:
                pass
        self._history_after_id = self.root.after(
            4000, lambda: self.history_var.set(""))

    def _apply_font_settings(self):
        s = self.settings
        mpl.rcParams['font.family'] = s['font_family']
        mpl.rcParams['font.size'] = s['font_base']
        mpl.rcParams['axes.titlesize'] = s['font_title']
        mpl.rcParams['axes.labelsize'] = s['font_labels']
        mpl.rcParams['legend.fontsize'] = s['font_legend']
        mpl.rcParams['xtick.labelsize'] = s['font_ticks']
        mpl.rcParams['ytick.labelsize'] = s['font_ticks']
        mpl.rcParams['axes.linewidth'] = s['axis_lw']
        if hasattr(self, 'canvas'):
            self._redraw_all()

    # ========================================================================
    # ПАНЕЛЬ ДОКУМЕНТОВ / РАЗНОЕ
    # ========================================================================
    def _build_documents_bar(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, before=self.plot_notebook)
        ttk.Button(bar, text="＋ Новый документ",
                   command=lambda: self._new_document(switch=True)
                   ).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(bar, text="✕ Закрыть",
                   command=lambda: self._close_document(self.current_doc_idx)
                   ).pack(side=tk.LEFT, padx=2, pady=2)

    def _toggle_fullscreen(self):
        self._fullscreen = not getattr(self, '_fullscreen', False)
        self.root.attributes('-fullscreen', self._fullscreen)

    def _on_delete_key(self, event=None):
        if self.root.focus_get() == self.graph_tree:
            self._delete_graph()
            return "break"