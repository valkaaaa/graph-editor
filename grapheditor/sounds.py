"""Звуковые эффекты через winsound (только Windows).

На Linux/macOS `winsound` отсутствует — звук автоматически
отключается, приложение работает без него.
"""
import os
import sys

try:
    import winsound
except ImportError:
    winsound = None


class SoundMixin:
    _sound_enabled = True
    _click_wav = None

    def _init_sounds(self):
        """Инициализация: находит click.wav и читает флаг из настроек.

        На не-Windows платформах (или при отсутствии winsound)
        звук принудительно отключается.
        """
        path = self._asset_sound_path("click.wav")
        if os.path.exists(path):
            self._click_wav = path

        # Звук доступен только если winsound импортировался
        # (то есть на Windows) и пользователь его не отключил.
        user_enabled = self.settings.get('sounds_enabled', True)
        self._sound_enabled = bool(user_enabled) and winsound is not None

    def _asset_sound_path(self, filename):
        """Путь к assets/<file> с учётом PyInstaller _MEIPASS."""
        base = getattr(
            sys, '_MEIPASS',
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, 'assets', filename)

    def _play_click(self):
        """Воспроизвести клик (асинхронно, не блокирует UI).

        На не-Windows платформах — no-op.
        """
        if not self._sound_enabled or self._click_wav is None:
            return
        if winsound is None:                # двойная защита
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
        """Включить/выключить звук (для настроек).

        На не-Windows платформах всегда остаётся выключенным,
        даже если пользователь поставил галочку.
        """
        self._sound_enabled = bool(enabled) and winsound is not None