"""3D-графики.

Миксин для CreateArtistMixin. Вызывается из _create_artist._draw_3d()
для типов из TYPES_3D.

Все типы требуют axes с projection='3d' (проверка: hasattr(ax, 'get_zlim')).
target_ax не используется: для 3D-осей use_y2 блокируется в _create_artist.
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


TYPES_3D = frozenset({
    "3D Линия",
    "3D Точечная",
    "3D Столбчатая",
    "3D Гистограмма",
    "3D Круговая",
    "3D Поверхность",
    "3D Сетка",
    "3D Полигон",
    "3D Триангуляция",
    "3D Quiver",
    "Ribbon plot 3D",
    "Waterfall spectrogram 3D",
    "Riemann surface 3D",
    "Joyplot 3D",
    "Isosurface 3D",
    "Radial tree 3D",
})


class Artists3DMixin:

    def _draw_3d(self, data, base_ax, target_ax):
        """Рисует 3D-график. Возвращает artist или None."""
        # Все 3D-типы требуют 3D-осей
        if not hasattr(base_ax, 'get_zlim'):
            return None

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
        fill = data.get('fill', False)
        glow = data.get('glow', False)

        artist = None

        # ====================================================================
        # 3D Линия
        # ====================================================================
        if t == "3D Линия":
            artist, = base_ax.plot3D(x, y, z, label=lbl, color=c,
                                     lw=lw, ls=ls, marker=marker,
                                     markersize=ms)
            if fill:
                try:
                    zs = data.get('z', [])
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

        # ====================================================================
        # 3D Точечная
        # ====================================================================
        elif t == "3D Точечная":
            extra = []
            if glow:
                try:
                    g1 = base_ax.scatter3D(x, y, z, color=c,
                                           s=ms ** 2 * 6, alpha=0.10)
                    g2 = base_ax.scatter3D(x, y, z, color=c,
                                           s=ms ** 2 * 3, alpha=0.25)
                    extra.extend([g1, g2])
                except Exception:
                    pass
            artist = base_ax.scatter3D(x, y, z, label=lbl,
                                       color=c, s=ms ** 2, marker=marker)
            data['_extra_artists'] = extra

        # ====================================================================
        # 3D Столбчатая
        # ====================================================================
        elif t == "3D Столбчатая":
            xs = np.array(x, dtype=float)
            ys = np.array(y, dtype=float)
            zs = np.array(z, dtype=float)
            n = min(len(xs), len(ys), len(zs))
            if n < 1:
                return None
            xs, ys, zs = xs[:n], ys[:n], zs[:n]
            artist = base_ax.bar3d(xs, ys, np.zeros_like(zs),
                                   0.8, 0.8, zs, color=c, alpha=0.85)

        # ====================================================================
        # 3D Гистограмма
        # ====================================================================
        elif t == "3D Гистограмма":
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

        # ====================================================================
        # 3D Круговая
        # ====================================================================
        elif t == "3D Круговая":
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

        # ====================================================================
        # 3D Поверхность / 3D Сетка
        # ====================================================================
        elif t in ("3D Поверхность", "3D Сетка"):
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

        # ====================================================================
        # 3D Полигон
        # ====================================================================
        elif t == "3D Полигон":
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

        # ====================================================================
        # 3D Триангуляция
        # ====================================================================
        elif t == "3D Триангуляция":
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

        # ====================================================================
        # 3D Quiver
        # ====================================================================
        elif t == "3D Quiver":
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

        # ====================================================================
        # Ribbon plot 3D
        # ====================================================================
        elif t == "Ribbon plot 3D":
            xs = np.array(x, dtype=float)
            ys = np.array(y, dtype=float)
            zs = np.array(data.get('z', []), dtype=float)
            n = min(len(xs), len(ys), len(zs))
            if n < 2:
                return None
            xs, ys, zs = xs[:n], ys[:n], zs[:n]
            width = max(0.05, float(data.get('bins', 1)) * 0.05)
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

        # ====================================================================
        # Waterfall spectrogram 3D
        # ====================================================================
        elif t == "Waterfall spectrogram 3D":
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
            fill_area = data.get('fill', True)
            for i in range(m):
                ln, = base_ax.plot(xs_axis, np.full(n_cols, ys_axis[i]),
                                   Z[i], color=c,
                                   lw=max(0.8, lw))
                artists.append(ln)
                if fill_area:
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

        # ====================================================================
        # Riemann surface 3D
        # ====================================================================
        elif t == "Riemann surface 3D":
            formula = data.get('z')
            if not isinstance(formula, str):
                formula = "sqrt(z)"

            # Диапазон r берём из data['x'] (это [rmin, rmax]).
            # НЕ используем self._parse_data — в MockApp его нет.
            x_range = data.get('x')
            if not isinstance(x_range, list) or not x_range:
                x_range = []
            try:
                rmin = float(x_range[0]) if len(x_range) >= 1 else 0.1
                rmax = float(x_range[-1]) if len(x_range) >= 2 else 2.0
                if rmax <= rmin:
                    rmax = rmin + 1.0
            except (ValueError, TypeError, IndexError):
                rmin, rmax = 0.1, 2.0

            r_vals = np.linspace(rmin, rmax, 60)
            th_vals = np.linspace(0, 2 * np.pi, 120)
            R, TH = np.meshgrid(r_vals, th_vals)
            Z_complex = R * np.exp(1j * TH)
            try:
                W = eval(formula, {"__builtins__": {}},
                         {"z": Z_complex, "np": np, "sqrt": np.sqrt,
                          "log": np.log, "exp": np.exp,
                          "sin": np.sin, "cos": np.cos,
                          "tan": np.tan, "abs": np.abs,
                          "pi": np.pi})
                W = np.broadcast_to(W, Z_complex.shape)
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

        # ====================================================================
        # Joyplot 3D
        # ====================================================================
        elif t == "Joyplot 3D":
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

        # ====================================================================
        # Isosurface 3D
        # ====================================================================
        elif t == "Isosurface 3D":
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

        # ====================================================================
        # Radial tree 3D
        # ====================================================================
        elif t == "Radial tree 3D":
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

        return artist