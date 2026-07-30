"""
Native macOS window chrome for a Tahoe / Finder / Tailscale look, reached
through the Objective-C runtime via ctypes (no pyobjc dependency).

It does two things to a Qt top-level window:
  1. Hides the title bar and lets content run full height, while keeping the
     native traffic-light buttons and the window's rounded corners.
  2. Slides a real NSVisualEffectView (the system blur) behind the whole
     window, so any Qt widget left transparent - the sidebar - shows live
     vibrancy, exactly like Finder's sidebar. Opaque widgets cover it.

macOS Tahoe inserts an opaque NSScrollPocket "backdrop" sibling between the
blur and Qt's content, which would hide the vibrancy; we keep those hidden.

Everything is guarded: on non-macOS, or if any native call fails, it silently
does nothing and the app keeps its normal opaque look.
"""

import sys
import platform
import ctypes
import ctypes.util

# NSWindowStyleMask / enum constants
_FULL_SIZE_CONTENT = 1 << 15          # NSWindowStyleMaskFullSizeContentView
_TITLE_HIDDEN = 1                     # NSWindowTitleHidden
_MATERIAL_SIDEBAR = 7                 # NSVisualEffectMaterialSidebar
_BLEND_BEHIND_WINDOW = 0              # NSVisualEffectBlendingModeBehindWindow
_STATE_ACTIVE = 1                     # NSVisualEffectStateActive
_VIEW_WIDTH_SIZABLE = 2
_VIEW_HEIGHT_SIZABLE = 16
_WINDOW_BELOW = -1                    # NSWindowBelow


class _NSRect(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double),
                ("w", ctypes.c_double), ("h", ctypes.c_double)]


class _NSPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


_IS_ARM = platform.machine() == "arm64"


try:
    _objc = ctypes.CDLL(ctypes.util.find_library("objc"))
    _objc.objc_getClass.restype = ctypes.c_void_p
    _objc.objc_getClass.argtypes = [ctypes.c_char_p]
    _objc.sel_registerName.restype = ctypes.c_void_p
    _objc.sel_registerName.argtypes = [ctypes.c_char_p]
    _send = _objc.objc_msgSend
except Exception:
    _objc = None


def _sel(name):
    return _objc.sel_registerName(name.encode())


def _cls(name):
    return _objc.objc_getClass(name.encode())


def _msg(receiver, selector, *args, restype=ctypes.c_void_p, argtypes=()):
    _send.restype = restype
    _send.argtypes = [ctypes.c_void_p, ctypes.c_void_p] + list(argtypes)
    return _send(receiver, selector, *args)


def _is_cocoa():
    from PySide6.QtGui import QGuiApplication
    return QGuiApplication.platformName() == "cocoa"


def _ns_window(widget):
    nsview = int(widget.winId())
    return _msg(nsview, _sel("window"))


def _view_frame(view):
    """Read an NSView's frame. On Intel a 32-byte struct return must go through
    objc_msgSend_stret; on Apple Silicon the regular msgSend returns it."""
    if _IS_ARM:
        _send.restype = _NSRect
        _send.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        return _send(view, _sel("frame"))
    stret = _objc.objc_msgSend_stret
    stret.restype = None
    stret.argtypes = [ctypes.POINTER(_NSRect), ctypes.c_void_p, ctypes.c_void_p]
    r = _NSRect()
    stret(ctypes.byref(r), view, _sel("frame"))
    return r


def _center_traffic_lights(widget, bar_height):
    """Move the three traffic-light buttons down so they sit vertically centred
    in a taller top bar - a single cohesive toolbar, the way Tailscale does it,
    rather than the buttons clinging to the very top edge."""
    if _objc is None or sys.platform != "darwin" or not _is_cocoa():
        return
    try:
        window = _ns_window(widget)
        if not window:
            return
        height = float(widget.height())          # window/frame-view height, points
        for i in (0, 1, 2):                       # close, miniaturize, zoom
            btn = _msg(window, _sel("standardWindowButton:"), ctypes.c_long(i),
                       argtypes=[ctypes.c_long])
            if not btn:
                continue
            fr = _view_frame(btn)
            # Frame view coords are bottom-left origin, y up: put the button's
            # centre at bar_height/2 from the top.
            new_y = height - bar_height / 2.0 - fr.h / 2.0
            _msg(btn, _sel("setFrameOrigin:"), _NSPoint(fr.x, new_y),
                 argtypes=[_NSPoint])
    except Exception:
        pass


def _hide_backdrops(widget):
    """Hide the Tahoe NSScrollPocket backdrop views that AppKit slips above our
    vibrancy layer - otherwise they'd paint over it and kill the blur. Safe to
    call repeatedly; the backdrop appears a beat after the window is shown."""
    if _objc is None or sys.platform != "darwin" or not _is_cocoa():
        return
    try:
        window = _ns_window(widget)
        if not window:
            return
        content_view = _msg(window, _sel("contentView"))
        superview = _msg(content_view, _sel("superview"))
        subs = _msg(superview, _sel("subviews"))
        count = _msg(subs, _sel("count"), restype=ctypes.c_ulong)
        for i in range(count):
            v = _msg(subs, _sel("objectAtIndex:"), ctypes.c_ulong(i), argtypes=[ctypes.c_ulong])
            name_ptr = _msg(_msg(v, _sel("className")), _sel("UTF8String"), restype=ctypes.c_char_p)
            name = name_ptr.decode() if name_ptr else ""
            if "Backdrop" in name or "Pocket" in name:
                _msg(v, _sel("setHidden:"), ctypes.c_bool(True), argtypes=[ctypes.c_bool])
    except Exception:
        pass


def enable_tahoe_chrome(widget, material=_MATERIAL_SIDEBAR, titlebar_height=None):
    """Apply the frameless-titlebar + behind-window vibrancy treatment to a
    shown Qt top-level widget. Must be called after the native window exists
    (i.e. after show()). If titlebar_height is given, the traffic-light buttons
    are centred vertically in a top bar of that height. Returns True on
    success."""
    if _objc is None or sys.platform != "darwin":
        return False
    # Only touch native window internals when there's a real Cocoa NSView.
    # Under the "offscreen" platform winId() is not an NSView, and an
    # Objective-C exception there would bypass Python's try/except and abort.
    if not _is_cocoa():
        return False
    try:
        window = _ns_window(widget)
        if not window:
            return False

        # --- title bar: transparent, hidden text, content runs full height ---
        style = _msg(window, _sel("styleMask"), restype=ctypes.c_ulong)
        _msg(window, _sel("setStyleMask:"), ctypes.c_ulong(style | _FULL_SIZE_CONTENT),
             argtypes=[ctypes.c_ulong])
        _msg(window, _sel("setTitlebarAppearsTransparent:"), ctypes.c_bool(True),
             argtypes=[ctypes.c_bool])
        _msg(window, _sel("setTitleVisibility:"), ctypes.c_long(_TITLE_HIDDEN),
             argtypes=[ctypes.c_long])

        # --- window must be non-opaque with a clear backdrop for the blur ---
        _msg(window, _sel("setOpaque:"), ctypes.c_bool(False), argtypes=[ctypes.c_bool])
        clear = _msg(_cls("NSColor"), _sel("clearColor"))
        _msg(window, _sel("setBackgroundColor:"), clear, argtypes=[ctypes.c_void_p])

        # --- NSVisualEffectView behind Qt's content ---
        # Qt's winId() IS the window's contentView, so a child of it would draw
        # ON TOP. Instead we drop the effect into the content view's superview,
        # below the content view. Qt's content view is translucent, so wherever
        # a Qt widget is transparent - the sidebar - this blur shows through.
        content_view = _msg(window, _sel("contentView"))
        superview = _msg(content_view, _sel("superview"))
        w, h = float(widget.width()), float(widget.height())
        frame = _NSRect(0.0, 0.0, w, h)
        effect = _msg(_cls("NSVisualEffectView"), _sel("alloc"))
        effect = _msg(effect, _sel("initWithFrame:"), frame, argtypes=[_NSRect])
        _msg(effect, _sel("setMaterial:"), ctypes.c_long(material), argtypes=[ctypes.c_long])
        _msg(effect, _sel("setBlendingMode:"), ctypes.c_long(_BLEND_BEHIND_WINDOW),
             argtypes=[ctypes.c_long])
        _msg(effect, _sel("setState:"), ctypes.c_long(_STATE_ACTIVE), argtypes=[ctypes.c_long])
        _msg(effect, _sel("setAutoresizingMask:"),
             ctypes.c_ulong(_VIEW_WIDTH_SIZABLE | _VIEW_HEIGHT_SIZABLE),
             argtypes=[ctypes.c_ulong])
        target = superview if superview else content_view
        _msg(target, _sel("addSubview:positioned:relativeTo:"),
             effect, ctypes.c_long(_WINDOW_BELOW), content_view,
             argtypes=[ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p])

        if titlebar_height:
            _center_traffic_lights(widget, titlebar_height)

        # The Tahoe backdrop is inserted a beat later, so hide it now and again
        # shortly after (it would otherwise paint over the blur). Re-centre the
        # traffic lights on the same beats, since AppKit may reset them.
        def _touch_up():
            _hide_backdrops(widget)
            if titlebar_height:
                _center_traffic_lights(widget, titlebar_height)

        _touch_up()
        from PySide6.QtCore import QTimer
        for delay in (50, 200, 500, 1000):
            QTimer.singleShot(delay, _touch_up)
        return True
    except Exception:
        return False
