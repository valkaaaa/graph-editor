"""Сборка интерфейса: _build_ui, поля ввода, панели."""
import tkinter as tk

from tkinter import ttk

from translator import (tr, INTERNAL_TYPES, INTERNAL_ANIM_TYPES)
from settings import UNIT_TO_M, attach_tooltip, FORMULA_TEMPLATES


class BuildUIMixin:

    # ========================================================================
    # UI — СБОРКА
    # ========================================================================
    def _create_scrollable_tab(self, parent_notebook, tab_text):
        """Создает вкладку с вертикальной прокруткой и возвращает внутренний фрейм."""
        container = ttk.Frame(parent_notebook)
        parent_notebook.add(container, text=tab_text)

        canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        inner_frame = ttk.Frame(canvas, padding=5)

        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        inner_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

        def _bind_wheel(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            canvas.bind_all("<Button-5>", _on_mousewheel_linux)

        def _unbind_wheel(e):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)

        return inner_frame

    def _build_ui(self):
        # ---------- Статус-бар (пакуется первым, чтобы не скрывался) ----------
        statusbar = ttk.Frame(self.root, relief=tk.SUNKEN)
        statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.perf_var = tk.StringVar(value='')
        ttk.Label(statusbar, textvariable=self.status_var, anchor=tk.W,
                  padding=(5, 2)).pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Separator(statusbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Label(statusbar, textvariable=self.history_var, anchor=tk.W,
                  padding=(5, 2), foreground="#008000").pack(
            side=tk.LEFT, fill=tk.X, expand=True)
        console_btn = ttk.Button(statusbar, text="🐍 Python", width=12,
                                 command=self._open_console)
        console_btn.pack(side=tk.RIGHT, padx=5, pady=1)
        attach_tooltip(console_btn, "Открыть Python-консоль (Ctrl+`)")

        dsl_btn = ttk.Button(statusbar, text="⌨️ DSL", width=10,
                             command=self._open_dsl_console)
        dsl_btn.pack(side=tk.RIGHT, padx=5, pady=1)
        attach_tooltip(dsl_btn, "Открыть DSL-консоль (Ctrl+Alt+C)")

        ttk.Label(statusbar, textvariable=self.perf_var,
                  anchor=tk.E, padding=(5, 2),
                  foreground="#888").pack(side=tk.RIGHT, padx=5)

        # ---------- Тулбар ----------
        tb = ttk.Frame(self.root, padding=2)
        tb.pack(side=tk.TOP, fill=tk.X)

        for key, icon, cmd in [
            ('toolbar.open_json', 'open', self._load_json),
            ('toolbar.save_json', 'save', self._save_json),
            ('toolbar.zip', 'zip', self._save_zip),
        ]:
            self._tr_button_icon(tb, key, icon, cmd).pack(side=tk.LEFT, padx=2)
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        for key, icon, cmd in [
            ('toolbar.import_csv', 'import', self._import_csv),
            ('toolbar.export_csv', 'export', self._export_csv),
            ('toolbar.export_html', 'html', self._export_html),
        ]:
            self._tr_button_icon(tb, key, icon, cmd).pack(side=tk.LEFT, padx=2)
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        self._tr_button_icon(tb, 'toolbar.save_image', 'image',
                             self._save_image).pack(side=tk.LEFT, padx=2)
        ttk.Separator(tb, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # ---------- Левая панель ----------
        left_frame = ttk.Frame(self.root, padding=5, width=460)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)

        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ---------- Вкладка 1: Создание ----------
        tab_create = self._create_scrollable_tab(self.notebook, tr.t('tab.create'))

        self._tr_label(tab_create, 'create.plot_type').pack(anchor=tk.W)

        type_row = ttk.Frame(tab_create)
        type_row.pack(fill=tk.X, pady=(0, 5))

        # Оставляем скрытый Combobox для совместимости с другими методами
        self.type_combo = ttk.Combobox(
            type_row, textvariable=self.type_var,
            values=[tr.type_name(t) for t in INTERNAL_TYPES],
            state="readonly")
        # self.type_combo.pack(...) — больше не показываем его напрямую

        # Новая кнопка выбора типа
        self.type_btn = ttk.Button(
            type_row,
            textvariable=self.type_var,
            command=self._show_type_picker
        )
        self.type_btn.pack(fill=tk.X, expand=True)

        grid_row = ttk.Frame(tab_create)
        grid_row.pack(fill=tk.X, pady=(0, 5))
        self._tr_label(grid_row, 'create.subplot_grid').pack(side=tk.LEFT)
        self.subplot_grid_combo = ttk.Combobox(
            grid_row, textvariable=self.subplot_grid_var,
            values=['1x1', '1x2', '2x1', '2x2', '2x3', '3x2', '3x3'],
            state='readonly', width=6)
        self.subplot_grid_combo.pack(side=tk.LEFT, padx=5)
        self.subplot_grid_combo.bind('<<ComboboxSelected>>',
                                     self._on_grid_change)
        self._tr_label(grid_row, 'create.subplot_index').pack(
            side=tk.LEFT, padx=(15, 0))
        self.subplot_index_spin = ttk.Spinbox(
            grid_row, from_=0, to=0,
            textvariable=self.subplot_index_var, width=4)
        self.subplot_index_spin.pack(side=tk.LEFT, padx=5)

        self.frame_x = ttk.Frame(tab_create)
        self.frame_y = ttk.Frame(tab_create)
        self.frame_z = ttk.Frame(tab_create)
        self.frame_yerr = ttk.Frame(tab_create)
        self.frame_pie_labels = ttk.Frame(tab_create)
        self.frame_pie_colors = ttk.Frame(tab_create)
        self.frame_bins = ttk.Frame(tab_create)
        self.frame_treemap = ttk.Frame(tab_create)
        self.frame_y2_check = ttk.Frame(tab_create)
        self.frame_fill = ttk.Frame(tab_create)
        self.frame_glow = ttk.Frame(tab_create)
        self.frame_hint = ttk.Frame(tab_create)

        self.entry_x = self._create_entry_with_table(
            self.frame_x, 'create.x_data', "1, 2, 3, 4, 5", 'x')
        self.entry_y = self._create_entry_with_table(
            self.frame_y, 'create.y_data', "10, 20, 15, 25, 30", 'y')
        self.entry_z = self._create_entry_with_table(
            self.frame_z, 'create.z_data', "5, 10, 5, 15, 10", 'z')
        self.entry_yerr = self._create_entry_with_table(
            self.frame_yerr, 'create.yerr', "", 'yerr')

        self.entry_pie = self._create_entry(
            self.frame_pie_labels, 'create.pie_labels',
            "A, B, C, D, E")
        self.entry_pie_colors = self._create_entry(
            self.frame_pie_colors, 'create.pie_colors',
            "red, blue, green, orange, purple")
        self.treemap_parents = self._create_entry(
            self.frame_treemap, 'create.treemap_parents', "")

        self._tr_label(self.frame_bins, 'create.bins').pack(side=tk.LEFT)
        self.bins_var = tk.IntVar(value=10)
        ttk.Spinbox(self.frame_bins, from_=1, to=200,
                    textvariable=self.bins_var, width=6).pack(
            side=tk.LEFT, padx=5)

        self.hint_label = ttk.Label(
            self.frame_hint, text="", foreground="#666",
            font=('Arial', 8), wraplength=420, justify=tk.LEFT)
        self.hint_label.pack(anchor=tk.W)

        self.frame_x.pack(fill=tk.X)
        self.frame_y.pack(fill=tk.X)

        self.use_y2_var = tk.BooleanVar(value=False)
        self.fill_var = tk.BooleanVar(value=False)
        self.glow_var = tk.BooleanVar(value=False)

        self.frame_y2_check.pack(fill=tk.X)
        self._tr_checkbutton(self.frame_y2_check, 'create.use_y2',
                             variable=self.use_y2_var).pack(anchor=tk.W)
        self.frame_fill.pack(fill=tk.X)
        self._tr_checkbutton(self.frame_fill, 'create.fill',
                             variable=self.fill_var).pack(anchor=tk.W)
        self.frame_glow.pack(fill=tk.X)
        self._tr_checkbutton(self.frame_glow, 'create.glow',
                             variable=self.glow_var).pack(anchor=tk.W)

        # Единицы
        units_frame = self._tr_labelframe(tab_create, 'units.title', padding=5)
        units_frame.pack(fill=tk.X, pady=5)
        ur = ttk.Frame(units_frame)
        ur.pack(fill=tk.X)
        ALL_UNITS = ["—", "m", "cm", "mm", "km", "µm", "nm",
                     "in", "ft", "yd", "mi", "nmi",
                     "s", "ms", "µs", "min", "h",
                     "kg", "g", "mg", "t", "lb", "oz"]
        for i, (key, var_name) in enumerate([
            ('units.x_label', 'unit_x_var'),
            ('units.y_label', 'unit_y_var'),
            ('units.z_label', 'unit_z_var'),
        ]):
            self._tr_label(ur, key).grid(row=0, column=i * 2, sticky=tk.W,
                                         padx=(8 if i else 0, 0))
            v = tk.StringVar(value="—")
            setattr(self, var_name, v)
            ttk.Combobox(ur, textvariable=v, values=ALL_UNITS,
                         width=5, state="readonly").grid(
                row=0, column=i * 2 + 1, padx=3)

        # Внешний вид
        style_frame = self._tr_labelframe(tab_create, 'create.appearance', padding=5)
        style_frame.pack(fill=tk.X, pady=5)
        cr = ttk.Frame(style_frame)
        cr.pack(fill=tk.X, pady=2)
        self._tr_label(cr, 'create.color').pack(side=tk.LEFT)
        self.color_var = tk.StringVar(value="blue")
        ttk.Entry(cr, textvariable=self.color_var, width=10).pack(
            side=tk.LEFT, padx=5)
        self._tr_button_icon(cr, 'create.palette', 'palette',
                             self._pick_color).pack(
            side=tk.LEFT, expand=True, fill=tk.X)

        gf = ttk.Frame(style_frame)
        gf.pack(fill=tk.X, pady=2)
        self._tr_label(gf, 'create.linewidth').grid(row=0, column=0, sticky=tk.W)
        self.lw_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(gf, from_=0.5, to=10, increment=0.5,
                    textvariable=self.lw_var, width=5).grid(row=0, column=1, padx=5)
        self._tr_label(gf, 'create.linestyle').grid(row=1, column=0, sticky=tk.W)
        self.ls_var = tk.StringVar(value="-")
        ttk.Combobox(gf, textvariable=self.ls_var,
                     values=["-", "--", ":", "-."], width=5,
                     state="readonly").grid(row=1, column=1, padx=5)
        self._tr_label(gf, 'create.markersize').grid(row=2, column=0, sticky=tk.W)
        self.ms_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(gf, from_=1, to=30, increment=1,
                    textvariable=self.ms_var, width=5).grid(row=2, column=1, padx=5)
        self._tr_label(gf, 'create.marker').grid(row=3, column=0, sticky=tk.W)
        self.marker_var = tk.StringVar(value="o")
        ttk.Combobox(gf, textvariable=self.marker_var,
                     values=["None", "o", "s", "^", "v", "D", "*", "x", "+"],
                     width=5, state="readonly").grid(row=3, column=1, padx=5)

        self._tr_label(tab_create, 'create.name').pack(anchor=tk.W, pady=(5, 0))
        self.entry_label = ttk.Entry(tab_create)
        self.entry_label.pack(fill=tk.X, pady=(0, 5))
        self._tr_label(tab_create, 'create.notes').pack(anchor=tk.W)
        self.entry_notes = ttk.Entry(tab_create)
        self.entry_notes.pack(fill=tk.X, pady=(0, 5))

        bf = ttk.Frame(tab_create)
        bf.pack(fill=tk.X, pady=5)
        self._tr_button_icon(bf, 'create.create_btn', 'create',
                             self._add_graph).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self._tr_button_icon(bf, 'create.apply_btn', 'apply',
                             self._update_graph).pack(
            side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        # ---------- Вкладка 2: Генератор ----------
        tab_gen = self._create_scrollable_tab(self.notebook, tr.t('tab.generator'))

        # 1. Выбор режима и шаблона
        mode_row = ttk.Frame(tab_gen)
        mode_row.pack(fill=tk.X, pady=5)

        self.gen_mode_var = tk.StringVar(value="cartesian")
        self.gen_template_var = tk.StringVar()

        self._tr_label(mode_row, 'Режим:').pack(side=tk.LEFT)
        self.gen_mode_combo = ttk.Combobox(mode_row, textvariable=self.gen_mode_var, state="readonly", width=20)
        self.gen_mode_combo['values'] = [
            "Декартова (y=f(x))",
            "Параметрическая 2D",
            "Полярная (r=θ)",
            "Поверхность 3D (z=f(x,y))",
            "Параметрическая 3D"
        ]
        self._mode_map = {
            "Декартова (y=f(x))": "cartesian",
            "Параметрическая 2D": "parametric",
            "Полярная (r=θ)": "polar",
            "Поверхность 3D (z=f(x,y))": "surface3d",
            "Параметрическая 3D": "parametric3d"
        }
        self._mode_rev_map = {v: k for k, v in self._mode_map.items()}

        self.gen_mode_combo.current(0)
        self.gen_mode_combo.pack(side=tk.LEFT, padx=5)
        self.gen_mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        self._tr_label(mode_row, 'Шаблон:').pack(side=tk.LEFT, padx=(10, 0))
        tmpl_combo = ttk.Combobox(mode_row, textvariable=self.gen_template_var, state="readonly", width=18)
        tmpl_combo['values'] = list(FORMULA_TEMPLATES.keys())
        tmpl_combo.pack(side=tk.LEFT, padx=5)
        tmpl_combo.bind("<<ComboboxSelected>>", self._on_template_select)

        ttk.Button(mode_row, text="?", width=3, command=self._show_formula_help).pack(side=tk.RIGHT, padx=(5, 0))

        # 2. Поля ввода формул
        self.frame_cartesian = ttk.Frame(tab_gen)
        self.frame_parametric = ttk.Frame(tab_gen)
        self.frame_polar = ttk.Frame(tab_gen)
        self.frame_surface3d = ttk.Frame(tab_gen)
        self.frame_parametric3d = ttk.Frame(tab_gen)

        self.gen_expr = ttk.Entry(self.frame_cartesian)
        self.gen_expr.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gen_expr.insert(0, "sin(x) * exp(-x/5)")
        self.gen_expr.bind('<Tab>', self._on_gen_expr_tab)

        ttk.Label(self.frame_parametric, text="x(t) =").pack(side=tk.LEFT)
        self.gen_expr_x = ttk.Entry(self.frame_parametric)
        self.gen_expr_x.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 10))
        self.gen_expr_x.bind('<Tab>', self._on_gen_expr_tab)

        ttk.Label(self.frame_parametric, text="y(t) =").pack(side=tk.LEFT)
        self.gen_expr_y = ttk.Entry(self.frame_parametric)
        self.gen_expr_y.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gen_expr_y.bind('<Tab>', self._on_gen_expr_tab)

        ttk.Label(self.frame_polar, text="r(θ) =").pack(side=tk.LEFT)
        self.gen_expr_polar = ttk.Entry(self.frame_polar)
        self.gen_expr_polar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gen_expr_polar.bind('<Tab>', self._on_gen_expr_tab)

        ttk.Label(self.frame_surface3d, text="z(x,y) =").pack(side=tk.LEFT)
        self.gen_expr_z_surf = ttk.Entry(self.frame_surface3d)
        self.gen_expr_z_surf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.gen_expr_z_surf.insert(0, "sin(sqrt(x**2 + y**2))")

        ttk.Label(self.frame_parametric3d, text="x(t)=").pack(side=tk.LEFT)
        self.gen_expr_x3d = ttk.Entry(self.frame_parametric3d, width=8)
        self.gen_expr_x3d.pack(side=tk.LEFT, padx=2)
        self.gen_expr_x3d.insert(0, "sin(t)")

        ttk.Label(self.frame_parametric3d, text="y(t)=").pack(side=tk.LEFT, padx=(5,0))
        self.gen_expr_y3d = ttk.Entry(self.frame_parametric3d, width=8)
        self.gen_expr_y3d.pack(side=tk.LEFT, padx=2)
        self.gen_expr_y3d.insert(0, "cos(t)")

        ttk.Label(self.frame_parametric3d, text="z(t)=").pack(side=tk.LEFT, padx=(5,0))
        self.gen_expr_z3d = ttk.Entry(self.frame_parametric3d, width=8)
        self.gen_expr_z3d.pack(side=tk.LEFT, padx=2)
        self.gen_expr_z3d.insert(0, "t")

        self.frame_cartesian.pack(fill=tk.X, pady=5)

        # 3. Панель математических символов
        self.math_toolbar = ttk.Frame(tab_gen)
        self.math_toolbar.pack(fill=tk.X, pady=(0, 5))

        MATH_BUTTONS = [
            ("√",      "sqrt()",       -1, True),
            ("x²",     "**2",           0, False),
            ("x³",     "**3",           0, False),
            ("xⁿ",     "**",            0, False),
            ("a/b",    "/",             0, True),
            ("( )",    "()",           -1, False),
            ("sin",    "sin()",        -1, True),
            ("cos",    "cos()",        -1, True),
            ("tan",    "tan()",        -1, True),
            ("arcsin", "arcsin()",     -1, True),
            ("ln",     "log()",        -1, True),
            ("|x|",    "abs()",        -1, True),
            ("π",      "pi",            0, False),
            ("e",      "e",             0, False),
            ("×",      "*",             0, False),
            ("÷",      "/",             0, False),
        ]

        row1 = ttk.Frame(self.math_toolbar)
        row1.pack(fill=tk.X, pady=1)
        row2 = ttk.Frame(self.math_toolbar)
        row2.pack(fill=tk.X, pady=1)

        rows = [row1, row2]
        per_row = (len(MATH_BUTTONS) + 1) // 2
        for i, (label, text, back, wrap) in enumerate(MATH_BUTTONS):
            target_row = rows[i // per_row]
            btn = ttk.Button(
                target_row, text=label, width=6,
                command=lambda t=text, b=back, w=wrap:
                    self._insert_math_symbol(t, b, w))
            btn.pack(side=tk.LEFT, padx=1)

        # 4. Кнопки символьных операций (SymPy)
        sympy_row = ttk.Frame(tab_gen)
        sympy_row.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(sympy_row, text="Упростить",
                   command=lambda: self._sympy_transform('simplify')).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(sympy_row, text="Производная",
                   command=lambda: self._sympy_transform('diff')).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(sympy_row, text="Интеграл",
                   command=lambda: self._sympy_transform('integrate')).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)
        ttk.Button(sympy_row, text="Скобки",
                   command=lambda: self._sympy_transform('expand')).pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)

        # 5. ИИ-помощник
        ai_frame = self._tr_labelframe(tab_gen, 'ИИ-помощник (локальный)', padding=5)
        ai_frame.pack(fill=tk.X, pady=5)
        ai_row = ttk.Frame(ai_frame)
        ai_row.pack(fill=tk.X)
        self.ai_prompt_var = tk.StringVar()
        ttk.Entry(ai_row, textvariable=self.ai_prompt_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(ai_row, text="✨ Сгенерировать", command=self._ai_generate_formula).pack(side=tk.RIGHT)

        ai_model_row = ttk.Frame(ai_frame)
        ai_model_row.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(ai_model_row, text="Модель:").pack(side=tk.LEFT)
        self.ai_model_var = tk.StringVar(value="qwen2.5-coder:1.5b")
        ttk.Entry(ai_model_row, textvariable=self.ai_model_var, width=20).pack(side=tk.LEFT, padx=5)

        # 6. Параметры (ползунки)
        self.frame_params = ttk.LabelFrame(tab_gen, text="Параметры")
        self.frame_params.pack(fill=tk.X, pady=5)
        self.gen_params = {}

        # Триггер обновления ползунков при вводе
        self.gen_expr.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_x.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_y.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_polar.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_z_surf.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_x3d.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_y3d.bind("<KeyRelease>", self._update_gen_params)
        self.gen_expr_z3d.bind("<KeyRelease>", self._update_gen_params)

        # 7. Диапазон и кнопка генерации
        rf = ttk.Frame(tab_gen)
        rf.pack(fill=tk.X, pady=5)
        self._tr_label(rf, 'gen.from').pack(side=tk.LEFT)
        self.gen_xmin = ttk.Entry(rf, width=6)
        self.gen_xmin.pack(side=tk.LEFT, padx=2)
        self.gen_xmin.insert(0, "0")
        self._tr_label(rf, 'gen.to').pack(side=tk.LEFT)
        self.gen_xmax = ttk.Entry(rf, width=6)
        self.gen_xmax.pack(side=tk.LEFT, padx=2)
        self.gen_xmax.insert(0, "10")
        self._tr_label(rf, 'gen.points').pack(side=tk.LEFT, padx=(10, 0))
        self.gen_n = ttk.Entry(rf, width=5)
        self.gen_n.pack(side=tk.LEFT, padx=2)
        self.gen_n.insert(0, "200")

        self._tr_button_icon(tab_gen, 'gen.generate_btn', 'generate',
                             self._generate_data).pack(fill=tk.X, pady=10)

        # 8. Генератор случайных данных
        rnd_frame = self._tr_labelframe(tab_gen, 'gen.random_title', padding=5)
        rnd_frame.pack(fill=tk.X, pady=5)

        r1 = ttk.Frame(rnd_frame)
        r1.pack(fill=tk.X, pady=2)
        self._tr_label(r1, 'gen.distribution').pack(side=tk.LEFT)
        self.rnd_dist_var = tk.StringVar(value="normal")
        ttk.Combobox(r1, textvariable=self.rnd_dist_var,
                     values=["normal", "uniform", "exponential",
                             "poisson", "integers"],
                     width=12, state="readonly").pack(side=tk.LEFT, padx=5)
        self._tr_label(r1, 'gen.n').pack(side=tk.LEFT, padx=(10, 2))
        self.rnd_n_var = tk.IntVar(value=50)
        ttk.Spinbox(r1, from_=1, to=100000,
                    textvariable=self.rnd_n_var, width=7).pack(side=tk.LEFT)

        r_shape = ttk.Frame(rnd_frame)
        r_shape.pack(fill=tk.X, pady=2)
        self._tr_label(r_shape, 'gen.rnd_shape').pack(side=tk.LEFT)
        self.rnd_shape_var = tk.StringVar(value=tr.t('gen.rnd_shape_2d'))
        self.rnd_shape_combo = ttk.Combobox(
            r_shape, textvariable=self.rnd_shape_var,
            values=[tr.t('gen.rnd_shape_2d'), tr.t('gen.rnd_shape_3d'),
                    tr.t('gen.rnd_shape_3d_grid')],
            state='readonly', width=26)
        self.rnd_shape_combo.pack(side=tk.LEFT, padx=5)
        self.rnd_shape_combo.bind('<<ComboboxSelected>>', self._on_rnd_shape_change)

        self.rnd_grid_frame = ttk.Frame(rnd_frame)
        self._tr_label(self.rnd_grid_frame, 'gen.rnd_grid_size').pack(side=tk.LEFT)
        self.rnd_grid_n_var = tk.IntVar(value=15)
        ttk.Spinbox(self.rnd_grid_frame, from_=3, to=200,
                    textvariable=self.rnd_grid_n_var, width=6).pack(side=tk.LEFT, padx=3)
        ttk.Label(self.rnd_grid_frame, text="×").pack(side=tk.LEFT)
        self.rnd_grid_m_var = tk.IntVar(value=15)
        ttk.Spinbox(self.rnd_grid_frame, from_=3, to=200,
                    textvariable=self.rnd_grid_m_var, width=6).pack(side=tk.LEFT, padx=3)

        r2 = ttk.Frame(rnd_frame)
        r2.pack(fill=tk.X, pady=2)
        self._tr_label(r2, 'gen.param1').pack(side=tk.LEFT)
        self.rnd_p1_var = tk.StringVar(value="0")
        ttk.Entry(r2, textvariable=self.rnd_p1_var, width=8).pack(side=tk.LEFT, padx=3)
        self._tr_label(r2, 'gen.param2').pack(side=tk.LEFT, padx=(8, 0))
        self.rnd_p2_var = tk.StringVar(value="1")
        ttk.Entry(r2, textvariable=self.rnd_p2_var, width=8).pack(side=tk.LEFT, padx=3)

        r3 = ttk.Frame(rnd_frame)
        r3.pack(fill=tk.X, pady=2)
        self._tr_label(r3, 'gen.seed').pack(side=tk.LEFT)
        self.rnd_seed_var = tk.StringVar(value="")
        ttk.Entry(r3, textvariable=self.rnd_seed_var, width=8).pack(side=tk.LEFT, padx=3)

        self._tr_button_icon(rnd_frame, 'gen.random_btn', 'dice',
                             self._generate_random_data).pack(fill=tk.X, pady=(5, 0))

        # ---------- Вкладка 3: Объекты ----------
        tab_list = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_list, text=tr.t('tab.objects'))

        search_row = ttk.Frame(tab_list)
        search_row.pack(fill=tk.X, pady=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_var.trace_add('write', lambda *_: self._update_listbox())
        ttk.Button(search_row, text='✕', width=3, command=lambda: self.search_var.set('')).pack(side=tk.RIGHT, padx=(3, 0))

        tree_frame = ttk.Frame(tab_list)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.graph_tree = ttk.Treeview(tree_frame, show='tree', height=12, selectmode='extended')
        self.graph_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(0, 5))
        tree_sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.graph_tree.yview)
        tree_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.graph_tree.configure(yscrollcommand=tree_sb.set)
        self.graph_tree.bind('<Double-1>', self._on_tree_double_click)
        self.graph_tree.bind('<Button-3>', self._on_tree_right_click)

        trend_frame = self._tr_labelframe(tab_list, 'obj.analysis', padding=5)
        trend_frame.pack(fill=tk.X, pady=(0, 5))
        trend_row = ttk.Frame(trend_frame)
        trend_row.pack(fill=tk.X)
        self._tr_label(trend_row, 'obj.trend_degree').pack(side=tk.LEFT)
        self.trend_degree_var = tk.IntVar(value=1)
        ttk.Combobox(trend_row, textvariable=self.trend_degree_var,
                     values=[1, 2, 3], width=3, state="readonly").pack(side=tk.LEFT, padx=5)

        bl = ttk.Frame(tab_list)
        bl.pack(fill=tk.X)
        for key, icon, cmd in [
            ('obj.load_btn', 'load', self._load_selected_to_form),
            ('obj.duplicate_btn', 'duplicate', self._duplicate_graph),
            ('obj.delete_btn', 'delete', self._delete_graph),
        ]:
            self._tr_button_icon(bl, key, icon, cmd).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self._tr_button_icon(bl, 'obj.clear_btn', 'clear', self._clear_all).pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        # ---------- Вкладка 4: Статистика ----------
        tab_stats = self._create_scrollable_tab(self.notebook, tr.t('tab.stats'))

        self.stats_label = ttk.Label(tab_stats, text=tr.t('stats.none_selected'),
                                      font=('Arial', 10, 'bold'), foreground='#666')
        self.stats_label.pack(anchor=tk.W, pady=(0, 5))

        self.stats_frame = self._tr_labelframe(tab_stats, 'stats.title', padding=5)
        self.stats_frame.pack(fill=tk.X, pady=5)
        self.stats_vars = {}
        for label_key, var_name in [
            ('stats.n', 'n'), ('stats.min', 'min'), ('stats.max', 'max'),
            ('stats.mean', 'mean'), ('stats.median', 'median'),
            ('stats.std', 'std'), ('stats.var', 'var'),
            ('stats.q1', 'q1'), ('stats.q3', 'q3'), ('stats.iqr', 'iqr'),
            ('stats.sum', 'sum'), ('stats.corr', 'corr'),
        ]:
            row = ttk.Frame(self.stats_frame)
            row.pack(fill=tk.X, pady=1)
            self._tr_label(row, label_key).pack(side=tk.LEFT)
            v = tk.StringVar(value='—')
            self.stats_vars[var_name] = v
            ttk.Label(row, textvariable=v, font=('Consolas', 10)).pack(side=tk.RIGHT)

        fit_frame = self._tr_labelframe(tab_stats, 'stats.fit_title', padding=5)
        fit_frame.pack(fill=tk.X, pady=5)
        fr1 = ttk.Frame(fit_frame)
        fr1.pack(fill=tk.X, pady=2)
        self._tr_button_icon(fr1, 'stats.fit_linear', 'fit_linear', lambda: self._add_fit('linear')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(fr1, 'stats.fit_log', 'fit_log', lambda: self._add_fit('log')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        fr2 = ttk.Frame(fit_frame)
        fr2.pack(fill=tk.X, pady=2)
        self._tr_button_icon(fr2, 'stats.fit_exp', 'fit_exp', lambda: self._add_fit('exp')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(fr2, 'stats.fit_power', 'fit_power', lambda: self._add_fit('power')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        fr3 = ttk.Frame(fit_frame)
        fr3.pack(fill=tk.X, pady=2)
        self._tr_label(fr3, 'stats.fit_poly').pack(side=tk.LEFT)
        self.fit_degree_var = tk.IntVar(value=2)
        ttk.Spinbox(fr3, from_=1, to=10, textvariable=self.fit_degree_var, width=4).pack(side=tk.LEFT, padx=5)
        self._tr_button_icon(fr3, 'obj.add_trend', 'trend', self._add_fit_poly).pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self.fit_result_var = tk.StringVar(value='')
        ttk.Label(tab_stats, textvariable=self.fit_result_var, font=('Consolas', 9),
                  foreground='#333', wraplength=400, justify=tk.LEFT).pack(anchor=tk.W, pady=5, fill=tk.X)

        peaks_frame = self._tr_labelframe(tab_stats, 'stats.peaks_title', padding=5)
        peaks_frame.pack(fill=tk.X, pady=5)
        self._tr_button_icon(peaks_frame, 'stats.find_peaks', 'search', self._find_peaks).pack(fill=tk.X)

        smooth_frame = self._tr_labelframe(tab_stats, 'stats.smoothing_title', padding=5)
        smooth_frame.pack(fill=tk.X, pady=5)

        sg_row1 = ttk.Frame(smooth_frame)
        sg_row1.pack(fill=tk.X, pady=2)
        self._tr_label(sg_row1, 'stats.savgol_window').pack(side=tk.LEFT)
        ttk.Spinbox(sg_row1, from_=3, to=101, increment=2, textvariable=self.savgol_window_var, width=5).pack(side=tk.LEFT, padx=5)
        self._tr_label(sg_row1, 'stats.savgol_poly').pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(sg_row1, from_=1, to=6, textvariable=self.savgol_poly_var, width=4).pack(side=tk.LEFT, padx=5)

        self._tr_button_icon(smooth_frame, 'stats.savgol_btn', 'smooth', self._apply_savgol).pack(fill=tk.X, pady=(4, 2))

        ip_row1 = ttk.Frame(smooth_frame)
        ip_row1.pack(fill=tk.X, pady=(8, 2))
        self._tr_label(ip_row1, 'stats.interp_method').pack(side=tk.LEFT)
        ttk.Combobox(ip_row1, textvariable=self.interp_method_var, values=['linear', 'cubic', 'pchip'], width=10, state='readonly').pack(side=tk.LEFT, padx=5)
        self._tr_label(ip_row1, 'stats.interp_points').pack(side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(ip_row1, from_=50, to=5000, increment=50, textvariable=self.interp_n_var, width=6).pack(side=tk.LEFT, padx=5)

        self._tr_button_icon(smooth_frame, 'stats.interp_btn', 'interp', self._apply_interpolation).pack(fill=tk.X, pady=(4, 0))

        calc_frame = self._tr_labelframe(tab_stats, 'stats.calc_title', padding=5)
        calc_frame.pack(fill=tk.X, pady=5)
        row_di = ttk.Frame(calc_frame)
        row_di.pack(fill=tk.X, pady=2)
        self._tr_button_icon(row_di, 'stats.derivative_btn', 'deriv', self._add_derivative).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(row_di, 'stats.integral_btn', 'integr', self._add_integral).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # ---------- Правая панель ----------
        right_frame = ttk.Frame(self.root, padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.settings_frame = self._tr_labelframe(right_frame, 'right.canvas_settings', padding=5)
        self.settings_frame.pack(fill=tk.X, pady=(0, 5))
        for i, (key, var) in enumerate([
            ('right.title', self.plot_title_var),
            ('right.xlabel', self.plot_xlabel_var),
            ('right.ylabel', self.plot_ylabel_var),
        ]):
            self._tr_label(self.settings_frame, key).grid(row=i, column=0, sticky=tk.W)
            ttk.Entry(self.settings_frame, textvariable=var, width=20).grid(row=i, column=1, padx=5, pady=2)
        self._tr_button_icon(self.settings_frame, 'right.apply', 'apply', self._apply_canvas_settings).grid(row=0, column=2, rowspan=3, padx=5)

        self.limits_frame = self._tr_labelframe(right_frame, 'right.limits', padding=5)
        self.limits_frame.pack(fill=tk.X, pady=(0, 5))
        self.lim_auto_var = tk.BooleanVar(value=True)
        self._tr_checkbutton(self.limits_frame, 'right.limits_auto', variable=self.lim_auto_var, command=self._apply_limits).grid(row=0, column=0, rowspan=2, padx=5, sticky=tk.W)
        limits_conf = [
            ('right.limits_xmin', 'lim_xmin', 0, 1),
            ('right.limits_xmax', 'lim_xmax', 0, 3),
            ('right.limits_ymin', 'lim_ymin', 1, 1),
            ('right.limits_ymax', 'lim_ymax', 1, 3),
        ]
        for key, var_name, row, col in limits_conf:
            self._tr_label(self.limits_frame, key).grid(row=row, column=col, sticky=tk.E, padx=2)
            v = tk.StringVar(value="")
            setattr(self, var_name, v)
            ttk.Entry(self.limits_frame, textvariable=v, width=8).grid(row=row, column=col + 1, padx=2, pady=2)
        self._tr_button_icon(self.limits_frame, 'right.apply', 'apply', self._apply_limits).grid(row=0, column=5, rowspan=2, padx=10)

        self.anim_labelframe = self._tr_labelframe(right_frame, 'right.anim_engine', padding=5)
        self.anim_labelframe.pack(fill=tk.X, pady=(0, 5))
        ar = ttk.Frame(self.anim_labelframe)
        ar.pack(fill=tk.X, pady=2)
        self._tr_label(ar, 'right.anim_type').pack(side=tk.LEFT, padx=(0, 5))
        self.anim_combo = ttk.Combobox(ar, textvariable=self.anim_type_var, values=[tr.anim_name(a) for a in INTERNAL_ANIM_TYPES], state="readonly", width=22)
        self.anim_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.anim_combo.bind("<<ComboboxSelected>>", self._on_anim_type_change)
        self.anim_speed_var = tk.IntVar(value=30)
        self._tr_label(ar, 'right.anim_frame_ms').pack(side=tk.LEFT, padx=(10, 2))
        ttk.Spinbox(ar, from_=10, to=500, increment=10, textvariable=self.anim_speed_var, width=5).pack(side=tk.LEFT)

        self.frame_custom_anim = ttk.Frame(self.anim_labelframe)
        ttk.Label(self.frame_custom_anim, text="y(x,t)/z(x,y,t):").pack(side=tk.LEFT)
        self.entry_custom_anim = ttk.Entry(self.frame_custom_anim, width=22)
        self.entry_custom_anim.pack(side=tk.LEFT, padx=5)
        self.entry_custom_anim.insert(0, "sin(x + t) * cos(t/2)")
        ttk.Button(self.frame_custom_anim, text="?", width=3, command=self._show_formula_help).pack(side=tk.LEFT)

        baf = ttk.Frame(self.anim_labelframe)
        baf.pack(fill=tk.X)
        for key, icon, cmd in [
            ('right.anim_start', 'play', self._start_animation),
            ('right.anim_pause', 'pause', self._toggle_pause_anim),
            ('right.anim_stop', 'stop', self._stop_animation),
            ('right.anim_save', 'save', self._save_animation),
            ('right.anim_save_file', 'package', self._save_graphxanim),
            ('right.anim_load_file', 'open', self._load_graphxanim),
        ]:
            self._tr_button_icon(baf, key, icon, cmd).pack(side=tk.LEFT, padx=2)
        self.anim_progress = ttk.Progressbar(self.anim_labelframe, maximum=self.anim_frames_total, mode='determinate')
        self.anim_progress.pack(fill=tk.X, padx=2, pady=(3, 0))

        self.plot_notebook = ttk.Notebook(right_frame)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)
        self.plot_notebook.bind('<<NotebookTabChanged>>', self._on_plot_tab_changed)
        self._build_documents_bar(right_frame)
        self.plot_frame = None

    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ UI
    # ========================================================================
    def _create_entry(self, parent, label_key, default_text):
        self._tr_label(parent, label_key).pack(anchor=tk.W)
        entry = ttk.Entry(parent)
        entry.pack(fill=tk.X, pady=(0, 5))
        entry.insert(0, default_text)
        return entry

    def _create_entry_with_table(self, parent, label_key, default_text, axis):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 5))
        self._tr_label(frame, label_key).pack(anchor=tk.W)
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.insert(0, default_text)
        entry.bind("<KeyRelease>", self._on_data_change)
        self._tr_button(frame, 'create.table_btn', lambda: self._open_table_editor(axis), width=8).pack(side=tk.RIGHT, padx=(5, 0))
        return entry

    def _toggle_ui_panels(self):
        anchor = getattr(self, 'plot_notebook', None) or self.plot_frame
        if anchor is None:
            return

        if self.show_anim_var.get():
            self.anim_labelframe.pack(fill=tk.X, pady=(0, 5), before=anchor)
        else:
            self.anim_labelframe.pack_forget()

        if self.show_limits_var.get():
            target = (self.anim_labelframe if self.show_anim_var.get() else anchor)
            self.limits_frame.pack(fill=tk.X, pady=(0, 5), before=target)
        else:
            self.limits_frame.pack_forget()

        if self.show_settings_var.get():
            if self.show_limits_var.get():
                target = self.limits_frame
            elif self.show_anim_var.get():
                target = self.anim_labelframe
            else:
                target = anchor
            self.settings_frame.pack(fill=tk.X, pady=(0, 5), before=target)
        else:
            self.settings_frame.pack_forget()

    def _active_gen_entry(self):
        mode = getattr(self, 'gen_mode_var', None)
        mode = mode.get() if mode else "cartesian"
        if mode == "cartesian":
            return self.gen_expr
        elif mode == "parametric":
            try:
                focused = self.root.focus_get()
                if focused == self.gen_expr_y:
                    return self.gen_expr_y
            except Exception:
                pass
            return self.gen_expr_x
        elif mode == "polar":
            return self.gen_expr_polar
        elif mode == "surface3d":
            return self.gen_expr_z_surf
        elif mode == "parametric3d":
            try:
                focused = self.root.focus_get()
                if focused == self.gen_expr_y3d:
                    return self.gen_expr_y3d
                elif focused == self.gen_expr_z3d:
                    return self.gen_expr_z3d
            except Exception:
                pass
            return self.gen_expr_x3d
        return self.gen_expr

    def _insert_math_symbol(self, text, back_offset=0, wrap=False):
        entry = self._active_gen_entry()
        if entry is None:
            return

        try:
            has_selection = True
            sel_start = entry.index(tk.SEL_FIRST)
            sel_end = entry.index(tk.SEL_LAST)
        except tk.TclError:
            has_selection = False

        if wrap and has_selection:
            selected = entry.get()[sel_start:sel_end]
            if text in ("sqrt()", "sin()", "cos()", "tan()",
                        "arcsin()", "arctan()", "log()", "abs()"):
                func_name = text[:-2]
                new_text = f"{func_name}({selected})"
                entry.delete(sel_start, sel_end)
                entry.insert(sel_start, new_text)
                entry.icursor(sel_start + len(new_text))
            elif text == "/":
                new_text = f"({selected})/"
                entry.delete(sel_start, sel_end)
                entry.insert(sel_start, new_text)
                entry.icursor(sel_start + len(new_text))
            else:
                entry.delete(sel_start, sel_end)
                entry.insert(sel_start, text)
                if back_offset:
                    entry.icursor(sel_start + len(text) + back_offset)
                else:
                    entry.icursor(sel_start + len(text))
        else:
            try:
                pos = entry.index(tk.INSERT)
            except Exception:
                pos = len(entry.get())

            if has_selection:
                entry.delete(sel_start, sel_end)
                pos = sel_start

            entry.insert(pos, text)

            if back_offset:
                new_pos = pos + len(text) + back_offset
            else:
                new_pos = pos + len(text)
            entry.icursor(new_pos)

        entry.focus_set()

    def _on_gen_expr_tab(self, event):
        entry = event.widget
        try:
            pos = entry.index(tk.INSERT)
        except Exception:
            return

        text = entry.get()
        next_paren = text.find('()', pos)
        if next_paren >= 0:
            entry.icursor(next_paren + 1)
            return 'break'
        return None

    def _on_mode_change(self, event=None):
        display = self.gen_mode_combo.get()
        mode = self._mode_map.get(display, "cartesian")
        self.gen_mode_var.set(mode)

        for f in [self.frame_cartesian, self.frame_parametric,
                  self.frame_polar, self.frame_surface3d, self.frame_parametric3d]:
            f.pack_forget()

        if mode == "cartesian":
            self.frame_cartesian.pack(fill=tk.X, pady=5, before=self.math_toolbar)
        elif mode == "parametric":
            self.frame_parametric.pack(fill=tk.X, pady=5, before=self.math_toolbar)
        elif mode == "polar":
            self.frame_polar.pack(fill=tk.X, pady=5, before=self.math_toolbar)
        elif mode == "surface3d":
            self.frame_surface3d.pack(fill=tk.X, pady=5, before=self.math_toolbar)
        elif mode == "parametric3d":
            self.frame_parametric3d.pack(fill=tk.X, pady=5, before=self.math_toolbar)

        self._update_gen_params()

    def _categorize_type(self, t):
        """Автоматически распределяет тип по категориям на основе ключевых слов."""
        if "3D" in t:
            if t in ("Radial tree 3D", "Ribbon plot 3D", "Waterfall spectrogram 3D",
                     "Riemann surface 3D", "Joyplot 3D", "Isosurface 3D"):
                return "3D: Специальные"
            return "3D: Базовые"

        stats = ("Box plot", "Violin", "Strip plot", "Ridge plot", "Raincloud",
                 "Beanplot", "Swarm", "Cherry", "Dot-and-whisker", "Q-Q", "ECDF",
                 "Hexbin", "Сезонная", "Rolling")
        if t in stats:
            return "2D: Статистика"

        networks = ("Дендрограмма", "Cluster", "Sankey", "Alluvial", "Chord",
                    "Сетевой", "Hive", "Arc", "Дерево", "Circle", "Adjacency", "Mapper")
        if t in networks:
            return "2D: Сетевые и иерархия"

        fin = ("Свечи", "Renko", "Point-and-Figure", "Парето", "Гант", "Воронка", "Bullet")
        if t in fin:
            return "2D: Финансы и проекты"

        fields = ("Heatmap", "Contour", "Imshow", "Stream", "Quiver", "Isopleth",
                  "Dot density", "Choropleth", "Cartogram")
        if t in fields:
            return "2D: Поля и матрицы"

        return "2D: Базовые и специальные"

    def _show_type_picker(self):
        """Открывает окно выбора типа графика с поиском и категориями."""
        win = tk.Toplevel(self.root)
        win.title("Выбор типа графика")
        win.geometry("500x650")
        win.transient(self.root)

        # Поиск
        search_frame = ttk.Frame(win, padding=10)
        search_frame.pack(fill=tk.X)
        ttk.Label(search_frame, text="🔍 Поиск:").pack(side=tk.LEFT)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.focus_set()

        # Дерево с категориями
        tree_frame = ttk.Frame(win, padding=(10, 0))
        tree_frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(tree_frame, show='tree', selectmode='browse')
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)

        # Функция заполнения дерева с учетом фильтра
        def populate(query=""):
            tree.delete(*tree.get_children())
            query = query.lower().strip()

            # Собираем все типы по категориям
            categories = {}
            for t in INTERNAL_TYPES:
                cat = self._categorize_type(t)
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(t)

            for cat_name in sorted(categories.keys()):
                matching = []
                for t in categories[cat_name]:
                    disp = tr.type_name(t)
                    if not query or query in disp.lower() or query in t.lower():
                        matching.append((t, disp))

                if matching:
                    # Добавляем категорию (открытую)
                    cat_node = tree.insert('', 'end', text=f"📁 {cat_name}", open=True)
                    for t, disp in matching:
                        tree.insert(cat_node, 'end', text=disp, values=(t,))

        populate()

        # Привязка поиска
        def on_search(*args):
            populate(search_var.get())

        search_var.trace_add('write', on_search)

        # Выбор элемента
        def on_select(event=None):
            sel = tree.selection()
            if not sel:
                return
            item = sel[0]
            vals = tree.item(item, 'values')
            if vals:  # Если это лист (тип графика), а не папка
                internal_id = vals[0]
                display_name = tr.type_name(internal_id)
                self.type_var.set(display_name)
                win.destroy()
                self._on_type_change()

        tree.bind('<Double-1>', on_select)

        # Кнопки
        btn_frame = ttk.Frame(win, padding=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(btn_frame, text="Выбрать", command=on_select).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _on_template_select(self, event=None):
        name = self.gen_template_var.get()
        tmpl = FORMULA_TEMPLATES.get(name)
        if not tmpl:
            return

        mode = tmpl.get("mode", "cartesian")
        self.gen_mode_var.set(mode)
        self.gen_mode_combo.set(self._mode_rev_map.get(mode, "Декартова (y=f(x))"))

        for f in [self.frame_cartesian, self.frame_parametric,
                  self.frame_polar, self.frame_surface3d, self.frame_parametric3d]:
            f.pack_forget()

        if mode == "cartesian":
            self.frame_cartesian.pack(fill=tk.X, pady=5, before=self.math_toolbar)
            self.gen_expr.delete(0, tk.END)
            self.gen_expr.insert(0, tmpl.get("expr", ""))
        elif mode == "parametric":
            self.frame_parametric.pack(fill=tk.X, pady=5, before=self.math_toolbar)
            self.gen_expr_x.delete(0, tk.END)
            self.gen_expr_x.insert(0, tmpl.get("expr_x", ""))
            self.gen_expr_y.delete(0, tk.END)
            self.gen_expr_y.insert(0, tmpl.get("expr_y", ""))
        elif mode == "polar":
            self.frame_polar.pack(fill=tk.X, pady=5, before=self.math_toolbar)
            self.gen_expr_polar.delete(0, tk.END)
            self.gen_expr_polar.insert(0, tmpl.get("expr", ""))
        elif mode == "surface3d":
            self.frame_surface3d.pack(fill=tk.X, pady=5, before=self.math_toolbar)
            self.gen_expr_z_surf.delete(0, tk.END)
            self.gen_expr_z_surf.insert(0, tmpl.get("expr", ""))
        elif mode == "parametric3d":
            self.frame_parametric3d.pack(fill=tk.X, pady=5, before=self.math_toolbar)
            self.gen_expr_x3d.delete(0, tk.END)
            self.gen_expr_x3d.insert(0, tmpl.get("expr_x", ""))
            self.gen_expr_y3d.delete(0, tk.END)
            self.gen_expr_y3d.insert(0, tmpl.get("expr_y", ""))
            self.gen_expr_z3d.delete(0, tk.END)
            self.gen_expr_z3d.insert(0, tmpl.get("expr_z", ""))

        self.gen_xmin.delete(0, tk.END)
        self.gen_xmin.insert(0, str(tmpl.get("xmin", 0)))
        self.gen_xmax.delete(0, tk.END)
        self.gen_xmax.insert(0, str(tmpl.get("xmax", 10)))

        self._update_gen_params()

    def _update_gen_params(self, event=None):
        import re
        for widget in self.frame_params.winfo_children():
            widget.destroy()
        self.gen_params.clear()

        text = ""
        mode = self.gen_mode_var.get()
        if mode == "cartesian":
            text += self.gen_expr.get() + " "
        elif mode == "parametric":
            text += self.gen_expr_x.get() + " " + self.gen_expr_y.get() + " "
        elif mode == "polar":
            text += self.gen_expr_polar.get() + " "
        elif mode == "surface3d":
            text += self.gen_expr_z_surf.get() + " "
        elif mode == "parametric3d":
            text += (self.gen_expr_x3d.get() + " " +
                     self.gen_expr_y3d.get() + " " +
                     self.gen_expr_z3d.get() + " ")

        if not text.strip():
            return

        reserved = {'x', 't', 'y', 'e', 'r', 'i', 'o'}
        found_vars = set(re.findall(r'\b[a-zA-Z]\b', text)) - reserved

        if not found_vars:
            ttk.Label(self.frame_params, text="Нет переменных (используйте a, b, c...)",
                      foreground="gray").pack()
            return

        for var_name in sorted(found_vars):
            row = ttk.Frame(self.frame_params)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=f"{var_name} =").pack(side=tk.LEFT)

            var = tk.DoubleVar(value=1.0)
            self.gen_params[var_name] = var

            scale = ttk.Scale(row, from_=-10.0, to=10.0, variable=var, orient=tk.HORIZONTAL)
            scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            val_label = ttk.Label(row, text="1.00", width=5)
            val_label.pack(side=tk.LEFT)

            def make_updater(v=var, lbl=val_label):
                return lambda *_: lbl.config(text=f"{v.get():.2f}")
            var.trace_add("write", make_updater())