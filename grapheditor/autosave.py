# autosave.py
"""Автосохранение всех открытых документов в ~/.grapheditor/autosave.graphxtemp.

Формат: zip с одним файлом autosave.json внутри.

Восстановление:
  - автоматически при старте (_check_autosave_on_start);
  - вручную — перетаскиванием .graphxtemp в окно (_on_drop).
"""
import datetime
import json
import logging
import os
import tempfile
import zipfile

from tkinter import messagebox

from config import config_dir


log = logging.getLogger('autosave')

AUTOSAVE_NAME = "autosave.graphxtemp"


def autosave_path():
    return os.path.join(config_dir(), AUTOSAVE_NAME)


class AutosaveMixin:

    # ------------------------------------------------------------------
    # Инициализация
    # ------------------------------------------------------------------
    def _init_autosave(self, interval_ms=60_000):
        self._autosave_interval = interval_ms
        self._autosave_path = autosave_path()
        self.root.after(interval_ms, self._autosave_tick)

    def _autosave_tick(self):
        try:
            if self._has_unsaved_changes():
                self._do_autosave()
        except Exception:
            log.exception("autosave tick failed")
        finally:
            self.root.after(self._autosave_interval, self._autosave_tick)

    def _has_unsaved_changes(self):
        try:
            return any(getattr(d, 'modified', False) for d in self.documents)
        except Exception:
            return bool(self.graphs_data)

    # ------------------------------------------------------------------
    # Запись
    # ------------------------------------------------------------------
    def _do_autosave(self):
        path = self._autosave_path
        payload = {
            'format': 'graphxtemp',
            'created': datetime.datetime.now().isoformat(),
            'active': getattr(self, 'current_doc_idx', 0),
            'settings': self.settings,
            'documents': [],
        }
        for d in self.documents:
            payload['documents'].append({
                'name': d.name,
                'path': d.path,
                'title': d.plot_title,
                'xlabel': d.plot_xlabel,
                'ylabel': d.plot_ylabel,
                'subplot_grid': [d.subplot_rows, d.subplot_cols],
                'folders': d.folders,
                'graphs': [
                    {k: v for k, v in g.items() if k != 'artist'}
                    for g in d.graphs_data
                ],
            })

        try:
            with tempfile.TemporaryDirectory() as td:
                ap = os.path.join(td, 'autosave.json')
                with open(ap, 'w', encoding='utf-8') as f:
                    json.dump(
                        payload, f,
                        ensure_ascii=False, indent=2,
                        default=lambda o: o.tolist()
                        if hasattr(o, 'tolist') else str(o),
                    )
                with zipfile.ZipFile(path, 'w',
                                     zipfile.ZIP_DEFLATED) as zf:
                    zf.write(ap, 'autosave.json')
        except Exception:
            log.exception("autosave write failed")
            return

    # ------------------------------------------------------------------
    # Проверка при старте
    # ------------------------------------------------------------------
    def _check_autosave_on_start(self):
        path = self._autosave_path
        if not os.path.exists(path):
            return
        try:
            mtime = datetime.datetime.fromtimestamp(
                os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
        except Exception:
            mtime = "?"

        ans = messagebox.askyesnocancel(
            "Автосохранение",
            f"Найден файл автосохранения от {mtime}.\n\n"
            f"«Да» — открыть\n"
            f"«Нет» — удалить\n"
            f"«Отмена» — оставить до следующего запуска",
            parent=self.root,
        )
        if ans is True:
            self._load_autosave(path)
        elif ans is False:
            try:
                os.remove(path)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Восстановление
    # ------------------------------------------------------------------
    def _load_autosave(self, path):
        try:
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(td)
                with open(os.path.join(td, 'autosave.json'),
                          'r', encoding='utf-8') as f:
                    data = json.load(f)
        except Exception as e:
            log.exception("autosave load failed")
            messagebox.showerror(
                "Ошибка",
                f"Не удалось открыть автосохранение:\n{e}")
            return

        # Закрываем все вкладки — включая последнюю.
        # ВАЖНО: нельзя использовать `while self.documents:
        # _close_document(0, ...)`, потому что _close_document при
        # len == 1 вызывает _reset_document и НЕ удаляет документ
        # из списка — получился бы бесконечный цикл (старый баг).
        self._close_all_documents_for_restore()

        docs = data.get('documents') or []
        if not docs:
            self._new_document(switch=True)
            self._show_history("Автосохранение восстановлено (пусто)")
            return

        for i, dd in enumerate(docs):
            self._new_document(
                switch=True,
                name=dd.get('name', f'Doc {i + 1}'))
            doc = self.documents[-1]
            doc.plot_title = dd.get('title', 'График')
            doc.plot_xlabel = dd.get('xlabel', 'X')
            doc.plot_ylabel = dd.get('ylabel', 'Y')
            doc.folders = dd.get('folders', [''])
            doc.hidden_folders = set()

            grid = dd.get('subplot_grid', [1, 1])
            try:
                rows = int(grid[0])
                cols = int(grid[1])
            except (TypeError, ValueError, IndexError):
                rows = cols = 1
            doc.subplot_rows = max(1, rows)
            doc.subplot_cols = max(1, cols)

            doc.graphs_data = []
            for g in dd.get('graphs', []):
                g['artist'] = None
                g['_extra_artists'] = []
                g['_cleanup'] = None
                doc.graphs_data.append(g)

        idx = min(max(int(data.get('active', 0)), 0),
                  len(self.documents) - 1)
        self._switch_document(idx)
        doc = self.documents[idx]

        self.subplot_grid_var.set(
            f"{doc.subplot_rows}x{doc.subplot_cols}")
        self.subplot_rows = doc.subplot_rows
        self.subplot_cols = doc.subplot_cols
        self.subplot_index_spin.configure(
            to=self.subplot_rows * self.subplot_cols - 1)
        self._rebuild_subplots()

        # Пересоздаём artist'ы на текущих осях
        for g in doc.graphs_data:
            if g.get('subplot_index', 0) >= len(self.axes):
                g['subplot_index'] = 0
            g['artist'] = self._create_artist(g)

        self._update_listbox()
        self._redraw()
        self._show_history("Автосохранение восстановлено")

    # ------------------------------------------------------------------
    # Утилита: закрыть ВСЕ вкладки (в т.ч. последнюю)
    # ------------------------------------------------------------------
    def _close_all_documents_for_restore(self):
        """Удаляет все документы, включая последний, и сбрасывает
        current_doc_idx в -1.

        Отличие от _close_document(): тот при len == 1 вызывает
        _reset_document и НЕ удаляет документ из списка — для цикла
        восстановления это означало бы бесконечный цикл.
        """
        for doc in list(self.documents):
            try:
                doc.canvas.get_tk_widget().destroy()
            except Exception:
                pass
            try:
                self.plot_notebook.forget(doc.plot_frame)
            except Exception:
                pass
        self.documents.clear()
        self.current_doc_idx = -1