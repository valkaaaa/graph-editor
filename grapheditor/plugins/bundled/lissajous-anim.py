"""Плагин: анимация фигур Лиссажу."""
import numpy as np

__author__ = "valkaa"

def register(api):
    api.add_animation(
        id="lissajous",
        display={"ru": "Фигуры Лиссажу", "en": "Lissajous"},
        create=create_lissajous,
    )


def create_lissajous(app, ax):
    """Создаёт анимацию на переданных осях ax."""
    # Начальная настройка осей
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_aspect('equal')
    ax.set_title("Фигуры Лиссажу")
    ax.grid(True, linestyle='--', alpha=0.3)

    # Создаём пустую линию, которую будем обновлять
    line, = ax.plot([], [], 'c-', lw=2)

    t = np.linspace(0, 2 * np.pi, 500)

    # ЭТА ФУНКЦИЯ БУДЕТ ВЫЗЫВАТЬСЯ ДЛЯ КАЖДОГО КАДРА
    def update(frame):
        # Меняем частоты (a и b) каждые 100 кадров
        a = 1 + (frame // 100) % 5
        b = 1 + ((frame // 100) + 2) % 5

        # Фаза плавно меняется
        phase = frame / 20.0

        # Вычисляем координаты
        x = np.sin(a * t + phase)
        y = np.sin(b * t)

        # Обновляем линию и возвращаем её (для отрисовки)
        line.set_data(x, y)
        return line,

    return update