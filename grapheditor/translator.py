"""Локализация GraphEditor Pro.

Словари переводов лежат в пакете translations/ (по одному файлу на язык).
Здесь — только механизм: класс Translator, реестр типов, алиасы.
"""
from translations import TRANSLATIONS


_LANG_ALIASES = {'ko': 'kr'} # старый ключ 'ko' → 'kr'


# ============================================================================
# ПОДДЕРЖИВАЕМЫЕ ЯЗЫКИ
# ============================================================================
SUPPORTED_LANGS = [
    ('ru', 'Русский'), ('en', 'English'),
    ('de', 'Deutsch'), ('fr', 'Français'),
    ('es', 'Español'), ('pt', 'Português'),
    ('it', 'Italiano'), ('vi', 'Tiếng Việt'),
    ('th', 'ไทย'), ('zh', '简体中文'),
    ('ja', '日本語'), ('kr', '한국어'),
    ('ar', 'العربية'), ('hi', 'हिन्दी'),
    ('ua', 'Українська'), ('by', 'Беларуская'),
    ('sl', 'Slovenščina'), ('pl', 'Polski'),
    ('kz', 'Қазақша'), ('uz', 'Oʻzbekcha'),
]


# ============================================================================
# ВНУТРЕННИЕ ID ТИПОВ ГРАФИКОВ
# ============================================================================
INTERNAL_TYPES = [
    # 2D базовые
    "Линия", "Столбчатая", "Гистограмма", "Точечная", "Круговая",
    # 2D продвинутые
    "Box plot", "Violin", "Heatmap", "Contour", "Imshow",
    "Treemap", "Sunburst",
    # специальные 2D
    "Полигон", "Quiver", "Кольцевая", "Вложенная круговая",
    "Мозаика", "Радиальная", "Столбчатая с накоплением",
    "Полярный scatter", "Пузырьковая",
    # финансовые и проектные
    "Водопад", "Гант",
    "Свечи (OHLC)", "Step plot", "Диаграмма Парето",
    "Renko", "Point-and-Figure",
    # статистические
    "Q-Q plot", "ECDF", "Hexbin", "Strip plot",
    "Ridge plot", "Raincloud plot", "Beanplot", "Swarm plot",
    "Cherry blossom plot", "Dot-and-whisker",
    "Сезонная декомпозиция", "Rolling statistics",
    # сетевые и иерархические
    "Дендрограмма", "Cluster dendrogram",
    "Sankey", "Alluvial diagram", "Chord",
    "Сетевой график", "Hive plot", "Arc diagram",
    "Дерево (tree diagram)", "Radial tree 3D",
    "Circle packing", "Adjacency matrix", "Mapper algorithm",
    # векторные поля
    "Stream plot", "Streamlines", "3D Quiver",
    # радиотехника
    "Bode plot", "Smith chart", "Nyquist plot",
    "Root locus", "Constellation diagram",
    # 3D базовые
    "3D Линия", "3D Точечная", "3D Столбчатая",
    "3D Гистограмма", "3D Круговая",
    "3D Поверхность", "3D Сетка",
    "3D Полигон", "3D Триангуляция",
    # 3D-расширенные
    "Ribbon plot 3D", "Waterfall spectrogram 3D",
    "Riemann surface 3D", "Joyplot 3D", "Isosurface 3D",
    # гео / метео / научные
    "Choropleth", "Flow map", "Isopleth", "Cartogram",
    "Dot density map", "Hodograph", "Роза ветров",
    "Skew-T log-P", "Thermodynamic diagram",
    "Диаграмма Вороного", "Выпуклая оболочка", "Alpha shape",
    # ML
    "Volcano plot", "ROC curve", "Manhattan plot",
    "MA plot", "Recurrence plot", "Cobweb plot",
    "Poincaré plot", "Phase portrait",
    # сравнение / ранги
    "Dot plot", "Lollipop", "Пирамида", "Sparkline",
    "Cycle plot", "Bump chart", "Slopegraph",
    "Dumbbell plot", "Bar of pie", "Ribbon plot 2D",
    "Bullet chart", "Funnel chart",
    "Календарная теплокарта", "Полярная теплокарта",
    "Диаграмма бифуркаций", "Parallel coordinates",
    "Radar chart", "Спидометр",
    # новые (v1.4.0)
    "Вафельная диаграмма", "Сосулька (icicle)",
    "Диаграмма Аргана", "Диаграмма Тейлора",
    "Горизонтальная столбчатая", "Горизонтальная линия",
    "Pie of pie", "Топографический профиль",
    "Вейвлет-скейлограмма",
]


# ============================================================================
# СООТВЕТСТВИЕ: внутренний ID → ключ перевода
# ============================================================================
TYPE_TO_KEY = {
    "Линия": "type.line",
    "Столбчатая": "type.bar",
    "Гистограмма": "type.hist",
    "Точечная": "type.scatter",
    "Круговая": "type.pie",
    "Box plot": "type.box",
    "Violin": "type.violin",
    "Heatmap": "type.heatmap",
    "Contour": "type.contour",
    "Imshow": "type.imshow",
    "Treemap": "type.treemap",
    "Sunburst": "type.sunburst",
    "Полигон": "type.polygon",
    "Quiver": "type.quiver",
    "Кольцевая": "type.donut",
    "Вложенная круговая": "type.nested_pie",
    "Мозаика": "type.mosaic",
    "Радиальная": "type.radial",
    "Столбчатая с накоплением": "type.stacked_bar",
    "Полярный scatter": "type.polar_scatter",
    "Пузырьковая": "type.bubble",
    "Водопад": "type.waterfall",
    "Гант": "type.gantt",
    "Свечи (OHLC)": "type.candlestick",
    "Step plot": "type.step",
    "Диаграмма Парето": "type.pareto",
    "Renko": "type.renko",
    "Point-and-Figure": "type.pnf",
    "Q-Q plot": "type.qq",
    "ECDF": "type.ecdf",
    "Hexbin": "type.hexbin",
    "Strip plot": "type.strip",
    "Ridge plot": "type.ridge",
    "Raincloud plot": "type.raincloud",
    "Beanplot": "type.beanplot",
    "Swarm plot": "type.swarm",
    "Cherry blossom plot": "type.cherry",
    "Dot-and-whisker": "type.dotwhisker",
    "Сезонная декомпозиция": "type.seasonal",
    "Rolling statistics": "type.rolling",
    "Дендрограмма": "type.dendrogram",
    "Cluster dendrogram": "type.clusterdendro",
    "Sankey": "type.sankey",
    "Alluvial diagram": "type.alluvial",
    "Chord": "type.chord",
    "Сетевой график": "type.network",
    "Hive plot": "type.hive",
    "Arc diagram": "type.arc",
    "Дерево (tree diagram)": "type.tree",
    "Radial tree 3D": "type.radialtree3d",
    "Circle packing": "type.circlepack",
    "Adjacency matrix": "type.adjmatrix",
    "Mapper algorithm": "type.mapper",
    "Stream plot": "type.stream",
    "Streamlines": "type.streamlines",
    "3D Quiver": "type.quiver3d",
    "Bode plot": "type.bode",
    "Smith chart": "type.smith",
    "Nyquist plot": "type.nyquist",
    "Root locus": "type.rootlocus",
    "Constellation diagram": "type.constellation",
    "3D Линия": "type.line3d",
    "3D Точечная": "type.scatter3d",
    "3D Столбчатая": "type.bar3d",
    "3D Гистограмма": "type.hist3d",
    "3D Круговая": "type.pie3d",
    "3D Поверхность": "type.surface3d",
    "3D Сетка": "type.mesh3d",
    "3D Полигон": "type.polygon3d",
    "3D Триангуляция": "type.trisurf3d",
    "Ribbon plot 3D": "type.ribbon3d",
    "Waterfall spectrogram 3D": "type.waterfall_spectrogram3d",
    "Riemann surface 3D": "type.riemann3d",
    "Joyplot 3D": "type.joyplot3d",
    "Isosurface 3D": "type.isosurface3d",
    "Choropleth": "type.choropleth",
    "Flow map": "type.flowmap",
    "Isopleth": "type.isopleth",
    "Cartogram": "type.cartogram",
    "Dot density map": "type.dotdensity",
    "Hodograph": "type.hodograph",
    "Роза ветров": "type.windrose",
    "Skew-T log-P": "type.skewt",
    "Thermodynamic diagram": "type.thermo",
    "Диаграмма Вороного": "type.voronoi",
    "Выпуклая оболочка": "type.convexhull",
    "Alpha shape": "type.alphashape",
    "Volcano plot": "type.volcano",
    "ROC curve": "type.roc",
    "Manhattan plot": "type.manhattan",
    "MA plot": "type.maplot",
    "Recurrence plot": "type.recurrence",
    "Cobweb plot": "type.cobweb",
    "Poincaré plot": "type.poincare",
    "Phase portrait": "type.phase",
    "Dot plot": "type.dotplot",
    "Lollipop": "type.lollipop",
    "Пирамида": "type.pyramid",
    "Sparkline": "type.sparkline",
    "Cycle plot": "type.cycle",
    "Bump chart": "type.bump",
    "Slopegraph": "type.slope",
    "Dumbbell plot": "type.dumbbell",
    "Bar of pie": "type.barofpie",
    "Ribbon plot 2D": "type.ribbon2d",
    "Bullet chart": "type.bullet",
    "Funnel chart": "type.funnel",
    "Календарная теплокарта": "type.calheat",
    "Полярная теплокарта": "type.polarheat",
    "Диаграмма бифуркаций": "type.bifurcation",
    "Parallel coordinates": "type.parallel",
    "Radar chart": "type.radar",
    "Спидометр": "type.gauge",
    # новые (v1.4.0)
    "Вафельная диаграмма": "type.waffle",
    "Сосулька (icicle)": "type.icicle",
    "Диаграмма Аргана": "type.argand",
    "Диаграмма Тейлора": "type.taylor",
    "Горизонтальная столбчатая": "type.hbar",
    "Горизонтальная линия": "type.hline",
    "Pie of pie": "type.pieofpie",
    "Топографический профиль": "type.topoprofile",
    "Вейвлет-скейлограмма": "type.wavelet",
}


# ============================================================================
# ВНУТРЕННИЕ ID ТИПОВ АНИМАЦИЙ
# ============================================================================
INTERNAL_ANIM_TYPES = [
    "Нет",
    "Волна (2D)", "Растущий столбец", "Спираль (3D)",
    "Пульсация точек", "Своя функция (2D)", "Своя функция (3D)",
    "Маятник (2D)", "Лоренц-аттрактор (3D)", "Двойной маятник (2D)",
    "Эпициклоид (2D)", "Бегущие частицы (3D)", "Клеточный автомат (2D)",
    "Морфинг функций (2D)", "Тепловая карта (2D)", "Вращение 3D",
]


# ============================================================================
# СООТВЕТСТВИЕ: анимация → ключ перевода
# ============================================================================
ANIM_TO_KEY = {
    "Нет": "anim.none",
    "Волна (2D)": "anim.wave2d",
    "Растущий столбец": "anim.rising_bar",
    "Спираль (3D)": "anim.spiral3d",
    "Пульсация точек": "anim.pulsing",
    "Своя функция (2D)": "anim.custom2d",
    "Своя функция (3D)": "anim.custom3d",
    "Маятник (2D)": "anim.pendulum",
    "Лоренц-аттрактор (3D)": "anim.lorenz",
    "Двойной маятник (2D)": "anim.double_pendulum",
    "Эпициклоид (2D)": "anim.epicycloid",
    "Бегущие частицы (3D)": "anim.particles3d",
    "Клеточный автомат (2D)": "anim.cellular",
    "Морфинг функций (2D)": "anim.morph",
    "Тепловая карта (2D)": "anim.heatmap",
    "Вращение 3D": "anim.rotate3d",
}


# ============================================================================
# КЛАСС TRANSLATOR
# ============================================================================
class Translator:
    def __init__(self, lang='ru'):
        self.lang = lang
        self.observers = []
        self._plugin_types = {}   # id → {lang: display}
        self._plugin_anims = {}   # id → {lang: display}

    # ----- Плагины: типы графиков -----
    def register_plugin_type(self, id_, display):
        self._plugin_types[id_] = display

    def unregister_plugin_types(self):
        self._plugin_types = {}

    # ----- Плагины: анимации -----
    def register_plugin_anim(self, id_, display):
        self._plugin_anims[id_] = display

    def unregister_plugin_anims(self):
        self._plugin_anims = {}

    # ----- Перевод -----
    def t(self, key, **kwargs):
        text = TRANSLATIONS.get(self.lang, {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError, ValueError):
                return text
        return text

    # ----- Имена типов -----
    def type_name(self, internal_id):
        key = TYPE_TO_KEY.get(internal_id)
        if key:
            return self.t(key)
        if internal_id in self._plugin_types:
            disp = self._plugin_types[internal_id]
            return (disp.get(self.lang)
                    or disp.get('en')
                    or next(iter(disp.values()), internal_id))
        return internal_id

    def anim_name(self, internal_id):
        # 1. Плагины
        if internal_id in self._plugin_anims:
            disp = self._plugin_anims[internal_id]
            return (disp.get(self.lang)
                    or disp.get('en')
                    or next(iter(disp.values()), internal_id))
        # 2. Встроенные
        key = ANIM_TO_KEY.get(internal_id)
        return self.t(key) if key else internal_id

    # ----- Обратный поиск -----
    def find_type_by_display(self, display_text):
        for pid, disp in self._plugin_types.items():
            if display_text in disp.values() or display_text == pid:
                return pid
        for internal_id in INTERNAL_TYPES:
            if self.type_name(internal_id) == display_text:
                return internal_id
        return display_text

    def find_anim_by_display(self, display_text):
        for pid, disp in self._plugin_anims.items():
            if display_text in disp.values() or display_text == pid:
                return pid
        for internal_id in INTERNAL_ANIM_TYPES:
            if self.anim_name(internal_id) == display_text:
                return internal_id
        return display_text

    # ----- Смена языка -----
    def set_lang(self, lang):
        lang = _LANG_ALIASES.get(lang, lang)
        if lang not in TRANSLATIONS:
            return
        self.lang = lang
        for cb in self.observers:
            try:
                cb()
            except Exception:
                pass

    # ----- Наблюдатели -----
    def observe(self, cb):
        self.observers.append(cb)


# ============================================================================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# ============================================================================
tr = Translator('ru')