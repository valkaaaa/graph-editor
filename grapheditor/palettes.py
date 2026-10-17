import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from translator import tr


PALETTES = {
    'tab10':    'Tableau 10',
    'tab20':    'Tableau 20',
    'Set1':     'Set1',
    'Set2':     'Set2',
    'Set3':     'Set3',
    'Paired':   'Paired',
    'Dark2':    'Dark2',
    'Pastel1':  'Pastel1',
    'viridis':  'Viridis',
    'plasma':   'Plasma',
    'inferno':  'Inferno',
    'magma':    'Magma',
    'cividis':  'Cividis',
    'coolwarm': 'Cool–Warm',
    'RdYlGn':   'Red–Yellow–Green',
}


class PalettesMixin:

    def _colors_from_palette(self, name, n):
        """Возвращает список hex-цветов из палитры."""
        if n <= 0:
            return []
        try:
            cmap = matplotlib.colormaps.get_cmap(name)
        except Exception:
            try:
                cmap = plt.get_cmap(name)
            except Exception:
                cmap = plt.get_cmap('tab10')
        # дискретные палитры (tab10, Set1 …) — используем как есть
        base_colors = getattr(cmap, 'colors', None)
        if base_colors:
            return [mcolors.to_hex(base_colors[i % len(base_colors)])
                    for i in range(n)]
        # непрерывные — берём n точек
        return [mcolors.to_hex(cmap(i / max(n - 1, 1)))
                for i in range(n)]

    def _apply_palette(self, name, indices=None):
        if indices is None:
            indices = self._get_selected_indices()
        if not indices:
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('msg.select_object_short'))
            return
        colors = self._colors_from_palette(name, len(indices))
        self._snapshot(tr.t('hist.palette_applied',
                             name=PALETTES.get(name, name),
                             count=len(indices)))
        for idx, color in zip(indices, colors):
            d = self.graphs_data[idx]
            d['color'] = color
            self._destroy_object(d)
            d['artist'] = self._create_artist(d)
        self._update_listbox()
        self._redraw()

    def _show_palette_dialog(self):
        indices = self._get_selected_indices()
        if not indices:
            messagebox.showwarning(tr.t('msg.warning'),
                                    tr.t('msg.select_object_short'))
            return
        win = tk.Toplevel(self.root)
        win.title(tr.t('msg.palette_title'))
        win.transient(self.root)
        win.geometry('420x480')

        ttk.Label(win, text=tr.t('msg.palette_pick'),
                  font=('Arial', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))

        canvas = tk.Canvas(win, height=40, bg='#f0f0f0', highlightthickness=0)
        canvas.pack(fill=tk.X, padx=10, pady=5)

        names = list(PALETTES.keys())
        listbox = tk.Listbox(win, height=12, exportselection=False,
                              font=('Consolas', 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for k in names:
            listbox.insert(tk.END, f'  {PALETTES[k]}')

        n_preview = max(len(indices), 5)

        def draw_preview(*_):
            sel = listbox.curselection()
            if not sel:
                return
            colors = self._colors_from_palette(names[sel[0]], n_preview)
            canvas.delete('all')
            w = max(canvas.winfo_width(), 200)
            block = w / len(colors)
            for i, c in enumerate(colors):
                canvas.create_rectangle(i * block, 0, (i + 1) * block, 40,
                                          fill=c, outline='')

        listbox.bind('<<ListboxSelect>>', draw_preview)
        listbox.selection_set(0)
        win.after(80, draw_preview)

        def do_apply():
            sel = listbox.curselection()
            if not sel:
                return
            name = names[sel[0]]
            win.destroy()
            self._apply_palette(name, indices)

        bf = ttk.Frame(win, padding=8)
        bf.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(bf, text=tr.t('msg.palette_cancel'),
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bf, text=tr.t('msg.palette_apply'),
                    command=do_apply).pack(side=tk.RIGHT, padx=2)