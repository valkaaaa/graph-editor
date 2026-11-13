"""Плагин: 3D-анимация двойного маятника.

Демонстрирует, как создать свою 3D-анимацию.
Использует физические уравнения (метод Эйлера-Кромера) для расчета
траектории, а затем проигрывает её в 3D с вращением камеры.
"""
import numpy as np


def register(api):
    api.add_animation(
        id="double_pendulum_3d",
        display={
            "ru": "Двойной маятник (3D)",
            "en": "Double pendulum (3D)",
            "de": "Doppelpendel (3D)"
        },
        create=create_3d_double_pendulum
    )


def create_3d_double_pendulum(app, ax):
    """Создает анимацию на переданных 3D-осях ax."""
    # --- 1. Физические параметры ---
    L1, L2 = 1.0, 1.0
    m1, m2 = 1.0, 1.0
    g = 9.81

    # Начальные условия
    th1, th2 = np.pi / 2, np.pi / 2
    w1, w2 = 0.0, 0.0

    # Шаг времени и количество шагов
    dt = 0.005
    steps = 4000

    # --- 2. Предварительный расчет траектории ---
    # Чтобы анимация работала плавно, мы рассчитываем всё заранее,
    # а не вычисляем физику на каждом кадре.
    traj = np.zeros((steps, 4))
    for i in range(steps):
        # Уравнения движения двойного маятника
        a1 = (-g * (2 * m1 + m2) * np.sin(th1)
              - m2 * g * np.sin(th1 - 2 * th2)
              - 2 * np.sin(th1 - th2) * m2 * (w2 ** 2 * L2 + w1 ** 2 * L1 * np.cos(th1 - th2))) \
             / (L1 * (2 * m1 + m2 - m2 * np.cos(2 * th1 - 2 * th2)))

        a2 = (2 * np.sin(th1 - th2) * (w1 ** 2 * L1 * (m1 + m2)
                                       + g * (m1 + m2) * np.cos(th1)
                                       + w2 ** 2 * L2 * m2 * np.cos(th1 - th2))) \
             / (L2 * (2 * m1 + m2 - m2 * np.cos(2 * th1 - 2 * th2)))

        # Интегрирование (Эйлер-Кромер)
        w1 += a1 * dt
        w2 += a2 * dt
        th1 += w1 * dt
        th2 += w2 * dt

        traj[i] = [th1, th2, w1, w2]

    # --- 3. Настройка 3D-осей ---
    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-0.5, 0.5)
    ax.set_zlim(-2.5, 1.0)
    ax.set_title("Двойной маятник в 3D")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # --- 4. Создание графических объектов ---
    # Стержни (линии)
    rod1, = ax.plot([], [], [], 'b-', lw=2, label="Стержень 1")
    rod2, = ax.plot([], [], [], 'g-', lw=2, label="Стержень 2")

    # Грузы (точки)
    bob1 = ax.scatter([], [], [], color='blue', s=100, edgecolors='black', zorder=5)
    bob2 = ax.scatter([], [], [], color='green', s=100, edgecolors='black', zorder=5)

    # След (траектория нижнего груза)
    trace_line, = ax.plot([], [], [], 'r-', lw=1, alpha=0.5, zorder=1)

    # Буфер для хранения следа (максимум 200 точек)
    trace_x, trace_y, trace_z = [], [], []
    max_trace = 200

    # --- 5. Функция обновления (вызывается для каждого кадра) ---
    def update(frame):
        # Берем кадр из заранее рассчитанной траектории
        # Умножаем на 3, чтобы маятник двигался быстрее
        idx = (frame * 3) % len(traj)
        t1, t2 = traj[idx, 0], traj[idx, 1]

        # Вычисляем декартовы координаты в 3D
        x1 = L1 * np.sin(t1)
        y1 = 0.0
        z1 = -L1 * np.cos(t1)

        x2 = x1 + L2 * np.sin(t2)
        y2 = 0.0
        z2 = z1 - L2 * np.cos(t2)

        # Обновляем стержни
        rod1.set_data_3d([0, x1], [0, y1], [0, z1])
        rod2.set_data_3d([x1, x2], [y1, y2], [z1, z2])

        # Обновляем грузы
        bob1._offsets3d = ([x1], [y1], [z1])
        bob2._offsets3d = ([x2], [y2], [z2])

        # Обновляем след
        trace_x.append(x2)
        trace_y.append(y2)
        trace_z.append(z2)
        if len(trace_x) > max_trace:
            trace_x.pop(0)
            trace_y.pop(0)
            trace_z.pop(0)
        trace_line.set_data_3d(trace_x, trace_y, trace_z)

        # Вращаем камеру для 3D-эффекта!
        azim = (frame * 0.5) % 360
        ax.view_init(elev=20, azim=azim)

        return rod1, rod2, bob1, bob2, trace_line

    return update