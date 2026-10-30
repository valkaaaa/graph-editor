"""Пример плагина GraphEditor Pro: Stem plot (дискретный сигнал).

Расположение:
  - встроенный пример:  grapheditor/plugins/stem_plot.py
  - пользовательский:   ~/.grapheditor_plugins/stem_plot.py

После копирования в ~/.grapheditor_plugins/ перезагрузите через:
  Меню → Плагины → Перезагрузить плагины
"""
__author__ = "valkaa"

def register(api):
    """Точка входа плагина. Вызывается при загрузке."""
    api.add_chart_type(
        id="stem_plugin",
        display={
            "ru": "Ствол (stem)",
            "en": "Stem plot",
            "de": "Stammdiagramm",
            "fr": "Diagramme en tiges",
            "es": "Diagrama de tallos",
        },
        hint={
            "ru": "X, Y — значения. Рисует вертикальные «иголки» из нуля.\n"
                  "Идеально для дискретных сигналов, импульсов, отсчётов.",
            "en": "X, Y — values. Draws vertical 'needles' from zero.\n"
                  "Great for discrete signals, impulses, samples.",
        },
        fields=["x", "y"],
        draw=draw_stem,
        projection="2d",
    )


def draw_stem(ax, data, api):
    """Рисует stem plot. Возвращает artist или список artists.

    Параметры
    ---------
    ax   : matplotlib.axes.Axes — целевые оси (уже с учётом subplot_index
           и вторичной оси Y, если она включена)
    data : dict — все поля объекта:
           x, y, color, lw, ls, ms, marker, label, notes, ...
    api  : PluginAPI — помощник (np, plt, mcolors, parse_data, show_error)
    """
    import matplotlib.pyplot as plt

    x = data.get('x', [])
    y = data.get('y', [])
    if not x or not y:
        return None

    color = data.get('color', 'blue')
    lw = data.get('lw', 2.0)
    ms = data.get('ms', 6.0)
    label = data.get('label', 'stem')

    # matplotlib.stem возвращает три объекта
    markerline, stemlines, baseline = ax.stem(
        x, y,
        linefmt='-',
        markerfmt='o',
        basefmt='k-',
        label=label,
    )

    # Применяем стиль пользователя
    plt.setp(markerline, color=color, markersize=ms)
    plt.setp(stemlines, color=color, linewidth=lw)
    plt.setp(baseline, color='gray', linewidth=0.8, alpha=0.7)

    # Можно вернуть список — app сам обработает (см. _remove_artist)
    return [markerline, stemlines, baseline]