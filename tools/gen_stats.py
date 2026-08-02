#!/usr/bin/env python3
"""
Generate assets/stats.svg from the live GitHub GraphQL API.

Run by .github/workflows/refresh.yml on a schedule. Uses only the standard
library so the workflow needs no pip install step.

    GITHUB_TOKEN=... python3 tools/gen_stats.py

Private repositories are included when the token can see them, which is the
point: most of the real work on this profile lives in private repos.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from theme import (AMBER, CYAN, EDGE, MINT, MONO, MUTED, TEXT, VIOLET, esc,
                   reveal, panel_open, panel_close, section_label)

ROOT = Path(__file__).resolve().parent.parent
LOGIN = os.environ.get("GH_LOGIN", "Brian-Kimario")
W = 1000

QUERY = """
query($login:String!) {
  user(login:$login) {
    followers { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false) {
      totalCount
      nodes {
        stargazerCount
        languages(first:12, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalRepositoryContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY,
                         "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": f"{LOGIN}-profile-build"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def streaks(weeks):
    """Current and longest daily contribution streak, ignoring a blank today."""
    days = [d for w in weeks for d in w["contributionDays"]
            if d["date"] <= date.today().isoformat()]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)

    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif current or d["date"] != date.today().isoformat():
            # today not yet contributed to doesn't break the streak
            break
    return current, longest


def top_languages(repos, limit=6):
    totals, colours = {}, {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] = totals.get(name, 0) + edge["size"]
            colours[name] = edge["node"]["color"] or "#8b949e"
    grand = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:limit]
    return [(n, s / grand, colours[n]) for n, s in ranked]


def build(user):
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]
    repos = user["repositories"]["nodes"]
    current, longest = streaks(cal["weeks"])
    stars = sum(r["stargazerCount"] for r in repos)
    langs = top_languages(repos)

    h = 268
    out = [panel_open(W, h, "SIGNAL.LIVE",
                      f"synced {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")]

    # ---- headline number
    out.append(f'<text x="34" y="118" font-family="{MONO}" font-size="62"'
               f' font-weight="700" fill="url(#grad)">'
               f'{cal["totalContributions"]}</text>')
    out.append(f'<text x="36" y="140" font-family="{MONO}" font-size="10.5"'
               f' letter-spacing="1.8" fill="{MUTED}">'
               f'CONTRIBUTIONS · LAST 12 MONTHS</text>')
    out.append(f'<text x="36" y="182" font-family="{MONO}" font-size="13"'
               f' fill="{AMBER}">{current}-day streak</text>')
    out.append(f'<text x="36" y="204" font-family="{MONO}" font-size="11"'
               f' fill="{MUTED}">longest: {longest} days</text>')
    out.append(f'<line x1="300" y1="58" x2="300" y2="{h - 26}" stroke="{EDGE}"/>')

    # ---- metric column
    # Deliberately not "stars" or "followers": for someone two years in, those
    # measure audience, not output, and a wall of zeros undersells the work.
    metrics = [
        ("Commits", cc["totalCommitContributions"], CYAN),
        ("Pull requests", cc["totalPullRequestContributions"], VIOLET),
        ("Repositories", user["repositories"]["totalCount"], MINT),
        ("Repos touched", cc["totalRepositoryContributions"], AMBER),
        ("Languages used", len(top_languages(repos, limit=99)), TEXT),
    ]
    out.append(section_label(332, 76, "COUNTERS"))
    for i, (label, value, colour) in enumerate(metrics):
        y = 108 + i * 27
        out.append(f'<g>{reveal(0.1 + i * .08)}')
        out.append(f'<text x="332" y="{y}" font-family="{MONO}" font-size="12"'
                   f' fill="{MUTED}">{esc(label)}</text>')
        out.append(f'<text x="600" y="{y}" text-anchor="end" font-family="{MONO}"'
                   f' font-size="14" font-weight="600" fill="{colour}">'
                   f'{value}</text>')
        out.append("</g>")
    out.append(f'<line x1="640" y1="58" x2="640" y2="{h - 26}" stroke="{EDGE}"/>')

    # ---- language mix
    out.append(section_label(672, 76, "LANGUAGE MIX · ALL REPOS"))
    bx, bw = 672, W - 672 - 34
    out.append(f'<rect x="{bx}" y="94" width="{bw}" height="7" rx="3.5"'
               f' fill="#0d1424"/>')
    off = 0.0
    for _, share, colour in langs:
        seg = bw * share
        out.append(f'<rect x="{bx + off:.1f}" y="94" width="{max(seg - 2, 1):.1f}"'
                   f' height="7" rx="3.5" fill="{colour}"/>')
        off += seg
    # One column, not two: names like "Jupyter Notebook" collide in two.
    for i, (name, share, colour) in enumerate(langs):
        cy = 126 + i * 23
        out.append(f'<g>{reveal(0.2 + i * .07)}')
        out.append(f'<circle cx="{bx + 4}" cy="{cy - 4}" r="4" fill="{colour}"/>')
        out.append(f'<text x="{bx + 16}" y="{cy}" font-family="{MONO}"'
                   f' font-size="11.5" fill="{TEXT}">{esc(name)}</text>')
        out.append(f'<text x="{bx + bw}" y="{cy}" text-anchor="end"'
                   f' font-family="{MONO}" font-size="11" fill="{MUTED}">'
                   f'{share * 100:.1f}%</text>')
        out.append("</g>")

    out.append(panel_close())
    return "\n".join(out)


def main():
    svg = build(fetch())
    out = ROOT / "assets" / "stats.svg"
    out.write_text(svg)
    print(f"{out.relative_to(ROOT)}  {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
