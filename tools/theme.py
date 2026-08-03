"""Shared palette, type scale and panel chrome for every generated asset."""

BG = "#05070f"
PANEL = "#080d1a"
EDGE = "#16203a"
CYAN = "#38bdf8"
VIOLET = "#a78bfa"
MINT = "#34d399"
AMBER = "#fbbf24"
TEXT = "#dbe4f0"
MUTED = "#5b6b86"

MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace"


def panel_open(w, h, label, note=""):
    """Opening tags for a titled panel: frame, shared defs, entrance animation."""
    note_el = (f'<text x="{w - 18}" y="27" text-anchor="end" font-family="{MONO}"'
               f' font-size="10.5" fill="{MUTED}">{note}</text>' if note else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">
<defs>
  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{CYAN}"/>
    <stop offset="100%" stop-color="{VIOLET}"/>
  </linearGradient>
</defs>
<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{EDGE}"/>
<text x="18" y="27" font-family="{MONO}" font-size="10.5" letter-spacing="2.6" fill="{CYAN}">{label}</text>
{note_el}
<line x1="18" y1="38" x2="{w - 18}" y2="38" stroke="{EDGE}"/>"""


def panel_close():
    return "</svg>"


def reveal(_delay):
    """
    Entrance animations are disabled, deliberately, and this returns nothing.

    It used to emit a staggered SMIL fade from opacity:0. That is load-bearing
    animation: if the timeline never advances — which is exactly what happened
    to hero.svg on the profile page — every element it decorates stays at
    opacity 0 and the panel renders blank, with no clue as to why. A profile
    has to be legible on first paint, so nothing here may depend on motion.
    Kept as a no-op so call sites read unchanged; the only animation left in
    this project is the particle morph, which is decorative by construction.
    """
    return ""


def esc(s):
    """XML-escape text destined for an SVG text node."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def section_label(x, y, text):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="9.5"'
            f' letter-spacing="1.8" fill="{VIOLET}">{esc(text)}</text>')
