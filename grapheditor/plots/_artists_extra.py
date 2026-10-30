"""Дополнительные типы графиков.

14 типов, которые раньше были объявлены в INTERNAL_TYPES,
но не имели ветки отрисовки (рисовались fallback-линией).

Миксин для CreateArtistMixin. Вызывается из
_create_artist._draw_extra() для типов из TYPES_EXTRA.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


TYPES_EXTRA = frozenset({
    # 2D
    "Bar of pie", "Bump chart", "Cycle plot", "Dot plot",
    "Dumbbell plot", "Lollipop", "Ribbon plot 2D", "Sparkline",
    # Специальные
    "Funnel chart", "Parallel coordinates", "Пирамида",
    "Календарная теплокарта",
    # Полярные
    "Radar chart", "Полярная теплокарта",
})


class ArtistsExtraMixin:

    def _draw_extra(self, data, base_ax, target_ax):
        """Рисует 2D / polar график из TYPES_EXTRA."""
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        z = data.get('z', [])
        lw = data.get('lw', 2.0)
        ms = data.get('ms', 6.0)
        raw_marker = data.get('marker', 'o')
        marker = None if raw_marker == "None" else raw_marker
        fill = data.get('fill', False)

        artist = None

        # ====================================================================
        # 2D БАЗОВЫЕ
        # ====================================================================
        if t == "Dot plot":
            # x — метки категорий, y — значения.
            # Классический Cleveland dot plot: точки на горизонтальных линиях.
            if not y:
                return None
            y_arr = np.array(y, dtype=float)
            n = len(y_arr)
            if isinstance(x, list) and x and isinstance(x[0], str):
                labels = [str(v) for v in x[:n]]
            elif data.get('pie_labels'):
                labels = [str(v) for v in data['pie_labels'][:n]]
            else:
                labels = [f"C{i + 1}" for i in range(n)]
            while len(labels) < n:
                labels.append(f"C{len(labels) + 1}")

            ys = np.arange(n)
            base_ax.hlines(ys, 0, y_arr, color=c, lw=max(0.8, lw * 0.6),
                           alpha=0.6, zorder=1)
            artist = base_ax.scatter(
                y_arr, ys, s=max(40, ms ** 2 * 2),
                color=c, edgecolors='white', linewidths=0.8,
                zorder=3, label=lbl)
            base_ax.set_yticks(ys)
            base_ax.set_yticklabels(labels)
            base_ax.set_xlabel("Value")
            base_ax.invert_yaxis()
            base_ax.grid(True, axis='x', ls='--', alpha=0.4)

        elif t == "Lollipop":
            # x, y — как у обычной линии, но точки на «палочках» от оси Y=0.
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            n = min(len(x_arr), len(y_arr))
            if n < 1:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]

            base_ax.vlines(x_arr, 0, y_arr, color=c,
                           lw=max(0.8, lw * 0.6), alpha=0.7, zorder=1)
            artist = base_ax.scatter(
                x_arr, y_arr, s=max(50, ms ** 2 * 2.5),
                color=c, edgecolors='white', linewidths=0.8,
                zorder=3, label=lbl)
            base_ax.axhline(0, color='gray', lw=0.6, zorder=0)

        elif t == "Dumbbell plot":
            # x — метки, y и z — два значения на категорию.
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(z, dtype=float) if z else np.array([])
            n = min(len(y_arr), len(z_arr))
            if n < 1:
                return None
            y_arr, z_arr = y_arr[:n], z_arr[:n]

            if isinstance(x, list) and x and isinstance(x[0], str):
                labels = [str(v) for v in x[:n]]
            else:
                labels = [f"C{i + 1}" for i in range(n)]

            ys = np.arange(n)
            artists = []
            for i in range(n):
                ln, = base_ax.plot([y_arr[i], z_arr[i]], [i, i],
                                   color='#999', lw=1.5, zorder=2)
                artists.append(ln)
            s1 = base_ax.scatter(y_arr, ys,
                                 s=max(40, ms ** 2 * 2), color='#3498db',
                                 edgecolors='white', linewidths=0.8,
                                 zorder=3, label='Before')
            s2 = base_ax.scatter(z_arr, ys,
                                 s=max(40, ms ** 2 * 2), color=c,
                                 edgecolors='white', linewidths=0.8,
                                 zorder=3, label='After')
            base_ax.set_yticks(ys)
            base_ax.set_yticklabels(labels)
            base_ax.invert_yaxis()
            base_ax.grid(True, axis='x', ls='--', alpha=0.4)
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass
            artist = s2
            data['_extra_artists'] = artists

        elif t == "Sparkline":
            # Мини-линия без осей. x — индексы (или что угодно), y — значения.
            if not y:
                return None
            y_arr = np.array(y, dtype=float)
            x_arr = (np.array(x, dtype=float) if x and len(x) == len(y_arr)
                     else np.arange(len(y_arr)))
            artist, = base_ax.plot(x_arr, y_arr, color=c, lw=max(1.0, lw))
            # Точку-максимум и минимум
            try:
                imax = int(np.argmax(y_arr))
                imin = int(np.argmin(y_arr))
                base_ax.scatter([x_arr[imax]], [y_arr[imax]],
                                color='red', s=ms ** 2, zorder=3)
                base_ax.scatter([x_arr[imin]], [y_arr[imin]],
                                color='blue', s=ms ** 2, zorder=3)
            except Exception:
                pass
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            for spine in base_ax.spines.values():
                try:
                    spine.set_visible(False)
                except Exception:
                    pass

        elif t == "Cycle plot":
            # x — значения, y — ряд, z — фаза (или индекс цикла).
            # Рисует точки, разбитые по фазам; линия соединяет точки одной фазы.
            y_arr = np.array(y, dtype=float)
            n = len(y_arr)
            if n < 2:
                return None
            x_arr = (np.array(x, dtype=float) if x and len(x) == n
                     else np.arange(n))

            # Фазы: если z задан — берём оттуда, иначе 4 (кварталы)
            if z and len(z) >= n:
                phases = np.array(z[:n], dtype=int)
            else:
                period = int(data.get('bins', 4) or 4)
                phases = np.arange(n) % max(2, period)

            cmap = plt.get_cmap('tab10')
            artists = []
            unique_phases = sorted(set(int(p) for p in phases))
            for k, ph in enumerate(unique_phases):
                mask = phases == ph
                col = cmap(k % 10)
                sc = base_ax.scatter(x_arr[mask], y_arr[mask],
                                     s=max(30, ms ** 2 * 1.5),
                                     color=col, zorder=3,
                                     label=f"Phase {ph}")
                artists.append(sc)
                # Линия через точки одной фазы
                idx_sorted = np.argsort(x_arr[mask])
                ln, = base_ax.plot(x_arr[mask][idx_sorted],
                                   y_arr[mask][idx_sorted],
                                   color=col, lw=max(0.8, lw * 0.7),
                                   alpha=0.7, zorder=2)
                artists.append(ln)
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Ribbon plot 2D":
            # x, y — верхняя граница, z — нижняя граница. Заливка между ними.
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(z, dtype=float) if z else np.array([])
            n = min(len(x_arr), len(y_arr), len(z_arr))
            if n < 2:
                return None
            x_arr, y_arr, z_arr = x_arr[:n], y_arr[:n], z_arr[:n]

            fill_area = base_ax.fill_between(
                x_arr, z_arr, y_arr, color=c, alpha=0.35,
                label=lbl, zorder=2)
            top_line, = base_ax.plot(x_arr, y_arr, color=c,
                                     lw=max(1.2, lw), zorder=3)
            bot_line, = base_ax.plot(x_arr, z_arr, color=c,
                                     lw=max(0.8, lw * 0.7),
                                     ls='--', alpha=0.7, zorder=3)
            artist = top_line
            data['_extra_artists'] = [fill_area, bot_line]

        # ====================================================================
        # СПЕЦИАЛЬНЫЕ (2D)
        # ====================================================================
        elif t == "Bump chart":
            # x — временные точки, z — матрица [ranking × time].
            # Рисует линии, показывающие изменения рангов.
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                M = np.array(raw, dtype=float)
            except Exception:
                return None
            if M.ndim != 2:
                return None
            n_series, n_time = M.shape
            if n_series < 1 or n_time < 2:
                return None

            labels = data.get('pie_labels') or \
                     [f"S{i + 1}" for i in range(n_series)]
            x_vals = np.arange(n_time)
            cmap = plt.get_cmap('tab10')
            artists = []
            for i in range(n_series):
                col = cmap(i % 10)
                lbl_i = labels[i] if i < len(labels) else f"S{i + 1}"
                line, = base_ax.plot(x_vals, M[i], '-o',
                                     color=col, lw=max(1.2, lw),
                                     markersize=ms, zorder=2,
                                     label=str(lbl_i))
                artists.append(line)
                # Подписи на концах
                try:
                    base_ax.text(x_vals[-1] + 0.1, M[i, -1],
                                 str(lbl_i), va='center', fontsize=9,
                                 color=col)
                    base_ax.text(x_vals[0] - 0.1, M[i, 0],
                                 str(lbl_i), va='center', ha='right',
                                 fontsize=9, color=col)
                except Exception:
                    pass
            base_ax.set_xticks(x_vals)
            col_labels = data.get('col_labels', [])
            if col_labels and len(col_labels) == n_time:
                base_ax.set_xticklabels([str(v) for v in col_labels])
            base_ax.set_ylabel("Rank")
            base_ax.invert_yaxis()
            base_ax.set_xlim(-1, n_time)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Funnel chart":
            # x — метки этапов, y — значения (убывающие)
            y_arr = np.array(y, dtype=float) if y else np.array([])
            if len(y_arr) < 1:
                return None
            n = len(y_arr)

            if isinstance(x, list) and x and isinstance(x[0], str):
                labels = [str(v) for v in x[:n]]
            elif data.get('pie_labels'):
                labels = [str(v) for v in data['pie_labels'][:n]]
            else:
                labels = [f"Step {i + 1}" for i in range(n)]
            while len(labels) < n:
                labels.append(f"Step {len(labels) + 1}")

            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != n:
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(n)]

            max_val = float(y_arr.max()) or 1.0
            artists = []
            for i in range(n):
                width = y_arr[i] / max_val
                # Трапеция: сверху шире, снизу уже (следующий этап)
                next_width = (y_arr[i + 1] / max_val
                              if i + 1 < n else width * 0.8)
                y_top = n - 1 - i
                y_bot = y_top - 1
                verts = [
                    (-width / 2, y_top),
                    (width / 2, y_top),
                    (next_width / 2, y_bot),
                    (-next_width / 2, y_bot),
                ]
                poly = plt.Polygon(verts, facecolor=pc[i],
                                   edgecolor='white', linewidth=2.0,
                                   alpha=0.85, zorder=2)
                base_ax.add_patch(poly)
                artists.append(poly)
                # Подпись в центре
                base_ax.text(0, y_top - 0.5,
                             f"{labels[i]}: {y_arr[i]:g}",
                             ha='center', va='center', fontsize=9,
                             color='white', fontweight='bold', zorder=3)

            base_ax.set_xlim(-0.7, 0.7)
            base_ax.set_ylim(-0.2, n)
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            try:
                base_ax.axis('off')
            except Exception:
                pass
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Пирамида":
            # x — метки, y — левая сторона, z — правая сторона
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(z, dtype=float) if z else np.array([])
            n = min(len(y_arr), len(z_arr))
            if n < 1:
                return None
            y_arr, z_arr = y_arr[:n], z_arr[:n]

            if isinstance(x, list) and x and isinstance(x[0], str):
                labels = [str(v) for v in x[:n]]
            else:
                labels = [f"G{i + 1}" for i in range(n)]

            ys = np.arange(n)
            left_bars = base_ax.barh(ys, -y_arr, color='#3498db',
                                     edgecolor='white', alpha=0.85,
                                     label='Left', zorder=2)
            right_bars = base_ax.barh(ys, z_arr, color=c,
                                      edgecolor='white', alpha=0.85,
                                      label='Right', zorder=2)
            base_ax.axvline(0, color='black', lw=0.8, zorder=3)
            base_ax.set_yticks(ys)
            base_ax.set_yticklabels(labels)
            base_ax.set_xlabel("← Left   |   Right →")
            # Симметричные пределы
            max_val = max(float(np.abs(y_arr).max()),
                          float(np.abs(z_arr).max()), 1e-9)
            base_ax.set_xlim(-max_val * 1.15, max_val * 1.15)
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass
            artist = right_bars
            data['_extra_artists'] = [left_bars]

        elif t == "Parallel coordinates":
            # z — матрица [строк × осей]. Каждая строка — линия.
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                M = np.array(raw, dtype=float)
            except Exception:
                return None
            if M.ndim != 2:
                return None
            n_rows, n_axes = M.shape
            if n_axes < 2 or n_rows < 1:
                return None

            # Нормализация каждой оси к [0, 1]
            mn = M.min(axis=0)
            mx = M.max(axis=0)
            rng_ = np.where(mx > mn, mx - mn, 1.0)
            Mn = (M - mn) / rng_

            axis_names = data.get('pie_labels') or \
                         [f"A{i + 1}" for i in range(n_axes)]
            cmap = plt.get_cmap('tab10')
            xs = np.arange(n_axes)
            artists = []
            for i in range(n_rows):
                ln, = base_ax.plot(xs, Mn[i], '-',
                                   color=cmap(i % 10),
                                   lw=max(0.8, lw * 0.7),
                                   alpha=0.6, zorder=2)
                artists.append(ln)

            # Оси
            for j in range(n_axes):
                ln = base_ax.axvline(j, color='#999', lw=1.0,
                                     alpha=0.5, zorder=1)
                artists.append(ln)
            base_ax.set_xticks(xs)
            base_ax.set_xticklabels([str(a) for a in axis_names[:n_axes]],
                                    rotation=30, ha='right')
            base_ax.set_yticks([0, 0.5, 1])
            base_ax.set_yticklabels(['min', 'mid', 'max'])
            base_ax.set_xlim(-0.2, n_axes - 0.8)
            base_ax.grid(True, axis='y', ls='--', alpha=0.3)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Календарная теплокарта":
            # y — значения по дням (≥ 365).
            y_arr = np.array(y, dtype=float) if y else np.array([])
            if len(y_arr) < 1:
                return None
            n = len(y_arr)

            # Раскладка: 7 дней в неделе × ~52 недели
            n_cols = max(1, (n + 6) // 7)
            grid = np.full((7, n_cols), np.nan)
            for i, v in enumerate(y_arr):
                row = i % 7
                col = i // 7
                if col < n_cols:
                    grid[row, col] = v

            artist = base_ax.imshow(grid, cmap='YlGn', aspect='auto',
                                    interpolation='nearest')
            base_ax.set_yticks(range(7))
            base_ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu',
                                     'Fri', 'Sat', 'Sun'])
            base_ax.set_xlabel("Week")
            base_ax.set_title("Calendar heatmap")
            try:
                cb = base_ax.figure.colorbar(artist, ax=base_ax,
                                             shrink=0.8, pad=0.02)
                data['_extra_artists'] = [cb]
            except Exception:
                pass

        elif t == "Bar of pie":
            # y — значения, первая доля раскрывается как бары.
            vals = np.array(y, dtype=float)
            if len(vals) < 2:
                return None
            labels = data.get('pie_labels') or \
                     [f"C{i + 1}" for i in range(len(vals))]
            while len(labels) < len(vals):
                labels.append(f"C{len(labels) + 1}")
            labels = labels[:len(vals)]

            # Раскрываем ПЕРВУЮ долю (n_out = первая доля), остальные — пирог
            n_out = 1
            small = [vals[0]]
            big_vals = vals[1:]
            big_labels = labels[1:]

            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(vals):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(vals))]

            artists = []
            # Пирог справа
            w1, t1, a1 = base_ax.pie(
                big_vals, labels=big_labels, colors=pc[1:],
                autopct='%1.1f%%', radius=0.5, center=(0.6, 0.5),
                wedgeprops=dict(edgecolor='white', linewidth=1.0))
            for t_ in t1:
                t_.set_fontsize(8)
            for t_ in a1:
                t_.set_fontsize(7)
            artists.extend(w1)

            # Бары слева для раскрытой доли (одна доля → один бар)
            if isinstance(small, list) and len(small) == 1:
                bars = base_ax.barh(
                    [0], [small[0]], color=pc[0],
                    edgecolor='white', height=0.4)
                artists.extend(list(bars))
                base_ax.text(
                    -0.05, 0.5,
                    f"{labels[0]}\n{small[0]:g}",
                    ha='right', va='center', fontsize=9)

            # Соединительные линии
            try:
                conn1, = base_ax.plot([-0.05, 0.15], [0.6, 0.65],
                                      color='#999', lw=0.8, zorder=1)
                conn2, = base_ax.plot([-0.05, 0.15], [0.4, 0.35],
                                      color='#999', lw=0.8, zorder=1)
                artists.extend([conn1, conn2])
            except Exception:
                pass

            base_ax.set_xlim(-0.6, 1.1)
            base_ax.set_ylim(0, 1)
            base_ax.set_aspect('equal')
            base_ax.axis('off')
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        # ====================================================================
        # ПОЛЯРНЫЕ (требуют polar projection)
        # ====================================================================
        elif t == "Radar chart":
            if getattr(target_ax, 'name', '') != 'polar':
                return None
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                M = np.array(raw, dtype=float)
            except Exception:
                return None
            if M.ndim != 2:
                return None
            n_series, n_axes = M.shape
            if n_axes < 3:
                return None

            axis_labels = data.get('pie_labels') or \
                          [f"A{i + 1}" for i in range(n_axes)]
            while len(axis_labels) < n_axes:
                axis_labels.append(f"A{len(axis_labels) + 1}")
            axis_labels = axis_labels[:n_axes]

            angles = np.linspace(0, 2 * np.pi, n_axes,
                                 endpoint=False).tolist()
            angles += angles[:1]     # замкнуть

            cmap = plt.get_cmap('tab10')
            artists = []
            for i in range(n_series):
                vals = M[i].tolist()
                vals += vals[:1]
                ln, = target_ax.plot(angles, vals,
                                     color=cmap(i % 10),
                                     lw=max(1.2, lw),
                                     label=f"Series {i + 1}", zorder=3)
                fill_area = target_ax.fill(angles, vals,
                                           color=cmap(i % 10),
                                           alpha=0.2, zorder=2)
                artists.extend([ln, fill_area])

            target_ax.set_xticks(angles[:-1])
            target_ax.set_xticklabels(axis_labels)
            target_ax.set_theta_zero_location('N')
            target_ax.set_theta_direction(-1)
            target_ax.set_title("Radar chart")
            try:
                target_ax.legend(fontsize=8, loc='best',
                                 bbox_to_anchor=(1.1, 1.1))
            except Exception:
                pass
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Полярная теплокарта":
            if getattr(target_ax, 'name', '') != 'polar':
                return None
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.ndim != 2:
                return None
            n_rings, n_sectors = Z.shape
            if n_rings < 1 or n_sectors < 1:
                return None

            # Углы — сектора, радиусы — кольца
            theta = np.linspace(0, 2 * np.pi, n_sectors, endpoint=False)
            radii = np.arange(1, n_rings + 1)

            # Mesh: theta_edges × r_edges
            theta_edges = np.linspace(0, 2 * np.pi, n_sectors + 1)
            r_edges = np.linspace(0, n_rings, n_rings + 1)
            T, R = np.meshgrid(theta_edges, r_edges)

            artist = target_ax.pcolormesh(T, R, Z, cmap='viridis',
                                          shading='auto')
            target_ax.set_theta_zero_location('N')
            target_ax.set_theta_direction(-1)
            target_ax.set_title("Polar heatmap")
            try:
                cb = target_ax.figure.colorbar(artist, ax=target_ax,
                                               shrink=0.8, pad=0.1)
                data['_extra_artists'] = [cb]
            except Exception:
                pass

        return artist