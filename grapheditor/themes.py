import os
import re
import json
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
import matplotlib as mpl


# ============================================================================
# ВСТРОЕННЫЕ ТЕМЫ
# ============================================================================
THEMES = {
    'light': {
        'name': 'Светлая', 'is_dark': False,
        'bg': '#f0f0f0', 'fg': '#000000', 'field': '#ffffff',
        'select': '#4b6eaf', 'button': '#e0e0e0',
        'button_active': '#d0d0d0', 'border': '#c0c0c0',
        'plot_bg': '#ffffff', 'grid': '#cccccc', 'axes': '#000000',
        'mpl_style': 'default',
    },
    'dark': {
        'name': 'Тёмная', 'is_dark': True,
        'bg': '#2b2b2b', 'fg': '#ffffff', 'field': '#3c3f41',
        'select': '#4b6eaf', 'button': '#3c3f41',
        'button_active': '#4b6eaf', 'border': '#555555',
        'plot_bg': '#2b2b2b', 'grid': '#555555', 'axes': '#ffffff',
        'mpl_style': 'dark_background',
    },
    'solarized_light': {
        'name': 'Solarized Light', 'is_dark': False,
        'bg': '#fdf6e3', 'fg': '#657b83', 'field': '#eee8d5',
        'select': '#268bd2', 'button': '#eee8d5',
        'button_active': '#d6cdb3', 'border': '#d3cbb7',
        'plot_bg': '#fdf6e3', 'grid': '#d6cdb3', 'axes': '#586e75',
        'mpl_style': 'default',
    },
    'solarized_dark': {
        'name': 'Solarized Dark', 'is_dark': True,
        'bg': '#002b36', 'fg': '#93a1a1', 'field': '#073642',
        'select': '#268bd2', 'button': '#073642',
        'button_active': '#0d4c5c', 'border': '#0d4c5c',
        'plot_bg': '#002b36', 'grid': '#0d4c5c', 'axes': '#93a1a1',
        'mpl_style': 'dark_background',
    },
    'nord': {
        'name': 'Nord', 'is_dark': True,
        'bg': '#2e3440', 'fg': '#d8dee9', 'field': '#3b4252',
        'select': '#88c0d0', 'button': '#3b4252',
        'button_active': '#434c5e', 'border': '#4c566a',
        'plot_bg': '#2e3440', 'grid': '#4c566a', 'axes': '#d8dee9',
        'mpl_style': 'dark_background',
    },
    'dracula': {
        'name': 'Dracula', 'is_dark': True,
        'bg': '#282a36', 'fg': '#f8f8f2', 'field': '#44475a',
        'select': '#bd93f9', 'button': '#44475a',
        'button_active': '#6272a4', 'border': '#6272a4',
        'plot_bg': '#282a36', 'grid': '#44475a', 'axes': '#f8f8f2',
        'mpl_style': 'dark_background',
    },
    'gruvbox_dark': {
        'name': 'Gruvbox Dark', 'is_dark': True,
        'bg': '#282828', 'fg': '#ebdbb2', 'field': '#3c3836',
        'select': '#d79921', 'button': '#3c3836',
        'button_active': '#504945', 'border': '#504945',
        'plot_bg': '#282828', 'grid': '#504945', 'axes': '#ebdbb2',
        'mpl_style': 'dark_background',
    },
    'monokai': {
        'name': 'Monokai', 'is_dark': True,
        'bg': '#272822', 'fg': '#f8f8f2', 'field': '#3e3d32',
        'select': '#fd971f', 'button': '#3e3d32',
        'button_active': '#49483e', 'border': '#49483e',
        'plot_bg': '#272822', 'grid': '#49483e', 'axes': '#f8f8f2',
        'mpl_style': 'dark_background',
    },
    'one_dark': {
        'name': 'One Dark', 'is_dark': True,
        'bg': '#282c34', 'fg': '#abb2bf', 'field': '#21252b',
        'select': '#61afef', 'button': '#21252b',
        'button_active': '#3a3f4b', 'border': '#3a3f4b',
        'plot_bg': '#282c34', 'grid': '#3a3f4b', 'axes': '#abb2bf',
        'mpl_style': 'dark_background',
    },
    'tokyo_night': {
        'name': 'Tokyo Night', 'is_dark': True,
        'bg': '#1a1b26', 'fg': '#c0caf5', 'field': '#24283b',
        'select': '#7aa2f7', 'button': '#24283b',
        'button_active': '#3b4261', 'border': '#3b4261',
        'plot_bg': '#1a1b26', 'grid': '#3b4261', 'axes': '#c0caf5',
        'mpl_style': 'dark_background',
    },
    'catppuccin_mocha': {
        'name': 'Catppuccin Mocha', 'is_dark': True,
        'bg': '#1e1e2e', 'fg': '#cdd6f4', 'field': '#313244',
        'select': '#cba6f7', 'button': '#313244',
        'button_active': '#45475a', 'border': '#45475a',
        'plot_bg': '#1e1e2e', 'grid': '#45475a', 'axes': '#cdd6f4',
        'mpl_style': 'dark_background',
    },
    'catppuccin_latte': {
        'name': 'Catppuccin Latte', 'is_dark': False,
        'bg': '#eff1f5', 'fg': '#4c4f69', 'field': '#e6e9ef',
        'select': '#8839ef', 'button': '#e6e9ef',
        'button_active': '#dce0e8', 'border': '#ccd0da',
        'plot_bg': '#eff1f5', 'grid': '#ccd0da', 'axes': '#4c4f69',
        'mpl_style': 'default',
    },
    'github_light': {
        'name': 'GitHub Light', 'is_dark': False,
        'bg': '#ffffff', 'fg': '#24292f', 'field': '#f6f8fa',
        'select': '#0969da', 'button': '#f6f8fa',
        'button_active': '#eaeef2', 'border': '#d0d7de',
        'plot_bg': '#ffffff', 'grid': '#d0d7de', 'axes': '#24292f',
        'mpl_style': 'default',
    },
    'github_dark': {
        'name': 'GitHub Dark', 'is_dark': True,
        'bg': '#0d1117', 'fg': '#c9d1d9', 'field': '#161b22',
        'select': '#58a6ff', 'button': '#161b22',
        'button_active': '#21262d', 'border': '#30363d',
        'plot_bg': '#0d1117', 'grid': '#21262d', 'axes': '#c9d1d9',
        'mpl_style': 'dark_background',
    },
}


# Ключи цветов для редактора темы (пара: внутренний ключ + ключ перевода)
THEME_KEYS = [
    ('bg',            'theme.editor.c_bg'),
    ('fg',            'theme.editor.c_fg'),
    ('field',         'theme.editor.c_field'),
    ('select',        'theme.editor.c_select'),
    ('button',        'theme.editor.c_button'),
    ('button_active', 'theme.editor.c_button_active'),
    ('border',        'theme.editor.c_border'),
    ('plot_bg',       'theme.editor.c_plot_bg'),
    ('grid',          'theme.editor.c_grid'),
    ('axes',          'theme.editor.c_axes'),
]


# Помечаем встроенные темы как не-пользовательские
for _k, _v in THEMES.items():
    _v['custom'] = False
del _k, _v


# ============================================================================
# ПОЛЬЗОВАТЕЛЬСКИЕ ТЕМЫ
# ============================================================================
def custom_themes_dir():
    """Папка с пользовательскими темами (создаётся при необходимости)."""
    d = os.path.expanduser("~/.grapheditor_themes")
    os.makedirs(d, exist_ok=True)
    return d


def load_custom_themes():
    """Загружает все темы из ~/.grapheditor_themes/*.json."""
    result = {}
    try:
        files = sorted(f for f in os.listdir(custom_themes_dir())
                       if f.endswith('.json'))
    except Exception:
        return result
    for fname in files:
        path = os.path.join(custom_themes_dir(), fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            key = os.path.splitext(fname)[0]
            data['custom'] = True
            data.setdefault('is_dark', False)
            data.setdefault('mpl_style',
                            'dark_background' if data['is_dark'] else 'default')
            # Проверяем обязательные ключи
            for k, _ in THEME_KEYS:
                if k not in data:
                    data[k] = '#000000'
            result[key] = data
        except Exception as e:
            print(f"[themes] не удалось загрузить {fname}: {e}")
    return result


def save_custom_theme(key, data):
    """Сохраняет тему в ~/.grapheditor_themes/<key>.json."""
    path = os.path.join(custom_themes_dir(), f"{key}.json")
    payload = dict(data)
    payload.pop('custom', None)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def delete_custom_theme(key):
    """Удаляет файл пользовательской темы."""
    path = os.path.join(custom_themes_dir(), f"{key}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def is_custom_theme(key):
    """Проверяет, пользовательская ли тема."""
    return THEMES.get(key, {}).get('custom', False)


def theme_key_from_name(name):
    """Преобразует человекочитаемое имя в безопасный ключ."""
    key = re.sub(r'\W+', '_', name, flags=re.UNICODE).strip('_').lower()
    return key


# Загружаем пользовательские темы и вливаем в общий словарь
THEMES.update(load_custom_themes())


# ============================================================================
# MIXIN
# ============================================================================
class ThemesMixin:

    def _apply_theme(self, name):
        """Применяет тему по имени."""
        if name not in THEMES:
            return
        theme = THEMES[name]
        self.current_theme = name
        self.settings['theme'] = name
        self.dark_mode_var.set(theme.get('is_dark', False))

        # База matplotlib
        try:
            plt.style.use(theme.get('mpl_style', 'default'))
        except Exception:
            pass

        self._apply_font_settings()
        self._apply_mpl_colors(theme)
        self._apply_tk_theme(theme)

        try:
            self.fig.set_facecolor(theme.get('plot_bg', '#ffffff'))
            for ax in self.axes:
                try:
                    ax.set_facecolor(theme.get('plot_bg', '#ffffff'))
                except Exception:
                    pass
            for ax in self.axes_secondary.values():
                try:
                    ax.set_facecolor(theme.get('plot_bg', '#ffffff'))
                except Exception:
                    pass
        except Exception:
            pass

        self._redraw()

    def _apply_mpl_colors(self, theme):
        mpl.rcParams.update({
            'axes.edgecolor': theme.get('axes', '#000000'),
            'axes.labelcolor': theme.get('axes', '#000000'),
            'xtick.color': theme.get('axes', '#000000'),
            'ytick.color': theme.get('axes', '#000000'),
            'text.color': theme.get('axes', '#000000'),
            'grid.color': theme.get('grid', '#cccccc'),
            'figure.facecolor': theme.get('plot_bg', '#ffffff'),
            'axes.facecolor': theme.get('plot_bg', '#ffffff'),
            'savefig.facecolor': theme.get('plot_bg', '#ffffff'),
        })

    def _apply_tk_theme(self, theme):
        style = ttk.Style()
        style.theme_use('clam')

        bg = theme.get('bg', '#f0f0f0')
        fg = theme.get('fg', '#000000')
        fld = theme.get('field', '#ffffff')
        sel = theme.get('select', '#4b6eaf')
        btn_bg = theme.get('button', '#e0e0e0')
        btn_act = theme.get('button_active', '#d0d0d0')
        border = theme.get('border', '#c0c0c0')

        style.configure(".", background=bg, foreground=fg,
                        fieldbackground=fld, borderwidth=0)

        for name in ("TFrame", "TLabel", "TLabelframe",
                     "TLabelframe.Label", "TCheckbutton", "TNotebook"):
            style.configure(name, background=bg, foreground=fg)

        style.configure("TButton", background=btn_bg, foreground=fg, padding=5)
        style.map("TButton", background=[('active', btn_act)],
                  foreground=[('active', fg)])

        style.configure("TEntry", fieldbackground=fld, foreground=fg,
                        bordercolor=border)
        style.configure("TCombobox", fieldbackground=fld, foreground=fg,
                        bordercolor=border)
        style.map("TCombobox",
                  fieldbackground=[('readonly', fld)],
                  foreground=[('readonly', fg)])

        try:
            style.configure("TSpinbox", fieldbackground=fld,
                            foreground=fg, bordercolor=border)
        except Exception:
            pass

        style.map("TCheckbutton", background=[('active', bg)])

        style.configure("TNotebook.Tab", background=btn_bg, foreground=fg,
                        padding=[10, 2])
        style.map("TNotebook.Tab", background=[('selected', bg)],
                  foreground=[('selected', fg)])

        style.configure("Treeview", background=fld, foreground=fg,
                        fieldbackground=fld)
        style.configure("Treeview.Heading", background=btn_bg, foreground=fg)
        style.map("Treeview", background=[('selected', sel)])

        try:
            style.configure("TProgressbar", background=sel, troughcolor=fld)
        except Exception:
            pass

        style.configure("TSeparator", background=border)

        try:
            style.configure("TScrollbar", background=btn_bg,
                            troughcolor=bg, bordercolor=border, arrowcolor=fg)
        except Exception:
            pass

        self.root.config(bg=bg)

    def _toggle_dark_mode(self):
        if self.dark_mode_var.get():
            self._apply_theme('dark')
        else:
            self._apply_theme('light')

    def _set_theme(self, name):
        self._apply_theme(name)

    def _list_themes(self):
        """Сначала встроенные, потом пользовательские."""
        built_in = [(k, v.get('name', k)) for k, v in THEMES.items()
                    if not v.get('custom', False)]
        custom = [(k, v.get('name', k)) for k, v in THEMES.items()
                  if v.get('custom', False)]
        return built_in + custom