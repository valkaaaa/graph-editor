"""Диалоги: настройки, Python-консоль, DSL-консоль, справки, онбординг."""
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

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(560, sw - 80)
        h = min(680, sh - 120)
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        win.minsize(480, 380)
        win.bind('<Escape>', lambda e: win.destroy())

        footer = ttk.Frame(win, padding=(10, 10))
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        nb = ttk.Notebook(win)
        nb.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                padx=10, pady=(10, 0))

        tab_ui = ttk.Frame(nb, padding=15)
        tab_style = ttk.Frame(nb, padding=15)
        tab_behavior = ttk.Frame(nb, padding=15)
        nb.add(tab_ui, text=tr.t('settings.tab.interface'))
        nb.add(tab_style, text=tr.t('settings.tab.style'))
        nb.add(tab_behavior, text=tr.t('settings.tab.behavior'))

        # ---------------- ВКЛАДКА 1: ИНТЕРФЕЙС ----------------
        ttk.Label(tab_ui, text=tr.t('settings.language'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        label_to_code = {label: code for code, label in SUPPORTED_LANGS}
        code_to_label = {code: label for code, label in SUPPORTED_LANGS}
        current = self.settings.get('language', 'ru')
        if current not in code_to_label:
            current = 'en'
        lang_var = tk.StringVar(value=code_to_label[current])
        ttk.Combobox(tab_ui, textvariable=lang_var,
                     values=[lbl for _, lbl in SUPPORTED_LANGS],
                     state='readonly', width=30).pack(anchor=tk.W, pady=(2, 0))

        ttk.Label(tab_ui, text=tr.t('settings.theme'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 2))
        theme_var = tk.StringVar(value=self.settings.get('theme', 'light'))
        ttk.Combobox(tab_ui, textvariable=theme_var,
                     values=[k for k, _ in self._list_themes()],
                     state='readonly', width=25).pack(anchor=tk.W)

        ttk.Label(tab_ui, text=tr.t('settings.auto_theme'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 2))
        if not hasattr(self, '_auto_theme_var'):
            self._auto_theme_var = tk.BooleanVar(
                value=self.settings.get('auto_theme_by_time', False))
        ttk.Checkbutton(tab_ui, text=tr.t('settings.auto_theme_by_time'),
                        variable=self._auto_theme_var,
                        command=self._toggle_auto_theme).pack(anchor=tk.W)

        row_at = ttk.Frame(tab_ui)
        row_at.pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(row_at, text=tr.t('settings.theme_day_start')).pack(side=tk.LEFT)
        day_start_var = tk.IntVar(value=self.settings.get('theme_day_start', 7))
        ttk.Spinbox(row_at, from_=0, to=23,
                    textvariable=day_start_var, width=4).pack(side=tk.LEFT, padx=3)
        ttk.Label(row_at, text=tr.t('settings.theme_day_end')).pack(side=tk.LEFT)
        day_end_var = tk.IntVar(value=self.settings.get('theme_day_end', 19))
        ttk.Spinbox(row_at, from_=0, to=23,
                    textvariable=day_end_var, width=4).pack(side=tk.LEFT, padx=3)

        row_at2 = ttk.Frame(tab_ui)
        row_at2.pack(anchor=tk.W, pady=(4, 0))
        ttk.Label(row_at2, text=tr.t('settings.theme_day')).pack(side=tk.LEFT)
        theme_day_var = tk.StringVar(value=self.settings.get('theme_day', 'light'))
        ttk.Combobox(row_at2, textvariable=theme_day_var, width=12,
                     state='readonly',
                     values=[k for k, _ in self._list_themes()]).pack(
            side=tk.LEFT, padx=3)
        ttk.Label(row_at2, text=tr.t('settings.theme_night')).pack(
            side=tk.LEFT, padx=(10, 0))
        theme_night_var = tk.StringVar(
            value=self.settings.get('theme_night', 'dark'))
        ttk.Combobox(row_at2, textvariable=theme_night_var, width=12,
                     state='readonly',
                     values=[k for k, _ in self._list_themes()]).pack(
            side=tk.LEFT, padx=3)

        ttk.Label(tab_ui, text=tr.t('settings.tour'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(20, 2))
        tour_var = tk.BooleanVar(
            value=self.settings.get('show_tour_on_start', False))
        ttk.Checkbutton(tab_ui, text=tr.t('settings.tour_show_on_start'),
                        variable=tour_var).pack(anchor=tk.W)

        def run_tour_now():
            win.destroy()
            self.root.after(100, self._start_onboarding)

        ttk.Button(tab_ui, text=tr.t('settings.tour_run_now'),
                   command=run_tour_now).pack(anchor=tk.W, pady=(5, 0))

        # ---------------- ВКЛАДКА 2: ШРИФТЫ И СТИЛЬ ----------------
        ttk.Label(tab_style, text=tr.t('settings.fonts'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        row_ff = ttk.Frame(tab_style)
        row_ff.pack(fill=tk.X, pady=(2, 8))
        ttk.Label(row_ff, text=tr.t('settings.font_family')).pack(side=tk.LEFT)
        font_family_var = tk.StringVar(value=self.settings['font_family'])
        ttk.Combobox(row_ff, textvariable=font_family_var,
                     values=FONTS, width=25,
                     state="readonly").pack(side=tk.LEFT, padx=5)

        grid_ff = ttk.Frame(tab_style)
        grid_ff.pack(fill=tk.X, pady=(0, 10))
        font_vars = {}
        for i, (key, label_key) in enumerate([
            ('font_base',   'settings.font_base'),
            ('font_title',  'settings.font_title'),
            ('font_labels', 'settings.font_labels'),
            ('font_legend', 'settings.font_legend'),
            ('font_ticks',  'settings.font_ticks'),
        ]):
            var = tk.IntVar(value=self.settings[key])
            font_vars[key] = var
            r, c = divmod(i, 2)
            ttk.Label(grid_ff, text=f"{tr.t(label_key)}:").grid(
                row=r, column=c * 2, sticky=tk.W, pady=2, padx=(0, 3))
            ttk.Spinbox(grid_ff, from_=6, to=48,
                        textvariable=var, width=6).grid(
                row=r, column=c * 2 + 1, sticky=tk.W, padx=(0, 15))

        ttk.Label(tab_style, text=tr.t('settings.style'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 2))

        row_color = ttk.Frame(tab_style)
        row_color.pack(fill=tk.X, pady=(2, 5))
        ttk.Label(row_color, text=tr.t('settings.default_color')).pack(
            side=tk.LEFT)
        default_color_var = tk.StringVar(value=self.settings['default_color'])
        ttk.Entry(row_color, textvariable=default_color_var, width=12).pack(
            side=tk.LEFT, padx=5)

        def pick_default_color():
            from tkinter import colorchooser
            c = colorchooser.askcolor(initialcolor=default_color_var.get())
            if c[1]:
                default_color_var.set(c[1])

        ttk.Button(row_color, text='…', width=3,
                   command=pick_default_color).pack(side=tk.LEFT)

        row_lw = ttk.Frame(tab_style)
        row_lw.pack(fill=tk.X, pady=(2, 5))
        ttk.Label(row_lw, text=tr.t('settings.default_lw')).pack(side=tk.LEFT)
        default_lw_var = tk.DoubleVar(value=self.settings['default_lw'])
        ttk.Spinbox(row_lw, from_=0.5, to=10, increment=0.5,
                    textvariable=default_lw_var, width=6).pack(
            side=tk.LEFT, padx=5)

        row_axis = ttk.Frame(tab_style)
        row_axis.pack(fill=tk.X, pady=(2, 5))
        ttk.Label(row_axis, text=tr.t('settings.axis_lw')).pack(side=tk.LEFT)
        axis_lw_var = tk.DoubleVar(value=self.settings['axis_lw'])
        ttk.Spinbox(row_axis, from_=0.5, to=5, increment=0.5,
                    textvariable=axis_lw_var, width=6).pack(
            side=tk.LEFT, padx=5)

        ttk.Label(tab_style, text=tr.t('settings.smooth'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(15, 2))
        row_smooth = ttk.Frame(tab_style)
        row_smooth.pack(fill=tk.X)
        ttk.Label(row_smooth, text=tr.t('settings.smooth_window')).pack(
            side=tk.LEFT)
        smooth_var = tk.IntVar(value=self.settings['smooth_window'])
        ttk.Spinbox(row_smooth, from_=1, to=100,
                    textvariable=smooth_var, width=6).pack(side=tk.LEFT, padx=5)

        # ---------------- ВКЛАДКА 3: ПОВЕДЕНИЕ ----------------
        ttk.Label(tab_behavior, text=tr.t('hotkey.section'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Button(tab_behavior, text=tr.t('hotkey.open_editor'),
                   command=self._open_hotkey_editor).pack(
            anchor=tk.W, pady=(2, 10))

        ttk.Label(tab_behavior, text=tr.t('settings.editing'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 2))
        ttk.Checkbutton(tab_behavior, text=tr.t('menu.view.drag_points'),
                        variable=self.drag_points_enabled).pack(anchor=tk.W)

        ttk.Label(tab_behavior, text=tr.t('settings.sounds'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(15, 2))
        if not hasattr(self, '_sound_enabled_var'):
            self._sound_enabled_var = tk.BooleanVar(
                value=self.settings.get('sounds_enabled', True))
        ttk.Checkbutton(tab_behavior, text=tr.t('settings.sounds_enabled'),
                        variable=self._sound_enabled_var,
                        command=lambda: self._toggle_click_sound(
                            self._sound_enabled_var.get())).pack(anchor=tk.W)

        ttk.Label(tab_behavior, text=tr.t('settings.other'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(15, 2))
        row_undo = ttk.Frame(tab_behavior)
        row_undo.pack(fill=tk.X)
        ttk.Label(row_undo, text=tr.t('settings.max_undo')).pack(side=tk.LEFT)
        undo_var = tk.IntVar(value=self.max_undo)
        ttk.Spinbox(row_undo, from_=10, to=500,
                    textvariable=undo_var, width=8).pack(
            side=tk.LEFT, padx=5)

        # ---------------- КНОПКИ ----------------
        def do_reset():
            if not messagebox.askyesno(
                    tr.t('msg.confirm'), tr.t('settings.reset_confirm')):
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
            messagebox.showinfo(tr.t('msg.info'), tr.t('settings.reset_done'))

        def save():
            new_lang = label_to_code.get(
                lang_var.get(), self.settings.get('language', 'ru'))
            lang_changed = (new_lang != self.settings.get('language', 'ru'))
            new_theme = theme_var.get()
            theme_changed = (new_theme != self.settings.get('theme', 'light'))

            self.settings['smooth_window']       = smooth_var.get()
            self.settings['font_family']         = font_family_var.get()
            self.settings['default_color']       = default_color_var.get()
            self.settings['default_lw']          = default_lw_var.get()
            self.settings['axis_lw']             = axis_lw_var.get()
            for key, var in font_vars.items():
                self.settings[key] = var.get()
            self.max_undo                        = undo_var.get()
            self.settings['show_tour_on_start']  = tour_var.get()
            self.settings['theme']               = new_theme
            self.settings['language']            = new_lang
            self.settings['auto_theme_by_time']  = bool(self._auto_theme_var.get())
            self.settings['theme_day_start']     = day_start_var.get()
            self.settings['theme_day_end']       = day_end_var.get()
            self.settings['theme_day']           = theme_day_var.get()
            self.settings['theme_night']         = theme_night_var.get()

            self.color_var.set(default_color_var.get())
            self.lw_var.set(default_lw_var.get())
            self._apply_font_settings()

            self.settings['sounds_enabled'] = bool(self._sound_enabled_var.get())
            self._toggle_click_sound(self.settings['sounds_enabled'])

            win.destroy()
            self._show_history(tr.t('hist.settings_applied'))

            if theme_changed:
                self._apply_theme(new_theme)
                self.theme_var.set(new_theme)
                self._populate_theme_menu()
            if lang_changed:
                self._switch_lang(new_lang)

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
                 text="⚠️ Консоль выполняет код с полными правами. "
                      "Доступно: app, np, plt, tk, mpl, messagebox, tr.",
                 bg="#2b2b2b", fg="#f39c12", anchor=tk.W,
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
    # СПРАВОЧНИК ФОРМУЛ
    # ========================================================================
    def _show_formula_help(self):
        """Справочник по доступным математическим функциям."""
        win = tk.Toplevel(self.root)
        win.title("Справочник формул")
        win.transient(self.root)
        win.geometry("720x620")
        win.bind('<Escape>', lambda e: win.destroy())

        HELP = {
            "Тригонометрия": [
                ("sin(x)",         "Синус"),
                ("cos(x)",         "Косинус"),
                ("tan(x)",         "Тангенс"),
                ("arcsin(x)",      "Арксинус"),
                ("arccos(x)",      "Арккосинус"),
                ("arctan(x)",      "Арктангенс"),
                ("arctan2(y, x)",  "Арктангенс (два аргумента)"),
                ("sinh(x)",        "Гиперболический синус"),
                ("cosh(x)",        "Гиперболический косинус"),
                ("tanh(x)",        "Гиперболический тангенс"),
                ("deg2rad(x)",     "Градусы → радианы"),
                ("rad2deg(x)",     "Радианы → градусы"),
            ],
            "Экспоненты / логарифмы": [
                ("exp(x)",         "e^x"),
                ("exp2(x)",        "2^x"),
                ("log(x)",         "Натуральный логарифм"),
                ("log10(x)",       "Логарифм по основанию 10"),
                ("log2(x)",        "Логарифм по основанию 2"),
                ("sqrt(x)",        "Квадратный корень"),
                ("cbrt(x)",        "Кубический корень"),
                ("power(x, 3)",    "Степень"),
            ],
            "Специальные": [
                ("erf(x)",         "Функция ошибок (интеграл Гаусса)"),
                ("erfc(x)",        "Дополнительная функция ошибок"),
                ("gamma(x)",       "Гамма-функция"),
                ("lgamma(x)",      "Логарифм гамма-функции"),
                ("jv(0, x)",       "Функция Бесселя J₀"),
                ("yv(0, x)",       "Функция Бесселя Y₀"),
                ("heaviside(x)",   "Функция Хевисайда (ступенька)"),
                ("airy(x)",        "Функция Эйри"),
            ],
            "Работа с данными": [
                ("cumsum(x)",      "Накопленная сумма"),
                ("diff(x)",        "Первая разность"),
                ("abs(x)",         "Модуль"),
                ("sign(x)",        "Знак"),
                ("floor(x)",       "Округление вниз"),
                ("ceil(x)",        "Округление вверх"),
                ("clip(x, -1, 1)", "Обрезать по диапазону"),
                ("where(x>0, x, 0)", "Условие"),
            ],
            "Комплексные": [
                ("real(z)",        "Действительная часть"),
                ("imag(z)",        "Мнимая часть"),
                ("abs(z)",         "Модуль комплексного"),
                ("angle(z)",       "Аргумент (фаза)"),
                ("conj(z)",        "Сопряжённое"),
            ],
            "Константы": [
                ("pi",             "π = 3.14159…"),
                ("e",              "e = 2.71828…"),
                ("tau",            "τ = 2π"),
                ("inf",            "Бесконечность"),
            ],
            "Переменные": [
                ("x",              "Независимая переменная"),
                ("t",              "Время (для анимаций)"),
                ("y",              "Y-переменная (для 3D)"),
            ],
            "Готовые примеры": [
                ("sin(x) * exp(-x/5)",          "Затухающая синусоида"),
                ("sin(x) * sin(10 * x)",        "Биения"),
                ("exp(-x**2 / 2) / sqrt(2*pi)", "Нормальное распределение"),
                ("1 / (1 + exp(-x))",           "Сигмоида"),
                ("x * sin(1/x)",                "Колебания с затуханием"),
                ("sin(x + t)",                  "Анимация: волна"),
                ("sin(x + t) * cos(y - t)",     "Анимация: 3D волна"),
            ],
        }

        top = ttk.Frame(win, padding=(10, 10, 10, 5))
        top.pack(fill=tk.X)
        ttk.Label(
            top,
            text="Двойной клик по строке — формула попадёт в поле ввода.",
            foreground='gray',
        ).pack(anchor=tk.W)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        trees = {}
        for category, items in HELP.items():
            tab = ttk.Frame(nb, padding=5)
            nb.add(tab, text=category)

            tree = ttk.Treeview(
                tab, columns=('expr', 'desc'),
                show='headings', height=15)
            tree.heading('expr', text='Формула')
            tree.heading('desc', text='Описание')
            tree.column('expr', width=280, anchor=tk.W)
            tree.column('desc', width=380, anchor=tk.W)
            tree.pack(fill=tk.BOTH, expand=True)

            for expr, desc in items:
                tree.insert('', tk.END, values=(expr, desc))
            trees[category] = tree

        footer = ttk.Frame(win, padding=(10, 5, 10, 10))
        footer.pack(fill=tk.X)

        def _get_active_tree():
            try:
                idx = nb.index(nb.select())
            except tk.TclError:
                return None
            keys = list(trees.keys())
            if 0 <= idx < len(keys):
                return trees[keys[idx]]
            return None

        def _get_selected_expr():
            tree = _get_active_tree()
            if tree is None:
                return None
            sel = tree.selection()
            if not sel:
                return None
            return tree.item(sel[0], 'values')[0]

        def _insert():
            expr = _get_selected_expr()
            if not expr:
                return
            try:
                self.gen_expr.delete(0, tk.END)
                self.gen_expr.insert(0, expr)
            except AttributeError:
                try:
                    self.entry_custom_anim.delete(0, tk.END)
                    self.entry_custom_anim.insert(0, expr)
                except AttributeError:
                    win.clipboard_clear()
                    win.clipboard_append(expr)

        def _on_double_click(event):
            _insert()

        for tree in trees.values():
            tree.bind('<Double-1>', _on_double_click)

        ttk.Button(footer, text="Вставить",
                    command=_insert).pack(side=tk.RIGHT, padx=2)
        ttk.Button(footer, text="Закрыть",
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)

    # ========================================================================
    # DSL-КОНСОЛЬ
    # ========================================================================
    def _open_dsl_console(self):
        """Мини-консоль с DSL для быстрого создания графиков."""
        win = tk.Toplevel(self.root)
        win.title("DSL-консоль")
        win.geometry("700x500")
        win.transient(self.root)

        help_text = (
            "Введите команду и нажмите Enter. "
            "Кнопка «? Справка» — все команды с примерами.\n"
            "Быстрый старт: line x=0..10 y=sin(x)"
        )
        ttk.Label(win, text=help_text, font=('Consolas', 9),
                   background='#2b2b2b', foreground='#d4d4d4',
                   justify=tk.LEFT, padding=8).pack(fill=tk.X)

        input_frame = ttk.Frame(win, padding=5)
        input_frame.pack(fill=tk.X)
        ttk.Label(input_frame, text=">>>").pack(side=tk.LEFT)
        entry = ttk.Entry(input_frame, font=('Consolas', 10))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.focus_set()

        output = tk.Text(win, bg='#1e1e1e', fg='#d4d4d4',
                          font=('Consolas', 10), wrap=tk.WORD, height=15)
        output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        def log(msg, tag='info'):
            output.insert(tk.END, msg + '\n', tag)
            output.see(tk.END)
        output.tag_config('info', foreground='#d4d4d4')
        output.tag_config('ok', foreground='#2ecc71')
        output.tag_config('err', foreground='#e74c3c')
        output.tag_config('cmd', foreground='#61afef')

        def _parse_range(text):
            if '..' in text:
                a, b = text.split('..', 1)
                return np.linspace(float(a), float(b), 100)
            return np.array([float(v) for v in text.split(',')
                             if v.strip()])

        def _parse_list(text):
            items = [v.strip() for v in text.split(',') if v.strip()]
            out = []
            for v in items:
                try:
                    out.append(float(v))
                except ValueError:
                    out.append(v)
            return out

        def _parse_kwargs(tokens):
            kwargs = {}
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if '=' in tok:
                    k, v = tok.split('=', 1)
                    if not v:
                        i += 1
                        v = tokens[i] if i < len(tokens) else ''
                    v = v.strip('"\'')
                    kwargs[k.strip()] = v
                i += 1
            return kwargs

        def execute(cmd):
            cmd = cmd.strip()
            if not cmd or cmd.startswith('#'):
                return

            log(f">>> {cmd}", 'cmd')
            tokens = cmd.split()
            if not tokens:
                return
            head = tokens[0].lower()
            rest = tokens[1:]

            try:
                # ---- Создание графиков ----
                if head in ('line', 'scatter', 'bar', 'hist'):
                    kwargs = _parse_kwargs(rest)
                    x_text = kwargs.get('x', '')
                    y_text = kwargs.get('y', '')
                    label = kwargs.get('label', '')

                    type_map = {
                        'line': 'Линия', 'scatter': 'Точечная',
                        'bar': 'Столбчатая', 'hist': 'Гистограмма',
                    }
                    t_type = type_map[head]

                    if head == 'hist':
                        x_vals = _parse_list(x_text) if x_text else []
                        self.type_var.set(tr.type_name('Гистограмма'))
                        self.entry_x.delete(0, tk.END)
                        self.entry_x.insert(0, ','.join(map(str, x_vals)))
                        self._add_graph()
                        log(f"✓ {t_type}: {len(x_vals)} точек", 'ok')
                        return

                    x_vals = _parse_range(x_text) if x_text else []
                    if head == 'line' and y_text:
                        x_arr = (np.asarray(x_vals, dtype=float)
                                 if len(x_vals) else
                                 np.linspace(0, 1, 100))
                        y_arr = self._safe_eval(y_text, x_arr, 0,
                                                 silent=True)
                        if y_arr is None:
                            log(f"✗ Не удалось вычислить: {y_text}", 'err')
                            return
                        y_vals = (np.asarray(y_arr).tolist()
                                  if hasattr(y_arr, 'tolist')
                                  else list(y_arr))
                        x_vals = x_arr.tolist()
                    else:
                        y_vals = _parse_list(y_text)

                    self.line_counter += 1
                    d = self._default_data(
                        t_type, list(x_vals), list(y_vals),
                        label=label or f"{t_type} {self.line_counter}",
                        color=self.color_var.get())
                    d['artist'] = self._create_artist(d)
                    self.graphs_data.append(d)
                    self._update_listbox()
                    self._redraw()
                    log(f"✓ {t_type}: {len(x_vals)} точек", 'ok')

                # ---- Анализ ----
                elif head == 'fit':
                    sub = rest[0].lower() if rest else ''
                    if sub == 'poly':
                        deg = int(rest[1]) if len(rest) > 1 else 2
                        self.fit_degree_var.set(deg)
                        self._add_fit_poly()
                    elif sub == 'linear':
                        self._add_fit('linear')
                    elif sub == 'log':
                        self._add_fit('log')
                    elif sub == 'exp':
                        self._add_fit('exp')
                    elif sub == 'power':
                        self._add_fit('power')
                    else:
                        log(f"✗ Неизвестный fit: {sub}", 'err')
                        return
                    log(f"✓ fit {sub}", 'ok')

                elif head == 'filter' or head == 'savgol':
                    kwargs = _parse_kwargs(rest)
                    w = int(kwargs.get('window', 11))
                    p = int(kwargs.get('poly', 2))
                    self.savgol_window_var.set(w)
                    self.savgol_poly_var.set(p)
                    self._apply_savgol()
                    log(f"✓ SG-фильтр окно={w} порядок={p}", 'ok')

                elif head == 'interp':
                    method = rest[0] if rest else 'cubic'
                    kwargs = _parse_kwargs(rest[1:])
                    n = int(kwargs.get('n', 500))
                    self.interp_method_var.set(method)
                    self.interp_n_var.set(n)
                    self._apply_interpolation()
                    log(f"✓ интерполяция {method} n={n}", 'ok')

                elif head == 'derivative':
                    self._add_derivative()
                    log("✓ производная", 'ok')

                elif head == 'integral':
                    self._add_integral()
                    log("✓ интеграл", 'ok')

                # ---- Управление ----
                elif head == 'clear':
                    self._clear_all()
                    log("✓ очищено", 'ok')

                elif head == 'redraw':
                    self._redraw()
                    log("✓ перерисовано", 'ok')

                # ---- Экспорт ----
                elif head == 'export':
                    fmt = rest[0].lower() if rest else ''
                    path = rest[1] if len(rest) > 1 else ''
                    if not path:
                        log("✗ укажите путь: export png out.png", 'err')
                        return
                    if fmt == 'png':
                        self.fig.savefig(path, dpi=300,
                                          bbox_inches='tight')
                    elif fmt == 'svg':
                        self.fig.savefig(path, format='svg',
                                          bbox_inches='tight')
                    elif fmt == 'pdf':
                        self.fig.savefig(path, format='pdf',
                                          bbox_inches='tight')
                    elif fmt == 'csv':
                        import csv
                        with open(path, 'w', newline='',
                                   encoding='utf-8') as f:
                            w = csv.writer(f)
                            for d in self.graphs_data:
                                w.writerow(
                                    [f"# {d['label']} ({d['type']})"])
                                w.writerow(["X", "Y"])
                                for xv, yv in zip(d['x'], d['y']):
                                    w.writerow([xv, yv])
                                w.writerow([])
                    else:
                        log(f"✗ неизвестный формат: {fmt}", 'err')
                        return
                    log(f"✓ сохранено: {path}", 'ok')

                else:
                    all_cmds = [
                        "line", "scatter", "bar", "hist", "pie",
                        "polygon", "fit", "filter", "interp",
                        "derivative", "integral", "peaks",
                        "clear", "redraw", "undo", "redo",
                        "title", "xlabel", "ylabel", "export",
                    ]
                    similar = [c for c in all_cmds
                               if head[:3] in c or c[:3] in head]
                    msg = f"✗ неизвестная команда: {head}"
                    if similar:
                        msg += f"\n  Возможно: {', '.join(similar[:3])}"
                    msg += "\n  См. «? Справка» — там все команды."
                    log(msg, 'err')

            except Exception as e:
                import traceback
                log(f"✗ Ошибка: {e}", 'err')
                log(traceback.format_exc(), 'err')

        history = []
        history_pos = [-1]

        def on_enter(event=None):
            cmd = entry.get()
            entry.delete(0, tk.END)
            if cmd.strip():
                if not history or history[-1] != cmd:
                    history.append(cmd)
                history_pos[0] = -1
            execute(cmd)

        def on_up(event=None):
            if not history:
                return 'break'
            if history_pos[0] == -1:
                history_pos[0] = len(history) - 1
            else:
                history_pos[0] = max(0, history_pos[0] - 1)
            entry.delete(0, tk.END)
            entry.insert(0, history[history_pos[0]])
            return 'break'

        def on_down(event=None):
            if history_pos[0] == -1:
                return 'break'
            history_pos[0] = min(len(history) - 1,
                                  history_pos[0] + 1)
            entry.delete(0, tk.END)
            entry.insert(0, history[history_pos[0]])
            return 'break'

        entry.bind('<Return>', on_enter)
        entry.bind('<Up>', on_up)
        entry.bind('<Down>', on_down)

        btn_frame = ttk.Frame(win, padding=5)
        btn_frame.pack(fill=tk.X)

        def _show_help():
            def _insert(text):
                entry.delete(0, tk.END)
                entry.insert(0, text)
                entry.focus_set()

            def _run(text):
                entry.delete(0, tk.END)
                entry.insert(0, text)
                on_enter()
                entry.focus_set()

            self._show_dsl_help(
                insert_callback=_insert,
                run_callback=_run,
            )

        ttk.Button(btn_frame, text="? Справка",
                    command=_show_help).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Очистить лог",
                    command=lambda: output.delete('1.0', tk.END)
                    ).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Закрыть",
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)

        log("DSL-консоль готова. Введите команду и нажмите Enter.",
            'info')
        log("Пример: line x=0..10 y=sin(x) label='Синус'", 'info')
        log("", 'info')

    # ========================================================================
    # DSL-СПРАВОЧНИК
    # ========================================================================
    def _show_dsl_help(self, insert_callback=None, run_callback=None):
        """Справочник команд DSL."""
        win = tk.Toplevel(self.root)
        win.title("DSL — Справочник команд")
        win.transient(self.root)
        win.geometry("820x640")
        win.bind('<Escape>', lambda e: win.destroy())

        HELP = {
            "📈 Графики": [
                {
                    "cmd": "line x=0..10 y=sin(x)",
                    "desc": "Линия. x — диапазон (0..10) или список "
                            "(1,2,3); y — формула или список чисел.",
                    "example": "line x=0..10 y=sin(x) label='Синус'",
                },
                {
                    "cmd": "line x=1,2,3,4,5 y=2,4,6,8,10",
                    "desc": "Линия по явным спискам координат.",
                    "example": "line x=1,2,3,4,5 y=2,4,6,8,10 label='Данные'",
                },
                {
                    "cmd": "scatter x=1,2,3 y=4,5,6",
                    "desc": "Точечная диаграмма.",
                    "example": "scatter x=1,2,3,4,5 y=2.5,3.1,4.8,5.2,6.9",
                },
                {
                    "cmd": "bar x=A,B,C y=10,20,30",
                    "desc": "Столбчатая.",
                    "example": "bar x=A,B,C,D y=10,25,18,32",
                },
                {
                    "cmd": "hist x=1.5,2.5,1.8 bins=8",
                    "desc": "Гистограмма.",
                    "example": "hist x=1.2,2.5,1.8,2.1,2.9 bins=8",
                },
            ],
            "🔧 Анализ": [
                {
                    "cmd": "fit poly 2",
                    "desc": "Полиномиальная аппроксимация.",
                    "example": "fit poly 2",
                },
                {
                    "cmd": "fit linear / exp / log / power",
                    "desc": "Другие виды аппроксимации.",
                    "example": "fit linear",
                },
                {
                    "cmd": "filter sg window=11 poly=2",
                    "desc": "Фильтр Савицкого-Голея.",
                    "example": "filter sg window=11 poly=2",
                },
                {
                    "cmd": "interp cubic n=500",
                    "desc": "Интерполяция (linear / cubic / pchip).",
                    "example": "interp cubic n=500",
                },
                {
                    "cmd": "derivative",
                    "desc": "Производная как новая линия.",
                    "example": "derivative",
                },
                {
                    "cmd": "integral",
                    "desc": "Интеграл как новая линия.",
                    "example": "integral",
                },
            ],
            "⚙️ Управление": [
                {
                    "cmd": "clear",
                    "desc": "Очистить все объекты.",
                    "example": "clear",
                },
                {
                    "cmd": "redraw",
                    "desc": "Перерисовать холст.",
                    "example": "redraw",
                },
                {
                    "cmd": "title 'Заголовок'",
                    "desc": "Установить заголовок.",
                    "example": "title 'Мой график'",
                },
                {
                    "cmd": "xlabel 'Time, s'",
                    "desc": "Подпись оси X.",
                    "example": "xlabel 'Time, s'",
                },
                {
                    "cmd": "ylabel 'Signal'",
                    "desc": "Подпись оси Y.",
                    "example": "ylabel 'Signal'",
                },
            ],
            "💾 Экспорт": [
                {
                    "cmd": "export png out.png",
                    "desc": "PNG (300 DPI).",
                    "example": "export png result.png",
                },
                {
                    "cmd": "export svg out.svg",
                    "desc": "SVG (векторный).",
                    "example": "export svg result.svg",
                },
                {
                    "cmd": "export pdf out.pdf",
                    "desc": "PDF (векторный).",
                    "example": "export pdf result.pdf",
                },
                {
                    "cmd": "export csv out.csv",
                    "desc": "CSV с данными.",
                    "example": "export csv data.csv",
                },
            ],
            "🌟 Рецепты": [
                {
                    "cmd": "Синусоида",
                    "desc": "Линия + оформление.",
                    "example": (
                        "line x=0..6.28 y=sin(x) label='sin(x)'\n"
                        "title 'График синуса'\n"
                        "xlabel 'x, rad'\n"
                        "ylabel 'sin(x)'"
                    ),
                },
                {
                    "cmd": "Нормальное распределение",
                    "desc": "Плотность N(0,1).",
                    "example": (
                        "line x=-4..4 y=exp(-x*x/2)/sqrt(2*pi)\n"
                        "title 'Нормальное распределение'"
                    ),
                },
                {
                    "cmd": "Scatter + регрессия",
                    "desc": "Точки + полином 2-й степени.",
                    "example": (
                        "scatter x=1,2,3,4,5,6,7,8 y=2.1,4.2,5.9,8.3,10.1,11.8,14.2,15.9\n"
                        "fit poly 2"
                    ),
                },
            ],
        }

        top = ttk.Frame(win, padding=(10, 10, 10, 5))
        top.pack(fill=tk.X)
        ttk.Label(
            top,
            text="Двойной клик по строке — команда попадёт в консоль.",
            foreground='gray',
        ).pack(anchor=tk.W)

        search_frame = ttk.Frame(win, padding=(10, 0, 10, 5))
        search_frame.pack(fill=tk.X)
        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=search_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        trees = {}
        item_data = {}

        for category, items in HELP.items():
            tab = ttk.Frame(nb, padding=5)
            nb.add(tab, text=category)

            tree = ttk.Treeview(
                tab, columns=('cmd', 'desc'),
                show='headings', height=15)
            tree.heading('cmd', text='Команда')
            tree.heading('desc', text='Описание')
            tree.column('cmd', width=320, anchor=tk.W)
            tree.column('desc', width=420, anchor=tk.W)
            tree.pack(fill=tk.BOTH, expand=True)

            for item in items:
                iid = tree.insert(
                    '', tk.END,
                    values=(item["cmd"], item["desc"]))
                item_data[iid] = item
            trees[category] = tree

        footer = ttk.Frame(win, padding=(10, 5, 10, 10))
        footer.pack(fill=tk.X)

        preview_var = tk.StringVar(value="")
        ttk.Label(
            footer, textvariable=preview_var,
            font=('Consolas', 9),
            foreground='#4f46e5', wraplength=700,
        ).pack(anchor=tk.W, pady=(0, 5))

        def _get_active_tree():
            try:
                idx = nb.index(nb.select())
            except tk.TclError:
                return None
            keys = list(trees.keys())
            if 0 <= idx < len(keys):
                return trees[keys[idx]]
            return None

        def _get_selected_item():
            tree = _get_active_tree()
            if tree is None:
                return None
            sel = tree.selection()
            if not sel:
                return None
            return item_data.get(sel[0])

        def _on_select(event=None):
            item = _get_selected_item()
            if not item:
                preview_var.set("")
                return
            preview_var.set(f"Пример: {item['example']}")

        for tree in trees.values():
            tree.bind('<<TreeviewSelect>>', _on_select)

        def _insert_command(item, run=False):
            text = item.get("example") or item.get("cmd")
            if insert_callback:
                insert_callback(text)
            if run and run_callback:
                run_callback(text)
            if not insert_callback:
                win.clipboard_clear()
                win.clipboard_append(text)
                preview_var.set("Скопировано в буфер обмена")

        def _on_double_click(event=None):
            item = _get_selected_item()
            if not item:
                return
            if event and (event.state & 0x1):
                _insert_command(item, run=True)
            else:
                _insert_command(item, run=False)

        for tree in trees.values():
            tree.bind('<Double-1>', _on_double_click)

        def _do_insert(event=None):
            item = _get_selected_item()
            if item:
                _insert_command(item, run=False)

        def _do_run(event=None):
            item = _get_selected_item()
            if item:
                _insert_command(item, run=True)

        def _do_copy(event=None):
            item = _get_selected_item()
            if not item:
                return
            text = item.get("example") or item.get("cmd")
            win.clipboard_clear()
            win.clipboard_append(text)
            preview_var.set("Скопировано в буфер обмена")

        def _do_search(*args):
            q = search_var.get().strip().lower()
            for category, tree in trees.items():
                tree.delete(*tree.get_children())
                for item in HELP[category]:
                    haystack = (
                        item["cmd"].lower() + " " +
                        item["desc"].lower() + " " +
                        item.get("example", "").lower()
                    )
                    if q and q not in haystack:
                        continue
                    iid = tree.insert(
                        '', tk.END,
                        values=(item["cmd"], item["desc"]))
                    item_data[iid] = item
            if q:
                for i, (cat, tree) in enumerate(trees.items()):
                    if tree.get_children():
                        nb.select(i)
                        break

        search_var.trace_add('write', _do_search)

        ttk.Button(footer, text="Копировать",
                    command=_do_copy).pack(side=tk.LEFT, padx=2)
        if run_callback:
            ttk.Button(footer, text="▶ Выполнить",
                        command=_do_run).pack(side=tk.LEFT, padx=2)
        if insert_callback:
            ttk.Button(footer, text="→ Вставить",
                        command=_do_insert).pack(side=tk.LEFT, padx=2)

        ttk.Button(footer, text="Закрыть",
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)

    # ========================================================================
    # СПИСОК ПЛАГИНОВ
    # ========================================================================
    def _show_plugins_list(self):
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.plugins_list_title'))
        win.transient(self.root)
        win.geometry('640x500')

        ttk.Label(win, text=tr.t('msg.plugins_warning'),
                  foreground='#c0392b', wraplength=600
                  ).pack(anchor=tk.W, padx=10, pady=(8, 4))

        txt = tk.Text(win, wrap=tk.WORD, font=('Consolas', 9))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        reg = self.plugin_registry
        lines = []
        lines.append(f"Типы графиков: {len(reg.chart_types)}")
        lines.append(f"Анимации:      {len(getattr(reg, 'animations', {}))}")
        lines.append(f"Темы:          {len(getattr(reg, 'themes', {}))}")
        lines.append(f"Шаблоны:       {len(getattr(reg, 'templates', {}))}")
        lines.append('')
        lines.append('—' * 50)
        lines.append('')

        if reg.chart_types:
            lines.append("📊 Типы графиков:")
            for tid, td in reg.chart_types.items():
                disp = td.display.get(tr.lang) or td.display.get('en') or tid
                lines.append(f"  • {disp}  (id: {tid})")
                lines.append(f"    fields: {', '.join(td.fields)}")
                lines.append('')

        if getattr(reg, 'animations', None):
            lines.append("🎬 Анимации:")
            for aid, ad in reg.animations.items():
                disp = (ad["display"].get(tr.lang)
                        or ad["display"].get("en") or aid)
                lines.append(f"  • {disp}  (id: {aid})")
                lines.append('')

        if getattr(reg, 'themes', None):
            lines.append("🎨 Темы:")
            for tid, td in reg.themes.items():
                lines.append(f"  • {td.get('name', tid)}  (id: {tid})")
                lines.append('')

        if getattr(reg, 'templates', None):
            lines.append("📋 Шаблоны:")
            for tid, td in reg.templates.items():
                disp = (td["display"].get(tr.lang)
                        or td["display"].get("en") or tid)
                lines.append(f"  • {disp}  (id: {tid})")
                lines.append('')

        if reg.errors:
            lines.append(tr.t('msg.plugins_errors_header'))
            for name, tb in reg.errors:
                lines.append(f"[{name}]")
                lines.append(tb)
                lines.append('')

        if not reg.chart_types and not reg.errors \
                and not getattr(reg, 'animations', None) \
                and not getattr(reg, 'themes', None) \
                and not getattr(reg, 'templates', None):
            lines.append("Плагинов не загружено.")
            lines.append("")
            lines.append("Положите .py-файлы в:")
            try:
                from plugins import PLUGINS_DIR
            except ImportError:
                from grapheditor.plugins import PLUGINS_DIR
            lines.append(f"  {PLUGINS_DIR}")
            lines.append("")
            lines.append("Затем: Плагины → Перезагрузить плагины")

        txt.insert('1.0', '\n'.join(lines))
        txt.configure(state='disabled')

        ttk.Button(win, text=tr.t('msg.pdf_cancel'),
                   command=win.destroy).pack(pady=(0, 10))

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