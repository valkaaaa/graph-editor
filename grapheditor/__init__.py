"""/grapheditor/__init__.py"""
import os
import sys

# Поддержка bare-импортов внутри пакета:
#   from translator import tr
# работает и в dev-режиме (app.py), и после `pip install`
# (когда app.py не участвует, а sys.path содержит только site-packages).
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

__version__ = '1.5.0'
__author__ = 'valkaa'