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
CHART_EXAMPLES = {
    # ===== 2D БАЗОВЫЕ =====
    "Линия": {
        "category": "2D Базовые",
        "desc": "Классический график линии. Поддерживает заливку под кривой, "
                "error bars, вторую ось Y, сглаживание.",
        "fields": "X, Y, Yerr (опционально)",
        "example_x": "0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0",
        "example_y": "0, 0.48, 0.84, 1.0, 0.91, 0.60, 0.14",
        "hint": "Включите «Заливка под графиком» — получите area chart. "
                "«Свечение для точек» — эффект неона.",
    },
    "Точечная": {
        "category": "2D Базовые",
        "desc": "Диаграмма рассеяния. Каждая пара (X, Y) — отдельная точка.",
        "fields": "X, Y, Yerr (опционально)",
        "example_x": "1, 2, 3, 4, 5, 6, 7, 8",
        "example_y": "2.5, 3.1, 4.8, 5.2, 6.9, 8.1, 8.6, 9.4",
        "hint": "Включите «Свечение для точек» для эффекта на презентациях.",
    },
    "Столбчатая": {
        "category": "2D Базовые",
        "desc": "Вертикальные столбцы. X — позиции, Y — высоты.",
        "fields": "X, Y, Yerr (опционально)",
        "example_x": "1, 2, 3, 4, 5",
        "example_y": "10, 25, 18, 32, 15",
        "hint": "Для горизонтальной — тип «Горизонтальная столбчатая».",
    },
    "Гистограмма": {
        "category": "2D Базовые",
        "desc": "Распределение одной выборки. Автоматически считает частоты по бинам.",
        "fields": "X (выборка), Кол-во бинов",
        "example_x": "1.2, 2.5, 1.8, 2.1, 2.9, 1.5, 2.3, 2.7, 1.9, 2.0, "
                     "2.4, 2.6, 1.7, 2.2, 1.6, 2.8, 1.4, 2.05, 2.35, 2.15",
        "example_y": "",
        "hint": "Для нормального распределения — 20-30 бинов.",
    },
    "Круговая": {
        "category": "2D Базовые",
        "desc": "Секторная диаграмма. Y — значения, «Подписи» — названия секторов.",
        "fields": "Y, Подписи, Цвета",
        "example_x": "",
        "example_y": "30, 25, 20, 15, 10",
        "hint": "Подписи: A, B, C, D, E. Цвета: red, blue, green, orange, purple.",
    },
    "Кольцевая": {
        "category": "2D Базовые",
        "desc": "Пирог с вырезанной серединой.",
        "fields": "Y, Подписи, Цвета",
        "example_x": "",
        "example_y": "45, 30, 15, 10",
        "hint": "Подписи: Desktop, Mobile, Tablet, Other.",
    },
    "Step plot": {
        "category": "2D Базовые",
        "desc": "Ступенчатая линия. Y меняется рывком в каждой точке X.",
        "fields": "X, Y",
        "example_x": "1, 2, 3, 4, 5",
        "example_y": "3, 5, 3, 6, 4",
        "hint": "Стандарт в телекоме и системах массового обслуживания.",
    },
    "Полигон": {
        "category": "2D Базовые",
        "desc": "Замкнутая фигура по точкам.",
        "fields": "X, Y",
        "example_x": "0, 1, 2, 1.5, 0.5",
        "example_y": "0, 0.5, 2, 3, 2",
        "hint": "Последняя точка соединяется с первой.",
    },

    # ===== 2D СТАТИСТИКА =====
    "Box plot": {
        "category": "2D Статистика",
        "desc": "Ящик с усами. Y — группы через ;, X — подписи групп.",
        "fields": "Y (группы), X (подписи)",
        "example_x": "A, B, C",
        "example_y": "1,2,3,4,5,6,7 ; 3,4,5,6,7,8,9 ; 2,3,4,5,6",
        "hint": "Каждая группа — числа через запятую, группы отделены ;",
    },
    "Violin": {
        "category": "2D Статистика",
        "desc": "Скрипичная диаграмма. Показывает плотность распределения (KDE).",
        "fields": "Y (группы), X (подписи)",
        "example_x": "A, B, C",
        "example_y": "2,3,4,5,6,7 ; 5,6,7,8,9,10 ; 1,2,3,4,5",
        "hint": "Требует scipy. Гладкая форма = оценка плотности.",
    },
    "ECDF": {
        "category": "2D Статистика",
        "desc": "Эмпирическая функция распределения. Показывает долю значений ≤ x.",
        "fields": "Y (выборка)",
        "example_x": "",
        "example_y": "1.2, 2.5, 1.8, 2.1, 2.9, 1.5, 2.3, 2.7, 1.9, 2.0, "
                     "2.4, 2.6, 1.7, 2.2, 1.6, 2.8, 1.4, 2.05, 2.35, 2.15",
        "hint": "Альтернатива гистограмме для точных квантильных оценок.",
    },
    "Q-Q plot": {
        "category": "2D Статистика",
        "desc": "Квант-квант. Проверка нормальности распределения.",
        "fields": "Y (выборка)",
        "example_x": "",
        "example_y": "0.5, -1.2, 0.8, 1.5, -0.3, 2.1, -1.8, 0.2, 1.1, -0.7",
        "hint": "Если точки лежат на красной линии — данные нормальны.",
    },
    "Hexbin": {
        "category": "2D Статистика",
        "desc": "Гексагональная тепловая карта для больших наборов точек.",
        "fields": "X, Y, Кол-во бинов",
        "example_x": "1,2,3,4,5,3,2,4,5,3,2,4,5,1,2,3,4,5,3,2,4,5,1,2,3,4,5",
        "example_y": "2,3,4,5,6,4,3,5,6,4,3,5,6,2,3,4,5,6,4,3,5,6,2,3,4,5,6",
        "hint": "Для 1000+ точек. Гексагон — количество точек в нём.",
    },
    "Strip plot": {
        "category": "2D Статистика",
        "desc": "Точки с джиттером по группам.",
        "fields": "Y (группы), X (подписи)",
        "example_x": "A, B, C",
        "example_y": "1,2,3,4,5 ; 5,6,7,8,9 ; 2,3,4,5,6",
        "hint": "Каждая точка — отдельное наблюдение.",
    },
    "Ridge plot": {
        "category": "2D Статистика",
        "desc": "Гребёнка (joyplot). Наложенные KDE-кривые.",
        "fields": "Y (группы), X (подписи)",
        "example_x": "Первая, Вторая, Третья",
        "example_y": "1,2,3,4,5,6 ; 5,6,7,8,9,10 ; 2,3,4,5,6",
        "hint": "Требует scipy. Красиво для сравнения распределений.",
    },

    # ===== 3D =====
    "3D Линия": {
        "category": "3D",
        "desc": "Пространственная кривая (x(t), y(t), z(t)).",
        "fields": "X, Y, Z",
        "example_x": "0, 0.5, 1, 1.5, 2, 2.5, 3",
        "example_y": "0, 0.48, 0.84, 1, 0.91, 0.6, 0.14",
        "example_z": "0, 1, 2, 3, 4, 5, 6",
        "hint": "Спираль: X=sin(t), Y=cos(t), Z=t. Или через «Генератор».",
    },
    "3D Точечная": {
        "category": "3D",
        "desc": "Облако точек в пространстве.",
        "fields": "X, Y, Z",
        "example_x": "1, 2, 3, 4, 5, 6, 7, 8",
        "example_y": "2, 3, 4, 3, 5, 4, 6, 5",
        "example_z": "1, 2, 3, 4, 5, 6, 7, 8",
        "hint": "Включите «Свечение» для wow-эффекта.",
    },
    "3D Поверхность": {
        "category": "3D",
        "desc": "Поверхность z = f(x, y). X, Y — сетки, Z — матрица.",
        "fields": "X (сетка), Y (сетка), Z (матрица через ;)",
        "example_x": "-2, -1, 0, 1, 2",
        "example_y": "-2, -1, 0, 1, 2",
        "example_z": "0.5, 0.8, 1.0, 0.8, 0.5 ; "
                     "0.8, 0.9, 1.2, 0.9, 0.8 ; "
                     "1.0, 1.2, 1.5, 1.2, 1.0 ; "
                     "0.8, 0.9, 1.2, 0.9, 0.8 ; "
                     "0.5, 0.8, 1.0, 0.8, 0.5",
        "hint": "Или «Генератор → Поверхность 3D» с формулой "
                "z = sin(sqrt(x²+y²)).",
    },
    "3D Столбчатая": {
        "category": "3D",
        "desc": "3D-столбцы. X, Y — позиции, Z — высоты.",
        "fields": "X, Y, Z",
        "example_x": "0, 1, 2, 3, 4",
        "example_y": "0, 1, 2, 3, 4",
        "example_z": "5, 8, 3, 6, 4",
        "hint": "Классика для трёхмерных гистограмм.",
    },

    # ===== 2D СЕТЕВЫЕ =====
    "Chord": {
        "category": "2D Сетевые",
        "desc": "Хордовая диаграмма. Матрица смежности, каждая дуга — связь.",
        "fields": "Z (квадратная матрица), Подписи",
        "example_x": "",
        "example_y": "",
        "example_z": "0,5,3,1 ; 5,0,2,4 ; 3,2,0,6 ; 1,4,6,0",
        "hint": "Матрица N×N. Диагональ — нули. Подписи: A, B, C, D.",
    },
    "Sankey": {
        "category": "2D Сетевые",
        "desc": "Диаграмма Санкей. Первое значение — вход, остальные — выходы.",
        "fields": "Y (потоки), Подписи",
        "example_x": "",
        "example_y": "100, 60, 30, 10",
        "example_z": "",
        "hint": "Подписи: Вход, Канал A, Канал B, Канал C.",
    },
    "Сетевой график": {
        "category": "2D Сетевые",
        "desc": "Граф. Рёбра задаются как «A-B; B-C; ...».",
        "fields": "Z (рёбра)",
        "example_x": "",
        "example_y": "",
        "example_z": "A-B; B-C; C-D; D-A; A-C; B-D; D-E; E-A",
        "hint": "Требует networkx. Пружинный layout применяется автоматически.",
    },
    "Дендрограмма": {
        "category": "2D Сетевые",
        "desc": "Иерархическая кластеризация. Z — матрица, подписи — метки.",
        "fields": "Z (матрица), Подписи",
        "example_x": "",
        "example_y": "",
        "example_z": "1,2,3 ; 4,5,6 ; 1,3,2 ; 7,8,9 ; 4,6,5",
        "hint": "Все строки одной длины. Подписи: A, B, C, D, E.",
    },
    "Circle packing": {
        "category": "2D Сетевые",
        "desc": "Упаковка кругов. Y — размеры, X — названия.",
        "fields": "X (подписи), Y (размеры)",
        "example_x": "Python, JS, Rust, Go",
        "example_y": "30, 20, 25, 15",
        "hint": "Круги не пересекаются, размеры пропорциональны Y.",
    },

    # ===== РАДИО =====
    "Bode plot": {
        "category": "2D Радиотехника",
        "desc": "АЧХ и ФЧХ. X — частота (лог), Y — амплитуда, Z — фаза.",
        "fields": "X (freq), Y (dB), Z (phase)",
        "example_x": "1, 10, 100, 1000, 10000, 100000",
        "example_y": "0, -3, -20, -40, -60, -80",
        "example_z": "0, -45, -90, -135, -170, -180",
        "hint": "Ось X автоматически логарифмическая.",
    },
    "Smith chart": {
        "category": "2D Радиотехника",
        "desc": "Круговая диаграмма полных сопротивлений.",
        "fields": "X (Re), Y (Im) или Z-матрица",
        "example_x": "0.5, 1.0, 2.0, 1.0, 0.3",
        "example_y": "0.5, 0.0, -0.5, 1.0, -0.2",
        "example_z": "",
        "hint": "Или Z-матрица: две строки (Re; Im) через ;",
    },
    "Nyquist plot": {
        "category": "2D Радиотехника",
        "desc": "Годограф Найквиста. X — ω, Y — Re, Z — Im.",
        "fields": "X (ω), Y (Re), Z (Im)",
        "example_x": "0.1, 0.5, 1, 2, 5, 10",
        "example_y": "-1, -2, -3, -2, -1, -0.5",
        "example_z": "1, 2, 3, 2, 1, 0.5",
        "hint": "Проверка устойчивости: линия не должна охватывать (-1, 0).",
    },

    # ===== ФИНАНСЫ =====
    "Свечи (OHLC)": {
        "category": "2D Финансы",
        "desc": "Свечной график. Y — 4 серии через ; : Open;High;Low;Close.",
        "fields": "X, Y (4 серии через ;)",
        "example_x": "1, 2, 3, 4, 5",
        "example_y": "100,102,101,103,105 ; 105,107,106,108,110 ; "
                     "98,100,99,101,103 ; 102,105,104,106,109",
        "example_z": "",
        "hint": "Зелёные — рост (Close>Open), красные — падение.",
    },
    "Водопад": {
        "category": "2D Финансы",
        "desc": "Водопадная диаграмма. Y — изменения, X — подписи.",
        "fields": "X (подписи), Y (дельты), Подписи",
        "example_x": "Старт, Продажи, Возвраты, Расходы, Итог",
        "example_y": "100, 30, -15, -25, 90",
        "example_z": "",
        "hint": "Положительные — зелёные, отрицательные — красные.",
    },
    "Диаграмма Парето": {
        "category": "2D Финансы",
        "desc": "Столбцы + накопленный %. Автоматически сортирует по убыванию.",
        "fields": "X (метки), Y (значения)",
        "example_x": "A, B, C, D, E",
        "example_y": "45, 30, 12, 8, 5",
        "example_z": "",
        "hint": "Показывает 80/20 правило.",
    },
    "Гант": {
        "category": "2D Проекты",
        "desc": "Диаграмма Ганта. X — начало задачи, Y — длительность.",
        "fields": "X (начало), Y (длительность), Подписи, Цвета",
        "example_x": "0, 1, 3, 5, 7, 9",
        "example_y": "2, 3, 2, 4, 1, 3",
        "example_z": "",
        "hint": "Подписи: Разработка, Тесты, Документация, Деплой, ...",
    },
    "Воронка": {
        "category": "2D Проекты",
        "desc": "Funnel chart. Этапы конверсии, сужающиеся вниз.",
        "fields": "X (этапы), Y (значения), Цвета",
        "example_x": "Visit, Signup, Buy, Return",
        "example_y": "100, 60, 30, 10",
        "example_z": "",
        "hint": "Идеально для маркетинга и продуктовой аналитики.",
    },

    # ===== ML / НАУКА =====
    "ROC curve": {
        "category": "2D ML",
        "desc": "ROC-кривая. Y — истинные метки (0/1), Z — вероятности модели.",
        "fields": "Y (labels 0/1), Z (scores 0..1)",
        "example_x": "",
        "example_y": "1,1,1,1,0,0,0,0",
        "example_z": "0.9, 0.8, 0.7, 0.6, 0.4, 0.3, 0.2, 0.1",
        "hint": "AUC рассчитывается автоматически.",
    },
    "Volcano plot": {
        "category": "2D ML",
        "desc": "Вулкан. X — log2(FoldChange), Y — -log10(p-value).",
        "fields": "X, Y",
        "example_x": "-2,-1.5,-0.8,0,0.5,1.2,2,2.5,-2.8,0.3",
        "example_y": "1,2,3,0.5,1.5,4,5,3.5,4.2,0.8",
        "example_z": "",
        "hint": "Красные — значимо вверх, синие — значимо вниз.",
    },
    "Manhattan plot": {
        "category": "2D ML",
        "desc": "Манхэттен. X — позиция SNP, Y — -log10(p), Z — хромосома.",
        "fields": "X, Y, Z (хромосомы)",
        "example_x": "1,2,3,4,5,6,7,8,9,10,11,12",
        "example_y": "1,2,1.5,3,2,4,1,2,3,5,1,2",
        "example_z": "1,1,1,1,2,2,2,2,3,3,3,3",
        "hint": "Каждая хромосома — свой цвет.",
    },

    # ===== ГЕОМЕТРИЯ =====
    "Диаграмма Вороного": {
        "category": "2D Геометрия",
        "desc": "Плоскость разбита на области для каждой точки.",
        "fields": "X, Y",
        "example_x": "1, 5, 3, 8, 6, 2, 7",
        "example_y": "2, 4, 6, 3, 8, 7, 1",
        "hint": "Требует scipy.spatial.Voronoi.",
    },
    "Выпуклая оболочка": {
        "category": "2D Геометрия",
        "desc": "Минимальный выпуклый многоугольник вокруг точек.",
        "fields": "X, Y",
        "example_x": "1, 2, 3, 4, 5, 3, 2",
        "example_y": "1, 3, 2, 4, 1, 5, 2",
        "hint": "Требует scipy.spatial.ConvexHull.",
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
