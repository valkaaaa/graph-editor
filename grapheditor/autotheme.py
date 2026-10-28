"""Авто-переключение темы по времени суток."""
import datetime


class AutoThemeMixin:

    def _init_auto_theme(self):
        if self.settings.get('auto_theme_by_time', False):
            self.root.after(5_000, self._auto_theme_tick)

    def _auto_theme_tick(self):
        try:
            if not self.settings.get('auto_theme_by_time', False):
                return
            h = datetime.datetime.now().hour
            day_start = int(self.settings.get('theme_day_start', 7))
            day_end = int(self.settings.get('theme_day_end', 19))
            is_day = day_start <= h < day_end
            target = (self.settings.get('theme_day', 'light')
                      if is_day
                      else self.settings.get('theme_night', 'dark'))
            if target != self.settings.get('theme'):
                try:
                    self._apply_theme(target)
                    if hasattr(self, 'theme_var'):
                        self.theme_var.set(target)
                    if hasattr(self, '_populate_theme_menu'):
                        self._populate_theme_menu()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self.root.after(60_000, self._auto_theme_tick)

    def _toggle_auto_theme(self):
        """Вкл/выкл авторежим из UI."""
        enabled = bool(self._auto_theme_var.get())
        self.settings['auto_theme_by_time'] = enabled
        if enabled:
            self.root.after(200, self._auto_theme_tick)
        else:
            # вернуть вручную выбранную тему
            pass