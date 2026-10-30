"""Ввод/вывод, tooltip, crosshair, drag, группы, папки, генераторы, экспорт."""
import os
import re
import csv
import json
import zipfile
import tempfile
import datetime

import tkinter as tk
import numpy as np

from tkinter import ttk, messagebox, colorchooser, filedialog, simpledialog
from mpl_toolkits.mplot3d import proj3d

from translator import tr
from settings import (UNIT_TO_M, APP_NAME, APP_VERSION, GRAPHX_MANIFEST)


class IOMixin:

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

    _TOOLTIP_SKIP = (
        "Круговая", "Heatmap", "Contour", "Imshow",
        "Box plot", "Violin", "Treemap", "Sunburst",
        "Мозаика", "Радиальная", "Столбчатая с накоплением",
        "Вложенная круговая", "Полигон", "Кольцевая",
        "Полярный scatter", "Пузырьковая", "Quiver",
        "Водопад", "Гант", "Renko", "Point-and-Figure",
        "Q-Q plot", "Ridge plot", "Strip plot",
        "Raincloud plot", "Beanplot", "Swarm plot",
        "Cherry blossom plot", "Dot-and-whisker",
        "Свечи (OHLC)", "Диаграмма Парето",
        "Дендрограмма", "Cluster dendrogram",
        "Sankey", "Alluvial diagram", "Chord",
        "Сетевой график", "Hive plot", "Arc diagram",
        "Дерево (tree diagram)", "Circle packing",
        "Adjacency matrix", "Mapper algorithm",
        "Hexbin", "Stream plot", "Streamlines",
        "Bode plot", "Smith chart", "Nyquist plot",
        "Root locus", "Constellation diagram",
        "Ribbon plot 3D", "Waterfall spectrogram 3D",
        "Riemann surface 3D", "Joyplot 3D", "Isosurface 3D",
        "Choropleth", "Flow map", "Isopleth", "Cartogram",
        "Dot density map", "Hodograph", "Роза ветров",
        "Skew-T log-P", "Thermodynamic diagram",
        "Диаграмма Вороного", "Выпуклая оболочка", "Alpha shape",
        "Volcano plot", "ROC curve", "Manhattan plot",
        "MA plot", "Recurrence plot", "Cobweb plot",
        "Poincaré plot", "Phase portrait",
        "Dot plot", "Lollipop", "Пирамида", "Sparkline",
        "Cycle plot", "Bump chart", "Slopegraph",
        "Dumbbell plot", "Bar of pie", "Ribbon plot 2D",
        "Bullet chart", "Funnel chart",
        "Календарная теплокарта", "Полярная теплокарта",
        "Диаграмма бифуркаций", "Parallel coordinates",
        "Radar chart", "Спидометр",
        "Вафельная диаграмма", "Сосулька (icicle)",
        "Диаграмма Аргана", "Диаграмма Тейлора",
        "Горизонтальная столбчатая", "Горизонтальная линия",
        "Pie of pie", "Топографический профиль",
        "Вейвлет-скейлограмма",
    )

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
        skip = self._TOOLTIP_SKIP
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

        # --- Обновлено: X, Y, sin, cos ---
        if len(best) == 4:
            xv, yv, lbl, note = best
            sin_val = np.sin(yv)
            cos_val = np.cos(yv)
            text = (f"{lbl}\n"
                    f"X: {xv:.4g}\n"
                    f"Y: {yv:.4g}\n"
                    f"sin(Y): {sin_val:.3f}\n"
                    f"cos(Y): {cos_val:.3f}")
            if note: text += f"\n💬 {note}"

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
        subplot_idx = self.axes.index(ax) if ax in self.axes else 0
        for d in self.graphs_data:
            if d.get('subplot_index', 0) != subplot_idx:
                continue
            if d['type'] in ("Radial tree 3D", "3D Quiver",
                             "Riemann surface 3D", "Isosurface 3D",
                             "Waterfall spectrogram 3D"):
                return
        try:
            ax.M = ax.get_proj()
            x3, y3, _ = proj3d.inv_transform(event.xdata,
                                              event.ydata, ax.M)
        except Exception:
            return
        best = None
        best_d2 = float('inf')
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
                    best = (xi, yi, zi, d['label'], d.get('notes', ''))
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

        # --- Обновлено: X, Y, Z, sin, cos ---
        xv, yv, zv, lbl, note = best
        sin_val = np.sin(zv)
        cos_val = np.cos(zv)
        text = (f"{lbl}\n"
                f"X: {xv:.4g}\n"
                f"Y: {yv:.4g}\n"
                f"Z: {zv:.4g}\n"
                f"sin(Z): {sin_val:.3f}\n"
                f"cos(Z): {cos_val:.3f}")
        if note: text += f"\n💬 {note}"

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
    # ЛИНЕЙКА (MEASURE TOOL)
    # ========================================================================
    def _toggle_measure(self):
        self.measure_mode = self.measure_var.get()
        if not self.measure_mode:
            if hasattr(self, '_measure_artist') and self._measure_artist:
                try: self._measure_artist.remove()
                except: pass
            if hasattr(self, '_measure_text') and self._measure_text:
                try: self._measure_text.remove()
                except: pass
            self._measure_pt1 = None
            self.canvas.draw_idle()

    def _on_press_measure(self, event):
        if not getattr(self, 'measure_mode', False):
            return
        if event.inaxes is None or event.xdata is None:
            return

        if not hasattr(self, '_measure_pt1'):
            self._measure_pt1 = None

        # Первая точка
        if self._measure_pt1 is None:
            self._measure_pt1 = (event.xdata, event.ydata)
            self.status_var.set("Линейка: выберите вторую точку")
            return

        # Вторая точка — рисуем
        x1, y1 = self._measure_pt1
        x2, y2 = event.xdata, event.ydata

        # Удаляем старую линию
        if hasattr(self, '_measure_artist') and self._measure_artist:
            try: self._measure_artist.remove()
            except: pass
        if hasattr(self, '_measure_text') and self._measure_text:
            try: self._measure_text.remove()
            except: pass

        ax = event.inaxes
        dx = x2 - x1
        dy = y2 - y1
        dist = np.hypot(dx, dy)

        self._measure_artist = ax.annotate(
            '', xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle='<->', color='red', lw=1.5),
            zorder=999
        )

        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        text = f"ΔX={dx:.3g}\nΔY={dy:.3g}\nДлина={dist:.3g}"

        self._measure_text = ax.text(
            mid_x, mid_y, text,
            bbox=dict(boxstyle="round", fc="white", ec="red", alpha=0.9),
            fontsize=9, ha='center', va='center', color='red', zorder=1000
        )

        self._measure_pt1 = None  # Сброс
        self.canvas.draw_idle()

    # ========================================================================
    # INLINE-РЕДАКТОР
    # ========================================================================
    def _on_inline_edit_press(self, event):
        if event.button != 1 or event.inaxes is None:
            return
        if event.dblclick is False:
            return
        if event.xdata is None or event.ydata is None:
            return

        ax = event.inaxes
        if hasattr(ax, 'get_zlim'):
            return
        ex, ey = event.xdata, event.ydata
        subplot_idx = self.axes.index(ax) if ax in self.axes else 0

        best = None
        best_d2 = float('inf')
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
                    best = (i, j, xi, yi)

        if best is None:
            return

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        thresh = 0.003 * ((xlim[1] - xlim[0]) ** 2
                          + (ylim[1] - ylim[0]) ** 2)
        if best_d2 > thresh:
            return

        obj_idx, pt_idx, xi, yi = best

        try:
            x_px, y_px = ax.transData.transform((xi, yi))
        except Exception:
            return
        canvas = self.canvas.get_tk_widget()
        canvas_h = canvas.winfo_height()
        y_tk = int(canvas_h - y_px)

        entry = tk.Entry(canvas, width=12, font=('Consolas', 10),
                          justify='center',
                          bg='#ffffcc', fg='#000000',
                          relief='solid', borderwidth=1)
        entry.place(x=int(x_px) - 40, y=y_tk - 25, width=80)
        entry.insert(0, f"{yi:g}")
        entry.select_range(0, tk.END)
        entry.focus_set()

        def _commit(event=None):
            try:
                new_val = float(entry.get().replace(',', '.'))
            except ValueError:
                entry.destroy()
                return
            self._snapshot(
                f"Точка #{pt_idx}: Y {yi:.4g} → {new_val:.4g}")
            self.graphs_data[obj_idx]['y'][pt_idx] = new_val
            self._destroy_object(self.graphs_data[obj_idx])
            self.graphs_data[obj_idx]['artist'] = self._create_artist(
                self.graphs_data[obj_idx])
            self._redraw()
            entry.destroy()

        def _cancel(event=None):
            entry.destroy()

        entry.bind('<Return>', _commit)
        entry.bind('<Escape>', _cancel)
        entry.bind('<FocusOut>', _cancel)

    # ========================================================================
    # ДАННЫЕ / БУФЕР / DROP
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
            try:
                self._load_autosave(path)
            except Exception:
                pass

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
            self._destroy_object(self.graphs_data[idx])
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
            self._destroy_object(self.graphs_data[idx])
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
            self._destroy_object(self.graphs_data[idx])
            self.graphs_data[idx]['artist'] = self._create_artist(
                self.graphs_data[idx])
        self._update_listbox()
        self._redraw()

    def _export_selected_json(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        items = [{k: v for k, v in self.graphs_data[i].items()
                  if k not in ('artist', '_extra_artists', '_cleanup')}
                 for i in sel]
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
            new = {k: v for k, v in src.items()
                   if k not in ('artist', '_extra_artists', '_cleanup')}
            for key in ('x', 'y', 'z', 'pie_labels', 'pie_colors',
                        'yerr', 'treemap_parents', 'col_labels',
                        'dst_labels'):
                if key in src:
                    new[key] = list(src[key])
            new['box_data'] = [list(g) for g in src.get('box_data', [])]
            new['heatmap_data'] = [list(r)
                                    for r in src.get('heatmap_data', [])]
            new['yerr_matrix'] = [list(r)
                                   for r in src.get('yerr_matrix', [])]
            new['label'] = src['label'] + " (copy)"
            new['artist'] = None
            new['_extra_artists'] = []
            new['_cleanup'] = None
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
                    self._destroy_object(d)
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
    # DRAG ТОЧЕК МЫШЬЮ
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
        self._destroy_object(data)
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
    # IO — JSON
    # ========================================================================
    def _save_json(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = [{k: v for k, v in d.items()
                 if k not in ('artist', '_extra_artists', '_cleanup')}
                for d in self.graphs_data]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4,
                          allow_nan=False,
                          default=lambda o: o.tolist()
                          if isinstance(o, np.ndarray) else o)
            if getattr(self, 'current_doc_idx', -1) >= 0:
                doc = self.documents[self.current_doc_idx]
                doc.path = path
                doc.modified = False
                doc.name = os.path.splitext(os.path.basename(path))[0]
            if hasattr(self, '_update_window_title'):
                self._update_window_title()
            self._show_history(tr.t('hist.saved_json',
                                     name=os.path.basename(path)))
            self.status_var.set(tr.t('hist.saved_json', name=path))
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
                             ('heatmap_data', []), ('yerr_matrix', []),
                             ('folder', ''),
                             ('smooth', False), ('fill', False),
                             ('glow', False), ('notes', ''),
                             ('treemap_parents', []),
                             ('subplot_index', 0),
                             ('unit_x', '—'), ('unit_y', '—'),
                             ('unit_z', '—'),
                             ('visible', True),
                             ('_extra_artists', []), ('_cleanup', None)]:
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
            if getattr(self, 'current_doc_idx', -1) >= 0:
                doc = self.documents[self.current_doc_idx]
                doc.path = path
                doc.modified = False
                doc.name = os.path.splitext(os.path.basename(path))[0]
            if hasattr(self, '_update_window_title'):
                self._update_window_title()
            self._show_history(tr.t('hist.loaded_json',
                                     name=os.path.basename(path)))
            self.status_var.set(tr.t('hist.loaded_json', name=path))
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            data = [{k: v for k, v in d.items()
                     if k not in ('artist', '_extra_artists', '_cleanup')}
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            data = [{k: v for k, v in d.items()
                     if k not in ('artist', '_extra_artists', '_cleanup')}
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            if getattr(self, 'current_doc_idx', -1) >= 0:
                doc = self.documents[self.current_doc_idx]
                doc.path = path
                doc.modified = False
                doc.name = os.path.splitext(os.path.basename(path))[0]
            if hasattr(self, '_update_window_title'):
                self._update_window_title()
            self._show_history(tr.t('hist.loaded_graphx',
                                     name=os.path.basename(path)))
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
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
        items = [{k: v for k, v in d.items()
                  if k not in ('artist', '_extra_artists', '_cleanup')}
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
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror(tr.t('msg.import_error'), str(e))

    # ========================================================================
    # IO — ИЗОБРАЖЕНИЕ
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

    # ========================================================================
    # IO — HTML (Plotly)
    # ========================================================================
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
        skipped = []
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
                    elif t == "ECDF":
                        y_arr = np.sort(np.array(d['y'], dtype=float))
                        xs = np.concatenate([[y_arr[0]], y_arr])
                        ys = np.concatenate([[0],
                                              np.arange(1, len(y_arr) + 1)
                                              / len(y_arr)])
                        fig.add_trace(go.Scatter(
                            x=xs.tolist(), y=ys.tolist(),
                            mode='lines', name=d['label'],
                            line_shape='hv'))
                    elif t == "Step plot":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'],
                            mode='lines', name=d['label'],
                            line_shape='hv'))
                    elif t == "Strip plot":
                        rng = np.random.default_rng(42)
                        for i, g in enumerate(d.get('box_data', [])):
                            g_arr = np.array(g, dtype=float)
                            jitter = rng.normal(0, 0.06, size=len(g_arr))
                            fig.add_trace(go.Scatter(
                                x=(np.full_like(g_arr, i) + jitter).tolist(),
                                y=g_arr.tolist(),
                                mode='markers', name=f"{d['label']} #{i+1}"))
                    elif t == "Свечи (OHLC)":
                        groups = d.get('box_data', [])
                        if len(groups) >= 4:
                            fig.add_trace(go.Candlestick(
                                x=d['x'],
                                open=groups[0],
                                high=groups[1],
                                low=groups[2],
                                close=groups[3],
                                name=d['label']))
                    elif t == "Диаграмма Парето":
                        y_arr = np.array(d['y'], dtype=float)
                        order = np.argsort(-y_arr)
                        ys = y_arr[order]
                        xs = [d['x'][i] for i in order]
                        cum = np.cumsum(ys) / ys.sum() * 100
                        fig.add_trace(go.Bar(x=xs, y=ys.tolist(),
                                              name=d['label']))
                        fig.add_trace(go.Scatter(
                            x=xs, y=cum.tolist(),
                            mode='lines+markers', name='Cum %',
                            yaxis='y2'))
                        fig.update_layout(
                            yaxis2=dict(overlaying='y', side='right',
                                         range=[0, 105]))
                    elif t == "Manhattan plot":
                        z_vals = d.get('z', [])
                        if z_vals and len(z_vals) == len(d['x']):
                            chroms = np.array(z_vals, dtype=float)
                            unique_c = np.unique(chroms)
                            colors_ = ['#1f77b4', '#ff7f0e',
                                        '#2ca02c', '#d62728',
                                        '#9467bd', '#8c564b',
                                        '#e377c2', '#7f7f7f']
                            offset = 0.0
                            for i, c_ in enumerate(unique_c):
                                mask = chroms == c_
                                xs = np.array(d['x'])[mask]
                                ys = np.array(d['y'])[mask]
                                span = (xs.max() - xs.min()
                                        if len(xs) > 1 else 1.0)
                                fig.add_trace(go.Scatter(
                                    x=(xs - xs.min() + offset).tolist(),
                                    y=ys.tolist(),
                                    mode='markers',
                                    name=f"Chr {int(c_)}",
                                    marker=dict(
                                        color=colors_[i % len(colors_)],
                                        size=4)))
                                offset += span * 1.1
                        else:
                            fig.add_trace(go.Scatter(
                                x=d['x'], y=d['y'],
                                mode='markers',
                                name=d['label'],
                                marker=dict(color=d['color'],
                                             size=4)))
                    elif t == "MA plot":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'], mode='markers',
                            name=d['label'],
                            marker=dict(color=d['color'],
                                         size=6, opacity=0.6)))
                        fig.add_hline(y=0, line_dash='dash',
                                       line_color='red')
                    elif t == "Swarm plot":
                        for i, g in enumerate(d.get('box_data', [])):
                            g_arr = np.array(g, dtype=float)
                            rng_ = np.random.default_rng(42 + i)
                            jitter = rng_.normal(0, 0.08,
                                                   size=len(g_arr))
                            labels_ = d.get('pie_labels', [])
                            lbl_ = (labels_[i]
                                    if i < len(labels_)
                                    else f"G{i+1}")
                            fig.add_trace(go.Scatter(
                                x=(np.full_like(g_arr, i) +
                                    jitter).tolist(),
                                y=g_arr.tolist(),
                                mode='markers',
                                name=str(lbl_),
                                marker=dict(color=d['color'],
                                             size=6,
                                             opacity=0.6)))
                    elif t == "Cherry blossom plot":
                        for i, g in enumerate(d.get('box_data', [])):
                            g_arr = np.array(g, dtype=float)
                            labels_ = d.get('pie_labels', [])
                            lbl_ = (labels_[i]
                                    if i < len(labels_)
                                    else f"G{i+1}")
                            fig.add_trace(go.Box(
                                y=g_arr.tolist(),
                                name=str(lbl_),
                                marker_color=d['color']))
                    elif t == "Ribbon plot 2D":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'],
                            mode='lines',
                            name=f"{d['label']} (верх)",
                            line=dict(color=d['color'])))
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d.get('z', []),
                            mode='lines',
                            name=f"{d['label']} (низ)",
                            line=dict(color=d['color'],
                                       dash='dash'),
                            fill='tonexty',
                            fillcolor=d['color']))
                    # === НОВЫЕ ТИПЫ ===
                    elif t == "Горизонтальная столбчатая":
                        fig.add_trace(go.Bar(
                            x=d['y'], y=d['x'],
                            orientation='h',
                            name=d['label'],
                            marker=dict(color=d['color'])))
                    elif t == "Горизонтальная линия":
                        fig.add_trace(go.Scatter(
                            x=d['y'], y=d['x'],
                            mode='lines+markers',
                            name=d['label'],
                            line=dict(color=d['color'])))
                    elif t == "Pie of pie":
                        labels = d.get('pie_labels') or \
                            [f"C{i+1}" for i in range(len(d['y']))]
                        fig.add_trace(go.Pie(
                            labels=labels, values=d['y'],
                            hole=0.35, name=d['label']))
                    elif t == "Топографический профиль":
                        fig.add_trace(go.Scatter(
                            x=d['x'], y=d['y'],
                            mode='lines', name=d['label'],
                            line=dict(color=d['color']),
                            fill='tozeroy'))
                    else:
                        skipped.append(t)
                except Exception:
                    skipped.append(t)
                    continue
            fig.update_layout(title=self.plot_title_var.get(),
                              xaxis_title=self.plot_xlabel_var.get(),
                              yaxis_title=self.plot_ylabel_var.get())
            fig.write_html(path, include_plotlyjs='cdn')
            msg = tr.t('msg.html_saved', path=path)
            if skipped:
                msg += f"\n\nПропущены типы (нет поддержки HTML):\n" \
                       f"{', '.join(sorted(set(skipped)))}"
            self._show_history(tr.t('hist.saved_html',
                                     name=os.path.basename(path)))
            messagebox.showinfo(tr.t('msg.done'), msg)
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ========================================================================
    # IO — EXCEL
    # ========================================================================
    def _export_excel(self):
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
                          "3D Поверхность", "3D Сетка", "Chord",
                          "Дендрограмма", "Stream plot"):
                    for row in d.get('heatmap_data', []):
                        ws.append(list(row))
                elif t in ("Box plot", "Violin",
                            "Вложенная круговая", "Мозаика",
                            "Столбчатая с накоплением", "Свечи (OHLC)",
                            "Strip plot", "Ridge plot"):
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

            if 'z' in cols_data and 'x' in cols_data:
                self.type_var.set(tr.type_name("3D Линия"))
            else:
                self.type_var.set(tr.type_name("Линия"))
            self._on_type_change()

            self._show_history(tr.t('excel.imported', n=n))
            self.notebook.select(0)
            try:
                self._push_recent(path)
                self._save_config()
            except Exception:
                pass

        ttk.Button(pick, text=tr.t('excel.apply'),
                    command=proceed).pack(pady=10)
        pick.bind('<Return>', lambda e: proceed())
        pick.bind('<Escape>', lambda e: pick.destroy())