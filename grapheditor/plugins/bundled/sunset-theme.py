"""Плагин: тема оформления Sunset."""
__author__ = "valkaa"

def register(api):
    api.add_theme("sunset", {
        "name": "Закат (Sunset)",
        "is_dark": True,
        "mpl_style": "dark_background",
        "bg": "#1a1110",          # Основной фон окна
        "fg": "#ffd8be",          # Основной текст
        "field": "#2d1c1a",       # Поля ввода (Entry)
        "select": "#ff7b54",      # Выделение
        "button": "#3b2421",      # Кнопки
        "button_active": "#5c372e",# Кнопки при наведении
        "border": "#5c372e",      # Границы
        "plot_bg": "#1a1110",     # Фон самого холста с графиком
        "grid": "#5c372e",        # Сетка на графике
        "axes": "#ffd8be",        # Оси и подписи на графике
    })