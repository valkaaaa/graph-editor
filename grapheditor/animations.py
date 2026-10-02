import itertools

import numpy as np

from tkinter import messagebox, filedialog
from matplotlib.animation import FuncAnimation

from translator import tr


class AnimationsMixin:

    def _toggle_pause_anim(self):
        self.anim_paused = not self.anim_paused
        self.status_var.set(tr.t('status.anim_paused') if self.anim_paused
                            else tr.t('status.anim_running'))

    def _start_animation(self):
        if self.current_animation is not None:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.anim_already_running'))
            return
        self._stop_animation()
        self.fig.clear()
        at = tr.find_anim_by_display(self.anim_type_var.get())
        self.axes = []
        if "3D" in at:
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax = self.fig.add_subplot(111)
        self.axes.append(self.ax)
        self._style_axes()
        x = np.linspace(0, 4 * np.pi, 100)
        interval = self.anim_speed_var.get()

        if at == "Волна (2D)":
            line, = self.ax.plot(x, np.sin(x), 'b-', lw=2)
            self.ax.set_ylim(-1.5, 1.5)
            self.ax.set_title(tr.anim_name(at))

            def update(frame):
                line.set_ydata(np.sin(x + frame / 10.0))
                return line,
        elif at == "Растущий столбец":
            bars = self.ax.bar([1, 2, 3, 4], [0, 0, 0, 0],
                               color=['red', 'blue', 'green', 'orange'])
            self.ax.set_ylim(0, 11)
            targets = [5, 8, 4, 10]

            def update(frame):
                tt = frame / 20.0
                for b, tg in zip(bars, targets):
                    b.set_height(tg * min(tt, 1.0))
                return bars
        elif at == "Спираль (3D)":
            line, = self.ax.plot3D([], [], [], 'g-', lw=2)
            self.ax.set_xlim(-5, 5)
            self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(0, 10)

            def update(frame):
                tt = frame / 10.0
                zl = np.linspace(0, tt * 2, 100)
                line.set_data_3d(np.sin(zl) * (5 - zl / 4),
                                 np.cos(zl) * (5 - zl / 4), zl)
                return line,
        elif at == "Пульсация точек":
            sc = self.ax.scatter(x, np.sin(x), s=50, color='purple')
            self.ax.set_ylim(-1.5, 1.5)

            def update(frame):
                sc.set_sizes(np.full_like(x, 50 + 200 * abs(np.sin(frame / 5.0))))
                sc.set_offsets(np.c_[x, np.sin(x + frame / 10.0)])
                return sc,
        elif at == "Своя функция (2D)":
            expr = self.entry_custom_anim.get()
            y0 = self._safe_eval(expr, x, 0, silent=True)
            if y0 is None:
                return
            line, = self.ax.plot(x, y0, 'r-', lw=2)
            self.ax.set_title(f"y = {expr}")

            def update(frame):
                yn = self._safe_eval(expr, x, frame / 10.0, silent=True)
                if yn is None:
                    return line,
                line.set_ydata(yn)
                return line,
        elif at == "Своя функция (3D)":
            expr = self.entry_custom_anim.get()
            xg = np.linspace(-5, 5, 45)
            yg = np.linspace(-5, 5, 45)
            X, Y = np.meshgrid(xg, yg)
            Z0 = self._safe_eval(expr, X, 0, Y, silent=True)
            if Z0 is None:
                return
            self.ax.set_title(f"z = {expr}")
            holder = [self.ax.plot_surface(X, Y, Z0, cmap='viridis',
                                            edgecolor='none', alpha=0.95)]

            def update(frame):
                Z = self._safe_eval(expr, X, frame / 10.0, Y, silent=True)
                if Z is None:
                    return []
                try:
                    holder[0].remove()
                except Exception:
                    pass
                holder[0] = self.ax.plot_surface(X, Y, Z, cmap='viridis',
                                                  edgecolor='none', alpha=0.95)
                return [holder[0]]
        elif at == "Маятник (2D)":
            L = 1.0; g = 9.81; theta0 = np.pi / 3
            t_arr = np.linspace(0, 8, 300); dt = t_arr[1] - t_arr[0]
            theta = theta0; omega = 0.0; angles = []
            for _ in t_arr:
                alpha = -g / L * np.sin(theta)
                omega += alpha * dt
                theta += omega * dt
                angles.append(theta)
            angles = np.array(angles)
            rod, = self.ax.plot([], [], 'b-', lw=2)
            ball, = self.ax.plot([], [], 'ro', markersize=12)
            trace, = self.ax.plot([], [], 'r-', lw=0.7, alpha=0.6)
            self.ax.set_xlim(-1.2, 1.2); self.ax.set_ylim(-1.2, 0.3)
            self.ax.set_aspect('equal'); self.ax.set_title(tr.anim_name(at))
            tx, ty = [], []

            def update(frame):
                idx = frame % len(angles); th = angles[idx]
                x_ball = L * np.sin(th); y_ball = -L * np.cos(th)
                rod.set_data([0, x_ball], [0, y_ball])
                ball.set_data([x_ball], [y_ball])
                tx.append(x_ball); ty.append(y_ball)
                if len(tx) > 100:
                    tx.pop(0); ty.pop(0)
                trace.set_data(tx, ty)
                return rod, ball, trace
        elif at == "Лоренц-аттрактор (3D)":
            sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
            dt = 0.01; x0, y0, z0 = 0.1, 0.0, 0.0
            n_steps = 30
            traj = np.zeros((2000, 3))
            xx, yy, zz = x0, y0, z0
            for i in range(2000):
                dx = sigma * (yy - xx)
                dy = xx * (rho - zz) - yy
                dz = xx * yy - beta * zz
                xx += dx * dt; yy += dy * dt; zz += dz * dt
                traj[i] = [xx, yy, zz]
            line, = self.ax.plot3D([], [], [], 'b-', lw=1.2)
            head, = self.ax.plot3D([], [], [], 'ro', markersize=8)
            self.ax.set_xlim(-25, 25); self.ax.set_ylim(-30, 30)
            self.ax.set_zlim(0, 55); self.ax.set_title(tr.anim_name(at))

            def update(frame):
                end = min(len(traj), (frame + 1) * n_steps)
                start = max(0, end - 800)
                seg = traj[start:end]
                line.set_data_3d(seg[:, 0], seg[:, 1], seg[:, 2])
                head.set_data_3d([seg[-1, 0]], [seg[-1, 1]], [seg[-1, 2]])
                return line, head
        elif at == "Двойной маятник (2D)":
            L1, L2 = 1.0, 1.0; m1, m2 = 1.0, 1.0; g = 9.81
            th1, th2 = np.pi / 2, np.pi / 2
            w1, w2 = 0.0, 0.0; dt = 0.005
            steps = 3000
            traj = np.zeros((steps, 4))
            for i in range(steps):
                a = -(g * (2 * m1 + m2) * np.sin(th1)
                      + m2 * g * np.sin(th1 - 2 * th2)
                      + 2 * m2 * np.sin(th1 - th2)
                      * (w2 ** 2 * L2 + w1 ** 2 * L1 * np.cos(th1 - th2))) \
                    / (L1 * (2 * m1 + m2 - m2 * np.cos(2 * th1 - 2 * th2)))
                b = 2 * np.sin(th1 - th2) * (
                    w1 ** 2 * L1 * (m1 + m2) + g * (m1 + m2) * np.cos(th1)
                    + w2 ** 2 * L2 * m2 * np.cos(th1 - th2)
                ) / (L2 * (2 * m1 + m2 - m2 * np.cos(2 * th1 - 2 * th2)))
                w1 += a * dt; w2 += b * dt
                th1 += w1 * dt; th2 += w2 * dt
                traj[i] = [th1, th2, w1, w2]
            rod1, = self.ax.plot([], [], 'b-', lw=2)
            rod2, = self.ax.plot([], [], 'g-', lw=2)
            b1, = self.ax.plot([], [], 'bo', markersize=10)
            b2, = self.ax.plot([], [], 'go', markersize=10)
            trace, = self.ax.plot([], [], 'r-', lw=0.5, alpha=0.5)
            self.ax.set_xlim(-2.5, 2.5); self.ax.set_ylim(-2.5, 2.5)
            self.ax.set_aspect('equal'); self.ax.set_title(tr.anim_name(at))
            tx, ty = [], []

            def update(frame):
                idx = (frame * 5) % len(traj)
                t1, t2, _, _ = traj[idx]
                x1 = L1 * np.sin(t1); y1 = -L1 * np.cos(t1)
                x2 = x1 + L2 * np.sin(t2); y2 = y1 - L2 * np.cos(t2)
                rod1.set_data([0, x1], [0, y1])
                rod2.set_data([x1, x2], [y1, y2])
                b1.set_data([x1], [y1]); b2.set_data([x2], [y2])
                tx.append(x2); ty.append(y2)
                if len(tx) > 200:
                    tx.pop(0); ty.pop(0)
                trace.set_data(tx, ty)
                return rod1, rod2, b1, b2, trace
        elif at == "Эпициклоид (2D)":
            R = 3.0; r = 1.0; d = 1.5
            t_arr = np.linspace(0, 6 * np.pi, 2000)
            x_full = (R + r) * np.cos(t_arr) - d * np.cos((R + r) / r * t_arr)
            y_full = (R + r) * np.sin(t_arr) - d * np.sin((R + r) / r * t_arr)
            line, = self.ax.plot([], [], 'purple', lw=1.8)
            head, = self.ax.plot([], [], 'ro', markersize=8)
            self.ax.set_xlim(x_full.min() - 1, x_full.max() + 1)
            self.ax.set_ylim(y_full.min() - 1, y_full.max() + 1)
            self.ax.set_aspect('equal'); self.ax.set_title(tr.anim_name(at))

            def update(frame):
                end = min(len(t_arr), (frame + 1) * 15)
                line.set_data(x_full[:end], y_full[:end])
                if end > 0:
                    head.set_data([x_full[end - 1]], [y_full[end - 1]])
                return line, head
        elif at == "Бегущие частицы (3D)":
            n = self.anim_params['particles_n']
            positions = np.random.uniform(-5, 5, (n, 3))
            speeds = np.random.uniform(0.05, 0.2, (n, 3)) * \
                     np.random.choice([-1, 1], (n, 3))
            colors_arr = np.random.rand(n)
            scat = self.ax.scatter3D(positions[:, 0], positions[:, 1],
                                      positions[:, 2], c=colors_arr,
                                      cmap='plasma', s=30, alpha=0.8)
            self.ax.set_xlim(-5, 5); self.ax.set_ylim(-5, 5)
            self.ax.set_zlim(-5, 5); self.ax.set_title(tr.anim_name(at))

            def update(frame):
                nonlocal positions
                positions = positions + speeds
                for dim in range(3):
                    mh = positions[:, dim] > 5
                    ml = positions[:, dim] < -5
                    speeds[mh, dim] *= -1; speeds[ml, dim] *= -1
                    positions[mh, dim] = 5 - (positions[mh, dim] - 5)
                    positions[ml, dim] = -5 + (-5 - positions[ml, dim])
                scat._offsets3d = (positions[:, 0], positions[:, 1],
                                   positions[:, 2])
                return scat,
        elif at == "Клеточный автомат (2D)":
            N = self.anim_params['cellular_size']
            grid = (np.random.rand(N, N) <
                    self.anim_params['cellular_density']).astype(int)
            im = self.ax.imshow(grid, cmap='binary', vmin=0, vmax=1,
                                interpolation='nearest', animated=True)
            self.ax.set_title(tr.anim_name(at))
            self.ax.set_xticks([]); self.ax.set_yticks([])

            def step_life(g):
                neighbors = sum(np.roll(np.roll(g, i, 0), j, 1)
                                for i in (-1, 0, 1) for j in (-1, 0, 1)
                                if not (i == 0 and j == 0))
                birth = (neighbors == 3) & (g == 0)
                survive = ((neighbors == 2) | (neighbors == 3)) & (g == 1)
                return (birth | survive).astype(int)

            def update(frame):
                nonlocal grid
                grid = step_life(grid)
                im.set_array(grid)
                return im,
        elif at == "Морфинг функций (2D)":
            xm = np.linspace(-2 * np.pi, 2 * np.pi, 300)
            funcs = [np.sin(xm), np.sin(2 * xm) * np.exp(-xm ** 2 / 8),
                     np.cos(xm) * xm / 3, np.tanh(xm),
                     np.sin(xm) * np.cos(2 * xm)]
            line, = self.ax.plot(xm, funcs[0], 'b-', lw=2)
            self.ax.set_ylim(-2, 2); self.ax.set_title(tr.anim_name(at))

            def update(frame):
                period = 60
                idx = (frame // period) % len(funcs)
                nxt = (idx + 1) % len(funcs)
                alpha = (frame % period) / period
                yv = (1 - alpha) * funcs[idx] + alpha * funcs[nxt]
                line.set_ydata(yv)
                return line,
        elif at == "Тепловая карта (2D)":
            N = self.anim_params['heatmap_size']
            u = np.zeros((N, N))
            cx, cy = N // 2, N // 2
            u[cx - 2:cx + 3, cy - 2:cy + 3] = 1.0
            alpha = self.anim_params['heatmap_alpha']
            im = self.ax.imshow(u, cmap='inferno', vmin=0, vmax=1,
                                interpolation='bilinear', animated=True)
            self.ax.set_title(tr.anim_name(at))
            self.ax.set_xticks([]); self.ax.set_yticks([])

            def laplacian(g):
                return (np.roll(g, 1, 0) + np.roll(g, -1, 0) +
                        np.roll(g, 1, 1) + np.roll(g, -1, 1) - 4 * g)

            def update(frame):
                nonlocal u
                u = u + alpha * laplacian(u)
                u[cx - 1:cx + 2, cy - 1:cy + 2] = np.maximum(
                    u[cx - 1:cx + 2, cy - 1:cy + 2], 0.9)
                im.set_array(u)
                return im,
        elif at == "Вращение 3D":
            xg = np.linspace(-2, 2, 40); yg = np.linspace(-2, 2, 40)
            X, Y = np.meshgrid(xg, yg)
            Z = np.sin(np.sqrt(X ** 2 + Y ** 2)) / (
                np.sqrt(X ** 2 + Y ** 2) + 0.1)
            surf = self.ax.plot_surface(X, Y, Z, cmap='viridis',
                                         edgecolor='none', alpha=0.95)
            self.ax.set_title(tr.anim_name(at))

            def update(frame):
                self.ax.view_init(elev=30, azim=frame * 2 % 360)
                return surf,
        else:
            return

        self.anim_paused = False
        self.anim_frame = 0
        try:
            self.anim_progress['value'] = 0
        except Exception:
            pass
        last = [None]

        def wrapped(_):
            if self.anim_paused:
                return last[0] if last[0] is not None else []
            self.anim_frame += 1
            try:
                self.anim_progress['value'] = (
                    self.anim_frame % self.anim_frames_total)
            except Exception:
                pass
            last[0] = update(self.anim_frame)
            return last[0]

        self.current_animation = FuncAnimation(
            self.fig, wrapped, frames=itertools.count(),
            interval=interval, blit=False,
            cache_frame_data=False, save_count=self.anim_frames_total)
        self.canvas.draw()

    def _stop_animation(self):
        if self.current_animation is not None:
            try:
                self.current_animation.event_source.stop()
            except Exception:
                pass
            self.current_animation = None
        if not hasattr(self, 'fig'):
            return
        self.anim_paused = False
        try:
            self.anim_progress['value'] = 0
        except Exception:
            pass
        self.fig.clear()
        for ax in self.axes_secondary.values():
            try:
                ax.remove()
            except Exception:
                pass
        self.axes_secondary = {}
        needs_3d = any("3D" in d['type'] for d in self.graphs_data)
        proj_kw = {'projection': '3d'} if needs_3d else {}
        self.axes = []
        n = self.subplot_rows * self.subplot_cols
        for i in range(n):
            ax = self.fig.add_subplot(self.subplot_rows, self.subplot_cols,
                                      i + 1, **proj_kw)
            self.axes.append(ax)
        self.ax = self.axes[0]
        self._style_axes()
        self._init_tooltip()
        self._init_crosshair()
        self.canvas.draw()
        self._redraw()

    def _save_animation(self):
        if self.current_animation is None:
            messagebox.showinfo(tr.t('msg.info'), tr.t('msg.anim_save_first'))
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF", "*.gif"), ("MP4", "*.mp4")])
        if not path:
            return
        self.status_var.set(tr.t('status.saving_anim'))
        self.root.update_idletasks()
        try:
            if path.lower().endswith('.gif'):
                self.current_animation.save(
                    path,
                    writer='pillow',
                    fps=20,
                    dpi=100)
            else:
                self.current_animation.save(
                    path,
                    writer='ffmpeg',
                    fps=30,
                    dpi=150)
            self._show_history(tr.t('hist.saved_anim',
                                    name=__import__('os').path.basename(path)))
            messagebox.showinfo(tr.t('msg.done'),
                                tr.t('msg.anim_saved', path=path))
        except Exception as e:
            messagebox.showerror(tr.t('msg.error'),
                                 tr.t('msg.anim_save_error', error=e))
            self.status_var.set(tr.t('status.anim_save_error'))
