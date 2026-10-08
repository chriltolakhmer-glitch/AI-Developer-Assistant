"""Local appearance controller: presentation only, no developer operations."""

from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import font, ttk
from tkinter.scrolledtext import ScrolledText

from .preferences import MODES


LIGHT = dict(main="#FFFFFF", sidebar="#F3F4F6", result="#F5F6F8", composer="#ECEEF2",
             text="#20242B", muted="#535C69", border="#D7DCE3", focus="#2457C5",
             selected="#E2E9F7", hover="#ECEEF2", addition_bg="#EAF5EE",
             addition="#176B3A", deletion_bg="#FCECEE", deletion="#A52432",
             warning="#805500", error="#A52432")
DARK = dict(main="#181818", sidebar="#141414", result="#2C2C2C", composer="#363636",
            text="#F1F3F5", muted="#B8C0CC", border="#434B58", focus="#9AB7FF",
            selected="#262626", hover="#363636", addition_bg="#20372A",
            addition="#8ED8AB", deletion_bg="#3C262D", deletion="#FFADB7",
            warning="#F1CE7C", error="#FFADB7")


class ThemedScrolledText(ScrolledText):
    """Retain Text behavior and layout, using a controllable ttk scrollbar."""
    def __init__(self, parent, **options):
        super().__init__(parent, **options)
        self.vbar.destroy()
        self.vbar = ttk.Scrollbar(self.frame, command=self.yview)
        self.vbar.pack(side="right", fill="y")
        self.configure(yscrollcommand=self.vbar.set)


@dataclass(frozen=True)
class SystemAppearance:
    mode: str | None = None
    high_contrast: bool = False
    colors: tuple[tuple[str, str], ...] = ()


def detect_windows_appearance():
    """Read app preference and accessibility colors; never change OS settings."""
    if sys.platform != "win32":
        return SystemAppearance()
    import ctypes
    from ctypes import wintypes
    import winreg

    mode = None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, kind = winreg.QueryValueEx(key, "AppsUseLightTheme")
        if kind == winreg.REG_DWORD and value in (0, 1):
            mode = "Light" if value else "Dark"
    except OSError:
        pass

    class HighContrast(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwFlags", wintypes.DWORD),
                    ("lpszDefaultScheme", wintypes.LPWSTR)]

    try:
        api = ctypes.windll.user32
        record = HighContrast()
        record.cbSize = ctypes.sizeof(record)
        if api.SystemParametersInfoW(0x0042, record.cbSize, ctypes.byref(record), 0) and record.dwFlags & 1:
            def color(index):
                value = api.GetSysColor(index)
                return f"#{value & 255:02X}{(value >> 8) & 255:02X}{(value >> 16) & 255:02X}"
            return SystemAppearance(mode, True, tuple({
                "main": color(5), "text": color(8), "result": color(15),
                "selected": color(13), "selection_text": color(14), "focus": color(13),
            }.items()))
    except (OSError, AttributeError):
        pass
    return SystemAppearance(mode)


def palette(mode, system=None):
    colors = dict(DARK if mode == "Dark" else LIGHT)
    colors["selection_text"] = colors["text"]
    if system and system.high_contrast:
        colors.update(dict(system.colors))
        for token in ("sidebar", "result", "composer", "hover", "addition_bg", "deletion_bg"):
            colors[token] = colors["main"]
        for token in ("muted", "addition", "deletion", "warning", "error", "border"):
            colors[token] = colors["text"]
    return colors


def contrast(foreground, background):
    def luminance(value):
        channels = [int(value[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
        return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + .05) / (low + .05)


class ThemeController:
    def __init__(self, root, *, mode="System", detector=detect_windows_appearance, on_change=None):
        if mode not in MODES:
            raise ValueError("Unknown appearance mode.")
        self.root, self.mode, self.detector = root, mode, detector
        self.on_change = on_change
        self.colors = None
        self.closed = False
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.fonts = {name: font.nametofont(name, root=root) for name in ("TkDefaultFont", "TkFixedFont")}
        self.map_binding = root.bind("<Map>", self._mapped, add="+")
        self.focus_binding = root.bind("<FocusIn>", self._activated, add="+")
        self.refresh()
        self.timer = root.after(2000, self._poll)

    def set_mode(self, mode):
        if mode not in MODES:
            raise ValueError("Unknown appearance mode.")
        self.mode = mode
        self.refresh()
        self.apply_widgets(self.root)

    def refresh(self):
        try:
            system = self.detector()
        except (OSError, ValueError):
            system = SystemAppearance()
        self.resolved = system.mode if self.mode == "System" and system.mode in MODES[:2] else (
            "Light" if self.mode == "System" else self.mode)
        self.message = ("Windows high contrast overrides appearance." if system.high_contrast else
                        "System appearance unavailable; using Light." if self.mode == "System" and system.mode is None else
                        f"{self.mode} appearance; resolved {self.resolved}.")
        colors = palette(self.resolved, system)
        if colors != self.colors:
            self.colors = colors
            self._styles()
            self.apply_widgets(self.root)
        if self.on_change:
            self.on_change(self.message)

    def _styles(self):
        c, s = self.colors, self.style
        s.configure(".", background=c["main"], foreground=c["text"], font="TkDefaultFont",
                    bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                    focuscolor=c["focus"], focusthickness=2)
        for name in ("TFrame", "TLabel", "TLabelframe", "TLabelframe.Label", "TNotebook"):
            s.configure(name, background=c["main"], foreground=c["text"])
        for name in ("TButton", "TCheckbutton", "TRadiobutton", "TMenubutton", "TNotebook.Tab", "Treeview.Heading"):
            s.configure(name, background=c["result"], foreground=c["text"], focuscolor=c["focus"],
                        borderwidth=1, focusthickness=2)
            s.map(name, background=[("disabled", c["result"]), ("selected", c["selected"]),
                                    ("active", c["hover"])],
                  foreground=[("disabled", c["muted"]), ("selected", c["selection_text"])],
                  bordercolor=[("focus", c["focus"]), ("!focus", c["border"])])
        for name in ("TEntry", "TCombobox"):
            s.configure(name, fieldbackground=c["main"], foreground=c["text"], insertcolor=c["text"],
                        selectbackground=c["selected"], selectforeground=c["selection_text"],
                        arrowcolor=c["text"], borderwidth=2)
            s.map(name, fieldbackground=[("disabled", c["result"]), ("readonly", c["main"])],
                  foreground=[("disabled", c["muted"]), ("readonly", c["text"])],
                  bordercolor=[("focus", c["focus"]), ("!focus", c["border"])])
        s.configure("Treeview", background=c["main"], fieldbackground=c["main"], foreground=c["text"])
        s.map("Treeview", background=[("selected", c["selected"])],
              foreground=[("selected", c["selection_text"])], bordercolor=[("focus", c["focus"])])
        for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            s.configure(name, background=c["result"], troughcolor=c["main"], arrowcolor=c["text"],
                        bordercolor=c["border"])
            s.map(name, background=[("active", c["hover"]), ("disabled", c["result"])])
        for name in ("TPanedwindow", "Sash"):
            s.configure(name, background=c["main"])
        for name, token in (("Warning.TLabel", "warning"), ("Error.TLabel", "error")):
            s.configure(name, foreground=c[token], background=c["main"])
        # Option defaults cover Tcl-created combobox popdowns as well as later widgets.
        for option, value in (("background", c["main"]), ("foreground", c["text"]),
                              ("selectBackground", c["selected"]), ("selectForeground", c["selection_text"])):
            self.root.option_add(f"*TCombobox*Listbox.{option}", value)
        # Toplevel descendants use their own bindtags, not the root's Map binding.
        # Supply their initial colors before construction; later switches scan them.
        for family in ("Toplevel", "Frame", "Text", "Listbox", "Canvas"):
            for option, value in (("background", c["main"]), ("highlightColor", c["focus"]),
                                  ("highlightBackground", c["border"])):
                self.root.option_add(f"*{family}.{option}", value)
        for family in ("Text", "Listbox"):
            for option, value in (("foreground", c["text"]), ("selectBackground", c["selected"]),
                                  ("selectForeground", c["selection_text"])):
                self.root.option_add(f"*{family}.{option}", value)
        self.root.option_add("*Text.insertBackground", c["text"])
        self.root.option_add("*Text.font", "TkFixedFont")
        self.root.option_add("*Listbox.disabledForeground", c["muted"])
        for option, value in (("background", c["result"]), ("activeBackground", c["hover"]),
                              ("troughColor", c["main"]), ("highlightBackground", c["border"])):
            self.root.option_add(f"*Scrollbar.{option}", value)

    def apply_widgets(self, widget):
        c = self.colors
        if isinstance(widget, ttk.Widget):
            pass  # ttk Entry/Combobox also inherit Tk classes; styles own their colors.
        elif isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame)):
            widget.configure(background=c["main"])
        elif isinstance(widget, (tk.Text, tk.Listbox, tk.Entry)):
            options = dict(background=c["main"], foreground=c["text"],
                           selectbackground=c["selected"], selectforeground=c["selection_text"],
                           highlightcolor=c["focus"], highlightbackground=c["border"], highlightthickness=2)
            if isinstance(widget, (tk.Text, tk.Entry)):
                options["insertbackground"] = c["text"]
            if isinstance(widget, tk.Text):
                options["font"] = "TkFixedFont"
            if isinstance(widget, (tk.Listbox, tk.Entry)):
                options["disabledforeground"] = c["muted"]
            widget.configure(**options)
            if isinstance(widget, tk.Text):
                for tag, foreground, background in (("addition", "addition", "addition_bg"),
                                                     ("deletion", "deletion", "deletion_bg"),
                                                     ("heading", "focus", "main"), ("hunk", "muted", "main")):
                    if tag in widget.tag_names():
                        widget.tag_configure(tag, foreground=c[foreground], background=c[background])
        elif isinstance(widget, tk.Canvas):
            widget.configure(background=c["main"], highlightcolor=c["focus"],
                             highlightbackground=c["border"], highlightthickness=2 if widget.cget("takefocus") else 0)
        elif isinstance(widget, tk.Scrollbar):
            widget.configure(background=c["result"], troughcolor=c["main"], activebackground=c["hover"],
                             highlightbackground=c["border"])
        elif isinstance(widget, tk.Menu):
            widget.configure(background=c["main"], foreground=c["text"],
                             activebackground=c["selected"], activeforeground=c["selection_text"],
                             disabledforeground=c["muted"])
        if isinstance(widget, ttk.Combobox):
            popdown = widget.tk.call("ttk::combobox::PopdownWindow", widget)
            widget.tk.call(f"{popdown}.f.l", "configure", "-background", c["main"],
                           "-foreground", c["text"], "-selectbackground", c["selected"],
                           "-selectforeground", c["selection_text"], "-highlightcolor", c["focus"])
        for child in widget.winfo_children():
            self.apply_widgets(child)

    def _mapped(self, event):
        if not self.closed and isinstance(event.widget, tk.Misc):
            self.apply_widgets(event.widget)

    def _activated(self, event):
        if event.widget == self.root:
            self.refresh()

    def _poll(self):
        if not self.closed:
            self.refresh()
            self.timer = self.root.after(2000, self._poll)

    def close(self):
        self.closed = True
        self.root.after_cancel(self.timer)
        self.root.unbind("<Map>", self.map_binding)
        self.root.unbind("<FocusIn>", self.focus_binding)
