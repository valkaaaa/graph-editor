import os
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np

from translator import tr


class CodeExportMixin:

    def export_python_code(self):
        if not self.graphs_data:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.no_data'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.py',
            filetypes=[('Python', '*.py')])
        if not path:
            return
        try:
            code = self._generate_python_code()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(code)
            self._show_history(tr.t('hist.exported_python',
                                     name=os.path.basename(path)))
            messagebox.showinfo(tr.t('msg.done'),
                                 tr.t('msg.python_exported', path=path))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'), str(e))

    # ---------- внутреннее ----------

    @staticmethod
    def _fmt_num(v):
        if isinstance(v, (int, float, np.integer, np.floating)):
            v = v.item() if hasattr(v, 'item') else v
            return repr(v)
        return repr(v)

    def _fmt_arr(self, arr):
        return '[' + ', '.join(self._fmt_num(v) for v in arr) + ']'

    def _generate_python_code(self) -> str:
        L = []
        L.append('# -*- coding: utf-8 -*-')
        L.append(f'"""Сгенерировано GraphEditor Pro. '
                 f'Объектов: {len(self.graphs_data)}"""')
        L.append('')
        L.append('import matplotlib.pyplot as plt')
        L.append('import numpy as np')
        has_3d = any('3D' in d['type'] for d in self.graphs_data)
        if has_3d:
            L.append('from mpl_toolkits.mplot3d import Axes3D  # noqa: F401')
        L.append('')
        L.append('fig = plt.figure(figsize=(10, 6))')
        proj = ", projection='3d'" if has_3d else ''
        L.append(f'ax = fig.add_subplot(111{proj})')
        L.append('')

        for i, d in enumerate(self.graphs_data):
            L.append(f'# --- {i+1}. {d["label"]} ({d["type"]}) ---')
            try:
                L.extend(self._emit_object_code(d))
            except Exception as e:
                L.append(f'# (ошибка генерации: {e})')
            L.append('')

        L.append(f'ax.set_title({self.plot_title_var.get()!r})')
        L.append(f'ax.set_xlabel({self.plot_xlabel_var.get()!r})')
        L.append(f'ax.set_ylabel({self.plot_ylabel_var.get()!r})')
        if self.show_grid_var.get():
            L.append('ax.grid(True, linestyle="--", alpha=0.6)')
        L.append('ax.legend()')
        L.append('fig.tight_layout()')
        L.append('plt.show()')
        return '\n'.join(L)

    def _emit_object_code(self, d) -> list:
        t = d['type']
        c = d.get('color', 'blue')
        lbl = d.get('label', '')
        x = d.get('x') or []
        y = d.get('y') or []
        z = d.get('z') or []
        lw = d.get('lw', 2.0)
        ls = d.get('ls', '-')
        ms = d.get('ms', 6.0)
        marker = d.get('marker', 'o')
        out = []

        def arr(a):
            return self._fmt_arr(a)

        if t == 'Линия':
            out.append(f'ax.plot({arr(x)}, {arr(y)}, color={c!r}, lw={lw}, '
                       f'ls={ls!r}, marker={marker!r}, ms={ms}, label={lbl!r})')
            if d.get('fill'):
                out.append(f'ax.fill_between({arr(x)}, {arr(y)}, '
                           f'alpha=0.3, color={c!r})')
        elif t == 'Точечная':
            out.append(f'ax.scatter({arr(x)}, {arr(y)}, color={c!r}, '
                       f's={ms**2}, marker={marker!r}, label={lbl!r})')
        elif t == 'Столбчатая':
            out.append(f'ax.bar({arr(x)}, {arr(y)}, color={c!r}, label={lbl!r})')
        elif t == 'Гистограмма':
            bins = d.get('bins', 10)
            out.append(f'ax.hist({arr(x)}, bins={bins}, color={c!r}, '
                       f'alpha=0.75, label={lbl!r})')
        elif t == 'Круговая':
            labels = d.get('pie_labels') or [str(i) for i in range(len(y))]
            out.append(f'ax.pie({arr(y)}, labels={labels!r}, autopct="%1.1f%%")')
        elif t == 'Step plot':
            out.append(f'ax.step({arr(x)}, {arr(y)}, where="post", '
                       f'color={c!r}, lw={lw}, label={lbl!r})')
        elif t == 'Полигон':
            if x and y:
                xs, ys = list(x) + [x[0]], list(y) + [y[0]]
                out.append(f'ax.plot({self._fmt_arr(xs)}, {self._fmt_arr(ys)}, '
                           f'color={c!r}, lw={lw}, label={lbl!r})')
                out.append(f'ax.fill({arr(x)}, {arr(y)}, color={c!r}, alpha=0.4)')
        elif t == 'Столбчатая с накоплением':
            series = d.get('box_data') or [y]
            for s in series:
                out.append(f'ax.bar({arr(x)}, {arr(s)}, label={lbl!r})')
        elif t == 'Box plot':
            groups = d.get('box_data') or []
            if groups:
                out.append(f'ax.boxplot({groups!r}, patch_artist=True)')
        elif t == 'Violin':
            groups = d.get('box_data') or []
            if groups:
                out.append(f'ax.violinplot({groups!r})')
        elif t in ('Heatmap', 'Imshow'):
            hm = d.get('heatmap_data') or []
            if hm:
                out.append(f'ax.imshow(np.array({hm!r}), cmap="viridis", '
                           f'aspect="auto")')
        elif t == 'Contour':
            hm = d.get('heatmap_data') or []
            if hm:
                out.append(f'ax.contour(np.array({hm!r}), cmap="viridis")')
        elif t == '3D Линия':
            out.append(f'ax.plot3D({arr(x)}, {arr(y)}, {arr(z)}, '
                       f'color={c!r}, lw={lw}, label={lbl!r})')
        elif t == '3D Точечная':
            out.append(f'ax.scatter3D({arr(x)}, {arr(y)}, {arr(z)}, '
                       f'color={c!r}, s={ms**2}, label={lbl!r})')
        elif t == '3D Поверхность':
            hm = d.get('heatmap_data') or []
            if hm:
                m, n = len(hm), len(hm[0])
                out.append(f'_X, _Y = np.meshgrid(np.arange({n}), np.arange({m}))')
                out.append(f'ax.plot_surface(_X, _Y, np.array({hm!r}), '
                           f'cmap="viridis")')
        elif t == '3D Сетка':
            hm = d.get('heatmap_data') or []
            if hm:
                m, n = len(hm), len(hm[0])
                out.append(f'_X, _Y = np.meshgrid(np.arange({n}), np.arange({m}))')
                out.append(f'ax.plot_wireframe(_X, _Y, np.array({hm!r}), '
                           f'color={c!r})')
        else:
            # универсальная аппроксимация
            if x and y:
                out.append(f'# fallback для типа {t!r}')
                out.append(f'ax.plot({arr(x)}, {arr(y)}, label={lbl!r})')
        return out