"""Звуковые эффекты через winsound (только Windows).

При отсутствии click.wav — приложение работает без звука.
"""
import os
import sys

import winsound


class SoundMixin:
    _sound_enabled = True
    _click_wav = None

    def _init_sounds(self):
        """Инициализация: находит click.wav и читает флаг из настроек.
        Вызывается один раз из AdvancedGraphEditorApp.__init__."""
        path = self._asset_sound_path("click.wav")
        if os.path.exists(path):
            self._click_wav = path
        self._sound_enabled = self.settings.get('sounds_enabled', True)

    def _asset_sound_path(self, filename):
        """Путь к assets/<file> с учётом PyInstaller _MEIPASS."""
        base = getattr(
            sys, '_MEIPASS',
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'assets', filename)

    def _play_click(self):
        """Воспроизвести клик (асинхронно, не блокирует UI)."""
        if not self._sound_enabled or self._click_wav is None:
            return
        try:
            winsound.PlaySound(
                self._click_wav,
                winsound.SND_FILENAME
                | winsound.SND_ASYNC
                | winsound.SND_NODEFAULT)
        except Exception:
            pass

    def _with_click_sound(self, command):
        """Оборачивает коллбэк так, чтобы он проигрывал клик."""
        if not callable(command):
            return command

        def wrapped(*args, **kwargs):
            self._play_click()
            return command(*args, **kwargs)

        return wrapped

    def _toggle_click_sound(self, enabled):
        """Включить/выключить звук (для настроек)."""
        self._sound_enabled = bool(enabled)