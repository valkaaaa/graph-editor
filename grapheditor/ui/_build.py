"""Сборка интерфейса: _build_ui, поля ввода, панели."""
import tkinter as tk

from tkinter import ttk

from translator import (tr, INTERNAL_TYPES, INTERNAL_ANIM_TYPES)
from settings import UNIT_TO_M, attach_tooltip


class BuildUIMixin:

    # ========================================================================
    # UI — СБОРКА
    # ========================================================================
    def _build_ui(self):
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

        left_frame = ttk.Frame(self.root, padding=5, width=440)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        left_frame.pack_propagate(False)

        self.notebook = ttk.Notebook(left_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ---------- Создание ----------
        tab_create = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_create, text=tr.t('tab.create'))

        self._tr_label(tab_create, 'create.plot_type').pack(anchor=tk.W)
        self.type_combo = ttk.Combobox(
            tab_create, textvariable=self.type_var,
            values=[tr.type_name(t) for t in INTERNAL_TYPES],
            state="readonly")
        self.type_combo.pack(fill=tk.X, pady=(0, 5))
        self.type_combo.bind("<<ComboboxSelected>>", self._on_type_change)

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
            "Яблоки, Груши, Сливы, Персики, Абрикосы")
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
        units_frame = self._tr_labelframe(tab_create, 'units.title',
                                          padding=5)
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
        style_frame = self._tr_labelframe(tab_create, 'create.appearance',
                                          padding=5)
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
        self._tr_label(gf, 'create.linewidth').grid(
            row=0, column=0, sticky=tk.W)
        self.lw_var = tk.DoubleVar(value=2.0)
        ttk.Spinbox(gf, from_=0.5, to=10, increment=0.5,
                    textvariable=self.lw_var, width=5).grid(
            row=0, column=1, padx=5)
        self._tr_label(gf, 'create.linestyle').grid(
            row=1, column=0, sticky=tk.W)
        self.ls_var = tk.StringVar(value="-")
        ttk.Combobox(gf, textvariable=self.ls_var,
                     values=["-", "--", ":", "-."], width=5,
                     state="readonly").grid(row=1, column=1, padx=5)
        self._tr_label(gf, 'create.markersize').grid(
            row=2, column=0, sticky=tk.W)
        self.ms_var = tk.DoubleVar(value=6.0)
        ttk.Spinbox(gf, from_=1, to=30, increment=1,
                    textvariable=self.ms_var, width=5).grid(
            row=2, column=1, padx=5)
        self._tr_label(gf, 'create.marker').grid(
            row=3, column=0, sticky=tk.W)
        self.marker_var = tk.StringVar(value="o")
        ttk.Combobox(gf, textvariable=self.marker_var,
                     values=["None", "o", "s", "^", "v", "D", "*", "x", "+"],
                     width=5, state="readonly").grid(
            row=3, column=1, padx=5)

        self._tr_label(tab_create, 'create.name').pack(
            anchor=tk.W, pady=(5, 0))
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

        # ---------- Генератор ----------
        tab_gen = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_gen, text=tr.t('tab.generator'))
        self._tr_label(tab_gen, 'gen.formula_label',
                       font=('Arial', 9, 'bold')).pack(
            anchor=tk.W, pady=(0, 2))
        self._tr_label(tab_gen, 'gen.formula_hint',
                       foreground="gray", wraplength=400).pack(
            anchor=tk.W)

        expr_row = ttk.Frame(tab_gen)
        expr_row.pack(fill=tk.X, pady=5)
        self.gen_expr = ttk.Entry(expr_row)
        self.gen_expr.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.gen_expr.insert(0, "sin(x) * exp(-x/5)")
        ttk.Button(expr_row, text="?", width=3,
                   command=self._show_formula_help).pack(side=tk.RIGHT, padx=(5, 0))

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
        self.gen_n.insert(0, "50")
        self._tr_label(rf, 'gen.unit').pack(side=tk.LEFT, padx=(10, 2))
        self.gen_unit_var = tk.StringVar(value="m")
        self.gen_unit_combo = ttk.Combobox(
            rf, textvariable=self.gen_unit_var,
            values=list(UNIT_TO_M.keys()), width=5, state="readonly")
        self.gen_unit_combo.pack(side=tk.LEFT)

        self._tr_button_icon(tab_gen, 'gen.generate_btn', 'generate',
                             self._generate_data).pack(fill=tk.X, pady=10)

        rnd_frame = self._tr_labelframe(tab_gen, 'gen.random_title',
                                        padding=5)
        rnd_frame.pack(fill=tk.X, pady=5)
        r1 = ttk.Frame(rnd_frame)
        r1.pack(fill=tk.X, pady=2)
        self._tr_label(r1, 'gen.distribution').pack(side=tk.LEFT)
        self.rnd_dist_var = tk.StringVar(value="normal")
        ttk.Combobox(r1, textvariable=self.rnd_dist_var,
                     values=["normal", "uniform", "exponential",
                             "poisson", "integers"],
                     width=12, state="readonly").pack(
            side=tk.LEFT, padx=5)
        self._tr_label(r1, 'gen.n').pack(side=tk.LEFT, padx=(10, 2))
        self.rnd_n_var = tk.IntVar(value=50)
        ttk.Spinbox(r1, from_=1, to=100000,
                    textvariable=self.rnd_n_var, width=7).pack(
            side=tk.LEFT)

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
        self.rnd_shape_combo.bind('<<ComboboxSelected>>',
                                  self._on_rnd_shape_change)

        self.rnd_grid_frame = ttk.Frame(rnd_frame)
        self._tr_label(self.rnd_grid_frame, 'gen.rnd_grid_size').pack(
            side=tk.LEFT)
        self.rnd_grid_n_var = tk.IntVar(value=15)
        ttk.Spinbox(self.rnd_grid_frame, from_=3, to=200,
                    textvariable=self.rnd_grid_n_var, width=6).pack(
            side=tk.LEFT, padx=3)
        ttk.Label(self.rnd_grid_frame, text="×").pack(side=tk.LEFT)
        self.rnd_grid_m_var = tk.IntVar(value=15)
        ttk.Spinbox(self.rnd_grid_frame, from_=3, to=200,
                    textvariable=self.rnd_grid_m_var, width=6).pack(
            side=tk.LEFT, padx=3)

        r2 = ttk.Frame(rnd_frame)
        r2.pack(fill=tk.X, pady=2)
        self._tr_label(r2, 'gen.param1').pack(side=tk.LEFT)
        self.rnd_p1_var = tk.StringVar(value="0")
        ttk.Entry(r2, textvariable=self.rnd_p1_var, width=8).pack(
            side=tk.LEFT, padx=3)
        self._tr_label(r2, 'gen.param2').pack(side=tk.LEFT, padx=(8, 0))
        self.rnd_p2_var = tk.StringVar(value="1")
        ttk.Entry(r2, textvariable=self.rnd_p2_var, width=8).pack(
            side=tk.LEFT, padx=3)
        r3 = ttk.Frame(rnd_frame)
        r3.pack(fill=tk.X, pady=2)
        self._tr_label(r3, 'gen.seed').pack(side=tk.LEFT)
        self.rnd_seed_var = tk.StringVar(value="")
        ttk.Entry(r3, textvariable=self.rnd_seed_var, width=8).pack(
            side=tk.LEFT, padx=3)
        self._tr_button_icon(rnd_frame, 'gen.random_btn', 'dice',
                             self._generate_random_data).pack(
            fill=tk.X, pady=(5, 0))

        # ---------- Объекты ----------
        tab_list = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_list, text=tr.t('tab.objects'))

        search_row = ttk.Frame(tab_list)
        search_row.pack(fill=tk.X, pady=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_var.trace_add('write',
                                  lambda *_: self._update_listbox())
        ttk.Button(search_row, text='✕', width=3,
                   command=lambda: self.search_var.set('')
                   ).pack(side=tk.RIGHT, padx=(3, 0))

        tree_frame = ttk.Frame(tab_list)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.graph_tree = ttk.Treeview(tree_frame, show='tree', height=12,
                                       selectmode='extended')
        self.graph_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                             pady=(0, 5))
        tree_sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                                command=self.graph_tree.yview)
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
                     values=[1, 2, 3], width=3,
                     state="readonly").pack(side=tk.LEFT, padx=5)

        bl = ttk.Frame(tab_list)
        bl.pack(fill=tk.X)
        for key, icon, cmd in [
            ('obj.load_btn', 'load', self._load_selected_to_form),
            ('obj.duplicate_btn', 'duplicate', self._duplicate_graph),
            ('obj.delete_btn', 'delete', self._delete_graph),
        ]:
            self._tr_button_icon(bl, key, icon, cmd).pack(
                side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        self._tr_button_icon(bl, 'obj.clear_btn', 'clear',
                             self._clear_all).pack(
            side=tk.RIGHT, expand=True, fill=tk.X, padx=2)

        # ---------- Статистика ----------
        tab_stats = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_stats, text=tr.t('tab.stats'))
        self.stats_label = ttk.Label(
            tab_stats, text=tr.t('stats.none_selected'),
            font=('Arial', 10, 'bold'), foreground='#666')
        self.stats_label.pack(anchor=tk.W, pady=(0, 5))

        self.stats_frame = self._tr_labelframe(tab_stats, 'stats.title',
                                               padding=5)
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
            ttk.Label(row, textvariable=v,
                      font=('Consolas', 10)).pack(side=tk.RIGHT)

        fit_frame = self._tr_labelframe(tab_stats, 'stats.fit_title',
                                        padding=5)
        fit_frame.pack(fill=tk.X, pady=5)
        fr1 = ttk.Frame(fit_frame)
        fr1.pack(fill=tk.X, pady=2)
        self._tr_button_icon(fr1, 'stats.fit_linear', 'fit_linear',
                             lambda: self._add_fit('linear')).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(fr1, 'stats.fit_log', 'fit_log',
                             lambda: self._add_fit('log')).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        fr2 = ttk.Frame(fit_frame)
        fr2.pack(fill=tk.X, pady=2)
        self._tr_button_icon(fr2, 'stats.fit_exp', 'fit_exp',
                             lambda: self._add_fit('exp')).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(fr2, 'stats.fit_power', 'fit_power',
                             lambda: self._add_fit('power')).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        fr3 = ttk.Frame(fit_frame)
        fr3.pack(fill=tk.X, pady=2)
        self._tr_label(fr3, 'stats.fit_poly').pack(side=tk.LEFT)
        self.fit_degree_var = tk.IntVar(value=2)
        ttk.Spinbox(fr3, from_=1, to=10,
                    textvariable=self.fit_degree_var, width=4).pack(
            side=tk.LEFT, padx=5)
        self._tr_button_icon(fr3, 'obj.add_trend', 'trend',
                             self._add_fit_poly).pack(
            side=tk.RIGHT, fill=tk.X, expand=True)

        self.fit_result_var = tk.StringVar(value='')
        ttk.Label(tab_stats, textvariable=self.fit_result_var,
                  font=('Consolas', 9), foreground='#333',
                  wraplength=400, justify=tk.LEFT).pack(
            anchor=tk.W, pady=5, fill=tk.X)

        peaks_frame = self._tr_labelframe(tab_stats, 'stats.peaks_title',
                                          padding=5)
        peaks_frame.pack(fill=tk.X, pady=5)
        self._tr_button_icon(peaks_frame, 'stats.find_peaks', 'search',
                             self._find_peaks).pack(fill=tk.X)

        # ---------- Обработка сигналов ----------
        smooth_frame = self._tr_labelframe(
            tab_stats, 'stats.smoothing_title', padding=5)
        smooth_frame.pack(fill=tk.X, pady=5)

        # --- Савицкий-Голей ---
        sg_row1 = ttk.Frame(smooth_frame)
        sg_row1.pack(fill=tk.X, pady=2)
        self._tr_label(sg_row1, 'stats.savgol_window').pack(side=tk.LEFT)
        ttk.Spinbox(
            sg_row1, from_=3, to=101, increment=2,
            textvariable=self.savgol_window_var, width=5
        ).pack(side=tk.LEFT, padx=5)
        self._tr_label(sg_row1, 'stats.savgol_poly').pack(
            side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(
            sg_row1, from_=1, to=6,
            textvariable=self.savgol_poly_var, width=4
        ).pack(side=tk.LEFT, padx=5)

        self._tr_button_icon(
            smooth_frame, 'stats.savgol_btn', 'smooth',
            self._apply_savgol).pack(fill=tk.X, pady=(4, 2))

        # --- Интерполяция ---
        ip_row1 = ttk.Frame(smooth_frame)
        ip_row1.pack(fill=tk.X, pady=(8, 2))
        self._tr_label(ip_row1, 'stats.interp_method').pack(side=tk.LEFT)
        ttk.Combobox(
            ip_row1, textvariable=self.interp_method_var,
            values=['linear', 'cubic', 'pchip'],
            width=10, state='readonly'
        ).pack(side=tk.LEFT, padx=5)
        self._tr_label(ip_row1, 'stats.interp_points').pack(
            side=tk.LEFT, padx=(10, 0))
        ttk.Spinbox(
            ip_row1, from_=50, to=5000, increment=50,
            textvariable=self.interp_n_var, width=6
        ).pack(side=tk.LEFT, padx=5)

        self._tr_button_icon(
            smooth_frame, 'stats.interp_btn', 'interp',
            self._apply_interpolation).pack(fill=tk.X, pady=(4, 0))

        # --- Производная / интеграл ---
        calc_frame = self._tr_labelframe(
            tab_stats, 'stats.calc_title', padding=5)
        calc_frame.pack(fill=tk.X, pady=5)

        row_di = ttk.Frame(calc_frame)
        row_di.pack(fill=tk.X, pady=2)
        self._tr_button_icon(row_di, 'stats.derivative_btn',
                             'deriv', self._add_derivative).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        self._tr_button_icon(row_di, 'stats.integral_btn',
                             'integr', self._add_integral).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)

        # ---------- Правая панель ----------
        right_frame = ttk.Frame(self.root, padding=5)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ---------- Правая панель: настройки холста ----------
        self.settings_frame = self._tr_labelframe(
            right_frame, 'right.canvas_settings', padding=5)
        self.settings_frame.pack(fill=tk.X, pady=(0, 5))
        for i, (key, var) in enumerate([
            ('right.title', self.plot_title_var),
            ('right.xlabel', self.plot_xlabel_var),
            ('right.ylabel', self.plot_ylabel_var),
        ]):
            self._tr_label(self.settings_frame, key).grid(
                row=i, column=0, sticky=tk.W)
            ttk.Entry(self.settings_frame, textvariable=var,
                      width=20).grid(row=i, column=1, padx=5, pady=2)
        self._tr_button_icon(self.settings_frame, 'right.apply', 'apply',
                             self._apply_canvas_settings).grid(
            row=0, column=2, rowspan=3, padx=5)

        # ---------- Правая панель: пределы осей ----------
        self.limits_frame = self._tr_labelframe(
            right_frame, 'right.limits', padding=5)
        self.limits_frame.pack(fill=tk.X, pady=(0, 5))
        self.lim_auto_var = tk.BooleanVar(value=True)
        self._tr_checkbutton(self.limits_frame, 'right.limits_auto',
                             variable=self.lim_auto_var,
                             command=self._apply_limits).grid(
            row=0, column=0, rowspan=2, padx=5, sticky=tk.W)
        limits_conf = [
            ('right.limits_xmin', 'lim_xmin', 0, 1),
            ('right.limits_xmax', 'lim_xmax', 0, 3),
            ('right.limits_ymin', 'lim_ymin', 1, 1),
            ('right.limits_ymax', 'lim_ymax', 1, 3),
        ]
        for key, var_name, row, col in limits_conf:
            self._tr_label(self.limits_frame, key).grid(
                row=row, column=col, sticky=tk.E, padx=2)
            v = tk.StringVar(value="")
            setattr(self, var_name, v)
            ttk.Entry(self.limits_frame, textvariable=v, width=8).grid(
                row=row, column=col + 1, padx=2, pady=2)
        self._tr_button_icon(self.limits_frame, 'right.apply', 'apply',
                             self._apply_limits).grid(
            row=0, column=5, rowspan=2, padx=10)

        # ---------- Правая панель: анимации ----------
        self.anim_labelframe = self._tr_labelframe(
            right_frame, 'right.anim_engine', padding=5)
        self.anim_labelframe.pack(fill=tk.X, pady=(0, 5))
        ar = ttk.Frame(self.anim_labelframe)
        ar.pack(fill=tk.X, pady=2)
        self._tr_label(ar, 'right.anim_type').pack(side=tk.LEFT, padx=(0, 5))
        self.anim_combo = ttk.Combobox(
            ar, textvariable=self.anim_type_var,
            values=[tr.anim_name(a) for a in INTERNAL_ANIM_TYPES],
            state="readonly", width=22)
        self.anim_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.anim_combo.bind("<<ComboboxSelected>>",
                             self._on_anim_type_change)
        self.anim_speed_var = tk.IntVar(value=30)
        self._tr_label(ar, 'right.anim_frame_ms').pack(
            side=tk.LEFT, padx=(10, 2))
        ttk.Spinbox(ar, from_=10, to=500, increment=10,
                    textvariable=self.anim_speed_var, width=5).pack(
            side=tk.LEFT)
        self.frame_custom_anim = ttk.Frame(self.anim_labelframe)
        ttk.Label(self.frame_custom_anim,
                  text="y(x,t)/z(x,y,t):").pack(side=tk.LEFT)
        self.entry_custom_anim = ttk.Entry(self.frame_custom_anim, width=22)
        self.entry_custom_anim.pack(side=tk.LEFT, padx=5)
        self.entry_custom_anim.insert(0, "sin(x + t) * cos(t/2)")
        ttk.Button(self.frame_custom_anim, text="?", width=3,
                   command=self._show_formula_help).pack(side=tk.LEFT)
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
            self._tr_button_icon(baf, key, icon, cmd).pack(
                side=tk.LEFT, padx=2)
        self.anim_progress = ttk.Progressbar(
            self.anim_labelframe, maximum=self.anim_frames_total,
            mode='determinate')
        self.anim_progress.pack(fill=tk.X, padx=2, pady=(3, 0))

        # ---------- Правая панель: холст ----------
        self.plot_notebook = ttk.Notebook(right_frame)
        self.plot_notebook.pack(fill=tk.BOTH, expand=True)
        self.plot_notebook.bind('<<NotebookTabChanged>>',
                                self._on_plot_tab_changed)
        self._build_documents_bar(right_frame)
        self.plot_frame = None

        # ---------- Статус-бар ----------
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

    # ========================================================================
    # ПОЛЯ ВВОДА
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
        entry.bind("<Control-v>",
                   lambda e: self._paste_from_clipboard(e, entry))
        entry.bind("<KeyRelease>", self._on_data_change)
        self._tr_button(frame, 'create.table_btn',
                        lambda: self._open_table_editor(axis),
                        width=8).pack(side=tk.RIGHT, padx=(5, 0))
        return entry

    # ========================================================================
    # ПАНЕЛИ (показать/скрыть правые блоки)
    # ========================================================================
    def _toggle_ui_panels(self):
        anchor = getattr(self, 'plot_notebook', None) or self.plot_frame
        if anchor is None:
            return

        if self.show_anim_var.get():
            self.anim_labelframe.pack(fill=tk.X, pady=(0, 5),
                                      before=anchor)
        else:
            self.anim_labelframe.pack_forget()

        if self.show_limits_var.get():
            target = (self.anim_labelframe
                      if self.show_anim_var.get() else anchor)
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
            self.settings_frame.pack(fill=tk.X, pady=(0, 5),
                                     before=target)
        else:
            self.settings_frame.pack_forget()