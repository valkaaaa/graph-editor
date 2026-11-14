import tkinter as tk

APP_NAME = "GraphEditor Pro"
APP_VERSION = "1.6.0"
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
FORMULA_TEMPLATES = {
    # ------------------------------------------------------------------
    # Декартовы (y = f(x))
    # ------------------------------------------------------------------
    "sin(x) * exp(-x/5)": {
        "mode": "cartesian",
        "expr": "sin(x) * exp(-x/5)",
        "xmin": 0, "xmax": 20,
    },
    "Нормальное распределение": {
        "mode": "cartesian",
        "expr": "(1/sqrt(2*pi)) * exp(-x**2/2)",
        "xmin": -4, "xmax": 4,
    },
    "Затухающие колебания": {
        "mode": "cartesian",
        "expr": "exp(-x/3) * sin(5*x)",
        "xmin": 0, "xmax": 10,
    },
    "Биения": {
        "mode": "cartesian",
        "expr": "sin(x) * sin(10*x)",
        "xmin": 0, "xmax": 20,
    },
    "Сигмоида": {
        "mode": "cartesian",
        "expr": "1 / (1 + exp(-x))",
        "xmin": -10, "xmax": 10,
    },
    "Функция Гаусса (erf)": {
        "mode": "cartesian",
        "expr": "erf(x)",
        "xmin": -4, "xmax": 4,
    },
    "Гамма-функция": {
        "mode": "cartesian",
        "expr": "gamma(x)",
        "xmin": 0.1, "xmax": 5,
    },
    "Парабола": {
        "mode": "cartesian",
        "expr": "a*x**2 + b*x + c",
        "xmin": -10, "xmax": 10,
    },
    "Полином 4-й степени": {
        "mode": "cartesian",
        "expr": "x**4 - 4*x**2 + 1",
        "xmin": -3, "xmax": 3,
    },
    "Пила / касательная": {
        "mode": "cartesian",
        "expr": "tan(x)",
        "xmin": -1.5, "xmax": 1.5,
    },
    "Асимптота (1/x)": {
        "mode": "cartesian",
        "expr": "1/x",
        "xmin": 0.1, "xmax": 10,
    },
    "Логарифм": {
        "mode": "cartesian",
        "expr": "log(x)",
        "xmin": 0.1, "xmax": 10,
    },
    "Функция Бесселя J₀": {
        "mode": "cartesian",
        "expr": "jv(0, x)",
        "xmin": 0, "xmax": 20,
    },
    "Фрактал (x * sin(1/x))": {
        "mode": "cartesian",
        "expr": "x * sin(1/x)",
        "xmin": 0.01, "xmax": 1,
    },

    # ------------------------------------------------------------------
    # Параметрические (x(t), y(t))
    # ------------------------------------------------------------------
    "Лиссажу 3:5": {
        "mode": "parametric",
        "expr_x": "sin(3*t)",
        "expr_y": "sin(5*t)",
        "xmin": 0, "xmax": 6.28318,   # 2π
    },
    "Лиссажу 5:7": {
        "mode": "parametric",
        "expr_x": "sin(5*t)",
        "expr_y": "sin(7*t)",
        "xmin": 0, "xmax": 6.28318,
    },
    "Сердце": {
        "mode": "parametric",
        "expr_x": "16 * sin(t)**3",
        "expr_y": (
            "13*cos(t) - 5*cos(2*t) "
            "- 2*cos(3*t) - cos(4*t)"
        ),
        "xmin": 0, "xmax": 6.28318,
    },
    "Циклоида": {
        "mode": "parametric",
        "expr_x": "t - sin(t)",
        "expr_y": "1 - cos(t)",
        "xmin": 0, "xmax": 18.84956,  # 6π
    },
    "Астроида": {
        "mode": "parametric",
        "expr_x": "cos(t)**3",
        "expr_y": "sin(t)**3",
        "xmin": 0, "xmax": 6.28318,
    },
    "Спирограф": {
        "mode": "parametric",
        "expr_x": (
            "(a - b)*cos(t) + b*cos(t*(a-b)/b)"
        ),
        "expr_y": (
            "(a - b)*sin(t) - b*sin(t*(a-b)/b)"
        ),
        "xmin": 0, "xmax": 62.8318,   # 20π
    },
    "Эпициклоид": {
        "mode": "parametric",
        "expr_x": (
            "(3+1)*cos(t) - 1.5*cos((3+1)/1 * t)"
        ),
        "expr_y": (
            "(3+1)*sin(t) - 1.5*sin((3+1)/1 * t)"
        ),
        "xmin": 0, "xmax": 6.28318,
    },

    # ------------------------------------------------------------------
    # Полярные (r = f(θ))
    # ------------------------------------------------------------------
    "Роза 6 лепестков": {
        "mode": "polar",
        "expr": "1 + 0.5*cos(6*theta)",
        "xmin": 0, "xmax": 6.28318,
    },
    "Роза 4 лепестка": {
        "mode": "polar",
        "expr": "cos(2*theta)",
        "xmin": 0, "xmax": 6.28318,
    },
    "Кардиоида": {
        "mode": "polar",
        "expr": "1 + cos(theta)",
        "xmin": 0, "xmax": 6.28318,
    },
    "Лемниската": {
        "mode": "polar",
        "expr": "sqrt(abs(cos(2*theta)))",
        "xmin": 0, "xmax": 6.28318,
    },
    "Спираль Архимеда": {
        "mode": "polar",
        "expr": "theta",
        "xmin": 0, "xmax": 25.13274,  # 8π
    },
    "Логарифмическая спираль": {
        "mode": "polar",
        "expr": "exp(0.2*theta)",
        "xmin": 0, "xmax": 25.13274,
    },
    "Улитка Паскаля": {
        "mode": "polar",
        "expr": "1 - 2*sin(theta)",
        "xmin": 0, "xmax": 6.28318,
    },
    # ------------------------------------------------------------------
    # 3D Поверхности и кривые
    # ------------------------------------------------------------------
    "Поверхность (z = sin(r)/r)": {
        "mode": "surface3d",
        "expr": "sin(sqrt(x**2 + y**2)) / (sqrt(x**2 + y**2) + 0.1)",
        "xmin": -10, "xmax": 10,
    },
    "Седло (z = x² - y²)": {
        "mode": "surface3d",
        "expr": "x**2 - y**2",
        "xmin": -3, "xmax": 3,
    },
    "3D Спираль": {
        "mode": "parametric3d",
        "expr_x": "sin(3*t)",
        "expr_y": "cos(3*t)",
        "expr_z": "t",
        "xmin": 0, "xmax": 20,
    },
    "3D Узел (Trefoil)": {
        "mode": "parametric3d",
        "expr_x": "sin(t) + 2*sin(2*t)",
        "expr_y": "cos(t) - 2*cos(2*t)",
        "expr_z": "-sin(3*t)",
        "xmin": 0, "xmax": 6.28318,
    },
    # ------------------------------------------------------------------
    # 3D Поверхности
    # ------------------------------------------------------------------
    "Гиперболический параболоид (седло)": {
        "mode": "surface3d",
        "expr": "where((x**2/a**2 + y**2/b**2) < 1, x**2/a**2 - y**2/b**2, nan)",
        "xmin": -1.5,
        "xmax": 1.5,
    },
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
