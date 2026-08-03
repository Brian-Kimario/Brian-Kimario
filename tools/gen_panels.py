#!/usr/bin/env python3
"""
Generate the static README panels: assets/projects.svg and assets/stack.svg.

Content lives in the two tables below — edit those, re-run, commit. Everything
shares the palette and type scale defined in theme.py so the profile reads as
one designed surface rather than a pile of third-party badges.
"""

from pathlib import Path

from theme import (AMBER, BG, CYAN, EDGE, MINT, MONO, MUTED, PANEL, TEXT,
                   VIOLET, esc, reveal, panel_open, panel_close, section_label)

ROOT = Path(__file__).resolve().parent.parent

# Public, non-coursework repositories only — three real projects rather than a
# padded grid. repo, label, [description lines], flow line,
# [(language, share, colour)], [tags]
PROJECTS = [
    ("etl_weather", "ETLWeather", [
        "Airflow 3 pipeline on Astronomer's Astro Runtime, built with the",
        "TaskFlow API. Goes past the tutorial it started from: idempotent",
        "upserts, exponential-backoff retries, dynamic task mapping and",
        "DAG-integrity tests.",
    ], "Open-Meteo  →  extract  →  transform  →  quality gate  →  Postgres",
     [("Python", .98, "#3572A5"), ("Dockerfile", .02, "#384d54")],
     ["Airflow 3", "TaskFlow", "Astro CLI", "Docker", "OrbStack"]),

    ("kaggle_etl_pipeline", "Local ETL Pipeline", [
        "Kaggle e-commerce sales (2023–2025) reshaped into a star schema —",
        "four dimensions and a fact table — loaded to a DuckDB warehouse and",
        "exported flat for Tableau. A quality gate halts the run before bad",
        "data reaches the warehouse.",
    ], "Kaggle  →  star schema  →  test  →  DuckDB  →  Tableau export",
     [("Jupyter Notebook", .83, "#DA5B0B"), ("Python", .17, "#3572A5")],
     ["Prefect", "DuckDB", "Star schema", "pytest"]),

    ("dynamic-post-composer", "Dynamic Post Composer", [
        "Compose one draft, validate it against the character limits of",
        "Facebook, X, LinkedIn and Instagram at once. Normalised Redux",
        "Toolkit store, JWT auth with stateless sessions, role-based access,",
        "and a drag-to-reorder content calendar.",
    ], "compose  →  validate per platform  →  save draft  →  schedule",
     [("JavaScript", .99, "#f1e05a"), ("CSS", .01, "#563d7c")],
     ["React", "Redux Toolkit", "JWT", "RBAC"]),

    ("leetcode_cc", "LeetCode Log", [
        "Solutions committed straight out of LeetCode by LeetHub v2, each",
        "one filed under the topics it exercises — arrays, binary search,",
        "hash tables, sliding window. Keeps the algorithm side sharp while",
        "the rest of the work is pipelines and analysis.",
    ], "solve  →  auto-commit  →  write-up  →  topic index",
     [("Python", 1.0, "#3572A5")],
     ["Algorithms", "LeetHub v2", "Interview prep"]),
]

# No repo-count note: the list is curated, and a stale number reads worse than
# no number at all.
ACCENTS = [CYAN, MINT, VIOLET, AMBER]

# group, [(tool, proficiency 0..1)]
STACK = [
    ("LANGUAGES", [("Python", .90), ("SQL", .85), ("TypeScript", .80),
                   ("Java", .65)]),
    ("ANALYSIS", [("Pandas", .80), ("NumPy", .70), ("Jupyter", .85),
                  ("Tableau", .65)]),
    ("ORCHESTRATION", [("Apache Airflow 3", .85), ("Prefect", .70),
                       ("Astro Runtime", .70), ("GitHub Actions", .80)]),
    ("DATA & STORAGE", [("PostgreSQL", .85), ("DuckDB", .75), ("Supabase", .80),
                        ("SQLite", .85)]),
    ("APP & PLATFORM", [("FastAPI", .85), ("Next.js 15", .80), ("Docker", .75),
                        ("Vercel", .80)]),
]

W = 1000


# ---------------------------------------------------------------- projects

def projects_svg():
    """Full-width cards: three projects with room to say what they do."""
    cw, ch, gy, top = 968, 158, 14, 62
    split = 620                       # where the text column hands over to meta
    h = top + len(PROJECTS) * ch + (len(PROJECTS) - 1) * gy + 18

    out = [panel_open(W, h, "PROJECTS.LIST",
                      f"{len(PROJECTS)} selected · all public")]

    for i, (repo, title, desc, flow, langs, tags) in enumerate(PROJECTS):
        x, y = 16, top + i * (ch + gy)
        accent = ACCENTS[i % len(ACCENTS)]

        out.append(f'<g>{reveal(0.15 + i * 0.14)}')
        out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10"'
                   f' fill="{PANEL}" stroke="{EDGE}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="3" height="{ch}" rx="1.5"'
                   f' fill="{accent}" opacity=".85"/>')

        out.append(f'<text x="{x + 24}" y="{y + 32}" font-family="{MONO}"'
                   f' font-size="16" fill="{TEXT}" font-weight="600">'
                   f'{esc(title)}</text>')
        out.append(f'<text x="{x + 24 + len(title) * 9.9 + 14}" y="{y + 32}"'
                   f' font-family="{MONO}" font-size="11.5" fill="{MUTED}">'
                   f'{esc(repo)}</text>')

        for j, line in enumerate(desc):
            out.append(f'<text x="{x + 24}" y="{y + 58 + j * 17}"'
                       f' font-family="{MONO}" font-size="11.5" fill="{MUTED}">'
                       f'{esc(line)}</text>')

        # the shape of the pipeline, which is the point of these projects
        out.append(f'<rect x="{x + 24}" y="{y + ch - 38}" width="{split - 48}"'
                   f' height="26" rx="6" fill="{accent}" opacity=".07"/>')
        out.append(f'<text x="{x + 38}" y="{y + ch - 20}" font-family="{MONO}"'
                   f' font-size="10.5" fill="{accent}">{esc(flow)}</text>')

        out.append(f'<line x1="{x + split}" y1="{y + 18}" x2="{x + split}"'
                   f' y2="{y + ch - 18}" stroke="{EDGE}"/>')

        # meta column: language split, then tags
        bx, bw = x + split + 26, cw - split - 50
        out.append(f'<rect x="{bx}" y="{y + 26}" width="{bw}" height="5"'
                   f' rx="2.5" fill="#0d1424"/>')
        off = 0.0
        for _, share, colour in langs:
            seg = bw * share
            out.append(f'<rect x="{bx + off:.1f}" y="{y + 26}"'
                       f' width="{max(seg - 2, 1):.1f}" height="5" rx="2.5"'
                       f' fill="{colour}"/>')
            off += seg
        for j, (name, share, colour) in enumerate(langs):
            ly = y + 52 + j * 19
            out.append(f'<circle cx="{bx + 4}" cy="{ly - 4}" r="3.6"'
                       f' fill="{colour}"/>')
            out.append(f'<text x="{bx + 15}" y="{ly}" font-family="{MONO}"'
                       f' font-size="11" fill="{TEXT}">{esc(name)}</text>')
            out.append(f'<text x="{bx + bw}" y="{ly}" text-anchor="end"'
                       f' font-family="{MONO}" font-size="10.5" fill="{MUTED}">'
                       f'{share * 100:.0f}%</text>')

        tx, ty = bx, y + 52 + len(langs) * 19 + 12
        for tag in tags:
            tw = len(tag) * 6.6 + 16
            if tx + tw > bx + bw:                 # wrap instead of clipping
                tx, ty = bx, ty + 23
            if ty > y + ch - 12:
                break
            out.append(f'<rect x="{tx:.0f}" y="{ty}" width="{tw:.0f}"'
                       f' height="18" rx="4" fill="{VIOLET}" opacity=".10"/>')
            out.append(f'<text x="{tx + tw / 2:.0f}" y="{ty + 13}"'
                       f' text-anchor="middle" font-family="{MONO}"'
                       f' font-size="10.5" fill="{VIOLET}">{esc(tag)}</text>')
            tx += tw + 7
        out.append("</g>")

    out.append(panel_close())
    return "\n".join(out)


# ---------------------------------------------------------------- stack

def stack_svg():
    col_w, top = 190, 66
    h = top + 5 * 22 + 44
    out = [panel_open(W, h, "TOOLCHAIN", "weighted by what I actually reach for")]

    for c, (group, tools) in enumerate(STACK):
        x = 18 + c * (col_w + 6)
        out.append(section_label(x, 46, group))
        for r, (tool, level) in enumerate(tools):
            y = top + r * 22
            delay = 0.1 + (c * 4 + r) * 0.05
            out.append(f'<g>{reveal(delay)}')
            out.append(f'<text x="{x}" y="{y}" font-family="{MONO}"'
                       f' font-size="11.5" fill="{TEXT}">{esc(tool)}</text>')
            out.append(f'<rect x="{x}" y="{y + 5}" width="{col_w - 30}"'
                       f' height="3" rx="1.5" fill="#0d1424"/>')
            out.append(f'<rect x="{x}" y="{y + 5}"'
                       f' width="{(col_w - 30) * level:.0f}" height="3" rx="1.5"'
                       f' fill="url(#grad)"/>')
            out.append("</g>")

    out.append(panel_close())
    return "\n".join(out)


def main():
    for name, svg in (("projects", projects_svg()), ("stack", stack_svg())):
        p = ROOT / "assets" / f"{name}.svg"
        p.write_text(svg)
        print(f"{p.relative_to(ROOT)}  {len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
