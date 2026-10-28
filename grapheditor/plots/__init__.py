"""/grapheditor/plots/__init__.py"""
from ._base import BasePlotsMixin
from ._create_artist import CreateArtistMixin
from ._extras import ExtrasMixin
from ._io import IOMixin


class PlotsMixin(
    BasePlotsMixin,
    CreateArtistMixin,
    ExtrasMixin,
    IOMixin,
):
    """Сборный миксин для AdvancedGraphEditorApp."""
    pass


__all__ = ['PlotsMixin']