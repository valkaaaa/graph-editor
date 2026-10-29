"""Матричные, сетевые и иерархические графики.

Миксин для CreateArtistMixin. Вызывается из _create_artist._draw_network()
для типов из TYPES_NETWORK.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


TYPES_NETWORK = frozenset({
    # Матричные
    "Heatmap", "Contour", "Imshow",
    # Иерархия
    "Дендрограмма", "Cluster dendrogram",
    "Circle packing",
    # Потоки
    "Sankey", "Alluvial diagram", "Chord",
    # Сети
    "Сетевой график", "Hive plot", "Arc diagram",
    "Дерево (tree diagram)",
    "Adjacency matrix",
    "Mapper algorithm",
})


class ArtistsNetworkMixin:

    def _draw_network(self, data, base_ax, target_ax):
        """Рисует матричный / сетевой график. Возвращает artist или None."""
        t = data['type']
        c = data['color']
        lbl = data['label']
        x = data['x']
        y = data['y']
        z = data.get('z', [])
        lw = data.get('lw', 2.0)
        ms = data.get('ms', 6.0)

        artist = None

        # ====================================================================
        # МАТРИЧНЫЕ
        # ====================================================================
        if t in ("Heatmap", "Contour", "Imshow"):
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
            elif t == "Imshow":
                artist = base_ax.imshow(
                    Z, cmap='viridis', aspect='auto',
                    interpolation='nearest')
            elif t == "Contour":
                if Z.shape[0] < 2 or Z.shape[1] < 2:
                    artist = base_ax.text(
                        0.5, 0.5, "Contour needs a matrix ≥2×2",
                        ha='center', va='center',
                        transform=base_ax.transAxes, fontsize=10,
                        color='gray',
                        bbox=dict(boxstyle='round', fc='#f8f8f8',
                                  ec='gray'))
                else:
                    try:
                        artist = base_ax.contour(Z, cmap='viridis')
                        base_ax.set_aspect('auto')
                    except Exception as e:
                        artist = base_ax.text(
                            0.5, 0.5, f"Contour error: {e}",
                            ha='center', va='center',
                            transform=base_ax.transAxes,
                            fontsize=10, color='red')

        # ====================================================================
        # ИЕРАРХИЯ
        # ====================================================================
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

        # ====================================================================
        # ПОТОКИ
        # ====================================================================
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

        # ====================================================================
        # СЕТИ
        # ====================================================================
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

        # ====================================================================
        # ПРОЧИЕ МАТРИЧНЫЕ
        # ====================================================================
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

        return artist