"""Главное меню, темы, плагины.

Содержит:
  - _build_menu — полное меню приложения
  - _populate_theme_menu, _delete_theme, _open_theme_editor
  - _open_plugins_folder, _reload_plugins, _show_plugins_list
"""
import os
import sys
import tkinter as tk

from tkinter import ttk, messagebox, colorchooser, Menu

from translator import tr, INTERNAL_TYPES
from themes import (THEMES, THEME_KEYS, is_custom_theme,
                    save_custom_theme, delete_custom_theme,
                    theme_key_from_name)


class MenuUIMixin:

    # ========================================================================
    # ГЛАВНОЕ МЕНЮ
    # ========================================================================
    def _build_menu(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, Menu):
                widget.destroy()

        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        # Файл
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=tr.t('menu.file'), menu=self.filemenu)
        self.filemenu.add_command(label=tr.t('menu.file.open_json'),
                                  accelerator="Ctrl+O", command=self._load_json)
        self.filemenu.add_command(label=tr.t('menu.file.save_json'),
                                  accelerator="Ctrl+S", command=self._save_json)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('menu.file.open_zip'),
                                  command=self._load_zip)
        self.filemenu.add_command(label=tr.t('menu.file.save_zip'),
                                  command=self._save_zip)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('file.open_graphx'),
                                  command=self._load_graphx)
        self.filemenu.add_command(label=tr.t('file.save_graphx'),
                                  command=self._save_graphx)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('menu.file.import_csv'),
                                  command=self._import_csv)
        self.filemenu.add_command(label=tr.t('menu.file.export_csv'),
                                  command=self._export_csv)
        self.filemenu.add_command(label=tr.t('menu.file.import_excel'),
                                  command=self._import_excel)
        self.filemenu.add_command(label=tr.t('menu.file.export_excel'),
                                  command=self._export_excel)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('menu.file.save_image'),
                                  command=self._save_image)
        self.filemenu.add_command(label=tr.t('menu.file.export_html'),
                                  command=self._export_html)
        self.filemenu.add_command(label=tr.t('menu.file.export_pdf'),
                                  command=self.export_pdf)
        self.filemenu.add_command(label=tr.t('menu.file.export_python'),
                                  command=self.export_python_code)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('menu.file.console'),
                                  accelerator="Ctrl+`",
                                  command=self._open_console)
        self.filemenu.add_command(label=tr.t('menu.file.tour'),
                                  command=self._start_onboarding)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=tr.t('menu.file.settings'),
                                  command=self._open_settings)
        # === НЕДАВНИЕ ФАЙЛЫ ===
        self.filemenu.add_separator()
        self.recent_menu = Menu(self.filemenu, tearoff=0)
        self.filemenu.add_cascade(label=tr.t('menu.file.recent'),
                                  menu=self.recent_menu)
        self._rebuild_recent_menu()

        # Правка
        self.editmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=tr.t('menu.edit'), menu=self.editmenu)
        self.editmenu.add_command(label=tr.t('menu.edit.undo'),
                                  accelerator="Ctrl+Z", command=self._undo)
        self.editmenu.add_command(label=tr.t('menu.edit.redo'),
                                  accelerator="Ctrl+Y", command=self._redo)
        self.editmenu.add_separator()
        self.editmenu.add_command(label=tr.t('menu.edit.duplicate'),
                                  accelerator="Ctrl+D",
                                  command=self._duplicate_graph)
        self.editmenu.add_command(label=tr.t('menu.edit.notes'),
                                  command=self._edit_notes)
        self.editmenu.add_separator()
        # === ПАЛИТРА ===
        palette_menu = Menu(self.editmenu, tearoff=0)
        try:
            from grapheditor.palettes import PALETTES
        except ImportError:
            from palettes import PALETTES
        for key, label in PALETTES.items():
            palette_menu.add_command(
                label=label,
                command=lambda k=key: self._apply_palette(k))
        self.editmenu.add_cascade(label=tr.t('menu.edit.palette'),
                                  menu=palette_menu)
        self.editmenu.add_command(
            label=tr.t('menu.edit.palette_dialog'),
            command=self._show_palette_dialog)
        self.editmenu.add_separator()
        self.editmenu.add_command(label=tr.t('menu.edit.clear_all'),
                                  command=self._clear_all)

        # Шаблоны
        self.templatemenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=tr.t('menu.templates'),
                                 menu=self.templatemenu)
        for key, name in [
            ('menu.templates.empty', 'empty'),
            ('menu.templates.sine', 'sine'),
            ('menu.templates.damped', 'damped'),
            ('menu.templates.distribution', 'distribution'),
            ('menu.templates.spiral3d', 'spiral3d'),
        ]:
            self.templatemenu.add_command(
                label=tr.t(key),
                command=lambda n=name: self._apply_template(n))
        self.templatemenu.add_separator()
        for key, name in [
            ('menu.templates.trig', 'trig'),
            ('menu.templates.distributions', 'distributions'),
            ('menu.templates.dashboard', 'dashboard'),
            ('menu.templates.fitting', 'fitting'),
            ('menu.templates.showcase', 'showcase'),
            ('menu.templates.fractal', 'fractal'),
        ]:
            self.templatemenu.add_command(
                label=tr.t(key),
                command=lambda n=name: self._apply_template(n))
        self.templatemenu.add_separator()
        self.templatemenu.add_command(
            label=tr.t('menu.templates.save_current'),
            command=self._save_as_template)
        self.templatemenu.add_command(
            label=tr.t('menu.templates.open_folder'),
            command=self._open_templates_folder)
        tpls = self._list_user_templates()
        if tpls:
            sub = Menu(self.templatemenu, tearoff=0)
            for name, path in tpls:
                sub.add_command(
                    label=name,
                    command=lambda p=path: self._load_template_file(p))
            self.templatemenu.add_cascade(
                label=tr.t('menu.templates.my'), menu=sub)
        self.templatemenu.add_separator()
        self.templatemenu.add_command(
            label=tr.t('menu.templates.export'),
            command=self._export_template_file)
        self.templatemenu.add_command(
            label=tr.t('menu.templates.import'),
            command=self._import_template_file)

        # === ПЛАГИНЫ ===
        self.pluginmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=tr.t('menu.plugins'),
                                 menu=self.pluginmenu)
        self.pluginmenu.add_command(
            label=tr.t('menu.plugins.open_folder'),
            command=self._open_plugins_folder)
        self.pluginmenu.add_command(
            label=tr.t('menu.plugins.reload'),
            command=self._reload_plugins)
        self.pluginmenu.add_separator()
        self.pluginmenu.add_command(
            label=tr.t('menu.plugins.list'),
            command=self._show_plugins_list)

        # Вид
        self.viewmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=tr.t('menu.view'), menu=self.viewmenu)
        for key, var, cmd in [
            ('menu.view.legend', self.show_legend_var, self._update_legend),
            ('menu.view.axes', self.show_axes_var, self._update_axes),
        ]:
            self.viewmenu.add_checkbutton(label=tr.t(key),
                                          variable=var, command=cmd)
        self.viewmenu.add_separator()
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.smooth'),
            variable=self.smooth_var, command=self._redraw_all)
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.tooltip'),
            variable=self.show_tooltip_var, command=self._redraw_all)
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.crosshair'),
            variable=self.crosshair_enabled,
            command=self._toggle_crosshair)
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.drag_points'),
            variable=self.drag_points_enabled)
        self.viewmenu.add_separator()
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.panel_settings'),
            variable=self.show_settings_var,
            command=self._toggle_ui_panels)
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.panel_limits'),
            variable=self.show_limits_var,
            command=self._toggle_ui_panels)
        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.panel_anim'),
            variable=self.show_anim_var,
            command=self._toggle_ui_panels)
        self.viewmenu.add_separator()

        # Подменю тем
        self.theme_menu = Menu(self.viewmenu, tearoff=0)
        self.viewmenu.add_cascade(label=tr.t('menu.view.theme'),
                                  menu=self.theme_menu)
        if not hasattr(self, 'theme_var'):
            self.theme_var = tk.StringVar(
                value=self.settings.get('theme', 'light'))
        self._populate_theme_menu()

        self.viewmenu.add_checkbutton(
            label=tr.t('menu.view.live_preview'),
            variable=self.live_preview_var)

    # ========================================================================
    # ТЕМЫ
    # ========================================================================
    def _populate_theme_menu(self):
        menu = self.theme_menu
        menu.delete(0, 'end')

        current = self.settings.get('theme', 'light')

        built_in = [(k, v) for k, v in THEMES.items()
                    if not v.get('custom', False)]
        for key, t in built_in:
            menu.add_radiobutton(
                label=t.get('name', key), variable=self.theme_var,
                value=key, command=lambda k=key: self._set_theme(k))

        custom = [(k, v) for k, v in THEMES.items()
                  if v.get('custom', False)]
        if custom:
            menu.add_separator()
            for key, t in custom:
                menu.add_radiobutton(
                    label='⭐ ' + t.get('name', key),
                    variable=self.theme_var, value=key,
                    command=lambda k=key: self._set_theme(k))

        menu.add_separator()
        menu.add_command(label=tr.t('menu.view.theme.create'),
                         command=lambda: self._open_theme_editor(None))
        if is_custom_theme(current):
            menu.add_command(
                label=tr.t('menu.view.theme.edit'),
                command=lambda: self._open_theme_editor(current))
            menu.add_command(
                label=tr.t('menu.view.theme.delete'),
                command=lambda: self._delete_theme(current))

    def _delete_theme(self, name):
        if not is_custom_theme(name):
            messagebox.showinfo(
                tr.t('msg.info'),
                tr.t('theme.editor.cannot_delete_builtin'))
            return
        display = THEMES.get(name, {}).get('name', name)
        if not messagebox.askyesno(
                tr.t('msg.confirm'),
                f"Удалить тему «{display}»?"):
            return
        try:
            delete_custom_theme(name)
            THEMES.pop(name, None)
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))
            return
        self._set_theme('light')
        self.theme_var.set('light')
        self._populate_theme_menu()
        self._show_history(tr.t('theme.deleted', name=display))

    def _open_theme_editor(self, name=None):
        if name and not is_custom_theme(name):
            base = dict(THEMES[name])
            base['name'] = tr.t('theme.copy_of',
                                name=THEMES[name].get('name', name))
            name = None
        else:
            base = dict(THEMES.get(name, THEMES['light']))

        win = tk.Toplevel(self.root)
        win.title(tr.t('theme.editor.title'))
        win.transient(self.root)
        win.geometry("500x640")

        top = ttk.Frame(win, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text=tr.t('theme.editor.name')).grid(
            row=0, column=0, sticky=tk.W)
        name_var = tk.StringVar(value=base.get('name', ''))
        ttk.Entry(top, textvariable=name_var, width=30).grid(
            row=0, column=1, padx=5, sticky=tk.EW)

        dark_var = tk.BooleanVar(value=base.get('is_dark', True))
        ttk.Checkbutton(top, text=tr.t('theme.editor.dark'),
                        variable=dark_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(6, 0))

        ttk.Label(top, text=tr.t('theme.editor.mpl_style')).grid(
            row=2, column=0, sticky=tk.W, pady=(6, 0))
        mpl_style_var = tk.StringVar(
            value=base.get('mpl_style', 'dark_background'))
        ttk.Combobox(top, textvariable=mpl_style_var,
                     values=['default', 'dark_background', 'ggplot',
                             'seaborn-v0_8', 'bmh'],
                     state='readonly', width=20).grid(
            row=2, column=1, padx=5, sticky=tk.W, pady=(6, 0))
        top.columnconfigure(1, weight=1)

        colors_frame = ttk.LabelFrame(win,
                                      text=tr.t('theme.editor.colors'),
                                      padding=8)
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        color_vars = {}
        for key, label_key in THEME_KEYS:
            row = ttk.Frame(colors_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=tr.t(label_key) + ":",
                      width=22, anchor=tk.W).pack(side=tk.LEFT)

            var = tk.StringVar(value=base.get(key, '#000000'))
            color_vars[key] = var

            prev = tk.Label(row, text='  ', bg=var.get(), width=4,
                            relief=tk.SOLID, borderwidth=1)
            prev.pack(side=tk.LEFT, padx=(2, 6))

            ttk.Entry(row, textvariable=var, width=12).pack(
                side=tk.LEFT, padx=(0, 4))

            def make_picker(v=var, p=prev):
                def pick():
                    c = colorchooser.askcolor(
                        title=tr.t('theme.editor.pick'),
                        initialcolor=v.get())
                    if c[1]:
                        v.set(c[1])
                        p.config(bg=c[1])
                return pick
            ttk.Button(row, text=tr.t('theme.editor.pick'),
                       command=make_picker()).pack(side=tk.LEFT)

            def make_trace(v=var, p=prev):
                def update(*_):
                    try:
                        p.config(bg=v.get())
                    except Exception:
                        pass
                return update
            var.trace_add('write', make_trace())

        btn_frame = ttk.Frame(win, padding=8)
        btn_frame.pack(fill=tk.X)

        def collect():
            return {
                'name': name_var.get().strip(),
                'is_dark': dark_var.get(),
                'mpl_style': mpl_style_var.get(),
                'custom': True,
                **{k: v.get() for k, v in color_vars.items()},
            }

        def do_preview():
            THEMES['__preview__'] = collect()
            self._apply_theme('__preview__')

        def do_save():
            t = collect()
            display_name = t['name']
            if not display_name:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('theme.editor.need_name'))
                return
            key = theme_key_from_name(display_name)
            if not key:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('theme.editor.bad_name'))
                return
            if key in THEMES and not THEMES[key].get('custom', False):
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('theme.editor.bad_name'))
                return
            if key in THEMES and THEMES[key].get('custom', False):
                if not messagebox.askyesno(
                        tr.t('msg.confirm'),
                        tr.t('theme.editor.name_exists')):
                    return
            try:
                THEMES.pop('__preview__', None)
                save_custom_theme(key, t)
                t['custom'] = True
                THEMES[key] = t
            except Exception as e:
                messagebox.showerror(tr.t('msg.error'), str(e))
                return
            self.settings['theme'] = key
            self.theme_var.set(key)
            self._apply_theme(key)
            self._populate_theme_menu()
            self._show_history(tr.t('theme.saved', name=display_name))
            win.destroy()

        def do_cancel():
            THEMES.pop('__preview__', None)
            self._apply_theme(self.settings.get('theme', 'light'))
            win.destroy()

        ttk.Button(btn_frame, text=tr.t('theme.editor.preview'),
                   command=do_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text=tr.t('theme.editor.cancel'),
                   command=do_cancel).pack(side=tk.RIGHT, padx=2)
        ttk.Button(btn_frame, text=tr.t('theme.editor.save'),
                   command=do_save).pack(side=tk.RIGHT, padx=2)
        win.protocol("WM_DELETE_WINDOW", do_cancel)

    # ========================================================================
    # ПЛАГИНЫ
    # ========================================================================
    def _open_plugins_folder(self):
        try:
            from plugins import ensure_plugins_dir, PLUGINS_DIR
        except ImportError:
            from grapheditor.plugins import ensure_plugins_dir, PLUGINS_DIR
        ensure_plugins_dir()
        try:
            if os.name == 'nt':
                os.startfile(PLUGINS_DIR)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', PLUGINS_DIR])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', PLUGINS_DIR])
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _reload_plugins(self):
        if not messagebox.askyesno(
                tr.t('msg.confirm'),
                tr.t('msg.plugins_reload_confirm')):
            return
        try:
            from plugins import load_plugins
        except ImportError:
            from grapheditor.plugins import load_plugins
        try:
            self.plugin_registry = load_plugins(self)
            self.type_combo['values'] = [tr.type_name(t)
                                         for t in INTERNAL_TYPES]
            msg = tr.t('msg.plugins_loaded',
                       count=len(self.plugin_registry.chart_types))
            if self.plugin_registry.errors:
                msg += "\n\n" + tr.t(
                    'msg.plugins_errors',
                    count=len(self.plugin_registry.errors))
            messagebox.showinfo(tr.t('msg.info'), msg)
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _show_plugins_list(self):
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.plugins_list_title'))
        win.transient(self.root)
        win.geometry('560x420')

        ttk.Label(win, text=tr.t('msg.plugins_warning'),
                  foreground='#c0392b', wraplength=520
                  ).pack(anchor=tk.W, padx=10, pady=(8, 4))

        txt = tk.Text(win, wrap=tk.WORD, font=('Consolas', 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        lines = []
        lines.append(tr.t('msg.plugins_list_header',
                          count=len(self.plugin_registry.chart_types)))
        lines.append('')
        for tid, td in self.plugin_registry.chart_types.items():
            disp = td.display.get(tr.lang) or td.display.get('en') or tid
            lines.append(f"• {disp}   (id: {tid})")
            lines.append(f"    fields: {', '.join(td.fields)}")
            lines.append(f"    projection: {td.projection}")
            lines.append('')
        if self.plugin_registry.errors:
            lines.append(tr.t('msg.plugins_errors_header'))
            for name, tb in self.plugin_registry.errors:
                lines.append(f"[{name}]")
                lines.append(tb)
                lines.append('')

        txt.insert('1.0', '\n'.join(lines))
        txt.configure(state='disabled')

        ttk.Button(win, text=tr.t('msg.pdf_cancel'),
                   command=win.destroy).pack(pady=(0, 10))