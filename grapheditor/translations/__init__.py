"""Пакет переводов GraphEditor Pro.

Каждый язык — отдельный модуль xx.py с переменной TEXTS (dict).
Здесь все они собираются в TRANSLATIONS.

/grapheditor/translations/__init__.py
"""
from .ru import TEXTS as _ru
from .en import TEXTS as _en
from .de import TEXTS as _de
from .fr import TEXTS as _fr
from .es import TEXTS as _es
from .pt import TEXTS as _pt
from .it import TEXTS as _it
from .vi import TEXTS as _vi
from .th import TEXTS as _th
from .zh import TEXTS as _zh
from .ja import TEXTS as _ja
from .kr import TEXTS as _kr
from .ar import TEXTS as _ar
from .hi import TEXTS as _hi
from .sl import TEXTS as _sl
from .pl import TEXTS as _pl
from .kz import TEXTS as _kz
from .uz import TEXTS as _uz
from .by import TEXTS as _by
from .ua import TEXTS as _ua


TRANSLATIONS = {
    'ru': _ru,
    'en': _en,
    'de': _de,
    'fr': _fr,
    'es': _es,
    'pt': _pt,
    'it': _it,
    'vi': _vi,
    'th': _th,
    'zh': _zh,
    'ja': _ja,
    'kr': _kr,
    'ar': _ar,
    'hi': _hi,
    'sl': _sl,
    'pl': _pl,
    'kz': _kz,
    'uz': _uz,
    'by': _by,
    'ua': _ua,
}

__all__ = ['TRANSLATIONS']