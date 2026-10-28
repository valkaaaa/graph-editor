"""Копирование / вставка / вырезание объектов между документами."""
import copy

from translator import tr


class ClipboardMixin:

    def _is_text_input_focused(self):
        """True, если фокус в поле ввода — чтобы Ctrl+C не крал текст."""
        import tkinter as tk
        try:
            w = self.root.focus_get()
            if w is None:
                return False
            cls = str(w.winfo_class()).lower()
            return cls in ('entry', 'text', 'tentry', 'spibox', 'spinbox',
                           'ttk::entry', 'ttk::spinbox', 'combobox',
                           'ttk::combobox')
        except Exception:
            return False

    def _copy_selected(self, cut=False):
        sel = self._get_selected_indices()
        if not sel:
            return
        self._clipboard = []
        for idx in sel:
            d = self.graphs_data[idx]
            new = {k: v for k, v in d.items()
                   if k not in ('artist', '_extra_artists', '_cleanup')}
            for key in ('x', 'y', 'z', 'pie_labels', 'pie_colors', 'yerr',
                        'treemap_parents', 'col_labels', 'dst_labels',
                        'box_data', 'heatmap_data', 'yerr_matrix'):
                if key in d:
                    new[key] = copy.deepcopy(d[key])
            self._clipboard.append(new)

        if cut:
            self._snapshot(tr.t('hist.cut_objects', count=len(sel)))
            self._delete_graph()
        else:
            self._show_history(
                tr.t('hist.copied_objects', count=len(self._clipboard)))

    def _paste_objects(self):
        if not getattr(self, '_clipboard', None):
            self._show_history(tr.t('msg.clipboard_empty'))
            return
        self._snapshot(
            tr.t('hist.pasted_objects', count=len(self._clipboard)))
        for src in self._clipboard:
            d = copy.deepcopy(src)
            d['label'] = src.get('label', 'Object') + ' (paste)'
            d['artist'] = None
            d['_extra_artists'] = []
            d['_cleanup'] = None
            d.setdefault('visible', True)
            self.line_counter += 1
            d['artist'] = self._create_artist(d)
            self.graphs_data.append(d)
        self._update_listbox()
        self._redraw()

    # ---- Обёртки для хоткеев (с проверкой фокуса) ----

    def _hk_copy(self, event=None):
        if self._is_text_input_focused():
            return
        self._copy_selected(cut=False)
        return 'break'

    def _hk_cut(self, event=None):
        if self._is_text_input_focused():
            return
        self._copy_selected(cut=True)
        return 'break'

    def _hk_paste(self, event=None):
        if self._is_text_input_focused():
            return
        self._paste_objects()
        return 'break'