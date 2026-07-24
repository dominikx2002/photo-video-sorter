#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_app.py - Photo & Video Sorter

A 4-step wizard UI (Source -> Destination & Options -> Sorting -> Summary)
styled after the Raspberry Pi Imager: light background, a step list in a
left sidebar (current step shown as a solid rounded "pill"), and rounded
buttons/cards throughout. Sorting runs on a background thread; the GUI is
only ever touched from the main thread via a queue - the safe way to do
it with Tkinter.
"""

import os
import sys
import subprocess
import queue
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from sorter_logic import run_sort, scan_source

# ----------------------------------------------------------------------
# Look & feel
# ----------------------------------------------------------------------
# These values come straight from the real Raspberry Pi Imager's Style.qml
# (the user pulled it from the app itself) - not guesses from a screenshot.
COLOR_PRIMARY = "#ab1e3a"              # raspberryRed
COLOR_PRIMARY_PRESSED = "#8f122c"      # button2FocusedBackgroundColor
COLOR_PRIMARY_HOVER_BG = "#eac7ce"     # button2HoveredBackgroundColor
COLOR_PRIMARY_HOVER_TEXT = "#ab1e3a"   # button2HoveredForegroundColor
COLOR_PRIMARY_LIGHT = "#e3b3bf"        # disabled tint (derived, not in Style.qml)
COLOR_SECONDARY_HOVER_BG = "#f2f2f2"   # buttonHoveredBackgroundColor
COLOR_SECONDARY_BORDER = "#dcdcdc"     # popupBorderColor
COLOR_GREEN = "#6cc04a"                # progressBarVerifyForegroundColor
COLOR_ORANGE = "#D9822B"               # not in Style.qml - kept for our own warnings
COLOR_BG = "#ffffff"                   # mainBackgroundColor
COLOR_CARD_BG = "#f5f5f5"              # titleBackgroundColor
COLOR_TEXT = "#1a1a1a"                 # textDescriptionColor
COLOR_MUTED = "#646464"                # textMetadataColor
COLOR_BORDER = "#dcdcdc"               # popupBorderColor
COLOR_SIDEBAR_VISITED_TEXT = "#ab1e3a"  # sidebarTextOnInactiveColor
COLOR_SIDEBAR_FUTURE_TEXT = "#E0E0E0"   # sidebarTextDisabledColor
COLOR_SIDEBAR_DIVIDER = "#ab1e3a"       # sidebarBorderColour

FONT_FAMILY = "Roboto"   # the real app bundles Roboto; Tk falls back to the
                          # system default automatically if it's not installed
FONT_MONO = "Menlo"

STEP_TITLES = ["Source Folder", "Destination & Options", "Sorting", "Summary"]


# ----------------------------------------------------------------------
# Where logs live
# ----------------------------------------------------------------------
def get_log_dir():
    """
    While developing (running via 'python3 gui_app.py'), logs are written
    next to this script, in a 'logs' subfolder - easy to find in VS Code.

    Once packaged as a .app with PyInstaller, sys.frozen is True. App
    bundles are meant to be read-only, so packaged builds write logs to
    the standard macOS location for per-app logs instead:
    ~/Library/Logs/PhotoSorterApp (also visible in Console.app).
    """
    if getattr(sys, "frozen", False):
        base = os.path.expanduser("~/Library/Logs/PhotoSorterApp")
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(base, exist_ok=True)
    return base


def get_log_path(parent_name):
    safe_name = "".join(c for c in parent_name.strip() if c.isalnum() or c in " _-") or "sort"
    return os.path.join(get_log_dir(), f"sort_log_{safe_name}_{datetime.now():%Y%m%d_%H%M%S}.txt")


# ----------------------------------------------------------------------
# Rounded-corner building blocks
#
# Tkinter has no native rounded corners, so these draw them by hand on a
# Canvas: a rounded rectangle is a 12-point polygon with smooth=True,
# which Tk renders with curved joins. Both widgets always paint their own
# Canvas background as COLOR_BG, because every place they get used in
# this app sits directly on a white page - if that ever changes, the
# "outside the rounded shape" area would show the wrong color.
# ----------------------------------------------------------------------
def _round_rect_points(x1, y1, x2, y2, radius):
    return [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]


class RoundedButton(tk.Canvas):
    def __init__(self, master, text, command=None, style="primary",
                 width=None, height=30, radius=7, font=None, state="normal", pad_x=16):
        super().__init__(master, height=height, bg=COLOR_BG, highlightthickness=0)
        self.command = command
        self.style = style
        self.radius = radius
        self.text = text
        self.font = font or (FONT_FAMILY, 11, "bold" if style == "primary" else "normal")
        self.state = state
        self.height = height

        text_w = tkfont.Font(font=self.font).measure(text)
        self.width = width or (text_w + pad_x * 2)
        self.configure(width=self.width)

        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        try:
            self.configure(cursor="pointinghand")
        except tk.TclError:
            pass

    def _colors(self):
        # "primary" mirrors the real app's Button2 (solid red CTA, e.g. "Next");
        # "secondary" mirrors its plain Button (white bg, red text, e.g. "Back").
        if self.style == "primary":
            return {"normal": COLOR_PRIMARY, "hover": COLOR_PRIMARY_HOVER_BG,
                     "disabled": COLOR_PRIMARY_LIGHT,
                     "text": "white", "text_hover": COLOR_PRIMARY_HOVER_TEXT,
                     "text_disabled": "white", "border": None}
        return {"normal": "white", "hover": COLOR_SECONDARY_HOVER_BG, "disabled": "white",
                 "text": COLOR_PRIMARY, "text_hover": COLOR_PRIMARY,
                 "text_disabled": "#C9C9C9", "border": COLOR_SECONDARY_BORDER}

    def _draw(self, hover=False):
        self.delete("all")
        c = self._colors()
        fill = c["disabled"] if self.state == "disabled" else (c["hover"] if hover else c["normal"])
        outline = c["border"] or fill
        pts = _round_rect_points(1, 1, self.width - 1, self.height - 1, self.radius)
        self.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=1)
        if self.state == "disabled":
            text_color = c["text_disabled"]
        elif hover:
            text_color = c["text_hover"]
        else:
            text_color = c["text"]
        self.create_text(self.width / 2, self.height / 2, text=self.text,
                          fill=text_color, font=self.font)

    def _on_enter(self, _event):
        if self.state != "disabled":
            self._draw(hover=True)

    def _on_leave(self, _event):
        if self.state != "disabled":
            self._draw(hover=False)

    def _on_click(self, _event):
        if self.state != "disabled" and self.command:
            self.command()

    def configure(self, **kwargs):
        redraw = False
        if "state" in kwargs:
            self.state = kwargs.pop("state")
            redraw = True
        if "text" in kwargs:
            self.text = kwargs.pop("text")
            redraw = True
        if kwargs:
            super().configure(**kwargs)
        if redraw:
            self._draw()

    config = configure


class RoundedFrame(tk.Canvas):
    """A rounded-corner panel. Put your content in `.inner` (a plain Frame)."""

    def __init__(self, master, radius=8, bg_color=COLOR_CARD_BG, border_color=None, height=None):
        super().__init__(master, height=height, bg=COLOR_BG, highlightthickness=0)
        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.inner = tk.Frame(self, bg=bg_color)
        self._window = self.create_window(0, 0, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        w, h = max(event.width, 2), max(event.height, 2)
        self.delete("bg")
        pts = _round_rect_points(1, 1, w - 1, h - 1, self.radius)
        shape = self.create_polygon(pts, smooth=True, fill=self.bg_color,
                                     outline=self.border_color or self.bg_color, width=1, tags="bg")
        self.tag_lower(shape)
        self.itemconfigure(self._window, width=w, height=h)


# ----------------------------------------------------------------------
# Sidebar - plain step labels, current step highlighted as a solid pill
# (this mirrors Raspberry Pi Imager's setup-steps sidebar)
# ----------------------------------------------------------------------
class Sidebar(tk.Frame):
    def __init__(self, master, steps, **kwargs):
        super().__init__(master, bg=COLOR_BG, **kwargs)
        self.steps = steps
        self.rows = []
        self.current = 0
        self.completed = set()

        tk.Label(self, text="SETUP STEPS", bg=COLOR_BG, fg=COLOR_PRIMARY,
                  font=(FONT_FAMILY, 11, "bold")).pack(anchor="w", padx=18, pady=(22, 3))
        tk.Label(self, text="Photo & Video Sorter", bg=COLOR_BG, fg=COLOR_MUTED,
                  font=(FONT_FAMILY, 9)).pack(anchor="w", padx=18, pady=(0, 16))

        for i, step in enumerate(steps):
            row = tk.Canvas(self, height=32, bg=COLOR_BG, highlightthickness=0)
            row.pack(fill="x", padx=10, pady=1)
            row.bind("<Configure>", lambda _e, idx=i: self._draw_row(idx))
            self.rows.append(row)

        tk.Frame(self, bg=COLOR_SIDEBAR_DIVIDER, width=1).place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

    def _draw_row(self, idx):
        canvas = self.rows[idx]
        canvas.delete("all")
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        if idx == self.current:
            # Current step: solid rounded pill (sidebarActiveBackgroundColor).
            pts = _round_rect_points(0, 1, w, h - 1, 4)
            canvas.create_polygon(pts, smooth=True, fill=COLOR_PRIMARY, outline="")
            canvas.create_text(14, h / 2, text=self.steps[idx], fill="white",
                                anchor="w", font=(FONT_FAMILY, 11, "bold"))
        elif idx in self.completed:
            # Already-visited step: red text, no pill (sidebarTextOnInactiveColor).
            canvas.create_text(14, h / 2, text=self.steps[idx], fill=COLOR_SIDEBAR_VISITED_TEXT,
                                anchor="w", font=(FONT_FAMILY, 11))
        else:
            # Not reached yet: pale gray (sidebarTextDisabledColor).
            canvas.create_text(14, h / 2, text=self.steps[idx], fill=COLOR_SIDEBAR_FUTURE_TEXT,
                                anchor="w", font=(FONT_FAMILY, 11))

    def set_state(self, current, completed=None):
        self.current = current
        self.completed = completed or set()
        for idx in range(len(self.rows)):
            self._draw_row(idx)


# ----------------------------------------------------------------------
# Main app
# ----------------------------------------------------------------------
class PhotoSorterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo & Video Sorter")
        self.root.geometry("760x560")
        self.root.minsize(700, 520)
        self.root.configure(bg=COLOR_BG)

        # --- form state ---
        self.parent_name = tk.StringVar()
        self.src_folder = tk.StringVar()
        self.dst_folder = tk.StringVar()
        self.use_folder_date = tk.BooleanVar(value=True)

        # --- run state ---
        self.scan_result = None
        self.last_stats = None
        self.last_log_path = None
        self.busy = False
        self.msg_queue = queue.Queue()
        self.current_step = 0
        self.completed_steps = set()

        self._setup_style()
        self._build_layout()
        self.go_to_step(0)

    # ------------------------------------------------------------------
    # ttk styling (must switch away from the 'aqua' theme on macOS, or
    # ttk ignores color overrides and renders native gray widgets)
    # ------------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)

        style.configure("Heading.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                         font=(FONT_FAMILY, 18, "bold"))
        style.configure("Sub.TLabel", background=COLOR_BG, foreground=COLOR_MUTED,
                         font=(FONT_FAMILY, 11), wraplength=440, justify="left")
        style.configure("Field.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                         font=(FONT_FAMILY, 12, "bold"))
        style.configure("Status.TLabel", background=COLOR_BG, foreground=COLOR_MUTED,
                         font=(FONT_FAMILY, 11))
        style.configure("Card.TLabel", background=COLOR_CARD_BG, foreground=COLOR_TEXT,
                         font=(FONT_FAMILY, 11))
        style.configure("CardMuted.TLabel", background=COLOR_CARD_BG, foreground=COLOR_MUTED,
                         font=(FONT_FAMILY, 10))
        style.configure("CardNumber.TLabel", background=COLOR_CARD_BG, foreground=COLOR_PRIMARY,
                         font=(FONT_FAMILY, 16, "bold"))

        style.configure("TEntry", fieldbackground="white", foreground=COLOR_TEXT,
                         padding=6, relief="flat", bordercolor=COLOR_BORDER)
        style.map("TEntry", fieldbackground=[("readonly", COLOR_CARD_BG), ("disabled", COLOR_CARD_BG)])

        style.configure("TCheckbutton", background=COLOR_BG, foreground=COLOR_TEXT,
                         font=(FONT_FAMILY, 10))

        style.configure("Primary.Horizontal.TProgressbar", troughcolor=COLOR_CARD_BG,
                         background=COLOR_PRIMARY, bordercolor=COLOR_CARD_BG,
                         lightcolor=COLOR_PRIMARY, darkcolor=COLOR_PRIMARY, thickness=10)

    # ------------------------------------------------------------------
    # Layout: sidebar + content area holding 4 stacked step pages
    # ------------------------------------------------------------------
    def _build_layout(self):
        container = tk.Frame(self.root, bg=COLOR_BG)
        container.pack(fill="both", expand=True)

        self.sidebar = Sidebar(container, STEP_TITLES, width=170)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(container, bg=COLOR_BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.page1 = self._build_step1(self.content)
        self.page2 = self._build_step2(self.content)
        self.page3 = self._build_step3(self.content)
        self.page4 = self._build_step4(self.content)

        for page in (self.page1, self.page2, self.page3, self.page4):
            page.grid(row=0, column=0, sticky="nsew")

    def go_to_step(self, idx):
        self.current_step = idx
        [self.page1, self.page2, self.page3, self.page4][idx].tkraise()
        self.sidebar.set_state(current=idx, completed=self.completed_steps)
        if idx == 3:
            self.populate_summary()

    # ==================================================================
    # STEP 1 - Source folder
    # ==================================================================
    def _build_step1(self, parent):
        page = ttk.Frame(parent, padding=(24, 20, 24, 18))

        ttk.Label(page, text="Select Source Folder", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text=("Choose the folder to scan. All subfolders are searched automatically for "
                  "photos and videos (JPG, PNG, HEIC, MP4, MOV, DNG, WEBP, and more)."),
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(6, 16))

        row = ttk.Frame(page)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.src_folder, state="readonly").pack(
            side="left", fill="x", expand=True, ipady=4)
        self.step1_choose_btn = RoundedButton(row, text="Choose Folder...", style="secondary",
                                               command=self.choose_src)
        self.step1_choose_btn.pack(side="left", padx=(10, 0))

        self.step1_progress = ttk.Progressbar(page, mode="indeterminate",
                                               style="Primary.Horizontal.TProgressbar")

        self.step1_status_var = tk.StringVar(value="No folder selected yet.")
        ttk.Label(page, textvariable=self.step1_status_var, style="Status.TLabel").pack(
            anchor="w", pady=(12, 2))
        self.step1_detail_var = tk.StringVar(value="")
        ttk.Label(page, textvariable=self.step1_detail_var, style="Status.TLabel").pack(anchor="w")

        nav = ttk.Frame(page)
        nav.pack(side="bottom", fill="x", pady=(18, 0))
        self.step1_continue_btn = RoundedButton(nav, text="Continue", style="primary",
                                                 command=self.step1_continue, state="disabled")
        self.step1_continue_btn.pack(side="right")

        return page

    def choose_src(self):
        folder = filedialog.askdirectory(title="Select the folder to scan")
        if not folder:
            return
        self.src_folder.set(folder)
        self.scan_result = None
        self.step1_continue_btn.configure(state="disabled")
        self.step1_choose_btn.configure(state="disabled")
        self.step1_detail_var.set("")
        self.step1_status_var.set("Scanning folder for media files... this can take a moment for large libraries.")
        self.step1_progress.pack(fill="x", pady=(4, 0))
        self.step1_progress.start(12)
        self.busy = True
        threading.Thread(target=self._scan_worker, args=(folder,), daemon=True).start()
        self.root.after(100, self.poll_queue)

    def _scan_worker(self, folder):
        try:
            result = scan_source(folder)
            self.msg_queue.put(("scan_done", result))
        except Exception as e:
            self.msg_queue.put(("scan_error", str(e)))

    # ==================================================================
    # STEP 2 - Destination & options
    # ==================================================================
    def _build_step2(self, parent):
        page = ttk.Frame(parent, padding=(24, 20, 24, 18))

        ttk.Label(page, text="Destination & Options", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text="Choose where sorted files should be copied, and give this collection a name.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(6, 16))

        ttk.Label(page, text="Collection name (e.g. a person's name)", style="Field.TLabel").pack(anchor="w")
        entry = ttk.Entry(page, textvariable=self.parent_name)
        entry.pack(fill="x", pady=(4, 14), ipady=3)

        ttk.Label(page, text="Destination folder", style="Field.TLabel").pack(anchor="w")
        row = ttk.Frame(page)
        row.pack(fill="x", pady=(4, 14))
        ttk.Entry(row, textvariable=self.dst_folder, state="readonly").pack(
            side="left", fill="x", expand=True, ipady=4)
        RoundedButton(row, text="Choose Folder...", style="secondary",
                      command=self.choose_dst).pack(side="left", padx=(10, 0))

        ttk.Checkbutton(
            page,
            text="Use the date from the folder name when no EXIF/video date is available (e.g. 202401)",
            variable=self.use_folder_date,
        ).pack(anchor="w", pady=(3, 14))

        preview_card = RoundedFrame(page, bg_color=COLOR_CARD_BG, height=60)
        preview_card.pack(fill="x", pady=(0, 8))
        ttk.Label(preview_card.inner, text="Files will be organized as:", style="CardMuted.TLabel").pack(
            anchor="w", padx=12, pady=(10, 0))
        self.step2_preview_var = tk.StringVar()
        ttk.Label(preview_card.inner, textvariable=self.step2_preview_var, style="Card.TLabel").pack(
            anchor="w", padx=12, pady=(2, 10))

        self.parent_name.trace_add("write", self._update_step2_preview)
        self.dst_folder.trace_add("write", self._update_step2_preview)
        self._update_step2_preview()

        nav = ttk.Frame(page)
        nav.pack(side="bottom", fill="x", pady=(16, 0))
        RoundedButton(nav, text="Back", style="secondary",
                      command=lambda: self.go_to_step(0)).pack(side="left")
        self.step2_continue_btn = RoundedButton(nav, text="Continue", style="primary",
                                                 command=self.step2_continue, state="disabled")
        self.step2_continue_btn.pack(side="right")

        self.parent_name.trace_add("write", self._validate_step2)
        self.dst_folder.trace_add("write", self._validate_step2)

        return page

    def _update_step2_preview(self, *_args):
        dst = self.dst_folder.get().strip() or "<destination>"
        name = self.parent_name.get().strip() or "<collection name>"
        self.step2_preview_var.set(f"{dst}/{name}/2024/2024-01/photo.jpg")

    def _validate_step2(self, *_args):
        ok = bool(self.parent_name.get().strip()) and bool(self.dst_folder.get().strip())
        self.step2_continue_btn.configure(state="normal" if ok else "disabled")

    def choose_dst(self):
        folder = filedialog.askdirectory(title="Select the destination folder")
        if folder:
            self.dst_folder.set(folder)

    def step1_continue(self):
        self.completed_steps.add(0)
        self.go_to_step(1)

    def step2_continue(self):
        self.completed_steps.add(1)
        self.reset_step3_ui()
        self.go_to_step(2)

    # ==================================================================
    # STEP 3 - Sorting
    # ==================================================================
    def _build_step3(self, parent):
        page = ttk.Frame(parent, padding=(24, 20, 24, 18))

        ttk.Label(page, text="Sorting Files", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            page,
            text="Copying files into year/month folders. Originals are never modified or deleted.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(6, 12))

        self.step3_summary_var = tk.StringVar()
        ttk.Label(page, textvariable=self.step3_summary_var, style="Status.TLabel").pack(anchor="w", pady=(0, 14))

        self.step3_body = ttk.Frame(page)
        self.step3_body.pack(fill="both", expand=True)

        self.step3_start_btn = RoundedButton(self.step3_body, text="Start Sorting", style="primary",
                                              height=36, font=(FONT_FAMILY, 12, "bold"),
                                              command=self.start_sorting)

        self.step3_progress_container = ttk.Frame(self.step3_body)
        self.progress = ttk.Progressbar(self.step3_progress_container, mode="determinate",
                                         style="Primary.Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        self.step3_progress_var = tk.StringVar(value="")
        ttk.Label(self.step3_progress_container, textvariable=self.step3_progress_var,
                  style="Status.TLabel").pack(anchor="w", pady=(6, 10))

        log_card = RoundedFrame(self.step3_progress_container, bg_color="#FCFCFD",
                                 border_color=COLOR_BORDER)
        log_card.pack(fill="both", expand=True)

        self.log_text = tk.Text(log_card.inner, wrap="none", state="disabled", height=10,
                                 bg="#FCFCFD", fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                                 font=(FONT_MONO, 10), relief="flat", bd=0, highlightthickness=0,
                                 padx=8, pady=6)
        yscroll = ttk.Scrollbar(log_card.inner, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=yscroll.set)
        self.log_text.pack(side="left", fill="both", expand=True, pady=6)
        yscroll.pack(side="right", fill="y", padx=(0, 4), pady=6)

        self.log_text.tag_configure("copy", foreground=COLOR_GREEN)
        self.log_text.tag_configure("exif", foreground="#2A6FB0")
        self.log_text.tag_configure("video", foreground="#2A6FB0")
        self.log_text.tag_configure("folder_date", foreground=COLOR_ORANGE)
        self.log_text.tag_configure("no_date", foreground=COLOR_ORANGE)
        self.log_text.tag_configure("error", foreground=COLOR_PRIMARY)
        self.log_text.tag_configure("skip", foreground="#A9ACB1")
        self.log_text.tag_configure("heading", foreground=COLOR_TEXT, font=(FONT_MONO, 10, "bold"))

        nav = ttk.Frame(page)
        nav.pack(side="bottom", fill="x", pady=(16, 0))
        self.step3_back_btn = RoundedButton(nav, text="Back", style="secondary",
                                             command=lambda: self.go_to_step(1))
        self.step3_back_btn.pack(side="left")
        self.step3_continue_btn = RoundedButton(nav, text="View Summary", style="primary",
                                                 command=self.step3_continue, state="disabled")
        self.step3_continue_btn.pack(side="right")

        return page

    def reset_step3_ui(self):
        src = self.src_folder.get()
        dst = self.dst_folder.get()
        name = self.parent_name.get().strip()
        fallback = "on" if self.use_folder_date.get() else "off"
        self.step3_summary_var.set(
            f"Source: {src}    |    Destination: {dst}/{name}    |    Folder-name fallback: {fallback}"
        )
        self.step3_progress_container.pack_forget()
        self.step3_start_btn.pack(pady=40)
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.progress.configure(value=0, maximum=1)
        self.step3_progress_var.set("")
        self.step3_continue_btn.configure(state="disabled")
        self.step3_back_btn.configure(state="normal")

    def start_sorting(self):
        self.step3_start_btn.pack_forget()
        self.step3_progress_container.pack(fill="both", expand=True)
        self.step3_back_btn.configure(state="disabled")
        self.busy = True

        parent = self.parent_name.get().strip()
        src = self.src_folder.get().strip()
        dst = self.dst_folder.get().strip()
        use_folder_date = self.use_folder_date.get()
        log_path = get_log_path(parent)

        def cb_log(msg):
            self.msg_queue.put(("log", msg))

        def cb_progress(done, total):
            self.msg_queue.put(("progress", done, total))

        def worker():
            try:
                stats, path = run_sort(parent, src, dst, use_folder_date, log_path, cb_log, cb_progress)
                self.msg_queue.put(("done", stats, path))
            except Exception as e:
                self.msg_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self.poll_queue)

    def step3_continue(self):
        self.completed_steps.add(2)
        self.go_to_step(3)

    def append_log(self, msg):
        tag = None
        if "[COPY]" in msg:
            tag = "copy"
        elif "[EXIF]" in msg:
            tag = "exif"
        elif "[VIDEO]" in msg:
            tag = "video"
        elif "[FOLDER-DATE]" in msg:
            tag = "folder_date"
        elif "[NO DATE]" in msg:
            tag = "no_date"
        elif "[ERROR]" in msg:
            tag = "error"
        elif "[SKIP]" in msg:
            tag = "skip"
        elif msg.isupper() or msg.startswith("="):
            tag = "heading"

        self.log_text.configure(state="normal")
        if tag:
            self.log_text.insert("end", msg + "\n", tag)
        else:
            self.log_text.insert("end", msg + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    # ==================================================================
    # STEP 4 - Summary
    # ==================================================================
    def _build_step4(self, parent):
        page = ttk.Frame(parent, padding=(24, 20, 24, 18))

        header = ttk.Frame(page)
        header.pack(anchor="w", fill="x")
        self.step4_icon = tk.Canvas(header, width=36, height=36, bg=COLOR_BG, highlightthickness=0)
        self.step4_icon.pack(side="left")
        title_box = ttk.Frame(header)
        title_box.pack(side="left", padx=(12, 0))
        ttk.Label(title_box, text="Sorting Complete", style="Heading.TLabel").pack(anchor="w")
        self.sum_verify_var = tk.StringVar()
        self.sum_verify_label = tk.Label(title_box, textvariable=self.sum_verify_var, bg=COLOR_BG,
                                          font=(FONT_FAMILY, 10, "bold"))
        self.sum_verify_label.pack(anchor="w", pady=(2, 0))

        cards = ttk.Frame(page)
        cards.pack(fill="x", pady=(20, 8))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="cards")

        self.sum_scanned_var = tk.StringVar(value="0")
        self.sum_exif_var = tk.StringVar(value="0")
        self.sum_folder_var = tk.StringVar(value="0")
        self.sum_nodate_var = tk.StringVar(value="0")
        self.sum_errors_var = tk.StringVar(value="0")
        self.sum_skipped_var = tk.StringVar(value="0")

        stat_defs = [
            ("Files Scanned", self.sum_scanned_var),
            ("Dated via EXIF/Video", self.sum_exif_var),
            ("Dated via Folder Name", self.sum_folder_var),
            ("Needs Review (No Date)", self.sum_nodate_var),
            ("Errors", self.sum_errors_var),
            ("Non-Media Skipped", self.sum_skipped_var),
        ]
        for i, (label_text, var) in enumerate(stat_defs):
            card = RoundedFrame(cards, bg_color=COLOR_CARD_BG, height=64)
            card.grid(row=i // 3, column=i % 3, sticky="nsew", padx=6, pady=6)
            ttk.Label(card.inner, textvariable=var, style="CardNumber.TLabel").pack(
                anchor="w", padx=12, pady=(10, 0))
            ttk.Label(card.inner, text=label_text, style="CardMuted.TLabel").pack(
                anchor="w", padx=12, pady=(0, 10))

        self.sum_logpath_var = tk.StringVar()
        ttk.Label(page, textvariable=self.sum_logpath_var, style="Status.TLabel").pack(anchor="w", pady=(10, 0))

        nav = ttk.Frame(page)
        nav.pack(side="bottom", fill="x", pady=(16, 0))
        RoundedButton(nav, text="Open Destination Folder", style="secondary",
                      command=self.open_destination_folder).pack(side="left")
        RoundedButton(nav, text="Open Log File", style="secondary",
                      command=self.open_log_file).pack(side="left", padx=(10, 0))
        RoundedButton(nav, text="Start New Sort", style="primary",
                      command=self.start_new_sort).pack(side="right")

        return page

    def populate_summary(self):
        s = self.last_stats or {}
        self.sum_scanned_var.set(str(s.get("scanned", 0)))
        self.sum_exif_var.set(str(s.get("exif", 0)))
        self.sum_folder_var.set(str(s.get("folder", 0)))
        self.sum_nodate_var.set(str(s.get("no_date", 0)))
        self.sum_errors_var.set(str(s.get("errors", 0)))
        self.sum_skipped_var.set(str(s.get("skipped", 0)))

        total_out = s.get("exif", 0) + s.get("folder", 0) + s.get("no_date", 0)
        ok = total_out == s.get("scanned", 0) - s.get("errors", 0)

        self.step4_icon.delete("all")
        if ok:
            self.step4_icon.create_oval(1, 1, 34, 34, fill=COLOR_GREEN, outline="")
            self.step4_icon.create_text(17, 17, text="✓", fill="white", font=(FONT_FAMILY, 15, "bold"))
            self.sum_verify_var.set("Verification OK - all files accounted for.")
            self.sum_verify_label.configure(fg=COLOR_GREEN)
        else:
            self.step4_icon.create_oval(1, 1, 34, 34, fill=COLOR_ORANGE, outline="")
            self.step4_icon.create_text(17, 17, text="!", fill="white", font=(FONT_FAMILY, 15, "bold"))
            self.sum_verify_var.set("Warning: file counts do not match - check the log.")
            self.sum_verify_label.configure(fg=COLOR_ORANGE)

        self.sum_logpath_var.set(f"Log file: {self.last_log_path}")

    def open_destination_folder(self):
        path = os.path.join(self.dst_folder.get(), self.parent_name.get().strip())
        if os.path.isdir(path):
            subprocess.run(["open", path])

    def open_log_file(self):
        if self.last_log_path and os.path.exists(self.last_log_path):
            subprocess.run(["open", self.last_log_path])

    def start_new_sort(self):
        self.parent_name.set("")
        self.src_folder.set("")
        self.dst_folder.set("")
        self.use_folder_date.set(True)
        self.scan_result = None
        self.last_stats = None
        self.last_log_path = None
        self.completed_steps = set()

        self.step1_status_var.set("No folder selected yet.")
        self.step1_detail_var.set("")
        self.step1_choose_btn.configure(state="normal")
        self.step1_continue_btn.configure(state="disabled")

        self.reset_step3_ui()
        self.go_to_step(0)

    # ------------------------------------------------------------------
    # Queue polling - the ONLY place background-thread results are
    # allowed to touch widgets, and it runs on the main thread.
    # ------------------------------------------------------------------
    def poll_queue(self):
        try:
            while True:
                item = self.msg_queue.get_nowait()
                kind = item[0]

                if kind == "log":
                    self.append_log(item[1])

                elif kind == "progress":
                    done, total = item[1], item[2]
                    self.progress.configure(maximum=max(total, 1), value=done)
                    pct = int(done / total * 100) if total else 100
                    self.step3_progress_var.set(f"{done} / {total} files processed ({pct}%)")

                elif kind == "scan_done":
                    result = item[1]
                    self.step1_progress.stop()
                    self.step1_progress.pack_forget()
                    self.step1_choose_btn.configure(state="normal")
                    self.scan_result = result
                    if result["total"] == 0:
                        self.step1_status_var.set("No media files found in this folder. Choose a different folder.")
                        self.step1_detail_var.set("")
                    else:
                        self.step1_status_var.set(
                            f"Found {result['total']} media file(s) across {result['folders']} folder(s).")
                        top = sorted(result["by_ext"].items(), key=lambda kv: -kv[1])[:6]
                        self.step1_detail_var.set(
                            "File types: " + ", ".join(f"{ext} ({n})" for ext, n in top))
                        self.step1_continue_btn.configure(state="normal")
                    self.busy = False

                elif kind == "scan_error":
                    self.step1_progress.stop()
                    self.step1_progress.pack_forget()
                    self.step1_choose_btn.configure(state="normal")
                    self.step1_status_var.set(f"Error scanning folder: {item[1]}")
                    self.busy = False

                elif kind == "done":
                    self.last_stats, self.last_log_path = item[1], item[2]
                    self.step3_progress_var.set("Sorting complete.")
                    self.step3_continue_btn.configure(state="normal")
                    self.step3_back_btn.configure(state="normal")
                    self.busy = False

                elif kind == "error":
                    messagebox.showerror("Sorting Error", item[1])
                    self.step3_back_btn.configure(state="normal")
                    self.busy = False

        except queue.Empty:
            pass

        if self.busy:
            self.root.after(100, self.poll_queue)


if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoSorterApp(root)
    root.mainloop()