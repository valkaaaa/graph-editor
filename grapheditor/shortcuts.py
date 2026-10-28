"""Редактируемые горячие клавиши + диалог настройки."""
import tkinter as tk
from tkinter import ttk, messagebox

from translator import tr


# action_id → (default_sequence, human_description_key)
DEFAULT_HOTKEYS = {
    'save':              ('<Control-s>',        'hotkey.save'),
    'save_as':           ('<Control-Shift-S>',  'hotkey.save_as'),
    'open':              ('<Control-o>',        'hotkey.open'),
    'save_image':        ('<Control-p>',        'hotkey.save_image'),
    'export_excel':      ('<Control-e>',        'hotkey.export_excel'),
    'undo':              ('<Control-z>',        'hotkey.undo'),
    'redo':              ('<Control-y>',        'hotkey.redo'),
    'duplicate':         ('<Control-d>',        'hotkey.duplicate'),
    'clear_all':         ('<Control-Shift-N>',  'hotkey.clear_all'),
    'new_doc':           ('<Control-n>',        'hotkey.new_doc'),
    'close_doc':         ('<Control-w>',        'hotkey.close_doc'),
    'next_doc':          ('<Control-Tab>',      'hotkey.next_doc'),
    'prev_doc':          ('<Control-Shift-Tab>','hotkey.prev_doc'),
    'console':           ('<Control-grave>',    'hotkey.console'),
    'redraw':            ('<F5>',               'hotkey.redraw'),
    'fullscreen':        ('<F11>',              'hotkey.fullscreen'),
    'search':            ('<Control-f>',        'hotkey.search'),
    'copy':              ('<Control-c>',        'hotkey.copy'),
    'paste':             ('<Control-v>',        'hotkey.paste'),
    'cut':               ('<Control-x>',        'hotkey.cut'),
    'delete':            ('<Delete>',           'hotkey.delete'),
    'toggle_visibility': ('<Control-h>',        'hotkey.toggle_visibility'),
}


def _event_to_sequence(event):
    """<Control-Shift-S> из события Tkinter."""
    mods = []
    if event.state & 0x4:
        mods.append('Control')
    if event.state & 0x1:
        mods.append('Shift')
    if event.state & 0x8:
        mods.append('Alt')
    if event.state & 0x40:
        mods.append('Meta')

    keysym = event.keysym
    if not keysym:
        return None
    if keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R',
                  'Alt_L', 'Alt_R', 'Meta_L', 'Meta_R',
                  'Super_L', 'Super_R', 'Escape'):
        return None
    if len(keysym) == 1:
        keysym = keysym.upper() if 'Shift' in mods else keysym.lower()

    return f"<{'-'.join(mods + [keysym])}>" if mods else f"<{keysym}>"


class ShortcutsMixin:

    def _get_hotkeys(self):
        """Возвращает слитый словарь (дефолт + сохранённые)."""
        result = {a: seq for a, (seq, _) in DEFAULT_HOTKEYS.items()}
        saved = self.settings.get('hotkeys', {})
        if isinstance(saved, dict):
            result.update({k: v for k, v in saved.items()
                           if k in DEFAULT_HOTKEYS})
        return result

    def _bind_hotkeys(self):
        # Отвязать старые
        for seq in getattr(self, '_bound_hotkeys', []):
            try:
                self.root.unbind(seq)
            except Exception:
                pass
        self._bound_hotkeys = []

        handlers = {
            'save':              lambda e: self._save_json(),
            'save_as':           lambda e: self._save_json_as(),
            'open':              lambda e: self._load_json(),
            'save_image':        lambda e: self._save_image(),
            'export_excel':      lambda e: self._export_excel(),
            'undo':              lambda e: self._undo(),
            'redo':              lambda e: self._redo(),
            'duplicate':         lambda e: self._duplicate_graph(),
            'clear_all':         lambda e: self._clear_all(),
            'new_doc':           lambda e: self._new_document(switch=True),
            'close_doc':         lambda e: self._close_document(
                                                self.current_doc_idx),
            'next_doc':          lambda e: self._next_document(),
            'prev_doc':          lambda e: self._prev_document(),
            'console':           lambda e: self._open_console(),
            'redraw':            lambda e: self._redraw(),
            'fullscreen':        lambda e: self._toggle_fullscreen(),
            'search':            lambda e: self._focus_search(),
            'copy':              self._hk_copy,
            'cut':               self._hk_cut,
            'paste':             self._hk_paste,
            'delete':            self._on_delete_key,
            'toggle_visibility': lambda e: self._toggle_visibility(),
        }

        for action, seq in self._get_hotkeys().items():
            fn = handlers.get(action)
            if not fn or not seq:
                continue
            try:
                self.root.bind(seq, fn)
                self._bound_hotkeys.append(seq)
            except Exception:
                pass

    def _open_hotkey_editor(self):
        win = tk.Toplevel(self.root)
        win.title(tr.t('hotkey.editor_title'))
        win.transient(self.root)
        win.geometry('520x520')

        ttk.Label(win, text=tr.t('hotkey.editor_hint'),
                  foreground='gray').pack(anchor=tk.W, padx=10, pady=(10, 4))

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        tree = ttk.Treeview(frame, columns=('action', 'seq'),
                             show='headings', height=18)
        tree.heading('action', text=tr.t('hotkey.col_action'))
        tree.heading('seq', text=tr.t('hotkey.col_seq'))
        tree.column('action', width=280, anchor=tk.W)
        tree.column('seq', width=180, anchor=tk.CENTER)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=sb.set)

        current = self._get_hotkeys()

        for action in DEFAULT_HOTKEYS:
            desc = tr.t(DEFAULT_HOTKEYS[action][1])
            tree.insert('', tk.END, iid=action,
                         values=(desc, current.get(action, '')))

        status = tk.StringVar(value='')
        ttk.Label(win, textvariable=status, foreground='#c0392b'
                  ).pack(anchor=tk.W, padx=10)

        capture_win = [None]

        def start_capture(item):
            if capture_win[0] is not None:
                try: capture_win[0].destroy()
                except Exception: pass
            status.set(tr.t('hotkey.press_combo'))
            cw = tk.Toplevel(win)
            cw.transient(win)
            cw.overrideredirect(True)
            cw.geometry('+2000+2000')     # за пределами экрана
            capture_win[0] = cw
            cw.focus_force()

            def on_key(event):
                if event.keysym == 'Escape':
                    status.set('')
                    cw.destroy(); capture_win[0] = None
                    return
                seq = _event_to_sequence(event)
                if not seq:
                    return
                tree.set(item, 'seq', seq)
                status.set('')
                cw.destroy(); capture_win[0] = None

            cw.bind('<KeyPress>', on_key)
            cw.after(10000, lambda: (status.set(''), cw.destroy())
                     if capture_win[0] is cw else None)

        def on_double_click(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            start_capture(item)

        tree.bind('<Double-1>', on_double_click)

        def reset_all():
            for action in DEFAULT_HOTKEYS:
                tree.set(action, 'seq', DEFAULT_HOTKEYS[action][0])

        def save():
            # Проверка на дубли
            seen = {}
            for action in DEFAULT_HOTKEYS:
                seq = tree.set(action, 'seq').strip()
                if not seq:
                    continue
                if seq in seen:
                    messagebox.showerror(
                        tr.t('msg.error'),
                        tr.t('hotkey.duplicate',
                             seq=seq, a=seen[seq],
                             b=tr.t(DEFAULT_HOTKEYS[action][1])))
                    return
                seen[seq] = tr.t(DEFAULT_HOTKEYS[action][1])

            new_hotkeys = {}
            for action in DEFAULT_HOTKEYS:
                seq = tree.set(action, 'seq').strip()
                if seq and seq != DEFAULT_HOTKEYS[action][0]:
                    new_hotkeys[action] = seq
            self.settings['hotkeys'] = new_hotkeys
            self._bind_hotkeys()
            win.destroy()
            self._show_history(tr.t('hist.hotkeys_saved'))

        bf = ttk.Frame(win, padding=8)
        bf.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Button(bf, text=tr.t('hotkey.reset_all'),
                    command=reset_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(bf, text=tr.t('msg.palette_cancel'),
                    command=win.destroy).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bf, text=tr.t('settings.save'),
                    command=save).pack(side=tk.RIGHT, padx=2)