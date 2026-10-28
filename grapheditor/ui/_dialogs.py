"""Диалоги: настройки, Python-консоль, онбординг."""
import os
import tkinter as tk
import numpy as np
import matplotlib as mpl

from tkinter import ttk, messagebox, filedialog

from translator import tr, SUPPORTED_LANGS
from settings import FONTS


class DialogsUIMixin:

    # ========================================================================
    # НАСТРОЙКИ
    # ========================================================================
    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.settings_title'))
        win.transient(self.root)
        win.geometry("440x980")

        # Язык
        ttk.Label(win, text=tr.t('settings.language'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(10, 2))

        label_to_code = {label: code for code, label in SUPPORTED_LANGS}
        code_to_label = {code: label for code, label in SUPPORTED_LANGS}

        current = self.settings.get('language', 'ru')
        if current not in code_to_label:
            current = 'en'

        lang_var = tk.StringVar(value=code_to_label[current])
        ttk.Combobox(win, textvariable=lang_var,
                     values=[lbl for _, lbl in SUPPORTED_LANGS],
                     state='readonly', width=30).pack(
            anchor=tk.W, padx=10)

        # Тема
        ttk.Label(win, text=tr.t('settings.theme'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        theme_var = tk.StringVar(
            value=self.settings.get('theme', 'light'))
        ttk.Combobox(win, textvariable=theme_var,
                     values=[k for k, _ in self._list_themes()],
                     state='readonly', width=25).pack(
            anchor=tk.W, padx=10)

        # === Авто-тема по времени ===
        ttk.Label(win, text=tr.t('settings.auto_theme'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))

        if not hasattr(self, '_auto_theme_var'):
            self._auto_theme_var = tk.BooleanVar(
                value=self.settings.get('auto_theme_by_time', False))
        ttk.Checkbutton(win, text=tr.t('settings.auto_theme_by_time'),
                        variable=self._auto_theme_var,
                        command=self._toggle_auto_theme).pack(
            anchor=tk.W, padx=10)

        row_at = ttk.Frame(win)
        row_at.pack(anchor=tk.W, padx=10, pady=(4, 0))
        ttk.Label(row_at,
                  text=tr.t('settings.theme_day_start')).pack(
            side=tk.LEFT)
        day_start_var = tk.IntVar(
            value=self.settings.get('theme_day_start', 7))
        ttk.Spinbox(row_at, from_=0, to=23,
                    textvariable=day_start_var, width=4).pack(
            side=tk.LEFT, padx=3)
        ttk.Label(row_at,
                  text=tr.t('settings.theme_day_end')).pack(
            side=tk.LEFT)
        day_end_var = tk.IntVar(
            value=self.settings.get('theme_day_end', 19))
        ttk.Spinbox(row_at, from_=0, to=23,
                    textvariable=day_end_var, width=4).pack(
            side=tk.LEFT, padx=3)

        row_at2 = ttk.Frame(win)
        row_at2.pack(anchor=tk.W, padx=10, pady=(4, 0))
        ttk.Label(row_at2,
                  text=tr.t('settings.theme_day')).pack(side=tk.LEFT)
        theme_day_var = tk.StringVar(
            value=self.settings.get('theme_day', 'light'))
        ttk.Combobox(row_at2, textvariable=theme_day_var, width=12,
                     state='readonly',
                     values=[k for k, _ in self._list_themes()]).pack(
            side=tk.LEFT, padx=3)
        ttk.Label(row_at2,
                  text=tr.t('settings.theme_night')).pack(
            side=tk.LEFT, padx=(10, 0))
        theme_night_var = tk.StringVar(
            value=self.settings.get('theme_night', 'dark'))
        ttk.Combobox(row_at2, textvariable=theme_night_var, width=12,
                     state='readonly',
                     values=[k for k, _ in self._list_themes()]).pack(
            side=tk.LEFT, padx=3)

        # === Горячие клавиши ===
        ttk.Label(win, text=tr.t('hotkey.section'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        ttk.Button(win, text=tr.t('hotkey.open_editor'),
                   command=self._open_hotkey_editor).pack(
            anchor=tk.W, padx=10)

        # Сглаживание
        ttk.Label(win, text=tr.t('settings.smooth'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        smooth_var = tk.IntVar(value=self.settings['smooth_window'])
        ttk.Label(win,
                  text=tr.t('settings.smooth_window')).pack(
            anchor=tk.W, padx=10)
        ttk.Spinbox(win, from_=1, to=100,
                    textvariable=smooth_var, width=10).pack(
            anchor=tk.W, padx=10)

        # Шрифты
        ttk.Label(win, text=tr.t('settings.fonts'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        font_family_var = tk.StringVar(
            value=self.settings['font_family'])
        ttk.Label(win,
                  text=tr.t('settings.font_family')).pack(
            anchor=tk.W, padx=10)
        ttk.Combobox(win, textvariable=font_family_var,
                     values=FONTS, width=25,
                     state="readonly").pack(anchor=tk.W, padx=10)
        font_vars = {}
        for key, label_key in [
            ('font_base', 'settings.font_base'),
            ('font_title', 'settings.font_title'),
            ('font_labels', 'settings.font_labels'),
            ('font_legend', 'settings.font_legend'),
            ('font_ticks', 'settings.font_ticks'),
        ]:
            ttk.Label(win, text=f"{tr.t(label_key)}:").pack(
                anchor=tk.W, padx=10, pady=(5, 0))
            var = tk.IntVar(value=self.settings[key])
            font_vars[key] = var
            ttk.Spinbox(win, from_=6, to=48,
                        textvariable=var, width=8).pack(
                anchor=tk.W, padx=10)

        # Стиль
        ttk.Label(win, text=tr.t('settings.style'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        default_color_var = tk.StringVar(
            value=self.settings['default_color'])
        ttk.Label(win,
                  text=tr.t('settings.default_color')).pack(
            anchor=tk.W, padx=10)
        ttk.Entry(win, textvariable=default_color_var,
                  width=15).pack(anchor=tk.W, padx=10)
        default_lw_var = tk.DoubleVar(
            value=self.settings['default_lw'])
        ttk.Label(win,
                  text=tr.t('settings.default_lw')).pack(
            anchor=tk.W, padx=10, pady=(5, 0))
        ttk.Spinbox(win, from_=0.5, to=10, increment=0.5,
                    textvariable=default_lw_var, width=8).pack(
            anchor=tk.W, padx=10)
        axis_lw_var = tk.DoubleVar(value=self.settings['axis_lw'])
        ttk.Label(win,
                  text=tr.t('settings.axis_lw')).pack(
            anchor=tk.W, padx=10, pady=(5, 0))
        ttk.Spinbox(win, from_=0.5, to=5, increment=0.5,
                    textvariable=axis_lw_var, width=8).pack(
            anchor=tk.W, padx=10)

        # Обучение
        ttk.Label(win, text=tr.t('settings.tour'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        tour_var = tk.BooleanVar(
            value=self.settings.get('show_tour_on_start', False))
        ttk.Checkbutton(win,
                        text=tr.t('settings.tour_show_on_start'),
                        variable=tour_var).pack(
            anchor=tk.W, padx=10)

        def run_tour_now():
            win.destroy()
            self.root.after(100, self._start_onboarding)

        ttk.Button(win, text=tr.t('settings.tour_run_now'),
                   command=run_tour_now).pack(
            anchor=tk.W, padx=10, pady=(5, 0))

        ttk.Label(win, text=tr.t('menu.view.drag_points'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        ttk.Checkbutton(win, text=tr.t('menu.view.drag_points'),
                        variable=self.drag_points_enabled).pack(
            anchor=tk.W, padx=10)

        # === Звуки ===
        ttk.Label(win, text=tr.t('settings.sounds'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        if not hasattr(self, '_sound_enabled_var'):
            self._sound_enabled_var = tk.BooleanVar(
                value=self.settings.get('sounds_enabled', True))
        ttk.Checkbutton(win, text=tr.t('settings.sounds_enabled'),
                        variable=self._sound_enabled_var,
                        command=lambda: self._toggle_click_sound(
                            self._sound_enabled_var.get())).pack(
            anchor=tk.W, padx=10)

        ttk.Label(win, text=tr.t('settings.other'),
                  font=('Arial', 10, 'bold')).pack(
            anchor=tk.W, padx=10, pady=(15, 2))
        undo_var = tk.IntVar(value=self.max_undo)
        ttk.Label(win,
                  text=tr.t('settings.max_undo')).pack(
            anchor=tk.W, padx=10)
        ttk.Spinbox(win, from_=10, to=500,
                    textvariable=undo_var, width=10).pack(
            anchor=tk.W, padx=10)

        def do_reset():
            if not messagebox.askyesno(
                    tr.t('msg.confirm'),
                    tr.t('settings.reset_confirm')):
                return
            try:
                from config import reset_config
            except ImportError:
                from grapheditor.config import reset_config
            if not reset_config():
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('settings.reset_error'))
                return
            win.destroy()
            messagebox.showinfo(tr.t('msg.info'),
                                tr.t('settings.reset_done'))

        def save():
            new_lang = label_to_code.get(
                lang_var.get(),
                self.settings.get('language', 'ru'))
            lang_changed = (new_lang !=
                            self.settings.get('language', 'ru'))
            new_theme = theme_var.get()
            theme_changed = (new_theme !=
                             self.settings.get('theme', 'light'))

            self.settings['smooth_window'] = smooth_var.get()
            self.settings['font_family'] = font_family_var.get()
            self.settings['default_color'] = default_color_var.get()
            self.settings['default_lw'] = default_lw_var.get()
            self.settings['axis_lw'] = axis_lw_var.get()
            for key, var in font_vars.items():
                self.settings[key] = var.get()
            self.max_undo = undo_var.get()
            self.settings['show_tour_on_start'] = tour_var.get()
            self.settings['theme'] = new_theme
            self.settings['language'] = new_lang

            # === авто-тема ===
            self.settings['auto_theme_by_time'] = bool(
                self._auto_theme_var.get())
            self.settings['theme_day_start'] = day_start_var.get()
            self.settings['theme_day_end'] = day_end_var.get()
            self.settings['theme_day'] = theme_day_var.get()
            self.settings['theme_night'] = theme_night_var.get()

            self.color_var.set(default_color_var.get())
            self.lw_var.set(default_lw_var.get())
            self._apply_font_settings()

            self.settings['sounds_enabled'] = bool(
                self._sound_enabled_var.get())
            self._toggle_click_sound(
                self.settings['sounds_enabled'])

            win.destroy()
            self._show_history(tr.t('hist.settings_applied'))

            if theme_changed:
                self._apply_theme(new_theme)
                self.theme_var.set(new_theme)
                self._populate_theme_menu()

            if lang_changed:
                self._switch_lang(new_lang)

        footer = ttk.Frame(win, padding=(10, 15))
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(footer, text=tr.t('settings.reset'),
                   command=do_reset).pack(side=tk.LEFT)
        ttk.Button(footer, text=tr.t('settings.save'),
                   command=save).pack(side=tk.RIGHT)

    # ========================================================================
    # PYTHON-КОНСОЛЬ
    # ========================================================================
    def _open_console(self):
        if (self._console_window is not None
                and self._console_window.winfo_exists()):
            self._console_window.lift()
            self._console_window.focus_force()
            return
        win = tk.Toplevel(self.root)
        win.title(tr.t('menu.file.console'))
        win.geometry("720x500")
        win.transient(self.root)
        self._console_window = win

        tk.Label(win,
                 text="Доступно: app, np, plt, tk, mpl, messagebox, tr.",
                 bg="#2b2b2b", fg="#cccccc", anchor=tk.W,
                 font=('Consolas', 9), padx=6, pady=4).pack(fill=tk.X)

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)
        output = tk.Text(frame, bg="#1e1e1e", fg="#d4d4d4",
                         insertbackground="#ffffff",
                         font=('Consolas', 10), wrap=tk.NONE,
                         undo=True)
        output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y = ttk.Scrollbar(frame, orient=tk.VERTICAL,
                             command=output.yview)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        output.configure(yscrollcommand=sb_y.set)

        sb_x = ttk.Scrollbar(win, orient=tk.HORIZONTAL,
                             command=output.xview)
        sb_x.pack(fill=tk.X)
        output.configure(xscrollcommand=sb_x.set)

        input_frame = ttk.Frame(win)
        input_frame.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(input_frame, text=">>>").pack(
            side=tk.LEFT, padx=(0, 4))
        entry = ttk.Entry(input_frame, font=('Consolas', 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.focus()

        namespace = {
            'app': self, 'np': np,
            'plt': __import__('matplotlib.pyplot',
                              fromlist=['pyplot']),
            'tk': tk, 'mpl': mpl,
            'messagebox': messagebox, 'tr': tr,
            '__name__': '__console__', '__doc__': None,
        }
        multiline_buffer = {'text': None}
        history = []
        history_pos = [-1]

        def write_output(text):
            output.insert(tk.END, text)
            output.see(tk.END)

        def execute(code_text):
            import io, contextlib
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    try:
                        result = eval(code_text, namespace,
                                      namespace)
                        if result is not None:
                            print(repr(result))
                    except SyntaxError:
                        exec(code_text, namespace, namespace)
                out = buf.getvalue()
                if out:
                    write_output(out)
            except Exception as e:
                import traceback
                write_output("".join(traceback.format_exception(
                    type(e), e, e.__traceback__)) + "\n")

        def execute_with_history(code_text):
            if code_text.strip():
                history.append(code_text)
                history_pos[0] = -1
            execute(code_text)

        def on_enter(event=None):
            if multiline_buffer['text'] is not None:
                return
            code_text = entry.get()
            entry.delete(0, tk.END)
            write_output(f">>> {code_text}\n")
            if not code_text.strip():
                return
            execute_with_history(code_text)

        def on_ctrl_enter(event=None):
            if multiline_buffer['text'] is None:
                multiline_buffer['text'] = entry.get()
                entry.delete(0, tk.END)
                write_output("... " + multiline_buffer['text'] + "\n")
                return "break"
            else:
                multiline_buffer['text'] += "\n" + entry.get()
                entry.delete(0, tk.END)
                write_output("... " + entry.get() + "\n")
                execute_with_history(multiline_buffer['text'])
                multiline_buffer['text'] = None
                return "break"

        def on_up(event=None):
            if not history:
                return "break"
            if history_pos[0] == -1:
                history_pos[0] = len(history) - 1
            else:
                history_pos[0] = max(0, history_pos[0] - 1)
            entry.delete(0, tk.END)
            entry.insert(0, history[history_pos[0]])
            return "break"

        def on_down(event=None):
            if history_pos[0] == -1:
                return "break"
            history_pos[0] = min(len(history) - 1,
                                 history_pos[0] + 1)
            entry.delete(0, tk.END)
            entry.insert(0, history[history_pos[0]])
            return "break"

        entry.bind('<Return>', on_enter)
        entry.bind('<Control-Return>', on_ctrl_enter)
        entry.bind('<Up>', on_up)
        entry.bind('<Down>', on_down)
        write_output("GraphEditor Pro — Python-консоль\n\n")

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        def clear_output():
            output.delete("1.0", tk.END)

        def run_script():
            path = filedialog.askopenfilename(
                filetypes=[("Python", "*.py"),
                           ("All files", "*.*")])
            if not path:
                return
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    code = f.read()
                write_output(
                    f"--- {os.path.basename(path)} ---\n")
                execute_with_history(code)
                write_output("--- Выполнено ---\n")
            except Exception as e:
                write_output(f"Ошибка: {e}\n")

        ttk.Button(btn_frame, text="Очистить",
                   command=clear_output).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Загрузить .py...",
                   command=run_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Закрыть",
                   command=win.destroy).pack(side=tk.RIGHT, padx=2)
        win.after(100, entry.focus_set)

    # ========================================================================
    # ОНБОРДИНГ
    # ========================================================================
    def _maybe_start_onboarding(self):
        if not self.settings.get('show_tour_on_start', False):
            return
        if self.graphs_data:
            return
        self._start_onboarding()

    def _start_onboarding(self):
        self._onboarding_step = 0
        self._onboarding_widgets = [
            (self.notebook, 'tour.step1_title',
             'tour.step1_text'),
            (self.graph_tree, 'tour.step2_title',
             'tour.step2_text'),
            (self.plot_frame, 'tour.step3_title',
             'tour.step3_text'),
            (self.anim_labelframe, 'tour.step4_title',
             'tour.step4_text'),
            (self.plot_frame, 'tour.step5_title',
             'tour.step5_text'),
        ]
        self._show_onboarding_step()

    def _show_onboarding_step(self):
        if self._onboarding_step >= len(
                self._onboarding_widgets):
            self._finish_onboarding()
            return
        widget, title_key, text_key = \
            self._onboarding_widgets[self._onboarding_step]
        try:
            widget.update_idletasks()
            x, y = widget.winfo_rootx(), widget.winfo_rooty()
            w, h = widget.winfo_width(), widget.winfo_height()
        except Exception:
            x, y, w, h = 300, 300, 200, 100
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        popup = tk.Toplevel(self.root)
        popup.title(tr.t('msg.tour_title'))
        popup.transient(self.root)
        popup_w, popup_h = 340, 200
        px, py = x + w + 15, y
        if px + popup_w > sw - 20:
            px = x - popup_w - 15
            if px < 20:
                px = max(20, (sw - popup_w) // 2)
                py = min(y + h + 15, sh - popup_h - 40)
        py = max(20, min(py, sh - popup_h - 40))
        popup.geometry(f"{popup_w}x{popup_h}+{px}+{py}")
        total = len(self._onboarding_widgets)
        tk.Label(popup,
                 text=tr.t('msg.tour_step',
                           n=self._onboarding_step + 1,
                           total=total),
                 font=('Arial', 8), fg='gray').pack(
            anchor=tk.W, padx=10, pady=(8, 0))
        tk.Label(popup, text=tr.t(title_key),
                 font=('Arial', 12, 'bold')).pack(
            anchor=tk.W, padx=10)
        tk.Label(popup, text=tr.t(text_key),
                 wraplength=popup_w - 30,
                 justify=tk.LEFT).pack(
            anchor=tk.W, padx=10, pady=5, fill=tk.X)
        bf = tk.Frame(popup)
        bf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        def close_popup():
            try:
                popup.destroy()
            except Exception:
                pass

        def next_step():
            close_popup()
            self._onboarding_step += 1
            self.root.after(50, self._show_onboarding_step)

        def skip():
            close_popup()
            self._finish_onboarding()

        tk.Button(bf, text=tr.t('msg.tour_skip'),
                  command=skip).pack(side=tk.LEFT)
        is_last = self._onboarding_step == total - 1
        tk.Button(bf,
                  text=tr.t('msg.tour_finish') if is_last
                  else tr.t('msg.tour_next'),
                  command=next_step,
                  default=tk.ACTIVE).pack(side=tk.RIGHT)
        popup.bind('<Escape>', lambda e: skip())
        popup.protocol("WM_DELETE_WINDOW", skip)
        popup.after(50, lambda: popup.focus_force())

    def _finish_onboarding(self):
        self._show_history(tr.t('status.tour_finished'))