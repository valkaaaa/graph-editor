"""Bland-Altman plot — сравнение двух методов измерения.

X и Y — результаты двух методов для одних и тех же образцов.
Показывает разницу между методами против среднего.
"""
__author__ = "valkaa"

def register(api):
    api.add_chart_type(
        id="bland_altman",
        display={
            "ru": "Блэнд-Альтман",
            "en": "Bland-Altman",
            "de": "Bland-Altman",
            "fr": "Bland-Altman",
        },
        hint={
            "ru": "X — метод 1, Y — метод 2 (одинаковые образцы).\n"
                  "Показывает среднюю разницу и пределы согласия (95%).",
            "en": "X — method 1, Y — method 2 (same samples).\n"
                  "Shows mean difference and limits of agreement (95%).",
        },
        fields=["x", "y"],
        draw=draw_bland_altman,
        projection="2d",
    )


def draw_bland_altman(ax, data, api):
    import numpy as np
    x = np.array(data['x'], dtype=float)
    y = np.array(data['y'], dtype=float)
    n = min(len(x), len(y))
    if n < 2:
        return None
    x, y = x[:n], y[:n]

    mean_vals = (x + y) / 2
    diff_vals = x - y
    md = float(np.mean(diff_vals))
    sd = float(np.std(diff_vals, ddof=1))
    loa_hi = md + 1.96 * sd
    loa_lo = md - 1.96 * sd

    color = data.get('color', 'blue')
    label = data.get('label', 'Bland-Altman')
    ms = data.get('ms', 6.0)

    sc = ax.scatter(mean_vals, diff_vals, s=ms ** 2,
                    color=color, alpha=0.6,
                    edgecolors='black', linewidths=0.5,
                    label=label, zorder=3)

    ax.axhline(md, color='red', ls='-', lw=1.2, zorder=2,
               label=f'Mean diff = {md:.3g}')
    ax.axhline(loa_hi, color='gray', ls='--', lw=1.0, zorder=2,
               label=f'+1.96 SD = {loa_hi:.3g}')
    ax.axhline(loa_lo, color='gray', ls='--', lw=1.0, zorder=2,
               label=f'-1.96 SD = {loa_lo:.3g}')

    ax.set_xlabel('Среднее двух методов')
    ax.set_ylabel('Разница (метод 1 − метод 2)')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, ls='--', alpha=0.4)
    return sc