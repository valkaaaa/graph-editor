"""Операции с объектами: add/update/delete, list/redraw, type_change,
тренды, аппроксимации, пики, статистика, undo/redo.
"""
import numpy as np
import tkinter as tk

from tkinter import messagebox
from translator import tr


class ExtrasMixin:

    # ========================================================================
    # НОВЫЕ МЕТОДЫ (плагины)
    # ========================================================================
    def _add_plugin_graph(self, t):
        """Создание объекта для плагинного типа."""
        td = self.plugin_registry.chart_types[t]

        x_data = self._parse_data(self.entry_x.get()) or []
        y_data = self._parse_data(self.entry_y.get()) or []
        z_data = self._parse_data(self.entry_z.get()) or []
        yerr_data = self._parse_data(self.entry_yerr.get()) or []
        pie_labels = [s.strip()
                      for s in self.entry_pie.get().split(',')
                      if s.strip()]
        pie_colors = [s.strip()
                      for s in self.entry_pie_colors.get().split(',')
                      if s.strip()]

        if 'x' in td.fields and not x_data and 'y' in td.fields:
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.bad_format'))
            return
        if 'y' in td.fields and not y_data:
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.bad_format_y'))
            return

        self._snapshot(tr.t('hist.added_graph',
                            name=self.entry_label.get() or t))
        self.line_counter += 1
        d = self._default_data(
            t, x_data, y_data, z_data if z_data else None,
            label=(self.entry_label.get()
                   or f"{tr.type_name(t)} {self.line_counter}"),
            color=self.color_var.get(),
            lw=self.lw_var.get(), ls=self.ls_var.get(),
            ms=self.ms_var.get(), marker=self.marker_var.get(),
            pie_labels=pie_labels, pie_colors=pie_colors,
            yerr=yerr_data, bins=self.bins_var.get(),
            subplot_index=self.subplot_index_var.get(),
            notes=self.entry_notes.get(),
            use_y2=self.use_y2_var.get(),
            fill=self.fill_var.get(), glow=self.glow_var.get(),
            unit_x=self.unit_x_var.get(),
            unit_y=self.unit_y_var.get(),
            unit_z=self.unit_z_var.get(),
        )
        d.update(td.extra_defaults or {})

        d['artist'] = self._create_artist(d)
        self.graphs_data.append(d)
        self._update_listbox()
        self._redraw()
        self._refresh_stats()

    def _show_plugin_fields(self, t):
        """Показывает поля формы для плагинного типа."""
        td = self.plugin_registry.chart_types[t]
        field_to_frame = {
            'x': self.frame_x, 'y': self.frame_y, 'z': self.frame_z,
            'yerr': self.frame_yerr,
            'pie_labels': self.frame_pie_labels,
            'pie_colors': self.frame_pie_colors,
            'bins': self.frame_bins,
            'treemap_parents': self.frame_treemap,
            'y2': self.frame_y2_check,
            'fill': self.frame_fill, 'glow': self.frame_glow,
        }
        for f in td.fields:
            fr = field_to_frame.get(f)
            if fr is not None:
                fr.pack(fill=tk.X)
        hint = td.hint.get(tr.lang) or td.hint.get('en') or ''
        self.hint_label.config(text=hint)
        if hint:
            self.frame_hint.pack(fill=tk.X)

    def _load_plugin_to_form(self, data):
        """Загрузка объекта плагинного типа обратно в форму."""
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, ", ".join(map(str, data.get('x', []))))
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, ", ".join(map(str, data.get('y', []))))
        self.entry_z.delete(0, tk.END)
        zv = data.get('z', [])
        if isinstance(zv, str):
            self.entry_z.insert(0, zv)
        else:
            self.entry_z.insert(0, ", ".join(map(str, zv)))
        self.entry_yerr.delete(0, tk.END)
        self.entry_yerr.insert(0, ", ".join(map(str, data.get('yerr', []))))
        self.entry_pie.delete(0, tk.END)
        self.entry_pie.insert(0, ", ".join(data.get('pie_labels', [])))
        self.entry_pie_colors.delete(0, tk.END)
        self.entry_pie_colors.insert(0, ", ".join(data.get('pie_colors', [])))
        if 'bins' in data:
            self.bins_var.set(data['bins'])
        self.use_y2_var.set(data.get('use_y2', False))
        self.fill_var.set(data.get('fill', False))
        self.glow_var.set(data.get('glow', False))
        self.subplot_index_var.set(data.get('subplot_index', 0))
        self.unit_x_var.set(data.get('unit_x', '—'))
        self.unit_y_var.set(data.get('unit_y', '—'))
        self.unit_z_var.set(data.get('unit_z', '—'))
        self.entry_label.delete(0, tk.END)
        self.entry_label.insert(0, data.get('label', ''))
        self.entry_notes.delete(0, tk.END)
        self.entry_notes.insert(0, data.get('notes', ''))
        self.color_var.set(data.get('color', 'blue'))
        self.lw_var.set(data.get('lw', 2.0))
        self.ls_var.set(data.get('ls', '-'))
        self.ms_var.set(data.get('ms', 6.0))
        self.marker_var.set(data.get('marker', 'o'))
        self.notebook.select(0)

    def _load_selected_to_form(self):
        """Загружает выбранный объект дерева обратно в форму «Создание».

        Обрабатывает:
          - обычные типы (x/y/z/yerr, box_data, heatmap_data, yerr_matrix);
          - плагинные типы — делегирует в _load_plugin_to_form;
          - специальные поля — pie_labels/pie_colors/treemap_parents/dst_labels/
            col_labels, а также «label в X» для Box/Violin/Strip/… и «parents в X»
            для Сосульки (icicle).
        """
        sel = self._get_selected_indices()
        if not sel:
            messagebox.showwarning(tr.t('msg.warning'),
                                   tr.t('msg.select_object_short'))
            return

        data = self.graphs_data[sel[0]]
        t = data['type']

        # ----- Плагинные типы — отдельная ветка -----
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            self.type_var.set(tr.type_name(t))
            self._on_type_change()
            self._load_plugin_to_form(data)
            return

        # ----- Обычные типы -----
        self.type_var.set(tr.type_name(t))
        self._on_type_change()

        def _fmt_num(v):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                try:
                    return f"{v:g}"
                except (ValueError, TypeError):
                    return str(v)
            return str(v)

        def fill_entry(entry, values):
            entry.delete(0, tk.END)
            if values is None:
                return
            if isinstance(values, str):
                entry.insert(0, values)
                return
            if isinstance(values, (list, tuple)):
                if not values:
                    return
                entry.insert(0, ", ".join(_fmt_num(v) for v in values))

        def fill_matrix(entry, matrix):
            entry.delete(0, tk.END)
            if not matrix:
                return
            rows = [" ".join(_fmt_num(v) for v in row) for row in matrix]
            entry.insert(0, " ; ".join(rows))

        # ----- Специальные типы: переопределяем X под смысл -----
        # Типы, у которых в entry_x лежат подписи групп (pie_labels)
        label_in_x = {
            "Box plot", "Violin",
            "Strip plot", "Ridge plot", "Raincloud plot",
            "Beanplot", "Swarm plot",
            "Cherry blossom plot", "Dot-and-whisker",
            "Joyplot 3D",
        }
        # Типы, у которых в entry_z лежат рёбра (A-B; B-C)
        edges_in_z = {
            "Сетевой график", "Hive plot", "Arc diagram",
            "Дерево (tree diagram)", "Radial tree 3D", "Flow map",
        }

        if t in label_in_x and data.get('pie_labels'):
            fill_entry(self.entry_x, data['pie_labels'])
        elif t == "Alluvial diagram":
            fill_entry(self.entry_x,
                       [";".join([])] if False else
                       data.get('dst_labels', []))
        elif t == "Choropleth":
            fill_entry(self.entry_x, data.get('col_labels', []))
        elif t == "Bump chart":
            fill_entry(self.entry_x, data.get('col_labels', []))
        elif t == "Pie of pie":
            fill_entry(self.entry_x, data.get('pie_labels', []))
        elif t == "Сосулька (icicle)":
            parents = data.get('treemap_parents', [])
            self.entry_x.delete(0, tk.END)
            if parents:
                self.entry_x.insert(0, "; ".join(str(p) for p in parents))
        else:
            fill_entry(self.entry_x, data.get('x', []))

        # ----- Y: box_data имеет приоритет над плоским y -----
        if data.get('box_data'):
            groups_str = " ; ".join(
                ", ".join(_fmt_num(v) for v in g)
                for g in data['box_data']
            )
            self.entry_y.delete(0, tk.END)
            self.entry_y.insert(0, groups_str)
        else:
            fill_entry(self.entry_y, data.get('y', []))

        # ----- Z: matrix (heatmap_data) > строка-формула > плоский список -----
        if data.get('heatmap_data'):
            fill_matrix(self.entry_z, data['heatmap_data'])
        elif isinstance(data.get('z'), str):
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, data['z'])
        elif t in edges_in_z and data.get('z'):
            self.entry_z.delete(0, tk.END)
            self.entry_z.insert(0, " ; ".join(str(e) for e in data['z']))
        else:
            fill_entry(self.entry_z, data.get('z', []))

        # ----- Yerr: matrix (stream plot) > плоский список -----
        if data.get('yerr_matrix'):
            fill_matrix(self.entry_yerr, data['yerr_matrix'])
        else:
            fill_entry(self.entry_yerr, data.get('yerr', []))

        # ----- Pie labels / colors -----
        fill_entry(self.entry_pie, data.get('pie_labels', []))
        fill_entry(self.entry_pie_colors, data.get('pie_colors', []))

        # ----- Treemap parents (отдельное поле, не entry_x) -----
        parents = data.get('treemap_parents', [])
        self.treemap_parents.delete(0, tk.END)
        if parents:
            self.treemap_parents.insert(
                0, "; ".join(str(p) for p in parents))

        # ----- Скалярные параметры -----
        try:
            self.bins_var.set(int(data.get('bins', 10)))
        except (TypeError, ValueError):
            self.bins_var.set(10)
        self.use_y2_var.set(bool(data.get('use_y2', False)))
        self.fill_var.set(bool(data.get('fill', False)))
        self.glow_var.set(bool(data.get('glow', False)))
        try:
            self.subplot_index_var.set(
                int(data.get('subplot_index', 0)))
        except (TypeError, ValueError):
            self.subplot_index_var.set(0)

        # ----- Единицы -----
        self.unit_x_var.set(data.get('unit_x', '—') or '—')
        self.unit_y_var.set(data.get('unit_y', '—') or '—')
        self.unit_z_var.set(data.get('unit_z', '—') or '—')

        # ----- Имя, заметки -----
        self.entry_label.delete(0, tk.END)
        self.entry_label.insert(0, data.get('label', ''))
        self.entry_notes.delete(0, tk.END)
        self.entry_notes.insert(0, data.get('notes', ''))

        # ----- Стиль -----
        self.color_var.set(data.get('color', 'blue'))
        try:
            self.lw_var.set(float(data.get('lw', 2.0)))
        except (TypeError, ValueError):
            self.lw_var.set(2.0)
        self.ls_var.set(data.get('ls', '-'))
        try:
            self.ms_var.set(float(data.get('ms', 6.0)))
        except (TypeError, ValueError):
            self.ms_var.set(6.0)
        self.marker_var.set(data.get('marker', 'o'))

        # ----- Переключиться на вкладку «Создание» -----
        try:
            self.notebook.select(0)
        except Exception:
            pass

    # ========================================================================
    # УДАЛЕНИЕ И ОЧИСТКА
    # ========================================================================
    def _delete_graph(self):
        sel = self._get_selected_indices()
        if not sel:
            return
        self._snapshot(tr.t('hist.deleted_graphs', count=len(sel)))
        for idx in sorted(sel, reverse=True):
            if 0 <= idx < len(self.graphs_data):
                self._destroy_object(self.graphs_data.pop(idx))
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
        self._apply_grid_to_axes(self.axes)
        self.graphs_data.clear()
        self.folders = [""]
        self.line_counter = 0
        self._update_listbox()
        self.canvas.draw()
        self._refresh_stats()

    def _redraw_all(self):
        if hasattr(self, 'fig'):
            self._redraw()

    def _on_anim_type_change(self, event=None):
        t = tr.find_anim_by_display(self.anim_type_var.get())
        if t in ("Своя функция (2D)", "Своя функция (3D)"):
            self.frame_custom_anim.pack(fill=tk.X, pady=2)
        else:
            self.frame_custom_anim.pack_forget()

    # ========================================================================
    # СПИСОК ОБЪЕКТОВ (фильтр + иконка видимости)
    # ========================================================================
    def _update_listbox(self):
        tree = self.graph_tree
        tree.delete(*tree.get_children())
        q = ''
        if hasattr(self, 'search_var'):
            try:
                q = self.search_var.get().strip().lower()
            except Exception:
                q = ''

        folder_nodes = {}
        if not q:
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
            type_disp = tr.type_name(d['type'])
            vis_icon = '👁 ' if d.get('visible', True) else '🚫 '
            text = f"{vis_icon}[{type_disp}]{tag_str} {d['label']}"

            if q:
                haystack = (str(d.get('label', '')) + ' ' +
                            type_disp + ' ' +
                            str(d.get('notes', '')) + ' ' +
                            str(d.get('folder', ''))).lower()
                if q not in haystack:
                    continue
                tree.insert('', 'end', text=text, values=(i,))
            else:
                folder = d.get('folder', '')
                if folder and folder in self.hidden_folders:
                    continue
                parent = folder_nodes.get(folder, '')
                tree.insert(parent, 'end', text=text, values=(i,))

    def _refresh_stats(self):
        """Обновляет вкладку «Статистика» по первому выбранному объекту.

        Вызывается из _add_graph/_update_graph/_delete_graph/
        _add_plugin_graph/_clear_all_silent/_switch_document/двойного клика
        по дереву. Если выделения нет — все поля сбрасываются в «—».
        """
        # Защита: метод может быть вызван до того, как _build_ui
        # создаст stats_vars (теоретически при раннем _refresh_stats).
        if not hasattr(self, 'stats_vars'):
            return

        sel = self._get_selected_indices()

        # Нет выделения — сброс
        if not sel or not (0 <= sel[0] < len(self.graphs_data)):
            if hasattr(self, 'stats_label'):
                try:
                    self.stats_label.config(
                        text=tr.t('stats.none_selected'))
                except Exception:
                    pass
            for v in self.stats_vars.values():
                v.set('—')
            if hasattr(self, 'fit_result_var'):
                self.fit_result_var.set('')
            return

        data = self.graphs_data[sel[0]]

        # Заголовок — имя + тип
        if hasattr(self, 'stats_label'):
            try:
                self.stats_label.config(
                    text=f"{data.get('label', '?')} — "
                         f"{tr.type_name(data['type'])}")
            except Exception:
                pass

        # Числовые значения берём из Y — самый универсальный источник
        try:
            arr = np.asarray(data.get('y', []), dtype=float)
            arr = arr[np.isfinite(arr)]
        except (TypeError, ValueError):
            arr = np.array([])

        if arr.size == 0:
            for v in self.stats_vars.values():
                v.set('—')
            if hasattr(self, 'fit_result_var'):
                self.fit_result_var.set('')
            return

        def _fmt(v):
            try:
                f = float(v)
                if not np.isfinite(f):
                    return '—'
                return f"{f:.4g}"
            except (TypeError, ValueError):
                return '—'

        try:
            self.stats_vars['n'].set(str(int(arr.size)))
            self.stats_vars['min'].set(_fmt(arr.min()))
            self.stats_vars['max'].set(_fmt(arr.max()))
            self.stats_vars['mean'].set(_fmt(arr.mean()))
            self.stats_vars['median'].set(_fmt(np.median(arr)))

            if arr.size > 1:
                std = float(arr.std(ddof=1))
                var = float(arr.var(ddof=1))
            else:
                std = var = 0.0
            self.stats_vars['std'].set(_fmt(std))
            self.stats_vars['var'].set(_fmt(var))

            q1 = float(np.percentile(arr, 25))
            q3 = float(np.percentile(arr, 75))
            self.stats_vars['q1'].set(_fmt(q1))
            self.stats_vars['q3'].set(_fmt(q3))
            self.stats_vars['iqr'].set(_fmt(q3 - q1))
            self.stats_vars['sum'].set(_fmt(arr.sum()))

            # Корреляция Пирсона X↔Y (только если X — числа той же длины)
            corr_text = '—'
            try:
                xarr = np.asarray(data.get('x', []), dtype=float)
                n = min(xarr.size, arr.size)
                if n >= 2:
                    x_slice = xarr[:n]
                    y_slice = arr[:n]
                    x_ok = np.isfinite(x_slice)
                    if x_ok.sum() >= 2:
                        corr = float(np.corrcoef(
                            x_slice[x_ok], y_slice[x_ok])[0, 1])
                        if np.isfinite(corr):
                            corr_text = _fmt(corr)
            except (TypeError, ValueError):
                pass
            self.stats_vars['corr'].set(corr_text)
        except Exception:
            # Любая проблема с расчётом — не валим UI
            for v in self.stats_vars.values():
                v.set('—')

    # ========================================================================
    # ПЕРЕРИСОВКА (perf + visible)
    # ========================================================================
    def _redraw(self):
        import time
        t0 = time.perf_counter()

        for d in self.graphs_data:
            self._set_artist_visible(d.get('artist'),
                                     d.get('visible', True))

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
            self._apply_grid_to_axes(self.axes)
        except Exception:
            pass
        self.canvas.draw_idle()

        if hasattr(self, 'perf_var'):
            try:
                dt = (time.perf_counter() - t0) * 1000
                n_pts = sum(len(d.get('x') or [])
                            for d in self.graphs_data)
                self.perf_var.set(
                    f'⏱ {dt:.0f} ms · {n_pts} pts · '
                    f'{len(self.graphs_data)} obj')
            except Exception:
                pass

    def _on_type_change(self, event=None):
        for fr in (self.frame_x, self.frame_y, self.frame_z,
                   self.frame_pie_labels, self.frame_pie_colors,
                   self.frame_yerr, self.frame_y2_check,
                   self.frame_bins, self.frame_treemap,
                   self.frame_fill, self.frame_glow, self.frame_hint):
            fr.pack_forget()
        t = tr.find_type_by_display(self.type_var.get())
        self.hint_label.config(text="")

        # ----- Plugin-типы -----
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            self._show_plugin_fields(t)
            return

        # --- 2D базовые и продвинутые ---
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

        # --- Финансовые и проектные ---
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
        elif t == "Свечи (OHLC)":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.candlestick_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Диаграмма Парето":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.pareto_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Step plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.step_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Renko":
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.renko_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Point-and-Figure":
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.pnf_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Статистические ---
        elif t == "Q-Q plot":
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.qq_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "ECDF":
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(
                text="Y: выборка для эмпирической функции распределения")
            self.frame_hint.pack(fill=tk.X)
        elif t == "Hexbin":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.hexbin_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t in ("Strip plot", "Ridge plot", "Raincloud plot",
                   "Beanplot", "Swarm plot", "Cherry blossom plot",
                   "Dot-and-whisker"):
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            hint_key = {
                "Strip plot": 'create.strip_hint',
                "Ridge plot": 'create.ridge_hint',
                "Raincloud plot": 'create.raincloud_hint',
                "Beanplot": 'create.beanplot_hint',
                "Swarm plot": 'create.swarm_hint',
                "Cherry blossom plot": 'create.cherry_hint',
                "Dot-and-whisker": 'create.dotwhisker_hint',
            }.get(t, 'create.box_hint')
            self.hint_label.config(text=tr.t(hint_key))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Сезонная декомпозиция":
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.seasonal_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Rolling statistics":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.rolling_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Recurrence plot":
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.recurrence_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Cobweb plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.cobweb_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Poincaré plot":
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.poincare_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Phase portrait":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.phase_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Сетевые ---
        elif t == "Arc diagram":
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.arc_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Hive plot":
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.hive_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Дерево (tree diagram)":
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.tree_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Radial tree 3D":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.radialtree3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Сетевой график":
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.network_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Дендрограмма":
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.dendrogram_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Cluster dendrogram":
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.clusterdendro_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Sankey":
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.sankey_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Alluvial diagram":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.alluvial_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Chord":
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.chord_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Adjacency matrix":
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.adjmatrix_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Circle packing":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.circlepack_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Mapper algorithm":
            self.frame_z.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.mapper_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Векторные поля ---
        elif t in ("Stream plot", "Streamlines"):
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_yerr.pack(fill=tk.X)
            if t == "Streamlines":
                self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(
                text=tr.t('create.stream_hint'
                          if t == "Stream plot"
                          else 'create.streamlines_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Радиотехника ---
        elif t == "Bode plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.bode_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Smith chart":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.smith_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Nyquist plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.nyquist_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Root locus":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.rootlocus_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Constellation diagram":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.constellation_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- 3D-расширенные ---
        elif t == "Ribbon plot 3D":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.ribbon3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Waterfall spectrogram 3D":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_fill.pack(fill=tk.X)
            self.hint_label.config(
                text=tr.t('create.waterfall_spectrogram3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Riemann surface 3D":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.riemann3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Joyplot 3D":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.joyplot3d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Isosurface 3D":
            self.frame_z.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.isosurface3d_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Гео / метео ---
        elif t == "Choropleth":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.choropleth_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Flow map":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.flowmap_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Isopleth":
            self.frame_z.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.isopleth_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Cartogram":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.cartogram_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Dot density map":
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.dotdensity_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Hodograph":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.hodograph_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Роза ветров":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.windrose_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Skew-T log-P":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.skewt_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Thermodynamic diagram":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.thermo_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Диаграмма Вороного":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.voronoi_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Выпуклая оболочка":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.convexhull_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Alpha shape":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.alphashape_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- ML ---
        elif t == "Volcano plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.volcano_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "ROC curve":
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.roc_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Manhattan plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.manhattan_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "MA plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_fill.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.maplot_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Сравнение / ранги ---
        elif t == "Dot plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.dotplot_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Lollipop":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.lollipop_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Пирамида":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.pyramid_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Sparkline":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.sparkline_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Cycle plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.cycle_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Bump chart":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.bump_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Slopegraph":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.slope_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Dumbbell plot":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.dumbbell_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Bar of pie":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.barofpie_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Ribbon plot 2D":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.ribbon2d_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Bullet chart":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.bullet_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Funnel chart":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.funnel_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Календарная теплокарта":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.calheat_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Полярная теплокарта":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.polarheat_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Диаграмма бифуркаций":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.bifurcation_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Parallel coordinates":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.parallel_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Radar chart":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.radar_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Спидометр":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.gauge_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- Box / Violin / Heatmap / Treemap ---
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

        # --- 9 НОВЫХ ТИПОВ ---
        elif t == "Вафельная диаграмма":
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.waffle_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Сосулька (icicle)":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_labels.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.icicle_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Диаграмма Аргана":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.argand_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Диаграмма Тейлора":
            self.frame_x.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.taylor_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Горизонтальная столбчатая":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_yerr.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.hbar_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Горизонтальная линия":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_fill.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.hline_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Pie of pie":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_pie_colors.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.pieofpie_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Топографический профиль":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.topoprofile_hint'))
            self.frame_hint.pack(fill=tk.X)
        elif t == "Вейвлет-скейлограмма":
            self.frame_x.pack(fill=tk.X)
            self.frame_y.pack(fill=tk.X)
            self.frame_z.pack(fill=tk.X)
            self.frame_bins.pack(fill=tk.X)
            self.hint_label.config(text=tr.t('create.wavelet_hint'))
            self.frame_hint.pack(fill=tk.X)

        # --- 3D и остальное ---
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

    def _add_graph(self):
        t = tr.find_type_by_display(self.type_var.get())
        self._ensure_projection(self._projection_for_type(t))

        # ----- Plugin-типы: отдельная обработка -----
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            return self._add_plugin_graph(t)

        box_data = []
        heatmap_data = []
        treemap_parents = []
        yerr_matrix = []
        col_labels = []
        dst_labels = []
        x_data, y_data, z_data = [], [], []
        pie_labels, pie_colors, yerr_data = [], [], []

        # --- 2D базовые и продвинутые ---
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

        elif t in ("Quiver", "3D Quiver"):
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            yerr_data = self._parse_data(self.entry_yerr.get())
            if t == "Quiver":
                if not (x_data and y_data and z_data and yerr_data):
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('msg.quiver_needs_4'))
                    return
                if not (len(x_data) == len(y_data) == len(z_data)
                        == len(yerr_data)):
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('msg.quiver_needs_4'))
                    return
            else:
                if not (x_data and y_data and z_data):
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.quiver3d_hint'))
                    return
                n = min(len(x_data), len(y_data), len(z_data))
                x_data = x_data[:n]
                y_data = y_data[:n]
                z_data = z_data[:n]
                if not yerr_data or len(yerr_data) < n:
                    yerr_data = [1.0] * n
                else:
                    yerr_data = yerr_data[:n]

        elif t in ("Кольцевая", "Вложенная круговая"):
            if t == "Вложенная круговая":
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
            else:
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
            if t == "Кольцевая" and len(pie_labels) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.pie_labels_count'))
                return

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

        elif t == "Полярная теплокарта":
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = self._parse_data(self.entry_y.get()) or []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.polarheat_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.polarheat_hint'))
                return
            m = len(heatmap_data)
            n = len(heatmap_data[0])
            if not x_data or len(x_data) != n:
                x_data = list(range(n))
            if not y_data or len(y_data) != m:
                y_data = list(range(m))

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

        # --- Финансовые и проектные ---
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

        elif t == "Свечи (OHLC)":
            x_data = self._parse_data(self.entry_x.get()) or []
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            if len(box_data) != 4:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.candlestick_hint'))
                return
            if len(set(len(g) for g in box_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.candlestick_hint'))
                return
            y_data = box_data[0]
            if not x_data or len(x_data) != len(y_data):
                x_data = list(range(len(y_data)))

        elif t == "Диаграмма Парето":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')]
            else:
                x_data = [str(i + 1) for i in range(len(y_data))]
            if len(x_data) != len(y_data):
                x_data = [str(i + 1) for i in range(len(y_data))]

        elif t == "Step plot":
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

        elif t in ("Renko", "Point-and-Figure"):
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 2:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.renko_hint' if t == "Renko"
                         else tr.t('create.pnf_hint')))
                return
            x_data = list(range(len(y_data)))

        # --- Статистические ---
        elif t in ("Q-Q plot", "ECDF", "Poincaré plot"):
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            x_data = list(range(len(y_data)))

        elif t in ("Hexbin", "Dot plot", "Lollipop", "Sparkline",
                   "MA plot", "Hodograph", "Роза ветров",
                   "Диаграмма Вороного", "Выпуклая оболочка",
                   "Alpha shape", "Constellation diagram"):
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if t in ("Dot plot", "Sparkline"):
                if not y_data:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('msg.bad_format_y'))
                    return
                if isinstance(x_data, list) and x_data:
                    if len(x_data) == len(y_data):
                        x_data = [str(v) for v in x_data]
                    else:
                        x_data = [f"C{i + 1}"
                                  for i in range(len(y_data))]
                else:
                    if self.entry_x.get().strip():
                        x_data = [s.strip()
                                  for s in
                                  self.entry_x.get().split(',')]
                    else:
                        x_data = [f"C{i + 1}"
                                  for i in range(len(y_data))]
                if len(x_data) != len(y_data):
                    x_data = [f"C{i + 1}" for i in range(len(y_data))]
            else:
                if not x_data or not y_data:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('msg.bad_format'))
                    return
                if len(x_data) != len(y_data):
                    if t in ("Lollipop", "Sparkline"):
                        if not x_data:
                            x_data = list(range(len(y_data)))
                    else:
                        messagebox.showerror(tr.t('msg.error'),
                                             tr.t('msg.xy_length'))
                        return

        elif t in ("Strip plot", "Ridge plot", "Raincloud plot",
                   "Beanplot", "Swarm plot", "Cherry blossom plot",
                   "Dot-and-whisker"):
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            if not box_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.box_groups'))
                return
            y_data = box_data[0]
            x_data = list(range(len(y_data)))
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    pie_labels = raw_labels

        elif t == "Сезонная декомпозиция":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 4:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            if not x_data or len(x_data) != len(y_data):
                x_data = list(range(len(y_data)))

        elif t == "Rolling statistics":
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

        elif t == "Recurrence plot":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 4:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.recurrence_hint'))
                return
            if len(y_data) > 3000:
                messagebox.showwarning(
                    tr.t('msg.warning'),
                    f"Recurrence plot: {len(y_data)} точек —\n"
                    f"матрица ~{len(y_data) ** 2 // 1_000_000} млн ячеек.\n"
                    f"Используется только первые 3000 точек.")
                y_data = y_data[:3000]
            x_data = list(range(len(y_data)))

        elif t == "Cobweb plot":
            formula = self.entry_x.get().strip() or "r * x * (1 - x)"
            x_data = [formula]
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.cobweb_hint'))
                return
            x0 = float(y_data[0])
            N = int(y_data[1])
            if N < 3:
                N = 3
            if N > 200:
                N = 200
            y_data = [x0, float(N)]

        elif t == "Phase portrait":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.phase_hint'))
                return
            if not x_data or len(x_data) != len(y_data):
                x_data = list(range(len(y_data)))
            z_data = self.entry_z.get().strip() or ''

        # --- Сетевые и иерархические ---
        # --- Сетевые и иерархические ---
        elif t in ("Arc diagram", "Hive plot", "Дерево (tree diagram)",
                   "Radial tree 3D", "Сетевой график"):
            z_data = [s.strip()
                      for s in self.entry_z.get().split(';')
                      if s.strip()]
            if not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.network_hint'))
                return
            x_data = list(range(len(z_data)))
            y_data = list(range(len(z_data)))

        elif t == "Дендрограмма":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if len(heatmap_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.dendrogram_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.dendrogram_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            x_data = list(range(len(heatmap_data)))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Cluster dendrogram":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if len(heatmap_data) < 2:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.clusterdendro_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.clusterdendro_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            x_data = list(range(len(heatmap_data)))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Sankey":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.sankey_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            x_data = list(range(len(y_data)))

        elif t == "Alluvial diagram":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.alluvial_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.alluvial_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            dst_labels = [s.strip()
                          for s in self.entry_x.get().split(';')
                          if s.strip()]
            if not dst_labels:
                dst_labels = [f"D{j + 1}"
                              for j in range(len(heatmap_data[0]))]
            x_data = list(range(len(heatmap_data)))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Chord":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.chord_hint'))
                return
            if len(heatmap_data) != len(heatmap_data[0]):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.chord_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            x_data = list(range(len(heatmap_data)))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Adjacency matrix":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.adjmatrix_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.adjmatrix_hint'))
                return
            n = len(heatmap_data)
            if len(heatmap_data[0]) != n:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.adjmatrix_hint'))
                return
            if self.entry_pie.get().strip():
                pie_labels = [s.strip()
                              for s in self.entry_pie.get().split(',')
                              if s.strip()]
            else:
                pie_labels = [f"N{i + 1}" for i in range(n)]
            if len(pie_labels) != n:
                pie_labels = [f"N{i + 1}" for i in range(n)]
            x_data = list(range(n))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Circle packing":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.circlepack_hint'))
                return
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            else:
                x_data = [f"C{i + 1}" for i in range(len(y_data))]
            if len(x_data) != len(y_data):
                x_data = [f"C{i + 1}" for i in range(len(y_data))]
            z_data = self._parse_data(self.entry_z.get())
            if not z_data or len(z_data) != len(y_data):
                z_data = [-1.0] * len(y_data)

        elif t == "Mapper algorithm":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.mapper_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.mapper_hint'))
                return
            if len(heatmap_data) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.mapper_hint'))
                return
            x_data = list(range(len(heatmap_data[0])))
            y_data = list(range(len(heatmap_data)))

        # --- Векторные поля ---
        elif t in ("Stream plot", "Streamlines"):
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = self._parse_data(self.entry_y.get()) or []
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            yerr_matrix = []
            for r in self.entry_yerr.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    yerr_matrix.append(vals)
            if not heatmap_data or not yerr_matrix:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.stream_hint'
                         if t == "Stream plot"
                         else tr.t('create.streamlines_hint')))
                return
            if (len(set(len(r) for r in heatmap_data)) != 1
                    or len(set(len(r) for r in yerr_matrix)) != 1):
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.stream_hint'
                         if t == "Stream plot"
                         else tr.t('create.streamlines_hint')))
                return
            if (len(heatmap_data), len(heatmap_data[0])) != \
                    (len(yerr_matrix), len(yerr_matrix[0])):
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.stream_hint'
                         if t == "Stream plot"
                         else tr.t('create.streamlines_hint')))
                return
            m = len(heatmap_data)
            n = len(heatmap_data[0])
            if not x_data or len(x_data) != n:
                x_data = list(range(n))
            if not y_data or len(y_data) != m:
                y_data = list(range(m))

        # --- Радиотехника ---
        elif t in ("Bode plot", "Nyquist plot", "Root locus",
                   "Smith chart"):
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if t == "Bode plot":
                if not x_data or not y_data:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.bode_hint'))
                    return
                if len(x_data) != len(y_data):
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('msg.xy_length'))
                    return
                if z_data and len(z_data) >= len(x_data):
                    z_data = z_data[:len(x_data)]
                else:
                    z_data = []
            elif t == "Nyquist plot":
                if not x_data or not y_data or not z_data:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.nyquist_hint'))
                    return
                n = min(len(x_data), len(y_data), len(z_data))
                if n < 2:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.nyquist_hint'))
                    return
                x_data = x_data[:n]
                y_data = y_data[:n]
                z_data = z_data[:n]
            elif t == "Root locus":
                if not x_data or not y_data:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.rootlocus_hint'))
                    return
                if len(y_data) < 2:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.rootlocus_hint'))
                    return
            elif t == "Smith chart":
                z_matrix = []
                for r in self.entry_z.get().split(';'):
                    vals = self._parse_data(r)
                    if vals:
                        z_matrix.append(vals)
                if (len(z_matrix) >= 2
                        and len(z_matrix[0]) == len(z_matrix[1])
                        and len(z_matrix[0]) > 0):
                    x_data = z_matrix[0]
                    y_data = z_matrix[1]
                    heatmap_data = z_matrix
                elif x_data and y_data and len(x_data) == len(y_data):
                    heatmap_data = []
                else:
                    messagebox.showerror(tr.t('msg.error'),
                                         tr.t('create.smith_hint'))
                    return

        # --- 3D-расширенные ---
        elif t == "Ribbon plot 3D":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not x_data or not y_data or not z_data:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('msg.need_xyz_lengths', type=tr.type_name(t)))
                return
            n = min(len(x_data), len(y_data), len(z_data))
            if n < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.ribbon3d_hint'))
                return
            x_data = x_data[:n]
            y_data = y_data[:n]
            z_data = z_data[:n]

        elif t == "Waterfall spectrogram 3D":
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
                    tr.t('create.waterfall_spectrogram3d_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.waterfall_spectrogram3d_hint'))
                return
            m = len(heatmap_data)
            n = len(heatmap_data[0])
            if not x_data or len(x_data) != n:
                x_data = list(range(n))
            if not y_data or len(y_data) != m:
                y_data = list(range(m))

        elif t == "Riemann surface 3D":
            formula = self.entry_z.get().strip() or "sqrt(z)"
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = self._parse_data(self.entry_y.get()) or []
            x_data = [float(v) for v in x_data[:2]]
            y_data = [float(v) for v in y_data[:2]]
            z_data = formula

        elif t == "Joyplot 3D":
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            if not box_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.joyplot3d_hint'))
                return
            y_data = box_data[0]
            x_data = list(range(len(y_data)))
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    pie_labels = raw_labels

        elif t == "Isosurface 3D":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isosurface3d_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isosurface3d_hint'))
                return
            if len(heatmap_data) < 3 or len(heatmap_data[0]) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isosurface3d_hint'))
                return
            x_data = list(range(len(heatmap_data[0])))
            y_data = list(range(len(heatmap_data)))

        # --- Гео / метео / научные ---
        elif t == "Choropleth":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.choropleth_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.choropleth_hint'))
                return
            if self.entry_pie.get().strip():
                pie_labels = [s.strip()
                              for s in self.entry_pie.get().split(',')
                              if s.strip()]
            else:
                pie_labels = []
            x_raw = self.entry_x.get().strip()
            if x_raw:
                col_labels = [s.strip()
                              for s in x_raw.split(';')
                              if s.strip()]
            else:
                col_labels = []
            x_data = list(range(len(heatmap_data[0])))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Flow map":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.flowmap_hint'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.xy_length'))
                return
            if self.entry_pie.get().strip():
                pie_labels = [s.strip()
                              for s in self.entry_pie.get().split(',')
                              if s.strip()]
            else:
                pie_labels = [f"N{i + 1}" for i in range(len(x_data))]
            if len(pie_labels) != len(x_data):
                pie_labels = [f"N{i + 1}" for i in range(len(x_data))]
            z_data = [s.strip()
                      for s in self.entry_z.get().split(';')
                      if s.strip()]
            if not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.flowmap_hint'))
                return

        elif t == "Isopleth":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isopleth_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isopleth_hint'))
                return
            if len(heatmap_data) < 2 or len(heatmap_data[0]) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.isopleth_hint'))
                return
            x_data = list(range(len(heatmap_data[0])))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Cartogram":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.cartogram_hint'))
                return
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            else:
                x_data = [f"R{i + 1}" for i in range(len(y_data))]
            if len(x_data) != len(y_data):
                x_data = [f"R{i + 1}" for i in range(len(y_data))]

        elif t == "Dot density map":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.dotdensity_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.dotdensity_hint'))
                return
            x_data = list(range(len(heatmap_data[0])))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t in ("Skew-T log-P", "Thermodynamic diagram"):
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not x_data or not y_data or not z_data:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.skewt_hint'
                         if t == "Skew-T log-P"
                         else tr.t('create.thermo_hint')))
                return
            n = min(len(x_data), len(y_data), len(z_data))
            if n < 2:
                messagebox.showerror(
                    tr.t('msg.error'),
                    tr.t('create.skewt_hint'
                         if t == "Skew-T log-P"
                         else tr.t('create.thermo_hint')))
                return
            x_data = x_data[:n]
            y_data = y_data[:n]
            z_data = z_data[:n]

        # --- ML / статистика-2 ---
        elif t == "Volcano plot":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.volcano_hint'))
                return
            if len(x_data) != len(y_data):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.xy_length'))
                return
            z_data = self._parse_data(self.entry_z.get()) or []

        elif t == "ROC curve":
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not y_data or not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.roc_hint'))
                return
            if len(y_data) != len(z_data):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.roc_hint'))
                return
            if len(y_data) < 4:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.roc_hint'))
                return
            x_data = list(range(len(y_data)))

        elif t == "Manhattan plot":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.manhattan_hint'))
                return
            n = min(len(x_data), len(y_data))
            x_data = x_data[:n]
            y_data = y_data[:n]
            z_data = self._parse_data(self.entry_z.get()) or []
            if z_data and len(z_data) >= n:
                z_data = z_data[:n]
            else:
                z_data = [1.0] * n

        # --- Сравнение / ранги ---
        elif t == "Bump chart":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if not heatmap_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.bump_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.bump_hint'))
                return
            n_time = len(heatmap_data[0])
            x_parsed = self._parse_data(self.entry_x.get())
            if x_parsed and len(x_parsed) == n_time:
                col_labels = [str(v) for v in x_parsed]
            elif self.entry_x.get().strip():
                col_labels = [s.strip()
                              for s in self.entry_x.get().split(',')
                              if s.strip()]
            else:
                col_labels = [f"T{i + 1}" for i in range(n_time)]
            if len(col_labels) != n_time:
                col_labels = [f"T{i + 1}" for i in range(n_time)]
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]
            x_data = list(range(n_time))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Slopegraph":
            x_raw = self.entry_x.get().strip()
            if x_raw:
                x_data = [s.strip()
                          for s in x_raw.split(',')
                          if s.strip()]
            else:
                x_data = ["До", "После"]
            if len(x_data) < 2:
                x_data = x_data + ["?"] * (2 - len(x_data))
            x_data = x_data[:2]
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not y_data or not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.slope_hint'))
                return
            n = min(len(y_data), len(z_data))
            y_data = y_data[:n]
            z_data = z_data[:n]
            pie_labels = [l.strip()
                          for l in self.entry_pie.get().split(',')
                          if l.strip()]

        elif t == "Dumbbell plot":
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not y_data or not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.dumbbell_hint'))
                return
            n = min(len(y_data), len(z_data))
            y_data = y_data[:n]
            z_data = z_data[:n]
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            else:
                x_data = [f"C{i + 1}" for i in range(n)]
            if len(x_data) != n:
                x_data = [f"C{i + 1}" for i in range(n)]

        elif t == "Bar of pie":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.barofpie_hint'))
                return
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            else:
                x_data = [f"C{i + 1}" for i in range(len(y_data))]
            if len(x_data) != len(y_data):
                x_data = [f"C{i + 1}" for i in range(len(y_data))]
            pie_colors = [c.strip()
                          for c in
                          self.entry_pie_colors.get().split(',')
                          if c.strip()]

        elif t == "Ribbon plot 2D":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            z_data = self._parse_data(self.entry_z.get())
            if not x_data or not y_data or not z_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.ribbon2d_hint'))
                return
            n = min(len(x_data), len(y_data), len(z_data))
            if n < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.ribbon2d_hint'))
                return
            x_data = x_data[:n]
            y_data = y_data[:n]
            z_data = z_data[:n]

        elif t == "Bullet chart":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.bullet_hint'))
                return
            y_data = y_data[:3]
            if self.entry_x.get().strip():
                x_data = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
                x_data = x_data[:1]
            else:
                x_data = [self.entry_label.get() or 'KPI']

        elif t == "Funnel chart":
            x_raw = self.entry_x.get().strip()
            if x_raw:
                x_data = [s.strip()
                          for s in x_raw.split(',')
                          if s.strip()]
            else:
                x_data = []
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.funnel_hint'))
                return
            if len(x_data) != len(y_data):
                x_data = [f"Этап {i + 1}" for i in range(len(y_data))]
            pie_colors = [c.strip()
                          for c in
                          self.entry_pie_colors.get().split(',')
                          if c.strip()]

        elif t == "Календарная теплокарта":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.calheat_hint'))
                return
            x_data = self._parse_data(self.entry_x.get()) or []

        elif t == "Диаграмма бифуркаций":
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = self._parse_data(self.entry_y.get()) or []
            if not x_data:
                x_data = [2.5, 4.0]
            if not y_data:
                y_data = [0.5]
            x_data = [float(v) for v in x_data[:2]]
            y_data = [float(v) for v in y_data[:1]]
            if x_data[0] < 0:
                x_data[0] = 0.1
            if len(x_data) == 2 and x_data[1] <= x_data[0]:
                x_data[1] = x_data[0] + 1.0
            if y_data[0] <= 0 or y_data[0] >= 1:
                y_data[0] = 0.5

        elif t == "Parallel coordinates":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if len(heatmap_data) < 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.parallel_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.parallel_hint'))
                return
            if len(heatmap_data[0]) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.parallel_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_x.get().split(',')
                          if l.strip()]
            x_data = list(range(len(heatmap_data[0])))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Radar chart":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if len(heatmap_data) < 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.radar_hint'))
                return
            if len(set(len(r) for r in heatmap_data)) != 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.radar_hint'))
                return
            if len(heatmap_data[0]) < 3:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.radar_hint'))
                return
            pie_labels = [l.strip()
                          for l in self.entry_x.get().split(',')
                          if l.strip()]
            x_data = list(range(len(heatmap_data[0])))
            y_data = heatmap_data[0] if heatmap_data else []

        elif t == "Спидометр":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 1:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.gauge_hint'))
                return
            y_data = y_data[:1]
            x_data = self._parse_data(self.entry_x.get()) or []
            x_data = x_data[:2]
            if len(x_data) == 0:
                x_data = [0.0, 100.0]
            elif len(x_data) == 1:
                x_data = [0.0, x_data[0]]

        # --- Старые группы (Box, Violin, Heatmap, Treemap) ---
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

        # --- 9 НОВЫХ ТИПОВ ---
        elif t == "Вафельная диаграмма":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            x_data = list(range(len(y_data)))
            pie_labels = [s.strip()
                          for s in self.entry_pie.get().split(',')
                          if s.strip()]
            pie_colors = [s.strip()
                          for s in self.entry_pie_colors.get().split(',')
                          if s.strip()]
            if not pie_labels or len(pie_labels) != len(y_data):
                pie_labels = [f"C{i + 1}" for i in range(len(y_data))]

        elif t == "Сосулька (icicle)":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            x_data = list(range(len(y_data)))
            pie_labels = [s.strip()
                          for s in self.entry_pie.get().split(',')
                          if s.strip()]
            while len(pie_labels) < len(y_data):
                pie_labels.append(f"N{len(pie_labels) + 1}")
            treemap_parents = [s.strip()
                               for s in self.entry_x.get().split(';')]
            while len(treemap_parents) < len(y_data):
                treemap_parents.append('')

        elif t == "Диаграмма Аргана":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.argand_hint'))
                return
            n = min(len(x_data), len(y_data))
            x_data, y_data = x_data[:n], y_data[:n]
            z_data = self._parse_data(self.entry_z.get()) or []

        elif t == "Диаграмма Тейлора":
            heatmap_data = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    heatmap_data.append(vals)
            if len(heatmap_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.taylor_hint'))
                return
            if len(heatmap_data[0]) != len(heatmap_data[1]):
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.taylor_hint'))
                return
            n_models = len(heatmap_data[0])
            pie_labels = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            while len(pie_labels) < n_models:
                pie_labels.append(f"M{len(pie_labels) + 1}")
            x_data = self._parse_data(self.entry_x.get()) or []
            y_data = heatmap_data[0]
            z_data = heatmap_data[1]

        elif t == "Горизонтальная столбчатая":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('msg.bad_format_y'))
                return
            if self.entry_x.get().strip():
                try:
                    x_data = self._parse_data(self.entry_x.get())
                except Exception:
                    x_data = None
            else:
                x_data = None
            if not x_data or len(x_data) != len(y_data):
                x_data = list(range(len(y_data)))
            yerr_data = self._parse_data(self.entry_yerr.get()) or []

        elif t == "Горизонтальная линия":
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

        elif t == "Pie of pie":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 2:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.pieofpie_hint'))
                return
            x_data = list(range(len(y_data)))
            pie_labels = [s.strip()
                          for s in self.entry_x.get().split(',')
                          if s.strip()]
            if len(pie_labels) != len(y_data):
                pie_labels = [f"C{i + 1}" for i in range(len(y_data))]
            pie_colors = [s.strip()
                          for s in self.entry_pie_colors.get().split(',')
                          if s.strip()]

        elif t == "Топографический профиль":
            x_data = self._parse_data(self.entry_x.get())
            y_data = self._parse_data(self.entry_y.get())
            if not x_data or not y_data:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.topoprofile_hint'))
                return
            n = min(len(x_data), len(y_data))
            x_data, y_data = x_data[:n], y_data[:n]

        elif t == "Вейвлет-скейлограмма":
            y_data = self._parse_data(self.entry_y.get())
            if not y_data or len(y_data) < 8:
                messagebox.showerror(tr.t('msg.error'),
                                     tr.t('create.wavelet_hint'))
                return
            x_data = self._parse_data(self.entry_x.get()) or []
            if len(x_data) != len(y_data):
                x_data = list(range(len(y_data)))
            z_data = self.entry_z.get().strip() or 'cmor1.5-1.0'

        # --- Обычные типы (Линия, Точечная, 3D и пр.) ---
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

        # ================================================================
        # Создание объекта
        # ================================================================
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
        # Доп. поля для новых типов
        if t == "Choropleth":
            d['col_labels'] = col_labels
        if t == "Flow map":
            d['z'] = z_data
        if t == "Bump chart":
            d['col_labels'] = col_labels
        if t == "Bar of pie":
            d['pie_colors'] = pie_colors
        if yerr_matrix:
            d['yerr_matrix'] = yerr_matrix

        d['artist'] = self._create_artist(d)
        self.graphs_data.append(d)
        self._update_listbox()
        self._redraw()
        self._refresh_stats()

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
        self._destroy_object(data)
        t = tr.find_type_by_display(self.type_var.get())
        self._ensure_projection(self._projection_for_type(t))
        self._snapshot(tr.t('hist.changed_graph', name=data['label']))

        # ----- Plugin-типы -----
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            yerr_new = self._parse_data(self.entry_yerr.get()) or []
            data['x'] = x_new
            data['y'] = y_new
            data['z'] = z_new
            data['yerr'] = yerr_new
            data['pie_labels'] = [s.strip()
                                  for s in self.entry_pie.get().split(',')
                                  if s.strip()]
            data['pie_colors'] = [s.strip()
                                  for s in self.entry_pie_colors.get().split(',')
                                  if s.strip()]
            data.update({
                'type': t,
                'color': self.color_var.get(),
                'label': self.entry_label.get(),
                'lw': self.lw_var.get(), 'ls': self.ls_var.get(),
                'ms': self.ms_var.get(), 'marker': self.marker_var.get(),
                'use_y2': self.use_y2_var.get(),
                'bins': self.bins_var.get(),
                'fill': self.fill_var.get(),
                'glow': self.glow_var.get(),
                'notes': self.entry_notes.get(),
                'subplot_index': self.subplot_index_var.get(),
                'unit_x': self.unit_x_var.get(),
                'unit_y': self.unit_y_var.get(),
                'unit_z': self.unit_z_var.get(),
            })
            data['artist'] = self._create_artist(data)
            self._update_listbox()
            self._redraw()
            self._refresh_stats()
            return

        # --- Разбор данных по семействам ---
        if t in ("Полярный scatter", "3D Полигон",
                 "3D Триангуляция", "Пузырьковая"):
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if t in ("3D Полигон", "3D Триангуляция", "Пузырьковая"):
                data['z'] = self._parse_data(self.entry_z.get()) or []

        elif t in ("Quiver", "3D Quiver"):
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

        # --- Финансовые ---
        elif t == "Свечи (OHLC)":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
            if not data['x'] or len(data['x']) != len(data['y']):
                data['x'] = list(range(len(data['y'])))

        elif t == "Диаграмма Парето":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')]
                if len(x_new) == len(data['y']):
                    data['x'] = x_new
            if len(data.get('x', [])) != len(data['y']):
                data['x'] = [str(i + 1) for i in range(len(data['y']))]

        elif t == "Step plot":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []

        elif t in ("Renko", "Point-and-Figure"):
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))

        # --- Статистические ---
        elif t in ("Q-Q plot", "ECDF", "Poincaré plot"):
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))

        elif t in ("Hexbin", "Dot plot", "Lollipop", "Sparkline",
                   "MA plot", "Hodograph", "Роза ветров",
                   "Диаграмма Вороного", "Выпуклая оболочка",
                   "Alpha shape", "Constellation diagram"):
            if t in ("Dot plot", "Sparkline"):
                data['y'] = self._parse_data(self.entry_y.get()) or []
                if self.entry_x.get().strip():
                    x_new = [s.strip()
                             for s in self.entry_x.get().split(',')
                             if s.strip()]
                    if len(x_new) == len(data['y']):
                        data['x'] = x_new
                    else:
                        data['x'] = [f"C{i + 1}"
                                     for i in range(len(data['y']))]
                else:
                    data['x'] = [f"C{i + 1}"
                                 for i in range(len(data['y']))]
            else:
                data['x'] = self._parse_data(self.entry_x.get()) or []
                data['y'] = self._parse_data(self.entry_y.get()) or []
            if t == "Constellation diagram":
                data['z'] = self._parse_data(self.entry_z.get()) or []

        elif t in ("Strip plot", "Ridge plot", "Raincloud plot",
                   "Beanplot", "Swarm plot", "Cherry blossom plot",
                   "Dot-and-whisker"):
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
            data['x'] = list(range(len(data['y'])))
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    data['pie_labels'] = raw_labels
                else:
                    data['pie_labels'] = []

        elif t == "Сезонная декомпозиция":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if not data['x'] or len(data['x']) != len(data['y']):
                data['x'] = list(range(len(data['y'])))

        elif t == "Rolling statistics":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []

        elif t == "Recurrence plot":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if len(data['y']) > 3000:
                data['y'] = data['y'][:3000]
            data['x'] = list(range(len(data['y'])))

        elif t == "Cobweb plot":
            formula = self.entry_x.get().strip() or "r * x * (1 - x)"
            data['x'] = [formula]
            y_new = self._parse_data(self.entry_y.get()) or []
            if len(y_new) >= 2:
                x0 = float(y_new[0])
                N = int(y_new[1])
                if N < 3:
                    N = 3
                if N > 200:
                    N = 200
                data['y'] = [x0, float(N)]

        elif t == "Phase portrait":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if not data['x'] or len(data['x']) != len(data['y']):
                data['x'] = list(range(len(data['y'])))
            data['z'] = self.entry_z.get().strip()

        # --- Сетевые ---
        elif t in ("Arc diagram", "Hive plot", "Дерево (tree diagram)",
                   "Radial tree 3D", "Сетевой график"):
            z_new = [s.strip()
                     for s in self.entry_z.get().split(';')
                     if s.strip()]
            data['z'] = z_new
            data['x'] = list(range(len(z_new)))
            data['y'] = list(range(len(z_new)))

        elif t == "Дендрограмма":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(len(hm)))
            data['y'] = hm[0] if hm else []

        elif t == "Cluster dendrogram":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(len(hm)))
            data['y'] = hm[0] if hm else []

        elif t == "Sankey":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]

        elif t == "Alluvial diagram":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]
            data['dst_labels'] = [s.strip()
                                  for s in
                                  self.entry_x.get().split(';')
                                  if s.strip()]
            if not data['dst_labels'] and hm:
                data['dst_labels'] = [f"D{j + 1}"
                                      for j in range(len(hm[0]))]
            data['x'] = list(range(len(hm)))
            data['y'] = hm[0] if hm else []

        elif t == "Chord":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(len(hm)))
            data['y'] = hm[0] if hm else []

        elif t == "Adjacency matrix":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            n = len(hm) if hm else 0
            if self.entry_pie.get().strip():
                pie_labels = [s.strip()
                              for s in self.entry_pie.get().split(',')
                              if s.strip()]
            else:
                pie_labels = [f"N{i + 1}" for i in range(n)]
            if len(pie_labels) != n:
                pie_labels = [f"N{i + 1}" for i in range(n)]
            data['pie_labels'] = pie_labels
            data['x'] = list(range(n))
            data['y'] = hm[0] if hm else []

        elif t == "Circle packing":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')
                         if s.strip()]
                if len(x_new) != len(data['y']):
                    x_new = [f"C{i + 1}"
                             for i in range(len(data['y']))]
            else:
                x_new = [f"C{i + 1}" for i in range(len(data['y']))]
            data['x'] = x_new
            z_new = self._parse_data(self.entry_z.get())
            if not z_new or len(z_new) != len(data['y']):
                z_new = [-1.0] * len(data['y'])
            data['z'] = z_new

        elif t == "Mapper algorithm":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = list(range(len(hm)))

        # --- Векторные поля ---
        elif t in ("Stream plot", "Streamlines"):
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            vm = []
            for r in self.entry_yerr.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    vm.append(vals)
            m = len(hm)
            n = len(hm[0]) if hm else 0
            if not x_new or len(x_new) != n:
                x_new = list(range(n))
            if not y_new or len(y_new) != m:
                y_new = list(range(m))
            data['x'] = x_new
            data['y'] = y_new
            data['heatmap_data'] = hm
            data['yerr_matrix'] = vm

        # --- Радиотехника ---
        elif t == "Bode plot":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['z'] = self._parse_data(self.entry_z.get()) or []

        elif t == "Nyquist plot":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(x_new), len(y_new), len(z_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]

        elif t == "Root locus":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []

        elif t == "Smith chart":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_matrix = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    z_matrix.append(vals)
            if len(z_matrix) >= 2 and len(z_matrix[0]) == len(z_matrix[1]):
                data['x'] = z_matrix[0]
                data['y'] = z_matrix[1]
                data['heatmap_data'] = z_matrix
            elif x_new and y_new and len(x_new) == len(y_new):
                data['x'] = x_new
                data['y'] = y_new
                data['heatmap_data'] = []

        # --- 3D-расширенные ---
        elif t == "Ribbon plot 3D":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(x_new), len(y_new), len(z_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]

        elif t == "Waterfall spectrogram 3D":
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

        elif t == "Riemann surface 3D":
            data['x'] = (self._parse_data(self.entry_x.get()) or [])[:2]
            data['y'] = (self._parse_data(self.entry_y.get()) or [])[:2]
            data['z'] = self.entry_z.get().strip() or "sqrt(z)"

        elif t == "Joyplot 3D":
            box_data = [self._parse_data(g) or []
                        for g in self.entry_y.get().split(';')
                        if g.strip()]
            box_data = [g for g in box_data if g]
            data['box_data'] = box_data
            data['y'] = box_data[0] if box_data else []
            data['x'] = list(range(len(data['y'])))
            if self.entry_x.get().strip():
                raw_labels = [l.strip()
                              for l in self.entry_x.get().split(',')]
                if len(raw_labels) == len(box_data):
                    data['pie_labels'] = raw_labels
                else:
                    data['pie_labels'] = []

        elif t == "Isosurface 3D":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = list(range(len(hm)))

        # --- Гео / метео ---
        elif t == "Choropleth":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            if self.entry_pie.get().strip():
                data['pie_labels'] = [s.strip()
                                      for s in
                                      self.entry_pie.get().split(',')
                                      if s.strip()]
            else:
                data['pie_labels'] = []
            x_raw = self.entry_x.get().strip()
            if x_raw:
                data['col_labels'] = [s.strip()
                                      for s in x_raw.split(';')
                                      if s.strip()]
            else:
                data['col_labels'] = []
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = hm[0] if hm else []

        elif t == "Flow map":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            n = min(len(x_new), len(y_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            if self.entry_pie.get().strip():
                labels = [s.strip()
                          for s in self.entry_pie.get().split(',')
                          if s.strip()]
            else:
                labels = [f"N{i + 1}" for i in range(n)]
            if len(labels) != n:
                labels = [f"N{i + 1}" for i in range(n)]
            data['pie_labels'] = labels
            data['z'] = [s.strip()
                         for s in self.entry_z.get().split(';')
                         if s.strip()]

        elif t == "Isopleth":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = hm[0] if hm else []

        elif t == "Cartogram":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')
                         if s.strip()]
                if len(x_new) != len(data['y']):
                    x_new = [f"R{i + 1}"
                             for i in range(len(data['y']))]
            else:
                x_new = [f"R{i + 1}" for i in range(len(data['y']))]
            data['x'] = x_new

        elif t == "Dot density map":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = hm[0] if hm else []

        elif t in ("Skew-T log-P", "Thermodynamic diagram"):
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(x_new), len(y_new), len(z_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]

        # --- ML ---
        elif t == "Volcano plot":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['z'] = self._parse_data(self.entry_z.get()) or []

        elif t == "ROC curve":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['z'] = self._parse_data(self.entry_z.get()) or []
            data['x'] = list(range(len(data['y'])))

        elif t == "Manhattan plot":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            n = min(len(x_new), len(y_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            z_new = self._parse_data(self.entry_z.get()) or []
            if z_new and len(z_new) >= n:
                data['z'] = z_new[:n]
            else:
                data['z'] = [1.0] * n

        # --- Сравнение / ранги ---
        elif t == "Bump chart":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            n_time = len(hm[0]) if hm else 0
            x_parsed = self._parse_data(self.entry_x.get())
            if x_parsed and len(x_parsed) == n_time:
                col_labels = [str(v) for v in x_parsed]
            elif self.entry_x.get().strip():
                col_labels = [s.strip()
                              for s in self.entry_x.get().split(',')
                              if s.strip()]
            else:
                col_labels = [f"T{i + 1}" for i in range(n_time)]
            if len(col_labels) != n_time:
                col_labels = [f"T{i + 1}" for i in range(n_time)]
            data['col_labels'] = col_labels
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(n_time))
            data['y'] = hm[0] if hm else []

        elif t == "Slopegraph":
            x_raw = self.entry_x.get().strip()
            if x_raw:
                x_new = [s.strip()
                         for s in x_raw.split(',')
                         if s.strip()]
            else:
                x_new = ["До", "После"]
            if len(x_new) < 2:
                x_new = x_new + ["?"] * (2 - len(x_new))
            data['x'] = x_new[:2]
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(y_new), len(z_new))
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_pie.get().split(',')
                                  if l.strip()]

        elif t == "Dumbbell plot":
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(y_new), len(z_new))
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')
                         if s.strip()]
                if len(x_new) != n:
                    x_new = [f"C{i + 1}" for i in range(n)]
            else:
                x_new = [f"C{i + 1}" for i in range(n)]
            data['x'] = x_new

        elif t == "Bar of pie":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')
                         if s.strip()]
                if len(x_new) != len(data['y']):
                    x_new = [f"C{i + 1}"
                             for i in range(len(data['y']))]
            else:
                x_new = [f"C{i + 1}" for i in range(len(data['y']))]
            data['x'] = x_new
            data['pie_colors'] = [c.strip()
                                  for c in
                                  self.entry_pie_colors.get().split(',')
                                  if c.strip()]

        elif t == "Ribbon plot 2D":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            z_new = self._parse_data(self.entry_z.get()) or []
            n = min(len(x_new), len(y_new), len(z_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            data['z'] = z_new[:n]

        elif t == "Bullet chart":
            y_new = self._parse_data(self.entry_y.get()) or []
            data['y'] = y_new[:3]
            if self.entry_x.get().strip():
                x_new = [s.strip()
                         for s in self.entry_x.get().split(',')
                         if s.strip()]
                data['x'] = x_new[:1]
            else:
                data['x'] = [self.entry_label.get() or 'KPI']

        elif t == "Funnel chart":
            x_raw = self.entry_x.get().strip()
            if x_raw:
                x_new = [s.strip()
                         for s in x_raw.split(',')
                         if s.strip()]
            else:
                x_new = []
            y_new = self._parse_data(self.entry_y.get()) or []
            if len(x_new) != len(y_new):
                x_new = [f"Этап {i + 1}" for i in range(len(y_new))]
            data['x'] = x_new
            data['y'] = y_new
            data['pie_colors'] = [c.strip()
                                  for c in
                                  self.entry_pie_colors.get().split(',')
                                  if c.strip()]

        elif t == "Календарная теплокарта":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = self._parse_data(self.entry_x.get()) or []

        elif t == "Диаграмма бифуркаций":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            if not x_new:
                x_new = [2.5, 4.0]
            if not y_new:
                y_new = [0.5]
            data['x'] = [float(v) for v in x_new[:2]]
            data['y'] = [float(v) for v in y_new[:1]]

        elif t == "Parallel coordinates":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_x.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = hm[0] if hm else []

        elif t == "Radar chart":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            data['pie_labels'] = [l.strip()
                                  for l in
                                  self.entry_x.get().split(',')
                                  if l.strip()]
            data['x'] = list(range(len(hm[0]) if hm else 0))
            data['y'] = hm[0] if hm else []

        elif t == "Спидометр":
            y_new = self._parse_data(self.entry_y.get()) or []
            data['y'] = y_new[:1]
            x_new = (self._parse_data(self.entry_x.get()) or [])[:2]
            if len(x_new) == 0:
                x_new = [0.0, 100.0]
            elif len(x_new) == 1:
                x_new = [0.0, x_new[0]]
            data['x'] = x_new

        # --- Box / Violin / Heatmap / Treemap ---
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

        # --- 9 новых типов ---
        elif t == "Вафельная диаграмма":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [s.strip()
                                  for s in self.entry_pie.get().split(',')
                                  if s.strip()]
            data['pie_colors'] = [s.strip()
                                  for s in self.entry_pie_colors.get().split(',')
                                  if s.strip()]
            if not data['pie_labels'] or len(data['pie_labels']) != len(data['y']):
                data['pie_labels'] = [f"C{i + 1}" for i in range(len(data['y']))]

        elif t == "Сосулька (icicle)":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))
            data['pie_labels'] = [s.strip()
                                  for s in self.entry_pie.get().split(',')
                                  if s.strip()]
            while len(data['pie_labels']) < len(data['y']):
                data['pie_labels'].append(f"N{len(data['pie_labels']) + 1}")
            data['treemap_parents'] = [s.strip()
                                       for s in self.entry_x.get().split(';')]
            while len(data['treemap_parents']) < len(data['y']):
                data['treemap_parents'].append('')

        elif t == "Диаграмма Аргана":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            n = min(len(x_new), len(y_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]
            data['z'] = self._parse_data(self.entry_z.get()) or []

        elif t == "Диаграмма Тейлора":
            hm = []
            for r in self.entry_z.get().split(';'):
                vals = self._parse_data(r)
                if vals:
                    hm.append(vals)
            data['heatmap_data'] = hm
            n_models = len(hm[0]) if hm else 0
            labels = [s.strip()
                      for s in self.entry_x.get().split(',')
                      if s.strip()]
            while len(labels) < n_models:
                labels.append(f"M{len(labels) + 1}")
            data['pie_labels'] = labels
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = hm[0] if hm else []
            data['z'] = hm[1] if len(hm) >= 2 else []

        elif t == "Горизонтальная столбчатая":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            if self.entry_x.get().strip():
                x_new = self._parse_data(self.entry_x.get())
                if not x_new or len(x_new) != len(data['y']):
                    x_new = list(range(len(data['y'])))
            else:
                x_new = list(range(len(data['y'])))
            data['x'] = x_new
            data['yerr'] = self._parse_data(self.entry_yerr.get()) or []

        elif t == "Горизонтальная линия":
            data['x'] = self._parse_data(self.entry_x.get()) or []
            data['y'] = self._parse_data(self.entry_y.get()) or []

        elif t == "Pie of pie":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            data['x'] = list(range(len(data['y'])))
            labels = [s.strip()
                      for s in self.entry_x.get().split(',')
                      if s.strip()]
            if len(labels) != len(data['y']):
                labels = [f"C{i + 1}" for i in range(len(data['y']))]
            data['pie_labels'] = labels
            data['pie_colors'] = [s.strip()
                                  for s in self.entry_pie_colors.get().split(',')
                                  if s.strip()]

        elif t == "Топографический профиль":
            x_new = self._parse_data(self.entry_x.get()) or []
            y_new = self._parse_data(self.entry_y.get()) or []
            n = min(len(x_new), len(y_new))
            data['x'] = x_new[:n]
            data['y'] = y_new[:n]

        elif t == "Вейвлет-скейлограмма":
            data['y'] = self._parse_data(self.entry_y.get()) or []
            x_new = self._parse_data(self.entry_x.get()) or []
            if len(x_new) != len(data['y']):
                x_new = list(range(len(data['y'])))
            data['x'] = x_new
            data['z'] = self.entry_z.get().strip() or 'cmor1.5-1.0'

        # --- Обычные (Линия, Точечная, 3D и пр.) ---
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

        # --- Мета-обновления ---
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

    def _add_fit(self, kind):
        sel = self._get_selected_indices()
        if not sel:
            messagebox.showwarning(tr.t('msg.warning'),
                                   tr.t('msg.select_object_short'))
            return
        data = self.graphs_data[sel[0]]

        # Универсальная проверка: подходят ли данные для fit'а
        try:
            x = np.asarray(data.get('x', []), dtype=float)
            y = np.asarray(data.get('y', []), dtype=float)
        except (TypeError, ValueError):
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.trend_only_2d'))
            return
        if x.size < 3 or y.size < 3:
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.trend_only_2d'))
            return

        mask = np.isfinite(x) & np.isfinite(y)
        x, y = x[mask], y[mask]
        if len(x) < 3:
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.trend_only_2d'))
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

        try:
            x = np.asarray(data.get('x', []), dtype=float)
            y = np.asarray(data.get('y', []), dtype=float)
        except (TypeError, ValueError):
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.trend_only_2d'))
            return
        mask = np.isfinite(x) & np.isfinite(y)
        x, y = x[mask], y[mask]

        deg = self.fit_degree_var.get()
        if deg >= len(x):
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.trend_degree'))
            return
        try:
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
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

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

    def _snapshot(self, description=""):
        try:
            self._mark_modified()
        except Exception:
            pass
        if description:
            self._show_history(description)
        snap = {
            'graphs': [
                {k: v for k, v in d.items()
                 if k not in ('artist', '_extra_artists', '_cleanup')}
                for d in self.graphs_data
            ],
            'folders': list(self.folders),
            'subplot_rows': self.subplot_rows,
            'subplot_cols': self.subplot_cols,
        }
        self.undo_stack.append(snap)
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _undo(self):
        if not self.undo_stack:
            self.status_var.set(tr.t('status.nothing_undo'))
            return
        current = {
            'graphs': [
                {k: v for k, v in d.items()
                 if k not in ('artist', '_extra_artists', '_cleanup')}
                for d in self.graphs_data
            ],
            'folders': list(self.folders),
            'subplot_rows': self.subplot_rows,
            'subplot_cols': self.subplot_cols,
        }
        self.redo_stack.append(current)
        self._restore_snapshot(self.undo_stack.pop())
        self._show_history(tr.t('status.undo'))
        self.status_var.set(tr.t('status.undo'))

    def _redo(self):
        if not self.redo_stack:
            self.status_var.set(tr.t('status.nothing_redo'))
            return
        current = {
            'graphs': [
                {k: v for k, v in d.items()
                 if k not in ('artist', '_extra_artists', '_cleanup')}
                for d in self.graphs_data
            ],
            'folders': list(self.folders),
            'subplot_rows': self.subplot_rows,
            'subplot_cols': self.subplot_cols,
        }
        self.undo_stack.append(current)
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
        self._restore_snapshot(self.redo_stack.pop())
        self._show_history(tr.t('status.redo'))
        self.status_var.set(tr.t('status.redo'))

    def _restore_snapshot(self, snap):
        self._stop_animation()

        # Backward-compat: старый формат — просто список графов
        if isinstance(snap, dict):
            graphs_snap = snap.get('graphs', [])
            folders_snap = snap.get('folders')
            rows_snap = snap.get('subplot_rows')
            cols_snap = snap.get('subplot_cols')
        else:
            graphs_snap = snap
            folders_snap = None
            rows_snap = None
            cols_snap = None

        # Восстанавливаем сетку subplot'ов, если снапшот её хранит
        if rows_snap is not None and cols_snap is not None:
            self.subplot_rows = int(rows_snap)
            self.subplot_cols = int(cols_snap)
            try:
                self.subplot_grid_var.set(
                    f"{self.subplot_rows}x{self.subplot_cols}")
                self.subplot_index_spin.configure(
                    to=self.subplot_rows * self.subplot_cols - 1)
            except Exception:
                pass

        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        self.fig.clear()

        needs_3d = any("3D" in d['type'] for d in graphs_snap)
        needs_polar = any(d['type'] in ("Радиальная", "Полярный scatter",
                                        "Полярная теплокарта",
                                        "Роза ветров",
                                        "Диаграмма Тейлора")
                          for d in graphs_snap)
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
        self._apply_grid_to_axes(self.axes)
        self.graphs_data = []

        # Папки: из снапшота, если есть; иначе — минимум
        if folders_snap is not None:
            self.folders = list(folders_snap) or [""]
        else:
            self.folders = [""]

        for d in graphs_snap:
            d = dict(d)
            for k, v in [('folder', ''), ('box_data', []),
                         ('heatmap_data', []), ('yerr_matrix', []),
                         ('smooth', False),
                         ('fill', False), ('glow', False),
                         ('notes', ''), ('treemap_parents', []),
                         ('col_labels', []), ('dst_labels', []),
                         ('subplot_index', 0),
                         ('unit_x', '—'), ('unit_y', '—'),
                         ('unit_z', '—'),
                         ('visible', True),
                         ('_extra_artists', []), ('_cleanup', None)]:
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
