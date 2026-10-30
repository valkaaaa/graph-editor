"""Плагин: шаблон «Линейная регрессия с шумом»."""
import numpy as np

__author__ = "valkaa"

def register(api):
    api.add_template(
        id="regression_demo",
        display={"ru": "Линейная регрессия с шумом"},
        builder=build_regression,
    )


def build_regression(app):
    """Заполняет документ объектами (вызывается автоматически)."""
    np.random.seed(42)

    # 1. Генерируем данные
    x = np.linspace(0, 10, 50)
    y_true = 2 * x + 1
    y_noisy = y_true + np.random.normal(0, 2, len(x))

    # 2. Добавляем точки (scatter)
    app._quick_add(
        'Точечная',
        x.tolist(),
        y_noisy.tolist(),
        label='Данные',
        color='black',
        ms=8
    )

    # 3. Считаем линию тренда
    coeffs = np.polyfit(x, y_noisy, 1)
    y_fit = np.polyval(coeffs, x)
    eq_text = f"y = {coeffs[0]:.2f}x + {coeffs[1]:.2f}"

    # 4. Добавляем линию тренда (line)
    app._quick_add(
        'Линия',
        x.tolist(),
        y_fit.tolist(),
        label=eq_text,
        color='red',
        ls='--',
        lw=1.5
    )

    # 5. Меняем заголовки холста
    app.plot_title_var.set("Пример регрессии")
    app.plot_xlabel_var.set("Ось X")
    app.plot_ylabel_var.set("Ось Y")