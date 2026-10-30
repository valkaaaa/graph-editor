"""Система плагинов GraphEditor Pro.

Плагин — это .py файл, определяющий функцию register(api).
Плагины загружаются из:
  - ~/.grapheditor_plugins/   (пользовательские)
  - grapheditor/plugins/bundled/  (встроенные примеры)

Безопасность:
  Плагины выполняются с полными правами приложения.
  Используйте только доверенные плагины.

/grapheditor/plugins/__init__.py
"""
import importlib.util
import os
import sys
import traceback
from tkinter import messagebox

from translator import tr, INTERNAL_TYPES, TYPE_TO_KEY


# ============================================================================
# КОНСТАНТЫ
# ============================================================================

API_VERSION = "1.0"

PLUGINS_DIR = os.path.expanduser("~/.grapheditor_plugins")

# Встроенные примеры лежат в подпапке bundled/ рядом с этим __init__.py
BUNDLED_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "bundled")


# ============================================================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================================================

def ensure_plugins_dir():
    """Создаёт папку плагинов и README с инструкцией, если их нет."""
    os.makedirs(PLUGINS_DIR, exist_ok=True)
    readme = os.path.join(PLUGINS_DIR, "README.txt")
    if not os.path.exists(readme):
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                "GraphEditor Pro — папка плагинов\n"
                "=================================\n\n"
                "Каждый .py файл в этой папке — плагин.\n"
                "Плагин должен определять функцию register(api).\n\n"
                "Минимальный пример:\n\n"
                "  def register(api):\n"
                "      api.add_chart_type(\n"
                "          id=\"my_type\",\n"
                "          display={'ru': 'Мой тип', 'en': 'My type'},\n"
                "          hint={'ru': 'Введите X и Y', 'en': 'Enter X and Y'},\n"
                "          fields=['x', 'y'],\n"
                "          draw=draw_my_type,\n"
                "      )\n\n"
                "  def draw_my_type(ax, data, api):\n"
                "      line, = ax.plot(data['x'], data['y'],\n"
                "                      color=data.get('color', 'blue'))\n"
                "      return line\n\n"
                "После добавления/изменения плагина:\n"
                "  Меню → Плагины → Перезагрузить плагины\n\n"
                "Плагины запускаются с полными правами приложения.\n"
                "Не используйте чужие плагины без проверки кода.\n"
            )


def list_plugin_files():
    """Возвращает список (полный_путь, имя_файла) всех плагинов."""
    files = []
    for d in (PLUGINS_DIR, BUNDLED_DIR):
        if not os.path.isdir(d):
            continue
        try:
            for fname in sorted(os.listdir(d)):
                if fname.endswith(".py") and not fname.startswith("_"):
                    files.append((os.path.join(d, fname), fname))
        except OSError:
            continue
    return files


def _reset_plugin_registrations():
    """Убирает все ранее зарегистрированные plugin-типы из реестров."""
    old_ids = list(getattr(tr, '_plugin_types', {}).keys())
    for pid in old_ids:
        while pid in INTERNAL_TYPES:
            INTERNAL_TYPES.remove(pid)
    tr.unregister_plugin_types()


# ============================================================================
# ОПИСАНИЕ ТИПА ГРАФИКА
# ============================================================================

class ChartTypeDef:
    """Одно описание plugin-типа графика."""

    __slots__ = ('id', 'display', 'hint', 'fields',
                 'draw', 'projection', 'extra_defaults')

    def __init__(self, id, display, hint, fields, draw,
                 projection='2d', extra_defaults=None):
        self.id = id
        self.display = display or {"en": id}
        self.hint = hint or {}
        self.fields = fields or ["x", "y"]
        self.draw = draw
        self.projection = projection
        self.extra_defaults = extra_defaults or {}


# ============================================================================
# РЕЕСТР
# ============================================================================

class PluginRegistry:
    """Хранит все зарегистрированные plugin-типы и ошибки загрузки."""

    def __init__(self):
        self.chart_types = {}   # id -> ChartTypeDef
        self.errors = []        # [(filename, traceback_str)]

    def call_draw(self, app, target_ax, data):
        """Вызывает draw() соответствующего plugin-типа."""
        td = self.chart_types.get(data.get('type'))
        if td is None:
            return None
        try:
            return td.draw(target_ax, data, PluginAPI(app, self))
        except Exception:
            tb = traceback.format_exc()
            self.errors.append((td.id, tb))
            try:
                messagebox.showerror(
                    "Плагин упал",
                    f"Тип '{td.display.get(tr.lang, td.id)}':\n\n"
                    f"{tb[-900:]}")
            except Exception:
                pass
            return None


# ============================================================================
# API ДЛЯ ПЛАГИНОВ
# ============================================================================

class PluginAPI:
    """Объект, передаваемый в register(api) при загрузке плагина
    и в draw(ax, data, api) при отрисовке."""

    def __init__(self, app, registry):
        self._app = app
        self._registry = registry
        self.version = API_VERSION

    # ----- Регистрация типа -----
    def add_chart_type(self, id, display, draw, hint=None,
                       fields=None, projection='2d',
                       extra_defaults=None):
        """Регистрирует новый тип графика."""
        if not id or not callable(draw):
            raise ValueError("add_chart_type: нужны id и draw")
        if id in TYPE_TO_KEY:
            raise ValueError(
                f"'{id}' — встроенный тип, нельзя переопределить")
        if id in self._registry.chart_types:
            raise ValueError(f"Тип '{id}' уже зарегистрирован")
        if id in INTERNAL_TYPES:
            raise ValueError(f"Тип '{id}' уже есть в списке")

        td = ChartTypeDef(id, display, hint, fields, draw,
                          projection, extra_defaults)
        self._registry.chart_types[id] = td
        tr.register_plugin_type(id, display)
        INTERNAL_TYPES.append(id)

    # ----- Хелперы (чтобы плагин не делал лишних импортов) -----
    @property
    def np(self):
        import numpy
        return numpy

    @property
    def plt(self):
        import matplotlib.pyplot as pyplot
        return pyplot

    @property
    def mcolors(self):
        import matplotlib.colors
        return matplotlib.colors

    def parse_data(self, text):
        """Разбор строки "1, 2, 3" → [1.0, 2.0, 3.0]."""
        if not text:
            return []
        try:
            parts = [p.strip()
                     for p in text.replace(';', ',')
                                    .replace('\t', ',').split(',')]
            return [float(p.replace(',', '.'))
                    for p in parts if p]
        except (ValueError, AttributeError):
            return []

    def show_error(self, title, msg):
        messagebox.showerror(title, msg)

    def show_info(self, title, msg):
        messagebox.showinfo(title, msg)


# ============================================================================
# ЗАГРУЗКА
# ============================================================================

def load_plugins(app):
    """Загружает все плагины. Возвращает PluginRegistry.

    Вызывается из AdvancedGraphEditorApp.__init__ ДО _build_ui,
    чтобы новые типы попали в combobox.
    """
    ensure_plugins_dir()
    _reset_plugin_registrations()

    registry = PluginRegistry()
    api = PluginAPI(app, registry)

    for path, name in list_plugin_files():
        try:
            mod_name = f"grapheditor_plugin_{name[:-3]}"
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {path}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)

            if not hasattr(module, 'register'):
                raise AttributeError(
                    f"{name}: нет функции register(api)")
            module.register(api)
        except Exception:
            registry.errors.append((name, traceback.format_exc()))

    _patch_app_methods(app, registry)

    return registry

def _patch_app_methods(app, registry):
    """Оборачивает _start_animation и _apply_template, чтобы они
    знали про плагины. Если плагинов нужного типа нет — ничего не делает.
    Вызывается один раз из load_plugins.
    """
    # ----- Анимации -----
    if getattr(registry, 'animations', None):
        if not getattr(app, '_anim_patched', False):
            original_start = app._start_animation
            animations = registry.animations

            def patched_start():
                at = tr.find_anim_by_display(app.anim_type_var.get())

                if at not in animations:
                    return original_start()

                # Плагинная анимация — своя логика
                if app.current_animation is not None:
                    from tkinter import messagebox
                    messagebox.showinfo(
                        tr.t('msg.info'),
                        tr.t('msg.anim_already_running'))
                    return

                app._stop_animation()
                app.fig.clear()

                is_3d = '3D' in at
                app.axes = []
                if is_3d:
                    app.ax = app.fig.add_subplot(111, projection='3d')
                else:
                    app.ax = app.fig.add_subplot(111)
                app.axes.append(app.ax)
                app._style_axes()

                try:
                    update = animations[at]["create"](app, app.ax)
                except Exception:
                    import traceback
                    from tkinter import messagebox
                    traceback.print_exc()
                    messagebox.showerror(
                        "Ошибка анимации плагина", at)
                    return

                if update is None:
                    return

                import itertools
                from matplotlib.animation import FuncAnimation

                app.anim_paused = False
                app.anim_frame = 0
                try:
                    app.anim_progress['value'] = 0
                except Exception:
                    pass

                interval = app.anim_speed_var.get()

                def wrapped(_):
                    if app.anim_paused:
                        return []
                    app.anim_frame += 1
                    try:
                        app.anim_progress['value'] = (
                            app.anim_frame % app.anim_frames_total)
                    except Exception:
                        pass
                    return update(app.anim_frame)

                app.current_animation = FuncAnimation(
                    app.fig, wrapped, frames=itertools.count(),
                    interval=interval, blit=False,
                    cache_frame_data=False,
                    save_count=app.anim_frames_total)
                app.canvas.draw()

            app._start_animation = patched_start
            app._anim_patched = True

    # ----- Шаблоны -----
    if getattr(registry, 'templates', None):
        if not getattr(app, '_templates_patched', False):
            original_apply = app._apply_template
            templates = registry.templates

            def patched_apply(name):
                if name not in templates:
                    return original_apply(name)

                from tkinter import messagebox
                td = templates[name]
                display = (td["display"].get(tr.lang)
                           or td["display"].get("en")
                           or name)

                app._snapshot(f"Шаблон плагина: {display}")
                app._clear_all_silent(keep_undo=True)

                try:
                    td["builder"](app)
                except Exception:
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror(
                        "Ошибка шаблона плагина",
                        f"{display}\n\nСм. консоль для подробностей.")
                    return

                app._apply_canvas_settings()
                app._update_listbox()
                app._redraw()
                app._show_history(f"Шаблон плагина: {display}")

            app._apply_template = patched_apply
            app._templates_patched = True

__all__ = [
    'load_plugins', 'PluginRegistry', 'PluginAPI', 'ChartTypeDef',
    'ensure_plugins_dir', 'list_plugin_files',
    'PLUGINS_DIR', 'BUNDLED_DIR', 'API_VERSION',
]