import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler


LOG_DIR = os.path.join(os.path.expanduser('~'), '.grapheditor')
LOG_FILE = os.path.join(LOG_DIR, 'errors.log')


def setup_logging(level=logging.INFO):
    """Настраивает логирование в файл и в консоль."""
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    # Убираем возможные дубли (если setup вызван дважды)
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # Файл: ротация при 1 МБ, храним 3 копии
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)
    root.addHandler(file_handler)

    # Консоль: только WARNING и выше
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.WARNING)
    root.addHandler(console_handler)

    return root


def install_excepthook():
    """Перехватывает НЕПОЙМАННЫЕ исключения (вне Tk)."""
    log = logging.getLogger('excepthook')

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log.critical("Необработанное исключение",
                     exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _hook


def install_tk_excepthook(root):
    """Перехватывает ошибки ВНУТРИ Tk-колбэков.
    Это 90% всех ошибок GUI — без этого они летят в stderr и теряются."""
    log = logging.getLogger('tk')

    def _tk_hook(exc_type, exc_value, exc_tb):
        log.error("Ошибка в Tk-колбэке",
                  exc_info=(exc_type, exc_value, exc_tb))

    root.report_callback_exception = _tk_hook