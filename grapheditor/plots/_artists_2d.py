"""2D базовые и статистические графики.

Миксин для CreateArtistMixin. Вызывается из _create_artist._draw_2d()
для типов из TYPES_2D.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


TYPES_2D = frozenset({
    # Базовые
    "Линия", "Столбчатая", "Гистограмма", "Точечная", "Круговая",
    # Статистика
    "Box plot", "Violin",
    "Strip plot", "Ridge plot", "Raincloud plot",
    "Beanplot", "Swarm plot",
    "Cherry blossom plot", "Dot-and-whisker",
    "Q-Q plot", "ECDF", "Hexbin",
    "Сезонная декомпозиция", "Rolling statistics",
    # 2D продвинутые
    "Полигон", "Водопад", "Гант",
    "Кольцевая", "Вложенная круговая", "Мозаика",
    "Радиальная", "Столбчатая с накоплением",
    "Полярный scatter", "Пузырьковая", "Quiver",
    "Свечи (OHLC)", "Step plot", "Диаграмма Парето",
    "Renko", "Point-and-Figure",
})


class Artists2DMixin:

    def _draw_2d(self, data, base_ax, target_ax):
        """Рисует 2D-график. Возвращает artist или None."""
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        z = data.get('z', [])                     # FIX: было NameError в Slopegraph
        lw = data.get('lw', 2.0)
        ls = data.get('ls', '-')
        ms = data.get('ms', 6.0)
        raw_marker = data.get('marker', 'o')
        marker = None if raw_marker == "None" else raw_marker
        yerr = data.get('yerr', []) or None
        fill = data.get('fill', False)
        glow = data.get('glow', False)

        artist = None

        # ====================================================================
        # БАЗОВЫЕ
        # ====================================================================
        if t == "Линия":
            artist, = target_ax.plot(x, y, label=lbl, color=c, lw=lw,
                                     ls=ls, marker=marker, markersize=ms)
            extra = []
            if fill:
                try:
                    fb = target_ax.fill_between(x, y, alpha=0.3, color=c)
                    extra.append(fb)
                except Exception:
                    pass
            if yerr:
                try:
                    eb = target_ax.errorbar(x, y, yerr=yerr, fmt='none',
                                            ecolor=c, capsize=3)
                    extra.append(eb)
                except Exception:
                    pass
            data['_extra_artists'] = extra

        elif t == "Столбчатая":
            artist = target_ax.bar(x, y, label=lbl, color=c,
                                   yerr=yerr, capsize=3)

        elif t == "Гистограмма":
            edge = 'white' if self.dark_mode_var.get() else 'black'
            _, _, patches = target_ax.hist(
                x, bins=data.get('bins', 10), color=c, label=lbl,
                alpha=0.75, edgecolor=edge)
            artist = list(patches)

        elif t == "Точечная":
            extra = []
            if glow:
                try:
                    g1 = target_ax.scatter(x, y, s=ms ** 2 * 6, color=c,
                                           alpha=0.10, zorder=1)
                    g2 = target_ax.scatter(x, y, s=ms ** 2 * 3, color=c,
                                           alpha=0.25, zorder=2)
                    extra.extend([g1, g2])
                except Exception:
                    pass
            artist = target_ax.scatter(x, y, label=lbl, color=c,
                                       s=ms ** 2, marker=marker, zorder=3)
            if yerr:
                try:
                    eb = target_ax.errorbar(x, y, yerr=yerr, fmt='none',
                                            ecolor=c, capsize=3)
                    extra.append(eb)
                except Exception:
                    pass
            data['_extra_artists'] = extra

        elif t == "Круговая":
            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(y):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(y))]
            artist = list(base_ax.pie(y, labels=data['pie_labels'] or None,
                                      colors=pc, autopct='%1.1f%%'))

        # ====================================================================
        # СТАТИСТИКА
        # ====================================================================
        elif t == "Box plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            labels = data.get('pie_labels', [])
            labels_arg = labels if labels and len(labels) == len(groups) else None
            try:
                bp = base_ax.boxplot(groups, patch_artist=True,
                                     tick_labels=labels_arg)
            except TypeError:
                bp = base_ax.boxplot(groups, patch_artist=True,
                                     labels=labels_arg)
            for b in bp['boxes']:
                b.set_facecolor(c)
            artist = bp

        elif t == "Violin":
            groups = data.get('box_data', [])
            if not groups:
                return None
            vp = base_ax.violinplot(groups, showmedians=True)
            for b in vp['bodies']:
                b.set_facecolor(c)
                b.set_alpha(0.75)
            artist = vp

        elif t == "Strip plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            rng = np.random.default_rng(42)
            artists = []
            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) == 0:
                    continue
                jitter = rng.normal(0, 0.06, size=len(g_arr))
                sc = base_ax.scatter(
                    np.full_like(g_arr, i, dtype=float) + jitter,
                    g_arr, alpha=0.6, color=c, s=ms ** 2,
                    edgecolors='black', linewidths=0.4,
                    label=lbl if i == 0 else None,
                    zorder=3)
                artists.append(sc)
            labels = data.get('pie_labels', [])
            base_ax.set_xticks(range(len(groups)))
            if labels and len(labels) == len(groups):
                base_ax.set_xticklabels(labels)
            base_ax.set_xlim(-0.5, len(groups) - 0.5)
            artist = artists

        elif t == "Ridge plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            try:
                from scipy.stats import gaussian_kde
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            labels = data.get('pie_labels', [])
            artists = []
            n = len(groups)
            all_vals = np.concatenate(
                [np.array(g, dtype=float) for g in groups
                 if len(g) > 1])
            if len(all_vals) == 0:
                return None
            xmin, xmax = np.nanmin(all_vals), np.nanmax(all_vals)
            pad = (xmax - xmin) * 0.1 or 1.0
            xs = np.linspace(xmin - pad, xmax + pad, 400)
            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) < 2:
                    continue
                try:
                    kde = gaussian_kde(g_arr)
                    ys = kde(xs)
                except Exception:
                    continue
                ys = ys / ys.max() * 0.7
                offset = (n - 1 - i) * 1.0
                color_i = c if i == 0 else None
                fill_area = base_ax.fill_between(
                    xs, offset, offset + ys,
                    color=color_i, alpha=0.75,
                    edgecolor='white', linewidth=0.8,
                    label=lbl if i == 0 else None)
                artists.append(fill_area)
                ln, = base_ax.plot(xs, offset + ys,
                                   color='#333', lw=0.8)
                artists.append(ln)
                if labels and i < len(labels):
                    base_ax.text(xmin - pad * 0.5, offset + 0.15,
                                 labels[i], ha='right', va='bottom',
                                 fontsize=9)
                else:
                    base_ax.text(xmin - pad * 0.5, offset + 0.15,
                                 f"Группа {i + 1}",
                                 ha='right', va='bottom', fontsize=9)
            base_ax.set_yticks([])
            try:
                base_ax.spines['left'].set_visible(False)
            except Exception:
                pass
            base_ax.set_ylim(-0.2, n + 0.3)
            artist = artists

        elif t == "Raincloud plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            try:
                from scipy.stats import gaussian_kde
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            labels = data.get('pie_labels', [])
            n = len(groups)
            rng = np.random.default_rng(42)
            artists = []
            half = 0.35

            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) < 2:
                    continue
                try:
                    kde = gaussian_kde(g_arr)
                except Exception:
                    continue
                ys = np.linspace(g_arr.min(), g_arr.max(), 200)
                xs_dens = kde(ys)
                xs_dens = xs_dens / xs_dens.max() * half

                fill_area = base_ax.fill_betweenx(
                    ys, i - xs_dens, i, color=c, alpha=0.6,
                    label=lbl if i == 0 else None)
                artists.append(fill_area)
                edge, = base_ax.plot(i - xs_dens, ys, color=c, lw=0.8)
                artists.append(edge)

                q1 = np.percentile(g_arr, 25)
                q2 = np.percentile(g_arr, 50)
                q3 = np.percentile(g_arr, 75)
                iqr = q3 - q1
                w_lo = max(g_arr.min(), q1 - 1.5 * iqr)
                w_hi = min(g_arr.max(), q3 + 1.5 * iqr)
                box_center = i + 0.15
                box_w = 0.08
                rect = plt.Rectangle(
                    (box_center - box_w / 2, q1),
                    box_w, q3 - q1,
                    facecolor='white', edgecolor='black',
                    linewidth=0.8, zorder=4)
                base_ax.add_patch(rect)
                artists.append(rect)
                med, = base_ax.plot(
                    [box_center - box_w / 2, box_center + box_w / 2],
                    [q2, q2],
                    color='black', lw=1.2, zorder=5)
                artists.append(med)
                for w_end, w_start in ((w_lo, q1), (w_hi, q3)):
                    wl, = base_ax.plot(
                        [box_center, box_center],
                        [w_start, w_end],
                        color='black', lw=0.6)
                    artists.append(wl)

                jitter = rng.normal(0, 0.05, size=len(g_arr))
                sc = base_ax.scatter(
                    np.full_like(g_arr, i + 0.35) + jitter,
                    g_arr, s=ms ** 2 * 0.5, color=c,
                    alpha=0.7, edgecolors='none', zorder=3)
                artists.append(sc)

                if labels and i < len(labels):
                    t_lbl = base_ax.text(
                        i, g_arr.min() - 0.05, labels[i],
                        ha='center', va='top', fontsize=9)
                    artists.append(t_lbl)

            base_ax.set_xticks([])
            base_ax.set_xlim(-0.7, n - 0.3)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Beanplot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            try:
                from scipy.stats import gaussian_kde
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            rng = np.random.default_rng(42)
            artists = []

            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) < 2:
                    continue
                try:
                    kde = gaussian_kde(g_arr)
                except Exception:
                    continue
                ys = np.linspace(g_arr.min(), g_arr.max(), 200)
                dens = kde(ys)
                max_d = dens.max() if dens.max() > 0 else 1.0
                dens = dens / max_d * 0.4

                fill_area = base_ax.fill_betweenx(
                    ys, i - dens, i + dens,
                    color=c, alpha=0.5)
                artists.append(fill_area)
                edge_l, = base_ax.plot(i - dens, ys,
                                       color=c, lw=0.8)
                edge_r, = base_ax.plot(i + dens, ys,
                                       color=c, lw=0.8)
                artists.extend([edge_l, edge_r])

                jitter = rng.uniform(-0.05, 0.05,
                                     size=len(g_arr))
                sc = base_ax.scatter(
                    np.full_like(g_arr, i) + jitter, g_arr,
                    s=max(4, ms * 0.5),
                    color='black', alpha=0.5, zorder=3)
                artists.append(sc)

                mean_val = float(np.mean(g_arr))
                mean_ln, = base_ax.plot(
                    [i - 0.4, i + 0.4],
                    [mean_val, mean_val],
                    color='red', lw=2.0, zorder=4)
                artists.append(mean_ln)

            labels = data.get('pie_labels', [])
            base_ax.set_xticks(range(len(groups)))
            if labels and len(labels) == len(groups):
                base_ax.set_xticklabels(labels)
            base_ax.set_xlim(-0.5, len(groups) - 0.5)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Swarm plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            labels = data.get('pie_labels', [])
            artists = []

            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) == 0:
                    continue
                sorted_vals = np.sort(g_arr)
                y_range = sorted_vals.max() - sorted_vals.min()
                if y_range == 0:
                    y_range = 1.0
                point_diameter_y = y_range / 40
                placed = []
                for v in sorted_vals:
                    candidates = [0.0]
                    for step in range(1, 30):
                        candidates.append(step * 0.04)
                        candidates.append(-step * 0.04)
                    placed_x = 0.0
                    for cx in candidates:
                        ok = True
                        for (px, py) in placed:
                            if (abs(px - cx) < 0.06 and
                                    abs(py - v) < point_diameter_y):
                                ok = False
                                break
                        if ok:
                            placed_x = cx
                            break
                    placed.append((placed_x, v))

                xs_pts = np.array([i + p[0] for p in placed])
                ys_pts = np.array([p[1] for p in placed])
                sc = base_ax.scatter(
                    xs_pts, ys_pts,
                    s=max(15, ms ** 2 * 0.6),
                    color=c, alpha=0.7,
                    edgecolors='white', linewidths=0.4,
                    zorder=3,
                    label=lbl if i == 0 else None)
                artists.append(sc)

                med = float(np.median(g_arr))
                med_line, = base_ax.plot(
                    [i - 0.4, i + 0.4], [med, med],
                    color='black', lw=1.5, zorder=4)
                artists.append(med_line)

            base_ax.set_xticks(range(len(groups)))
            if labels and len(labels) == len(groups):
                base_ax.set_xticklabels(labels)
            base_ax.set_xlim(-0.5, len(groups) - 0.5)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Cherry blossom plot":
            groups = data.get('box_data', [])
            if not groups:
                return None
            labels = data.get('pie_labels', [])
            artists = []
            cmap_c = plt.get_cmap('spring')

            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) == 0:
                    continue
                qs = [0, 5, 10, 25, 50, 75, 90, 95, 100]
                q_vals = [float(np.percentile(g_arr, q)) for q in qs]
                median = q_vals[4]
                stem, = base_ax.plot(
                    [i, i], [q_vals[0], q_vals[-1]],
                    color='#5a3a1a', lw=1.5, zorder=1)
                artists.append(stem)
                for q_idx, qv in enumerate(q_vals):
                    dist = abs(q_idx - 4)
                    w = max(0.05, 0.35 - dist * 0.05)
                    color_i = cmap_c(dist / 4.0)
                    line, = base_ax.plot(
                        [i - w, i + w], [qv, qv],
                        color=color_i, lw=3.0,
                        solid_capstyle='round',
                        alpha=0.85, zorder=3)
                    artists.append(line)
                med_line, = base_ax.plot(
                    [i - 0.4, i + 0.4], [median, median],
                    color='#c0392b', lw=3.5,
                    solid_capstyle='round',
                    zorder=4,
                    label=lbl if i == 0 else None)
                artists.append(med_line)

            base_ax.set_xticks(range(len(groups)))
            if labels and len(labels) == len(groups):
                base_ax.set_xticklabels(labels)
            base_ax.set_xlim(-0.5, len(groups) - 0.5)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Dot-and-whisker":
            groups = data.get('box_data', [])
            if not groups:
                return None
            labels = data.get('pie_labels', [])
            artists = []

            for i, g in enumerate(groups):
                g_arr = np.array(g, dtype=float)
                g_arr = g_arr[np.isfinite(g_arr)]
                if len(g_arr) == 0:
                    continue
                q1 = float(np.percentile(g_arr, 25))
                q2 = float(np.percentile(g_arr, 50))
                q3 = float(np.percentile(g_arr, 75))
                gmin = float(g_arr.min())
                gmax = float(g_arr.max())

                whisk, = base_ax.plot(
                    [i, i], [gmin, gmax],
                    color='#888', lw=1.0, zorder=1)
                artists.append(whisk)
                iqr_ln, = base_ax.plot(
                    [i, i], [q1, q3],
                    color='black', lw=3.0,
                    solid_capstyle='round', zorder=2)
                artists.append(iqr_ln)
                for gv in (gmin, gmax):
                    cap, = base_ax.plot(
                        [i - 0.08, i + 0.08], [gv, gv],
                        color='#888', lw=1.0, zorder=1)
                    artists.append(cap)
                dot = base_ax.scatter(
                    [i], [q2],
                    s=max(80, ms ** 2 * 5),
                    color=c, edgecolors='black',
                    linewidths=1.0, zorder=3,
                    label=lbl if i == 0 else None)
                artists.append(dot)

            base_ax.set_xticks(range(len(groups)))
            if labels and len(labels) == len(groups):
                base_ax.set_xticklabels(labels)
            base_ax.set_xlim(-0.5, len(groups) - 0.5)
            artist = artists[0] if artists else None
            data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

        elif t == "Q-Q plot":
            try:
                from scipy import stats as _stats
            except ImportError:
                base_ax.text(0.5, 0.5, 'scipy required',
                             transform=base_ax.transAxes,
                             ha='center', color='red')
                return None
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 3:
                return None
            try:
                (osm, osr), (slope, intercept, r) = _stats.probplot(
                    y_arr, dist="norm", fit=True)
            except Exception:
                return None
            pts = base_ax.plot(osm, osr, marker, color=c,
                               markersize=ms, alpha=0.7,
                               linestyle='none', label=lbl)[0]
            x_line = np.array([osm[0], osm[-1]])
            y_line = slope * x_line + intercept
            line, = base_ax.plot(x_line, y_line, '--',
                                 color='red', lw=lw,
                                 label=f"R² = {r ** 2:.4f}")
            base_ax.set_xlabel("Теоретические квантили")
            base_ax.set_ylabel("Выборочные квантили")
            data['_extra_artists'] = [line]
            artist = pts

        elif t == "ECDF":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 1:
                return None
            y_sorted = np.sort(y_arr)
            xs = np.concatenate([[y_sorted[0]], y_sorted])
            ys = np.concatenate([[0],
                                 np.arange(1, len(y_sorted) + 1)
                                 / len(y_sorted)])
            artist, = base_ax.step(xs, ys, where='post',
                                   color=c, lw=lw, ls=ls, label=lbl)
            base_ax.set_ylim(0, 1.05)
            base_ax.set_ylabel("P(X ≤ x)")

        elif t == "Hexbin":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            n = min(len(x_arr), len(y_arr))
            if n < 3:
                return None
            gridsize = int(data.get('bins', 30))
            gridsize = max(3, min(200, gridsize))
            extra = []
            try:
                hb = base_ax.hexbin(
                    x_arr[:n], y_arr[:n],
                    gridsize=gridsize,
                    cmap=data.get('cmap', 'viridis'),
                    mincnt=1)
                if data.get('show_colorbar', True):
                    cb = base_ax.figure.colorbar(hb, ax=base_ax)
                    extra.append(cb)
            except Exception:
                return None
            data['_extra_artists'] = extra
            artist = hb

        elif t == "Сезонная декомпозиция":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 4:
                return None
            period = max(2, int(data.get('bins', 12)))
            if period >= len(y_arr):
                period = max(2, len(y_arr) // 2)

            window = period if period % 2 == 1 else period + 1
            kernel = np.ones(window) / window
            trend = np.convolve(y_arr, kernel, mode='same')
            half = window // 2
            trend[:half] = np.nan
            trend[-half:] = np.nan

            detrended = y_arr - trend
            seasonal = np.full_like(y_arr, np.nan)
            for phase in range(period):
                vals = [detrended[j] for j in range(phase, len(y_arr), period)
                        if np.isfinite(detrended[j])]
                if vals:
                    mean_val = np.mean(vals)
                    for j in range(phase, len(y_arr), period):
                        seasonal[j] = mean_val

            residual = y_arr - trend - seasonal

            xs = (x if len(x) == len(y_arr) else np.arange(len(y_arr)))
            l_orig, = base_ax.plot(
                xs, y_arr, '-', color=c, lw=lw,
                label=f"{lbl or 'Ряд'} (наблюдения)")
            l_trend, = base_ax.plot(
                xs, trend, '-', color='red', lw=lw,
                label='Тренд')
            l_seas, = base_ax.plot(
                xs, seasonal, '-', color='green', lw=lw,
                label='Сезонность')
            l_res, = base_ax.plot(
                xs, residual, '-', color='purple',
                lw=max(0.6, lw * 0.7),
                label='Остаток')
            try:
                base_ax.legend(fontsize=8)
            except Exception:
                pass
            data['_extra_artists'] = [l_trend, l_seas, l_res]
            artist = l_orig

        elif t == "Rolling statistics":
            y_arr = np.array(y, dtype=float)
            if len(y_arr) < 2:
                return None
            window = max(2, int(data.get('bins', 5)))
            window = min(window, len(y_arr))

            kernel = np.ones(window) / window
            y_mean = np.convolve(y_arr, kernel, mode='same')

            y_std = np.zeros_like(y_arr)
            for i in range(len(y_arr)):
                lo = max(0, i - window // 2)
                hi = min(len(y_arr), i + window // 2 + 1)
                y_std[i] = np.nanstd(y_arr[lo:hi])

            xs = (x if len(x) == len(y_arr) else np.arange(len(y_arr)))

            l_orig, = base_ax.plot(
                xs, y_arr, '-', color=c,
                lw=max(0.6, lw * 0.5), alpha=0.5,
                label=f"{lbl or 'Сигнал'}")
            fill_area = base_ax.fill_between(
                xs, y_mean - y_std, y_mean + y_std,
                color=c, alpha=0.25,
                label=f"±σ (окно {window})")
            l_mean, = base_ax.plot(
                xs, y_mean, '-', color='red', lw=lw,
                label=f"Среднее (окно {window})")
            try:
                base_ax.legend(fontsize=8)
            except Exception:
                pass
            data['_extra_artists'] = [l_orig, fill_area]
            artist = l_mean

        # ====================================================================
        # 2D ПРОДВИНУТЫЕ
        # ====================================================================
        elif t == "Полигон":
            if not x or not y:
                return None
            try:
                closed_x = list(x) + [x[0]]
                closed_y = list(y) + [y[0]]
                fill_artist = base_ax.fill(x, y, color=c, alpha=0.4,
                                           label=lbl)
                line_artist, = base_ax.plot(closed_x, closed_y,
                                            color=c, lw=lw)
                artist = list(fill_artist) + [line_artist]
            except Exception:
                return None

        elif t == "Водопад":
            vals = np.array(y, dtype=float)
            n = len(vals)
            if n == 0:
                return None
            cumulative = np.cumsum(vals)
            starts = np.concatenate([[0], cumulative[:-1]])
            colors_w = ['#2ecc71' if v >= 0 else '#e74c3c' for v in vals]
            xs = np.arange(n)
            bars = base_ax.bar(xs, vals, bottom=starts,
                               color=colors_w, edgecolor='white',
                               label=lbl)
            extra = []
            for i in range(n - 1):
                y_lvl = cumulative[i]
                ln, = base_ax.plot([xs[i] + 0.4, xs[i + 1] - 0.4],
                                   [y_lvl, y_lvl],
                                   color='#888', lw=1, ls='--')
                extra.append(ln)
            total = base_ax.bar([n], [cumulative[-1]], color='#3498db',
                                edgecolor='white', label='Total')
            extra.append(total)
            labels = data.get('pie_labels') or []
            ticks = list(xs) + [n]
            if labels and len(labels) >= n:
                ticklabels = list(labels[:n]) + ['Total']
            else:
                ticklabels = [str(i) for i in range(n)] + ['Total']
            base_ax.set_xticks(ticks)
            base_ax.set_xticklabels(ticklabels, rotation=30, ha='right')

            def _cleanup(_ax=base_ax):
                try:
                    _ax.set_xticks([])
                    _ax.set_xticklabels([])
                except Exception:
                    pass

            data['_extra_artists'] = extra
            data['_cleanup'] = _cleanup
            artist = bars

        elif t == "Гант":
            starts = np.array(x, dtype=float)
            durations = np.array(y, dtype=float)
            n = min(len(starts), len(durations))
            if n == 0:
                return None
            starts, durations = starts[:n], durations[:n]
            labels = list(data.get('pie_labels') or [])
            labels = labels + [f"Task {i + 1}"
                               for i in range(len(labels), n)]
            labels = labels[:n]
            colors_g = [cc for cc in data.get('pie_colors', [])
                        if mcolors.is_color_like(cc)]
            if len(colors_g) != n:
                cmap = plt.get_cmap('tab10')
                colors_g = [cmap(i % 10) for i in range(n)]
            ys = np.arange(n)
            bars = base_ax.barh(ys, durations, left=starts,
                                color=colors_g, edgecolor='white',
                                height=0.6, label=lbl)
            base_ax.set_yticks(ys)
            base_ax.set_yticklabels(labels)
            base_ax.invert_yaxis()
            base_ax.grid(True, axis='x', ls='--', alpha=0.5)

            def _cleanup(_ax=base_ax):
                try:
                    _ax.set_yticks([])
                    _ax.set_yticklabels([])
                    _ax.invert_yaxis()
                    _ax.xaxis.grid(self.show_grid_var.get(),
                                   linestyle='--', alpha=0.6)
                    _ax.yaxis.grid(self.show_grid_var.get(),
                                   linestyle='--', alpha=0.6)
                except Exception:
                    pass

            data['_extra_artists'] = []
            data['_cleanup'] = _cleanup
            artist = bars

        elif t == "Кольцевая":
            pc = [cc for cc in data.get('pie_colors', [])
                  if mcolors.is_color_like(cc)]
            if len(pc) != len(y):
                cmap = plt.get_cmap('tab10')
                pc = [cmap(i % 10) for i in range(len(y))]
            artist = list(base_ax.pie(
                y, labels=data['pie_labels'] or None,
                colors=pc, autopct='%1.1f%%',
                wedgeprops=dict(width=0.4, edgecolor='white')))

        elif t == "Вложенная круговая":
            rings = data.get('box_data', [])
            if not rings:
                return None
            labels = data.get('pie_labels', [])
            all_artists = []
            size = 1.0 / len(rings)
            for i, ring_vals in enumerate(rings):
                radius = 1.0 - i * size
                pc = [cc for cc in data.get('pie_colors', [])
                      if mcolors.is_color_like(cc)]
                if len(pc) != len(ring_vals):
                    cmap = plt.get_cmap('tab10')
                    pc = [cmap(j % 10) for j in range(len(ring_vals))]
                wp = dict(width=size, edgecolor='white')
                if i == 0 and labels and len(labels) == len(ring_vals):
                    w_ = base_ax.pie(ring_vals, radius=radius, colors=pc,
                                     wedgeprops=wp, autopct='%1.1f%%',
                                     pctdistance=radius - size / 2)
                else:
                    w_ = base_ax.pie(ring_vals, radius=radius, colors=pc,
                                     wedgeprops=wp)
                all_artists.append(w_)
            artist = all_artists

        elif t == "Мозаика":
            rows = data.get('box_data', [])
            if len(rows) < 2:
                return None
            if len(set(len(r) for r in rows)) != 1:
                return None
            labels = data.get('pie_labels', [])
            col_sums = [sum(row[col] for row in rows)
                        for col in range(len(rows[0]))]
            total = sum(col_sums)
            if total <= 0:
                return None
            cmap = plt.get_cmap('tab10')
            x_pos = 0.0
            artists = []
            for col in range(len(rows[0])):
                col_total = col_sums[col]
                width = col_total / total
                y_pos = 0.0
                for r_idx, row in enumerate(rows):
                    height = row[col] / col_total if col_total > 0 else 0
                    lbl_use = None
                    if col == 0 and r_idx < len(labels):
                        lbl_use = labels[r_idx]
                    rects = base_ax.bar(x_pos, height, width=width,
                                        bottom=y_pos, align='edge',
                                        color=cmap(r_idx % 10),
                                        edgecolor='white', label=lbl_use)
                    y_pos += height
                    artists.append(rects)
                x_pos += width
            base_ax.set_xlim(0, 1)
            base_ax.set_ylim(0, 1)
            base_ax.set_xticks([])
            base_ax.set_yticks([])
            artist = artists

        elif t == "Радиальная":
            if not x or not y:
                return None
            try:
                theta = np.deg2rad(np.array(x, dtype=float))
                vals = np.array(y, dtype=float)
                width = 2 * np.pi / max(len(theta), 1) * 0.8
                artist = base_ax.bar(theta, vals, width=width, color=c,
                                     label=lbl, alpha=0.85,
                                     edgecolor='white')
            except Exception:
                return None

        elif t == "Полярный scatter":
            if not x or not y:
                return None
            try:
                theta = np.deg2rad(np.array(x, dtype=float))
                r = np.array(y, dtype=float)
                n = min(len(theta), len(r))
                if n == 0:
                    return None
                artist = base_ax.scatter(
                    theta[:n], r[:n], color=c, s=ms ** 2,
                    label=lbl, alpha=0.85,
                    edgecolors='black', linewidths=0.5)
            except Exception:
                return None

        elif t == "Пузырьковая":
            sizes = np.array(data.get('z', []), dtype=float)
            if len(sizes) == 0 or len(x) != len(sizes):
                return None
            try:
                smin, smax = sizes.min(), sizes.max()
                if smax > smin:
                    norm = (sizes - smin) / (smax - smin)
                else:
                    norm = np.zeros_like(sizes)
                areas = 20 + norm * 980
                artist = base_ax.scatter(
                    x, y, s=areas, color=c, alpha=0.55,
                    edgecolors='black', linewidths=0.6,
                    label=lbl, zorder=3)
            except Exception:
                return None

        elif t == "Quiver":
            U = np.array(data.get('z', []), dtype=float)
            V = np.array(data.get('yerr', []), dtype=float)
            if len(U) == 0 or len(U) != len(V):
                return None
            if len(x) != len(U) or len(y) != len(U):
                return None
            try:
                artist = base_ax.quiver(
                    x, y, U, V, angles='xy', scale_units='xy',
                    scale=1, color=c, width=0.005, label=lbl)
            except Exception:
                return None

        elif t == "Столбчатая с накоплением":
            series = data.get('box_data', [])
            if not series:
                series = [y]
            if not x:
                xs = np.arange(len(series[0]))
            else:
                xs = np.array(x, dtype=float)
            width = (xs[1] - xs[0]) * 0.8 if len(xs) > 1 else 0.8
            cmap = plt.get_cmap('tab10')
            bottom = np.zeros(len(xs))
            artists = []
            for i, s in enumerate(series):
                s_arr = np.array(s, dtype=float)
                min_len = min(len(s_arr), len(xs))
                col = c if i == 0 else cmap(i % 10)
                lbl_use = lbl if i == 0 else f"{lbl} #{i + 1}"
                bars = base_ax.bar(xs[:min_len], s_arr[:min_len],
                                   width=width, bottom=bottom[:min_len],
                                   color=col, label=lbl_use,
                                   edgecolor='white')
                artists.append(bars)
                bottom[:min_len] += s_arr[:min_len]
            artist = artists

        elif t == "Свечи (OHLC)":
            groups = data.get('box_data', [])
            if len(groups) < 4:
                base_ax.text(0.5, 0.5,
                             'Нужны 4 серии OHLC (Open;High;Low;Close)',
                             transform=base_ax.transAxes,
                             ha='center', va='center', color='red')
                return None
            o = np.array(groups[0], dtype=float)
            h = np.array(groups[1], dtype=float)
            l_ = np.array(groups[2], dtype=float)
            cl = np.array(groups[3], dtype=float)
            n = min(len(o), len(h), len(l_), len(cl))
            if n == 0:
                return None
            o, h, l_, cl = o[:n], h[:n], l_[:n], cl[:n]
            xs = np.arange(n)

            artists = []
            for i in range(n):
                color_i = '#2ecc71' if cl[i] >= o[i] else '#e74c3c'
                wick, = base_ax.plot([i, i], [l_[i], h[i]],
                                     color=color_i, lw=1.0, zorder=2)
                artists.append(wick)

            width = 0.6
            for i in range(n):
                color_i = '#2ecc71' if cl[i] >= o[i] else '#e74c3c'
                bottom = min(o[i], cl[i])
                height = abs(cl[i] - o[i]) or 0.001
                rect = plt.Rectangle(
                    (i - width / 2, bottom), width, height,
                    facecolor=color_i, edgecolor='black',
                    linewidth=0.5, zorder=3)
                base_ax.add_patch(rect)
                artists.append(rect)

            x_labels = x[:n] if len(x) >= n else xs
            base_ax.set_xticks(xs)
            try:
                base_ax.set_xticklabels([str(v) for v in x_labels],
                                        rotation=30, ha='right')
            except Exception:
                pass
            base_ax.set_xlim(-0.7, n - 0.3)
            base_ax.grid(True, axis='y', ls='--', alpha=0.4)
            artist = artists
            data['_extra_artists'] = []

        elif t == "Диаграмма Парето":
            if not x or not y:
                return None
            y_arr = np.array(y, dtype=float)
            x_arr = list(x)
            n = min(len(x_arr), len(y_arr))
            if n < 1:
                return None
            x_arr = x_arr[:n]
            y_arr = y_arr[:n]
            order = np.argsort(-y_arr)
            y_sorted = y_arr[order]
            x_sorted = [x_arr[i] for i in order]
            xs = np.arange(len(y_sorted))

            bars = base_ax.bar(xs, y_sorted, color=c,
                               edgecolor='white', label=lbl)
            base_ax.set_xticks(xs)
            try:
                base_ax.set_xticklabels(
                    [str(v) for v in x_sorted], rotation=30, ha='right')
            except Exception:
                pass

            ax2 = base_ax.twinx()
            cumsum = np.cumsum(y_sorted)
            total = cumsum[-1] if cumsum[-1] != 0 else 1
            cum_pct = cumsum / total * 100.0
            line, = ax2.plot(xs, cum_pct, 'o-', color='red',
                             lw=lw, markersize=max(3, ms))
            ax2.set_ylim(0, 105)
            ax2.set_ylabel('Накопленный %', color='red')
            try:
                ax2.tick_params(axis='y', labelcolor='red')
            except Exception:
                pass
            eighty = ax2.axhline(80, color='gray', lw=0.8, ls='--')

            def _cleanup(_ax2=ax2):
                try:
                    _ax2.remove()
                except Exception:
                    pass

            data['_extra_artists'] = [line, eighty]
            data['_cleanup'] = _cleanup
            artist = bars

        elif t == "Step plot":
            artist, = base_ax.step(x, y, where='post',
                                   color=c, lw=lw, ls=ls,
                                   label=lbl)

        elif t == "Renko":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 2:
                return None
            brick = float(data.get('bins', 0) or 0)
            if brick <= 0:
                rng_val = np.max(y_arr) - np.min(y_arr)
                brick = rng_val / 20 if rng_val > 0 else 1.0

            bricks = []
            cur = float(y_arr[0])
            col = 0
            for price in y_arr[1:]:
                guard = 0
                while abs(price - cur) >= brick and guard < 10000:
                    guard += 1
                    if price > cur:
                        bricks.append((col, cur, cur + brick, 1))
                        cur = cur + brick
                    else:
                        bricks.append((col, cur, cur - brick, -1))
                        cur = cur - brick
                    col += 1

            if not bricks:
                base_ax.text(0.5, 0.5,
                             f'Мало движения (кирпич = {brick:.4g})',
                             transform=base_ax.transAxes,
                             ha='center', va='center', color='orange')
                return None

            artists = []
            for idx, op, cl_, direction in bricks:
                color_i = '#2ecc71' if direction > 0 else '#e74c3c'
                bottom = min(op, cl_)
                height = abs(cl_ - op)
                rect = plt.Rectangle(
                    (idx - 0.4, bottom), 0.8, height,
                    facecolor=color_i, edgecolor='black',
                    linewidth=0.5, zorder=3)
                base_ax.add_patch(rect)
                artists.append(rect)

            base_ax.set_xlim(-1, len(bricks))
            base_ax.grid(True, axis='y', ls='--', alpha=0.4)
            base_ax.set_xlabel(f"Кирпич = {brick:.4g}")
            artist = artists[0]
            data['_extra_artists'] = artists[1:]

        elif t == "Point-and-Figure":
            y_arr = np.array(y, dtype=float)
            y_arr = y_arr[np.isfinite(y_arr)]
            if len(y_arr) < 2:
                return None
            box = float(data.get('bins', 0) or 0)
            if box <= 0:
                rng_val = np.max(y_arr) - np.min(y_arr)
                box = rng_val / 20 if rng_val > 0 else 1.0

            columns = []
            last_level = int(np.floor(y_arr[0] / box))
            col_dir = None
            col_levels = [last_level]

            for price in y_arr[1:]:
                lvl = int(np.floor(price / box))
                guard = 0
                while lvl != last_level and guard < 10000:
                    guard += 1
                    if lvl > last_level:
                        if col_dir == -1:
                            columns.append((col_dir, col_levels))
                            col_dir = 1
                            last_level += 1
                            col_levels = [last_level]
                        else:
                            if col_dir is None:
                                col_dir = 1
                            last_level += 1
                            col_levels.append(last_level)
                    else:
                        if col_dir == 1:
                            columns.append((col_dir, col_levels))
                            col_dir = -1
                            last_level -= 1
                            col_levels = [last_level]
                        else:
                            if col_dir is None:
                                col_dir = -1
                            last_level -= 1
                            col_levels.append(last_level)
            if col_levels:
                columns.append((col_dir, col_levels))

            if not columns:
                return None

            artists = []
            for col_idx, (direction, levels) in enumerate(columns):
                color_i = '#2ecc71' if direction == 1 else '#e74c3c'
                mark = 'X' if direction == 1 else 'O'
                for lvl in levels:
                    t_lbl = base_ax.text(
                        col_idx, lvl * box, mark,
                        ha='center', va='center',
                        color=color_i, fontsize=10,
                        fontweight='bold', zorder=4)
                    artists.append(t_lbl)

            base_ax.set_xticks(range(len(columns)))
            base_ax.set_xlim(-1, len(columns))
            base_ax.grid(True, ls='--', alpha=0.3)
            base_ax.set_ylabel(f"Клетка = {box:.4g}")
            artist = artists[0]
            data['_extra_artists'] = artists[1:]

        return artist