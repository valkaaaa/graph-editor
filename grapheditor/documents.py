import tkinter as tk
from tkinter import ttk, messagebox


class Document:
    def __init__(self, name="Без имени"):
        self.name = name
        self.path = None
        self.modified = False
        self.fig = None
        self.axes = []
        self.ax = None
        self.axes_secondary = {}
        self.canvas = None
        self.toolbar = None
        self.plot_frame = None
        self.graphs_data = []
        self.folders = [""]
        self.hidden_folders = set()
        self.line_counter = 0
        self.subplot_rows = 1
        self.subplot_cols = 1
        self.undo_stack = []
        self.redo_stack = []
        self.plot_title = "График"
        self.plot_xlabel = "X"
        self.plot_ylabel = "Y"


class DocumentsMixin:

    def _init_documents(self):
        self.documents = []
        self.current_doc_idx = -1
        self._new_document(switch=True)

    def _new_document(self, switch=True, name=None):
        if name is None:
            name = f"Без имени {len(self.documents) + 1}"
        frame = ttk.Frame(self.plot_notebook)
        self.plot_notebook.add(frame, text=name)
        doc = Document(name=name)
        doc.plot_frame = frame
        self.documents.append(doc)

        prev_idx = self.current_doc_idx
        self.current_doc_idx = len(self.documents) - 1
        self.plot_frame = frame

        # Свежие стеки для нового документа
        self.graphs_data = []
        self.folders = [""]
        self.hidden_folders = set()
        self.line_counter = 0
        self.subplot_rows = 1
        self.subplot_cols = 1
        self.subplot_grid_var.set("1x1")
        self.undo_stack = []
        self.redo_stack = []

        self._setup_plot(parent=frame)
        self._save_current_state_to_doc()

        if switch:
            self.plot_notebook.select(frame)
        else:
            # откат
            self.current_doc_idx = prev_idx
            if prev_idx >= 0:
                self._load_state_from_doc(self.documents[prev_idx])
        return doc

    def _on_plot_tab_changed(self, event=None):
        try:
            idx = self.plot_notebook.index(self.plot_notebook.select())
        except Exception:
            return
        if idx == self.current_doc_idx:
            return
        self._switch_document(idx)

    def _switch_document(self, idx):
        if idx < 0 or idx >= len(self.documents):
            return
        if idx == self.current_doc_idx:
            return
        if self.current_doc_idx >= 0:
            self._save_current_state_to_doc()
        self.current_doc_idx = idx
        self._load_state_from_doc(self.documents[idx])
        self._init_tooltip()
        self._init_crosshair()
        self._update_listbox()
        self._refresh_stats()
        try:
            self.canvas.draw_idle()
        except Exception:
            pass

    def _save_current_state_to_doc(self):
        if self.current_doc_idx < 0:
            return
        d = self.documents[self.current_doc_idx]
        d.fig = getattr(self, 'fig', None)
        d.axes = getattr(self, 'axes', [])
        d.ax = getattr(self, 'ax', None)
        d.axes_secondary = getattr(self, 'axes_secondary', {})
        d.canvas = getattr(self, 'canvas', None)
        d.toolbar = getattr(self, 'toolbar', None)
        d.graphs_data = getattr(self, 'graphs_data', [])
        d.folders = getattr(self, 'folders', [''])
        d.hidden_folders = getattr(self, 'hidden_folders', set())
        d.line_counter = getattr(self, 'line_counter', 0)
        d.subplot_rows = self.subplot_rows
        d.subplot_cols = self.subplot_cols
        d.undo_stack = self.undo_stack
        d.redo_stack = self.redo_stack
        d.plot_title = self.plot_title_var.get()
        d.plot_xlabel = self.plot_xlabel_var.get()
        d.plot_ylabel = self.plot_ylabel_var.get()

    def _load_state_from_doc(self, d):
        self.fig = d.fig
        self.axes = d.axes
        self.ax = d.ax
        self.axes_secondary = d.axes_secondary
        self.canvas = d.canvas
        self.toolbar = d.toolbar
        self.plot_frame = d.plot_frame
        self.graphs_data = d.graphs_data
        self.folders = d.folders
        self.hidden_folders = d.hidden_folders
        self.line_counter = d.line_counter
        self.subplot_rows = d.subplot_rows
        self.subplot_cols = d.subplot_cols
        self.undo_stack = d.undo_stack
        self.redo_stack = d.redo_stack
        self.plot_title_var.set(d.plot_title)
        self.plot_xlabel_var.set(d.plot_xlabel)
        self.plot_ylabel_var.set(d.plot_ylabel)
        self.subplot_grid_var.set(f"{d.subplot_rows}x{d.subplot_cols}")
        try:
            self.subplot_index_spin.configure(
                to=d.subplot_rows * d.subplot_cols - 1)
        except Exception:
            pass

    def _close_document(self, idx, ask=True, silent=False):
        if idx < 0 or idx >= len(self.documents):
            return
        doc = self.documents[idx]
        if ask and getattr(doc, 'modified', False):
            ans = messagebox.askyesnocancel(
                "Закрыть документ",
                f"«{doc.name}» был изменён. Сохранить перед закрытием?",
                parent=self.root)
            if ans is None:
                return
            if ans is True:
                self._switch_document(idx)
                self._save_json()
        if len(self.documents) == 1:
            self._reset_document(doc)
            return
        try:
            doc.canvas.get_tk_widget().destroy()
        except Exception:
            pass
        try:
            self.plot_notebook.forget(doc.plot_frame)
        except Exception:
            pass
        was_current = (idx == self.current_doc_idx)
        self.documents.pop(idx)
        if was_current:
            new_idx = max(0, min(idx, len(self.documents) - 1))
            self.current_doc_idx = -1
            self._switch_document(new_idx)

    def _reset_document(self, doc):
        doc.graphs_data = []
        doc.folders = [""]
        doc.hidden_folders = set()
        doc.line_counter = 0
        doc.undo_stack = []
        doc.redo_stack = []
        doc.modified = False
        doc.path = None
        if self.current_doc_idx >= 0 \
                and self.documents[self.current_doc_idx] is doc:
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
            self.canvas.draw()
            self._update_listbox()

    def _next_document(self):
        if not self.documents:
            return
        idx = (self.current_doc_idx + 1) % len(self.documents)
        self.plot_notebook.select(self.documents[idx].plot_frame)

    def _prev_document(self):
        if not self.documents:
            return
        idx = (self.current_doc_idx - 1) % len(self.documents)
        self.plot_notebook.select(self.documents[idx].plot_frame)

    def _mark_modified(self):
        if self.current_doc_idx >= 0:
            self.documents[self.current_doc_idx].modified = True
            try:
                base = "GraphEditor Pro"
                name = self.documents[self.current_doc_idx].name
                self.root.title(f"{base} — {name} *")
            except Exception:
                pass
