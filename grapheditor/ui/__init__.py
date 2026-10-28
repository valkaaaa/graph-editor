"""GraphEditor Pro — интерфейс.

Все миксины работают через `self`, поэтому файлы не импортируют друг друга.

/grapheditor/ui/__init__.py
"""
from ._base import BaseUIMixin
from ._menu import MenuUIMixin
from ._build import BuildUIMixin
from ._tree import TreeUIMixin
from ._dialogs import DialogsUIMixin


class UIMixin(
    BaseUIMixin,
    MenuUIMixin,
    BuildUIMixin,
    TreeUIMixin,
    DialogsUIMixin,
):
    """Сборный миксин интерфейса для AdvancedGraphEditorApp."""
    pass


__all__ = ['UIMixin']