"""Forest plot — сводка эффектов из нескольких исследований.

X — эффект для каждого исследования
Y — матрица: "lower; upper" (границы 95% CI)
Подписи — названия исследований
"""
__author__ = "valkaa"

def register(api):
    api.add_chart_type(
        id="forest_plot",
        display={
            "ru": "Форест-плот (мета-анализ)",
            "en": "Forest plot",
        },
        hint={
            "ru": "X — эффекты (числа через запятую).\n"
                  "Y — матрица границ CI (две строки через ';'):\n"
                  "    нижние_границы ; верхние_границы\n"
                  "Подписи — названия исследований.",
            "en": "X — effects. Y — CI bounds matrix (lower; upper).\n"
                  "Labels — study names.",
        },
        fields=["x", "y", "pie_labels"],
        draw=draw_forest,
        projection="2d",
    )


def draw_forest(ax, data, api):
    import numpy as np
    effects = np.array(data['x'], dtype=float)
    if len(effects) < 1:
        return None

    raw_y = data.get('y', [])
    if isinstance(raw_y, list) and raw_y and isinstance(raw_y[0], str):
        return None
    try:
        ci_matrix = np.array(raw_y, dtype=float)
    except (ValueError, TypeError):
        return None
    if ci_matrix.ndim != 2 or ci_matrix.shape[0] != 2:
        return None
    if ci_matrix.shape[1] != len(effects):
        return None
    lower = ci_matrix[0]
    upper = ci_matrix[1]

    labels = data.get('pie_labels') or \
             [f'Study {i + 1}' for i in range(len(effects))]
    while len(labels) < len(effects):
        labels.append(f'Study {len(labels) + 1}')

    n = len(effects)
    ys = np.arange(n)[::-1]
    color = data.get('color', 'blue')

    # CI whiskers
    for i in range(n):
        ax.plot([lower[i], upper[i]], [ys[i], ys[i]],
                color='black', lw=1.5, zorder=2)

    # Effect points
    sizes = 20 + np.abs(effects) * 15
    ax.scatter(effects, ys, s=sizes, color=color,
               edgecolors='black', linewidths=0.8,
               zorder=3, label=data.get('label', ''))

    # Reference line (no effect)
    ax.axvline(0, color='gray', ls='--', lw=1.0, zorder=1)

    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('Effect size (95% CI)')
    ax.set_ylim(-0.7, n - 0.3)
    ax.grid(True, axis='x', ls='--', alpha=0.3)
    return ax.collections[-1] if ax.collections else None