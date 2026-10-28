import tkinter as tk

APP_NAME = "GraphEditor Pro"
APP_VERSION = "1.5.0"
GRAPHX_MANIFEST = "manifest.json"
i = "sin(t*x) + cos(t*y)"

FONTS = [
    "DejaVu Sans", "Arial", "Times New Roman",
    "Courier New", "Verdana", "Tahoma", "Georgia",
]

UNIT_TO_M = {
    'm': 1.0, 'cm': 0.01, 'mm': 0.001, 'km': 1000.0,
    'µm': 1e-6, 'nm': 1e-9,
    'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144,
    'mi': 1609.344, 'nmi': 1852.0,
}

TOOLTIPS = {
    'toolbar.open_json': "Открыть проект (Ctrl+O)",
    'toolbar.save_json': "Сохранить (Ctrl+S)",
    'toolbar.zip': "Сохранить в .zip",
    'toolbar.import_csv': "Импорт данных из CSV",
    'toolbar.export_csv': "Экспорт всех данных в CSV",
    'toolbar.export_html': "Интерактивный HTML (plotly)",
    'toolbar.save_image': "Сохранить как PNG / SVG / PDF",
    'toolbar.undo': "Отменить (Ctrl+Z)",
    'toolbar.redo': "Повторить (Ctrl+Y)",
    'create.create_btn': "Создать новый график",
    'create.apply_btn': "Применить изменения к выбранному",
    'create.palette': "Выбрать цвет из палитры",
    'gen.generate_btn': "Заполнить X и Y по формуле",
    'obj.add_trend': "Добавить линию тренда",
    'right.anim_start': "Запустить анимацию",
    'right.anim_pause': "Пауза / продолжить",
    'right.anim_stop': "Остановить анимацию",
    'right.anim_save': "Сохранить анимацию в GIF или MP4",
}

class ToolTip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._tip = None
        self._after_id = None
        widget.bind('<Enter>', self._schedule, add='+')
        widget.bind('<Leave>', self._hide, add='+')
        widget.bind('<ButtonPress>', self._hide, add='+')

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        self._tip.attributes('-topmost', True)
        tk.Label(self._tip, text=self.text, justify=tk.LEFT,
                 background="#ffffcc", relief=tk.SOLID, borderwidth=1,
                 font=('Arial', 9), padx=6, pady=3).pack()

    def _hide(self, event=None):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


def attach_tooltip(widget, text, delay=500):
    return ToolTip(widget, text, delay)
