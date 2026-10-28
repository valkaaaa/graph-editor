import numpy as np
import matplotlib as mpl
import matplotlib.cm
import matplotlib.ticker
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class CreateArtistMixin:
    def _create_artist(self, data):
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        lw = data.get('lw', 2.0)
        ls = data.get('ls', '-')
        ms = data.get('ms', 6.0)
        raw_marker = data.get('marker', 'o')
        marker = None if raw_marker == "None" else raw_marker
        yerr = data.get('yerr', []) or None
        fill = data.get('fill', False)
        glow = data.get('glow', False)

        # Сбрасываем возможные старые ссылки
        data['_extra_artists'] = []
        data['_cleanup'] = None

        if self.smooth_var.get() and t in ("Линия", "Точечная", "Столбчатая"):
            try:
                y = self._smooth(y, self.settings['smooth_window']).tolist()
            except Exception:
                pass

        subplot_idx = data.get('subplot_index', 0)
        base_ax = self._get_axis(subplot_idx)

        target_ax = base_ax
        if (data.get('use_y2')
                and not hasattr(base_ax, 'get_zlim')
                and getattr(base_ax, 'name', '') != 'polar'):
            if subplot_idx not in self.axes_secondary:
                self.axes_secondary[subplot_idx] = base_ax.twinx()
                if self.dark_mode_var.get():
                    self.axes_secondary[subplot_idx].set_facecolor('#2b2b2b')
                self.axes_secondary[subplot_idx].set_ylabel(
                    tr.t('right.second_y_axis'), color='red')
            target_ax = self.axes_secondary[subplot_idx]

        # ----- Plugin-типы (наивысший приоритет) -----
        if (hasattr(self, 'plugin_registry')
                and t in self.plugin_registry.chart_types):
            return self.plugin_registry.call_draw(self, target_ax, data)

        # ----- 2D базовые -----
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

        # ----- 2D продвинутые -----
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

        elif t in ("Heatmap", "Contour", "Imshow"):
            raw = data.get('heatmap_data', [])
            if not raw:
                return None
            row_lens = [len(r) for r in raw if r]
            if not row_lens:
                return None
            if len(set(row_lens)) != 1:
                min_len = min(row_lens)
                raw = [r[:min_len] for r in raw if len(r) >= min_len]
            try:
                Z = np.array(raw, dtype=float)
            except Exception:
                return None
            if Z.size == 0:
                return None
            if Z.ndim == 1:
                Z = Z.reshape(1, -1)
            if t == "Heatmap":
                artist = base_ax.pcolormesh(Z, cmap='viridis', shading='auto')
                try:
                    base_ax.set_aspect('auto')
                    base_ax.set_xlim(0, Z.shape[1])
                    base_ax.set_ylim(0, Z.shape[0])
                except Exception:
                    pass
            elif t == "Contour":
                if Z.shape[0] < 2 or Z.shape[1] < 2:
                    txt = base_ax.text(
                        0.5, 0.5, tr.t('msg.contour_needs_matrix'),
                        ha='center', va='center',
                        transform=base_ax.transAxes, fontsize=10,
                        color='gray',
                        bbox=dict(boxstyle='round', fc='#f8f8f8',
                                  ec='gray'))
                    artist = txt
                else:
                    try:
                        artist = base_ax.contour(Z, cmap='viridis')
                        base_ax.set_aspect('auto')
                    except Exception as e:
                        txt = base_ax.text(0.5, 0.5,
                                           f"Contour error: {e}",
                                           ha='center', va='center',
                                           transform=base_ax.transAxes,
                                           fontsize=10, color='red')
                        artist = txt
            # ----- Специальные 2D -----
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

            # ------------------- Водопад -------------------
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

            # ------------------- Гант -------------------
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

            elif t in ("Treemap", "Sunburst"):
                txt = base_ax.text(
                    0.5, 0.5,
                    tr.t('misc.treemap_only_html', type=tr.type_name(t)),
                    ha='center', va='center', transform=base_ax.transAxes,
                    fontsize=12, color='gray',
                    bbox=dict(boxstyle='round', fc='#f0f0f0',
                              ec='gray', alpha=0.7))
                artist = txt

            # ------------------- Свечи (OHLC) -------------------
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

            # ------------------- Диаграмма Парето -------------------
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

            # ------------------- Step plot -------------------
            elif t == "Step plot":
                artist, = base_ax.step(x, y, where='post',
                                       color=c, lw=lw, ls=ls,
                                       label=lbl)

            # ------------------- Renko -------------------
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

            # ------------------- Point-and-Figure -------------------
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

            # ------------------- Q-Q plot -------------------
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

            # ------------------- ECDF -------------------
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

            # ------------------- Hexbin -------------------
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

            # ------------------- Strip plot -------------------
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

            # ------------------- Ridge plot (Joyplot) -------------------
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
                    fill = base_ax.fill_between(
                        xs, offset, offset + ys,
                        color=color_i, alpha=0.75,
                        edgecolor='white', linewidth=0.8,
                        label=lbl if i == 0 else None)
                    artists.append(fill)
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

            # ------------------- Raincloud plot -------------------
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

                    fill = base_ax.fill_betweenx(
                        ys, i - xs_dens, i, color=c, alpha=0.6,
                        label=lbl if i == 0 else None)
                    artists.append(fill)
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

            # ------------------- Beanplot -------------------
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

                    fill = base_ax.fill_betweenx(
                        ys, i - dens, i + dens,
                        color=c, alpha=0.5)
                    artists.append(fill)
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

            # ------------------- Swarm plot -------------------
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
                    max_width = 0.4
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

            # ------------------- Cherry blossom plot -------------------
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

            # ------------------- Dot-and-whisker -------------------
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

            # ------------------- Сезонная декомпозиция -------------------
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

            # ------------------- Rolling statistics -------------------
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
                fill = base_ax.fill_between(
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
                data['_extra_artists'] = [l_orig, fill]
                artist = l_mean

            # ------------------- Дендрограмма -------------------
            elif t == "Дендрограмма":
                try:
                    from scipy.cluster.hierarchy import (
                        linkage, dendrogram as _dendro)
                except ImportError:
                    base_ax.text(0.5, 0.5, 'scipy required',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                raw = data.get('heatmap_data', [])
                if not raw or len(raw) < 2:
                    base_ax.text(0.5, 0.5, 'Нужна матрица ≥2×N',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                row_lens = [len(r) for r in raw if r]
                if not row_lens or len(set(row_lens)) != 1:
                    base_ax.text(0.5, 0.5, 'Все строки одной длины',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                Z = np.array(raw, dtype=float)
                lines_before = set(id(ln) for ln in base_ax.lines)
                texts_before = set(id(tx) for tx in base_ax.texts)
                colls_before = set(id(cl) for cl in base_ax.collections)
                labels = data.get('pie_labels') or None
                try:
                    _dendro(Z, ax=base_ax,
                            labels=labels,
                            color_threshold=0,
                            leaf_rotation=45)
                except Exception as e:
                    base_ax.text(0.5, 0.5, f'Dendrogram error: {e}',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                new_artists = []
                for ln in base_ax.lines:
                    if id(ln) not in lines_before:
                        new_artists.append(ln)
                for tx in base_ax.texts:
                    if id(tx) not in texts_before:
                        new_artists.append(tx)
                for cl in base_ax.collections:
                    if id(cl) not in colls_before:
                        new_artists.append(cl)
                if new_artists:
                    artist = new_artists[0]
                    data['_extra_artists'] = new_artists[1:]
                else:
                    artist = None
                try:
                    base_ax.set_ylabel("Расстояние")
                except Exception:
                    pass

            # ------------------- Cluster dendrogram -------------------
            elif t == "Cluster dendrogram":
                try:
                    from scipy.cluster.hierarchy import (
                        linkage, dendrogram as _dendro,
                        leaves_list as _leaves)
                except ImportError:
                    base_ax.text(0.5, 0.5, 'scipy required',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                raw = data.get('heatmap_data', [])
                if not raw or len(raw) < 2:
                    return None
                row_lens = [len(r) for r in raw if r]
                if not row_lens or len(set(row_lens)) != 1:
                    return None
                Z = np.array(raw, dtype=float)

                try:
                    row_link = linkage(Z, method='average')
                    col_link = linkage(Z.T, method='average')
                except Exception:
                    return None

                row_order = _leaves(row_link)
                col_order = _leaves(col_link)
                Z_ord = Z[np.ix_(row_order, col_order)]

                im = base_ax.imshow(Z_ord, cmap='viridis', aspect='auto')
                base_ax.set_xticks([])
                base_ax.set_yticks([])

                try:
                    from mpl_toolkits.axes_grid1 import make_axes_locatable
                    divider = make_axes_locatable(base_ax)
                    ax_top = divider.append_axes("top", size="25%",
                                                 pad=0.05, sharex=base_ax)
                    ax_left = divider.append_axes("left", size="25%",
                                                  pad=0.05,
                                                  sharey=base_ax)
                    _dendro(col_link, ax=ax_top, no_labels=True,
                            color_threshold=0)
                    _dendro(row_link, ax=ax_left, orientation='left',
                            no_labels=True, color_threshold=0)
                    ax_top.set_xticks([])
                    ax_top.set_yticks([])
                    ax_left.set_xticks([])
                    ax_left.set_yticks([])
                    for sp in ('top', 'right', 'bottom', 'left'):
                        try:
                            ax_top.spines[sp].set_visible(False)
                            ax_left.spines[sp].set_visible(False)
                        except Exception:
                            pass

                    def _cleanup(_top=ax_top, _left=ax_left):
                        try:
                            _top.remove()
                        except Exception:
                            pass
                        try:
                            _left.remove()
                        except Exception:
                            pass

                    data['_cleanup'] = _cleanup
                except Exception:
                    pass

                try:
                    cb = base_ax.figure.colorbar(im, ax=base_ax,
                                                 shrink=0.7, pad=0.1)
                    data['_extra_artists'] = [cb]
                except Exception:
                    pass
                artist = im

            # ------------------- Sankey -------------------
            elif t == "Sankey":
                try:
                    from matplotlib.sankey import Sankey
                except ImportError:
                    base_ax.text(0.5, 0.5, 'Sankey unavailable',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                vals = np.array(y, dtype=float)
                if len(vals) < 2:
                    return None
                labels = data.get('pie_labels') or \
                         [f'F{i + 1}' for i in range(len(vals))]
                input_val = abs(vals[0]) or 1.0
                outputs = np.abs(vals[1:])
                out_sum = outputs.sum()
                if out_sum > 0:
                    outputs = outputs / out_sum * input_val
                flows = [input_val] + (-outputs).tolist()
                orientations = [1]
                for i in range(1, len(flows)):
                    orientations.append(1 if i % 2 == 1 else -1)
                labels_use = list(labels[:len(flows)])
                while len(labels_use) < len(flows):
                    labels_use.append(f'F{len(labels_use) + 1}')

                patches_before = set(id(p) for p in base_ax.patches)
                texts_before = set(id(tx) for tx in base_ax.texts)
                try:
                    sk = Sankey(ax=base_ax,
                                scale=1.0 / input_val,
                                offset=0.15,
                                format='%.0f',
                                unit=' ')
                    sk.add(flows=flows,
                           labels=labels_use,
                           orientations=orientations,
                           patchlabel=lbl)
                    sk.finish()
                except Exception as e:
                    base_ax.text(0.5, 0.5, f'Sankey error: {e}',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                new_patches = [p for p in base_ax.patches
                               if id(p) not in patches_before]
                new_texts = [tx for tx in base_ax.texts
                             if id(tx) not in texts_before]
                base_ax.axis('off')
                if new_patches:
                    artist = new_patches[0]
                    data['_extra_artists'] = new_patches[1:] + new_texts
                else:
                    artist = None
                    data['_extra_artists'] = new_texts

            # ------------------- Alluvial -------------------
            elif t == "Alluvial diagram":
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    M = np.array(raw, dtype=float)
                except Exception:
                    return None
                if M.ndim != 2:
                    return None
                n_src, n_dst = M.shape
                if n_src < 1 or n_dst < 1:
                    return None

                src_labels = data.get('pie_labels') or \
                             [f"S{i + 1}" for i in range(n_src)]
                dst_labels = data.get('dst_labels') or \
                             [f"D{j + 1}" for j in range(n_dst)]

                from matplotlib.patches import Polygon
                cmap = plt.get_cmap('tab10')
                total = M.sum()
                if total <= 0:
                    return None

                src_sums = M.sum(axis=1)
                dst_sums = M.sum(axis=0)
                h_max = 1.0
                src_h = src_sums / total * h_max
                dst_h = dst_sums / total * h_max

                gap = 0.05
                total_src_h = sum(src_h) + gap * (n_src - 1)
                total_dst_h = sum(dst_h) + gap * (n_dst - 1)
                y_src_start = -total_src_h / 2
                y_dst_start = -total_dst_h / 2

                src_pos = []
                cur = y_src_start
                for h in src_h:
                    src_pos.append((cur, cur + h))
                    cur += h + gap
                dst_pos = []
                cur = y_dst_start
                for h in dst_h:
                    dst_pos.append((cur, cur + h))
                    cur += h + gap

                x_left, x_right = 0.0, 1.0
                bar_w = 0.05

                artists = []
                for i in range(n_src):
                    y0, y1 = src_pos[i]
                    rect = plt.Rectangle(
                        (x_left, y0), bar_w, y1 - y0,
                        facecolor=cmap(i % 10),
                        edgecolor='white', zorder=3)
                    base_ax.add_patch(rect)
                    artists.append(rect)
                    t_lbl = base_ax.text(
                        x_left - 0.02, (y0 + y1) / 2,
                        str(src_labels[i]), ha='right', va='center',
                        fontsize=9)
                    artists.append(t_lbl)

                for j in range(n_dst):
                    y0, y1 = dst_pos[j]
                    rect = plt.Rectangle(
                        (x_right - bar_w, y0), bar_w, y1 - y0,
                        facecolor=cmap((j + n_src) % 10),
                        edgecolor='white', zorder=3)
                    base_ax.add_patch(rect)
                    artists.append(rect)
                    t_lbl = base_ax.text(
                        x_right + 0.02, (y0 + y1) / 2,
                        str(dst_labels[j]), ha='left', va='center',
                        fontsize=9)
                    artists.append(t_lbl)

                src_off = [0.0] * n_src
                dst_off = [0.0] * n_dst
                for i in range(n_src):
                    for j in range(n_dst):
                        if M[i, j] <= 0:
                            continue
                        h = M[i, j] / total * h_max
                        y0_src = src_pos[i][0] + src_off[i]
                        y1_src = y0_src + h
                        y0_dst = dst_pos[j][0] + dst_off[j]
                        y1_dst = y0_dst + h

                        N = 30
                        t_curve = np.linspace(0, 1, N)
                        x_curve = (x_left + bar_w +
                                   (x_right - 2 * bar_w) * t_curve)
                        y_top = ((1 - t_curve) * y1_src +
                                 t_curve * y1_dst)
                        y_bot = ((1 - t_curve) * y0_src +
                                 t_curve * y0_dst)

                        top_pts = list(zip(x_curve, y_top))
                        bot_pts = list(zip(x_curve[::-1], y_bot[::-1]))
                        poly = Polygon(top_pts + bot_pts,
                                       closed=True,
                                       facecolor=cmap(i % 10),
                                       edgecolor='none',
                                       alpha=0.4, zorder=2)
                        base_ax.add_patch(poly)
                        artists.append(poly)

                        src_off[i] += h
                        dst_off[j] += h

                base_ax.set_xlim(-0.2, 1.2)
                base_ax.set_ylim(min(y_src_start, y_dst_start) - 0.1,
                                 max(sum(src_h) + y_src_start,
                                     sum(dst_h) + y_dst_start) + 0.1)
                try:
                    base_ax.axis('off')
                except Exception:
                    pass

                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Chord -------------------
            elif t == "Chord":
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    M = np.array(raw, dtype=float)
                except Exception:
                    return None
                if M.ndim != 2 or M.shape[0] != M.shape[1] or M.shape[0] < 2:
                    base_ax.text(0.5, 0.5, 'Нужна квадратная матрица N×N',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                n = M.shape[0]
                labels = data.get('pie_labels') or \
                         [f'N{i + 1}' for i in range(n)]
                row_sums = M.sum(axis=1)
                total = row_sums.sum()
                if total <= 0:
                    return None
                gap = 0.05
                avail = 2 * np.pi - n * gap
                angles = row_sums / total * avail

                starts = []
                cur = 0.0
                for i in range(n):
                    starts.append(cur)
                    cur += angles[i] + gap

                r_inner = 0.72
                r_outer = 0.95

                from matplotlib.patches import Polygon
                cmap = plt.get_cmap('tab10')
                artists = []

                offsets_out = [0.0] * n
                offsets_in = [0.0] * n
                for i in range(n):
                    for j in range(n):
                        if i == j or M[i, j] <= 0:
                            continue
                        if row_sums[i] <= 0 or row_sums[j] <= 0:
                            continue
                        out_w = angles[i] * (M[i, j] / row_sums[i])
                        in_w = angles[j] * (M[i, j] / row_sums[j])
                        a1 = starts[i] + offsets_out[i]
                        a2 = a1 + out_w
                        b1 = starts[j] + offsets_in[j]
                        b2 = b1 + in_w
                        n_steps = 20
                        t_a = np.linspace(a1, a2, n_steps)
                        t_b = np.linspace(b1, b2, n_steps)
                        p1 = list(zip(np.cos(t_a) * r_inner,
                                      np.sin(t_a) * r_inner))
                        p2 = list(zip(np.cos(t_b) * r_inner,
                                      np.sin(t_b) * r_inner))
                        verts = p1 + p2[::-1]
                        ribbon = Polygon(verts, closed=True,
                                         facecolor=cmap(i % 10),
                                         edgecolor='none',
                                         alpha=0.45, zorder=2)
                        base_ax.add_patch(ribbon)
                        artists.append(ribbon)
                        offsets_out[i] += out_w
                        offsets_in[j] += in_w

                for i in range(n):
                    if angles[i] <= 0:
                        continue
                    th = np.linspace(starts[i], starts[i] + angles[i], 50)
                    outer = list(zip(np.cos(th) * r_outer,
                                     np.sin(th) * r_outer))
                    inner = list(zip(np.cos(th) * r_inner,
                                     np.sin(th) * r_inner))
                    poly = Polygon(outer + inner[::-1], closed=True,
                                   facecolor=cmap(i % 10),
                                   edgecolor='white', alpha=0.95,
                                   zorder=3)
                    base_ax.add_patch(poly)
                    artists.append(poly)
                    mid = starts[i] + angles[i] / 2
                    x_lbl = np.cos(mid) * (r_outer + 0.06)
                    y_lbl = np.sin(mid) * (r_outer + 0.06)
                    t_lbl = base_ax.text(x_lbl, y_lbl,
                                         str(labels[i]) if i < len(labels)
                                         else f'N{i + 1}',
                                         ha='center', va='center',
                                         fontsize=9, zorder=4)
                    artists.append(t_lbl)

                base_ax.set_xlim(-1.2, 1.2)
                base_ax.set_ylim(-1.2, 1.2)
                try:
                    base_ax.set_aspect('equal')
                    base_ax.axis('off')
                except Exception:
                    pass

                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Сетевой график -------------------
            elif t == "Сетевой график":
                try:
                    import networkx as nx
                except ImportError:
                    base_ax.text(0.5, 0.5,
                                 'Установите networkx:\n  pip install networkx',
                                 transform=base_ax.transAxes,
                                 ha='center', va='center', color='red')
                    return None
                zs = data.get('z', []) or []
                if not zs and x and y:
                    zs = []
                    for i in range(min(len(x), len(y))):
                        zs.append(f"{x[i]}-{y[i]}")
                if not zs:
                    base_ax.text(0.5, 0.5,
                                 'Нужны рёбра в поле Z (A-B; B-C; ...)',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                G = nx.Graph()
                for e in zs:
                    if not isinstance(e, str):
                        continue
                    if '-' not in e:
                        continue
                    a, b = e.split('-', 1)
                    G.add_edge(a.strip(), b.strip())
                if G.number_of_nodes() == 0:
                    return None

                layout_name = data.get('layout', 'spring')
                try:
                    if layout_name == 'circular':
                        pos = nx.circular_layout(G)
                    elif layout_name == 'kamada':
                        pos = nx.kamada_kawai_layout(G)
                    elif layout_name == 'spectral':
                        pos = nx.spectral_layout(G)
                    elif layout_name == 'shell':
                        pos = nx.shell_layout(G)
                    else:
                        pos = nx.spring_layout(G, seed=42)
                except Exception:
                    pos = nx.spring_layout(G, seed=42)

                before_patches = set(id(p) for p in base_ax.patches)
                before_lines = set(id(ln) for ln in base_ax.lines)
                before_texts = set(id(tx) for tx in base_ax.texts)
                before_colls = set(id(cl) for cl in base_ax.collections)

                try:
                    nx.draw_networkx_nodes(
                        G, pos, ax=base_ax,
                        node_size=max(50, int(ms) ** 2 * 5),
                        node_color=c, edgecolors='white',
                        linewidths=0.8, alpha=0.9)
                    nx.draw_networkx_edges(
                        G, pos, ax=base_ax,
                        edge_color='#888', width=max(0.8, lw),
                        alpha=0.7)
                    if data.get('show_labels', True):
                        nx.draw_networkx_labels(
                            G, pos, ax=base_ax, font_size=9)
                except Exception as e:
                    base_ax.text(0.5, 0.5, f'Network error: {e}',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None

                new_artists = []
                for ln in base_ax.lines:
                    if id(ln) not in before_lines:
                        new_artists.append(ln)
                for tx in base_ax.texts:
                    if id(tx) not in before_texts:
                        new_artists.append(tx)
                for cl in base_ax.collections:
                    if id(cl) not in before_colls:
                        new_artists.append(cl)

                base_ax.axis('off')
                try:
                    base_ax.set_aspect('equal')
                except Exception:
                    pass

                artist = new_artists[0] if new_artists else None
                data['_extra_artists'] = new_artists[1:] if len(new_artists) > 1 else []

            # ------------------- Hive plot -------------------
            elif t == "Hive plot":
                zs = data.get('z', []) or []
                if not zs:
                    return None
                nodes = []
                edges = []
                for e in zs:
                    if not isinstance(e, str) or '-' not in e:
                        continue
                    a, b = e.split('-', 1)
                    a, b = a.strip(), b.strip()
                    if a not in nodes:
                        nodes.append(a)
                    if b not in nodes:
                        nodes.append(b)
                    edges.append((a, b))
                if not nodes:
                    return None

                deg = {n: 0 for n in nodes}
                for a, b in edges:
                    deg[a] += 1
                    deg[b] += 1

                sorted_nodes = sorted(nodes, key=lambda nn: deg[nn])
                n_axes = 3
                axes_nodes = [[] for _ in range(n_axes)]
                for i, nd in enumerate(sorted_nodes):
                    axes_nodes[i % n_axes].append(nd)

                axis_angles = [
                    np.pi / 2,
                    np.pi / 2 + 2 * np.pi / 3,
                    np.pi / 2 + 4 * np.pi / 3,
                ]
                positions = {}
                artists = []

                for ai, axis_nodes in enumerate(axes_nodes):
                    ang = axis_angles[ai]
                    axis_ln, = base_ax.plot(
                        [0, np.cos(ang)], [0, np.sin(ang)],
                        color='gray', lw=1.0, zorder=1)
                    artists.append(axis_ln)

                    for i, nd in enumerate(axis_nodes):
                        r = (i + 1) / (len(axis_nodes) + 1)
                        xx = r * np.cos(ang)
                        yy = r * np.sin(ang)
                        positions[nd] = (xx, yy)
                        sc = base_ax.scatter(
                            [xx], [yy], s=max(30, ms ** 2 * 2),
                            color=c, edgecolors='black',
                            linewidths=0.6, zorder=5)
                        artists.append(sc)
                        t_lbl = base_ax.text(
                            xx * 1.12, yy * 1.12, str(nd),
                            ha='center', va='center', fontsize=8)
                        artists.append(t_lbl)

                from matplotlib.patches import PathPatch
                from matplotlib.path import Path
                for a, b in edges:
                    if a not in positions or b not in positions:
                        continue
                    x1, y1 = positions[a]
                    x2, y2 = positions[b]
                    cx = (x1 + x2) * 0.15
                    cy = (y1 + y2) * 0.15
                    path = Path(
                        [(x1, y1), (cx, cy), (x2, y2)],
                        [Path.MOVETO, Path.CURVE3, Path.CURVE3])
                    patch = PathPatch(
                        path, facecolor='none',
                        edgecolor=c, lw=0.8,
                        alpha=0.5, zorder=2)
                    base_ax.add_patch(patch)
                    artists.append(patch)

                base_ax.set_xlim(-1.25, 1.25)
                base_ax.set_ylim(-1.25, 1.25)
                try:
                    base_ax.set_aspect('equal')
                    base_ax.axis('off')
                except Exception:
                    pass

                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Arc diagram -------------------
            elif t == "Arc diagram":
                zs = data.get('z', []) or []
                if not zs:
                    return None
                nodes = []
                edges = []
                for e in zs:
                    if not isinstance(e, str) or '-' not in e:
                        continue
                    a, b = e.split('-', 1)
                    a, b = a.strip(), b.strip()
                    if a not in nodes:
                        nodes.append(a)
                    if b not in nodes:
                        nodes.append(b)
                    edges.append((a, b))
                if not nodes:
                    return None
                pos = {n: i for i, n in enumerate(nodes)}
                n = len(nodes)

                artists = []
                for i, name in enumerate(nodes):
                    base_ax.scatter([i], [0], s=max(40, ms ** 2 * 3),
                                    color=c, edgecolors='black',
                                    linewidths=0.8, zorder=5)
                    t_lbl = base_ax.text(i, -0.15, name,
                                         ha='center', va='top',
                                         fontsize=9)
                    artists.append(t_lbl)

                for (a, b) in edges:
                    x1, x2 = pos[a], pos[b]
                    if x1 == x2:
                        continue
                    cx = (x1 + x2) / 2
                    R = abs(x2 - x1) / 2
                    theta = np.linspace(0, np.pi, 60)
                    arc_x = cx + R * np.cos(theta)
                    arc_y = R * np.sin(theta) * 0.6
                    ln, = base_ax.plot(arc_x, arc_y, color=c,
                                       lw=max(0.7, lw * 0.6), alpha=0.7)
                    artists.append(ln)

                base_ax.axis('off')
                base_ax.set_xlim(-0.5, n - 0.5)
                base_ax.set_ylim(-0.5, max(1.5, n * 0.4))
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Дерево (tree diagram) -------------------
            elif t == "Дерево (tree diagram)":
                zs = data.get('z', []) or []
                if not zs:
                    return None
                edges = []
                children_map = {}
                parents_map = {}
                nodes = set()
                for e in zs:
                    if not isinstance(e, str) or '-' not in e:
                        continue
                    p, c_ = e.split('-', 1)
                    p, c_ = p.strip(), c_.strip()
                    if not p or not c_:
                        continue
                    edges.append((p, c_))
                    nodes.add(p)
                    nodes.add(c_)
                    children_map.setdefault(p, []).append(c_)
                    parents_map[c_] = p

                if not nodes:
                    return None
                roots = [n for n in nodes if n not in parents_map]
                if not roots:
                    roots = [list(nodes)[0]]

                level = {r: 0 for r in roots}
                for _ in range(100):
                    changed = False
                    for p, c_ in edges:
                        if p in level and (c_ not in level
                                           or level[c_] <= level[p]):
                            level[c_] = level[p] + 1
                            changed = True
                    if not changed:
                        break

                def count_leaves(nn):
                    if nn not in children_map or not children_map[nn]:
                        return 1
                    return sum(count_leaves(ch)
                               for ch in children_map[nn])

                xs_map = {}

                def assign_x(node, x_start, x_end):
                    if node not in children_map or not children_map[node]:
                        xs_map[node] = (x_start + x_end) / 2
                        return
                    chs = children_map[node]
                    total = sum(count_leaves(ch) for ch in chs)
                    cur = x_start
                    for ch in chs:
                        w = (x_end - x_start) * count_leaves(ch) / total
                        assign_x(ch, cur, cur + w)
                        cur += w
                    xs_map[node] = (xs_map[chs[0]] + xs_map[chs[-1]]) / 2

                cur_x = 0
                for r in roots:
                    w = count_leaves(r)
                    assign_x(r, cur_x, cur_x + w)
                    cur_x += w

                artists = []
                y_scale = 1.0
                for p, c_ in edges:
                    if p in xs_map and c_ in xs_map:
                        x_p = xs_map[p]
                        x_c = xs_map[c_]
                        y_p = -level[p] * y_scale
                        y_c = -level[c_] * y_scale
                        ln, = base_ax.plot(
                            [x_p, x_c], [y_p, y_c],
                            color='#888', lw=1.2, zorder=2)
                        artists.append(ln)

                for nd in nodes:
                    if nd not in xs_map:
                        continue
                    xx = xs_map[nd]
                    yy = -level.get(nd, 0) * y_scale
                    sc = base_ax.scatter(
                        [xx], [yy], s=max(60, ms ** 2 * 3),
                        color=c, edgecolors='black',
                        linewidths=0.8, zorder=4)
                    artists.append(sc)
                    t_lbl = base_ax.text(
                        xx, yy + 0.1, str(nd),
                        ha='center', va='bottom', fontsize=9)
                    artists.append(t_lbl)

                base_ax.set_xlim(-1, cur_x + 1)
                max_level = max(level.values()) if level else 0
                base_ax.set_ylim(-max_level - 0.5, 1)
                base_ax.set_xticks([])
                base_ax.set_yticks([])
                try:
                    base_ax.axis('off')
                except Exception:
                    pass
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Radial tree 3D -------------------
            elif t == "Radial tree 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                zs = data.get('z', []) or []
                if not zs:
                    return None
                edges = []
                children_map = {}
                parents_map = {}
                nodes = set()
                for e in zs:
                    if not isinstance(e, str) or '-' not in e:
                        continue
                    p, c_ = e.split('-', 1)
                    p, c_ = p.strip(), c_.strip()
                    if not p or not c_:
                        continue
                    edges.append((p, c_))
                    nodes.add(p)
                    nodes.add(c_)
                    children_map.setdefault(p, []).append(c_)
                    parents_map[c_] = p
                if not nodes:
                    return None

                roots = [n for n in nodes if n not in parents_map]
                if not roots:
                    roots = [list(nodes)[0]]

                level = {r: 0 for r in roots}
                for _ in range(100):
                    changed = False
                    for p, c_ in edges:
                        if p in level and (c_ not in level
                                           or level[c_] <= level[p]):
                            level[c_] = level[p] + 1
                            changed = True
                    if not changed:
                        break

                max_level = max(level.values()) if level else 1
                if max_level == 0:
                    max_level = 1
                radius_map = {lvl: lvl / max_level
                              for lvl in range(max_level + 1)}

                def count_leaves(nn):
                    if nn not in children_map or not children_map[nn]:
                        return 1
                    return sum(count_leaves(ch)
                               for ch in children_map[nn])

                angles = {}

                def assign_angle(node, a_start, a_end):
                    if node not in children_map or not children_map[node]:
                        angles[node] = (a_start + a_end) / 2
                        return
                    chs = children_map[node]
                    total = sum(count_leaves(ch) for ch in chs)
                    cur = a_start
                    for ch in chs:
                        w = (a_end - a_start) * count_leaves(ch) / total
                        assign_angle(ch, cur, cur + w)
                        cur += w
                    angles[node] = (angles[chs[0]] + angles[chs[-1]]) / 2

                total_leaves = sum(count_leaves(r) for r in roots)
                cur_a = 0
                for r in roots:
                    w = 2 * np.pi * count_leaves(r) / total_leaves
                    assign_angle(r, cur_a, cur_a + w)
                    cur_a += w

                z_offset = float(x[0]) if x and len(x) >= 1 else 0.2
                if z_offset <= 0:
                    z_offset = 0.2

                pos3d = {}
                for nd in nodes:
                    if nd not in angles:
                        continue
                    a = angles[nd]
                    lvl = level.get(nd, 0)
                    r = radius_map.get(lvl, 0)
                    pos3d[nd] = (
                        r * np.cos(a),
                        r * np.sin(a),
                        lvl * z_offset,
                    )

                artists = []
                for p, c_ in edges:
                    if p not in pos3d or c_ not in pos3d:
                        continue
                    x1, y1, z1 = pos3d[p]
                    x2, y2, z2 = pos3d[c_]
                    ln, = base_ax.plot3D(
                        [x1, x2], [y1, y2], [z1, z2],
                        color='#888', lw=1.0, zorder=2)
                    artists.append(ln)

                for nd, (px, py, pz) in pos3d.items():
                    sc = base_ax.scatter3D(
                        [px], [py], [pz],
                        s=max(30, ms ** 2 * 2),
                        color=c, edgecolors='black',
                        depthshade=True, zorder=4)
                    artists.append(sc)
                    if nd not in children_map or not children_map[nd]:
                        t_lbl = base_ax.text(
                            px * 1.1, py * 1.1, pz,
                            str(nd), ha='center', va='center',
                            fontsize=7)
                        artists.append(t_lbl)

                base_ax.set_xlabel("X")
                base_ax.set_ylabel("Y")
                base_ax.set_zlabel("Уровень")

                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Circle packing -------------------
            elif t == "Circle packing":
                y_arr = np.array(y, dtype=float) if y else np.array([])
                if len(y_arr) < 1:
                    return None
                if isinstance(x, list) and x and isinstance(x[0], str):
                    labels = [str(v) for v in x]
                elif data.get('pie_labels'):
                    labels = [str(v) for v in data['pie_labels']]
                else:
                    labels = [f"C{i + 1}" for i in range(len(y_arr))]
                while len(labels) < len(y_arr):
                    labels.append(f"C{len(labels) + 1}")
                labels = labels[:len(y_arr)]

                vmax = float(y_arr.max())
                if vmax <= 0:
                    vmax = 1.0
                radii = np.sqrt(y_arr / vmax) * 0.3
                order = np.argsort(-radii)
                cmap = plt.get_cmap('tab20')
                artists = []

                cols = max(1, int(np.ceil(np.sqrt(len(radii)))))
                placed = []
                for idx in order:
                    r = radii[idx]
                    placed_flag = False
                    for row in range(20):
                        for col in range(cols + 5):
                            cx = col * 0.65 + 0.5
                            cy = row * 0.65 + 0.5
                            ok = True
                            for (px, py, pr) in placed:
                                if (cx - px) ** 2 + (cy - py) ** 2 < \
                                        (r + pr + 0.02) ** 2:
                                    ok = False
                                    break
                            if ok:
                                placed.append((cx, cy, r))
                                color_i = cmap(int(idx) % 20)
                                circ = plt.Circle(
                                    (cx, cy), r,
                                    facecolor=color_i,
                                    edgecolor='white',
                                    linewidth=1.2,
                                    alpha=0.9, zorder=3)
                                base_ax.add_patch(circ)
                                artists.append(circ)
                                if r > 0.06:
                                    t_lbl = base_ax.text(
                                        cx, cy, labels[idx],
                                        ha='center', va='center',
                                        fontsize=max(6, int(r * 25)),
                                        color='white',
                                        fontweight='bold',
                                        zorder=4)
                                    artists.append(t_lbl)
                                placed_flag = True
                                break
                        if placed_flag:
                            break

                if not placed:
                    return None

                xs_pl = [p[0] for p in placed]
                ys_pl = [p[1] for p in placed]
                rs_pl = [p[2] for p in placed]
                base_ax.set_xlim(min(xs_pl) - max(rs_pl) - 0.2,
                                 max(xs_pl) + max(rs_pl) + 0.2)
                base_ax.set_ylim(min(ys_pl) - max(rs_pl) - 0.2,
                                 max(ys_pl) + max(rs_pl) + 0.2)
                try:
                    base_ax.set_aspect('equal')
                    base_ax.axis('off')
                except Exception:
                    pass
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Adjacency matrix -------------------
            elif t == "Adjacency matrix":
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    M = np.array(raw, dtype=float)
                except Exception:
                    return None
                if M.ndim != 2 or M.shape[0] != M.shape[1]:
                    base_ax.text(0.5, 0.5,
                                 'Нужна квадратная матрица N×N',
                                 transform=base_ax.transAxes,
                                 ha='center', color='red')
                    return None
                n = M.shape[0]
                labels = data.get('pie_labels') or \
                         [f"N{i + 1}" for i in range(n)]
                if len(labels) < n:
                    labels = list(labels) + \
                             [f"N{i + 1}" for i in range(len(labels), n)]
                labels = labels[:n]

                if data.get('reorder', True):
                    deg = M.sum(axis=1)
                    order = np.argsort(-deg)
                    M_plot = M[np.ix_(order, order)]
                    labels_plot = [labels[i] for i in order]
                else:
                    M_plot = M
                    labels_plot = labels

                artist = base_ax.imshow(
                    M_plot, cmap='viridis',
                    aspect='equal', interpolation='nearest')
                base_ax.set_xticks(range(n))
                base_ax.set_yticks(range(n))
                base_ax.set_xticklabels(labels_plot,
                                        rotation=45, ha='right',
                                        fontsize=8)
                base_ax.set_yticklabels(labels_plot, fontsize=8)
                base_ax.set_title("Adjacency matrix")

                try:
                    cb = base_ax.figure.colorbar(artist, ax=base_ax,
                                                 shrink=0.7, pad=0.02)
                    data['_extra_artists'] = [cb]
                except Exception:
                    pass

            # ------------------- Mapper algorithm -------------------
            elif t == "Mapper algorithm":
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    M = np.array(raw, dtype=float)
                except Exception:
                    return None
                if M.ndim != 2:
                    return None
                n_pts, n_dims = M.shape
                if n_pts < 3:
                    return None

                n_clusters = max(2, min(n_pts, int(data.get('bins', 5))))

                mn = M.min(axis=0)
                mx = M.max(axis=0)
                rng_v = np.where(mx > mn, mx - mn, 1.0)
                Mn = (M - mn) / rng_v

                rng_np = np.random.default_rng(42)
                idx_init = rng_np.choice(n_pts, n_clusters, replace=False)
                centers = Mn[idx_init].copy()
                labels_arr = np.zeros(n_pts, dtype=int)
                for _ in range(50):
                    dists = np.linalg.norm(
                        Mn[:, None, :] - centers[None, :, :], axis=-1)
                    new_labels = np.argmin(dists, axis=1)
                    if np.array_equal(new_labels, labels_arr):
                        break
                    labels_arr = new_labels
                    for k in range(n_clusters):
                        mask = labels_arr == k
                        if mask.any():
                            centers[k] = Mn[mask].mean(axis=0)

                angles = np.linspace(0, 2 * np.pi, n_clusters,
                                     endpoint=False)
                pos = {k: (np.cos(a), np.sin(a))
                       for k, a in enumerate(angles)}

                sizes = [int(np.sum(labels_arr == k)) for k in range(n_clusters)]
                max_size = max(sizes) if sizes else 1

                artists = []
                edges_set = set()
                for i in range(n_clusters):
                    for j in range(i + 1, n_clusters):
                        d = np.linalg.norm(centers[i] - centers[j])
                        if d < 0.5 and sizes[i] > 0 and sizes[j] > 0:
                            edges_set.add((i, j))

                for (i, j) in edges_set:
                    x1, y1 = pos[i]
                    x2, y2 = pos[j]
                    ln, = base_ax.plot([x1, x2], [y1, y2],
                                       color='#888', lw=2.0,
                                       alpha=0.7, zorder=1)
                    artists.append(ln)

                cmap_m = plt.get_cmap('tab10')
                for k in range(n_clusters):
                    if sizes[k] == 0:
                        continue
                    xx, yy = pos[k]
                    sz = 200 + 800 * sizes[k] / max_size
                    sc = base_ax.scatter(
                        [xx], [yy], s=sz,
                        color=cmap_m(k % 10),
                        edgecolors='white', linewidths=1.5,
                        alpha=0.85, zorder=3,
                        label=lbl if k == 0 else None)
                    artists.append(sc)
                    t_lbl = base_ax.text(
                        xx, yy, f"K{k + 1}\n{sizes[k]}",
                        ha='center', va='center',
                        color='white', fontsize=9,
                        fontweight='bold', zorder=4)
                    artists.append(t_lbl)

                base_ax.set_aspect('equal')
                base_ax.set_xticks([])
                base_ax.set_yticks([])
                try:
                    base_ax.axis('off')
                except Exception:
                    pass
                base_ax.set_title("Mapper (упрощённый)")
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Stream plot -------------------
            elif t == "Stream plot":
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

            # ------------------- Streamlines -------------------
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

            # ------------------- 3D Quiver -------------------
            elif t == "3D Quiver":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                xs = np.array(x, dtype=float)
                ys = np.array(y, dtype=float)
                zs = np.array(data.get('z', []), dtype=float)
                n = min(len(xs), len(ys), len(zs))
                if n < 1:
                    return None
                xs, ys, zs = xs[:n], ys[:n], zs[:n]
                U = np.array(data.get('yerr', []), dtype=float)
                if len(U) != n:
                    U = np.ones(n)
                V = np.zeros(n)
                W = np.zeros(n)
                scale = float(data.get('quiver_scale', 1.0))
                try:
                    artist = base_ax.quiver(
                        xs, ys, zs, U * scale, V, W,
                        color=c, lw=max(0.8, lw * 0.7),
                        arrow_length_ratio=0.15,
                        label=lbl)
                except Exception:
                    return None

            # ------------------- Bode plot -------------------
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

            # ------------------- Smith chart -------------------
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

            # ------------------- Nyquist plot -------------------
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

            # ------------------- Root locus -------------------
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

            # ------------------- Constellation diagram -------------------
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

            # ------------------- Ribbon plot 3D -------------------
            elif t == "Ribbon plot 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                xs = np.array(x, dtype=float)
                ys = np.array(y, dtype=float)
                zs = np.array(data.get('z', []), dtype=float)
                n = min(len(xs), len(ys), len(zs))
                if n < 2:
                    return None
                xs, ys, zs = xs[:n], ys[:n], zs[:n]
                width = max(0.05, float(data.get('bins', 1)) * 0.05)
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                verts = []
                for i in range(n - 1):
                    verts.append([
                        (xs[i], ys[i] - width, zs[i]),
                        (xs[i + 1], ys[i + 1] - width, zs[i + 1]),
                        (xs[i + 1], ys[i + 1] + width, zs[i + 1]),
                        (xs[i], ys[i] + width, zs[i]),
                    ])
                poly = Poly3DCollection(verts, facecolor=c, edgecolor='none',
                                        alpha=0.75)
                base_ax.add_collection3d(poly)
                base_ax.set_xlim(xs.min(), xs.max())
                base_ax.set_ylim(ys.min() - width, ys.max() + width)
                base_ax.set_zlim(zs.min(), zs.max())
                artist = poly

            # ------------------- Waterfall spectrogram 3D -------------------
            elif t == "Waterfall spectrogram 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    Z = np.array(raw, dtype=float)
                except Exception:
                    return None
                m, n_cols = Z.shape
                xs_axis = (np.array(x, dtype=float)
                           if x and len(x) == n_cols
                           else np.arange(n_cols))
                ys_axis = (np.array(y, dtype=float)
                           if y and len(y) == m
                           else np.arange(m))
                artists = []
                fill = data.get('fill', True)
                for i in range(m):
                    ln, = base_ax.plot(xs_axis, np.full(n_cols, ys_axis[i]),
                                       Z[i], color=c,
                                       lw=max(0.8, lw))
                    artists.append(ln)
                    if fill:
                        try:
                            base_ax.add_collection3d(
                                Poly3DCollection(
                                    [list(zip(xs_axis,
                                              np.full(n_cols, ys_axis[i]),
                                              Z[i])) +
                                     list(zip(xs_axis[::-1],
                                              np.full(n_cols, ys_axis[i]),
                                              np.zeros(n_cols)))],
                                    facecolor=c, alpha=0.25,
                                    edgecolor='none'))
                        except Exception:
                            pass

                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Riemann surface 3D -------------------
            elif t == "Riemann surface 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                formula = data.get('z')
                if not isinstance(formula, str):
                    formula = "sqrt(z)"

                x_range = (self._parse_data(self.entry_x.get())
                           if hasattr(self, 'entry_x') else [])
                y_range = (self._parse_data(self.entry_y.get())
                           if hasattr(self, 'entry_y') else [])
                try:
                    rmin = float(x_range[0]) if len(x_range) >= 1 else 0.1
                    rmax = float(x_range[-1]) if len(x_range) >= 2 else 2.0
                    if rmax <= rmin:
                        rmax = rmin + 1.0
                except Exception:
                    rmin, rmax = 0.1, 2.0

                r_vals = np.linspace(rmin, rmax, 60)
                th_vals = np.linspace(0, 2 * np.pi, 120)
                R, TH = np.meshgrid(r_vals, th_vals)
                Z = R * np.exp(1j * TH)
                try:
                    W = eval(formula, {"__builtins__": {}},
                             {"z": Z, "np": np, "sqrt": np.sqrt,
                              "log": np.log, "exp": np.exp,
                              "sin": np.sin, "cos": np.cos,
                              "tan": np.tan, "abs": np.abs,
                              "pi": np.pi})
                    W = np.broadcast_to(W, Z.shape)
                except Exception:
                    return None

                X_out = R * np.cos(TH)
                Y_out = R * np.sin(TH)
                Z_out = np.real(W)
                try:
                    artist = base_ax.plot_surface(
                        X_out, Y_out, Z_out,
                        facecolors=plt.get_cmap('viridis')(
                            (np.angle(W) + np.pi) / (2 * np.pi)),
                        edgecolor='none', alpha=0.9)
                except Exception:
                    return None

            # ------------------- Joyplot 3D -------------------
            elif t == "Joyplot 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                groups = data.get('box_data', [])
                if not groups:
                    return None
                try:
                    from scipy.stats import gaussian_kde
                except ImportError:
                    return None
                labels = data.get('pie_labels', [])
                n = len(groups)
                all_vals = np.concatenate([np.array(g, dtype=float)
                                           for g in groups if len(g) > 1])
                if len(all_vals) == 0:
                    return None
                xmin, xmax = np.nanmin(all_vals), np.nanmax(all_vals)
                pad = (xmax - xmin) * 0.1 or 1.0
                xs = np.linspace(xmin - pad, xmax + pad, 200)
                artists = []
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
                    ys = ys / ys.max() * 0.7 if ys.max() > 0 else ys
                    offset = (n - 1 - i) * 0.8
                    ln, = base_ax.plot3D(xs, np.full_like(xs, offset),
                                         offset + ys, color=c,
                                         lw=max(1.0, lw))
                    artists.append(ln)
                    lbl_use = labels[i] if i < len(labels) else f"Группа {i + 1}"
                    base_ax.text(xmin - pad * 0.5, offset, offset,
                                 lbl_use, fontsize=8)
                base_ax.set_ylim(-0.5, n * 0.8)
                artist = artists[0] if artists else None
                data['_extra_artists'] = artists[1:] if len(artists) > 1 else []

            # ------------------- Isosurface 3D -------------------
            elif t == "Isosurface 3D":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                raw = data.get('heatmap_data', [])
                if not raw:
                    return None
                try:
                    Z = np.array(raw, dtype=float)
                except Exception:
                    return None
                if Z.ndim != 2 or Z.shape[0] < 3 or Z.shape[1] < 3:
                    return None
                level = float(data.get('bins', 0.5))
                m, n = Z.shape
                xg = np.linspace(0, 1, n)
                yg = np.linspace(0, 1, m)
                X, Y = np.meshgrid(xg, yg)
                try:
                    artist = base_ax.contour3D(X, Y, Z,
                                               levels=[level],
                                               colors=c,
                                               linewidths=max(0.8, lw))
                except Exception:
                    artist = base_ax.plot_surface(X, Y, Z, cmap='viridis',
                                                  edgecolor='none', alpha=0.85)

            # ------------------- Choropleth -------------------
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

            # ------------------- Flow map -------------------
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

            # ------------------- Isopleth -------------------
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

            # ------------------- Cartogram -------------------
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

            # ------------------- Dot density map -------------------
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

            # ------------------- Hodograph -------------------
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

            # ------------------- Роза ветров -------------------
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

            # ------------------- Skew-T log-P -------------------
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

            # ------------------- Thermodynamic diagram -------------------
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

            # ------------------- Диаграмма Вороного -------------------
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

            # ------------------- Выпуклая оболочка -------------------
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

                fill = base_ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                                    color='red', alpha=0.1, zorder=1)
                artists.append(fill)

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

            # ------------------- Alpha shape -------------------
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

            # ------------------- Volcano plot -------------------
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

            # ------------------- ROC curve -------------------
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
                fill = base_ax.fill_between(
                    fpr, 0, tpr,
                    color=c, alpha=0.15, zorder=1)
                artists.append(fill)

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

            # ------------------- Manhattan plot -------------------
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

            # ------------------- MA plot -------------------
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

            # ------------------- Recurrence plot -------------------
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

            # ------------------- Cobweb plot -------------------
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

            # ------------------- Poincaré plot -------------------
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

            # ------------------- Phase portrait -------------------
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

            # ------------------- 3D Линия -------------------
            elif t == "3D Линия":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                artist, = base_ax.plot3D(x, y, data['z'], label=lbl, color=c,
                                         lw=lw, ls=ls, marker=marker,
                                         markersize=ms)
                if fill:
                    try:
                        zs = data['z']
                        zmin = min(zs) if zs else 0
                        verts = [list(zip(x, y, zs)) +
                                 list(zip(x[::-1], y[::-1],
                                          [zmin] * len(x)))]
                        poly = Poly3DCollection(verts, alpha=0.3,
                                                facecolor=c,
                                                edgecolor='none')
                        base_ax.add_collection3d(poly)
                        artist = [artist, poly]
                    except Exception:
                        pass

            # ------------------- 3D Точечная -------------------
            elif t == "3D Точечная":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                extra = []
                if glow:
                    try:
                        g1 = base_ax.scatter3D(x, y, data['z'], color=c,
                                               s=ms ** 2 * 6, alpha=0.10)
                        g2 = base_ax.scatter3D(x, y, data['z'], color=c,
                                               s=ms ** 2 * 3, alpha=0.25)
                        extra.extend([g1, g2])
                    except Exception:
                        pass
                artist = base_ax.scatter3D(x, y, data['z'], label=lbl,
                                           color=c, s=ms ** 2, marker=marker)
                data['_extra_artists'] = extra

            # ------------------- 3D Столбчатая -------------------
            elif t == "3D Столбчатая":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                xs = np.array(x, dtype=float)
                ys = np.array(y, dtype=float)
                zs = np.array(data['z'], dtype=float)
                n = min(len(xs), len(ys), len(zs))
                xs, ys, zs = xs[:n], ys[:n], zs[:n]
                artist = base_ax.bar3d(xs, ys, np.zeros_like(zs),
                                       0.8, 0.8, zs, color=c, alpha=0.85)

            # ------------------- 3D Гистограмма -------------------
            elif t == "3D Гистограмма":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                xs = np.array(x, dtype=float)
                ys = np.array(y, dtype=float) if y else np.array(x, dtype=float)
                n = min(len(xs), len(ys))
                xs, ys = xs[:n], ys[:n]
                hist, xe, ye = np.histogram2d(xs, ys,
                                              bins=data.get('bins', 10))
                xp, yp = np.meshgrid(xe[:-1], ye[:-1])
                xp, yp = xp.ravel(), yp.ravel()
                dx = (xe[1] - xe[0]) if len(xe) > 1 else 1.0
                dy = (ye[1] - ye[0]) if len(ye) > 1 else 1.0
                artist = base_ax.bar3d(xp, yp,
                                       np.zeros_like(hist.ravel()),
                                       dx, dy, hist.ravel(),
                                       color=c, alpha=0.85)

            # ------------------- 3D Круговая -------------------
            elif t == "3D Круговая":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                vals = np.array(y, dtype=float)
                if vals.sum() <= 0:
                    return None
                fracs = vals / vals.sum()
                cols = data.get('pie_colors', [])
                if not cols or len(cols) != len(vals):
                    cmap = plt.get_cmap('tab10')
                    cols = [cmap(i % 10) for i in range(len(vals))]
                group = []
                theta0 = 0.0
                for frac, col in zip(fracs, cols):
                    dth = 2 * np.pi * frac
                    th = np.linspace(theta0, theta0 + dth, 30)
                    pts = [(0.0, 0.0)] + [(np.cos(a), np.sin(a)) for a in th]
                    top = [(p[0], p[1], 0.15) for p in pts]
                    bot = [(p[0], p[1], 0.0) for p in pts]
                    pt = Poly3DCollection([top], facecolor=col,
                                          edgecolor='k', alpha=0.9)
                    pb = Poly3DCollection([bot], facecolor=col,
                                          edgecolor='k', alpha=0.9)
                    sides = [[bot[k], bot[k + 1], top[k + 1], top[k]]
                             for k in range(len(pts) - 1)]
                    sides.append([bot[0], bot[-1], top[-1], top[0]])
                    ps = Poly3DCollection(sides, facecolor=col,
                                          edgecolor='k', alpha=0.9)
                    base_ax.add_collection3d(pt)
                    base_ax.add_collection3d(pb)
                    base_ax.add_collection3d(ps)
                    group.append((pt, pb, ps))
                    theta0 += dth
                try:
                    base_ax.set_xlim(-1.2, 1.2)
                    base_ax.set_ylim(-1.2, 1.2)
                    base_ax.set_zlim(0, 0.5)
                except Exception:
                    pass
                artist = group

            # ------------------- 3D Поверхность / 3D Сетка -------------------
            elif t in ("3D Поверхность", "3D Сетка"):
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                Z = np.array(data.get('heatmap_data', []), dtype=float)
                if Z.size == 0:
                    zz = np.array(data.get('z', []), dtype=float)
                    if zz.size == 0:
                        return None
                    side = int(np.ceil(np.sqrt(zz.size)))
                    pad = side * side - zz.size
                    if pad > 0:
                        zz = np.concatenate([zz, np.zeros(pad)])
                    Z = zz.reshape(side, side)
                if Z.ndim == 1:
                    Z = Z.reshape(1, -1)
                m, n = Z.shape
                xg = (np.array(x, dtype=float) if x and len(x) == n
                      else np.arange(n))
                yg = (np.array(y, dtype=float) if y and len(y) == m
                      else np.arange(m))
                X, Y = np.meshgrid(xg, yg)
                try:
                    if t == "3D Поверхность":
                        artist = base_ax.plot_surface(
                            X, Y, Z, cmap='viridis',
                            edgecolor='none', alpha=0.9)
                    else:
                        artist = base_ax.plot_wireframe(X, Y, Z,
                                                        color=c, lw=lw)
                except Exception:
                    return None

            # ------------------- 3D Полигон -------------------
            elif t == "3D Полигон":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                zs = data.get('z', [])
                if not x or not y or not zs:
                    return None
                try:
                    n = min(len(x), len(y), len(zs))
                    if n < 3:
                        return None
                    pts = list(zip(x[:n], y[:n], zs[:n]))
                    poly = Poly3DCollection([pts], facecolor=c, edgecolor='k',
                                            alpha=0.7, linewidths=lw)
                    base_ax.add_collection3d(poly)
                    verts = base_ax.scatter3D([p[0] for p in pts],
                                              [p[1] for p in pts],
                                              [p[2] for p in pts],
                                              color=c, s=ms ** 2,
                                              edgecolors='k',
                                              depthshade=True, zorder=5)
                    artist = [poly, verts]
                except Exception:
                    return None

            # ------------------- 3D Триангуляция -------------------
            elif t == "3D Триангуляция":
                if not hasattr(base_ax, 'get_zlim'):
                    return None
                zs = data.get('z', [])
                if not x or not y or not zs:
                    return None
                try:
                    xs = np.array(x, dtype=float)
                    ys = np.array(y, dtype=float)
                    zz = np.array(zs, dtype=float)
                    n = min(len(xs), len(ys), len(zz))
                    if n < 3:
                        return None
                    xs, ys, zz = xs[:n], ys[:n], zz[:n]
                    try:
                        artist = base_ax.plot_trisurf(xs, ys, zz,
                                                      cmap='viridis',
                                                      edgecolor='none',
                                                      alpha=0.9,
                                                      linewidth=0, label=lbl)
                    except Exception:
                        artist = base_ax.scatter3D(xs, ys, zz, color=c,
                                                   s=ms ** 2, label=lbl)
                except Exception:
                    return None

            # ------------------- Вафельная диаграмма -------------------
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
                        c = idx % cols
                        rect = plt.Rectangle(
                            (c + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
                            facecolor=col, edgecolor='white',
                            linewidth=1, zorder=3)
                        target_ax.add_patch(rect)
                        artists.append(rect)
                        idx += 1

                while idx < n_cells:
                    r = idx // cols
                    c = idx % cols
                    rect = plt.Rectangle(
                        (c + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
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

        # ------------------- Сосулька (icicle) -------------------
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

        # ------------------- Диаграмма Аргана -------------------
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

        # ------------------- Диаграмма Тейлора -------------------
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

        # ------------------- Горизонтальная столбчатая -------------------
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

        # ------------------- Горизонтальная линия -------------------
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

        # ------------------- Pie of pie -------------------
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
            pie_labels = list(small_labels) + ['...']
            pie_colors_list = list(small_colors) + ['#cccccc']

            artists = []
            w1, t1, a1 = target_ax.pie(
                pie_vals, labels=pie_labels, colors=pie_colors_list,
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

        # ------------------- Топографический профиль -------------------
        elif t == "Топографический профиль":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]

            artists = []
            fill = target_ax.fill_between(
                x_arr, y_arr.min() - 1, y_arr,
                color=c, alpha=0.35, zorder=2)
            artists.append(fill)
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

        # ------------------- Вейвлет-скейлограмма -------------------
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

        # ====================================================================
        # НОВЫЕ ТИПЫ
        # ====================================================================

        # ------------------- Вафельная диаграмма -------------------
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
                    c = idx % cols
                    rect = plt.Rectangle(
                        (c + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
                        facecolor=col, edgecolor='white',
                        linewidth=1, zorder=3)
                    target_ax.add_patch(rect)
                    artists.append(rect)
                    idx += 1

            while idx < n_cells:
                r = idx // cols
                c = idx % cols
                rect = plt.Rectangle(
                    (c + 0.05, rows - r - 1 + 0.05), 0.9, 0.9,
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

        # ------------------- Сосулька (icicle) -------------------
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

        # ------------------- Диаграмма Аргана -------------------
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

        # ------------------- Диаграмма Тейлора -------------------
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

        # ------------------- Горизонтальная столбчатая -------------------
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

        # ------------------- Горизонтальная линия -------------------
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

        # ------------------- Pie of pie -------------------
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
            pie_labels = list(small_labels) + ['...']
            pie_colors_list = list(small_colors) + ['#cccccc']

            artists = []
            w1, t1, a1 = target_ax.pie(
                pie_vals, labels=pie_labels, colors=pie_colors_list,
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

        # ------------------- Топографический профиль -------------------
        elif t == "Топографический профиль":
            x_arr = np.array(x, dtype=float)
            y_arr = np.array(y, dtype=float)
            n = min(len(x_arr), len(y_arr))
            if n < 2:
                return None
            x_arr, y_arr = x_arr[:n], y_arr[:n]

            artists = []
            fill = target_ax.fill_between(
                x_arr, y_arr.min() - 1, y_arr,
                color=c, alpha=0.35, zorder=2)
            artists.append(fill)
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

        # ------------------- Вейвлет-скейлограмма -------------------
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

        # ------------------- Fallback -------------------
        else:
            artist, = target_ax.plot(x, y, label=lbl, color=c)

        return artist