"""Draw a donut chart of the languages used across all of my repositories.

The script reads byte counts per language from the GitHub API and writes
languages-light.svg and languages-dark.svg. Only rounded percentages reach the image. Repository names,
byte counts and the number of repositories are never written or printed.

Standard library only. The token is read from LANG_TOKEN and needs nothing
beyond read-only Metadata access. Forks and archived repositories are
skipped, so archiving a repository on GitHub removes it from the chart.
"""

import json
import math
import os
import sys
import urllib.request
from html import escape

API = "https://api.github.com"
THEMES = {
    "light": ("#1f2328", "#59636e"),
    "dark": ("#e6edf3", "#9198a1"),
}
# Markup and notebooks, which Linguist does not class as programming languages
EXCLUDE = {"TeX", "Jupyter Notebook", "HTML", "CSS", "SCSS", "MDX", "Markdown"}
TOP = 6  # slices shown before the rest are grouped as Other

# Official colours from github-linguist/linguist languages.yml
COLOURS = {
    "Astro": "#ff5a03",
    "C": "#555555",
    "C++": "#f34b7d",
    "CSS": "#663399",
    "Dockerfile": "#384d54",
    "Fortran": "#4d41b1",
    "Go": "#00ADD8",
    "Haskell": "#5e5086",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "Julia": "#a270ba",
    "Jupyter Notebook": "#DA5B0B",
    "Kotlin": "#A97BFF",
    "Lua": "#000080",
    "MATLAB": "#e16737",
    "MDX": "#fcb32c",
    "Makefile": "#427819",
    "Python": "#3572A5",
    "R": "#198CE7",
    "Rust": "#dea584",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "Svelte": "#ff3e00",
    "Swift": "#F05138",
    "TeX": "#3D6117",
    "TypeScript": "#3178c6",
    "Vue": "#41b883",
}
OTHER = "#8b949e"


def get(url, token):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-languages",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response), response.headers.get("Link") or ""


def repositories(token):
    url = f"{API}/user/repos?affiliation=owner&visibility=all&per_page=100"
    while url:
        page, link = get(url, token)
        yield from page
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip(" <>")


def totals(token):
    counts = {}
    for repo in repositories(token):
        if repo["fork"] or repo["archived"]:
            continue
        languages, _ = get(repo["languages_url"], token)
        for name, size in languages.items():
            if name not in EXCLUDE:
                counts[name] = counts.get(name, 0) + size
    return counts


def shares(counts):
    total = sum(counts.values())
    ranked = sorted(counts.items(), key=lambda item: -item[1])
    rows = [(name, size / total * 100) for name, size in ranked[:TOP]]
    rest = sum(size for _, size in ranked[TOP:])
    if rest:
        rows.append(("Other", rest / total * 100))
    return rows


def svg(rows, theme):
    text, muted = THEMES[theme]
    width, top, step = 460, 66, 24
    height = top + step * len(rows) + 14
    cx, cy, r, ring = 92, top + step * (len(rows) - 1) / 2, 54, 20
    gap = 0.6 if len(rows) > 1 else 0

    slices, offset = [], 0.0
    for name, pct in rows:
        colour = COLOURS.get(name, OTHER)
        length = max(pct - gap, 0.05)
        slices.append(
            f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}" pathLength="100" '
            f'stroke="{colour}" stroke-width="{ring}" fill="none" '
            f'stroke-dasharray="{length:.2f} {100 - length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" '
            f'transform="rotate(-90 {cx} {cy:.1f})"/>'
        )
        offset += pct

    legend = []
    for i, (name, pct) in enumerate(rows):
        y = top + i * step
        colour = COLOURS.get(name, OTHER)
        legend.append(
            f'<circle cx="196" cy="{y - 4}" r="5" fill="{colour}"/>'
            f'<text x="210" y="{y}" class="t">{escape(name)}</text>'
            f'<text x="{width - 20}" y="{y}" class="m" text-anchor="end">{pct:.1f}%</text>'
        )

    label = ", ".join(f"{name} {pct:.1f}%" for name, pct in rows)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Languages: {escape(label)}">'
        f"<title>Languages: {escape(label)}</title>"
        "<style>"
        'text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif;font-size:13px}'
        f".t{{fill:{text}}}.m{{fill:{muted}}}.h{{font-size:15px;font-weight:600}}.s{{font-size:11px}}"
        "</style>"
        '<text x="20" y="28" class="t h">Languages</text>'
        '<text x="20" y="44" class="m s">Programming languages across all my repositories</text>'
        + "".join(slices)
        + "".join(legend)
        + "</svg>\n"
    )


def main():
    token = os.environ.get("LANG_TOKEN")
    if not token:
        sys.exit("LANG_TOKEN is not set")
    counts = totals(token)
    if not counts:
        sys.exit("No language data returned, keeping the old chart")
    rows = shares(counts)
    for theme in THEMES:
        with open(f"languages-{theme}.svg", "w", encoding="utf-8") as handle:
            handle.write(svg(rows, theme))


if __name__ == "__main__":
    main()
