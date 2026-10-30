"""Базовые утилиты и инфраструктура для построения графиков.

Содержит:
  - создание холста (fig, canvas, toolbar, события)
  - разбор данных, проекции (2d/polar/3d)
  - subplots и переключение между ними
  - управление artist-ами (удаление, видимость)
  - _default_data, _smooth, _safe_eval
  - сетка/легенда/оси/пределы/цвет
"""
import re

import tkinter as tk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from tkinter import messagebox, colorchooser
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from translator import tr


class BasePlotsMixin:

    # ========================================================================
    # ХОЛСТ
    # ========================================================================
    def _setup_plot(self, parent=None):
        parent = parent if parent is not None else self.plot_frame
        self.fig = plt.figure(figsize=(8, 5))
        self.axes = []
        n = self.subplot_rows * self.subplot_cols
        for i in range(n):
            ax = self.fig.add_subplot(self.subplot_rows,
                                      self.subplot_cols, i + 1)
            self.axes.append(ax)
        self.ax = self.axes[0]
        self._style_axes()
        self._init_tooltip()
        self._init_crosshair()
        self._apply_grid_to_axes(self.axes)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Привязка событий ---
        self.canvas.mpl_connect('motion_notify_event', self._update_status)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion_tooltip)
        self.canvas.mpl_connect('motion_notify_event',
                                self._on_motion_tooltip_3d)
        self.canvas.mpl_connect('motion_notify_event',
                                self._on_motion_crosshair)
        self.canvas.mpl_connect('axes_leave_event', self._hide_crosshair)
        self.canvas.mpl_connect('button_press_event', self._on_press_drag)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion_drag)
        self.canvas.mpl_connect('button_release_event', self._on_release_drag)

        # --- Inline-редактор данных ---
        self.canvas.mpl_connect('button_press_event', self._on_inline_edit_press)
        # --- Инструмент "Линейка" ---
        self.canvas.mpl_connect('button_press_event', self._on_press_measure)

    def _style_axes(self):
        for ax in self.axes:
            try:
                ax.set_title(self.plot_title_var.get())
            except Exception:
                pass
            if self.show_axes_var.get():
                try:
                    ax.set_xlabel(self.plot_xlabel_var.get())
                    ax.set_ylabel(self.plot_ylabel_var.get())
                except Exception:
                    pass
                if hasattr(ax, 'get_zlim'):
                    ax.set_zlabel("Z")

    def _apply_grid_to_axes(self, axes, state=None):
        if state is None:
            state = self.show_grid_var.get()
        for ax in axes or []:
            try:
                ax.xaxis.grid(state, linestyle='--', alpha=0.6)
                ax.yaxis.grid(state, linestyle='--', alpha=0.6)
            except Exception:
                pass

    def _parse_data(self, text):
        if not text or not text.strip():
            return []
        try:
            parts = re.split(r'[,;\s]+', text.strip())
            result = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                try:
                    result.append(float(p))
                except ValueError:
                    result.append(float(p.replace(',', '.')))
            return result
        except ValueError:
            return None

    # ========================================================================
    # ПРОЕКЦИИ
    # ========================================================================
    def _projection_for_type(self, t):
        # Plugin-типы — приоритетнее
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            return self.plugin_registry.chart_types[t].projection

        if t in ("Радиальная", "Полярный scatter",
                 "Полярная теплокарта", "Роза ветров",
                 "Диаграмма Тейлора", "Sunburst", "Radar chart"):
            return 'polar'
        if "3D" in t:
            return '3d'
        return '2d'

    def _ensure_correct_axes_dimension(self, needs_3d):
        self._ensure_projection('3d' if needs_3d else '2d')

    def _ensure_projection(self, projection):
        if not self.axes:
            return
        current = getattr(self.axes[0], 'name', 'rectilinear')
        need_rebuild = (
            (projection == '3d' and current != '3d') or
            (projection == 'polar' and current != 'polar') or
            (projection == '2d' and current != 'rectilinear')
        )
        if not need_rebuild:
            return
        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        self.fig.clear()
        proj_kw = {}
        if projection == '3d':
            proj_kw['projection'] = '3d'
        elif projection == 'polar':
            proj_kw['projection'] = 'polar'
        self.axes = []
        n = self.subplot_rows * self.subplot_cols
        for i in range(n):
            ax = self.fig.add_subplot(self.subplot_rows, self.subplot_cols,
                                      i + 1, **proj_kw)
            self.axes.append(ax)
        self.ax = self.axes[0]
        self._style_axes()
        self._init_tooltip()
        self._init_crosshair()
        self._apply_grid_to_axes(self.axes)

        if projection == '2d':
            self.graphs_data = [
                d for d in self.graphs_data
                if "3D" not in d['type'] and d['type'] not in
                ("Радиальная", "Полярный scatter",
                 "Полярная теплокарта", "Роза ветров",
                 "Диаграмма Тейлора", "Sunburst", "Radar chart")
            ]
        elif projection == '3d':
            self.graphs_data = [d for d in self.graphs_data
                                if "3D" in d['type']]

        for d in self.graphs_data:
            if d.get('subplot_index', 0) >= len(self.axes):
                d['subplot_index'] = 0
            d['artist'] = self._create_artist(d)
        self._update_listbox()
        self.canvas.draw()

    # ========================================================================
    # УПРАВЛЕНИЕ ARTIST
    # ========================================================================
    def _remove_artist(self, artist):
        if artist is None:
            return
        if isinstance(artist, (list, tuple)):
            for a in artist:
                self._remove_artist(a)
            return
        if isinstance(artist, dict):
            for a in artist.values():
                self._remove_artist(a)
            return
        if hasattr(artist, 'remove'):
            try:
                artist.remove()
            except Exception:
                pass

    def _destroy_object(self, data):
        if not isinstance(data, dict):
            self._remove_artist(data)
            return

        self._remove_artist(data.get('artist'))

        for extra in data.get('_extra_artists', []) or []:
            self._remove_artist(extra)
        data['_extra_artists'] = []

        cleanup = data.get('_cleanup')
        if callable(cleanup):
            try:
                cleanup()
            except Exception:
                pass
        data['_cleanup'] = None

    def _set_artist_visible(self, artist, visible):
        if artist is None:
            return
        if isinstance(artist, (list, tuple)):
            for a in artist:
                self._set_artist_visible(a, visible)
            return
        if isinstance(artist, dict):
            for a in artist.values():
                self._set_artist_visible(a, visible)
            return
        try:
            artist.set_visible(visible)
        except Exception:
            pass

    def _toggle_visibility(self, indices=None):
        if indices is None:
            indices = self._get_selected_indices()
        if not indices:
            return
        self._snapshot(tr.t('hist.visibility_toggled', count=len(indices)))
        for idx in indices:
            d = self.graphs_data[idx]
            d['visible'] = not d.get('visible', True)
            self._set_artist_visible(d.get('artist'), d['visible'])
        self._update_listbox()
        self._redraw()

    # ========================================================================
    # SUBPLOTS
    # ========================================================================
    def _on_grid_change(self, event=None):
        text = self.subplot_grid_var.get()
        try:
            r_str, c_str = text.split('x')
            r, c = int(r_str), int(c_str)
        except ValueError:
            return
        self.subplot_rows = r
        self.subplot_cols = c
        self.subplot_index_spin.configure(to=c * r - 1)
        self._rebuild_subplots()

    def _rebuild_subplots(self):
        self._stop_animation()
        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        self.fig.clear()
        needs_3d = any("3D" in d['type'] for d in self.graphs_data)
        needs_polar = any(d['type'] in ("Радиальная", "Полярный scatter",
                                         "Полярная теплокарта",
                                         "Роза ветров",
                                         "Диаграмма Тейлора",
                                         "Sunburst", "Radar chart")
                          for d in self.graphs_data)
        proj_kw = {}
        if needs_3d:
            proj_kw['projection'] = '3d'
        elif needs_polar:
            proj_kw['projection'] = 'polar'
        self.axes = []
        n = self.subplot_rows * self.subplot_cols
        for i in range(n):
            ax = self.fig.add_subplot(self.subplot_rows, self.subplot_cols,
                                      i + 1, **proj_kw)
            self.axes.append(ax)
        self.ax = self.axes[0]
        self._style_axes()
        self._init_tooltip()
        self._init_crosshair()
        self._apply_grid_to_axes(self.axes)
        for d in self.graphs_data:
            if d.get('subplot_index', 0) >= len(self.axes):
                d['subplot_index'] = 0
            d['artist'] = self._create_artist(d)
        self.canvas.draw()

    def _get_axis(self, idx):
        if not self.axes:
            return self.ax
        if 0 <= idx < len(self.axes):
            return self.axes[idx]
        return self.axes[0]

    # ========================================================================
    # DATA MODEL
    # ========================================================================
    def _default_data(self, t, x, y, z=None, label="", color="blue",
                      lw=2.0, ls="-", ms=6.0, marker="o", **kw):
        d = {
            'x': x, 'y': y, 'z': z or [],
            'pie_labels': [], 'pie_colors': [],
            'type': t, 'color': color,
            'label': label or f"Object {self.line_counter}",
            'lw': lw, 'ls': ls, 'ms': ms, 'marker': marker,
            'yerr': [], 'use_y2': False, 'bins': 10,
            'box_data': [], 'heatmap_data': [], 'yerr_matrix': [],
            'folder': '', 'smooth': False, 'fill': False,
            'glow': False, 'notes': '', 'treemap_parents': [],
            'col_labels': [], 'dst_labels': [],
            'subplot_index': 0,
            'unit_x': '—', 'unit_y': '—', 'unit_z': '—',
            'visible': True,
            'artist': None,
            '_extra_artists': [],
            '_cleanup': None,
        }
        d.update(kw)
        return d

    def _smooth(self, y, window):
        y = np.asarray(y, dtype=float)
        if window < 2 or len(y) < window:
            return y
        kernel = np.ones(window) / window
        return np.convolve(y, kernel, mode='same')

    def _safe_eval(self, expr, x_val, t_val, y_val=0, silent=False):
        # Базовые функции numpy
        sd = {
            # --- Базовые математические ---
            "abs": np.abs, "sign": np.sign,
            "floor": np.floor, "ceil": np.ceil, "round": np.round,
            "trunc": np.trunc, "rint": np.rint,
            "min": np.minimum, "max": np.maximum, "clip": np.clip,
            "where": np.where, "power": np.power, "mod": np.mod,

            # --- Тригонометрия ---
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "arcsin": np.arcsin, "arccos": np.arccos,
            "arctan": np.arctan, "arctan2": np.arctan2,
            "hypot": np.hypot,
            # Гиперболические
            "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
            "arcsinh": np.arcsinh, "arccosh": np.arccosh, "arctanh": np.arctanh,
            # Переводы углов
            "deg2rad": np.deg2rad, "rad2deg": np.rad2deg,

            # --- Экспоненты и логарифмы ---
            "exp": np.exp, "exp2": np.exp2, "expm1": np.expm1,
            "log": np.log, "log10": np.log10, "log2": np.log2, "log1p": np.log1p,
            "sqrt": np.sqrt, "cbrt": np.cbrt,

            # --- Работа с массивами (полезно для Генератора) ---
            "cumsum": np.cumsum, "diff": np.diff,
            "average": np.average, "median": np.median, "std": np.std,

            # --- Комплексные числа (для 3D и фракталов) ---
            "real": np.real, "imag": np.imag, "angle": np.angle, "conj": np.conj,

            # --- Константы ---
            "pi": np.pi, "e": np.e, "tau": np.tau, "inf": np.inf, "nan": np.nan,

            # --- Переменные ---
            "x": x_val, "y": y_val, "t": t_val,
        }

        # Добавляем спецфункции из scipy (если установлен)
        try:
            from scipy import special as sp
            sd.update({
                "erf": sp.erf,            # Функция ошибок (интеграл Гаусса)
                "erfc": sp.erfc,          # Дополнительная функция ошибок
                "gamma": sp.gamma,        # Гамма-функция
                "lgamma": sp.gammaln,     # Логарифм гамма-функции
                "jv": sp.jv,              # Функция Бесселя первого рода (jv(n, x))
                "yv": sp.yv,              # Функция Бесселя второго рода
                "heaviside": sp.heaviside,# Функция Хевисайда (ступенька)
                "airy": sp.airy,          # Функция Эйри
            })
        except ImportError:
            pass  # Если scipy нет, просто пропускаем

        try:
            return eval(expr, {"__builtins__": {}}, sd)
        except Exception as e:
            if not silent and not self.live_preview_var.get():
                messagebox.showerror(tr.t('msg.formula_error'), str(e))
            return None

    # ========================================================================
    # СЕТКА / ЛЕГЕНДА / ОСИ
    # ========================================================================
    def _update_grid(self):
        state = self.show_grid_var.get()
        docs = getattr(self, 'documents', None)
        if not docs:
            self._apply_grid_to_axes(self.axes, state)
            try:
                self.canvas.draw_idle()
            except Exception:
                pass
            return
        for doc in docs:
            self._apply_grid_to_axes(getattr(doc, 'axes', []), state)
            cv = getattr(doc, 'canvas', None)
            if cv is not None:
                try:
                    cv.draw_idle()
                except Exception:
                    pass

    def _update_legend(self):
        for i, ax in enumerate(self.axes):
            try:
                handles, labels = ax.get_legend_handles_labels()
                sec = self.axes_secondary.get(i)
                if sec:
                    h2, l2 = sec.get_legend_handles_labels()
                    handles.extend(h2)
                    labels.extend(l2)
                if self.show_legend_var.get() and handles:
                    ax.legend(handles, labels)
                elif ax.legend_:
                    ax.legend_.remove()
            except Exception:
                pass
        self.canvas.draw_idle()

    def _update_axes(self):
        for idx, ax in enumerate(self.axes):
            if not self.show_axes_var.get():
                ax.set_xlabel("")
                ax.set_ylabel("")
                if hasattr(ax, 'get_zlim'):
                    ax.set_zlabel("")
                continue
            xlabel = self.plot_xlabel_var.get()
            ylabel = self.plot_ylabel_var.get()
            for d in self.graphs_data:
                if d.get('subplot_index', 0) != idx:
                    continue
                ux = d.get('unit_x', '—')
                uy = d.get('unit_y', '—')
                if ux and ux != '—' and xlabel and '[' not in xlabel:
                    xlabel = f"{xlabel}, {ux}"
                if uy and uy != '—' and ylabel and '[' not in ylabel:
                    ylabel = f"{ylabel}, {uy}"
                break
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            if hasattr(ax, 'get_zlim'):
                ax.set_zlabel("Z")
            sec = self.axes_secondary.get(idx)
            if sec:
                sec.set_ylabel(tr.t('right.second_y_axis'), color='red')
        self.canvas.draw_idle()

    def _apply_canvas_settings(self):
        for ax in self.axes:
            try:
                ax.set_title(self.plot_title_var.get())
            except Exception:
                pass
        self._update_axes()
        self.canvas.draw_idle()

    def _apply_limits(self):
        if not self.axes:
            return
        if self.lim_auto_var.get():
            for ax in self.axes:
                try:
                    ax.relim()
                    ax.autoscale_view()
                except Exception:
                    pass
        else:
            try:
                xmin = self.lim_xmin.get()
                xmax = self.lim_xmax.get()
                ymin = self.lim_ymin.get()
                ymax = self.lim_ymax.get()
                for ax in self.axes:
                    try:
                        ax.set_xlim(
                            float(xmin.replace(',', '.'))
                            if xmin else None,
                            float(xmax.replace(',', '.'))
                            if xmax else None)
                        ax.set_ylim(
                            float(ymin.replace(',', '.'))
                            if ymin else None,
                            float(ymax.replace(',', '.'))
                            if ymax else None)
                    except Exception:
                        pass
            except ValueError:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_number'))
                return
        self.canvas.draw_idle()

    def _pick_color(self):
        c = colorchooser.askcolor(title=tr.t('msg.choose_color'),
                                  initialcolor=self.color_var.get())
        if c[1]:
            self.color_var.set(c[1])

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

        # --- MATHTEXT ---
        mpl.rcParams['text.usetex'] = s.get('use_latex', False)
        mpl.rcParams['mathtext.default'] = 'regular'

        if hasattr(self, 'canvas'):
            self._redraw_all()