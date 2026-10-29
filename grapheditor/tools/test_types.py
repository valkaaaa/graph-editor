"""Smoke-тест: прогоняет все типы графиков через _create_artist.

Проверяет, что для каждого типа из INTERNAL_TYPES:
  - вызов _create_artist не падает с исключением;
  - возвращается artist (или None — тип обрабатывается, но не рисует);
  - есть явная ветка в _create_artist.py (а не fallback-линия).

Запуск:
  python tools/test_types.py
  python tools/test_types.py --strict     # None тоже считается провалом
  python tools/test_types.py -v           # показать каждый тип
  python tools/test_types.py -v --strict  # полный вывод + строгий режим

Возврат:
  0 — все типы OK (или None, если не --strict)
  1 — есть ERROR (или None при --strict)

Не требует дисплея (matplotlib Agg), не требует Tk, работает в CI.
"""
from __future__ import annotations

import argparse
import re
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "grapheditor"))

from grapheditor.translator import INTERNAL_TYPES          # noqa: E402
from grapheditor.plots._create_artist import CreateArtistMixin  # noqa: E402


# ============================================================================
# ЗАГЛУШКИ ДЛЯ АТРИБУТОВ, КОТОРЫЕ _create_artist ЧИТАЕТ У self
# ============================================================================
class _Var:
    def __init__(self, value):
        self._v = value

    def get(self):
        return self._v


class _Entry:
    def __init__(self, text=""):
        self._text = text

    def get(self):
        return self._text


class _EmptyRegistry:
    """Пустой plugin_registry — имитирует 'плагины не загружены'."""
    chart_types = {}


class MockApp(CreateArtistMixin):
    """Минимальный объект с атрибутами, нужными _create_artist."""

    def __init__(self):
        self.smooth_var = _Var(False)
        self.dark_mode_var = _Var(False)
        self.show_grid_var = _Var(True)
        self.settings = {"smooth_window": 5}
        self.axes = []
        self.axes_secondary = {}
        self.subplot_rows = 1
        self.subplot_cols = 1
        # ВАЖНО: не None, иначе `t in self.plugin_registry.chart_types`
        # падает с AttributeError на каждом типе.
        self.plugin_registry = _EmptyRegistry()
        self.entry_x = _Entry("0.1, 2.0")
        self.entry_y = _Entry("-0.1, 2.0")
        self.live_preview_var = _Var(False)

    def _get_axis(self, idx):
        return self.axes[idx] if 0 <= idx < len(self.axes) else self.axes[0]

    def _smooth(self, y, window):
        return y


# ============================================================================
# БАЗОВЫЙ НАБОР ДАННЫХ
# ============================================================================
BASE = {
    "x": [1, 2, 3, 4, 5],
    "y": [2, 4, 3, 5, 4],
    "z": [1, 2, 3, 4, 5],
    "yerr": [0.1, 0.1, 0.1, 0.1, 0.1],
    "pie_labels": ["A", "B", "C", "D", "E"],
    "pie_colors": ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff"],
    "box_data": [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6], [3, 4, 5, 6, 7]],
    "heatmap_data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    "yerr_matrix": [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    "treemap_parents": ["", "", "A", "B", ""],
    "col_labels": ["c1", "c2", "c3"],
    "dst_labels": ["d1", "d2", "d3"],
    "bins": 10,
    "subplot_index": 0,
    "color": "blue",
    "label": "smoke test",
    "lw": 2.0, "ls": "-", "ms": 6.0, "marker": "o",
    "use_y2": False, "fill": False, "glow": False,
    "unit_x": "—", "unit_y": "—", "unit_z": "—",
    "visible": True, "artist": None,
    "_extra_artists": [], "_cleanup": None,
    "notes": "", "folder": "", "smooth": False,
}


# ============================================================================
# ПЕРЕОПРЕДЕЛЕНИЯ ПОД КОНКРЕТНЫЕ ТИПЫ
# ============================================================================
OVERRIDES = {
    # --- финансовые ---
    "Свечи (OHLC)": {
        "box_data": [
            [100, 102, 101, 103, 105],   # Open
            [105, 107, 106, 108, 110],   # High
            [98, 100, 99, 101, 103],     # Low
            [102, 105, 104, 106, 109],   # Close
        ],
    },
    "Renko":            {"bins": 0},
    "Point-and-Figure": {"bins": 0},

    # --- сетевые: z как список рёбер "A-B; B-C; ..." ---
    "Сетевой график": {"z": ["A-B", "B-C", "C-D", "D-A", "A-C"]},
    "Hive plot":      {"z": ["A-B", "B-C", "C-D", "D-A", "A-C"]},
    "Arc diagram":    {"z": ["A-B", "B-C", "C-D", "D-A", "A-C"]},
    "Дерево (tree diagram)": {"z": ["root-A", "root-B", "A-A1", "A-A2"]},
    "Radial tree 3D": {"z": ["root-A", "root-B", "A-A1", "A-A2"]},
    "Flow map": {
        "z": ["A-B", "B-C", "C-D"],
        "x": [0, 1, 2], "y": [0, 1, 0],
        "pie_labels": ["A", "B", "C"],
    },

    # --- матричные типы, где нужна квадратная матрица ---
    "Chord": {
        "heatmap_data": [
            [0, 5, 3, 1],
            [5, 0, 2, 4],
            [3, 2, 0, 6],
            [1, 4, 6, 0],
        ],
        "pie_labels": ["A", "B", "C", "D"],
    },
    "Adjacency matrix": {
        "heatmap_data": [
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0],
        ],
        "pie_labels": ["A", "B", "C", "D"],
    },
    "Дендрограмма": {
        "heatmap_data": [
            [1, 2, 3], [4, 5, 6], [1, 3, 2],
            [7, 8, 9], [4, 6, 5],
        ],
        "pie_labels": ["A", "B", "C", "D", "E"],
    },
    "Cluster dendrogram": {
        "heatmap_data": [
            [1, 2, 3], [4, 5, 6], [1, 3, 2],
            [7, 8, 9], [4, 6, 5],
        ],
    },
    "Mapper algorithm": {
        "heatmap_data": [
            [1, 2, 3], [4, 5, 6], [1, 3, 2],
            [7, 8, 9], [4, 6, 5],
        ],
    },
    "Alluvial diagram": {
        "heatmap_data": [[5, 3, 2], [2, 4, 1], [1, 2, 3]],
        "dst_labels": ["X", "Y", "Z"],
        "pie_labels": ["S1", "S2", "S3"],
    },
    "Sankey": {"y": [100, 30, 40, 30], "pie_labels": ["In", "A", "B", "C"]},

    # --- 3D со специальными данными ---
    "Riemann surface 3D": {
        "z": "sqrt(z)", "x": [0.1, 2.0], "y": [-0.1, 2.0],
    },
    "Waterfall spectrogram 3D": {
        "heatmap_data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    },
    "Isosurface 3D": {
        "heatmap_data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "bins": 5,
    },

    # --- стохастические / нелинейные ---
    "Cobweb plot":          {"x": ["r * x * (1 - x)"], "y": [0.2, 20]},
    "Диаграмма бифуркаций": {"x": [2.5, 4.0], "y": [0.5]},
    "Спидометр":            {"x": [0.0, 100.0], "y": [75.0]},

    # --- радиотехника ---
    "Root locus": {"x": [1.0], "y": [1.0, 3.0, 2.0], "bins": 100},
    "Constellation diagram": {
        "x": [1, -1, 1, -1], "y": [1, 1, -1, -1],
        "z": [1.1, -0.9, 0.8, -1.2, -1.1, 1.05, 0.9, 1.05],
    },

    # --- метео ---
    "Skew-T log-P": {
        "x": [1000, 850, 700, 500, 300],
        "y": [20, 10, 0, -20, -40],
        "z": [15, 5, -5, -25, -45],
    },
    "Thermodynamic diagram": {
        "x": [1000, 850, 700, 500, 300],
        "y": [20, 10, 0, -20, -40],
        "z": [15, 5, -5, -25, -45],
    },

    # --- типы, где x = строки (метки категорий) ---
    "Диаграмма Парето": {
        "x": ["A", "B", "C", "D", "E"], "y": [45, 30, 12, 8, 5],
    },
    "Водопад": {
        "x": ["Старт", "A", "B", "C", "Итог"],
        "y": [100, 30, -15, -25, 90],
        "pie_labels": ["Старт", "A", "B", "C", "Итог"],
    },
    "Dot plot": {
        "x": ["A", "B", "C", "D", "E"], "y": [5, 3, 8, 2, 7],
    },
    "Dumbbell plot": {
        "x": ["A", "B", "C", "D", "E"],
        "y": [10, 20, 30, 40, 50], "z": [15, 25, 35, 45, 55],
    },
    "Slopegraph": {
        "x": ["До", "После"],
        "y": [10, 20, 30], "z": [15, 25, 35],
        "pie_labels": ["a", "b", "c"],
    },
    "Funnel chart": {
        "x": ["Visit", "Signup", "Buy"],
        "y": [100, 40, 10],
        "pie_colors": ["#ff0000", "#00ff00", "#0000ff"],
    },
    "Bullet chart": {"x": ["KPI"], "y": [60, 40, 100]},
    "Pie of pie": {
        "x": ["A", "B", "C", "D", "E"], "y": [10, 20, 30, 15, 25],
    },
    "Сосулька (icicle)": {
        "y": [10, 20, 30, 15, 25],
        "pie_labels": ["root", "A", "B", "A1", "B1"],
        "treemap_parents": ["", "root", "root", "A", "B"],
    },

    # --- иерархические / радар ---
    "Parallel coordinates": {
        "heatmap_data": [[1, 2, 3], [2, 3, 1], [3, 1, 2]],
        "pie_labels": ["X", "Y", "Z"],
    },
    "Radar chart": {
        "heatmap_data": [[3, 5, 7, 4, 6], [5, 4, 6, 7, 3]],
        "pie_labels": ["A", "B", "C", "D", "E"],
    },
    "Диаграмма Тейлора": {
        "heatmap_data": [[1.5, 1.2, 0.9], [0.9, 0.7, 0.5]],
        "x": [1.0], "pie_labels": ["M1", "M2", "M3"],
    },

    # --- временные ---
    "Вейвлет-скейлограмма": {
        "y": list(range(20)), "z": "cmor1.5-1.0", "bins": 1,
    },
    "Календарная теплокарта": {
        "x": list(range(1, 31)),
        "y": [1, 2, 3, 4, 5, 2, 3, 4, 5, 6] * 3,
    },

    # --- прочие ---
    "Гант": {
        "x": [0, 1, 3, 5, 7], "y": [2, 3, 2, 4, 1],
        "pie_labels": ["T1", "T2", "T3", "T4", "T5"],
    },
}


# ============================================================================
# ПРОЕКЦИИ
# ============================================================================
POLAR_TYPES = {
    "Радиальная", "Полярный scatter", "Полярная теплокарта",
    "Роза ветров", "Диаграмма Тейлора", "Sunburst", "Radar chart",
}


def _projection_for(t: str) -> str:
    if "3D" in t:
        return "3d"
    if t in POLAR_TYPES:
        return "polar"
    return "2d"


# ============================================================================
# ПОИСК FALLBACK-ТИПОВ В ИСХОДНИКЕ
# ============================================================================
def _find_fallback_types() -> set[str]:
    path = ROOT / "grapheditor" / "plots" / "_create_artist.py"
    if not path.exists():
        return set()
    src = path.read_text(encoding="utf-8")
    handled: set[str] = set()
    handled.update(re.findall(r't\s*==\s*"([^"]+)"', src))
    for group in re.findall(r't\s+in\s+\(([^)]+)\)', src, re.S):
        handled.update(re.findall(r'"([^"]+)"', group))
    return {t for t in INTERNAL_TYPES if t not in handled}


# ============================================================================
# ОСНОВНОЙ ЦИКЛ
# ============================================================================
def run(strict: bool, verbose: bool) -> int:
    app = MockApp()
    fallback = _find_fallback_types()

    ok, none_ok, errors = [], [], []

    for t in INTERNAL_TYPES:
        data = dict(BASE)
        data["type"] = t
        data.update(OVERRIDES.get(t, {}))

        proj = _projection_for(t)
        fig = plt.figure()
        try:
            if proj == "3d":
                ax = fig.add_subplot(111, projection="3d")
            elif proj == "polar":
                ax = fig.add_subplot(111, projection="polar")
            else:
                ax = fig.add_subplot(111)
            app.axes = [ax]
            app.axes_secondary = {}

            try:
                artist = app._create_artist(data)
            except Exception as e:
                tb = traceback.format_exc(limit=3)
                errors.append((t, f"{type(e).__name__}: {e}", tb))
                if verbose:
                    print(f"❌ {t}: {type(e).__name__}: {e}")
                continue

            if artist is None:
                none_ok.append(t)
                if verbose:
                    print(f"⚠️  {t}: вернул None")
            else:
                ok.append(t)
                if verbose:
                    print(f"✅ {t}")
        finally:
            plt.close(fig)

    # ---------- Отчёт ----------
    total = len(INTERNAL_TYPES)
    print()
    print("=" * 60)
    print(f"Smoke-тест: {total} типов")
    print("=" * 60)
    print(f"✅ OK:      {len(ok)}")
    print(f"⚠️  None:    {len(none_ok)}    (обрабатывается, но не рисует)")
    print(f"❌ ERROR:   {len(errors)}")

    if errors:
        print()
        print("Ошибки:")
        for t, msg, tb in errors:
            print(f"  ❌ {t}")
            print(f"     {msg}")
            if verbose:
                print("     " + tb.replace("\n", "\n     "))

    if none_ok:
        print()
        print("Вернули None (обрабатывается, но нужны другие данные):")
        for t in none_ok:
            print(f"  - {t}")

    if fallback:
        print()
        print(f"Без явной ветки в _create_artist (fallback-линия): {len(fallback)}")
        for t in sorted(fallback):
            print(f"  ⚠️  {t}")

    # ---------- Exit code ----------
    if errors:
        return 1
    if strict and none_ok:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true",
                    help="None тоже считать провалом")
    ap.add_argument("--verbose", "-v", action="store_true",
                    help="показывать каждый тип")
    args = ap.parse_args()
    return run(strict=args.strict, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())