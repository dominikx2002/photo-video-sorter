from PySide6.QtCore import QSettings
from .constants import MEDIA_EXT


def _settings():
    return QSettings("DominikSerafin", "PhotoVideoSorter")


def load_language(default="en"):
    return _settings().value("language", default)


def save_language(code):
    _settings().setValue("language", code)


def load_enabled_extensions():
    """Returns the set of media extensions the user wants scanned. We persist
    the DISABLED set (not the enabled one) so that any newly supported format
    is on by default - the app must never silently miss a media file."""
    stored = _settings().value("disabled_extensions", None)
    if isinstance(stored, str):
        stored = [stored]
    disabled = set(stored) if stored else set()
    return MEDIA_EXT - disabled


def save_enabled_extensions(extensions):
    disabled = MEDIA_EXT - set(extensions)
    _settings().setValue("disabled_extensions", sorted(disabled))
