"""Кумулятивная гистограмма (CDF по бинам).

X — выборка (одна серия)
Кол-во бинов — из поля «бины»
"""
__author__ = "valkaa"

def register(api):
    api.add_chart_type(
        id="cumulative_hist",
        display={
            "ru": "Кумулятивная гистограмма",
            "en": "Cumulative histogram",
        },
        hint={
            "ru": "X — выборка. Показывает долю значений ≤ бина.",
            "en": "X — sample. Shows cumulative share.",
        },
        fields=["x", "bins"],
        draw=draw_cumhist,
        projection="2d",
        extra_defaults={"bins": 15},
    )


def draw_cumhist(ax, data, api):
    import numpy as np
    x = np.array(data['x'], dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return None
    bins = int(data.get('bins', 15))
    bins = max(3, min(200, bins))

    counts, edges = np.histogram(x, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    cumulative = np.cumsum(counts) / counts.sum() * 100

    color = data.get('color', 'blue')
    bars = ax.bar(centers, cumulative, width=np.diff(edges),
                  color=color, alpha=0.7, edgecolor='white',
                  label=data.get('label', ''))
    ax.set_ylabel('% накопленный')
    ax.set_ylim(0, 105)
    ax.grid(True, ls='--', alpha=0.4)
    return bars