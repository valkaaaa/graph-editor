"""Диспетчер отрисовки графиков.

Единственная публичная точка входа — `_create_artist(data)`.

Собирает `CreateArtistMixin` из четырёх миксинов по категориям:
  - Artists2DMixin      (_artists_2d.py)       — 2D базовые + статистика
  - ArtistsNetworkMixin (_artists_network.py)  — матричные + сетевые + иерархия
  - Artists3DMixin      (_artists_3d.py)       — все 3D-графики
  - ArtistsSpecialMixin (_artists_special.py)  — радио, ML, гео, экзотика

Общая инициализация (сброс ссылок, сглаживание, выбор осей,
плагины) — здесь. Специфика рисования — в миксинах.
"""
import numpy as np

from translator import tr

from ._artists_2d import Artists2DMixin, TYPES_2D
from ._artists_network import ArtistsNetworkMixin, TYPES_NETWORK
from ._artists_3d import Artists3DMixin, TYPES_3D
from ._artists_special import ArtistsSpecialMixin, TYPES_SPECIAL


# Множество всех известных встроенных типов.
# Полезно для тестов и проверок: если тип не в этом множестве
# и не зарегистрирован плагином — он уйдёт в fallback.
_ALL_KNOWN_TYPES = TYPES_2D | TYPES_NETWORK | TYPES_3D | TYPES_SPECIAL


class CreateArtistMixin(
    Artists2DMixin,
    ArtistsNetworkMixin,
    Artists3DMixin,
    ArtistsSpecialMixin,
):
    """Собирает все миксины отрисовки + предоставляет _create_artist()."""

    def _create_artist(self, data):
        """Создаёт matplotlib-artist по описанию объекта.

        Parameters
        ----------
        data : dict
            Поля объекта графика (type, x, y, z, color, label, ...).
            Может содержать служебные ключи `_extra_artists` и `_cleanup` —
            они сбрасываются в начале и заполняются миксинами по ходу.

        Returns
        -------
        artist | list | None
            Один matplotlib-artist, список artist-ов или None,
            если данных недостаточно.
        """
        t = data['type']

        # ---------- Сброс старых ссылок ----------
        data['_extra_artists'] = []
        data['_cleanup'] = None

        # ---------- Опциональное сглаживание ----------
        # В оригинале было `y = self._smooth(...).tolist()`, но `y`
        # локальная — эффект терялся. Пишем в data['y'], чтобы миксины
        # видели уже сглаженные данные.
        if (self.smooth_var.get()
                and t in ("Линия", "Точечная", "Столбчатая")):
            try:
                smooth_val = self._smooth(
                    data['y'], self.settings['smooth_window'])
                if hasattr(smooth_val, 'tolist'):
                    smooth_val = smooth_val.tolist()
                data['y'] = smooth_val
            except Exception:
                pass

        # ---------- Выбор осей (base / secondary) ----------
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

        # ---------- Плагины — наивысший приоритет ----------
        # ВАЖНО: getattr(..., None) is not None, а не hasattr.
        # Иначе при plugin_registry=None (например, в моках и при
        # неудачной инициализации) получаем AttributeError на каждом типе.
        registry = getattr(self, 'plugin_registry', None)
        if registry is not None and t in registry.chart_types:
            return registry.call_draw(self, target_ax, data)

        # ---------- Диспетчеризация по категориям ----------
        # Порядок важен: 3D проверяется первым, потому что
        # "Radial tree 3D" есть в TYPES_3D, но с точки зрения проекции
        # это тоже 3D-тип, и его нужно рисовать на 3D-осях.
        if t in TYPES_3D:
            return self._draw_3d(data, base_ax, target_ax)

        if t in TYPES_2D:
            return self._draw_2d(data, base_ax, target_ax)

        if t in TYPES_NETWORK:
            return self._draw_network(data, base_ax, target_ax)

        if t in TYPES_SPECIAL:
            return self._draw_special(data, base_ax, target_ax)

        # ---------- Fallback ----------
        # Неизвестный тип (обычно — опечатка в INTERNAL_TYPES
        # или незарегистрированный плагин): простая линия.
        x = data.get('x') or []
        y = data.get('y') or []
        try:
            artist, = target_ax.plot(
                x, y,
                label=data.get('label', ''),
                color=data.get('color', 'blue'))
            return artist
        except Exception:
            return None