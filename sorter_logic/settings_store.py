from PySide6.QtCore import QSettings


def _settings():
    return QSettings("DominikSerafin", "PhotoVideoSorter")


def load_language(default="en"):
    return _settings().value("language", default)


def save_language(code):
    _settings().setValue("language", code)
