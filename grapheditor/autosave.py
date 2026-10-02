# autosave.py
import os, json, zipfile, tempfile, datetime
from tkinter import messagebox
from config import config_dir

AUTOSAVE_NAME = "autosave.graphxtemp"

def autosave_path():
    return os.path.join(config_dir(), AUTOSAVE_NAME)


class AutosaveMixin:

    def _init_autosave(self, interval_ms=60_000):
        self._autosave_interval = interval_ms
        self._autosave_path = autosave_path()
        self.root.after(interval_ms, self._autosave_tick)

    def _autosave_tick(self):
        try:
            if self._has_unsaved_changes():
                self._do_autosave()
        except Exception as e:
            print(f"[autosave] {e}")
        finally:
            self.root.after(self._autosave_interval, self._autosave_tick)

    def _has_unsaved_changes(self):
        try:
            return any(getattr(d, 'modified', False) for d in self.documents)
        except Exception:
            return bool(self.graphs_data)

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
        with tempfile.TemporaryDirectory() as td:
            ap = os.path.join(td, 'autosave.json')
            with open(ap, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2,
                          default=lambda o: o.tolist()
                          if hasattr(o, 'tolist') else str(o))
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(ap, 'autosave.json')
        # сбрасываем флаг modified
        for d in self.documents:
            d.modified = False

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

    def _load_autosave(self, path):
        try:
            with tempfile.TemporaryDirectory() as td:
                with zipfile.ZipFile(path, 'r') as zf:
                    zf.extractall(td)
                with open(os.path.join(td, 'autosave.json'),
                          'r', encoding='utf-8') as f:
                    data = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть автосохранение:\n{e}")
            return

        # Закрываем все существующие документы
        while len(self.documents) > 0:
            self._close_document(0, ask=False, silent=True)

        docs = data.get('documents') or []
        if not docs:
            self._new_document(switch=True)
            return

        for i, dd in enumerate(docs):
            self._new_document(switch=True, name=dd.get('name', f'Doc {i+1}'))
            doc = self.documents[-1]
            doc.plot_title = dd.get('title', 'График')
            doc.plot_xlabel = dd.get('xlabel', 'X')
            doc.plot_ylabel = dd.get('ylabel', 'Y')
            doc.folders = dd.get('folders', [''])
            doc.hidden_folders = set()
            grid = dd.get('subplot_grid', [1, 1])
            doc.subplot_rows, doc.subplot_cols = grid[0], grid[1]
            doc.graphs_data = []
            for g in dd.get('graphs', []):
                g['artist'] = None
                doc.graphs_data.append(g)

        # Применяем к активному
        idx = min(data.get('active', 0), len(self.documents) - 1)
        self._switch_document(idx)
        doc = self.documents[idx]
        self.subplot_grid_var.set(f"{doc.subplot_rows}x{doc.subplot_cols}")
        self.subplot_rows, self.subplot_cols = doc.subplot_rows, doc.subplot_cols
        self._rebuild_subplots()
        for g in doc.graphs_data:
            g['artist'] = self._create_artist(g)
        self._update_listbox()
        self._redraw()
        self._show_history("Автосохранение восстановлено")
