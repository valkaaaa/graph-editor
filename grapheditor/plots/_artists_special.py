"""Специальные графики: векторные поля, радио, гео, ML, экзотика.

Миксин для CreateArtistMixin. Вызывается из _create_artist._draw_special()
для типов из TYPES_SPECIAL.
"""
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


TYPES_SPECIAL = frozenset({
    # Векторные поля
    "Stream plot", "Streamlines",
    # Радиотехника
    "Bode plot", "Smith chart", "Nyquist plot",
    "Root locus", "Constellation diagram",
    # Гео / метео
    "Choropleth", "Flow map", "Isopleth", "Cartogram",
    "Dot density map", "Hodograph", "Роза ветров",
    "Skew-T log-P", "Thermodynamic diagram",
    # Геометрия
    "Диаграмма Вороного", "Выпуклая оболочка", "Alpha shape",
    # ML / статистика
    "Volcano plot", "ROC curve", "Manhattan plot", "MA plot",
    "Recurrence plot", "Cobweb plot", "Poincaré plot",
    "Phase portrait",
    # Специальные / экзотика
    "Вафельная диаграмма", "Сосулька (icicle)",
    "Диаграмма Аргана", "Диаграмма Тейлора",
    "Горизонтальная столбчатая", "Горизонтальная линия",
    "Pie of pie", "Топографический профиль",
    "Вейвлет-скейлограмма",
    "Treemap", "Sunburst",
    # Сравнение / ранги
    "Slopegraph", "Bullet chart",
    "Диаграмма бифуркаций", "Спидометр",
})


class ArtistsSpecialMixin:

    def _draw_special(self, data, base_ax, target_ax):
        """Рисует специальный тип графика. Возвращает artist или None."""
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        z = data.get('z', [])
        lw = data.get('lw', 2.0)
        ls = data.get('ls', '-')
        ms = data.get('ms', 6.0)
        raw_marker = data.get('marker', 'o')
        marker = None if raw_marker == "None" else raw_marker
        yerr = data.get('yerr', []) or None
        fill = data.get('fill', False)

        artist = None

        # ====================================================================
        # ВЕКТОРНЫЕ ПОЛЯ
        # ====================================================================
        if t == "Stream plot":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            rawU = data.get('heatmap_data', [])
            rawV = data.get('yerr_matrix', [])
            if (not rawU or not rawV
                    or not x_arr.size or not y_arr.size):
                base_ax.text(0.5, 0.5,
                             'Нужны Z (U) и Yerr (V) в виде матриц',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            try:
                U = np.array(rawU, dtype=float)
                V = np.array(rawV, dtype=float)
            except Exception:
                return None
            if U.shape != V.shape:
                base_ax.text(0.5, 0.5,
                             'Матрицы U и V разной формы',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            m, n = U.shape
            xg = x_arr if len(x_arr) == n else np.arange(n)
            yg = y_arr if len(y_arr) == m else np.arange(m)
            X, Y = np.meshgrid(xg, yg)
            speed = np.sqrt(U ** 2 + V ** 2)
            try:
                strm = base_ax.streamplot(
                    X, Y, U, V,
                    color=speed, cmap=data.get('cmap', 'viridis'),
                    linewidth=max(0.5, lw * 0.5),
                    density=float(data.get('density', 1.2)),
                    arrowsize=1.2)
            except Exception as e:
                base_ax.text(0.5, 0.5, f'Streamplot error: {e}',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            extra = []
            if hasattr(strm, 'lines'):
                extra.append(strm.lines)
            if hasattr(strm, 'arrows'):
                extra.append(strm.arrows)
            if data.get('show_colorbar', True):
                try:
                    cb = base_ax.figure.colorbar(strm.lines, ax=base_ax)
                    extra.append(cb)
                except Exception:
                    pass
            data['_extra_artists'] = extra
            artist = strm.lines if hasattr(strm, 'lines') else None

        elif t == "Streamlines":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            rawU = data.get('heatmap_data', [])
            rawV = data.get('yerr_matrix', [])
            if (not rawU or not rawV
                    or not x_arr.size or not y_arr.size):
                base_ax.text(0.5, 0.5,
                             'Нужны Z (U) и Yerr (V) в виде матриц',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            try:
                U = np.array(rawU, dtype=float)
                V = np.array(rawV, dtype=float)
            except Exception:
                return None
            if U.shape != V.shape:
                base_ax.text(0.5, 0.5,
                             'Матрицы U и V разной формы',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            m, n = U.shape
            xg = x_arr if len(x_arr) == n else np.arange(n)
            yg = y_arr if len(y_arr) == m else np.arange(m)
            X, Y = np.meshgrid(xg, yg)
            speed = np.sqrt(U ** 2 + V ** 2)

            density = max(0.5, min(3.0,
                                   int(data.get('bins', 10)) / 5.0))
            try:
                strm = base_ax.streamplot(
                    X, Y, U, V,
                    color=speed, cmap=data.get('cmap', 'viridis'),
                    linewidth=max(0.6, lw * 0.6),
                    density=density,
                    arrowsize=1.5,
                    integration_direction='both')
            except Exception as e:
                base_ax.text(0.5, 0.5, f'Streamlines error: {e}',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None

            extra = []
            if hasattr(strm, 'lines'):
                extra.append(strm.lines)
            if hasattr(strm, 'arrows'):
                extra.append(strm.arrows)
            if data.get('show_colorbar', True):
                try:
                    cb = base_ax.figure.colorbar(strm.lines, ax=base_ax)
                    extra.append(cb)
                except Exception:
                    pass
            data['_extra_artists'] = extra
            artist = strm.lines if hasattr(strm, 'lines') else None

        # ====================================================================
        # РАДИОТЕХНИКА
        # ====================================================================
        elif t == "Bode plot":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            rawP = data.get('heatmap_data', [])
            if rawP:
                P_arr = np.array(rawP[0], dtype=float)
            else:
                z_col = data.get('z', [])
                P_arr = np.array(z_col, dtype=float) if z_col else None

            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]
            if P_arr is not None and len(P_arr) >= n:
                P_arr = P_arr[:n]

            mag_line, = base_ax.semilogx(
                np.abs(x_arr), y_arr, 'o-',
                color=c, lw=lw, markersize=max(3, ms * 0.6),
                label=(lbl or 'Magnitude'))
            base_ax.set_ylabel('Амплитуда (дБ)')
            base_ax.set_xlabel('Частота (лог)')

            extra = [mag_line]
            phase_axis = None
            subplot_idx = data.get('subplot_index', 0)
            total_axes = len(self.axes)
            next_idx = subplot_idx + 1

            if (total_axes > 1 and next_idx < total_axes
                    and P_arr is not None):
                phase_axis = self.axes[next_idx]
            else:
                try:
                    phase_axis = base_ax.twinx()
                except Exception:
                    phase_axis = None

            if phase_axis is not None and P_arr is not None:
                try:
                    ph_line, = phase_axis.semilogx(
                        np.abs(x_arr), P_arr, 's--',
                        color='orange', lw=max(0.8, lw * 0.8),
                        markersize=max(3, ms * 0.5))
                    phase_axis.set_ylabel('Фаза (°)', color='orange')
                    try:
                        phase_axis.tick_params(
                            axis='y', labelcolor='orange')
                    except Exception:
                        pass
                    extra.append(ph_line)

                    if (total_axes > 1 and next_idx < total_axes
                            and phase_axis is self.axes[next_idx]):
                        def _cleanup(_ax=phase_axis):
                            try:
                                _ax.clear()
                                _ax.set_title(
                                    self.plot_title_var.get())
                            except Exception:
                                pass

                        data['_cleanup'] = _cleanup
                    else:
                        def _cleanup(_ax=phase_axis):
                            try:
                                _ax.remove()
                            except Exception:
                                pass

                        data['_cleanup'] = _cleanup
                except Exception:
                    pass

            data['_extra_artists'] = extra
            artist = mag_line

        elif t == "Smith chart":
            z_matrix = data.get('heatmap_data', [])
            if z_matrix and len(z_matrix) >= 2:
                re_arr = np.array(z_matrix[0], dtype=float)
                im_arr = np.array(z_matrix[1], dtype=float)
            else:
                re_arr = np.array(x, dtype=float)
                im_arr = np.array(y, dtype=float)
            n = min(len(re_arr), len(im_arr))
            if n < 1:
                return None
            re_arr, im_arr = re_arr[:n], im_arr[:n]

            extra = []
            R_VALUES = [0, 0.2, 0.5, 1, 2, 5, 10]
            X_VALUES = [0.2, 0.5, 1, 2, 5, -0.2, -0.5, -1, -2, -5]

            for r in R_VALUES:
                cx = r / (r + 1)
                rad = 1 / (r + 1)
                th = np.linspace(0, 2 * np.pi, 200)
                circ_x = cx + rad * np.cos(th)
                circ_y = rad * np.sin(th)
                ln, = base_ax.plot(circ_x, circ_y, color='#bbb',
                                   lw=0.5, alpha=0.7, zorder=1)
                extra.append(ln)
            for xv in X_VALUES:
                cy = 1 / xv
                rad = abs(1 / xv)
                th = np.linspace(-np.pi, np.pi, 200)
                circ_x = 1 + rad * np.cos(th)
                circ_y = cy + rad * np.sin(th)
                mask = (circ_x ** 2 + circ_y ** 2) <= 1.0001
                if mask.any():
                    ln, = base_ax.plot(circ_x[mask], circ_y[mask],
                                       color='#bbb', lw=0.5,
                                       alpha=0.7, zorder=1)
                    extra.append(ln)

            th = np.linspace(0, 2 * np.pi, 300)
            border, = base_ax.plot(np.cos(th), np.sin(th),
                                   color='#333', lw=1.2, zorder=2)
            extra.append(border)
            axis_ln, = base_ax.plot([-1, 1], [0, 0],
                                    color='#333', lw=0.8, zorder=2)
            extra.append(axis_ln)

            z_complex = re_arr + 1j * im_arr
            gamma = (z_complex - 1) / (z_complex + 1)
            gx = np.real(gamma)
            gy = np.imag(gamma)
            main_artist = base_ax.scatter(
                gx, gy, s=max(20, ms ** 2 * 2),
                color=c, edgecolors='white', linewidths=0.8,
                zorder=5, label=lbl)

            if n > 2:
                trace, = base_ax.plot(gx, gy, '-',
                                      color=c, lw=max(0.6, lw * 0.6),
                                      alpha=0.6, zorder=4)
                extra.append(trace)

            base_ax.set_xlim(-1.15, 1.15)
            base_ax.set_ylim(-1.15, 1.15)
            try:
                base_ax.set_aspect('equal')
            except Exception:
                pass
            base_ax.set_xticks([])
            base_ax.set_yticks([])

            data['_extra_artists'] = extra
            artist = main_artist

        elif t == "Nyquist plot":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(data.get('z', []), dtype=float)
            n = min(len(x_arr), len(y_arr), len(z_arr))
            if n < 2:
                return None
            x_arr, y_arr, z_arr = x_arr[:n], y_arr[:n], z_arr[:n]

            artists = []
            h_axis, = base_ax.axhline(0, color='gray', lw=0.6, zorder=1)
            v_axis, = base_ax.axvline(0, color='gray', lw=0.6, zorder=1)
            artists.extend([h_axis, v_axis])

            line, = base_ax.plot(y_arr, z_arr, '-',
                                 color=c, lw=lw, label=lbl, zorder=3)
            artists.append(line)

            sc = base_ax.scatter(y_arr, z_arr,
                                 s=max(4, ms * 0.3),
                                 color=c, alpha=0.6,
                                 edgecolors='none', zorder=4)
            artists.append(sc)

            start = base_ax.scatter(
                [y_arr[0]], [z_arr[0]],
                s=max(40, ms ** 2 * 2), color='green',
                edgecolors='black', zorder=5, label='ω_min')
            end = base_ax.scatter(
                [y_arr[-1]], [z_arr[-1]],
                s=max(40, ms ** 2 * 2), color='red',
                edgecolors='black', zorder=5, label='ω_max')
            artists.extend([start, end])

            crit = base_ax.scatter(
                [-1], [0],
                s=max(80, ms ** 2 * 4), color='orange',
                marker='X', edgecolors='black',
                zorder=6, label='(-1, 0)')
            artists.append(crit)

            base_ax.set_xlabel("Re")
            base_ax.set_ylabel("Im")
            base_ax.set_title("Nyquist plot")
            base_ax.legend(fontsize=8, loc='best')
            try:
                base_ax.set_aspect('equal', adjustable='datalim')
            except Exception:
                pass

            data['_extra_artists'] = artists
            artist = line

        elif t == "Root locus":
            num = np.array(x, dtype=float)
            den = np.array(y, dtype=float)
            if len(num) < 1 or len(den) < 2:
                return None
            n_k = max(50, min(2000, int(data.get('bins', 200))))
            k_vals = np.concatenate([
                np.linspace(0, 1, n_k // 2, endpoint=False),
                np.logspace(0, 3, n_k - n_k // 2)
            ])
            all_roots = []
            for K in k_vals:
                L = max(len(den), len(num))
                d = np.pad(den, (L - len(den), 0))
                n_ = np.pad(num, (L - len(num), 0))
                coeffs = d + K * n_
                try:
                    roots = np.roots(coeffs)
                except Exception:
                    continue
                all_roots.append((K, roots))

            if not all_roots:
                return None

            order = len(den) - 1
            if order < 1:
                order = 1
            branches = [[] for _ in range(order)]
            prev_roots = None
            for K, roots in all_roots:
                roots_sorted = np.sort_complex(roots)
                if prev_roots is not None and \
                        len(prev_roots) == len(roots_sorted):
                    used = [False] * len(prev_roots)
                    new_order = []
                    for r in prev_roots:
                        best_j = -1
                        best_d = float('inf')
                        for j, rr in enumerate(roots_sorted):
                            if used[j]:
                                continue
                            d = abs(rr - r)
                            if d < best_d:
                                best_d = d
                                best_j = j
                        if best_j >= 0:
                            new_order.append(roots_sorted[best_j])
                            used[best_j] = True
                    if len(new_order) == len(roots_sorted):
                        roots_sorted = np.array(new_order)
                prev_roots = roots_sorted

                for i, r in enumerate(roots_sorted):
                    if i < len(branches):
                        branches[i].append(r)

            cmap_rl = plt.get_cmap('tab10')
            artists = []
            for i, branch in enumerate(branches):
                if len(branch) < 2:
                    continue
                re_arr = [r.real for r in branch]
                im_arr = [r.imag for r in branch]
                ln, = base_ax.plot(re_arr, im_arr, '-',
                                   color=cmap_rl(i % 10),
                                   lw=max(0.7, lw * 0.7),
                                   label=f"Ветвь {i + 1}"
                                   if i == 0 else None)
                artists.append(ln)
                sc = base_ax.scatter(
                    re_arr, im_arr, s=max(2, ms * 0.2),
                    color=cmap_rl(i % 10), alpha=0.4,
                    edgecolors='none', marker='x',
                    zorder=3)
                artists.append(sc)

            try:
                poles = np.roots(den)
                zeros = np.roots(num) if len(num) > 1 else np.array([])
            except Exception:
                poles = np.array([])
                zeros = np.array([])
            if len(poles) > 0:
                sc_p = base_ax.scatter(
                    [p.real for p in poles],
                    [p.imag for p in poles],
                    s=max(60, ms ** 2 * 3), marker='x',
                    color='red', linewidths=2,
                    zorder=5, label='Полюса')
                artists.append(sc_p)
            if len(zeros) > 0:
                sc_z = base_ax.scatter(
                    [z.real for z in zeros],
                    [z.imag for z in zeros],
                    s=max(60, ms ** 2 * 3), marker='o',
                    facecolors='none', edgecolors='blue',
                    linewidths=2, zorder=5, label='Нули')
                artists.append(sc_z)

            base_ax.axhline(0, color='gray', lw=0.5, zorder=1)
            base_ax.axvline(0, color='gray', lw=0.5, zorder=1)
            base_ax.set_xlabel("Re")
            base_ax.set_ylabel("Im")
            base_ax.set_title("Корневой годограф")
            base_ax.legend(fontsize=8, loc='best')
            try:
                base_ax.set_aspect('equal', adjustable='datalim')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Constellation diagram":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 1:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]

            artists = []
            ideal = base_ax.scatter(
                x_arr, y_arr,
                s=max(60, ms ** 2 * 3), color=c,
                edgecolors='black', linewidths=1.0,
                alpha=0.85, zorder=4,
                label=f"{lbl or 'Созвездие'} ({n} точек)")
            artists.append(ideal)

            z_arr = np.array(data.get('z', []), dtype=float)
            if len(z_arr) >= 2 and len(z_arr) % 2 == 0:
                n_sym = len(z_arr) // 2
                rxs = z_arr[0::2][:n_sym]
                rys = z_arr[1::2][:n_sym]
                rx = base_ax.scatter(
                    rxs, rys,
                    s=max(8, ms * 0.5), color='orange',
                    alpha=0.5, edgecolors='none',
                    zorder=3, label='Принятые')
                artists.append(rx)

            base_ax.axhline(0, color='gray', lw=0.6, zorder=1)
            base_ax.axvline(0, color='gray', lw=0.6, zorder=1)

            if n >= 2:
                try:
                    xs_sorted = np.sort(np.unique(np.abs(x_arr)))
                    ys_sorted = np.sort(np.unique(np.abs(y_arr)))
                    if len(xs_sorted) >= 2 and len(ys_sorted) >= 2:
                        d_min = min(
                            xs_sorted[1] - xs_sorted[0],
                            ys_sorted[1] - ys_sorted[0])
                        for (cx, cy) in zip(x_arr, y_arr):
                            th = np.linspace(0, 2 * np.pi, 60)
                            circ, = base_ax.plot(
                                cx + d_min / 2 * np.cos(th),
                                cy + d_min / 2 * np.sin(th),
                                color='gray', lw=0.4,
                                alpha=0.4, zorder=2)
                            artists.append(circ)
                except Exception:
                    pass

            base_ax.set_xlabel("I (In-phase)")
            base_ax.set_ylabel("Q (Quadrature)")
            base_ax.set_title("Constellation diagram")
            base_ax.legend(fontsize=8, loc='best')
            try:
                base_ax.set_aspect('equal', adjustable='datalim')
            except Exception:
                pass

            data['_extra_artists'] = artists
            artist = ideal

        # ====================================================================
        # ГЕО / МЕТЕО
        # ====================================================================
        elif t == "Choropleth":
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            m, n = Z.shape

            row_labels = data.get('pie_labels') or []
            col_labels = data.get('col_labels') or []

            vmin = float(np.nanmin(Z)) if np.isfinite(Z).any() else 0.0
            vmax = float(np.nanmax(Z)) if np.isfinite(Z).any() else 1.0
            rng = vmax - vmin if vmax > vmin else 1.0
            cmap = plt.get_cmap('YlOrRd')

            artists = []
            for i in range(m):
                for j in range(n):
                    val = Z[i, j]
                    norm = (val - vmin) / rng if np.isfinite(val) else 0.0
                    face = cmap(norm)
                    rect = plt.Rectangle(
                        (j, m - 1 - i), 1, 1,
                        facecolor=face, edgecolor='white',
                        linewidth=1.2, zorder=2)
                    base_ax.add_patch(rect)
                    artists.append(rect)
                    val_txt = base_ax.text(
                        j + 0.5, m - 1 - i + 0.5,
                        f"{val:.3g}", ha='center', va='center',
                        fontsize=8, zorder=3,
                        color='black' if norm < 0.6 else 'white')
                    artists.append(val_txt)

            for i in range(m):
                lbl_ = row_labels[i] if i < len(row_labels) \
                    else f"R{i + 1}"
                t_lbl = base_ax.text(
                    -0.1, m - 0.5 - i, str(lbl_),
                    ha='right', va='center', fontsize=9)
                artists.append(t_lbl)

            for j in range(n):
                lbl_ = col_labels[j] if j < len(col_labels) \
                    else f"C{j + 1}"
                t_lbl = base_ax.text(
                    j + 0.5, -0.1, str(lbl_),
                    ha='center', va='top', fontsize=9)
                artists.append(t_lbl)

            base_ax.set_xlim(-1, n)
            base_ax.set_ylim(-0.5, m)
            base_ax.set_aspect('equal')
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            base_ax.set_title("Choropleth (схема)")

            try:
                sm = mpl.cm.ScalarMappable(
                    cmap=cmap,
                    norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax))
                sm.set_array([])
                cb = base_ax.figure.colorbar(sm, ax=base_ax,
                                             shrink=0.7, pad=0.02)
                artists.append(cb)
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Flow map":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n_nodes = min(len(x_arr), len(y_arr))
            if n_nodes < 2:
                return None
            x_arr = x_arr[:n_nodes]
            y_arr = y_arr[:n_nodes]

            labels = data.get('pie_labels') or \
                     [f"N{i + 1}" for i in range(n_nodes)]
            if len(labels) < n_nodes:
                labels = list(labels) + \
                         [f"N{i + 1}" for i in range(len(labels), n_nodes)]
            labels = labels[:n_nodes]
            node_idx = {str(lbl_): i for i, lbl_ in enumerate(labels)}

            z_raw = data.get('z', []) or []
            edges = []
            for e in z_raw:
                if not isinstance(e, str) or '-' not in e:
                    continue
                a, b = e.split('-', 1)
                a, b = a.strip(), b.strip()
                if a in node_idx and b in node_idx:
                    edges.append((node_idx[a], node_idx[b]))

            artists = []
            from collections import Counter
            deg = Counter()
            for a, b in edges:
                deg[a] += 1
                deg[b] += 1
            deg_max = max(deg.values()) if deg else 1

            for a, b in edges:
                x1, y1 = x_arr[a], y_arr[a]
                x2, y2 = x_arr[b], y_arr[b]
                arr = base_ax.annotate(
                    "",
                    xy=(x2, y2),
                    xytext=(x1, y1),
                    arrowprops=dict(
                        arrowstyle='->',
                        color=c,
                        lw=max(0.8, lw * 0.6),
                        alpha=0.7,
                        shrinkA=10,
                        shrinkB=10,
                        connectionstyle='arc3,rad=0.15'),
                    zorder=2)
                artists.append(arr)

            for i in range(n_nodes):
                size = max(60, ms ** 2 * 3 +
                           (deg.get(i, 0) / deg_max) * ms ** 2 * 6)
                sc = base_ax.scatter(
                    [x_arr[i]], [y_arr[i]],
                    s=size, color=c,
                    edgecolors='black', linewidths=1.0,
                    alpha=0.9, zorder=4)
                artists.append(sc)
                t_lbl = base_ax.text(
                    x_arr[i], y_arr[i], str(labels[i]),
                    ha='center', va='center',
                    color='white', fontsize=9,
                    fontweight='bold', zorder=5)
                artists.append(t_lbl)

            base_ax.set_aspect('equal')
            try:
                base_ax.axis('off')
            except Exception:
                pass
            base_ax.set_title("Flow map")
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Isopleth":
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            row_lens = [len(r) for r in raw if r]
            if not row_lens or len(set(row_lens)) != 1:
                return None
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            if Z.shape[0] < 2 or Z.shape[1] < 2:
                return None
            n_levels = max(3, min(50, int(data.get('bins', 10))))

            cf = base_ax.contourf(Z, levels=n_levels,
                                  cmap='viridis', alpha=0.85)
            cl = base_ax.contour(Z, levels=n_levels,
                                 colors='black', linewidths=0.5,
                                 alpha=0.6)
            try:
                base_ax.clabel(cl, inline=True, fontsize=7,
                               fmt='%.3g')
            except Exception:
                pass

            extra = [cl]
            try:
                cb = base_ax.figure.colorbar(cf, ax=base_ax,
                                             shrink=0.7, pad=0.02)
                extra.append(cb)
            except Exception:
                pass
            base_ax.set_title("Isopleth")

            data['_extra_artists'] = extra
            artist = cf

        elif t == "Cartogram":
            y_arr = np.array(y, dtype=float) if y else np.array([])
            if len(y_arr) < 1:
                return None
            if isinstance(x, list) and x and isinstance(x[0], str):
                labels = [str(v) for v in x]
            elif data.get('pie_labels'):
                labels = [str(v) for v in data['pie_labels']]
            else:
                labels = [f"R{i + 1}" for i in range(len(y_arr))]
            while len(labels) < len(y_arr):
                labels.append(f"R{len(labels) + 1}")
            labels = labels[:len(y_arr)]

            vmax = float(y_arr.max())
            if vmax <= 0:
                vmax = 1.0
            sides = np.sqrt(y_arr / vmax)

            cmap = plt.get_cmap('tab20')
            order = np.argsort(-y_arr)

            artists = []
            placed = []
            x_cur = 0.0
            y_cur = 0.0
            row_h = 0.0
            max_x = 10.0

            for idx in order:
                s = float(sides[idx])
                if x_cur + s > max_x and x_cur > 0:
                    x_cur = 0.0
                    y_cur += row_h + 0.05
                    row_h = 0.0
                x0, y0 = x_cur, y_cur
                rect = plt.Rectangle(
                    (x0, y0), s, s,
                    facecolor=cmap(int(idx) % 20),
                    edgecolor='white', linewidth=1.5,
                    alpha=0.9, zorder=3)
                base_ax.add_patch(rect)
                artists.append(rect)
                if s > 0.25:
                    t_lbl = base_ax.text(
                        x0 + s / 2, y0 + s / 2,
                        f"{labels[idx]}\n{y_arr[idx]:.3g}",
                        ha='center', va='center',
                        fontsize=max(7, int(s * 10)),
                        color='white', fontweight='bold',
                        zorder=4)
                    artists.append(t_lbl)
                placed.append((x0, y0, s))
                x_cur += s + 0.05
                row_h = max(row_h, s)

            if not placed:
                return None
            max_y = max(p[1] + p[2] for p in placed)
            max_x_used = max(p[0] + p[2] for p in placed)
            base_ax.set_xlim(-0.2, max_x_used + 0.2)
            base_ax.set_ylim(-0.2, max_y + 0.2)
            base_ax.set_aspect('equal')
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            try:
                base_ax.axis('off')
            except Exception:
                pass
            base_ax.set_title("Cartogram")
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Dot density map":
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            m, n = Z.shape
            zmax = float(np.nanmax(Z)) if np.isfinite(Z).any() else 1.0
            if zmax <= 0:
                zmax = 1.0

            rng_d = np.random.default_rng(42)
            xs_list = []
            ys_list = []
            max_dots_per_cell = 100

            for i in range(m):
                for j in range(n):
                    val = float(Z[i, j])
                    if not np.isfinite(val) or val <= 0:
                        continue
                    count = int(val / zmax * max_dots_per_cell)
                    if count == 0:
                        continue
                    local_x = rng_d.uniform(0, 1, count) + j
                    local_y = rng_d.uniform(0, 1, count) + (m - 1 - i)
                    xs_list.append(local_x)
                    ys_list.append(local_y)

            for i in range(m):
                for j in range(n):
                    rect = plt.Rectangle(
                        (j, m - 1 - i), 1, 1,
                        facecolor='none', edgecolor='#ddd',
                        linewidth=0.5, zorder=1)
                    base_ax.add_patch(rect)

            if xs_list:
                xs_all = np.concatenate(xs_list)
                ys_all = np.concatenate(ys_list)
                sc = base_ax.scatter(
                    xs_all, ys_all, s=max(1.5, ms * 0.15),
                    color=c, alpha=0.7,
                    edgecolors='none', zorder=3)
                artist = sc
            else:
                artist = None

            base_ax.set_xlim(0, n)
            base_ax.set_ylim(0, m)
            base_ax.set_aspect('equal')
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            base_ax.set_title("Dot density map")
            data['_extra_artists'] = []

        elif t == "Hodograph":
            u_arr = np.array(x, dtype=float) if x else np.array([])
            v_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(u_arr), len(v_arr))
            if n < 2:
                return None
            u_arr = u_arr[:n]
            v_arr = v_arr[:n]

            artists = []
            line, = base_ax.plot(u_arr, v_arr, '-',
                                 color=c, lw=lw, label=lbl,
                                 zorder=3, marker='o',
                                 markersize=max(3, ms * 0.5))
            artists.append(line)

            for i in range(n - 1):
                arr = base_ax.annotate(
                    "",
                    xy=(u_arr[i + 1], v_arr[i + 1]),
                    xytext=(u_arr[i], v_arr[i]),
                    arrowprops=dict(
                        arrowstyle='-|>',
                        color=c, lw=0.8, alpha=0.5),
                    zorder=2)
                artists.append(arr)

            base_ax.axhline(0, color='gray', lw=0.6, zorder=1)
            base_ax.axvline(0, color='gray', lw=0.6, zorder=1)
            center = base_ax.scatter(
                [0], [0], s=max(30, ms ** 2 * 2),
                color='black', zorder=5, label='Штиль')
            artists.append(center)

            max_r = max(np.abs(u_arr).max(), np.abs(v_arr).max())
            if max_r > 0:
                step = max(1.0, round(max_r / 4))
                for r in np.arange(step, max_r * 1.2, step):
                    th = np.linspace(0, 2 * np.pi, 100)
                    ln, = base_ax.plot(
                        r * np.cos(th), r * np.sin(th),
                        color='#ddd', lw=0.4, zorder=0)
                    artists.append(ln)
                    t_lbl = base_ax.text(
                        r, 0.05 * max_r, f"{r:g}",
                        ha='center', va='bottom',
                        fontsize=7, color='gray')
                    artists.append(t_lbl)

            base_ax.set_xlabel("U (м/с)")
            base_ax.set_ylabel("V (м/с)")
            base_ax.set_title("Ходограф скорости")
            try:
                base_ax.set_aspect('equal', adjustable='datalim')
            except Exception:
                pass
            base_ax.legend(fontsize=8, loc='best')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Роза ветров":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 1:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]

            n_bins = max(4, min(72, int(data.get('bins', 16))))
            sector_width = 360.0 / n_bins
            sectors = np.zeros(n_bins)
            for xi, yi in zip(x_arr, y_arr):
                ang = xi % 360
                idx = int(ang // sector_width) % n_bins
                sectors[idx] += yi

            theta = np.deg2rad(
                (np.arange(n_bins) + 0.5) * sector_width)
            bar_width = np.deg2rad(sector_width) * 0.9

            artists = []
            if getattr(base_ax, 'name', '') == 'polar':
                bars = base_ax.bar(
                    theta, sectors, width=bar_width,
                    color=c, alpha=0.85,
                    edgecolor='white', linewidth=1.0,
                    label=lbl, zorder=3)
                artists.append(bars)
                try:
                    base_ax.set_theta_zero_location('N')
                    base_ax.set_theta_direction(-1)
                except Exception:
                    pass
                try:
                    dir_labels = ['С', 'СВ', 'В', 'ЮВ',
                                  'Ю', 'ЮЗ', 'З', 'СЗ']
                    dir_angles = np.deg2rad([0, 45, 90, 135,
                                             180, 225, 270, 315])
                    base_ax.set_thetagrids(np.rad2deg(dir_angles),
                                           dir_labels)
                except Exception:
                    pass
                base_ax.set_title("Роза ветров")
                artist = bars
            else:
                from matplotlib.patches import Polygon
                for i in range(n_bins):
                    a = theta[i]
                    r = sectors[i]
                    if r <= 0:
                        continue
                    th_range = np.linspace(
                        a - bar_width / 2, a + bar_width / 2, 20)
                    pts = [(0, 0)] + \
                          [(r * np.sin(t), r * np.cos(t))
                           for t in th_range]
                    poly = Polygon(pts, closed=True,
                                   facecolor=c, alpha=0.85,
                                   edgecolor='white',
                                   linewidth=1.0, zorder=3)
                    base_ax.add_patch(poly)
                    artists.append(poly)
                base_ax.set_aspect('equal')
                base_ax.set_title("Роза ветров")
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Skew-T log-P":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(data.get('z', []), dtype=float)
            n = min(len(x_arr), len(y_arr), len(z_arr))
            if n < 2:
                return None
            pres = x_arr[:n]
            temp = y_arr[:n]
            dewp = z_arr[:n]

            mask = (pres > 0)
            pres = pres[mask]
            temp = temp[mask]
            dewp = dewp[mask]
            if len(pres) < 2:
                return None

            order = np.argsort(-pres)
            pres = pres[order]
            temp = temp[order]
            dewp = dewp[order]

            p_min = max(100.0, pres.min())
            p_max = min(1050.0, pres.max())
            t_min = min(temp.min(), dewp.min()) - 10
            t_max = max(temp.max(), dewp.max()) + 10

            artists = []
            skew = 40.0
            p_arr = np.logspace(np.log10(p_min), np.log10(p_max), 60)
            for T0 in range(-100, 51, 10):
                T_iso = T0 + skew * np.log10(1000.0 / p_arr)
                ln, = base_ax.plot(T_iso, p_arr, '-',
                                   color='#ccc', lw=0.5,
                                   zorder=1)
                artists.append(ln)

            for theta in range(-40, 121, 20):
                T_dry = (theta + 273.15) * \
                        (p_arr / 1000.0) ** 0.286 - 273.15
                ln, = base_ax.plot(T_dry + skew *
                                   np.log10(1000.0 / p_arr),
                                   p_arr, '-',
                                   color='#f5c26b', lw=0.5,
                                   alpha=0.6, zorder=1)
                artists.append(ln)

            T_skewed = temp + skew * np.log10(1000.0 / pres)
            t_line, = base_ax.plot(T_skewed, pres, 'o-',
                                   color='red', lw=2.0,
                                   markersize=4, label='T')
            artists.append(t_line)

            Td_skewed = dewp + skew * np.log10(1000.0 / pres)
            td_line, = base_ax.plot(Td_skewed, pres, 's--',
                                    color='blue', lw=1.8,
                                    markersize=3, label='Td')
            artists.append(td_line)

            base_ax.set_yscale('log')
            base_ax.set_ylim(p_max, p_min)
            base_ax.set_xlim(t_min, t_max + 30)
            base_ax.set_xlabel("Температура (°C)")
            base_ax.set_ylabel("Давление (гПа)")
            base_ax.set_title("Skew-T log-P")
            base_ax.legend(fontsize=9, loc='upper right')
            base_ax.grid(True, which='major',
                         color='#eee', lw=0.5)

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Thermodynamic diagram":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(data.get('z', []), dtype=float)
            n = min(len(x_arr), len(y_arr), len(z_arr))
            if n < 2:
                return None
            pres = x_arr[:n]
            temp = y_arr[:n]
            dewp = z_arr[:n]

            mask = (pres > 0)
            pres = pres[mask]
            temp = temp[mask]
            dewp = dewp[mask]
            if len(pres) < 2:
                return None

            order = np.argsort(-pres)
            pres = pres[order]
            temp = temp[order]
            dewp = dewp[order]

            p_min = max(100.0, pres.min())
            p_max = min(1050.0, pres.max())

            artists = []
            for p0 in [1000, 925, 850, 700, 500, 400, 300, 250,
                       200, 150, 100]:
                if p_min <= p0 <= p_max:
                    ln, = base_ax.axhline(
                        p0, color='#ccc', lw=0.5, zorder=1)
                    artists.append(ln)
            for T0 in range(-100, 51, 10):
                ln, = base_ax.axvline(
                    T0, color='#eee', lw=0.4, zorder=0)
                artists.append(ln)

            t_line, = base_ax.plot(temp, pres, 'o-',
                                   color='red', lw=2.0,
                                   markersize=5, label='T')
            artists.append(t_line)
            td_line, = base_ax.plot(dewp, pres, 's--',
                                    color='blue', lw=1.8,
                                    markersize=4, label='Td')
            artists.append(td_line)

            try:
                base_ax.fill_betweenx(
                    pres, dewp, temp,
                    color='purple', alpha=0.15,
                    label='Область')
            except Exception:
                pass

            base_ax.set_yscale('log')
            base_ax.set_ylim(p_max, p_min)
            base_ax.set_xlabel("Температура (°C)")
            base_ax.set_ylabel("Давление (гПа)")
            base_ax.set_title("Emagram")
            base_ax.legend(fontsize=9, loc='best')
            base_ax.grid(True, which='major',
                         color='#eee', lw=0.5, alpha=0.5)

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        # ====================================================================
        # ГЕОМЕТРИЯ
        # ====================================================================
        elif t == "Диаграмма Вороного":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]
            points = np.column_stack([x_arr, y_arr])

            try:
                from scipy.spatial import Voronoi
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            try:
                vor = Voronoi(points)
            except Exception as e:
                base_ax.text(0.5, 0.5, f'Voronoi error: {e}',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None

            from matplotlib.collections import LineCollection
            artists = []
            segments = []
            for (p1, p2) in vor.ridge_vertices:
                if p1 >= 0 and p2 >= 0:
                    segments.append([vor.vertices[p1],
                                     vor.vertices[p2]])
            if segments:
                lc = LineCollection(segments, colors='black',
                                    linewidths=max(0.6, lw * 0.5),
                                    alpha=0.7, zorder=1)
                base_ax.add_collection(lc)
                artists.append(lc)

            sc = base_ax.scatter(
                x_arr, y_arr, s=max(30, ms ** 2 * 2),
                color=c, edgecolors='white',
                linewidths=1.0, zorder=3, label=lbl)
            artists.append(sc)

            xmin = min(v[0] for v in vor.vertices) - 1
            xmax = max(v[0] for v in vor.vertices) + 1
            ymin = min(v[1] for v in vor.vertices) - 1
            ymax = max(v[1] for v in vor.vertices) + 1
            base_ax.set_xlim(xmin, xmax)
            base_ax.set_ylim(ymin, ymax)
            base_ax.set_title("Диаграмма Вороного")

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Выпуклая оболочка":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 3:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]
            points = np.column_stack([x_arr, y_arr])

            try:
                from scipy.spatial import ConvexHull
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            try:
                hull = ConvexHull(points)
            except Exception as e:
                base_ax.text(0.5, 0.5, f'ConvexHull error: {e}',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None

            hull_pts = points[hull.vertices]
            hull_pts = np.vstack([hull_pts, hull_pts[0]])

            artists = []
            sc = base_ax.scatter(
                x_arr, y_arr, s=max(20, ms ** 2),
                color=c, alpha=0.6,
                edgecolors='none', zorder=2,
                label=f"{lbl} (n={n})")
            artists.append(sc)

            line, = base_ax.plot(hull_pts[:, 0], hull_pts[:, 1],
                                 '-', color='red',
                                 lw=max(1.0, lw * 0.8),
                                 zorder=3,
                                 label=f"Оболочка "
                                       f"({len(hull.vertices)} вершин)")
            artists.append(line)

            fill_area = base_ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                                     color='red', alpha=0.1, zorder=1)
            artists.append(fill_area)

            sc_hull = base_ax.scatter(
                hull_pts[:-1, 0], hull_pts[:-1, 1],
                s=max(50, ms ** 2 * 2.5), color='red',
                edgecolors='black', linewidths=0.8,
                zorder=4)
            artists.append(sc_hull)

            base_ax.set_title("Выпуклая оболочка")
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Alpha shape":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 3:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]
            points = np.column_stack([x_arr, y_arr])

            bins = max(1, int(data.get('bins', 5)))
            alpha = 1.0 / (bins / 2.0)
            alpha = max(0.05, min(10.0, alpha))

            try:
                from scipy.spatial import Delaunay
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            try:
                tri = Delaunay(points)
            except Exception as e:
                base_ax.text(0.5, 0.5, f'Delaunay error: {e}',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None

            def circumradius(a, b, c_):
                ax_, ay = a
                bx, by = b
                cx, cy = c_
                d = 2 * (ax_ * (by - cy) + bx * (cy - ay) +
                         cx * (ay - by))
                if abs(d) < 1e-12:
                    return float('inf')
                ux = ((ax_ ** 2 + ay ** 2) * (by - cy) +
                      (bx ** 2 + by ** 2) * (cy - ay) +
                      (cx ** 2 + cy ** 2) * (ay - by)) / d
                uy = ((ax_ ** 2 + ay ** 2) * (cx - bx) +
                      (bx ** 2 + by ** 2) * (ax_ - cx) +
                      (cx ** 2 + cy ** 2) * (bx - ax_)) / d
                r = np.hypot(ux - ax_, uy - ay)
                return r

            artists = []
            kept_edges = []
            for simplex in tri.simplices:
                a = points[simplex[0]]
                b = points[simplex[1]]
                c_ = points[simplex[2]]
                r = circumradius(a, b, c_)
                if r <= 1.0 / alpha:
                    kept_edges.append([a, b])
                    kept_edges.append([b, c_])
                    kept_edges.append([c_, a])

            sc = base_ax.scatter(
                x_arr, y_arr, s=max(15, ms ** 2 * 0.8),
                color=c, alpha=0.85,
                edgecolors='white', linewidths=0.5,
                zorder=3, label=f"{lbl} (α={alpha:.2f})")
            artists.append(sc)

            if kept_edges:
                from matplotlib.collections import LineCollection
                lc = LineCollection(kept_edges,
                                    colors='darkred',
                                    linewidths=max(0.6, lw * 0.5),
                                    alpha=0.8, zorder=2)
                base_ax.add_collection(lc)
                artists.append(lc)

            base_ax.set_title(f"Alpha shape (α = {alpha:.3f})")
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        # ====================================================================
        # ML / СТАТИСТИКА
        # ====================================================================
        elif t == "Volcano plot":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 1:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]

            fc_thr = 1.0
            p_thr = 1.3

            sig_up = (x_arr > fc_thr) & (y_arr > p_thr)
            sig_down = (x_arr < -fc_thr) & (y_arr > p_thr)
            nsig = ~(sig_up | sig_down)

            artists = []
            if nsig.any():
                s1 = base_ax.scatter(
                    x_arr[nsig], y_arr[nsig],
                    s=max(15, ms ** 2 * 0.7),
                    color='gray', alpha=0.5,
                    edgecolors='none', zorder=2,
                    label=f"Незначимые ({nsig.sum()})")
                artists.append(s1)
            if sig_up.any():
                s2 = base_ax.scatter(
                    x_arr[sig_up], y_arr[sig_up],
                    s=max(20, ms ** 2),
                    color='red', alpha=0.7,
                    edgecolors='black', linewidths=0.4,
                    zorder=3,
                    label=f"↑ ({sig_up.sum()})")
                artists.append(s2)
            if sig_down.any():
                s3 = base_ax.scatter(
                    x_arr[sig_down], y_arr[sig_down],
                    s=max(20, ms ** 2),
                    color='blue', alpha=0.7,
                    edgecolors='black', linewidths=0.4,
                    zorder=3,
                    label=f"↓ ({sig_down.sum()})")
                artists.append(s3)

            l1 = base_ax.axvline(fc_thr, color='#333', lw=0.8,
                                 ls='--', alpha=0.6, zorder=1)
            l2 = base_ax.axvline(-fc_thr, color='#333', lw=0.8,
                                 ls='--', alpha=0.6, zorder=1)
            l3 = base_ax.axhline(p_thr, color='#333', lw=0.8,
                                 ls='--', alpha=0.6, zorder=1)
            artists.extend([l1, l2, l3])

            base_ax.set_xlabel("log2(Fold Change)")
            base_ax.set_ylabel("-log10(p-value)")
            base_ax.set_title("Volcano plot")
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "ROC curve":
            y_arr = np.array(y, dtype=float) if y else np.array([])
            z_arr = np.array(data.get('z', []), dtype=float)
            n = min(len(y_arr), len(z_arr))
            if n < 4:
                return None
            y_true = y_arr[:n]
            y_score = z_arr[:n]

            classes = np.unique(y_true)
            if len(classes) != 2:
                base_ax.text(0.5, 0.5,
                             'ROC требует ровно 2 класса',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            pos_label = classes[-1]

            order = np.argsort(-y_score)
            y_true_sorted = y_true[order]

            P = int((y_true == pos_label).sum())
            N = int(n - P)
            if P == 0 or N == 0:
                return None

            tp = np.cumsum(y_true_sorted == pos_label)
            fp = np.cumsum(y_true_sorted != pos_label)
            tpr = tp / P
            fpr = fp / N

            fpr = np.concatenate([[0.0], fpr])
            tpr = np.concatenate([[0.0], tpr])

            auc = float(np.trapz(tpr, fpr))

            artists = []
            diag, = base_ax.plot([0, 1], [0, 1], '--',
                                 color='gray', lw=1.0,
                                 alpha=0.7, zorder=1,
                                 label='Случайный')
            artists.append(diag)
            roc_line, = base_ax.plot(
                fpr, tpr, '-', color=c,
                lw=max(1.5, lw), zorder=3,
                label=f"ROC (AUC = {auc:.4f})")
            artists.append(roc_line)
            fill_area = base_ax.fill_between(
                fpr, 0, tpr,
                color=c, alpha=0.15, zorder=1)
            artists.append(fill_area)

            base_ax.set_xlim(0, 1)
            base_ax.set_ylim(0, 1.05)
            base_ax.set_xlabel("False Positive Rate")
            base_ax.set_ylabel("True Positive Rate")
            base_ax.set_title(f"ROC-кривая (AUC = {auc:.4f})")
            try:
                base_ax.legend(fontsize=9, loc='lower right')
            except Exception:
                pass
            base_ax.set_aspect('equal', adjustable='box')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Manhattan plot":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]

            z_raw = data.get('z', [])
            if z_raw and len(z_raw) >= n:
                chrom = np.array(z_raw[:n], dtype=float)
            else:
                chrom = np.ones(n)

            chromosomes = np.unique(chrom)
            colors_pair = ['#1f77b4', '#ff7f0e', '#2ca02c',
                           '#d62728', '#9467bd', '#8c564b',
                           '#e377c2', '#7f7f7f', '#bcbd22',
                           '#17becf']

            artists = []
            offset = 0.0
            x_ticks = []
            x_labels = []
            all_x = []
            all_y = []
            all_c = []

            for i, c_ in enumerate(chromosomes):
                mask = chrom == c_
                xs = x_arr[mask]
                ys = y_arr[mask]
                span = float(xs.max() - xs.min()) if len(xs) > 1 else 1.0
                gap = span * 0.1 if span > 0 else 0.1
                xs_shifted = xs - xs.min() + offset
                all_x.append(xs_shifted)
                all_y.append(ys)
                color_i = colors_pair[i % len(colors_pair)]
                all_c.append(np.array([color_i] * len(xs_shifted)))
                x_ticks.append(offset + span / 2)
                x_labels.append(f"Chr {int(c_)}")
                offset += span + gap

            if not all_x:
                return None
            xs_all = np.concatenate(all_x)
            ys_all = np.concatenate(all_y)
            cs_all = np.concatenate(all_c)

            sc = base_ax.scatter(
                xs_all, ys_all, s=max(4, ms ** 2 * 0.4),
                c=cs_all, alpha=0.8,
                edgecolors='none', zorder=3)
            artists.append(sc)

            if ys_all.size > 0:
                threshold = max(5.0, float(np.percentile(ys_all, 95)))
                sig_line = base_ax.axhline(
                    threshold, color='red', lw=1.0,
                    ls='--', alpha=0.7, zorder=2,
                    label=f"Порог ({threshold:.2f})")
                artists.append(sig_line)

            base_ax.set_xticks(x_ticks)
            try:
                base_ax.set_xticklabels(x_labels,
                                        rotation=45, ha='right',
                                        fontsize=8)
            except Exception:
                pass
            base_ax.set_ylabel("-log10(p-value)")
            base_ax.set_title("Manhattan plot")
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "MA plot":
            x_arr = np.array(x, dtype=float) if x else np.array([])
            y_arr = np.array(y, dtype=float) if y else np.array([])
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]

            sc = base_ax.scatter(
                x_arr, y_arr, s=max(8, ms ** 2 * 0.5),
                color=c, alpha=0.6,
                edgecolors='none', zorder=3, label=lbl)
            artists = [sc]

            zero, = base_ax.plot([x_arr.min(), x_arr.max()],
                                 [0, 0], '--',
                                 color='red', lw=1.2,
                                 alpha=0.7, zorder=2,
                                 label='M = 0')
            artists.append(zero)

            if data.get('fill', False):
                base_ax.fill_between(
                    [x_arr.min(), x_arr.max()],
                    [-1, -1], [1, 1],
                    color='#ccc', alpha=0.15,
                    zorder=1)

            base_ax.set_xlabel("A = log2(mean)")
            base_ax.set_ylabel("M = log2(ratio)")
            base_ax.set_title("MA plot")
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            data['_extra_artists'] = artists[1:]
            artist = artists[0]

        elif t == "Recurrence plot":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 4:
                return None
            eps_factor = 0.1
            m = max(1, min(3, int(data.get('bins', 1))))
            if m > 1:
                n_v = len(y_arr) - m + 1
                if n_v < 4:
                    m = 1
            if m == 1:
                eps = float(np.std(y_arr)) * eps_factor
                if eps <= 0:
                    eps = 1e-9
                D = np.abs(y_arr[:, None] - y_arr[None, :])
                R = (D < eps).astype(float)
            else:
                n = len(y_arr)
                V = np.array([y_arr[i:i + m]
                              for i in range(n - m + 1)])
                eps = np.std(y_arr) * eps_factor * np.sqrt(m)
                if eps <= 0:
                    eps = 1e-9
                D = np.sqrt(
                    ((V[:, None, :] - V[None, :, :]) ** 2).sum(axis=-1))
                R = (D < eps).astype(float)

            artist = base_ax.imshow(
                R, cmap='binary', aspect='auto',
                interpolation='nearest', origin='lower')
            base_ax.set_xlabel("i")
            base_ax.set_ylabel("j")
            base_ax.set_title(f"Recurrence m={m}")

        elif t == "Cobweb plot":
            if isinstance(x, list) and x and isinstance(x[0], str):
                formula = str(x[0])
            else:
                formula = data.get('z') or "r * x * (1 - x)"
            if not isinstance(formula, str) or not formula.strip():
                formula = "r * x * (1 - x)"
            formula = formula.strip()

            y_arr = np.array(y, dtype=float) if y else np.array([0.2, 20.0])
            x0 = float(y_arr[0]) if len(y_arr) >= 1 else 0.2
            N = int(y_arr[1]) if len(y_arr) >= 2 else 20
            N = max(3, min(200, N))

            xmin = min(0.0, x0)
            xmax = max(1.0, x0)
            xs = np.linspace(xmin, xmax, 300)

            sd = {
                'x': xs,
                'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
                'exp': np.exp, 'log': np.log, 'sqrt': np.sqrt,
                'abs': np.abs, 'pi': np.pi, 'e': np.e,
                'power': np.power,
            }
            try:
                ys_curve = eval(formula, {"__builtins__": {}}, sd)
                ys_curve = np.broadcast_to(ys_curve, xs.shape)
            except Exception as e:
                base_ax.text(0.5, 0.5, f"Formula error:\n{e}",
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None

            artists = []
            diag, = base_ax.plot([xmin, xmax], [xmin, xmax],
                                 color='gray', lw=0.8, ls='--',
                                 label='y = x', zorder=1)
            artists.append(diag)
            curve, = base_ax.plot(xs, ys_curve, color=c, lw=lw,
                                  label=f"y = {formula}", zorder=2)
            artists.append(curve)

            xv = x0
            sd_scalar = dict(sd)
            for i in range(N):
                sd_scalar['x'] = xv
                try:
                    yv = float(eval(formula,
                                    {"__builtins__": {}},
                                    sd_scalar))
                except Exception:
                    break
                ln1, = base_ax.plot([xv, xv], [xv, yv],
                                    color='red', lw=0.6, alpha=0.6,
                                    zorder=3)
                ln2, = base_ax.plot([xv, yv], [yv, yv],
                                    color='red', lw=0.6, alpha=0.6,
                                    zorder=3)
                artists.extend([ln1, ln2])
                xv = yv
                if xv < xmin - 1 or xv > xmax + 1 or not np.isfinite(xv):
                    break

            base_ax.set_xlabel("x[n]")
            base_ax.set_ylabel("x[n+1]")
            base_ax.legend(fontsize=8, loc='best')

            data['_extra_artists'] = artists
            artist = curve

        elif t == "Poincaré plot":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 4:
                return None
            tau = max(1, int(data.get('bins', 1)))
            x1 = y_arr[:-tau]
            y1 = y_arr[tau:]
            n = len(x1)
            if n < 2:
                return None
            main = base_ax.scatter(
                x1, y1, s=max(10, ms ** 2 * 0.5), color=c,
                alpha=0.6, edgecolors='none',
                label=lbl, zorder=3)
            lo = min(x1.min(), y1.min())
            hi = max(x1.max(), y1.max())
            diag, = base_ax.plot([lo, hi], [lo, hi], '--',
                                 color='gray', lw=1.0, alpha=0.7)
            base_ax.set_xlabel("Y(t)")
            base_ax.set_ylabel(f"Y(t + {tau})")
            data['_extra_artists'] = [diag]
            artist = main

        elif t == "Phase portrait":
            y_arr = np.array(y, dtype=float)
            if len(y_arr) < 3:
                return None
            x_arr = (np.array(x, dtype=float)
                     if x and len(x) == len(y_arr)
                     else np.arange(len(y_arr)))
            try:
                dy = np.gradient(y_arr, x_arr)
            except Exception:
                dy = np.gradient(y_arr)
            line, = base_ax.plot(y_arr, dy, '-',
                                 color=c, lw=lw, alpha=0.7,
                                 label=lbl)
            start = base_ax.scatter(
                [y_arr[0]], [dy[0]],
                s=max(40, ms ** 2 * 2), color='green',
                edgecolors='black', zorder=5, label='Начало')
            end = base_ax.scatter(
                [y_arr[-1]], [dy[-1]],
                s=max(40, ms ** 2 * 2), color='red',
                edgecolors='black', zorder=5, label='Конец')

            formula = data.get('z')
            if isinstance(formula, str) and formula.strip():
                try:
                    yg = np.linspace(y_arr.min(), y_arr.max(), 20)
                    dg = np.linspace(dy.min(), dy.max(), 20)
                    Yg, Dg = np.meshgrid(yg, dg)
                    sd_p = {
                        'y': Yg, 'dy': Dg, 'x': Yg,
                        'sin': np.sin, 'cos': np.cos,
                        'exp': np.exp, 'sqrt': np.sqrt,
                        'abs': np.abs, 'pi': np.pi,
                    }
                    dY = eval(formula, {"__builtins__": {}}, sd_p)
                    base_ax.streamplot(
                        yg, dg, Yg * 0 + dY, Dg * 0 - Dg,
                        color='#ccc', density=0.8, arrowsize=0.8,
                        linewidth=0.5)
                except Exception:
                    pass

            base_ax.set_xlabel("Y")
            base_ax.set_ylabel("dY/dX")
            base_ax.legend(fontsize=8, loc='best')
            data['_extra_artists'] = [start, end]
            artist = line

        # ====================================================================
        # СПЕЦИАЛЬНЫЕ / ЭКЗОТИКА
        # ====================================================================
        elif t == "Вафельная диаграмма":
            vals = np.array(y, dtype=float)
            if len(vals) == 0:
                return None
            total = vals.sum()
            if total <= 0:
                return None
            rows = max(3, min(30, int(data.get('bins', 10))))
            cols = rows
            n_cells = rows * cols

            fracs = vals / total
            counts = np.floor(fracs * n_cells).astype(int)
            remainder = n_cells - counts.sum()
            if remainder > 0:
                order = np.argsort(-(fracs * n_cells - counts))
                for k in range(remainder):
                    counts[order[k % len(order)]] += 1

            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(vals):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(vals))]

            artists = []
            idx = 0
            for cnt, col in zip(counts, pc):
                for _ in range(int(cnt)):
                    if idx >= n_cells:
                        break
                    r = idx // cols
                    c_ = idx % cols
                    rect = plt.Rectangle(
                        (c_ + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
                        facecolor=col, edgecolor='white',
                        linewidth=1, zorder=3)
                    target_ax.add_patch(rect)
                    artists.append(rect)
                    idx += 1

            while idx < n_cells:
                r = idx // cols
                c_ = idx % cols
                rect = plt.Rectangle(
                    (c_ + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
                    facecolor='#eeeeee', edgecolor='white',
                    linewidth=1, zorder=2)
                target_ax.add_patch(rect)
                artists.append(rect)
                idx += 1

            target_ax.set_xlim(-0.5, cols + 0.5)
            target_ax.set_ylim(-0.5, rows + 0.5)
            target_ax.set_aspect('equal')
            target_ax.set_xticks([])
            target_ax.set_yticks([])

            labels = data.get('pie_labels') or []
            if labels:
                for i, (lbl_, col) in enumerate(zip(labels[:len(vals)], pc)):
                    target_ax.text(
                        cols + 0.7, rows - i - 1 + 0.5, f"{lbl_}",
                        ha='left', va='center', fontsize=9, color=col)

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Сосулька (icicle)":
            vals = np.array(y, dtype=float)
            if len(vals) == 0:
                return None
            labels = data.get('pie_labels') or [str(i + 1)
                                                for i in range(len(vals))]
            while len(labels) < len(vals):
                labels.append(str(len(labels) + 1))
            parents = data.get('treemap_parents') or [''] * len(vals)
            while len(parents) < len(vals):
                parents.append('')

            label_idx = {lbl_: i for i, lbl_ in enumerate(labels)}
            depth = [0] * len(vals)
            for _ in range(len(vals)):
                changed = False
                for i, p in enumerate(parents):
                    if p and p in label_idx:
                        new_d = depth[label_idx[p]] + 1
                        if depth[i] < new_d:
                            depth[i] = new_d
                            changed = True
                if not changed:
                    break

            child_map = {}
            roots = []
            for i, p in enumerate(parents):
                if p and p in label_idx:
                    child_map.setdefault(label_idx[p], []).append(i)
                else:
                    roots.append(i)

            def subtree_sum(i):
                s = vals[i]
                for ch in child_map.get(i, []):
                    s += subtree_sum(ch)
                return s

            total = sum(subtree_sum(r) for r in roots) or 1.0

            pos = {}

            def assign(i, x_start, width):
                pos[i] = (x_start, width)
                cur = x_start
                for ch in child_map.get(i, []):
                    w_ch = width * vals[ch] / max(subtree_sum(i), 1e-12)
                    assign(ch, cur, w_ch)
                    cur += w_ch

            cur_x = 0.0
            for r in roots:
                w_r = (subtree_sum(r) / total) if total else 0
                assign(r, cur_x, w_r)
                cur_x += w_r

            max_depth = max(depth) if depth else 0
            cmap = plt.get_cmap('tab20')
            artists = []
            for i in range(len(vals)):
                if i not in pos:
                    continue
                x0, w = pos[i]
                d = depth[i]
                col = cmap((i % 10) + (d % 2) * 10)
                rect = plt.Rectangle(
                    (x0, -d - 1), w * 0.98, 0.94,
                    facecolor=col, edgecolor='white',
                    linewidth=1.2, zorder=3)
                target_ax.add_patch(rect)
                artists.append(rect)
                if w > 0.02:
                    txt = target_ax.text(
                        x0 + w / 2, -d - 0.5,
                        f"{labels[i]}\n{vals[i]:g}",
                        ha='center', va='center',
                        fontsize=max(7, min(11, int(w * 20))),
                        color='black', zorder=4)
                    artists.append(txt)

            target_ax.set_xlim(-0.05, 1.05)
            target_ax.set_ylim(-max_depth - 1.2, 0.2)
            target_ax.set_xticks([])
            target_ax.set_yticks([])
            target_ax.axis('off')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Диаграмма Аргана":
            re_arr = np.array(x, dtype=float)
            im_arr = np.array(y, dtype=float)
            n = min(len(re_arr), len(im_arr))
            if n < 1:
                return None
            re_arr, im_arr = re_arr[:n], im_arr[:n]
            z_arr = data.get('z') or []

            artists = []
            th = np.linspace(0, 2 * np.pi, 200)
            circle, = target_ax.plot(np.cos(th), np.sin(th),
                                     color='#bbb', lw=0.8,
                                     ls='--', zorder=1)
            artists.append(circle)
            target_ax.axhline(0, color='#999', lw=0.6, zorder=1)
            target_ax.axvline(0, color='#999', lw=0.6, zorder=1)

            main = target_ax.scatter(
                re_arr, im_arr, s=max(20, ms ** 2 * 2),
                color=c, edgecolors='white', linewidths=0.8,
                zorder=4, label=lbl)

            if n > 1:
                trace, = target_ax.plot(
                    re_arr, im_arr, '-', color=c,
                    lw=max(0.6, lw * 0.6), alpha=0.5, zorder=3)
                artists.append(trace)

            for i in range(n):
                arr = target_ax.annotate(
                    "", xy=(re_arr[i], im_arr[i]), xytext=(0, 0),
                    arrowprops=dict(arrowstyle='->', color=c,
                                    lw=0.8, alpha=0.5),
                    zorder=2)
                artists.append(arr)
                if i < len(z_arr):
                    txt = target_ax.text(
                        re_arr[i] * 1.05, im_arr[i] * 1.05,
                        str(z_arr[i]), fontsize=8, color=c)
                    artists.append(txt)

            target_ax.set_xlabel("Re")
            target_ax.set_ylabel("Im")
            target_ax.set_aspect('equal', adjustable='datalim')
            target_ax.legend(fontsize=8, loc='best')

            artist = main
            data['_extra_artists'] = artists

        elif t == "Диаграмма Тейлора":
            if getattr(target_ax, 'name', '') != 'polar':
                return None
            raw = data.get('heatmap_data') or []
            if len(raw) < 2:
                return None
            stds = np.array(raw[0], dtype=float)
            corrs = np.array(raw[1], dtype=float)
            n = min(len(stds), len(corrs))
            if n < 1:
                return None
            stds, corrs = stds[:n], corrs[:n]
            corrs = np.clip(corrs, -1.0, 1.0)

            labels = data.get('pie_labels') or [f"M{i + 1}" for i in range(n)]
            while len(labels) < n:
                labels.append(f"M{len(labels) + 1}")

            theta = np.arccos(corrs)
            r = stds

            artists = []
            ref_std = float(np.max(stds)) if len(stds) else 1.0
            if data.get('x') and len(data['x']) >= 1:
                try:
                    ref_std = float(data['x'][0])
                except Exception:
                    pass

            cmap = plt.get_cmap('tab10')
            for i in range(n):
                sc = target_ax.scatter(
                    [theta[i]], [r[i]],
                    s=max(60, ms ** 2 * 3),
                    color=cmap(i % 10), edgecolors='black',
                    linewidths=0.8, zorder=5, label=str(labels[i]))
                artists.append(sc)
                txt = target_ax.text(
                    theta[i], r[i] * 1.05, str(labels[i]),
                    ha='center', va='bottom', fontsize=8)
                artists.append(txt)

            ref = target_ax.scatter(
                [0], [ref_std], s=max(80, ms ** 2 * 4),
                color='black', marker='*', zorder=6,
                label=f"Reference ({ref_std:.2g})")
            artists.append(ref)

            target_ax.set_thetalim(0, np.pi)
            target_ax.set_theta_zero_location('E')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Горизонтальная столбчатая":
            artist = target_ax.barh(x, y, label=lbl, color=c,
                                    edgecolor='white')
            if yerr:
                try:
                    eb = target_ax.errorbar(
                        y, x, xerr=yerr, fmt='none',
                        ecolor=c, capsize=3)
                    data['_extra_artists'] = [eb]
                except Exception:
                    pass

        elif t == "Горизонтальная линия":
            artist, = target_ax.plot(y, x, label=lbl, color=c, lw=lw,
                                     ls=ls, marker=marker, markersize=ms)
            if fill:
                try:
                    fb = target_ax.fill_betweenx(
                        x, 0, y, alpha=0.3, color=c)
                    data['_extra_artists'] = [fb]
                except Exception:
                    pass

        elif t == "Pie of pie":
            vals = np.array(y, dtype=float)
            if len(vals) < 2:
                return None
            labels = data.get('pie_labels') or [f"C{i + 1}"
                                                for i in range(len(vals))]
            while len(labels) < len(vals):
                labels.append(f"C{len(labels) + 1}")
            labels = labels[:len(vals)]

            n_out = max(1, min(len(vals) - 1,
                               int(data.get('bins', 3))))
            small = vals[:n_out]
            small_labels = labels[:n_out]
            big = vals[n_out:]
            big_labels = labels[n_out:]

            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(vals):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(vals))]
            small_colors = pc[:n_out]
            big_colors = pc[n_out:]

            pie_vals = list(small) + [big.sum()]
            pie_labels_ = list(small_labels) + ['...']
            pie_colors_list = list(small_colors) + ['#cccccc']

            artists = []
            w1, t1, a1 = target_ax.pie(
                pie_vals, labels=pie_labels_, colors=pie_colors_list,
                autopct='%1.1f%%', radius=0.5, center=(0.5, 0.5),
                wedgeprops=dict(edgecolor='white', linewidth=1.0))
            for t_ in t1:
                t_.set_fontsize(8)
            for t_ in a1:
                t_.set_fontsize(7)
            artists.extend(w1)

            w2, t2, a2 = target_ax.pie(
                big, labels=big_labels, colors=big_colors,
                autopct='%1.1f%%', radius=0.35, center=(-0.6, 0.5),
                wedgeprops=dict(edgecolor='white', linewidth=1.0))
            for t_ in t2:
                t_.set_fontsize(8)
            for t_ in a2:
                t_.set_fontsize(7)
            artists.extend(w2)

            try:
                conn1, = target_ax.plot(
                    [-0.25, 0.05],
                    [0.65, 0.5 + pie_vals[-1] / sum(pie_vals) * 0.5],
                    color='#999', lw=0.8, zorder=1)
                conn2, = target_ax.plot(
                    [-0.25, 0.05],
                    [0.35, 0.5 - pie_vals[-1] / sum(pie_vals) * 0.5],
                    color='#999', lw=0.8, zorder=1)
                artists.extend([conn1, conn2])
            except Exception:
                pass

            target_ax.set_xlim(-1.1, 1.0)
            target_ax.set_ylim(0.0, 1.0)
            target_ax.set_aspect('equal')
            target_ax.axis('off')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Топографический профиль":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]

            artists = []
            fill_area = target_ax.fill_between(
                x_arr, y_arr.min() - 1, y_arr,
                color=c, alpha=0.35, zorder=2)
            artists.append(fill_area)
            line, = target_ax.plot(
                x_arr, y_arr, color=c, lw=max(1.2, lw), zorder=3)
            artists.append(line)

            levels = int(data.get('bins', 5))
            for lvl in np.linspace(y_arr.min(), y_arr.max(),
                                   levels + 2)[1:-1]:
                ln = target_ax.axhline(
                    lvl, color='#999', lw=0.4, ls=':',
                    alpha=0.6, zorder=1)
                artists.append(ln)

            target_ax.set_xlabel("Distance")
            target_ax.set_ylabel("Elevation")
            target_ax.grid(True, ls='--', alpha=0.4)

            artist = artists[0]
            data['_extra_artists'] = artists[1:]

        elif t == "Вейвлет-скейлограмма":
            try:
                import pywt
            except ImportError:
                target_ax.text(
                    0.5, 0.5,
                    'Установите PyWavelets:\n  pip install PyWavelets',
                    transform=target_ax.transAxes,
                    ha='center', va='center', color='red')
                return None
            y_arr = np.array(y, dtype=float)
            if len(y_arr) < 8:
                return None
            fs = float(data.get('bins', 1) or 1)
            if fs <= 0:
                fs = 1.0

            wavelet = data.get('z')
            if not isinstance(wavelet, str):
                wavelet = 'cmor1.5-1.0'

            widths = np.arange(1, min(64, len(y_arr) // 2))
            try:
                coeffs, freqs = pywt.cwt(y_arr, widths, wavelet,
                                         sampling_period=1.0 / fs)
            except Exception:
                try:
                    wavelet = 'mexh'
                    widths = np.arange(1, min(64, len(y_arr) // 2))
                    coeffs, freqs = pywt.cwt(
                        y_arr, widths, wavelet,
                        sampling_period=1.0 / fs)
                except Exception as e:
                    target_ax.text(0.5, 0.5, f"wavelet error: {e}",
                                   transform=target_ax.transAxes,
                                   ha='center', va='center', color='red')
                    return None

            x_arr = np.array(x, dtype=float) if x else np.arange(len(y_arr))
            if len(x_arr) != len(y_arr):
                x_arr = np.arange(len(y_arr))

            artist = target_ax.imshow(
                np.abs(coeffs), extent=[
                    x_arr[0], x_arr[-1],
                    freqs[-1] if freqs.size else 0,
                    freqs[0] if freqs.size else 1],
                cmap=data.get('cmap', 'viridis'),
                aspect='auto', origin='upper')
            target_ax.set_xlabel("Time")
            target_ax.set_ylabel("Frequency")
            target_ax.set_yscale('log')
            try:
                cb = target_ax.figure.colorbar(artist, ax=target_ax,
                                               shrink=0.8)
                data['_extra_artists'] = [cb]
            except Exception:
                pass

        elif t == "Treemap":
            try:
                import squarify
            except ImportError:
                base_ax.text(
                    0.5, 0.5,
                    'Установите squarify:\n  pip install squarify',
                    transform=base_ax.transAxes,
                    ha='center', va='center', color='red')
                return None

            sizes = np.array(data.get('y', []), dtype=float)
            mask = sizes > 0
            sizes = sizes[mask]
            if len(sizes) == 0:
                return None

            labels = data.get('pie_labels') or \
                     [f"Item {i + 1}" for i in range(len(sizes))]
            labels = [str(l) for l in labels[:len(sizes)]]

            sizes_norm = squarify.normalize_sizes(sizes, 1, 1)
            rects = squarify.squarify(sizes_norm, 0, 0, 1, 1)

            custom_colors = [cc for cc in data.get('pie_colors', [])
                             if mcolors.is_color_like(cc)]
            if len(custom_colors) != len(sizes):
                cmap = plt.get_cmap('tab20')
                custom_colors = [cmap(i % 20) for i in range(len(sizes))]

            artists = []
            for rect, label, color in zip(rects, labels, custom_colors):
                patch = plt.Rectangle(
                    (rect['x'], rect['y']), rect['dx'], rect['dy'],
                    facecolor=color, edgecolor='white',
                    linewidth=1.5, zorder=2)
                base_ax.add_patch(patch)
                artists.append(patch)

                if rect['dx'] * rect['dy'] > 0.02:
                    base_ax.text(
                        rect['x'] + rect['dx'] / 2,
                        rect['y'] + rect['dy'] / 2,
                        label,
                        ha='center', va='center',
                        fontsize=max(6, int(
                            10 * (rect['dx'] * rect['dy']) ** 0.25)),
                        color='black', zorder=3)

            base_ax.set_xlim(0, 1)
            base_ax.set_ylim(0, 1)
            base_ax.set_aspect('equal')
            base_ax.axis('off')

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Sunburst":
            if getattr(base_ax, 'name', '') != 'polar':
                base_ax.text(0.5, 0.5,
                             'Sunburst требует полярную проекцию',
                             transform=base_ax.transAxes,
                             ha='center', va='center', color='red')
                return None

            sizes = np.array(data.get('y', []), dtype=float)
            labels = data.get('pie_labels') or \
                     [f"Item {i + 1}" for i in range(len(sizes))]
            parents = data.get('treemap_parents', []) or [''] * len(sizes)

            node_map = {}
            for lbl_, val, par in zip(labels, sizes, parents):
                node_map[str(lbl_)] = (float(val), str(par).strip())

            children = {}
            roots = []
            for lbl_, (val, par) in node_map.items():
                if par and par in node_map:
                    children.setdefault(par, []).append(lbl_)
                else:
                    roots.append(lbl_)

            if not roots:
                roots = list(node_map.keys())

            custom_colors = [cc for cc in data.get('pie_colors', [])
                             if mcolors.is_color_like(cc)]
            if len(custom_colors) != len(labels):
                cmap = plt.get_cmap('tab20')
                custom_colors = [cmap(i % 20) for i in range(len(labels))]
            color_map = dict(zip(labels, custom_colors))

            artists = []
            root_total = sum(node_map[r][0] for r in roots) or 1.0
            current_angle = 0.0

            for root_label in roots:
                root_val = node_map[root_label][0]
                root_angle = 2 * np.pi * (root_val / root_total)
                bars = base_ax.bar(
                    [current_angle + root_angle / 2],
                    [0.5],
                    [root_angle],
                    bottom=0.0,
                    color=color_map[root_label],
                    edgecolor='white', linewidth=1.2, zorder=2)
                artists.append(bars)

                base_ax.text(
                    current_angle + root_angle / 2, 0.25,
                    root_label, ha='center', va='center',
                    fontsize=8, color='white', fontweight='bold', zorder=3)

                child_labels = children.get(root_label, [])
                if child_labels:
                    child_total = sum(node_map[c_][0]
                                      for c_ in child_labels) or 1.0
                    child_angle_start = current_angle
                    for child_label in child_labels:
                        child_val = node_map[child_label][0]
                        child_angle = root_angle * (child_val / child_total)
                        base_ax.bar(
                            [child_angle_start + child_angle / 2],
                            [0.3],
                            [child_angle],
                            bottom=0.5,
                            color=color_map[child_label],
                            edgecolor='white', linewidth=0.8, zorder=2)
                        if child_angle > 0.3:
                            base_ax.text(
                                child_angle_start + child_angle / 2, 0.65,
                                child_label, ha='center', va='center',
                                fontsize=7, color='black', zorder=3)
                        child_angle_start += child_angle

                current_angle += root_angle

            base_ax.set_theta_direction(-1)
            base_ax.set_theta_zero_location('N')
            base_ax.set_axis_off()
            base_ax.set_ylim(0, 1.2)

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        # ====================================================================
        # СРАВНЕНИЕ / РАНГИ
        # ====================================================================
        elif t == "Slopegraph":
            if not x or len(x) < 2:
                return None
            left_label = str(x[0])
            right_label = str(x[1])

            y_vals = list(y) if y else []
            z_vals = list(z) if z else []
            n = min(len(y_vals), len(z_vals))
            if n < 1:
                return None
            y_vals = y_vals[:n]
            z_vals = z_vals[:n]

            labels_s = data.get('pie_labels') or \
                       [f"Item {i + 1}" for i in range(n)]
            cmap = plt.get_cmap('tab10')

            artists = []
            for i in range(n):
                color_i = c if i == 0 else cmap(i % 10)
                s1 = base_ax.scatter([0], [y_vals[i]],
                                     s=max(40, ms ** 2 * 2),
                                     color=color_i, zorder=3,
                                     label=labels_s[i]
                                     if i < len(labels_s) else None)
                s2 = base_ax.scatter([1], [z_vals[i]],
                                     s=max(40, ms ** 2 * 2),
                                     color=color_i, zorder=3)
                ln, = base_ax.plot([0, 1], [y_vals[i], z_vals[i]],
                                   '-', color=color_i, lw=lw,
                                   alpha=0.7, zorder=2)
                if i < len(labels_s):
                    base_ax.text(-0.05, y_vals[i],
                                 f"{labels_s[i]}: {y_vals[i]:g}",
                                 ha='right', va='center', fontsize=8)
                    base_ax.text(1.05, z_vals[i], f"{z_vals[i]:g}",
                                 ha='left', va='center', fontsize=8)
                artists.extend([s1, s2, ln])

            base_ax.set_xticks([0, 1])
            base_ax.set_xticklabels([left_label, right_label])
            base_ax.set_xlim(-0.3, 1.3)
            try:
                base_ax.legend(fontsize=8, loc='best')
            except Exception:
                pass

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:]

        elif t == "Bullet chart":
            if not y or len(y) < 1:
                return None
            try:
                target = float(y[0])
                warning = float(y[1]) if len(y) > 1 else target
                maximum = float(y[2]) if len(y) > 2 else warning
            except (ValueError, TypeError):
                return None

            label_b = str(x[0]) if x else "KPI"

            artists = []
            r_max = base_ax.barh([0], [maximum], height=0.5,
                                 color='#e0e0e0', edgecolor='gray',
                                 zorder=1)
            artists.extend(list(r_max))
            r_warn = base_ax.barh([0], [warning], height=0.5,
                                  color='#a0a0a0', edgecolor='gray',
                                  zorder=2)
            artists.extend(list(r_warn))
            r_target = base_ax.barh([0], [target], height=0.25,
                                    color='#e74c3c',
                                    edgecolor='black', zorder=3)
            artists.extend(list(r_target))

            tgt_line, = base_ax.plot([target, target], [-0.3, 0.3],
                                     '-', color='black', lw=2.5,
                                     zorder=4)
            artists.append(tgt_line)

            base_ax.set_yticks([0])
            base_ax.set_yticklabels([label_b])
            base_ax.set_xlim(0, maximum * 1.15)
            base_ax.set_ylim(-0.5, 0.5)
            base_ax.grid(True, axis='x', linestyle='--', alpha=0.4)

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:]

        elif t == "Диаграмма бифуркаций":
            if not x or len(x) < 2:
                return None
            try:
                r_min = float(x[0])
                r_max = float(x[1])
                x0 = float(y[0]) if y else 0.5
            except (ValueError, TypeError, IndexError):
                return None
            if r_max <= r_min:
                return None

            n_r = max(100, min(2000,
                               int(data.get('bins', 10)) * 100))
            n_iter = 200
            n_keep = 50

            r_vals = np.linspace(r_min, r_max, n_r)
            xs_log = []
            rs_log = []
            for r in r_vals:
                xv = x0
                for _ in range(n_iter):
                    xv = r * xv * (1 - xv)
                    if not np.isfinite(xv) or xv < -10 or xv > 10:
                        xv = 0.5
                for _ in range(n_keep):
                    xv = r * xv * (1 - xv)
                    if np.isfinite(xv):
                        rs_log.append(r)
                        xs_log.append(xv)

            if not rs_log:
                return None

            artist = base_ax.scatter(rs_log, xs_log,
                                     s=0.5, color=c, alpha=0.6,
                                     edgecolors='none')
            base_ax.set_xlabel("r")
            base_ax.set_ylabel("x*")
            base_ax.set_title("Bifurcation diagram")

        elif t == "Спидометр":
            if not y or len(y) < 1:
                return None
            try:
                xmin = float(x[0]) if x and len(x) >= 1 else 0.0
                xmax = float(x[1]) if x and len(x) >= 2 else 100.0
                value = float(y[0])
            except (ValueError, TypeError):
                return None
            if xmax <= xmin:
                xmax = xmin + 1.0

            frac = (value - xmin) / (xmax - xmin)
            frac = max(0.0, min(1.0, frac))

            artists = []
            theta_full = np.linspace(np.pi, 0, 100)
            bg, = base_ax.plot(np.cos(theta_full), np.sin(theta_full),
                               color='#e0e0e0', lw=20, zorder=1)
            artists.append(bg)

            theta_fill = np.linspace(np.pi,
                                     np.pi - frac * np.pi, 100)
            fill_ln, = base_ax.plot(np.cos(theta_fill),
                                    np.sin(theta_fill),
                                    color=c, lw=20, zorder=2)
            artists.append(fill_ln)

            angle = np.pi - frac * np.pi
            arrow, = base_ax.plot([0, 0.85 * np.cos(angle)],
                                  [0, 0.85 * np.sin(angle)],
                                  '-', color='black', lw=2.5,
                                  zorder=3)
            artists.append(arrow)

            txt = base_ax.text(0, -0.15, f"{value:g}",
                               ha='center', va='center',
                               fontsize=18, fontweight='bold',
                               zorder=4)
            artists.append(txt)

            base_ax.set_xlim(-1.3, 1.3)
            base_ax.set_ylim(-0.3, 1.3)
            base_ax.set_aspect('equal')
            base_ax.axis('off')
            base_ax.set_title("Speedometer")

            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:]

        return artist