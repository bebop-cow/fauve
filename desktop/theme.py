"""Fauve theme for Flet. Day 6am-6pm (paperboy), night otherwise (detective).

Every colour, font, size, spacing and radius the app uses lives here as a token,
taken from the "Fauve Approval Flow" design. main.py uses only these names (T20 I).
"""
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import flet as ft

ASSETS = Path(__file__).parent / "assets"

# Fonts: only local files in assets/fonts/. Missing ones fall back to system fonts.
# Never a URL: the app must work with Wi-Fi off and send nothing out (T20 H).
_FONT_FILES = {
    "Josefin Sans": "fonts/JosefinSans.ttf",
    "Courier Prime": "fonts/CourierPrime-Regular.ttf",
    "Courier Prime Bold": "fonts/CourierPrime-Bold.ttf",
    "Libre Franklin": "fonts/LibreFranklin.ttf",
}
FONTS = {name: local for name, local in _FONT_FILES.items() if (ASSETS / local).exists()}

DISPLAY = "Josefin Sans"      # 300 weight, headings
LABEL = "Courier Prime"       # labels, buttons, status
LABEL_BOLD = "Courier Prime Bold"
BODY = "Libre Franklin"       # body copy


def a(alpha: float, hex_color: str) -> str:
    return ft.Colors.with_opacity(alpha, hex_color)


# ---------- raw colours (the design's swatches) ----------
CREAM = "#f3e9d2"
INK = "#231b1b"
RED = "#cc2a18"            # "something can leave this Mac" (switches, cloud answers)
STUDIO_RED = "#b8291a"     # the Red Studio field while a card waits for you
STUDIO_DEEP = "#9a2013"
STUDIO_GOLD = "#e0b45a"
STUDIO_MUTED = "#f3d9b8"


@dataclass(frozen=True)
class Palette:
    mode: str
    bg: str
    panel: str
    bubble: str        # assistant bubble
    ink: str
    muted: str
    accent: str
    accent_text: str   # accent used as text on bg (passes contrast)
    line: str
    user_bg: str
    user_ink: str
    art: str           # idle painting
    painting: str      # working painting
    icon: str
    celebrate: str = "panels/bella-ciao.webp"   # after a cloud answer comes back
    red: str = RED
    on_accent: str = INK       # text on the gold accent
    on_red: str = CREAM        # text on red
    glow: str | None = None    # night: gold glow behind kickers
    field_line: str = ""       # composer border ("" = ink)


DAY = Palette(
    mode="day", bg=CREAM, panel="#fbf5e6", bubble="#fffaf0",
    ink=INK, muted="#6b5a4e", accent="#c99a1e", accent_text="#7d5a0c",
    line=a(0.18, INK), user_bg=INK, user_ink=CREAM,
    art="panels/picnic.webp", painting="panels/morning-edition.webp", icon="icon-day.png",
)

NIGHT = Palette(
    mode="night", bg="#0b1228", panel="#141d3d", bubble="#101833",
    ink=CREAM, muted="#aeb4cc", accent="#ddb13c", accent_text="#ddb13c",
    line=a(0.16, CREAM), user_bg=CREAM, user_ink="#0b1228",
    art="panels/rainy-window.webp", painting="panels/night-desk.webp", icon="icon-night.png",
    glow=a(0.55, "#ddb13c"), red="#f07a66",   # lighter red: #cc2a18 is only ~3:1 on navy
)


@dataclass(frozen=True)
class Ask:
    """The approval card on the Red Studio field: a cream card, red kicker and SEND ONCE."""
    bg: str = CREAM
    ink: str = INK
    muted: str = "#6b5a4e"
    kicker: str = STUDIO_RED
    line: str = STUDIO_GOLD
    well: str = "#fbf5e6"          # the "exactly this will be sent" box
    well_line: str = a(0.25, INK)
    send_bg: str = STUDIO_RED
    send_ink: str = CREAM
    chip_bg: str = CREAM           # header chip "WAITING ON YOU"
    chip_ink: str = STUDIO_RED


ASK = Ask()


def studio(p: Palette) -> Palette:
    """The Red Studio: while an approval card is open the chat column, the painting
    and the status card turn red together. The sidebar keeps p."""
    return replace(p, bg=STUDIO_RED, panel=STUDIO_DEEP, bubble=STUDIO_DEEP, ink=CREAM,
                   muted=STUDIO_MUTED, accent=STUDIO_GOLD, accent_text=STUDIO_MUTED,  # gold text is 3.2:1 on red
                   line=a(0.45, STUDIO_GOLD), user_bg=CREAM, user_ink=INK,
                   painting="panels/red-studio.webp", red=CREAM, glow=None, field_line=STUDIO_GOLD)


# Kept for older callers: the Red Studio as a dict.
RED_STUDIO = dict(bg=STUDIO_RED, panel=STUDIO_DEEP, ink=CREAM, muted=STUDIO_MUTED,
                  accent=STUDIO_GOLD, line=a(0.45, STUDIO_GOLD), painting="red-studio.webp")


# ---------- sizes, spacing, radii, motion ----------
@dataclass(frozen=True)
class Space:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 28


@dataclass(frozen=True)
class Radius:
    sm: int = 6        # buttons, wells
    md: int = 8        # sidebar buttons
    card: int = 10     # status card, notices
    field: int = 12    # composer, approval card
    bubble: int = 16
    tail: int = 4      # the bubble corner next to the speaker
    pill: int = 20


@dataclass(frozen=True)
class Size:
    window_w: int = 1280
    window_h: int = 800
    sidebar: int = 240
    painting: int = 380
    header: int = 60
    logo: int = 34
    avatar: int = 32
    user_bubble: int = 420
    reply: int = 560
    well: int = 180          # height of the "exactly this will be sent" box
    border: float = 1.5
    border_strong: int = 2


@dataclass(frozen=True)
class Type:
    logo: int = 22
    headline: int = 28
    body: int = 15
    title: int = 16
    small: int = 14
    mono: float = 12.5
    label: int = 12
    tiny: int = 11
    kicker_spacing: float = 2


SPACE, RADIUS, SIZE, TYPE = Space(), Radius(), Size(), Type()
FADE_MS = 600      # the design's cross-fade; not used yet: render() rebuilds every control


def palette_for(now: datetime | None = None) -> Palette:
    h = (now or datetime.now()).hour
    return DAY if 6 <= h < 18 else NIGHT


def _ts(font, size, weight=None, color=None, spacing=None, height=None, glow=None):
    return ft.TextStyle(font_family=font, size=size, weight=weight, color=color,
                        letter_spacing=spacing, height=height,
                        shadow=ft.BoxShadow(blur_radius=14, color=glow) if glow else None)


def build_theme(p: Palette) -> ft.Theme:
    # Flet 1.0: no `brightness` on ColorScheme — the theme_mode set in
    # apply() (DARK/LIGHT) determines brightness instead.
    return ft.Theme(
        font_family=BODY,
        color_scheme=ft.ColorScheme(
            primary=p.accent, on_primary=p.on_accent,
            secondary=p.red, on_secondary=p.on_red,
            surface=p.bg, on_surface=p.ink,
            surface_container=p.panel, surface_container_high=p.bubble,
            on_surface_variant=p.muted, outline=p.line, outline_variant=p.line,
            error=p.red, on_error=p.on_red,
        ),
        text_theme=ft.TextTheme(
            display_large=_ts(DISPLAY, 48, ft.FontWeight.W_300, p.ink, 2),
            headline_medium=_ts(DISPLAY, 28, ft.FontWeight.W_300, p.ink, 1),
            title_medium=_ts(BODY, 16, ft.FontWeight.W_600, p.ink),
            body_large=_ts(BODY, 15, ft.FontWeight.W_400, p.ink, height=1.5),
            body_medium=_ts(BODY, 14, ft.FontWeight.W_400, p.ink, height=1.45),
            label_large=_ts(LABEL_BOLD, 13, None, p.ink, 1),
            label_small=_ts(LABEL, 11, None, p.muted, 2),
        ),
        divider_theme=ft.DividerTheme(color=p.line, thickness=1, space=1),
    )


# Reusable text styles (for widgets outside the Material text theme)
def kicker(p: Palette, size=TYPE.label, color=None):
    return _ts(LABEL_BOLD, size, color=color or p.accent_text, spacing=2.5, glow=p.glow)


def display(p: Palette, size=TYPE.headline, color=None):
    return _ts(DISPLAY, size, ft.FontWeight.W_300, color or p.ink, 1, height=1.05)


def body(p: Palette, size=TYPE.body, weight=ft.FontWeight.W_400, color=None):
    return _ts(BODY, size, weight, color or p.ink, height=1.5)


def mono(p: Palette, size=TYPE.mono, color=None):
    return _ts(LABEL, size, color=color or p.muted, height=1.6)


def label(size=TYPE.label, color=None, spacing=1):
    """Bold mono label: buttons, chips, notice heads."""
    return _ts(LABEL_BOLD, size, color=color, spacing=spacing)


def apply(page: ft.Page, p: Palette | None = None) -> Palette:
    p = p or palette_for()
    # Flet 1.0 removed some page-level font registration paths;
    # guard so the app still runs if `page.fonts` is gone.
    try:
        page.fonts = FONTS
    except Exception:
        pass
    page.theme = build_theme(p)
    page.theme_mode = ft.ThemeMode.DARK if p.mode == "night" else ft.ThemeMode.LIGHT
    try:
        page.dark_theme = page.theme
    except Exception:
        pass
    page.bgcolor = p.bg
    return p
