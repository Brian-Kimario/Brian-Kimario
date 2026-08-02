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

# name, status, [description lines], [(language, share, colour)], [tags]
PROJECTS = [
    ("Matokeo", "ACTIVE", [
        "Civic data platform for Tanzania's NECTA exam results.",
        "Scraper → Postgres warehouse → analytics API → dashboards.",
    ], [("TypeScript", .52, "#3178c6"), ("Python", .40, "#3572A5"),
        ("PLpgSQL", .08, "#336790")],
     ["FastAPI", "Next.js 15", "Supabase", "Recharts"]),

    ("ETLWeather", "PUBLIC", [
        "Airflow 3 pipeline on Astro Runtime: Open-Meteo → transform",
        "→ data-quality gate → Postgres. Idempotent upserts, DAG tests.",
    ], [("Python", .98, "#3572A5"), ("Docker", .02, "#384d54")],
     ["Airflow 3", "TaskFlow", "Astro CLI", "OrbStack"]),

    ("Kaggle ETL Pipeline", "PRIVATE", [
        "E-commerce sales, raw CSV → star schema → DuckDB warehouse",
        "→ flat export for Tableau. Orchestrated with Prefect.",
    ], [("Jupyter", .83, "#DA5B0B"), ("Python", .17, "#3572A5")],
     ["Prefect", "DuckDB", "Star schema", "Tableau"]),

    ("Admissions System", "PRIVATE", [
        "University admissions workflow — application intake, review",
        "and decisioning over a Postgres core.",
    ], [("TypeScript", .86, "#3178c6"), ("Python", .08, "#3572A5"),
        ("PLpgSQL", .06, "#336790")],
     ["Next.js", "Postgres", "RBAC"]),

    ("Dynamic Post Composer", "PUBLIC", [
        "Multi-platform post composer with per-platform constraint",
        "validation, JWT auth, role-based access and a drag calendar.",
    ], [("JavaScript", .99, "#f1e05a"), ("CSS", .01, "#563d7c")],
     ["React", "Redux Toolkit", "JWT"]),

    ("Lakehouse Lab", "WIP", [
        "Working through lakehouse storage layers and query engines",
        "— the layer under everything else on this list.",
    ], [("Python", 1.0, "#3572A5")],
     ["Parquet", "DuckDB", "Layered storage"]),
]

STATUS_COLOUR = {"ACTIVE": MINT, "PUBLIC": CYAN, "PRIVATE": MUTED, "WIP": AMBER}

# group, [(tool, proficiency 0..1)]
STACK = [
    ("ORCHESTRATION", [("Apache Airflow 3", .85), ("Prefect", .70),
                       ("Astro Runtime", .70), ("Cron / GH Actions", .80)]),
    ("DATA & STORAGE", [("PostgreSQL", .85), ("DuckDB", .75), ("Supabase", .80),
                        ("SQLite", .85), ("Pandas", .80)]),
    ("LANGUAGES", [("Python", .90), ("TypeScript", .80), ("SQL", .85),
                   ("Java", .65)]),
    ("APPLICATION", [("FastAPI", .85), ("Next.js 15", .80), ("Tailwind", .80),
                     ("Redux Toolkit", .70)]),
    ("PLATFORM", [("Docker", .75), ("Git / GitHub", .90), ("Vercel", .80),
                  ("OrbStack", .70)]),
]

W = 1000


# ---------------------------------------------------------------- projects

def projects_svg():
    cw, ch, gx, gy = 484, 140, 16, 14
    top = 62
    rows = (len(PROJECTS) + 1) // 2
    h = top + rows * ch + (rows - 1) * gy + 18

    out = [panel_open(W, h, "PROJECTS.LIST",
                      "6 selected · 2 public · 4 private")]

    for i, (name, status, desc, langs, tags) in enumerate(PROJECTS):
        x = 16 + (i % 2) * (cw + gx)
        y = top + (i // 2) * (ch + gy)
        delay = 0.15 + i * 0.11

        out.append(f'<g>{reveal(delay)}')
        out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10"'
                   f' fill="{PANEL}" stroke="{EDGE}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="3" height="{ch}" rx="1.5"'
                   f' fill="{STATUS_COLOUR[status]}" opacity=".8"/>')

        out.append(f'<text x="{x + 20}" y="{y + 28}" font-family="{MONO}"'
                   f' font-size="14.5" fill="{TEXT}" font-weight="600">'
                   f'{esc(name)}</text>')
        sc = STATUS_COLOUR[status]
        out.append(f'<rect x="{x + cw - 20 - len(status) * 7.2 - 14}"'
                   f' y="{y + 15}" width="{len(status) * 7.2 + 14}" height="19"'
                   f' rx="9.5" fill="{sc}" opacity=".13"/>')
        out.append(f'<text x="{x + cw - 27}" y="{y + 28.5}" text-anchor="end"'
                   f' font-family="{MONO}" font-size="9.5" letter-spacing="1.1"'
                   f' fill="{sc}">{status}</text>')

        for j, line in enumerate(desc):
            out.append(f'<text x="{x + 20}" y="{y + 50 + j * 15}"'
                       f' font-family="{MONO}" font-size="11.5" fill="{MUTED}">'
                       f'{esc(line)}</text>')

        # stacked language bar
        bx, bw = x + 20, cw - 40
        out.append(f'<rect x="{bx}" y="{y + 88}" width="{bw}" height="4"'
                   f' rx="2" fill="#0d1424"/>')
        off = 0.0
        for _, share, colour in langs:
            seg = bw * share
            out.append(f'<rect x="{bx + off:.1f}" y="{y + 88}"'
                       f' width="{max(seg - 1.5, 1):.1f}" height="4" rx="2"'
                       f' fill="{colour}"/>')
            off += seg
        lang_txt = "  ".join(f"{n} {s * 100:.0f}%" for n, s, _ in langs)
        out.append(f'<text x="{bx}" y="{y + 107}" font-family="{MONO}"'
                   f' font-size="10.5" fill="{MUTED}">{esc(lang_txt)}</text>')

        tx = bx
        for tag in tags:
            tw = len(tag) * 6.6 + 16
            if tx + tw > x + cw - 20:
                break
            out.append(f'<rect x="{tx}" y="{y + 114}" width="{tw:.0f}"'
                       f' height="17" rx="4" fill="{VIOLET}" opacity=".10"/>')
            out.append(f'<text x="{tx + tw / 2:.0f}" y="{y + 126}"'
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
