#!/usr/bin/env python3
"""
Generate assets/hero.svg — the particle-morph identity panel.

Reads greyscale PGM bitmaps (produced by ffmpeg, see build.sh), samples them into
a fixed-size particle cloud, and emits a single self-contained SVG whose circles
morph between shapes with SMIL. No third-party dependencies.

Shapes, in loop order:
    portrait  ->  DAG pipeline glyph  ->  BK monogram  ->  star schema  ->  portrait
"""

import math
import sys
import random
from bisect import bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"

# ---------------------------------------------------------------- config

N = 1400              # particle count; keep the emitted SVG well under ~600 KB
                      # so the profile page can actually drive the SMIL timeline
SEED = 70329          # reg-number seed, so rebuilds are reproducible
CANVAS = (78, 122, 372, 416)   # x, y, w, h of the particle box inside the SVG
DUR = 26              # seconds per full loop

BG_CUT = 150          # flood-fill only spreads through pixels at least this light
BASE_FILL = 0.30      # every subject pixel gets this, so the silhouette stays solid
TONE_GAIN = 1.00      # extra density in the dark areas — hair, blazer, shadow
EDGE_GAIN = 2.10      # extra density on outlines — jaw, eyes, lapel


# ---------------------------------------------------------------- bitmap io

def read_pgm(path):
    """Minimal binary (P5) PGM reader."""
    data = path.read_bytes()
    fields, pos = [], 2
    while len(fields) < 3:
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b"#":
            pos = data.index(b"\n", pos) + 1
            continue
        start = pos
        while not data[pos:pos + 1].isspace():
            pos += 1
        fields.append(int(data[start:pos]))
    pos += 1
    w, h, _maxv = fields
    return w, h, data[pos:pos + w * h]


def background_mask(pix, w, h):
    """
    Flood-fill the backdrop inward from the border. A plain luminance threshold
    can't separate this photo's skin highlights from its light-grey backdrop —
    they overlap — but the backdrop is one connected region touching the frame,
    so filling it is unambiguous. The bottom row is excluded as a seed: the
    subject's light t-shirt runs off that edge and would otherwise be eaten.
    """
    bg = bytearray(w * h)
    stack = []
    for x in range(w):
        if pix[x] >= BG_CUT:
            stack.append(x)
    for y in range(h):
        for x in (0, w - 1):
            if pix[y * w + x] >= BG_CUT:
                stack.append(y * w + x)

    while stack:
        i = stack.pop()
        if bg[i]:
            continue
        bg[i] = 1
        x, y = i % w, i // w
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h:
                j = ny * w + nx
                if not bg[j] and pix[j] >= BG_CUT:
                    stack.append(j)
    return bg


def weight_map(pix, w, h):
    """Solid subject fill, plus extra density in dark areas and on outlines."""
    bg = background_mask(pix, w, h)
    weights = [0.0] * (w * h)
    for y in range(1, h - 1):
        row = y * w
        for x in range(1, w - 1):
            i = row + x
            if bg[i]:
                continue

            tone = max(0.0, (200 - pix[i]) / 200.0)

            gx = (pix[i - w + 1] + 2 * pix[i + 1] + pix[i + w + 1]
                  - pix[i - w - 1] - 2 * pix[i - 1] - pix[i + w - 1])
            gy = (pix[i + w - 1] + 2 * pix[i + w] + pix[i + w + 1]
                  - pix[i - w - 1] - 2 * pix[i - w] - pix[i - w + 1])
            edge = min(1.0, math.hypot(gx, gy) / 340.0)

            weights[i] = BASE_FILL + tone * TONE_GAIN + edge * EDGE_GAIN
    return weights


def sample(weights, w, h, n, rng, pix=None):
    """
    Weighted rejection-free sampling via a cumulative table + sub-pixel jitter.
    Each point carries the source tone (0 light .. 1 dark) so the particle can be
    shaded later — density alone doesn't render a face, brightness does.
    """
    cum, total = [], 0.0
    for wt in weights:
        total += wt
        cum.append(total)
    pts = []
    for _ in range(n):
        i = bisect_right(cum, rng.random() * total)
        i = min(i, len(cum) - 1)
        tone = 1.0 if pix is None else max(0.0, min(1.0, (215 - pix[i]) / 185.0))
        pts.append(((i % w) + rng.random(), (i // w) + rng.random(), tone))
    return pts, w, h


# ---------------------------------------------------------------- vector shapes

def _line(pts, a, b, count, rng, jitter=0.9):
    for k in range(count):
        t = k / max(1, count - 1)
        pts.append((a[0] + (b[0] - a[0]) * t + rng.uniform(-jitter, jitter),
                    a[1] + (b[1] - a[1]) * t + rng.uniform(-jitter, jitter), 1.0))


def _ring(pts, cx, cy, r, count, rng, jitter=0.8):
    for k in range(count):
        a = 2 * math.pi * k / count
        pts.append((cx + r * math.cos(a) + rng.uniform(-jitter, jitter),
                    cy + r * math.sin(a) + rng.uniform(-jitter, jitter), 1.0))


def _box(pts, cx, cy, w, h, count, rng):
    per = max(1, count // 4)
    _line(pts, (cx - w, cy - h), (cx + w, cy - h), per, rng)
    _line(pts, (cx + w, cy - h), (cx + w, cy + h), per, rng)
    _line(pts, (cx + w, cy + h), (cx - w, cy + h), per, rng)
    _line(pts, (cx - w, cy + h), (cx - w, cy - h), per, rng)


def shape_dag(n, rng):
    """Extract -> Transform -> Test -> Load, with a branch. His actual pipeline."""
    pts = []
    nodes = [(14, 50), (38, 50), (62, 30), (62, 70), (86, 50)]
    edges = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]
    for a, b in edges:
        _line(pts, nodes[a], nodes[b], 46, rng, 0.5)
    for cx, cy in nodes:
        _ring(pts, cx, cy, 7.0, 54, rng, 0.5)
        _ring(pts, cx, cy, 3.4, 26, rng, 0.5)
    while len(pts) < n:
        cx, cy = nodes[rng.randrange(len(nodes))]
        a, r = rng.uniform(0, 6.283), 7.0 * math.sqrt(rng.random())
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a), 1.0))
    return pts[:n], 100, 100


def shape_monogram(n, rng):
    w, h, pix = read_pgm(TOOLS / "mono.pgm")
    weights = [1.0 if v > 110 else 0.0 for v in pix]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            i = y * w + x
            if weights[i] and (pix[i - 1] < 110 or pix[i + 1] < 110
                               or pix[i - w] < 110 or pix[i + w] < 110):
                weights[i] = 6.0          # bias toward the letterform outline
    return sample(weights, w, h, n, rng)


def shape_star_schema(n, rng):
    """One fact table, four dimensions — the model behind his ETL work."""
    pts = []
    _box(pts, 50, 50, 11, 8, 150, rng)
    dims = [(50, 16), (50, 84), (16, 50), (84, 50)]
    for dx, dy in dims:
        _box(pts, dx, dy, 9, 6.5, 110, rng)
        vx, vy = dx - 50, dy - 50
        d = math.hypot(vx, vy)
        _line(pts, (50 + vx / d * 14, 50 + vy / d * 11),
              (dx - vx / d * 11, dy - vy / d * 8), 34, rng, 0.4)
    while len(pts) < n:
        pts.append((50 + rng.uniform(-10, 10), 50 + rng.uniform(-7, 7), 1.0))
    return pts[:n], 100, 100


# ---------------------------------------------------------------- morph plumbing

def fit(points, src_w, src_h, box):
    """Scale a point set into the canvas box, preserving aspect ratio."""
    bx, by, bw, bh = box
    scale = min(bw / src_w, bh / src_h) * 0.94
    ox = bx + (bw - src_w * scale) / 2
    oy = by + (bh - src_h * scale) / 2
    return [(ox + x * scale, oy + y * scale, tone) for x, y, tone in points]


def order(points):
    """
    Sort by angle about the centroid (radius as tiebreak) so that particle i in
    one shape lands near particle i in the next. Turns the morph into a sweep
    rather than random teleporting.
    """
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return sorted(points, key=lambda p: (math.atan2(p[1] - cy, p[0] - cx),
                                          math.hypot(p[0] - cx, p[1] - cy)))


# ---------------------------------------------------------------- svg assembly

BG, EDGE = "#05070f", "#16203a"
CYAN, VIOLET, MINT, AMBER = "#38bdf8", "#a78bfa", "#34d399", "#fbbf24"
TEXT, MUTED = "#dbe4f0", "#5b6b86"

# (label, value, colour). None inserts a gap; ("#", title, None) is a section rule.
DOSSIER = [
    ("#", "IDENTITY", None),
    ("Subject", "Brian Renald Kimario", TEXT),
    ("Alias", "@Brian-Kimario", CYAN),
    ("Origin", "Tanzania", MINT),
    ("Education", "CSE · Data Science · Chandigarh Univ.", TEXT),
    ("Role", "Analytics · Engineering · Science", VIOLET),
    ("Focus", "Competent across all three, not one lane", AMBER),
    None,
    ("#", "TOOLCHAIN", None),
    ("Core.Lang", "Python · SQL · TypeScript · Java", TEXT),
    ("Core.Data", "Pandas · NumPy · Jupyter · Tableau", TEXT),
    ("Core.Flow", "Airflow 3 · Prefect · Astro Runtime", TEXT),
    ("Core.Store", "PostgreSQL · DuckDB · Supabase", TEXT),
    ("Core.Build", "FastAPI · Next.js 15 · Docker · Vercel", TEXT),
    None,
    ("#", "SIGNAL", None),
    ("Certified", "IBM Java Fund. · Coursera Py4DS", MINT),
    ("Learning", "Machine learning — projects to follow", TEXT),
    ("Open.To", "Analytics · engineering · science roles", AMBER),
    None,
    ("#", "CONTACT", None),
    ("Grid.Mail", "kimario.brian.89@gmail.com", CYAN),
    ("Grid.GitHub", "github.com/Brian-Kimario", CYAN),
]

MONO = "ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,monospace"


REVEAL_SPAN = 2.8


def reveal(delay):
    """
    Staggered fade-in that degrades safely.

    A CSS `opacity:0 -> 1` entrance leaves the element permanently invisible in
    any renderer that ignores the stylesheet, and this dossier is the most
    important text on the profile. So the element's own opacity stays 1 and the
    hiding is done *inside* one SMIL timeline instead — anything that can't run
    SMIL simply shows the finished panel.
    """
    d = min(delay / REVEAL_SPAN, 0.96)
    return (f'<animate attributeName="opacity" dur="{REVEAL_SPAN}s"'
            f' fill="freeze" keyTimes="0;{d:.3f};{min(d + 0.1, 1):.3f};1"'
            f' values="0;0;1;1"/>')


def build_svg(particles):
    px, py, pw, ph = CANVAS
    rows, y = [], 128
    for idx, row in enumerate(DOSSIER):
        delay = 0.3 + idx * 0.075
        if row is None:
            y += 10
            continue
        label, value, colour = row
        if label == "#":
            rows.append(
                f'<g>'
                f'<text x="500" y="{y}" font-family="{MONO}" font-size="10.5"'
                f' letter-spacing="2.6" fill="{VIOLET}">{value}</text>'
                f'<path d="M{500 + 7.2 * len(value) + 14} {y - 4}H968"'
                f' stroke="{EDGE}" stroke-width="1"/></g>'
            )
            y += 24
        else:
            leader = f"{label} ".ljust(13, ".")
            rows.append(
                f'<text x="500" y="{y}" font-family="{MONO}" font-size="12.5">'
                f'<tspan fill="{MUTED}">{leader}</tspan>'
                f'<tspan fill="{colour}"> {esc(value)}</tspan></text>'
            )
            y += 19

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" role="img" aria-label="Brian Kimario — identity panel">
<defs>
  <radialGradient id="bloom" cx="50%" cy="45%" r="55%">
    <stop offset="0%" stop-color="{CYAN}" stop-opacity=".16"/>
    <stop offset="60%" stop-color="{VIOLET}" stop-opacity=".07"/>
    <stop offset="100%" stop-color="{VIOLET}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="rim" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{CYAN}"/>
    <stop offset="50%" stop-color="{VIOLET}"/>
    <stop offset="100%" stop-color="{MINT}"/>
  </linearGradient>
  <clipPath id="canvasClip">
    <rect x="{px - 8}" y="{py - 8}" width="{pw + 16}" height="{ph + 16}" rx="10"/>
  </clipPath>
</defs>

<rect width="1000" height="600" rx="14" fill="{BG}"/>
<rect x=".5" y=".5" width="999" height="599" rx="14" fill="none" stroke="{EDGE}"/>

<!-- window chrome -->
<path d="M0 14a14 14 0 0 1 14-14h972a14 14 0 0 1 14 14v32H0z" fill="#0a0f1d"/>
<line x1="0" y1="46" x2="1000" y2="46" stroke="{EDGE}"/>
<circle cx="26" cy="23" r="5.5" fill="#ff5f57"/>
<circle cx="46" cy="23" r="5.5" fill="#febc2e"/>
<circle cx="66" cy="23" r="5.5" fill="#28c840"/>
<text x="92" y="27" font-family="{MONO}" font-size="12" fill="{MUTED}">
  Brian-Kimario / <tspan fill="{TEXT}">IDENTITY.svg</tspan>
</text>
<circle cx="906" cy="23" r="3.5" fill="{MINT}">
  <animate attributeName="opacity" values=".35;1;.35" dur="2.4s"
           repeatCount="indefinite"/>
</circle>
<text x="918" y="27" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MINT}">LIVE</text>

<!-- particle canvas -->
<text x="56" y="86" font-family="{MONO}" font-size="10.5" letter-spacing="2.6" fill="{CYAN}">VISUAL.MAP</text>
<rect x="{px - 8}" y="{py - 8}" width="{pw + 16}" height="{ph + 16}" rx="10"
      fill="none" stroke="url(#rim)" stroke-width="1.4" opacity=".55"/>
<ellipse cx="{px + pw / 2}" cy="{py + ph / 2}" rx="{pw * .62}" ry="{ph * .55}" fill="url(#bloom)"/>
<g clip-path="url(#canvasClip)">
  <rect x="{px - 8}" y="{py - 88}" width="{pw + 16}" height="80"
        fill="{CYAN}" opacity=".05">
    <animateTransform attributeName="transform" type="translate" dur="6s"
                      repeatCount="indefinite" values="0 0;0 {ph + 104}"/>
  </rect>
</g>
{particles}

<!-- dossier -->
<text x="500" y="86" font-family="{MONO}" font-size="10.5" letter-spacing="2.6" fill="{CYAN}">SYSTEM.INFO</text>
{chr(10).join(rows)}
</svg>
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main():
    rng = random.Random(SEED)

    pw, ph, ppix = read_pgm(TOOLS / "portrait.pgm")
    portrait = fit(*sample(weight_map(ppix, pw, ph), pw, ph, N, rng, ppix), CANVAS)
    dag = fit(*shape_dag(N, rng), CANVAS)
    mono = fit(*shape_monogram(N, rng), CANVAS)
    star = fit(*shape_star_schema(N, rng), CANVAS)

    portrait_o = order(portrait)
    frames = [portrait_o, order(dag), order(mono), order(star), portrait_o]

    #        hold    ->     morph    hold      morph    hold     morph    hold   ->
    key_times = "0;.26;.34;.5;.58;.72;.8;.93;1"
    frame_at = [0, 0, 1, 1, 2, 2, 3, 3, 4]
    splines = ";".join([".65 0 .35 1"] * (len(frame_at) - 1))

    # One animateTransform per particle rather than separate cx/cy animations —
    # halves the emitted file, since keyTimes/keySplines are written once each.
    parts = []
    for i in range(N):
        seq = ";".join(f"{frames[f][i][0]:.0f} {frames[f][i][1]:.0f}"
                       for f in frame_at)

        # hue by height in the portrait: cyan at the crown, violet at the base.
        # brightness/size by source tone, so the face is lit rather than flat.
        t = (portrait_o[i][1] - CANVAS[1]) / CANVAS[3]
        hue = 188 + 70 * max(0.0, min(1.0, t))
        tone = portrait_o[i][2]
        r = round(0.85 + 1.05 * tone, 2)
        op = round(0.30 + 0.70 * tone, 2)

        parts.append(
            f'<circle r="{r}" fill="hsl({hue:.0f},92%,70%)" opacity="{op:.2f}">'
            f'<animateTransform attributeName="transform" type="translate"'
            f' dur="{DUR}s" repeatCount="indefinite" calcMode="spline"'
            f' keyTimes="{key_times}" keySplines="{splines}" values="{seq}"/>'
            f"</circle>"
        )

    # `gen_hero.py 2` freezes shape 2 into a still, for eyeballing a single pose.
    if len(sys.argv) > 1:
        k = int(sys.argv[1])
        still = "\n".join(
            f'<circle cx="{frames[k][i][0]:.0f}" cy="{frames[k][i][1]:.0f}"'
            f' r="{0.85 + 1.05 * frames[k][i][2]:.2f}" opacity="{0.30 + 0.70 * frames[k][i][2]:.2f}" fill="hsl({188 + 70 * max(0.0, min(1.0, (portrait_o[i][1] - CANVAS[1]) / CANVAS[3])):.0f},92%,70%)"/>'
            for i in range(N))
        out = ROOT / "tools" / f"freeze{k}.svg"
        out.write_text(build_svg(still))
        print(f"froze shape {k} -> {out}")
        return

    svg = build_svg("\n".join(parts))
    out = ROOT / "assets" / "hero.svg"
    out.write_text(svg)
    print(f"{N} particles -> {out.relative_to(ROOT)} ({len(svg) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
