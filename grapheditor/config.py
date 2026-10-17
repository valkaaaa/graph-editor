import os, json


def config_dir():
    d = os.path.expanduser("~/.grapheditor")
    os.makedirs(d, exist_ok=True)
    return d


def config_path():
    # Портативный режим
    base = os.path.dirname(os.path.abspath(__file__))
    portable = os.path.join(base, 'settings.json')
    if os.path.exists(portable):
        return portable
    return os.path.join(config_dir(), 'settings.json')


def load_config():
    path = config_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[config] load error: {e}")
        return {}


def save_config(data):
    path = config_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2,
                      default=lambda o: o.tolist()
                      if hasattr(o, 'tolist') else str(o))
    except Exception as e:
        print(f"[config] save error: {e}")


def reset_config():
    """Удаляет файл настроек. Возвращает True при успехе."""
    path = config_path()
    if not os.path.exists(path):
        return True
    try:
        os.remove(path)
        return True
    except Exception as e:
        print(f"[config] reset error: {e}")
        return False