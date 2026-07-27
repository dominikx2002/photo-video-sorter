from PySide6.QtCore import QSettings
from .constants import MEDIA_EXT


def _settings():
    return QSettings("DominikSerafin", "PhotoVideoSorter")


def load_language(default="en"):
    return _settings().value("language", default)


def save_language(code):
    _settings().setValue("language", code)


def load_enabled_extensions():
    """Returns the set of media extensions the user wants scanned. Defaults
    to every supported extension the first time the app runs."""
    stored = _settings().value("enabled_extensions", None)
    if not stored:
        return set(MEDIA_EXT)
    if isinstance(stored, str):
        stored = [stored]
    return set(stored) & MEDIA_EXT


def save_enabled_extensions(extensions):
    _settings().setValue("enabled_extensions", sorted(extensions))
