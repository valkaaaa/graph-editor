import tkinter as tk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import json, csv, re, os, zipfile, tempfile, sys, datetime

from tkinter import (ttk, messagebox, colorchooser,
                     filedialog, Menu, simpledialog)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from translator import tr, INTERNAL_TYPES, INTERNAL_ANIM_TYPES
from settings import (FONTS, UNIT_TO_M, TOOLTIPS, attach_tooltip,
                      APP_NAME, APP_VERSION, GRAPHX_MANIFEST)


class PlotsMixin:

    # ========================================================================
    # ХОЛСТ
    # ========================================================================
    def _setup_plot(self, parent=None):                       # [NEW] parent
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
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, parent)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
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
        if t in ("Радиальная", "Полярный scatter"):
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
        if projection == '2d':
            self.graphs_data = [
                d for d in self.graphs_data
                if "3D" not in d['type'] and d['type'] not in
                ("Радиальная", "Полярный scatter")
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

    def _remove_artist(self, artist):
        if artist is None:
            return
        if isinstance(artist, dict):
            for a in artist.values():
                self._remove_artist(a)
        elif isinstance(artist, (list, tuple)):
            for a in artist:
                self._remove_artist(a)
        else:
            try:
                artist.remove()
            except Exception:
                pass

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
        needs_polar = any(d['type'] in ("Радиальная", "Полярный scatter")
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
    # СОЗДАНИЕ ARTIST
    # ========================================================================
    def _create_artist(self, data):
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        lw = data.get('lw', 2.0)
        ls = data.get('ls', '-')
        ms = data.get('ms', 6.0)
        raw_marker = data.get('marker', 'o')
        marker = None if raw_marker == "None" else raw_marker
        yerr = data.get('yerr', []) or None
        fill = data.get('fill', False)
        glow = data.get('glow', False)

        if self.smooth_var.get() and t in ("Линия", "Точечная", "Столбчатая"):
            try:
                y = self._smooth(y, self.settings['smooth_window']).tolist()
            except Exception:
                pass

        subplot_idx = data.get('subplot_index', 0)
        base_ax = self._get_axis(subplot_idx)

        target_ax = base_ax
        if (data.get('use_y2')
                and not hasattr(base_ax, 'get_zlim')
                and getattr(base_ax, 'name', '') != 'polar'):
            if subplot_idx not in self.axes_secondary:
                self.axes_secondary[subplot_idx] = base_ax.twinx()
                if self.dark_mode_var.get():
                    self.axes_secondary[subplot_idx].set_facecolor('#2b2b2b')
                self.axes_secondary[subplot_idx].set_ylabel(
                    tr.t('right.second_y_axis'), color='red')
            target_ax = self.axes_secondary[subplot_idx]

        # ----- 2D базовые -----
        if t == "Линия":
            artist, = target_ax.plot(x, y, label=lbl, color=c, lw=lw,
                                     ls=ls, marker=marker, markersize=ms)
            if fill:
                try:
                    target_ax.fill_between(x, y, alpha=0.3, color=c)
                except Exception:
                    pass
            if yerr:
                target_ax.errorbar(x, y, yerr=yerr, fmt='none',
                                   ecolor=c, capsize=3)
        elif t == "Столбчатая":
            artist = target_ax.bar(x, y, label=lbl, color=c,
                                   yerr=yerr, capsize=3)
        elif t == "Гистограмма":
            edge = 'white' if self.dark_mode_var.get() else 'black'
            _, _, patches = target_ax.hist(
                x, bins=data.get('bins', 10), color=c, label=lbl,
                alpha=0.75, edgecolor=edge)
            artist = list(patches)
        elif t == "Точечная":
            if glow:
                target_ax.scatter(x, y, s=ms ** 2 * 6, color=c,
                                  alpha=0.10, zorder=1)
                target_ax.scatter(x, y, s=ms ** 2 * 3, color=c,
                                  alpha=0.25, zorder=2)
            artist = target_ax.scatter(x, y, label=lbl, color=c,
                                       s=ms ** 2, marker=marker, zorder=3)
            if yerr:
                target_ax.errorbar(x, y, yerr=yerr, fmt='none',
                                   ecolor=c, capsize=3)
        elif t == "Круговая":
            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(y):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(y))]
            artist = list(base_ax.pie(y, labels=data['pie_labels'] or None,
                                      colors=pc, autopct='%1.1f%%'))

        # ----- 2D продвинутые -----
        elif t == "Box plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            labels = data.get('pie_labels', [])
            labels_arg = labels if labels and len(labels) == len(groups) else None
            try:
                bp = base_ax.boxplot(groups, patch_artist=True,
                                     tick_labels=labels_arg)
            except TypeError:
                bp = base_ax.boxplot(groups, patch_artist=True,
                                     labels=labels_arg)
            for b in bp['boxes']:
                b.set_facecolor(c)
            artist = bp
        elif t == "Violin":
            groups = data.get('box_data', [])
            if not groups:
                return None
            vp = base_ax.violinplot(groups, showmedians=True)
            for b in vp['bodies']:
                b.set_facecolor(c)
                b.set_alpha(0.75)
            artist = vp
        elif t in ("Heatmap", "Contour", "Imshow"):
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            row_lens = [len(r) for r in raw if r]
            if not row_lens:
                return None
            if len(set(row_lens)) != 1:
                min_len = min(row_lens)
                raw = [r[:min_len] for r in raw if len(r) >= min_len]
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.size == 0:
                return None
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            if t == "Heatmap":
                artist = base_ax.pcolormesh(Z, cmap='viridis', shading='auto')
                try:
                    base_ax.set_aspect('auto')
                    base_ax.set_xlim(0, Z.shape[1])
                    base_ax.set_ylim(0, Z.shape[0])
                except Exception:
                    pass
            elif t == "Contour":
                if Z.shape[0] < 2 or Z.shape[1] < 2:
                    txt = base_ax.text(
                        0.5, 0.5, tr.t('msg.contour_needs_matrix'),
                        ha='center', va='center',
                        transform=base_ax.transAxes, fontsize=10,
                        color='gray',
                        bbox=dict(boxstyle='round', fc='#f8f8f8',
                                  ec='gray'))
                    artist = txt
                else:
                    try:
                        artist = base_ax.contour(Z, cmap='viridis')
                        base_ax.set_aspect('auto')
                    except Exception as e:
                        txt = base_ax.text(0.5, 0.5,
                                           f"Contour error: {e}",
                                           ha='center', va='center',
                                           transform=base_ax.transAxes,
                                           fontsize=10, color='red')
                        artist = txt
            else:
                artist = base_ax.imshow(Z, cmap='viridis', aspect='auto')

        # ----- Специальные 2D -----
        elif t == "Полигон":
            if not x or not y:
                return None
            try:
                closed_x = list(x) + [x[0]]
                closed_y = list(y) + [y[0]]
                fill_artist = base_ax.fill(x, y, color=c, alpha=0.4,
                                            label=lbl)
                line_artist, = base_ax.plot(closed_x, closed_y,
                                             color=c, lw=lw)
                artist = list(fill_artist) + [line_artist]
            except Exception:
                return None

        # ------------------- [NEW] Водопад -------------------
        elif t == "Водопад":
            vals = np.array(y, dtype=float)
            n = len(vals)
            if n == 0:
                return None
            cumulative = np.cumsum(vals)
            starts = np.concatenate([[0], cumulative[:-1]])
            colors_w = ['#2ecc71' if v >= 0 else '#e74c3c' for v in vals]
            xs = np.arange(n)
            bars = base_ax.bar(xs, vals, bottom=starts,
                               color=colors_w, edgecolor='white',
                               label=lbl)
            for i in range(n - 1):
                y_lvl = cumulative[i]
                base_ax.plot([xs[i] + 0.4, xs[i + 1] - 0.4],
                             [y_lvl, y_lvl],
                             color='#888', lw=1, ls='--')
            base_ax.bar([n], [cumulative[-1]], color='#3498db',
                        edgecolor='white', label='Total')
            labels = data.get('pie_labels') or []
            ticks = list(xs) + [n]
            if labels and len(labels) >= n:
                ticklabels = list(labels[:n]) + ['Total']
            else:
                ticklabels = [str(i) for i in range(n)] + ['Total']
            base_ax.set_xticks(ticks)
            base_ax.set_xticklabels(ticklabels, rotation=30, ha='right')
            artist = bars

        # ------------------- [NEW] Гант -------------------
        elif t == "Гант":
            starts = np.array(x, dtype=float)
            durations = np.array(y, dtype=float)
            n = min(len(starts), len(durations))
            if n == 0:
                return None
            starts, durations = starts[:n], durations[:n]
            labels = list(data.get('pie_labels') or [])
            labels = labels + [f"Task {i+1}"
                               for i in range(len(labels), n)]
            labels = labels[:n]
            colors_g = [cc for cc in data.get('pie_colors', [])
                        if mcolors.is_color_like(cc)]
            if len(colors_g) != n:
                cmap = plt.get_cmap('tab10')
                colors_g = [cmap(i % 10) for i in range(n)]
            ys = np.arange(n)
            bars = base_ax.barh(ys, durations, left=starts,
                                color=colors_g, edgecolor='white',
                                height=0.6, label=lbl)
            base_ax.set_yticks(ys)
            base_ax.set_yticklabels(labels)
            base_ax.invert_yaxis()
            base_ax.grid(True, axis='x', ls='--', alpha=0.5)
            artist = bars

        elif t == "Кольцевая":
            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(y):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(y))]
            artist = list(base_ax.pie(
                y, labels=data['pie_labels'] or None,
                colors=pc, autopct='%1.1f%%',
                wedgeprops=dict(width=0.4, edgecolor='white')))
        elif t == "Вложенная круговая":
            rings = data.get('box_data', [])
            if not rings:
                return None
            labels = data.get('pie_labels', [])
            all_artists = []
            size = 1.0 / len(rings)
            for i, ring_vals in enumerate(rings):
                radius = 1.0 - i * size
                pc = [cc for cc in data.get('pie_colors', [])
                      if mcolors.is_color_like(cc)]
                if len(pc) != len(ring_vals):
                    cmap = plt.get_cmap('tab10')
                    pc = [cmap(j % 10) for j in range(len(ring_vals))]
                wp = dict(width=size, edgecolor='white')
                if i == 0 and labels and len(labels) == len(ring_vals):
                    w_ = base_ax.pie(ring_vals, radius=radius, colors=pc,
                                     wedgeprops=wp, autopct='%1.1f%%',
                                     pctdistance=radius - size / 2)
                else:
                    w_ = base_ax.pie(ring_vals, radius=radius, colors=pc,
                                     wedgeprops=wp)
                all_artists.append(w_)
            artist = all_artists
        elif t == "Мозаика":
            rows = data.get('box_data', [])
            if len(rows) < 2:
                return None
            if len(set(len(r) for r in rows)) != 1:
                return None
            labels = data.get('pie_labels', [])
            col_sums = [sum(row[col] for row in rows)
                        for col in range(len(rows[0]))]
            total = sum(col_sums)
            if total <= 0:
                return None
            cmap = plt.get_cmap('tab10')
            x_pos = 0.0
            artists = []
            for col in range(len(rows[0])):
                col_total = col_sums[col]
                width = col_total / total
                y_pos = 0.0
                for r_idx, row in enumerate(rows):
                    height = row[col] / col_total if col_total > 0 else 0
                    lbl_use = None
                    if col == 0 and r_idx < len(labels):
                        lbl_use = labels[r_idx]
                    rects = base_ax.bar(x_pos, height, width=width,
                                        bottom=y_pos, align='edge',
                                        color=cmap(r_idx % 10),
                                        edgecolor='white', label=lbl_use)
                    y_pos += height
                    artists.append(rects)
                x_pos += width
            base_ax.set_xlim(0, 1)
            base_ax.set_ylim(0, 1)
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            artist = artists
        elif t == "Радиальная":
            if not x or not y:
                return None
            try:
                theta = np.deg2rad(np.array(x, dtype=float))
                vals = np.array(y, dtype=float)
                width = 2 * np.pi / max(len(theta), 1) * 0.8
                artist = base_ax.bar(theta, vals, width=width, color=c,
                                     label=lbl, alpha=0.85,
                                     edgecolor='white')
            except Exception:
                return None
        elif t == "Полярный scatter":
            if not x or not y:
                return None
            try:
                theta = np.deg2rad(np.array(x, dtype=float))
                r = np.array(y, dtype=float)
                n = min(len(theta), len(r))
                if n == 0:
                    return None
                artist = base_ax.scatter(
                    theta[:n], r[:n], color=c, s=ms ** 2,
                    label=lbl, alpha=0.85,
                    edgecolors='black', linewidths=0.5)
            except Exception:
                return None
        elif t == "Пузырьковая":
            sizes = np.array(data.get('z', []), dtype=float)
            if len(sizes) == 0 or len(x) != len(sizes):
                return None
            try:
                smin, smax = sizes.min(), sizes.max()
                if smax > smin:
                    norm = (sizes - smin) / (smax - smin)
                else:
                    norm = np.zeros_like(sizes)
                areas = 20 + norm * 980
                artist = base_ax.scatter(
                    x, y, s=areas, color=c, alpha=0.55,
                    edgecolors='black', linewidths=0.6,
                    label=lbl, zorder=3)
            except Exception:
                return None
        elif t == "Quiver":
            U = np.array(data.get('z', []), dtype=float)
            V = np.array(data.get('yerr', []), dtype=float)
            if len(U) == 0 or len(U) != len(V):
                return None
            if len(x) != len(U) or len(y) != len(U):
                return None
            try:
                artist = base_ax.quiver(
                    x, y, U, V, angles='xy', scale_units='xy',
                    scale=1, color=c, width=0.005, label=lbl)
            except Exception:
                return None
        elif t == "Столбчатая с накоплением":
            series = data.get('box_data', [])
            if not series:
                series = [y]
            if not x:
                xs = np.arange(len(series[0]))
            else:
                xs = np.array(x, dtype=float)
            width = (xs[1] - xs[0]) * 0.8 if len(xs) > 1 else 0.8
            cmap = plt.get_cmap('tab10')
            bottom = np.zeros(len(xs))
            artists = []
            for i, s in enumerate(series):
                s_arr = np.array(s, dtype=float)
                min_len = min(len(s_arr), len(xs))
                col = c if i == 0 else cmap(i % 10)
                lbl_use = lbl if i == 0 else f"{lbl} #{i + 1}"
                bars = base_ax.bar(xs[:min_len], s_arr[:min_len],
                                   width=width, bottom=bottom[:min_len],
                                   color=col, label=lbl_use,
                                   edgecolor='white')
                artists.append(bars)
                bottom[:min_len] += s_arr[:min_len]
            artist = artists
        elif t in ("Treemap", "Sunburst"):
            txt = base_ax.text(
                0.5, 0.5,
                tr.t('misc.treemap_only_html', type=tr.type_name(t)),
                ha='center', va='center', transform=base_ax.transAxes,
                fontsize=12, color='gray',
                bbox=dict(boxstyle='round', fc='#f0f0f0',
                          ec='gray', alpha=0.7))
            artist = txt

        # ----- 3D -----
        elif t == "3D Линия":
            artist, = base_ax.plot3D(x, y, data['z'], label=lbl, color=c,
                                     lw=lw, ls=ls, marker=marker,
                                     markersize=ms)
            if fill:
                try:
                    zs = data['z']
                    zmin = min(zs) if zs else 0
                    verts = [list(zip(x, y, zs)) +
                             list(zip(x[::-1], y[::-1],
                                      [zmin] * len(x)))]
                    poly = Poly3DCollection(verts, alpha=0.3,
                                            facecolor=c,
                                            edgecolor='none')
                    base_ax.add_collection3d(poly)
                    artist = [artist, poly]
                except Exception:
                    pass
        elif t == "3D Точечная":
            if glow:
                base_ax.scatter3D(x, y, data['z'], color=c,
                                  s=ms ** 2 * 6, alpha=0.10)
                base_ax.scatter3D(x, y, data['z'], color=c,
                                  s=ms ** 2 * 3, alpha=0.25)
            artist = base_ax.scatter3D(x, y, data['z'], label=lbl,
                                       color=c, s=ms ** 2, marker=marker)
        elif t == "3D Столбчатая":
            xs = np.array(x, dtype=float)
            ys = np.array(y, dtype=float)
            zs = np.array(data['z'], dtype=float)
            n = min(len(xs), len(ys), len(zs))
            xs, ys, zs = xs[:n], ys[:n], zs[:n]
            artist = base_ax.bar3d(xs, ys, np.zeros_like(zs),
                                   0.8, 0.8, zs, color=c, alpha=0.85)
        elif t == "3D Гистограмма":
            xs = np.array(x, dtype=float)
            ys = np.array(y, dtype=float) if y else np.array(x, dtype=float)
            n = min(len(xs), len(ys))
            xs, ys = xs[:n], ys[:n]
            hist, xe, ye = np.histogram2d(xs, ys,
                                           bins=data.get('bins', 10))
            xp, yp = np.meshgrid(xe[:-1], ye[:-1])
            xp, yp = xp.ravel(), yp.ravel()
            dx = (xe[1] - xe[0]) if len(xe) > 1 else 1.0
            dy = (ye[1] - ye[0]) if len(ye) > 1 else 1.0
            artist = base_ax.bar3d(xp, yp,
                                    np.zeros_like(hist.ravel()),
                                    dx, dy, hist.ravel(),
                                    color=c, alpha=0.85)
        elif t == "3D Круговая":
            vals = np.array(y, dtype=float)
            if vals.sum() <= 0:
                return None
            fracs = vals / vals.sum()
            cols = data.get('pie_colors', [])
            if not cols or len(cols) != len(vals):
                cmap = plt.get_cmap('tab10')
                cols = [cmap(i % 10) for i in range(len(vals))]
            group = []
            theta0 = 0.0
            for frac, col in zip(fracs, cols):
                dth = 2 * np.pi * frac
                th = np.linspace(theta0, theta0 + dth, 30)
                pts = [(0.0, 0.0)] + [(np.cos(a), np.sin(a)) for a in th]
                top = [(p[0], p[1], 0.15) for p in pts]
                bot = [(p[0], p[1], 0.0) for p in pts]
                pt = Poly3DCollection([top], facecolor=col,
                                      edgecolor='k', alpha=0.9)
                pb = Poly3DCollection([bot], facecolor=col,
                                      edgecolor='k', alpha=0.9)
                sides = [[bot[k], bot[k + 1], top[k + 1], top[k]]
                         for k in range(len(pts) - 1)]
                sides.append([bot[0], bot[-1], top[-1], top[0]])
                ps = Poly3DCollection(sides, facecolor=col,
                                      edgecolor='k', alpha=0.9)
                base_ax.add_collection3d(pt)
                base_ax.add_collection3d(pb)
                base_ax.add_collection3d(ps)
                group.append((pt, pb, ps))
                theta0 += dth
            try:
                base_ax.set_xlim(-1.2, 1.2)
                base_ax.set_ylim(-1.2, 1.2)
                base_ax.set_zlim(0, 0.5)
            except Exception:
                pass
            artist = group
        elif t in ("3D Поверхность", "3D Сетка"):
            Z = np.array(data.get('heatmap_data', []), dtype=float)
            if Z.size == 0:
                zz = np.array(data.get('z', []), dtype=float)
                if zz.size == 0:
                    return None
                side = int(np.ceil(np.sqrt(zz.size)))
                pad = side * side - zz.size
                if pad > 0:
                    zz = np.concatenate([zz, np.zeros(pad)])
                Z = zz.reshape(side, side)
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            m, n = Z.shape
            xg = (np.array(x, dtype=float) if x and len(x) == n
                  else np.arange(n))
            yg = (np.array(y, dtype=float) if y and len(y) == m
                  else np.arange(m))
            X, Y = np.meshgrid(xg, yg)
            try:
                if t == "3D Поверхность":
                    artist = base_ax.plot_surface(
                        X, Y, Z, cmap='viridis',
                        edgecolor='none', alpha=0.9)
                else:
                    artist = base_ax.plot_wireframe(X, Y, Z,
                                                     color=c, lw=lw)
            except Exception:
                return None
        elif t == "3D Полигон":
            zs = data.get('z', [])
            if not x or not y or not zs:
                return None
            try:
                n = min(len(x), len(y), len(zs))
                if n < 3:
                    return None
                pts = list(zip(x[:n], y[:n], zs[:n]))
                poly = Poly3DCollection([pts], facecolor=c, edgecolor='k',
                                        alpha=0.7, linewidths=lw)
                base_ax.add_collection3d(poly)
                verts = base_ax.scatter3D([p[0] for p in pts],
                                          [p[1] for p in pts],
                                          [p[2] for p in pts],
                                          color=c, s=ms ** 2,
                                          edgecolors='k',
                                          depthshade=True, zorder=5)
                artist = [poly, verts]
            except Exception:
                return None
        elif t == "3D Триангуляция":
            zs = data.get('z', [])
            if not x or not y or not zs:
                return None
            try:
                xs = np.array(x, dtype=float)
                ys = np.array(y, dtype=float)
                zz = np.array(zs, dtype=float)
                n = min(len(xs), len(ys), len(zz))
                if n < 3:
                    return None
                xs, ys, zz = xs[:n], ys[:n], zz[:n]
                try:
                    artist = base_ax.plot_trisurf(xs, ys, zz,
                                                   cmap='viridis',
                                                   edgecolor='none',
                                                   alpha=0.9,
                                                   linewidth=0, label=lbl)
                except Exception:
                    artist = base_ax.scatter3D(xs, ys, zz, color=c,
                                                s=ms ** 2, label=lbl)
            except Exception:
                return None
        else:
            artist, = target_ax.plot(x, y, label=lbl, color=c)
        return artist

    # ========================================================================
    # ДОБАВЛЕНИЕ / ОБНОВЛЕНИЕ
    # ========================================================================
    def _add_graph(self):
        t = tr.find_type_by_display(self.type_var.get())
        self._ensure_projection(self._projection_for_type(t))
        box_data = []
        heatmap_data = []
        treemap_parents = []
        x_data, y_data, z_data = [], [], []
        pie_labels, pie_colors, yerr_data = [], [], []

        if t in ("Полярный scatter", "3D Полигон",
                 "3D Триангуляция", "Пузырьковая"):
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
            if t in ("3D Полигон", "3D Триангуляция", "Пузырьковая"):
                z_data = self._parse_data(self.entry_z.get())
                if not z_data or len(z_data) != len(x_data):
                    messagebox.showerror(
                        tr.t('msg.error'),
                        tr.t('msg.need_xyz_lengths',
                             type=tr.type_name(t)))
                    return
            if t == "3D Полигон" and len(x_data) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.polygon_needs_xy'))
                return
        elif t == "Quiver":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            yerr_data = self._parse_data(self.entry_yerr.get())
            if not (x_data and y_data and z_data and yerr_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.quiver_needs_4'))
                return
            if not (len(x_data) == len(y_data) == len(z_data)
                    == len(yerr_data)):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.quiver_needs_4'))
                return
        elif t == "Кольцевая":
            y_data = self._parse_data(self.entry_y.get())
            if y_data is None:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format_y'))
                return
            x_data = list(range(len(y_data)))
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')]
            pie_colors = [c.strip()
                          for c in self.entry_pie_colors.get().split(',')]
            if len(pie_labels) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.pie_labels_count'))
                return
        elif t == "Вложенная круговая":
            box_data = []
            for r in self.entry_y.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    box_data.append(vals)
            if not box_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.nested_needs_rings'))
                return
            y_data = box_data[0]
            x_data = list(range(len(y_data)))
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')]
            pie_colors = [c.strip()
                          for c in self.entry_pie_colors.get().split(',')]
        elif t == "Мозаика":
            box_data = []
            for r in self.entry_y.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    box_data.append(vals)
            if len(box_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.mosaic_needs_rows'))
                return
            if len(set(len(r) for r in box_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.mosaic_uniform'))
                return
            y_data = box_data[0]
            x_data = list(range(len(y_data)))
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')]
        elif t == "Радиальная":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.radial_needs'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
        elif t in ("3D Поверхность", "3D Сетка"):
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = self._parse_data(self.entry_y.get()) or []
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('msg.surface_needs_z', type=tr.type_name(t)))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('msg.surface_uniform', type=tr.type_name(t)))
                return
            m = len(heatmap_data)
            n = len(heatmap_data[0])
            if not x_data or len(x_data) != n:
                x_data = list(range(n))
            if not y_data or len(y_data) != m:
                y_data = list(range(m))
        elif t == "Столбчатая с накоплением":
            x_data = self._parse_data(self.entry_x.get())
            box_data = []
            for s in self.entry_y.get().split(';'):
                vals = self._parse_data(s)
                if vals:
                    box_data.append(vals)
            if not box_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.stacked_needs_series'))
                return
            y_data = box_data[0]
            if not x_data:
                x_data = list(range(len(y_data)))
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
        elif t == "Полигон":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.polygon_needs_xy'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return

        # ------------------- [NEW] Водопад -------------------
        elif t == "Водопад":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format_y'))
                return
            if not x_data:
                x_data = list(range(len(y_data)))
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]

        # ------------------- [NEW] Гант -------------------
        elif t == "Гант":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.gantt_needs'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            pie_colors = [c.strip()
                          for c in self.entry_pie_colors.get().split(',')
                          if c.strip()]

        elif t in ("Box plot", "Violin"):
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            if not box_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.box_groups'))
                return
            y_data = box_data[0]
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    pie_labels = raw_labels
        elif t in ("Heatmap", "Contour", "Imshow"):
            for row_text in self.entry_z.get().split(';'):
                vals = self._parse_data(row_text)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.heatmap_matrix'))
                return
        elif t in ("Treemap", "Sunburst"):
            y_data = self._parse_data(self.entry_y.get())
            if y_data is None:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format_y'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')]
            treemap_parents = [p.strip()
                               for p in
                               self.treemap_parents.get().split(';')]
            while len(treemap_parents) < len(y_data):
                treemap_parents.append('')
        else:
            y_data = self._parse_data(self.entry_y.get())
            if y_data is None:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format_y'))
                return
            if t not in ("Круговая", "Гистограмма"):
                x_data = self._parse_data(self.entry_x.get())
            else:
                x_data = list(range(len(y_data)))
            if "3D" in t:
                z_data = self._parse_data(self.entry_z.get())
            if t == "Круговая":
                pie_labels = [l.strip()
                              for l in self.entry_pie.get().split(',')]
                pie_colors = [c.strip()
                              for c in
                              self.entry_pie_colors.get().split(',')]
            no_yerr = ("Круговая", "3D Линия", "3D Точечная",
                       "3D Столбчатая", "3D Гистограмма",
                       "3D Круговая", "Гистограмма")
            if t not in no_yerr:
                yerr_data = self._parse_data(self.entry_yerr.get())
                if yerr_data is None:
                    yerr_data = []
            if x_data is None:
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.bad_format_x'))
                return
            if "3D" in t and (z_data is None
                              or len(x_data) != len(z_data)):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.problem_z'))
                return
            if t == "Гистограмма":
                if not x_data:
                    messagebox.showerror(tr.t('msg.error'),
                                          tr.t('msg.need_x_data'))
                    return
            elif t != "Круговая" and len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.xy_length'))
                return
            if yerr_data and len(yerr_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.y_yerr_length'))
                return
            if t == "Круговая" and len(pie_labels) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                      tr.t('msg.pie_labels_count'))
                return

        self._snapshot(tr.t('hist.added_graph',
                            name=self.entry_label.get() or t))
        self.line_counter += 1
        d = self._default_data(
            t, x_data, y_data, z_data,
            label=self.entry_label.get() or f"Object {self.line_counter}",
            color=self.color_var.get(),
            lw=self.lw_var.get(), ls=self.ls_var.get(),
            ms=self.ms_var.get(), marker=self.marker_var.get(),
            pie_labels=pie_labels, pie_colors=pie_colors,
            yerr=yerr_data,
            use_y2=self.use_y2_var.get(),
            bins=self.bins_var.get(),
            box_data=box_data, heatmap_data=heatmap_data,
            treemap_parents=treemap_parents,
            fill=self.fill_var.get(), glow=self.glow_var.get(),
            notes=self.entry_notes.get(), smooth=self.smooth_var.get(),
            subplot_index=self.subplot_index_var.get(),
            unit_x=self.unit_x_var.get(),
            unit_y=self.unit_y_var.get(),
            unit_z=self.unit_z_var.get(),
        )
        d['artist'] = self._create_artist(d)
        self.graphs_data.append(d)
        self._update_listbox()
        self._redraw()
        self._refresh_stats()

    def _load_selected_to_form(self, event=None):
        sel = self._get_selected_indices()
        if not sel:
            return
        data = self.graphs_data[sel[0]]
        self.type_var.set(tr.type_name(data['type']))
        self._on_type_change()

        if data['type'] not in ("Круговая", "Гистограмма",
                                 "Heatmap", "Contour", "Imshow",
                                 "Кольцевая", "Вложенная круговая",
                                 "Мозаика", "Полярный scatter",
                                 "3D Полигон", "3D Триангуляция",
                                 "Пузырьковая"):
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
        elif data['type'] == "Гистограмма":
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))

        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, ", ".join(map(str, data['y'])))

        if "3D" in data['type']:
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, ", ".join(map(str, data['z'])))
        if data['type'] == "Круговая":
            self.entry_pie.delete(0, tk.END)
            self.entry_pie.insert(0, ", ".join(data['pie_labels']))
            self.entry_pie_colors.delete(0, tk.END)
            self.entry_pie_colors.insert(
                0, ", ".join(data.get('pie_colors', [])))
        if data['type'] in ("Кольцевая", "Вложенная круговая"):
            self.entry_pie.delete(0, tk.END)
            self.entry_pie.insert(0, ", ".join(data.get('pie_labels', [])))
            self.entry_pie_colors.delete(0, tk.END)
            self.entry_pie_colors.insert(
                0, ", ".join(data.get('pie_colors', [])))
            if data['type'] == "Вложенная круговая":
                self.entry_y.delete(0, tk.END)
                self.entry_y.insert(0, " ; ".join(
                    ", ".join(map(str, r))
                    for r in data.get('box_data', [])))
        if data['type'] == "Мозаика":
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, " ; ".join(
                ", ".join(map(str, r))
                for r in data.get('box_data', [])))
            self.entry_pie.delete(0, tk.END)
            self.entry_pie.insert(0, ", ".join(data.get('pie_labels', [])))

        # ------------------- [NEW] Водопад / Гант -------------------
        if data['type'] in ("Водопад", "Гант"):
            self.entry_pie.delete(0, tk.END)
            self.entry_pie.insert(0, ", ".join(data.get('pie_labels', [])))
            if data['type'] == "Гант":
                self.entry_pie_colors.delete(0, tk.END)
                self.entry_pie_colors.insert(
                    0, ", ".join(data.get('pie_colors', [])))

        if data['type'] == "Quiver":
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, data['y'])))
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, ", ".join(map(str, data.get('z', []))))
            self.entry_yerr.delete(0, tk.END)
            self.entry_yerr.insert(
                0, ", ".join(map(str, data.get('yerr', []))))
        if data['type'] == "Радиальная":
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, data['y'])))
        if data['type'] == "Полярный scatter":
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, data['y'])))
        if data['type'] in ("3D Полигон", "3D Триангуляция",
                            "Пузырьковая"):
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, data['y'])))
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, ", ".join(map(str, data.get('z', []))))
        if data['type'] in ("3D Поверхность", "3D Сетка"):
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, data['y'])))
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, " ; ".join(
                ", ".join(map(str, r))
                for r in data.get('heatmap_data', [])))
        if data['type'] == "Столбчатая с накоплением":
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, data['x'])))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, " ; ".join(
                ", ".join(map(str, s))
                for s in data.get('box_data', [])))
        if data['type'] in ("Box plot", "Violin"):
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, " ; ".join(
                ", ".join(map(str, g))
                for g in data.get('box_data', [])))
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(
                data.get('pie_labels', []) or []))
        if data['type'] in ("Heatmap", "Contour", "Imshow"):
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, " ; ".join(
                ", ".join(map(str, r))
                for r in data.get('heatmap_data', [])))
        if data['type'] in ("Treemap", "Sunburst"):
            self.entry_pie.delete(0, tk.END)
            self.entry_pie.insert(0, ", ".join(data.get('pie_labels', [])))
            self.treemap_parents.delete(0, tk.END)
            self.treemap_parents.insert(
                0, " ; ".join(data.get('treemap_parents', [])))

        if data['type'] not in ("Quiver",):
            self.entry_yerr.delete(0, tk.END)
            if data.get('yerr'):
                self.entry_yerr.insert(
                    0, ", ".join(map(str, data['yerr'])))
        self.use_y2_var.set(data.get('use_y2', False))
        self.bins_var.set(data.get('bins', 10))
        self.fill_var.set(data.get('fill', False))
        self.glow_var.set(data.get('glow', False))
        self.subplot_index_var.set(data.get('subplot_index', 0))
        self.unit_x_var.set(data.get('unit_x', '—'))
        self.unit_y_var.set(data.get('unit_y', '—'))
        self.unit_z_var.set(data.get('unit_z', '—'))
        self.entry_label.delete(0, tk.END)
        self.entry_label.insert(0, data['label'])
        self.entry_notes.delete(0, tk.END)
        self.entry_notes.insert(0, data.get('notes', ''))
        self.color_var.set(data['color'])
        self.lw_var.set(data.get('lw', 2.0))
        self.ls_var.set(data.get('ls', '-'))
        self.ms_var.set(data.get('ms', 6.0))
        self.marker_var.set(data.get('marker', 'o'))
        self.notebook.select(0)

    def _update_graph(self):
        sel = self._get_selected_indices()
        if not sel:
            if not self.live_preview_var.get():
                messagebox.showwarning(tr.t('msg.warning'),
                                        tr.t('msg.select_object_short'))
            return
        self._stop_animation()
        idx = sel[0]
        data = self.graphs_data[idx]
        self._remove_artist(data['artist'])
        t = tr.find_type_by_display(self.type_var.get())
        self._ensure_projection(self._projection_for_type(t))
        self._snapshot(tr.t('hist.changed_graph', name=data['label']))

        if t in ("Полярный scatter", "3D Полигон",
                 "3D Триангуляция", "Пузырьковая"):
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if t in ("3D Полигон", "3D Триангуляция", "Пузырьковая"):
                data['z'] = self._parse_data(self.entry_z.get()) or []
        elif t == "Quiver":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['z'] = self._parse_data(self.entry_z.get()) or []
            data['yerr'] = self._parse_data(self.entry_yerr.get()) or []
        elif t in ("Кольцевая", "Вложенная круговая"):
            if t == "Вложенная круговая":
                box_data = []
                for r in self.entry_y.get().split(';'):
                    vals = self._parse_data(r)
                    if vals:
                        box_data.append(vals)
                data['box_data'] = box_data
                data['y'] = box_data[0] if box_data else []
            else:
                data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [l.strip()
                                   for l in
                                   self.entry_pie.get().split(',')]
            data['pie_colors'] = [c.strip()
                                   for c in
                                   self.entry_pie_colors.get().split(',')]
        elif t == "Мозаика":
            box_data = []
            for r in self.entry_y.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    box_data.append(vals)
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
            data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [l.strip()
                                   for l in
                                   self.entry_pie.get().split(',')]

        # ------------------- [NEW] Водопад / Гант -------------------
        elif t == "Водопад":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if not data['x']:
                data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [l.strip()
                                   for l in
                                   self.entry_pie.get().split(',')
                                   if l.strip()]
        elif t == "Гант":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['pie_labels'] = [l.strip()
                                   for l in
                                   self.entry_pie.get().split(',')
                                   if l.strip()]
            data['pie_colors'] = [c.strip()
                                   for c in
                                   self.entry_pie_colors.get().split(',')
                                   if c.strip()]

        elif t == "Радиальная":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
        elif t in ("3D Поверхность", "3D Сетка"):
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            m = len(hm)
            n = len(hm[0]) if hm else 0
            if not x_new or len(x_new) != n:
                x_new = list(range(n))
            if not y_new or len(y_new) != m:
                y_new = list(range(m))
            data['x'] = x_new
            data['y'] = y_new
            data['heatmap_data'] = hm
        elif t == "Столбчатая с накоплением":
            x_new = self._parse_data(self.entry_x.get())
            box_data = []
            for s in self.entry_y.get().split(';'):
                vals = self._parse_data(s)
                if vals:
                    box_data.append(vals)
            if not x_new:
                x_new = (list(range(len(box_data[0])))
                         if box_data else [])
            data['x'] = x_new
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
        elif t == "Полигон":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
        elif t in ("Box plot", "Violin"):
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    data['pie_labels'] = raw_labels
                else:
                    data['pie_labels'] = []
        elif t in ("Heatmap", "Contour", "Imshow"):
            hm = []
            for row_text in self.entry_z.get().split(';'):
                vals = self._parse_data(row_text)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
        elif t in ("Treemap", "Sunburst"):
            data['y'] = self._parse_data(self.entry_y.get())
            data['pie_labels'] = [l.strip()
                                   for l in
                                   self.entry_pie.get().split(',')]
            data['treemap_parents'] = [p.strip()
                                        for p in
                                        self.treemap_parents.get().split(';')]
        else:
            no_yerr = ("Круговая", "3D Линия", "3D Точечная",
                       "3D Столбчатая", "3D Гистограмма",
                       "3D Круговая", "Гистограмма")
            if t not in no_yerr:
                ye = self._parse_data(self.entry_yerr.get())
                if ye is None:
                    ye = []
                data['yerr'] = ye
            data['y'] = self._parse_data(self.entry_y.get())
            if t == "Круговая":
                data['x'] = list(range(len(data['y'])))
                data['pie_labels'] = [l.strip()
                                       for l in
                                       self.entry_pie.get().split(',')]
                data['pie_colors'] = [c.strip()
                                       for c in
                                       self.entry_pie_colors.get().split(',')]
            elif t == "Гистограмма":
                data['x'] = self._parse_data(self.entry_x.get())
            else:
                data['x'] = self._parse_data(self.entry_x.get())
                if "3D" in t:
                    data['z'] = self._parse_data(self.entry_z.get())

        data.update({
            'type': t, 'color': self.color_var.get(),
            'label': self.entry_label.get(),
            'lw': self.lw_var.get(), 'ls': self.ls_var.get(),
            'ms': self.ms_var.get(), 'marker': self.marker_var.get(),
            'use_y2': self.use_y2_var.get(), 'bins': self.bins_var.get(),
            'smooth': self.smooth_var.get(), 'fill': self.fill_var.get(),
            'glow': self.glow_var.get(), 'notes': self.entry_notes.get(),
            'subplot_index': self.subplot_index_var.get(),
            'unit_x': self.unit_x_var.get(),
            'unit_y': self.unit_y_var.get(),
            'unit_z': self.unit_z_var.get(),
        })
        data['artist'] = self._create_artist(data)
        self._update_listbox()
        self._redraw()
        self._refresh_stats()

    def _delete_graph(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        self._snapshot(tr.t('hist.deleted_graphs', count=len(sel)))
        for idx in sorted(sel, reverse=True):
            if 0 <= idx < len(self.graphs_data):
                self._remove_artist(self.graphs_data.pop(idx)['artist'])
        for k in list(self.axes_secondary.keys()):
            if not any(d.get('use_y2')
                       and d.get('subplot_index', 0) == k
                       for d in self.graphs_data):
                try:
                    self.axes_secondary[k].remove()
                except Exception:
                    pass
                del self.axes_secondary[k]
        self._update_listbox()
        self._redraw()
        self._refresh_stats()

    def _clear_all(self):
        if self.graphs_data and messagebox.askyesno(
                tr.t('msg.confirm'),
                tr.t('msg.clear_all_confirm')):
            self._snapshot(tr.t('hist.cleared_all'))
            self._clear_all_silent(keep_undo=True)

    def _clear_all_silent(self, keep_undo=False):
        self._stop_animation()
        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        self.fig.clear()
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
        self.graphs_data.clear()
        self.folders = [""]
        self.line_counter = 0
        self._update_listbox()
        self.canvas.draw()
        self._refresh_stats()

    def _update_listbox(self):
        tree = self.graph_tree
        tree.delete(*tree.get_children())
        folder_nodes = {}
        for f in self.folders:
            if not f:
                continue
            is_hidden = f in self.hidden_folders
            icon = "📂" if is_hidden else "📁"
            folder_nodes[f] = tree.insert('', 'end',
                                           text=f"{icon} {f}",
                                           open=(not is_hidden),
                                           values=())
        for i, d in enumerate(self.graphs_data):
            tags = []
            if d.get('use_y2'):
                tags.append("Y2")
            if d.get('smooth'):
                tags.append("~")
            if d.get('notes'):
                tags.append("💬")
            tag_str = f" [{','.join(tags)}]" if tags else ""
            text = f"[{tr.type_name(d['type'])}]{tag_str} {d['label']}"
            folder = d.get('folder', '')
            if folder and folder in self.hidden_folders:
                continue
            parent = folder_nodes.get(folder, '')
            tree.insert(parent, 'end', text=text, values=(i,))

    def _redraw(self):
        try:
            if self.lim_auto_var.get():
                for ax in self.axes:
                    try:
                        ax.relim()
                        ax.autoscale_view()
                    except Exception:
                        pass
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
                try:
                    ax.grid(self.show_grid_var.get(),
                            linestyle='--', alpha=0.6)
                except Exception:
                    pass
        except Exception:
            pass
        self.canvas.draw_idle()

    def _redraw_all(self):
        if hasattr(self, 'fig'):
            self._redraw()

    # ========================================================================
    # ПЕРЕКЛЮЧЕНИЕ ТИПОВ
    # ========================================================================
    def _on_type_change(self, event=None):
        for fr in (self.frame_x, self.frame_y, self.frame_z,
                   self.frame_pie_labels, self.frame_pie_colors,
                   self.frame_yerr, self.frame_y2_check,
                   self.frame_bins, self.frame_treemap,
                   self.frame_fill, self.frame_glow, self.frame_hint):
            fr.pack_forget()
        t = tr.find_type_by_display(self.type_var.get())
        self.hint_label.config(text="")

        if t in ("Круговая", "Кольцевая"):
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
        elif t == "Вложенная круговая":
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.nested_pie_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Мозаика":
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.mosaic_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Quiver":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_yerr.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.quiver_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Радиальная":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.radial_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Полярный scatter":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.polar_scatter_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Пузырьковая":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.bubble_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "3D Полигон":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.polygon3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "3D Триангуляция":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.trisurf_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t in ("3D Поверхность", "3D Сетка"):
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.surface_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Столбчатая с накоплением":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.stacked_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Полигон":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)

        # ------------------- [NEW] Водопад / Гант -------------------
        elif t == "Водопад":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.waterfall_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Гант":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.gantt_hint'))
            self.frame_hint.pack(fill=tk.X)

        elif t in ("Box plot", "Violin"):
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.box_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t in ("Heatmap", "Contour", "Imshow"):
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.heatmap_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t in ("Treemap", "Sunburst"):
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.frame_treemap.pack(fill=tk.X)
        elif "3D" in t:
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            if t == "3D Линия":
                self.frame_fill.pack(fill=tk.X)
        elif t == "Гистограмма":
            self.frame_x.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
        else:
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_yerr.pack(fill=tk.X)
            self.frame_y2_check.pack(fill=tk.X)
            if t in ("Линия", "Точечная"):
                self.frame_fill.pack(fill=tk.X)
            if t == "Точечная":
                self.frame_glow.pack(fill=tk.X)

    def _on_anim_type_change(self, event=None):
        t = tr.find_anim_by_display(self.anim_type_var.get())
        if t in ("Своя функция (2D)", "Своя функция (3D)"):
            self.frame_custom_anim.pack(fill=tk.X, pady=2)
        else:
            self.frame_custom_anim.pack_forget()

    # ========================================================================
    # СЕТКА / ЛЕГЕНДА / ОСИ
    # ========================================================================
    def _update_grid(self):
        for ax in self.axes:
            try:
                ax.grid(self.show_grid_var.get(),
                        linestyle='--', alpha=0.6)
            except Exception:
                pass
        self.canvas.draw_idle()

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
            'box_data': [], 'heatmap_data': [],
            'folder': '', 'smooth': False, 'fill': False,
            'glow': False, 'notes': '', 'treemap_parents': [],
            'subplot_index': 0,
            'unit_x': '—', 'unit_y': '—', 'unit_z': '—',
            'artist': None,
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
        sd = {
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "arcsin": np.arcsin, "arccos": np.arccos,
            "arctan": np.arctan, "arctan2": np.arctan2,
            "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
            "exp": np.exp, "log": np.log, "log10": np.log10,
            "log2": np.log2, "sqrt": np.sqrt, "abs": np.abs,
            "sign": np.sign, "floor": np.floor, "ceil": np.ceil,
            "round": np.round, "min": np.minimum, "max": np.maximum,
            "where": np.where, "power": np.power, "mod": np.mod,
            "hypot": np.hypot, "radians": np.radians,
            "degrees": np.degrees, "pi": np.pi, "e": np.e,
            "x": x_val, "y": y_val, "t": t_val,
        }
        try:
            return eval(expr, {"__builtins__": {}}, sd)
        except Exception as e:
            if not silent and not self.live_preview_var.get():
                messagebox.showerror(tr.t('msg.formula_error'), str(e))
            return None

    def _add_trendline(self):
        selection = self._get_selected_indices()
        if not selection:
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('msg.select_object'))
            return
        data = self.graphs_data[selection[0]]
        invalid = ("Круговая", "Гистограмма", "Heatmap", "Contour",
                   "Imshow", "Box plot", "Violin", "Treemap",
                   "Sunburst", "Полигон", "Quiver", "Кольцевая",
                   "Вложенная круговая", "Мозаика", "Радиальная",
                   "Столбчатая с накоплением", "Полярный scatter",
                   "Пузырьковая", "3D Поверхность", "3D Сетка",
                   "3D Полигон", "3D Триангуляция",
                   "Водопад", "Гант")            # [NEW]
        if "3D" in data['type'] or data['type'] in invalid:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.trend_only_2d'))
            return
        x = np.array(data['x'])
        y = np.array(data['y'])
        degree = self.trend_degree_var.get()
        if degree >= len(x):
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.trend_degree'))
            return
        self._snapshot(tr.t('hist.trend_added', name=data['label']))
        coeffs = np.polyfit(x, y, degree)
        y_trend = np.polyval(coeffs, x)
        eq_parts = []
        for i, c in enumerate(coeffs[::-1]):
            power = degree - i
            if power == 0:
                eq_parts.append(f"{c:.2f}")
            elif power == 1:
                eq_parts.append(f"{c:.2f}x")
            else:
                eq_parts.append(f"{c:.2f}x^{power}")
        eq_str = " ".join(eq_parts).replace("+ -", "- ")
        self.line_counter += 1
        td = self._default_data('Линия', x.tolist(), y_trend.tolist(),
                                label=f"Trend (y = {eq_str})",
                                color='red', ls='--', ms=0,
                                marker='None',
                                subplot_index=data.get('subplot_index', 0))
        td['use_y2'] = data.get('use_y2', False)
        td['folder'] = data.get('folder', '')
        td['artist'] = self._create_artist(td)
        self.graphs_data.append(td)
        self._update_listbox()
        self._redraw()

    # ========================================================================
    # UNDO / REDO
    # ========================================================================
    def _snapshot(self, description=""):
        try:
            self._mark_modified()                       # [NEW]
        except Exception:
            pass
        if description:
            self._show_history(description)
        snap = [{k: v for k, v in d.items() if k != 'artist'}
                for d in self.graphs_data]
        self.undo_stack.append(snap)
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _undo(self):
        if not self.undo_stack:
            self.status_var.set(tr.t('status.nothing_undo'))
            return
        current = [{k: v for k, v in d.items() if k != 'artist'}
                   for d in self.graphs_data]
        self.redo_stack.append(current)
        self._restore_snapshot(self.undo_stack.pop())
        self._show_history(tr.t('status.undo'))
        self.status_var.set(tr.t('status.undo'))

    def _redo(self):
        if not self.redo_stack:
            self.status_var.set(tr.t('status.nothing_redo'))
            return
        current = [{k: v for k, v in d.items() if k != 'artist'}
                   for d in self.graphs_data]
        self.undo_stack.append(current)
        self._restore_snapshot(self.redo_stack.pop())
        self._show_history(tr.t('status.redo'))
        self.status_var.set(tr.t('status.redo'))

    def _restore_snapshot(self, snap):
        self._stop_animation()
        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        self.fig.clear()
        needs_3d = any("3D" in d['type'] for d in snap)
        needs_polar = any(d['type'] in ("Радиальная", "Полярный scatter")
                          for d in snap)
        proj_kw = {}
        if needs_3d:
            proj_kw['projection'] = '3d'
        elif needs_polar:
            proj_kw['projection'] = 'polar'
        self.axes = []
        n = self.subplot_rows * self.subplot_cols
        for i in range(n):
            ax = self.fig.add_subplot(self.subplot_rows,
                                      self.subplot_cols, i + 1, **proj_kw)
            self.axes.append(ax)
        self.ax = self.axes[0]
        self._style_axes()
        self._init_tooltip()
        self._init_crosshair()
        self.graphs_data = []
        self.folders = [""]
        for d in snap:
            d = dict(d)
            for k, v in [('folder', ''), ('box_data', []),
                         ('heatmap_data', []), ('smooth', False),
                         ('fill', False), ('glow', False),
                         ('notes', ''), ('treemap_parents', []),
                         ('subplot_index', 0),
                         ('unit_x', '—'), ('unit_y', '—'),
                         ('unit_z', '—')]:
                d.setdefault(k, v)
            if d['folder'] and d['folder'] not in self.folders:
                self.folders.append(d['folder'])
            if d['subplot_index'] >= len(self.axes):
                d['subplot_index'] = 0
            d['artist'] = self._create_artist(d)
            self.graphs_data.append(d)
        self.line_counter = len(self.graphs_data)
        self._update_listbox()
        self._redraw()

    # ========================================================================
    # ДАННЫЕ
    # ========================================================================
    def _paste_from_clipboard(self, event, entry_widget):
        try:
            cb = self.root.clipboard_get()
            if not cb:
                return
            values = []
            for row in cb.replace('\r\n', '\n').strip().split('\n'):
                values.extend([v.strip() for v in row.split('\t')
                               if v.strip()])
            if values:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, ", ".join(values))
                self._on_data_change(event)
        except tk.TclError:
            pass

    def _on_data_change(self, event=None):
        if self.live_preview_var.get() and self._get_selected_indices():
            self._update_graph()

    def _on_drop(self, event):
        path = event.data.strip('{}')
        low = path.lower()
        if low.endswith('.json'):
            self._load_json(path)
        elif low.endswith('.xlsx') or low.endswith('.xls'):
            self._import_excel(path)
        elif low.endswith('.csv'):
            self._import_csv(path)
        elif low.endswith('.zip'):
            self._load_zip(path)
        elif low.endswith('.graphx'):
            self._load_graphx(path)
        elif low.endswith('.graphxtpl'):
            self._import_template_file(path)
        elif low.endswith('.graphxanim'):
            self._load_graphxanim(path)
        elif low.endswith('.graphxtemp'):
            self._load_autosave(path)                       # [NEW]

    # ========================================================================
    # ГРУППОВЫЕ ОПЕРАЦИИ
    # ========================================================================
    def _group_change_color(self):
        sel = self._get_selected_indices()
        if len(sel) < 2:
            return
        c = colorchooser.askcolor(title=tr.t('msg.choose_color'))
        if not c[1]:
            return
        self._snapshot(tr.t('hist.group_color', count=len(sel)))
        for idx in sel:
            self.graphs_data[idx]['color'] = c[1]
            self._remove_artist(self.graphs_data[idx]['artist'])
            self.graphs_data[idx]['artist'] = self._create_artist(
                self.graphs_data[idx])
        self._update_listbox()
        self._redraw()

    def _group_change_lw(self):
        sel = self._get_selected_indices()
        if len(sel) < 2:
            return
        val = simpledialog.askfloat("Толщина", "Значение (0.5–10):",
                                    initialvalue=2.0, minvalue=0.1,
                                    maxvalue=20, parent=self.root)
        if val is None:
            return
        self._snapshot(tr.t('hist.group_lw', count=len(sel)))
        for idx in sel:
            self.graphs_data[idx]['lw'] = val
            self._remove_artist(self.graphs_data[idx]['artist'])
            self.graphs_data[idx]['artist'] = self._create_artist(
                self.graphs_data[idx])
        self._update_listbox()
        self._redraw()

    def _group_change_ms(self):
        sel = self._get_selected_indices()
        if len(sel) < 2:
            return
        val = simpledialog.askfloat("Размер маркера", "Значение (1–30):",
                                    initialvalue=6.0, minvalue=0.5,
                                    maxvalue=50, parent=self.root)
        if val is None:
            return
        self._snapshot(tr.t('hist.group_ms', count=len(sel)))
        for idx in sel:
            self.graphs_data[idx]['ms'] = val
            self._remove_artist(self.graphs_data[idx]['artist'])
            self.graphs_data[idx]['artist'] = self._create_artist(
                self.graphs_data[idx])
        self._update_listbox()
        self._redraw()

    def _export_selected_json(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        items = [{k: v for k, v in self.graphs_data[i].items()
                  if k != 'artist'} for i in sel]
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="selected.json")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2,
                          default=lambda o: o.tolist()
                          if hasattr(o, 'tolist') else o)
            self._show_history(tr.t('hist.exported_selected',
                                     count=len(items)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ========================================================================
    # ОБЪЕКТЫ / ПАПКИ
    # ========================================================================
    def _duplicate_graph(self, event=None):
        sel = self._get_selected_indices()
        if not sel:
            return
        self._snapshot(tr.t('hist.duplicated', count=len(sel)))
        new_list = []
        for idx in sel:
            src = self.graphs_data[idx]
            new = dict(src)
            for key in ('x', 'y', 'z', 'pie_labels', 'pie_colors',
                        'yerr', 'treemap_parents'):
                if key in src:
                    new[key] = list(src[key])
            new['box_data'] = [list(g) for g in src.get('box_data', [])]
            new['heatmap_data'] = [list(r)
                                    for r in src.get('heatmap_data', [])]
            new['label'] = src['label'] + " (copy)"
            new['artist'] = None
            new['artist'] = self._create_artist(new)
            new_list.append(new)
        self.graphs_data.extend(new_list)
        self._update_listbox()
        self._redraw()

    def _rename_graph(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        old = self.graphs_data[sel[0]]['label']
        new = simpledialog.askstring(tr.t('msg.rename_title'),
                                      tr.t('msg.new_name'),
                                      initialvalue=old,
                                      parent=self.root)
        if not new:
            return
        self._snapshot(tr.t('hist.renamed', old=old, new=new))
        for idx in sel:
            self.graphs_data[idx]['label'] = new
        self._update_listbox()

    def _edit_notes(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        data = self.graphs_data[sel[0]]
        new = simpledialog.askstring(
            tr.t('msg.notes_title'),
            tr.t('msg.notes_prompt', name=data['label']),
            initialvalue=data.get('notes', ''),
            parent=self.root)
        if new is None:
            return
        self._snapshot(tr.t('hist.notes_changed'))
        for idx in sel:
            self.graphs_data[idx]['notes'] = new
        self._update_listbox()
        if (self._get_selected_indices() == sel
                and self.entry_notes.winfo_exists()):
            self.entry_notes.delete(0, tk.END)
            self.entry_notes.insert(0, new)

    def _move_to_folder(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.move_folder_title'))
        win.transient(self.root)
        ttk.Label(win, text=tr.t('msg.folder_name')).pack(padx=10, pady=5)
        var = tk.StringVar(
            value=self.graphs_data[sel[0]].get('folder', ''))
        e = ttk.Entry(win, textvariable=var, width=25)
        e.pack(padx=10, pady=5)
        e.focus()

        def ok():
            f = var.get().strip()
            if f and f not in self.folders:
                self.folders.append(f)
            self._snapshot(tr.t('hist.moved_to_folder', name=f or '/'))
            for idx in sel:
                self.graphs_data[idx]['folder'] = f
            self._update_listbox()
            win.destroy()

        ttk.Button(win, text="OK", command=ok).pack(pady=10)
        e.bind('<Return>', lambda ev: ok())

    def _rename_folder(self, old_name):
        new_name = simpledialog.askstring(
            tr.t('msg.rename_folder_title'),
            tr.t('msg.new_name'),
            initialvalue=old_name, parent=self.root)
        if not new_name or new_name == old_name:
            return
        self._snapshot(tr.t('hist.folder_renamed',
                             old=old_name, new=new_name))
        for d in self.graphs_data:
            if d.get('folder') == old_name:
                d['folder'] = new_name
        if old_name in self.folders:
            self.folders[self.folders.index(old_name)] = new_name
        if old_name in self.hidden_folders:
            self.hidden_folders.discard(old_name)
            self.hidden_folders.add(new_name)
        self._update_listbox()

    def _delete_folder(self, item, with_content):
        name = (self.graph_tree.item(item, 'text')
                .replace("📁 ", "").replace("📂 ", ""))
        if not name:
            return
        if with_content:
            if not messagebox.askyesno(
                    tr.t('msg.confirm'),
                    tr.t('msg.delete_folder_confirm', name=name)):
                return
        self._snapshot(tr.t('hist.folder_deleted', name=name))
        if with_content:
            keep = []
            for d in self.graphs_data:
                if d.get('folder') == name:
                    self._remove_artist(d['artist'])
                else:
                    keep.append(d)
            self.graphs_data = keep
        else:
            for d in self.graphs_data:
                if d.get('folder') == name:
                    d['folder'] = ''
        if name in self.folders:
            self.folders.remove(name)
        self.hidden_folders.discard(name)
        self._update_listbox()
        self._redraw()

    # ========================================================================
    # ГЕНЕРАТОРЫ
    # ========================================================================
    def _generate_data(self):
        expr_all = self.gen_expr.get().strip()
        if not expr_all:
            return
        try:
            xmin = float(self.gen_xmin.get().replace(',', '.'))
            xmax = float(self.gen_xmax.get().replace(',', '.'))
            n = int(self.gen_n.get())
        except ValueError:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.bad_format'))
            return
        unit = self.gen_unit_var.get()
        factor = UNIT_TO_M.get(unit, 1.0)
        xmin_m = xmin * factor
        xmax_m = xmax * factor
        x = np.linspace(xmin_m, xmax_m, n)
        exprs = [e.strip() for e in expr_all.split(';') if e.strip()]
        if len(exprs) == 1:
            y = self._safe_eval(exprs[0], x, 0)
            if y is None:
                return
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(
                0, ", ".join(map(str, np.round(x, 6).tolist())))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(
                0, ", ".join(map(str, np.round(y, 4).tolist())))
            self._show_history(
                f"Сгенерировано ({xmin}–{xmax} {unit} → "
                f"{xmin_m:.4g}–{xmax_m:.4g} м)")
            self.notebook.select(0)
            return
        self._snapshot(tr.t('hist.generated_formulas',
                             count=len(exprs)))
        self._ensure_correct_axes_dimension(False)
        colors = ['blue', 'red', 'green', 'orange',
                  'purple', 'brown', 'magenta', 'cyan']
        added = 0
        for i, expr in enumerate(exprs):
            y = self._safe_eval(expr, x, 0, silent=True)
            if y is None:
                continue
            self.line_counter += 1
            d = self._default_data('Линия', x.tolist(),
                                    np.asarray(y).tolist(),
                                    label=f"y = {expr}",
                                    color=colors[i % len(colors)])
            d['artist'] = self._create_artist(d)
            self.graphs_data.append(d)
            added += 1
        self._update_listbox()
        self._redraw()
        self.status_var.set(f"{added}")

    def _get_rnd_shape(self):
        text = self.rnd_shape_var.get()
        if text == tr.t('gen.rnd_shape_3d'):
            return '3d'
        if text == tr.t('gen.rnd_shape_3d_grid'):
            return '3d_grid'
        return '2d'

    def _on_rnd_shape_change(self, event=None):
        if self._get_rnd_shape() == '3d_grid':
            self.rnd_grid_frame.pack(fill=tk.X, pady=2)
        else:
            self.rnd_grid_frame.pack_forget()

    def _generate_random_data(self):
        try:
            n = int(self.rnd_n_var.get())
            p1 = float(self.rnd_p1_var.get().replace(',', '.'))
            p2 = float(self.rnd_p2_var.get().replace(',', '.'))
            seed_text = self.rnd_seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
        except ValueError:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.bad_params'))
            return
        if seed is not None:
            np.random.seed(seed)
        dist = self.rnd_dist_var.get()
        shape = self._get_rnd_shape()

        def gen_values(count):
            if dist == "normal":
                return np.random.normal(p1, p2, count)
            if dist == "uniform":
                return np.random.uniform(p1, p2, count)
            if dist == "exponential":
                scale = p1 if p1 > 0 else 1.0
                return np.random.exponential(scale, count) + p2
            if dist == "poisson":
                lam = p1 if p1 > 0 else 1.0
                return np.random.poisson(lam, count)
            if dist == "integers":
                lo, hi = int(p1), int(p2)
                if hi < lo:
                    lo, hi = hi, lo
                return np.random.randint(lo, hi + 1, count)
            return np.random.normal(p1, p2, count)

        if shape == '2d':
            y = gen_values(n)
            x = np.arange(n)
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, x.tolist())))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(
                0, ", ".join(map(str, np.round(y, 4).tolist())))
            if "3D" not in tr.find_type_by_display(self.type_var.get()):
                self.type_var.set(tr.type_name("Линия"))
                self._on_type_change()
            self._show_history(
                tr.t('hist.generated_random', count=n, dist=dist))
            self.notebook.select(0)
            return
        if shape == '3d':
            x = np.arange(n)
            y = gen_values(n)
            z = gen_values(n)
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, x.tolist())))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(
                0, ", ".join(map(str, np.round(y, 4).tolist())))
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(
                0, ", ".join(map(str, np.round(z, 4).tolist())))
            t_cur = tr.find_type_by_display(self.type_var.get())
            if "3D" not in t_cur:
                self.type_var.set(tr.type_name("3D Линия"))
                self._on_type_change()
            self._show_history(
                tr.t('hist.generated_random_3d', count=n, dist=dist))
            self.notebook.select(0)
            return
        if shape == '3d_grid':
            try:
                gn = int(self.rnd_grid_n_var.get())
                gm = int(self.rnd_grid_m_var.get())
            except (ValueError, tk.TclError):
                gn, gm = 15, 15
            gn = max(3, gn)
            gm = max(3, gm)
            xg = (np.linspace(p1, p2, gn) if p2 != p1
                  else np.arange(gn, dtype=float))
            yg = (np.linspace(p1, p2, gm) if p2 != p1
                  else np.arange(gm, dtype=float))
            total = gn * gm
            z_flat = gen_values(total)
            Z = z_flat.reshape(gm, gn)
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(
                0, ", ".join(map(str, np.round(xg, 4).tolist())))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(
                0, ", ".join(map(str, np.round(yg, 4).tolist())))
            rows = [" ".join(map(str, np.round(row, 4).tolist()))
                    for row in Z]
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, " ; ".join(rows))
            t_cur = tr.find_type_by_display(self.type_var.get())
            if t_cur not in ("3D Поверхность", "3D Сетка"):
                self.type_var.set(tr.type_name("3D Поверхность"))
                self._on_type_change()
            self._show_history(
                tr.t('hist.generated_random_grid',
                     n=gn, m=gm, dist=dist))
            self.notebook.select(0)
            return

    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    def _refresh_stats(self):
        sel = self._get_selected_indices()
        if not sel:
            self.stats_label.config(text=tr.t('stats.none_selected'))
            for v in self.stats_vars.values():
                v.set('—')
            self.fit_result_var.set('')
            return
        data = self.graphs_data[sel[0]]
        self.stats_label.config(
            text=f"[{tr.type_name(data['type'])}] {data['label']}")
        try:
            y = np.array(data.get('y', []), dtype=float)
            x = np.array(data.get('x', []), dtype=float)
        except Exception:
            for v in self.stats_vars.values():
                v.set('—')
            return
        if len(y) == 0:
            for v in self.stats_vars.values():
                v.set('—')
            return

        def fmt(val, prec=4):
            if isinstance(val, (int, np.integer)):
                return str(val)
            return f"{val:.{prec}g}"

        self.stats_vars['n'].set(str(len(y)))
        self.stats_vars['min'].set(fmt(np.nanmin(y)))
        self.stats_vars['max'].set(fmt(np.nanmax(y)))
        self.stats_vars['mean'].set(fmt(np.nanmean(y)))
        self.stats_vars['median'].set(fmt(np.nanmedian(y)))
        self.stats_vars['std'].set(fmt(np.nanstd(y)))
        self.stats_vars['var'].set(fmt(np.nanvar(y)))
        q1, q3 = np.nanpercentile(y, [25, 75])
        self.stats_vars['q1'].set(fmt(q1))
        self.stats_vars['q3'].set(fmt(q3))
        self.stats_vars['iqr'].set(fmt(q3 - q1))
        self.stats_vars['sum'].set(fmt(np.nansum(y)))
        if len(x) == len(y) and len(x) > 1:
            try:
                corr = np.corrcoef(x, y)[0, 1]
                self.stats_vars['corr'].set(fmt(corr))
            except Exception:
                self.stats_vars['corr'].set('—')
        else:
            self.stats_vars['corr'].set('—')

    def _add_fit(self, kind):
        sel = self._get_selected_indices()
        if not sel:
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('msg.select_object_short'))
            return
        data = self.graphs_data[sel[0]]
        if "3D" in data['type'] or data['type'] in (
                "Круговая", "Гистограмма", "Heatmap", "Contour",
                "Imshow", "Box plot", "Violin", "Treemap", "Sunburst",
                "Водопад", "Гант"):                         # [NEW]
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.trend_only_2d'))
            return
        x = np.array(data['x'], dtype=float)
        y = np.array(data['y'], dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        x, y = x[mask], y[mask]
        if len(x) < 3:
            return
        try:
            if kind == 'linear':
                coeffs = np.polyfit(x, y, 1)
                y_fit = np.polyval(coeffs, x)
                title = f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}"
            elif kind == 'log':
                m = x > 0
                if m.sum() < 3:
                    messagebox.showerror(tr.t('msg.error'),
                                          "Log: X must be > 0")
                    return
                coeffs = np.polyfit(np.log(x[m]), y[m], 1)
                y_fit = np.full_like(x, np.nan)
                y_fit[m] = coeffs[0] * np.log(x[m]) + coeffs[1]
                title = (f"y = {coeffs[0]:.3f}·ln(x) "
                         f"+ {coeffs[1]:.3f}")
            elif kind == 'exp':
                m = y > 0
                if m.sum() < 3:
                    messagebox.showerror(tr.t('msg.error'),
                                          "Exp: Y must be > 0")
                    return
                coeffs = np.polyfit(x[m], np.log(y[m]), 1)
                y_fit = np.full_like(x, np.nan)
                y_fit[m] = (np.exp(coeffs[1])
                            * np.exp(coeffs[0] * x[m]))
                title = (f"y = {np.exp(coeffs[1]):.3f}"
                         f"·exp({coeffs[0]:.3f}x)")
            elif kind == 'power':
                m = (x > 0) & (y > 0)
                if m.sum() < 3:
                    messagebox.showerror(tr.t('msg.error'),
                                          "Power: X, Y must be > 0")
                    return
                coeffs = np.polyfit(np.log(x[m]), np.log(y[m]), 1)
                y_fit = np.full_like(x, np.nan)
                y_fit[m] = np.exp(coeffs[1]) * x[m] ** coeffs[0]
                title = (f"y = {np.exp(coeffs[1]):.3f}"
                         f"·x^{coeffs[0]:.3f}")
            else:
                return
            valid = np.isfinite(y_fit)
            if valid.sum() > 0:
                residuals = y[valid] - y_fit[valid]
                ss_res = np.sum(residuals ** 2)
                ss_tot = np.sum((y[valid] - y[valid].mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
                rmse = np.sqrt(np.mean(residuals ** 2))
                self.fit_result_var.set(
                    f"{title}\n"
                    f"{tr.t('stats.fit_r2')} {r2:.4f}   "
                    f"{tr.t('stats.fit_rmse')} {rmse:.4g}")
            self._snapshot(tr.t('hist.added_graph', name=title))
            self.line_counter += 1
            td = self._default_data(
                'Линия', x.tolist(), y_fit.tolist(),
                label=title, color='red', ls='--', lw=1.5,
                subplot_index=data.get('subplot_index', 0))
            td['artist'] = self._create_artist(td)
            self.graphs_data.append(td)
            self._update_listbox()
            self._redraw()
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _add_fit_poly(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        data = self.graphs_data[sel[0]]
        x = np.array(data['x'], dtype=float)
        y = np.array(data['y'], dtype=float)
        deg = self.fit_degree_var.get()
        if deg >= len(x):
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.trend_degree'))
            return
        coeffs = np.polyfit(x, y, deg)
        y_fit = np.polyval(coeffs, x)
        residuals = y - y_fit
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        rmse = np.sqrt(np.mean(residuals ** 2))
        eq_parts = []
        for i, c in enumerate(coeffs[::-1]):
            p = deg - i
            eq_parts.append(f"{c:.3g}" if p == 0
                            else f"{c:.3g}x" if p == 1
                            else f"{c:.3g}x^{p}")
        title = " + ".join(eq_parts).replace("+ -", "- ")
        self.fit_result_var.set(
            f"{title}\n"
            f"{tr.t('stats.fit_r2')} {r2:.4f}   "
            f"{tr.t('stats.fit_rmse')} {rmse:.4g}")
        self._snapshot(tr.t('hist.added_graph', name=title))
        self.line_counter += 1
        td = self._default_data(
            'Линия', x.tolist(), y_fit.tolist(),
            label=title, color='red', ls='--', lw=1.5,
            subplot_index=data.get('subplot_index', 0))
        td['artist'] = self._create_artist(td)
        self.graphs_data.append(td)
        self._update_listbox()
        self._redraw()

    def _find_peaks(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        data = self.graphs_data[sel[0]]
        try:
            from scipy.signal import find_peaks
        except ImportError:
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('stats.peaks_na'))
            return
        y = np.array(data['y'], dtype=float)
        x = np.array(data['x'], dtype=float)
        peaks, _ = find_peaks(y)
        if len(peaks) == 0:
            messagebox.showinfo(tr.t('msg.info'), "0")
            return
        self._snapshot(tr.t('stats.peaks_found', count=len(peaks)))
        self.line_counter += 1
        pk = self._default_data(
            'Точечная', x[peaks].tolist(), y[peaks].tolist(),
            label=f"Peaks ({len(peaks)})",
            color='orange', ms=10,
            subplot_index=data.get('subplot_index', 0))
        pk['artist'] = self._create_artist(pk)
        self.graphs_data.append(pk)
        self._update_listbox()
        self._redraw()
        messagebox.showinfo(tr.t('msg.done'),
                            tr.t('stats.peaks_found', count=len(peaks)))

    # ========================================================================
    # DRAG
    # ========================================================================
    def _on_press_drag(self, event):
        if not self.drag_points_enabled.get():
            return
        if event.button != 1 or event.inaxes is None:
            return
        if event.xdata is None or event.ydata is None:
            return
        if self.toolbar.mode != '':
            return
        ax = event.inaxes
        if hasattr(ax, 'get_zlim'):
            return
        ex, ey = event.xdata, event.ydata
        best = None
        best_d2 = float('inf')
        subplot_idx = self.axes.index(ax) if ax in self.axes else 0
        for i, d in enumerate(self.graphs_data):
            if d['type'] not in ("Линия", "Точечная"):
                continue
            if d.get('subplot_index', 0) != subplot_idx:
                continue
            xs = d.get('x', [])
            ys = d.get('y', [])
            for j, (xi, yi) in enumerate(zip(xs, ys)):
                try:
                    d2 = (xi - ex) ** 2 + (yi - ey) ** 2
                except TypeError:
                    continue
                if d2 < best_d2:
                    best_d2 = d2
                    best = (i, j)
        if best is None:
            return
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        thresh = 0.003 * ((xlim[1] - xlim[0]) ** 2
                          + (ylim[1] - ylim[0]) ** 2)
        if best_d2 > thresh:
            return
        self._drag_active = True
        self._drag_obj_idx = best[0]
        self._drag_point_idx = best[1]
        self._drag_count_in_session = 0
        self.status_var.set(f"Перетаскивание точки #{best[1]}...")

    def _on_motion_drag(self, event):
        if not self._drag_active:
            return
        if event.inaxes is None or event.xdata is None:
            return
        obj_idx = self._drag_obj_idx
        pt_idx = self._drag_point_idx
        if obj_idx is None or pt_idx is None:
            return
        data = self.graphs_data[obj_idx]
        data['x'][pt_idx] = event.xdata
        data['y'][pt_idx] = event.ydata
        self._drag_count_in_session += 1
        self._remove_artist(data['artist'])
        data['artist'] = self._create_artist(data)
        self.canvas.draw_idle()

    def _on_release_drag(self, event):
        if not self._drag_active:
            return
        if self._drag_count_in_session > 0:
            self._snapshot(tr.t('hist.point_moved',
                                 n=self._drag_point_idx))
        self._drag_active = False
        self._drag_obj_idx = None
        self._drag_point_idx = None
        self._drag_count_in_session = 0
        self.status_var.set(tr.t('status.ready'))

    # ========================================================================
    # TOOLTIP / CROSSHAIR / СТАТУС
    # ========================================================================
    def _update_status(self, event):
        if event.inaxes is None:
            self.status_var.set(tr.t('status.ready'))
            return
        ax = event.inaxes
        if hasattr(ax, 'get_zlim'):
            try:
                ax.M = ax.get_proj()
                x3, y3, z3 = proj3d.inv_transform(event.xdata,
                                                   event.ydata, ax.M)
                self.status_var.set(
                    tr.t('status.cursor_xyz', x=x3, y=y3, z=z3))
            except Exception:
                self.status_var.set(tr.t('misc.3d_chart'))
            return
        for sec in self.axes_secondary.values():
            if ax == sec:
                self.status_var.set(tr.t('status.cursor_xy2',
                                          x=event.xdata, y=event.ydata))
                return
        if event.xdata is not None and event.ydata is not None:
            self.status_var.set(tr.t('status.cursor_xy',
                                     x=event.xdata, y=event.ydata))
        else:
            self.status_var.set(tr.t('status.ready'))

    def _init_tooltip(self):
        if not self.axes:
            self.tooltip_annot = None
            return
        self.tooltip_annot = self.axes[0].annotate(
            "", xy=(0, 0), xytext=(12, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round", fc="#ffffcc",
                      ec="gray", alpha=0.9),
            arrowprops=dict(arrowstyle="->"))
        self.tooltip_annot.set_visible(False)

    def _on_motion_tooltip(self, event):
        if not self.show_tooltip_var.get() or self.tooltip_annot is None:
            return
        if event.inaxes not in self.axes or event.xdata is None:
            if self.tooltip_annot.get_visible():
                self.tooltip_annot.set_visible(False)
                self.canvas.draw_idle()
            return
        ax = event.inaxes
        if hasattr(ax, 'get_zlim'):
            return
        ex, ey = event.xdata, event.ydata
        best = None
        best_d2 = float('inf')
        skip = ("Круговая", "Heatmap", "Contour", "Imshow",
                "Box plot", "Violin", "Treemap", "Sunburst",
                "Мозаика", "Радиальная", "Столбчатая с накоплением",
                "Вложенная круговая", "Полигон", "Кольцевая",
                "Полярный scatter", "Пузырьковая", "Quiver",
                "Водопад", "Гант")                      # [NEW]
        subplot_idx = self.axes.index(ax) if ax in self.axes else 0
        for d in self.graphs_data:
            if d['type'] in skip or "3D" in d['type']:
                continue
            if d.get('subplot_index', 0) != subplot_idx:
                continue
            xs = d.get('x', [])
            ys = d.get('y', [])
            if not xs or not ys:
                continue
            for xi, yi in zip(xs, ys):
                try:
                    d2 = (xi - ex) ** 2 + (yi - ey) ** 2
                except TypeError:
                    continue
                if d2 < best_d2:
                    best_d2 = d2
                    best = (xi, yi, d['label'], d.get('notes', ''))
        if best is None:
            if self.tooltip_annot.get_visible():
                self.tooltip_annot.set_visible(False)
                self.canvas.draw_idle()
            return
        xl = ax.get_xlim()
        yl = ax.get_ylim()
        thresh = 0.0025 * ((xl[1] - xl[0]) ** 2
                            + (yl[1] - yl[0]) ** 2)
        if best_d2 > thresh:
            if self.tooltip_annot.get_visible():
                self.tooltip_annot.set_visible(False)
                self.canvas.draw_idle()
            return
        text = f"{best[2]}\n({best[0]:.3g}, {best[1]:.3g})"
        if best[3]:
            text += f"\n💬 {best[3]}"
        if self.tooltip_annot.axes != ax:
            try:
                self.tooltip_annot.remove()
            except Exception:
                pass
            self.tooltip_annot = ax.annotate(
                "", xy=(0, 0), xytext=(12, 12),
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="#ffffcc",
                          ec="gray", alpha=0.9),
                arrowprops=dict(arrowstyle="->"))
        self.tooltip_annot.xy = (best[0], best[1])
        self.tooltip_annot.set_text(text)
        self.tooltip_annot.set_visible(True)
        self.canvas.draw_idle()

    def _on_motion_tooltip_3d(self, event):
        if not self.show_tooltip_var.get():
            return
        if event.inaxes not in self.axes or event.xdata is None:
            return
        ax = event.inaxes
        if not hasattr(ax, 'get_zlim'):
            return
        try:
            ax.M = ax.get_proj()
            x3, y3, _ = proj3d.inv_transform(event.xdata,
                                              event.ydata, ax.M)
        except Exception:
            return
        best = None
        best_d2 = float('inf')
        subplot_idx = self.axes.index(ax) if ax in self.axes else 0
        for d in self.graphs_data:
            if "3D" not in d['type']:
                continue
            if d.get('subplot_index', 0) != subplot_idx:
                continue
            xs = d.get('x', [])
            ys = d.get('y', [])
            zs = d.get('z', [])
            if not xs or not ys or not zs:
                continue
            for xi, yi, zi in zip(xs, ys, zs):
                try:
                    d2 = (xi - x3) ** 2 + (yi - y3) ** 2
                except TypeError:
                    continue
                if d2 < best_d2:
                    best_d2 = d2
                    best = (xi, yi, zi, d['label'],
                            d.get('notes', ''))
        if best is None:
            return
        try:
            xl = ax.get_xlim()
            yl = ax.get_ylim()
            thresh = 0.01 * ((xl[1] - xl[0]) ** 2
                              + (yl[1] - yl[0]) ** 2)
        except Exception:
            thresh = float('inf')
        if best_d2 > thresh:
            return
        try:
            x2, y2, _ = proj3d.proj_transform(best[0], best[1],
                                                best[2], ax.get_proj())
        except Exception:
            return
        if self.tooltip_annot is None or self.tooltip_annot.axes != ax:
            try:
                if self.tooltip_annot:
                    self.tooltip_annot.remove()
            except Exception:
                pass
            self.tooltip_annot = ax.annotate(
                "", xy=(0, 0), xytext=(12, 12),
                textcoords="offset points",
                bbox=dict(boxstyle="round", fc="#ffffcc",
                          ec="gray", alpha=0.9),
                arrowprops=dict(arrowstyle="->"))
        text = (f"{best[3]}\n({best[0]:.3g}, "
                f"{best[1]:.3g}, {best[2]:.3g})")
        if best[4]:
            text += f"\n💬 {best[4]}"
        self.tooltip_annot.xy = (x2, y2)
        self.tooltip_annot.set_text(text)
        self.tooltip_annot.set_visible(True)
        self.canvas.draw_idle()

    def _toggle_crosshair(self):
        if not self.crosshair_enabled.get():
            self._hide_crosshair(None)
        self._redraw_all()

    def _init_crosshair(self):
        if not self.axes:
            self._crosshair_v = None
            self._crosshair_h = None
            return
        ax = self.axes[0]
        if hasattr(ax, 'get_zlim'):
            self._crosshair_v = None
            self._crosshair_h = None
            return
        self._crosshair_v = ax.axvline(0, color='gray', lw=0.8,
                                        alpha=0.5, linestyle='--',
                                        zorder=999)
        self._crosshair_h = ax.axhline(0, color='gray', lw=0.8,
                                        alpha=0.5, linestyle='--',
                                        zorder=999)
        self._crosshair_v.set_visible(False)
        self._crosshair_h.set_visible(False)

    def _on_motion_crosshair(self, event):
        if not self.crosshair_enabled.get():
            return
        if self._crosshair_v is None:
            return
        if event.inaxes not in self.axes or event.xdata is None:
            self._hide_crosshair(event)
            return
        ax = event.inaxes
        if hasattr(ax, 'get_zlim'):
            return
        if self._crosshair_v.axes != ax:
            try:
                self._crosshair_v.remove()
                self._crosshair_h.remove()
            except Exception:
                pass
            self._crosshair_v = ax.axvline(0, color='gray', lw=0.8,
                                            alpha=0.5,
                                            linestyle='--', zorder=999)
            self._crosshair_h = ax.axhline(0, color='gray', lw=0.8,
                                            alpha=0.5,
                                            linestyle='--', zorder=999)
        try:
            self._crosshair_v.set_xdata([event.xdata, event.xdata])
            self._crosshair_h.set_ydata([event.ydata, event.ydata])
            self._crosshair_v.set_visible(True)
            self._crosshair_h.set_visible(True)
            self.canvas.draw_idle()
        except Exception:
            pass

    def _hide_crosshair(self, event):
        if self._crosshair_v is None:
            return
        try:
            if self._crosshair_v.get_visible():
                self._crosshair_v.set_visible(False)
                self._crosshair_h.set_visible(False)
                self.canvas.draw_idle()
        except Exception:
            pass

    # ========================================================================
    # IO — JSON
    # ========================================================================
    def _save_json(self):
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
                          if isinstance(o, np.ndarray) else o)
            if self.current_doc_idx >= 0:
                self.documents[self.current_doc_idx].path = path
                self.documents[self.current_doc_idx].modified = False
            self._show_history(tr.t('hist.saved_json',
                                     name=os.path.basename(path)))
            self.status_var.set(tr.t('hist.saved_json', name=path))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _load_json(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._snapshot()
            self._clear_all_silent(keep_undo=True)
            self.folders = [""]
            for d in data:
                for k, v in [('bins', 10), ('box_data', []),
                             ('heatmap_data', []), ('folder', ''),
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
            self._update_listbox()
            self._redraw()
            if self.current_doc_idx >= 0:
                self.documents[self.current_doc_idx].path = path
                self.documents[self.current_doc_idx].modified = False
            self._show_history(tr.t('hist.loaded_json',
                                     name=os.path.basename(path)))
            self.status_var.set(tr.t('hist.loaded_json', name=path))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ========================================================================
    # IO — ZIP
    # ========================================================================
    def _save_zip(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP", "*.zip")])
        if not path:
            return
        try:
            data = [{k: v for k, v in d.items() if k != 'artist'}
                    for d in self.graphs_data]
            with tempfile.TemporaryDirectory() as td:
                jp = os.path.join(td, 'graph.json')
                with open(jp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2,
                              default=lambda o: o.tolist()
                              if hasattr(o, 'tolist') else o)
                pp = os.path.join(td, 'plot.png')
                try:
                    self.fig.savefig(pp, dpi=200, bbox_inches='tight')
                except Exception:
                    pass
                sp = os.path.join(td, 'settings.json')
                with open(sp, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': self.plot_title_var.get(),
                        'xlabel': self.plot_xlabel_var.get(),
                        'ylabel': self.plot_ylabel_var.get(),
                        'settings': self.settings,
                        'folders': self.folders,
                        'theme': self.settings.get('theme', 'light'),
                        'subplot_grid': [self.subplot_rows,
                                          self.subplot_cols],
                    }, f, ensure_ascii=False, indent=2)
                with zipfile.ZipFile(path, 'w',
                                      zipfile.ZIP_DEFLATED) as zf:
                    zf.write(jp, 'graph.json')
                    if os.path.exists(pp):
                        zf.write(pp, 'plot.png')
                    zf.write(sp, 'settings.json')
            self._show_history(tr.t('hist.saved_zip',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _load_zip(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("ZIP", "*.zip")])
        if not path:
            return
        try:
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(td)
                jp = os.path.join(td, 'graph.json')
                if os.path.exists(jp):
                    self._load_json(jp)
                sp = os.path.join(td, 'settings.json')
                if os.path.exists(sp):
                    with open(sp, 'r', encoding='utf-8') as f:
                        s = json.load(f)
                    self._apply_settings_dict(s)
            self._show_history(tr.t('hist.loaded_zip',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _apply_settings_dict(self, s):
        self.plot_title_var.set(s.get('title', 'График'))
        self.plot_xlabel_var.set(s.get('xlabel', 'X'))
        self.plot_ylabel_var.set(s.get('ylabel', 'Y'))
        self.settings.update(s.get('settings', {}))
        self.folders = s.get('folders', [''])
        grid = s.get('subplot_grid', [1, 1])
        if isinstance(grid, (list, tuple)) and len(grid) == 2:
            self.subplot_rows, self.subplot_cols = grid
            self.subplot_grid_var.set(f"{grid[0]}x{grid[1]}")
            self.subplot_index_spin.configure(
                to=grid[0] * grid[1] - 1)
            self._rebuild_subplots()

        new_theme = s.get('settings', {}).get('theme')
        if not new_theme and s.get('theme') == 'dark':
            new_theme = 'dark'
        if not new_theme:
            new_theme = 'light'
        if new_theme != self.settings.get('theme'):
            try:
                self._apply_theme(new_theme)
            except Exception:
                if s.get('theme') == 'dark' and not self.dark_mode_var.get():
                    self.dark_mode_var.set(True)
                    self._toggle_dark_mode()

        new_lang = s.get('settings', {}).get('language', 'ru')
        if new_lang != tr.lang:
            self._switch_lang(new_lang)
        self._apply_font_settings()
        self._update_listbox()
        self._apply_canvas_settings()

    # ========================================================================
    # IO — .graphx
    # ========================================================================
    def _save_graphx(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".graphx",
            filetypes=[("GraphX project", "*.graphx"),
                       ("ZIP", "*.zip")])
        if not path:
            return
        try:
            data = [{k: v for k, v in d.items() if k != 'artist'}
                    for d in self.graphs_data]
            with tempfile.TemporaryDirectory() as td:
                jp = os.path.join(td, 'graph.json')
                with open(jp, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2,
                              default=lambda o: o.tolist()
                              if hasattr(o, 'tolist') else o)
                mp = os.path.join(td, GRAPHX_MANIFEST)
                with open(mp, 'w', encoding='utf-8') as f:
                    json.dump({
                        'app': APP_NAME,
                        'version': APP_VERSION,
                        'format': 'graphx',
                        'created': datetime.datetime.now().isoformat(),
                    }, f, ensure_ascii=False, indent=2)
                sp = os.path.join(td, 'settings.json')
                with open(sp, 'w', encoding='utf-8') as f:
                    json.dump({
                        'title': self.plot_title_var.get(),
                        'xlabel': self.plot_xlabel_var.get(),
                        'ylabel': self.plot_ylabel_var.get(),
                        'settings': self.settings,
                        'folders': self.folders,
                        'theme': self.settings.get('theme', 'light'),
                        'subplot_grid': [self.subplot_rows,
                                          self.subplot_cols],
                    }, f, ensure_ascii=False, indent=2)
                pp = os.path.join(td, 'plot.png')
                try:
                    self.fig.savefig(pp, dpi=200, bbox_inches='tight')
                except Exception:
                    pass
                with zipfile.ZipFile(path, 'w',
                                      zipfile.ZIP_DEFLATED) as zf:
                    zf.write(jp, 'graph.json')
                    zf.write(mp, GRAPHX_MANIFEST)
                    zf.write(sp, 'settings.json')
                    if os.path.exists(pp):
                        zf.write(pp, 'plot.png')
            self._show_history(tr.t('hist.saved_graphx',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _load_graphx(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("GraphX project", "*.graphx"),
                           ("ZIP", "*.zip")])
        if not path:
            return
        try:
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(td)
                mp = os.path.join(td, GRAPHX_MANIFEST)
                if os.path.exists(mp):
                    with open(mp, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    if manifest.get('format') != 'graphx':
                        if not messagebox.askyesno(
                                tr.t('msg.confirm'),
                                "Файл не является .graphx. Продолжить?"):
                            return
                jp = os.path.join(td, 'graph.json')
                if os.path.exists(jp):
                    self._load_json(jp)
                sp = os.path.join(td, 'settings.json')
                if os.path.exists(sp):
                    with open(sp, 'r', encoding='utf-8') as f:
                        self._apply_settings_dict(json.load(f))
            self._show_history(tr.t('hist.loaded_graphx',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ========================================================================
    # IO — .graphxanim
    # ========================================================================
    def _save_graphxanim(self):
        anim_name = tr.find_anim_by_display(self.anim_type_var.get())
        if anim_name == "Нет":
            messagebox.showinfo(tr.t('msg.info'),
                                 tr.t('msg.anim_no_type'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".graphxanim",
            filetypes=[("GraphX animation", "*.graphxanim")])
        if not path:
            return
        try:
            with tempfile.TemporaryDirectory() as td:
                ap = os.path.join(td, 'animation.json')
                with open(ap, 'w', encoding='utf-8') as f:
                    json.dump({
                        'anim_type': anim_name,
                        'speed': self.anim_speed_var.get(),
                        'frames_total': self.anim_frames_total,
                        'custom_expr': self.entry_custom_anim.get(),
                        'anim_params': self.anim_params,
                        'subplot_grid': [self.subplot_rows,
                                          self.subplot_cols],
                    }, f, ensure_ascii=False, indent=2)
                mp = os.path.join(td, GRAPHX_MANIFEST)
                with open(mp, 'w', encoding='utf-8') as f:
                    json.dump({
                        'app': APP_NAME,
                        'version': APP_VERSION,
                        'format': 'graphxanim',
                        'created': datetime.datetime.now().isoformat(),
                    }, f, ensure_ascii=False, indent=2)
                pp = os.path.join(td, 'preview.png')
                try:
                    self.fig.savefig(pp, dpi=120, bbox_inches='tight')
                except Exception:
                    pass
                with zipfile.ZipFile(path, 'w',
                                      zipfile.ZIP_DEFLATED) as zf:
                    zf.write(ap, 'animation.json')
                    zf.write(mp, GRAPHX_MANIFEST)
                    if os.path.exists(pp):
                        zf.write(pp, 'preview.png')
            self._show_history(tr.t('hist.anim_saved_file',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _load_graphxanim(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("GraphX animation", "*.graphxanim"),
                           ("JSON", "*.json")])
        if not path:
            return
        try:
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(td)
                ap = os.path.join(td, 'animation.json')
                if not os.path.exists(ap):
                    messagebox.showerror(tr.t('msg.error'),
                                          tr.t('msg.anim_no_file'))
                    return
                with open(ap, 'r', encoding='utf-8') as f:
                    a = json.load(f)
            anim_type = a.get('anim_type', 'Нет')
            self.anim_type_var.set(tr.anim_name(anim_type))
            self._on_anim_type_change()
            if 'speed' in a:
                self.anim_speed_var.set(a['speed'])
            if 'frames_total' in a:
                self.anim_frames_total = a['frames_total']
                try:
                    self.anim_progress.configure(
                        maximum=self.anim_frames_total)
                except Exception:
                    pass
            if 'custom_expr' in a:
                self.entry_custom_anim.delete(0, tk.END)
                self.entry_custom_anim.insert(0, a['custom_expr'])
            if 'anim_params' in a and isinstance(a['anim_params'], dict):
                self.anim_params.update(a['anim_params'])
            self._show_history(tr.t('hist.anim_loaded_file',
                                     name=os.path.basename(path)))
            if messagebox.askyesno(tr.t('msg.info'),
                                    tr.t('msg.anim_run_now')):
                self._start_animation()
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ========================================================================
    # IO — CSV
    # ========================================================================
    def _export_csv(self):
        if not self.graphs_data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, 'w', newline='',
                      encoding='utf-8') as f:
                w = csv.writer(f)
                for d in self.graphs_data:
                    w.writerow([f"# {d['label']} ({d['type']})"])
                    if "3D" in d['type']:
                        w.writerow(["X", "Y", "Z"])
                        for x, y, z in zip(d['x'], d['y'], d['z']):
                            w.writerow([x, y, z])
                    else:
                        w.writerow(["X", "Y"])
                        for x, y in zip(d['x'], d['y']):
                            w.writerow([x, y])
                    w.writerow([])
            self._show_history(tr.t('hist.exported_csv',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _export_folder_csv(self, folder_name):
        items = [d for d in self.graphs_data
                 if d.get('folder') == folder_name]
        if not items:
            messagebox.showinfo(tr.t('msg.info'),
                                 tr.t('msg.folder_empty'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{folder_name or 'root'}.csv")
        if not path:
            return
        try:
            with open(path, 'w', newline='',
                      encoding='utf-8') as f:
                w = csv.writer(f)
                for d in items:
                    w.writerow([f"# {d['label']} ({d['type']})"])
                    if "3D" in d['type']:
                        w.writerow(["X", "Y", "Z"])
                        for x, y, z in zip(d['x'], d['y'], d['z']):
                            w.writerow([x, y, z])
                    else:
                        w.writerow(["X", "Y"])
                        for x, y in zip(d['x'], d['y']):
                            w.writerow([x, y])
                    w.writerow([])
            self._show_history(tr.t('hist.exported_folder',
                                     name=folder_name))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _export_folder_json(self, folder_name):
        items = [{k: v for k, v in d.items() if k != 'artist'}
                 for d in self.graphs_data
                 if d.get('folder') == folder_name]
        if not items:
            messagebox.showinfo(tr.t('msg.info'),
                                 tr.t('msg.folder_empty'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile=f"{folder_name or 'root'}.json")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2,
                          default=lambda o: o.tolist()
                          if hasattr(o, 'tolist') else o)
            self._show_history(tr.t('hist.exported_folder',
                                     name=folder_name))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _import_csv(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                xd, yd, zd, is_3d = [], [], [], False
                for row in reader:
                    if not row or row[0].startswith("#"):
                        continue
                    if row[0] == "X":
                        is_3d = len(row) == 3 and row[2] == "Z"
                        continue
                    try:
                        xd.append(float(row[0].replace(',', '.')))
                        yd.append(float(row[1].replace(',', '.')))
                        if is_3d:
                            zd.append(float(row[2].replace(',', '.')))
                    except (ValueError, IndexError):
                        continue
            self.entry_x.delete(0, tk.END)
            self.entry_x.insert(0, ", ".join(map(str, xd)))
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, ", ".join(map(str, yd)))
            if is_3d:
                self.type_var.set(tr.type_name("3D Линия"))
                self._on_type_change()
                self.entry_z.delete(0, tk.END)
                self.entry_z.insert(0, ", ".join(map(str, zd)))
            else:
                self.type_var.set(tr.type_name("Линия"))
                self._on_type_change()
            self._show_history(tr.t('hist.imported_csv',
                                     count=len(xd)))
            self.status_var.set(tr.t('hist.imported_csv',
                                     count=len(xd)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.import_error'), str(e))

    # ========================================================================
    # ИЗОБРАЖЕНИЯ / HTML
    # ========================================================================
    def _save_image(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("SVG", "*.svg"),
                       ("PDF", "*.pdf")])
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=300, bbox_inches='tight')
            self._show_history(tr.t('hist.saved_image',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _export_html(self):
        if not self.graphs_data:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.no_data'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if not path:
            return
        try:
            import plotly.graph_objects as go
        except ImportError:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('msg.install_plotly'))
            return
        try:
            fig = go.Figure()
            for d in self.graphs_data:
                t = d['type']
                try:
                    if t == "Линия":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'], mode='lines+markers',
                            name=d['label'],
                            line=dict(color=d['color']),
                            fill='tozeroy' if d.get('fill') else None))
                    elif t == "Точечная":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'], mode='markers',
                            name=d['label'],
                            marker=dict(color=d['color'])))
                    elif t == "Столбчатая":
                        fig.add_trace(go.Bar(
                            x=d['x'], y=d['y'], name=d['label'],
                            marker=dict(color=d['color'])))
                    elif t == "Гистограмма":
                        fig.add_trace(go.Histogram(
                            x=d['x'], nbinsx=d.get('bins', 10),
                            name=d['label'],
                            marker=dict(color=d['color'])))
                    elif t == "Круговая":
                        labels = (d.get('pie_labels')
                                  or [str(i) for i in d['x']])
                        fig.add_trace(go.Pie(labels=labels,
                                              values=d['y'],
                                              name=d['label']))
                    elif t in ("Heatmap", "Contour", "Imshow"):
                        z = d.get('heatmap_data', [])
                        if z:
                            fig.add_trace(go.Heatmap(z=z,
                                                      name=d['label']))
                    elif t == "Box plot":
                        for i, g in enumerate(d.get('box_data', [])):
                            fig.add_trace(go.Box(
                                y=g,
                                name=f"{d['label']} #{i+1}",
                                marker_color=d['color']))
                    elif t == "Violin":
                        for i, g in enumerate(d.get('box_data', [])):
                            fig.add_trace(go.Violin(
                                y=g,
                                name=f"{d['label']} #{i+1}",
                                marker_color=d['color']))
                    elif t == "Treemap":
                        parents = (d.get('treemap_parents')
                                   or [''] * len(d['x']))
                        labels = (d.get('pie_labels')
                                  or [str(i) for i in d['x']])
                        fig.add_trace(go.Treemap(labels=labels,
                                                  parents=parents,
                                                  values=d['y'],
                                                  name=d['label']))
                    elif t == "Sunburst":
                        parents = (d.get('treemap_parents')
                                   or [''] * len(d['x']))
                        labels = (d.get('pie_labels')
                                  or [str(i) for i in d['x']])
                        fig.add_trace(go.Sunburst(labels=labels,
                                                   parents=parents,
                                                   values=d['y'],
                                                   name=d['label']))
                    elif t == "Полигон":
                        fig.add_trace(go.Scatter(
                            x=list(d['x']) + [d['x'][0]],
                            y=list(d['y']) + [d['y'][0]],
                            fill='toself', mode='lines',
                            name=d['label'],
                            line=dict(color=d['color'])))
                    elif t == "Кольцевая":
                        labels = (d.get('pie_labels')
                                  or [str(i) for i in d['x']])
                        fig.add_trace(go.Pie(labels=labels,
                                              values=d['y'],
                                              hole=0.4,
                                              name=d['label']))
                    elif t == "Радиальная":
                        theta_rad = [np.deg2rad(a) for a in d['x']]
                        fig.add_trace(go.Barpolar(
                            r=d['y'], theta=theta_rad,
                            name=d['label'],
                            marker_color=d['color']))
                    elif t == "Столбчатая с накоплением":
                        for i, s in enumerate(d.get('box_data', [])):
                            fig.add_trace(go.Bar(
                                x=d['x'][:len(s)], y=s,
                                name=f"{d['label']} #{i+1}",
                                marker_color=d['color']
                                if i == 0 else None))
                        fig.update_layout(barmode='stack')
                    elif t == "Полярный scatter":
                        theta_rad = [np.deg2rad(a) for a in d['x']]
                        fig.add_trace(go.Scatterpolar(
                            r=d['y'],
                            theta=np.rad2deg(theta_rad),
                            mode='markers', name=d['label'],
                            marker=dict(
                                color=d['color'],
                                size=max(4, int(d.get('ms', 6))))))
                    elif t == "Пузырьковая":
                        sizes = d.get('z', [])
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'], mode='markers',
                            name=d['label'],
                            marker=dict(
                                color=d['color'], size=sizes,
                                sizemode='area',
                                sizeref=2.0 * max(sizes) / (60 ** 2)
                                if sizes and max(sizes) > 0 else 1,
                                sizemin=4,
                                line=dict(color='black', width=0.5))))
                    elif t == "3D Поверхность":
                        z = d.get('heatmap_data', [])
                        if z:
                            fig.add_trace(go.Surface(
                                z=z, name=d['label'],
                                colorscale='Viridis'))
                    elif t == "3D Сетка":
                        z = d.get('heatmap_data', [])
                        if z:
                            fig.add_trace(go.Surface(
                                z=z, name=d['label'],
                                colorscale='Viridis',
                                hidesurface=True, showscale=False))
                    elif t == "3D Линия":
                        fig.add_trace(go.Scatter3d(
                            x=d['x'], y=d['y'], z=d['z'],
                            mode='lines+markers', name=d['label']))
                    elif t == "3D Точечная":
                        fig.add_trace(go.Scatter3d(
                            x=d['x'], y=d['y'], z=d['z'],
                            mode='markers', name=d['label']))
                    elif t == "3D Полигон":
                        xs = list(d['x']) + [d['x'][0]]
                        ys = list(d['y']) + [d['y'][0]]
                        zs = list(d['z']) + [d['z'][0]]
                        fig.add_trace(go.Scatter3d(
                            x=xs, y=ys, z=zs,
                            mode='lines+markers',
                            name=d['label'],
                            line=dict(color=d['color'], width=4),
                            marker=dict(size=5)))
                    elif t == "3D Триангуляция":
                        fig.add_trace(go.Mesh3d(
                            x=d['x'], y=d['y'], z=d['z'],
                            name=d['label'], colorscale='Viridis',
                            opacity=0.85, intensity=d['z'],
                            delaunayaxis='z'))

                    # ------------------- [NEW] Водопад / Гант -------------------
                    elif t == "Водопад":
                        vals = list(d['y'])
                        labels = d.get('pie_labels') or \
                            [str(i) for i in range(len(vals))]
                        fig.add_trace(go.Waterfall(
                            x=list(labels) + ['Total'],
                            measure=['relative'] * len(vals) + ['total'],
                            y=vals + [0],
                            name=d['label']))
                    elif t == "Гант":
                        starts = list(d['x'])
                        durs = list(d['y'])
                        labels = d.get('pie_labels') or \
                            [f"Task {i+1}" for i in range(len(starts))]
                        fig.add_trace(go.Bar(
                            x=durs, y=labels,
                            orientation='h',
                            base=starts,
                            name=d['label'],
                            marker_color=d['color']))
                        fig.update_layout(barmode='overlay')
                except Exception:
                    continue
            fig.update_layout(title=self.plot_title_var.get(),
                              xaxis_title=self.plot_xlabel_var.get(),
                              yaxis_title=self.plot_ylabel_var.get())
            fig.write_html(path, include_plotlyjs='cdn')
            self._show_history(tr.t('hist.saved_html',
                                     name=os.path.basename(path)))
            messagebox.showinfo(tr.t('msg.done'),
                                tr.t('msg.html_saved', path=path))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _export_excel(self):
        """Экспорт всех объектов в Excel: один лист на объект."""
        if not self.graphs_data:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.no_data'))
            return
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('excel.install_openpyxl'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            wb = openpyxl.Workbook()
            wb.remove(wb.active)

            for i, d in enumerate(self.graphs_data):
                base = re.sub(r'[\\/*?:\[\]]', '_',
                               d['label'])[:28] or f"Sheet{i+1}"
                sheet_name = base
                j = 1
                while sheet_name in wb.sheetnames:
                    j += 1
                    sheet_name = f"{base[:26]}_{j}"
                ws = wb.create_sheet(sheet_name)

                t = d['type']
                if t in ("Heatmap", "Contour", "Imshow",
                          "3D Поверхность", "3D Сетка"):
                    for row in d.get('heatmap_data', []):
                        ws.append(list(row))
                elif t in ("Box plot", "Violin",
                            "Вложенная круговая", "Мозаика",
                            "Столбчатая с накоплением"):
                    groups = d.get('box_data', [])
                    max_g = max((len(g) for g in groups), default=0)
                    for r in range(max_g):
                        ws.append([g[r] if r < len(g) else None
                                   for g in groups])
                elif "3D" in t:
                    ws.append(["X", "Y", "Z"])
                    for x, y, z in zip(d['x'], d['y'], d['z']):
                        ws.append([x, y, z])
                else:
                    ws.append(["X", "Y"])
                    for x, y in zip(d['x'], d['y']):
                        ws.append([x, y])

            wb.save(path)
            self._show_history(tr.t('excel.exported',
                                     name=os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    def _import_excel(self, path=None):
        """Импорт данных из Excel в форму."""
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror(tr.t('msg.error'),
                                  tr.t('excel.install_openpyxl'))
            return
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("Excel", "*.xlsx"), ("All", "*.*")])
        if not path:
            return
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as e:
            messagebox.showerror(tr.t('excel.bad_file'), str(e))
            return

        pick = tk.Toplevel(self.root)
        pick.title(tr.t('excel.sheet_choose'))
        pick.transient(self.root)
        pick.geometry("320x240")
        ttk.Label(pick, text=tr.t('excel.sheet_choose')).pack(
            padx=10, pady=(10, 4))
        lb = tk.Listbox(pick, height=7)
        lb.pack(fill=tk.BOTH, expand=True, padx=10)
        for name in wb.sheetnames:
            lb.insert(tk.END, name)
        lb.selection_set(0)

        def proceed():
            sel = lb.curselection()
            if not sel:
                return
            sheet_name = wb.sheetnames[sel[0]]
            pick.destroy()
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return

            first = [str(c).strip().lower() if c is not None else ''
                     for c in rows[0]]
            has_header = any(h in ('x', 'y', 'z', 'yerr', 'err')
                              for h in first)
            data = rows[1:] if has_header else rows

            cols_data = {}
            if has_header:
                for i, h in enumerate(first):
                    if h in ('x', 'y', 'z', 'yerr', 'err'):
                        key = 'yerr' if h == 'err' else h
                        vals = [r[i] for r in data
                                if i < len(r) and r[i] is not None]
                        cols_data[key] = vals
            else:
                n_cols = len(rows[0])
                if n_cols == 1:
                    cols_data['y'] = [r[0] for r in data
                                       if r[0] is not None]
                elif n_cols == 2:
                    cols_data['x'] = [r[0] for r in data
                                       if r[0] is not None]
                    cols_data['y'] = [r[1] for r in data
                                       if r[1] is not None]
                else:
                    cols_data['x'] = [r[0] for r in data
                                       if r[0] is not None]
                    cols_data['y'] = [r[1] for r in data
                                       if r[1] is not None]
                    cols_data['z'] = [r[2] for r in data
                                       if r[2] is not None]

            def fmt_num(v):
                if isinstance(v, float) and v.is_integer():
                    return str(int(v))
                return str(v)

            n = 0
            for key, vals in cols_data.items():
                entry = getattr(self, f'entry_{key}', None)
                if entry is None:
                    continue
                entry.delete(0, tk.END)
                entry.insert(0, ", ".join(fmt_num(v) for v in vals))
                n = len(vals)

            # Автовыбор типа
            if 'z' in cols_data and 'x' in cols_data:
                self.type_var.set(tr.type_name("3D Линия"))
            else:
                self.type_var.set(tr.type_name("Линия"))
            self._on_type_change()

            self._show_history(tr.t('excel.imported', n=n))
            self.notebook.select(0)

        ttk.Button(pick, text=tr.t('excel.apply'),
                    command=proceed).pack(pady=10)
        pick.bind('<Return>', lambda e: proceed())
        pick.bind('<Escape>', lambda e: pick.destroy())
