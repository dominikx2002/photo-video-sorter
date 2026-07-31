import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QFrame, QCheckBox, QMessageBox, QToolTip,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QImageReader, QPixmap, QCursor
from sorter_logic.constants import PHOTO_EXT
from sorter_logic.fsutil import human_size, trash_or_remove
from sorter_logic.theme import mark_primary, mark_secondary, COLOR_GREEN, COLOR_ORANGE
from sorter_logic.i18n import translator as tr
from sorter_logic.mac_chrome import begin_activity, end_activity
from shimmer_progress import ShimmerProgressBar

_THUMB = 56
_PER_PAGE = 10
_THUMBS_PER_TICK = 3        # decode a few per timer tick so the UI stays live


def decode_thumb(path):
    """Decode a thumbnail, scaling down *while decoding* so even huge photos are
    cheap. Returns a QPixmap, or None if the file can't be read (e.g. a video)."""
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and (size.width() > _THUMB or size.height() > _THUMB):
        reader.setScaledSize(size.scaled(_THUMB, _THUMB, Qt.KeepAspectRatio))
    img = reader.read()
    if img.isNull():
        return None
    return QPixmap.fromImage(img)


class PreviewLoadingDialog(QDialog):
    """A small modal window with a progress bar shown while the first page of
    duplicate thumbnails is generated; it closes itself once they're all ready."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setFixedSize(380, 138)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)
        self.title = QLabel()
        self.title.setProperty("heading", "true")
        layout.addWidget(self.title)
        self.detail = QLabel()
        self.detail.setObjectName("activityLog")
        layout.addWidget(self.detail)
        self.progress = ShimmerProgressBar()
        self.progress.setRange(0, 1)
        layout.addWidget(self.progress)
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(tr.t("review.title"))
        self.title.setText(tr.t("review.generating"))

    def set_progress(self, done, total):
        self.progress.setRange(0, max(total, 1))
        self.progress.setValue(done)
        self.detail.setText(tr.t("review.gen_count", done=done, total=total))


class DuplicateReviewDialog(QDialog):
    """Page through the duplicate sets (10 at a time), see each copy as a
    thumbnail, and tick exactly which files to delete - always keeping at least
    one per set. Selection is remembered across pages; deleting removes the
    ticked files everywhere and tells the parent so it can refresh.

    Every file gets its own thumbnail, but they're decoded lazily off the paint
    path (a few per timer tick, scaled down while decoding, cached per path, and
    with App Nap held off) so opening and page-flipping stay responsive even on
    huge result sets. Videos need no decode - they show a film glyph."""

    def __init__(self, groups, parent=None, on_deleted=None, thumb_cache=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(700, 640)
        self.groups = [list(g) for g in groups]
        self.on_deleted = on_deleted
        self.page = 0
        # Pre-tick every copy except the first in each set - the usual "keep one".
        self.marked = set()
        for g in self.groups:
            self.marked.update(g[1:])
        self._checks = {}       # path -> QCheckBox on the current page
        self._metas = {}        # path -> meta QLabel on the current page
        # Seed the cache with any thumbnails already decoded up front (first page
        # generated in the loading window), so they appear instantly here.
        self._thumb_cache = dict(thumb_cache) if thumb_cache else {}  # path -> QPixmap|None
        self._thumb_queue = []  # [(path, thumb QLabel)] still to decode
        self._activity_token = None

        self._thumb_timer = QTimer(self)
        self._thumb_timer.setInterval(0)
        self._thumb_timer.timeout.connect(self._load_next_thumbs)

        self._del_timer = QTimer(self)
        self._del_timer.setInterval(0)
        self._del_timer.timeout.connect(self._delete_batch)
        self._del_queue = []
        self._deleted = []
        self._del_total = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        self.title_label = QLabel()
        self.title_label.setProperty("heading", "true")
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel()
        self.subtitle_label.setProperty("subheading", "true")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        # "Generating preview" bar, shown while the current page's thumbnails
        # are still decoding.
        self.loading_label = QLabel()
        self.loading_label.setObjectName("activityLog")
        layout.addWidget(self.loading_label)
        self.progress = ShimmerProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 10, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        pager = QHBoxLayout()
        self.prev_btn = QPushButton()
        mark_secondary(self.prev_btn)
        self.prev_btn.clicked.connect(self._prev)
        self.page_label = QLabel()
        self.page_label.setProperty("muted", "true")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.next_btn = QPushButton()
        mark_secondary(self.next_btn)
        self.next_btn.clicked.connect(self._next)
        pager.addWidget(self.prev_btn)
        pager.addStretch(1)
        pager.addWidget(self.page_label)
        pager.addStretch(1)
        pager.addWidget(self.next_btn)
        layout.addLayout(pager)

        nav = QHBoxLayout()
        self.close_btn = QPushButton()
        mark_secondary(self.close_btn)
        self.close_btn.clicked.connect(self.close)
        self.delete_btn = QPushButton()
        mark_primary(self.delete_btn)
        self.delete_btn.clicked.connect(self._delete)
        nav.addWidget(self.close_btn)
        nav.addStretch(1)
        nav.addWidget(self.delete_btn)
        layout.addLayout(nav)

        self.retranslate()
        tr.language_changed.connect(self.retranslate)
        # Show the window first, then build the first page on the next tick so it
        # never blocks the window from appearing.
        self._show_loading(True)
        QTimer.singleShot(0, self._render_page)

    # --- helpers -------------------------------------------------------------
    def _pages(self):
        return max(1, (len(self.groups) + _PER_PAGE - 1) // _PER_PAGE)

    def retranslate(self, *_):
        self.setWindowTitle(tr.t("review.title"))
        self.title_label.setText(tr.t("review.title"))
        self.subtitle_label.setText(tr.t("review.subtitle"))
        self.loading_label.setText(tr.t("review.generating"))
        self.prev_btn.setText(tr.t("review.prev"))
        self.next_btn.setText(tr.t("review.next"))
        self.close_btn.setText(tr.t("settings.close"))
        self._render_page_label()
        self._render_delete_btn()

    def _render_page_label(self):
        self.page_label.setText(tr.t("review.page", page=self.page + 1, pages=self._pages()))

    def _render_delete_btn(self):
        self.delete_btn.setText(tr.t("review.delete_selected", count=len(self.marked)))
        self.delete_btn.setEnabled(bool(self.marked))

    def _show_loading(self, on):
        self.loading_label.setVisible(on)
        self.progress.setVisible(on)

    def _prev(self):
        if self.page > 0:
            self.page -= 1
            self._render_page()

    def _next(self):
        if self.page < self._pages() - 1:
            self.page += 1
            self._render_page()

    def _clear_cards(self):
        while self.cards_layout.count() > 1:        # keep the trailing stretch
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)                   # drop it from view immediately
                w.deleteLater()

    # --- rendering -----------------------------------------------------------
    def _render_page(self):
        self._thumb_timer.stop()
        self._thumb_queue = []
        self._clear_cards()
        self._checks = {}
        self._metas = {}
        start = self.page * _PER_PAGE
        for idx, group in enumerate(self.groups[start:start + _PER_PAGE], start + 1):
            self.cards_layout.insertWidget(self.cards_layout.count() - 1,
                                           self._build_card(idx, group))
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page < self._pages() - 1)
        self._render_page_label()
        self._render_delete_btn()
        self.scroll.verticalScrollBar().setValue(0)

        if self._thumb_queue:
            # Hold off App Nap so decoding keeps going if the app loses focus.
            if self._activity_token is None:
                self._activity_token = begin_activity("Generating duplicate preview")
            self._show_loading(True)
            self._thumb_timer.start()
        else:
            self._end_activity()
            self._show_loading(False)

    def _build_card(self, idx, group):
        card = QFrame()
        card.setProperty("card", "true")
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(8)
        header = QLabel(tr.t("dupfinder.set_header", index=idx, count=len(group)))
        header.setProperty("muted", "true")
        v.addWidget(header)

        for path in group:
            row, thumb = self._build_row(path, group)
            v.addWidget(row)
            self._queue_thumb(path, thumb)
        return card

    def _queue_thumb(self, path, label):
        if os.path.splitext(path)[1].lower() not in PHOTO_EXT:
            label.setText("🎞")                      # videos: no decode needed
            return
        cached = self._thumb_cache.get(path, "MISS")
        if cached == "MISS":
            self._thumb_queue.append((path, label))  # decode later, off the paint path
        elif cached is not None:
            label.setPixmap(cached)
        else:
            label.setText("🎞")

    def _build_row(self, path, group):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        thumb = QLabel()
        thumb.setFixedSize(_THUMB, _THUMB)
        thumb.setAlignment(Qt.AlignCenter)
        h.addWidget(thumb)

        info = QVBoxLayout()
        info.setSpacing(2)
        name = QLabel(os.path.basename(path))
        meta = QLabel()
        meta.setTextFormat(Qt.RichText)
        info.addWidget(name)
        info.addWidget(meta)
        h.addLayout(info, 1)

        chk = QCheckBox(tr.t("review.delete_checkbox"))
        chk.setChecked(path in self.marked)
        chk.toggled.connect(lambda checked, p=path, g=group: self._toggle(p, g, checked))
        h.addWidget(chk)

        self._checks[path] = chk
        self._metas[path] = meta
        self._set_meta(path)
        return row, thumb

    def _size_str(self, path):
        try:
            return human_size(os.path.getsize(path))
        except OSError:
            return ""

    def _set_meta(self, path):
        meta = self._metas.get(path)
        if meta is None:
            return
        marked = path in self.marked
        color = COLOR_ORANGE if marked else COLOR_GREEN
        tag = tr.t("dupfinder.duplicate") if marked else tr.t("dupfinder.keep")
        meta.setText(f'<span style="color:{color}; font-weight:bold;">{tag}</span>'
                     f'&nbsp;&nbsp;<span style="color:#8A8D96;">{self._size_str(path)}</span>')

    # --- lazy thumbnails -----------------------------------------------------
    def _load_next_thumbs(self):
        budget = _THUMBS_PER_TICK
        while budget and self._thumb_queue:
            path, label = self._thumb_queue.pop(0)
            pix = self._decode_thumb(path)
            self._thumb_cache[path] = pix
            if pix is not None:
                label.setPixmap(pix)
            else:
                label.setText("🎞")
            budget -= 1
        if not self._thumb_queue:
            self._thumb_timer.stop()
            self._end_activity()
            self._show_loading(False)

    def _decode_thumb(self, path):
        return decode_thumb(path)

    # --- selection -----------------------------------------------------------
    def _toggle(self, path, group, checked):
        if checked:
            kept = [p for p in group if p not in self.marked]
            if len(kept) <= 1:              # this file is the last one kept
                chk = self._checks.get(path)
                if chk:
                    chk.blockSignals(True)
                    chk.setChecked(False)
                    chk.blockSignals(False)
                QToolTip.showText(QCursor.pos(), tr.t("review.min_keep"))
                return
            self.marked.add(path)
        else:
            self.marked.discard(path)
        self._set_meta(path)
        self._render_delete_btn()

    # --- deletion ------------------------------------------------------------
    def _delete(self):
        if not self.marked:
            QMessageBox.information(self, tr.t("review.title"), tr.t("review.none_selected"))
            return
        n = len(self.marked)
        # Build the confirm box explicitly and check *which button* was clicked
        # by identity - the QMessageBox.question convenience can report the wrong
        # standard button on macOS, which made "No" still delete.
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle(tr.t("dupfinder.confirm_title"))
        box.setText(tr.t("review.confirm", count=n))
        delete_button = box.addButton(tr.t("review.confirm_delete"), QMessageBox.DestructiveRole)
        cancel_button = box.addButton(tr.t("review.confirm_cancel"), QMessageBox.RejectRole)
        box.setDefaultButton(cancel_button)
        box.exec()
        if box.clickedButton() is not delete_button:
            return
        # Delete in batches with a real progress bar - thousands of files would
        # otherwise freeze the window solid.
        self._thumb_timer.stop()
        self._del_queue = list(self.marked)
        self._del_total = len(self._del_queue)
        self._deleted = []
        self._set_busy(True)
        if self._activity_token is None:
            self._activity_token = begin_activity("Deleting duplicates")
        self.progress.setRange(0, self._del_total)
        self.progress.setValue(0)
        self.loading_label.setText(tr.t("review.deleting", pct=0))
        self._show_loading(True)
        self._del_timer.start()

    def _delete_batch(self):
        budget = 200
        while budget and self._del_queue:
            p = self._del_queue.pop()
            try:
                trash_or_remove(p)
                self._deleted.append(p)
            except OSError:
                pass
            budget -= 1
        done = self._del_total - len(self._del_queue)
        pct = int(done * 100 / self._del_total) if self._del_total else 100
        self.progress.setValue(done)
        self.loading_label.setText(tr.t("review.deleting", pct=pct))
        if not self._del_queue:
            self._del_timer.stop()
            self._finish_delete()

    def _finish_delete(self):
        deleted = self._deleted
        dset = set(deleted)
        self.groups = [[p for p in g if p not in dset] for g in self.groups]
        self.groups = [g for g in self.groups if len(g) >= 2]
        self.marked = set()          # nothing pre-selected after a delete
        if self.on_deleted:
            self.on_deleted(deleted)
        self._end_activity()
        self.progress.setRange(0, 0)      # back to the busy style for thumbnails
        self._show_loading(False)
        self._set_busy(False)

        QMessageBox.information(self, tr.t("review.title"),
                                tr.t("review.deleted", count=len(deleted)))
        if not self.groups:
            self.close()
            return
        self.page = min(self.page, self._pages() - 1)
        self._render_page()

    def _set_busy(self, busy):
        for b in (self.delete_btn, self.prev_btn, self.next_btn, self.close_btn):
            b.setEnabled(not busy)

    def _end_activity(self):
        if self._activity_token is not None:
            end_activity(self._activity_token)
            self._activity_token = None

    def closeEvent(self, event):
        self._thumb_timer.stop()
        self._del_timer.stop()
        self._end_activity()
        super().closeEvent(event)
