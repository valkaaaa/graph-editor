import json
import os
import re
import sys
import datetime

import numpy as np

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from translator import tr
from settings import APP_NAME, APP_VERSION


class TemplatesMixin:

    # ========= Встроенные шаблоны =========
    def _apply_template(self, name):
        self._snapshot(tr.t('hist.template_applied', name=name))
        self._clear_all_silent(keep_undo=True)
        if name == "empty":
            return
        if name == "sine":
            x = np.linspace(0, 2 * np.pi, 200)
            self._quick_add('Линия', x.tolist(), np.sin(x).tolist(),
                            label="sin(x)")
            self.plot_title_var.set(tr.t('menu.templates.sine'))
        elif name == "damped":
            x = np.linspace(0, 4 * np.pi, 300)
            y = np.exp(-x / 5) * np.sin(x)
            self._quick_add('Линия', x.tolist(), y.tolist(), label="Damped")
            self.plot_title_var.set(tr.t('menu.templates.damped'))
        elif name == "distribution":
            np.random.seed(42)
            groups = [np.random.normal(0, 1, 200).tolist(),
                      np.random.normal(2, 1.2, 200).tolist(),
                      np.random.normal(-1, 0.8, 200).tolist()]
            self._quick_add('Violin', [0, 1, 2], groups[0],
                            label="Distributions", box_data=groups,
                            pie_labels=["A", "B", "C"])
            self.plot_title_var.set(tr.t('menu.templates.distribution'))
        elif name == "spiral3d":
            t = np.linspace(0, 6 * np.pi, 300)
            x = np.cos(t); y = np.sin(t); z = t
            self._quick_add('3D Линия', x.tolist(), y.tolist(),
                            z=z.tolist(), label="Spiral")
            self.plot_title_var.set(tr.t('menu.templates.spiral3d'))
        elif name == "trig":
            x = np.linspace(-2 * np.pi, 2 * np.pi, 400)
            funcs = [
                ('sin(x)', np.sin(x), 'blue', '-'),
                ('cos(x)', np.cos(x), 'red', '--'),
                ('tan(x)', np.tan(x), 'green', ':'),
                ('sin(x)·cos(2x)', np.sin(x) * np.cos(2 * x), 'purple', '-.'),
            ]
            for lbl, y_vals, col, ls in funcs:
                self._quick_add('Линия', x.tolist(), y_vals.tolist(),
                                label=lbl, color=col, ls=ls)
            self.plot_title_var.set(tr.t('menu.templates.trig'))
            self.plot_xlabel_var.set("X")
            self.plot_ylabel_var.set("Y")
        elif name == "distributions":
            x = np.linspace(-5, 10, 500)

            def normal_pdf(xx, mu, sigma):
                return (np.exp(-0.5 * ((xx - mu) / sigma) ** 2)
                        / (sigma * np.sqrt(2 * np.pi)))

            def exp_pdf(xx, lam):
                return lam * np.exp(-lam * xx) * (xx >= 0)

            dists = [
                ('Нормальное μ=0, σ=1', normal_pdf(x, 0, 1), 'blue'),
                ('Нормальное μ=3, σ=1.5', normal_pdf(x, 3, 1.5), 'red'),
                ('Экспоненциальное λ=1', exp_pdf(x, 1), 'green'),
            ]
            for lbl, y_vals, col in dists:
                self._quick_add('Линия', x.tolist(), y_vals.tolist(),
                                label=lbl, color=col, lw=2)
            self.plot_title_var.set(tr.t('menu.templates.distributions'))
            self.plot_xlabel_var.set("x")
            self.plot_ylabel_var.set("Плотность")
        elif name == "dashboard":
            np.random.seed(1)
            x = np.linspace(0, 2 * np.pi, 200)
            self._quick_add('Линия', x.tolist(), np.sin(x).tolist(),
                            label="sin(x)", color='blue', subplot_index=0)
            x2 = np.random.rand(50) * 10
            y2 = 2 * x2 + np.random.normal(0, 1.5, 50)
            self._quick_add('Точечная', x2.tolist(), y2.tolist(),
                            label="Scatter", color='red', ms=8,
                            subplot_index=1)
            data = np.random.normal(0, 1, 500)
            self._quick_add('Гистограмма', data.tolist(), [],
                            label="Histogram", color='green',
                            subplot_index=2)
            self._quick_add('Круговая', [0, 1, 2, 3], [30, 25, 30, 15],
                            label="Pie", color='orange',
                            pie_labels=['A', 'B', 'C', 'D'],
                            pie_colors=['#e74c3c', '#3498db',
                                        '#2ecc71', '#f39c12'],
                            subplot_index=3)
            self.plot_title_var.set(tr.t('menu.templates.dashboard'))
        elif name == "fitting":
            np.random.seed(7)
            x = np.linspace(0, 10, 30)
            y_true = 2 * np.exp(-x / 3) + 0.5
            y_noisy = y_true + np.random.normal(0, 0.05, len(x))
            self._quick_add('Точечная', x.tolist(), y_noisy.tolist(),
                            label="Данные", color='black', ms=8)
            colors_fit = ['red', 'green', 'blue', 'orange']
            for i, deg in enumerate([1, 2, 3, 5]):
                coeffs = np.polyfit(x, y_noisy, deg)
                y_fit = np.polyval(coeffs, x)
                self._quick_add('Линия', x.tolist(), y_fit.tolist(),
                                label=f"Полином {deg}°",
                                color=colors_fit[i], ls='--', lw=1.5)
            self.plot_title_var.set(tr.t('menu.templates.fitting'))
        elif name == "showcase":
            np.random.seed(3)
            x1 = np.linspace(0, 10, 50)
            self._quick_add('Линия', x1.tolist(),
                            (np.sin(x1) * 2 + 5).tolist(),
                            label="Линия", color='blue')
            x2 = np.linspace(0, 10, 20)
            self._quick_add('Точечная', x2.tolist(),
                            (np.cos(x2) * 2 + 3).tolist(),
                            label="Точки", color='red', ms=8)
            x3 = np.linspace(0, 10, 30)
            self._quick_add('Столбчатая', x3.tolist(),
                            (np.random.rand(30) + 0.5).tolist(),
                            label="Столбцы", color='green')
            self.plot_title_var.set(tr.t('menu.templates.showcase'))
        elif name == "fractal":
            def sierpinski(order=6):
                points = [(0.5, 1.0), (0.0, 0.0), (1.0, 0.0)]
                for _ in range(order):
                    new = []
                    for i, p in enumerate(points):
                        for q in points[i + 1:]:
                            new.append(((p[0] + q[0]) / 2,
                                        (p[1] + q[1]) / 2))
                    points.extend(new)
                return list(set(points))

            pts = sierpinski(6)
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self._quick_add('Точечная', xs, ys,
                            label="Серпинский", color='purple', ms=6)
            self.plot_title_var.set(tr.t('menu.templates.fractal'))
            self.plot_xlabel_var.set("")
            self.plot_ylabel_var.set("")
        self._apply_canvas_settings()
        self._update_listbox()
        self._redraw()

    def _quick_add(self, t, x, y, z=None, label="", **kw):
        self._ensure_correct_axes_dimension("3D" in t)
        self.line_counter += 1
        d = self._default_data(t, x, y, z or [], label=label, **kw)
        d['artist'] = self._create_artist(d)
        self.graphs_data.append(d)

    # ========= Пользовательские шаблоны =========
    def _templates_dir(self):
        d = os.path.expanduser("~/.grapheditor_templates")
        os.makedirs(d, exist_ok=True)
        return d

    def _list_user_templates(self):
        d = self._templates_dir()
        try:
            files = sorted(f for f in os.listdir(d)
                           if f.endswith('.graphxtpl'))
        except Exception:
            return []
        return [(f[:-len('.graphxtpl')], os.path.join(d, f)) for f in files]

    def _save_as_template(self):
        name = simpledialog.askstring(
            tr.t('menu.templates.save_current'),
            tr.t('msg.template_name'), parent=self.root)
        if not name:
            return
        safe = re.sub(r'[\\/:*?"<>|]', '_', name).strip() or "template"
        path = os.path.join(self._templates_dir(), f"{safe}.graphxtpl")
        data = [{k: v for k, v in d.items() if k != 'artist'}
                for d in self.graphs_data]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'app': APP_NAME,
                    'version': APP_VERSION,
                    'format': 'graphxtpl',
                    'name': name,
                    'title': self.plot_title_var.get(),
                    'xlabel': self.plot_xlabel_var.get(),
                    'ylabel': self.plot_ylabel_var.get(),
                    'graphs': data,
                    'folders': self.folders,
                    'subplot_grid': [self.subplot_rows, self.subplot_cols],
                }, f, ensure_ascii=False, indent=2,
                    default=lambda o: o.tolist()
                    if hasattr(o, 'tolist') else o)
            self._show_history(tr.t('hist.template_saved', name=name))
            self._build_menu()
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _load_template_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tpl = json.load(f)
            name = tpl.get('name', os.path.basename(path))
            self._snapshot(tr.t('hist.template_loaded', name=name))
            self._clear_all_silent(keep_undo=True)
            grid = tpl.get('subplot_grid', [1, 1])
            if isinstance(grid, (list, tuple)) and len(grid) == 2:
                self.subplot_rows, self.subplot_cols = grid
                self.subplot_grid_var.set(f"{grid[0]}x{grid[1]}")
                self.subplot_index_spin.configure(
                    to=grid[0] * grid[1] - 1)
                self._rebuild_subplots()
            self.plot_title_var.set(tpl.get('title', 'График'))
            self.plot_xlabel_var.set(tpl.get('xlabel', 'X'))
            self.plot_ylabel_var.set(tpl.get('ylabel', 'Y'))
            self.folders = tpl.get('folders', [''])
            self.hidden_folders = set()
            for d in tpl.get('graphs', []):
                for k, v in [('folder', ''), ('box_data', []),
                             ('heatmap_data', []),
                             ('smooth', False), ('fill', False),
                             ('glow', False), ('notes', ''),
                             ('treemap_parents', []),
                             ('subplot_index', 0),
                             ('unit_x', '—'), ('unit_y', '—'),
                             ('unit_z', '—')]:
                    d.setdefault(k, v)
                if d['folder'] and d['folder'] not in self.folders:
                    self.folders.append(d['folder'])
                self._ensure_correct_axes_dimension("3D" in d['type'])
                if d['subplot_index'] >= len(self.axes):
                    d['subplot_index'] = 0
                d['artist'] = self._create_artist(d)
                self.graphs_data.append(d)
                self.line_counter += 1
            self._apply_canvas_settings()
            self._update_listbox()
            self._redraw()
            self._refresh_stats()
            self._show_history(tr.t('hist.template_loaded', name=name))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _open_templates_folder(self):
        d = self._templates_dir()
        try:
            if os.name == 'nt':
                os.startfile(d)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', d])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', d])
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _export_template_file(self):
        if not self.graphs_data:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.no_data'))
            return
        default_name = re.sub(
            r'[\\/:*?"<>|]', '_',
            self.entry_label.get() or self.plot_title_var.get() or "template"
        ).strip() or "template"
        path = filedialog.asksaveasfilename(
            defaultextension=".graphxtpl",
            filetypes=[("GraphX template", "*.graphxtpl"),
                       ("JSON", "*.json")],
            initialfile=default_name)
        if not path:
            return
        data = [{k: v for k, v in d.items() if k != 'artist'}
                for d in self.graphs_data]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({
                    'app': APP_NAME,
                    'version': APP_VERSION,
                    'format': 'graphxtpl',
                    'created': datetime.datetime.now().isoformat(),
                    'name': os.path.splitext(os.path.basename(path))[0],
                    'title': self.plot_title_var.get(),
                    'xlabel': self.plot_xlabel_var.get(),
                    'ylabel': self.plot_ylabel_var.get(),
                    'graphs': data,
                    'folders': self.folders,
                    'subplot_grid': [self.subplot_rows, self.subplot_cols],
                }, f, ensure_ascii=False, indent=2,
                    default=lambda o: o.tolist()
                    if hasattr(o, 'tolist') else o)
            self._show_history(tr.t('hist.template_exported',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _import_template_file(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("GraphX template", "*.graphxtpl"),
                           ("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                tpl = json.load(f)
            if tpl.get('format') not in ('graphxtpl', None):
                if not messagebox.askyesno(
                        tr.t('msg.confirm'),
                        tr.t('msg.template_bad_format') + "\nПродолжить?"):
                    return
            name = tpl.get('name') or os.path.splitext(
                os.path.basename(path))[0]
            self._snapshot(tr.t('hist.template_imported', name=name))
            self._clear_all_silent(keep_undo=True)
            grid = tpl.get('subplot_grid', [1, 1])
            if isinstance(grid, (list, tuple)) and len(grid) == 2:
                self.subplot_rows, self.subplot_cols = grid
                self.subplot_grid_var.set(f"{grid[0]}x{grid[1]}")
                self.subplot_index_spin.configure(
                    to=grid[0] * grid[1] - 1)
                self._rebuild_subplots()
            self.plot_title_var.set(tpl.get('title', 'График'))
            self.plot_xlabel_var.set(tpl.get('xlabel', 'X'))
            self.plot_ylabel_var.set(tpl.get('ylabel', 'Y'))
            self.folders = tpl.get('folders', [''])
            self.hidden_folders = set()
            for d in tpl.get('graphs', []):
                for k, v in [('folder', ''), ('box_data', []),
                             ('heatmap_data', []),
                             ('smooth', False), ('fill', False),
                             ('glow', False), ('notes', ''),
                             ('treemap_parents', []),
                             ('subplot_index', 0),
                             ('unit_x', '—'), ('unit_y', '—'),
                             ('unit_z', '—')]:
                    d.setdefault(k, v)
                if d['folder'] and d['folder'] not in self.folders:
                    self.folders.append(d['folder'])
                self._ensure_correct_axes_dimension("3D" in d['type'])
                if d['subplot_index'] >= len(self.axes):
                    d['subplot_index'] = 0
                d['artist'] = self._create_artist(d)
                self.graphs_data.append(d)
                self.line_counter += 1
            self._apply_canvas_settings()
            self._update_listbox()
            self._redraw()
            self._refresh_stats()
            self._show_history(tr.t('hist.template_imported', name=name))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))
