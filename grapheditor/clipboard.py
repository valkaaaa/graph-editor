"""Копирование / вставка / вырезание объектов между документами."""
import copy
import tkinter as tk
from tkinter import ttk

from translator import tr


class ClipboardMixin:

    def _is_text_input_focused(self, event=None):
        """True, если фокус находится в поле ввода (Entry, Text, Spinbox, Combobox)."""
        try:
            # event.widget надежнее, чем focus_get(), так как точно указывает на цель
            w = event.widget if event else self.root.focus_get()
            if w is None:
                return False

            # 1. Проверка через isinstance (самый надежный способ)
            if isinstance(w, (tk.Entry, tk.Text, ttk.Entry, ttk.Combobox, ttk.Spinbox)):
                return True

            # 2. Проверка по классу виджета (на случай вложенных элементов)
            cls_name = w.winfo_class()
            if cls_name in ('Entry', 'Text', 'TEntry', 'TCombobox', 'TSpinbox', 'Spinbox'):
                return True

            return False
        except Exception:
            return False

    def _copy_selected(self, cut=False):
        """Копирование или вырезание выбранных объектов в дереве."""
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
        """Вставка скопированных объектов на холст."""
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
        if self._is_text_input_focused(event):
            w = event.widget if event else self.root.focus_get()
            if w:
                w.event_generate('<<Copy>>')
            return 'break'
        self._copy_selected(cut=False)
        return 'break'

    def _hk_cut(self, event=None):
        if self._is_text_input_focused(event):
            w = event.widget if event else self.root.focus_get()
            if w:
                w.event_generate('<<Cut>>')
            return 'break'
        self._copy_selected(cut=True)
        return 'break'

    def _hk_paste(self, event=None):
        if self._is_text_input_focused(event):
            w = event.widget if event else self.root.focus_get()
            if w:
                w.event_generate('<<Paste>>')
            return 'break'
        self._paste_objects()
        return 'break'

    def _hk_select_all(self, event=None):
        """Выделить всё (работает и в текстовых полях, и в дереве объектов)."""
        if self._is_text_input_focused(event):
            w = event.widget if event else self.root.focus_get()
            try:
                if hasattr(w, 'select_range'):  # Entry, Spinbox, Combobox
                    w.select_range(0, tk.END)
                    w.icursor(tk.END)
                elif hasattr(w, 'tag_add'):     # Text
                    w.tag_add(tk.SEL, "1.0", tk.END)
                    w.mark_set(tk.INSERT, "1.0")
                    w.see(tk.INSERT)
            except Exception:
                pass
            return 'break'

        # Если фокус не в тексте, выделяем все объекты в дереве
        try:
            if hasattr(self, 'graph_tree') and self.graph_tree.winfo_exists():
                all_items = self.graph_tree.get_children()
                self.graph_tree.selection_set(all_items)
        except Exception:
            pass
        return 'break'