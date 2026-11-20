"""Draw my profile card: an isometric contribution calendar and a language pie.

Contributions come from the public contributions pages, which is the same view
anyone sees on my profile, so no token is used for them.

Languages come from the GitHub API with LANG_TOKEN, a fine-grained token with
read-only Metadata and Contents access. Notebooks are counted by the code in
their code cells, because a whole .ipynb file is mostly saved outputs and
images. Forks and archived repositories are skipped, so archiving a
repository on GitHub removes it from the chart.

Only rounded percentages and daily contribution counts reach the image.
Repository names, byte counts and the number of repositories are never
written or printed. Standard library only.

Icons are from Primer Octicons (MIT License, Copyright GitHub Inc.).
"""

import base64
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from html import escape, unescape

API = "https://api.github.com"
LOGIN = os.environ.get("GITHUB_REPOSITORY_OWNER", "jerrygk")
WEEKS = 26  # weeks shown in the calendar
WIDTH = 480

# Markup, which Linguist does not class as programming languages
EXCLUDE = {"TeX", "HTML", "CSS", "SCSS", "MDX", "Markdown"}
NOTEBOOK = "Jupyter Notebook"
TOP = 6  # slices shown before the rest are grouped as Other

THEMES = {
    "light": {
        "title": "#0969da",
        "text": "#59636e",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
    "dark": {
        "title": "#4493f8",
        "text": "#9198a1",
        "levels": ["#2d333b", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
}

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

# Primer Octicons, 16px
ICONS = {
    "calendar": "M4.75 0a.75.75 0 0 1 .75.75V2h5V.75a.75.75 0 0 1 1.5 0V2h1.25c.966 0 1.75.784 1.75 1.75v10.5A1.75 1.75 0 0 1 13.25 16H2.75A1.75 1.75 0 0 1 1 14.25V3.75C1 2.784 1.784 2 2.75 2H4V.75A.75.75 0 0 1 4.75 0ZM2.5 7.5v6.75c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25V7.5Zm10.75-4H2.75a.25.25 0 0 0-.25.25V6h11V3.75a.25.25 0 0 0-.25-.25Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "flame": "M9.533.753V.752c.217 2.385 1.463 3.626 2.653 4.81C13.37 6.74 14.498 7.863 14.498 10c0 3.5-3 6-6.5 6S1.5 13.512 1.5 10c0-1.298.536-2.56 1.425-3.286.376-.308.862 0 1.035.454C4.46 8.487 5.581 8.419 6 8c.282-.282.341-.811-.003-1.5C4.34 3.187 7.035.75 8.77.146c.39-.137.726.194.763.607ZM7.998 14.5c2.832 0 5-1.98 5-4.5 0-1.463-.68-2.19-1.879-3.383l-.036-.037c-1.013-1.008-2.3-2.29-2.834-4.434-.322.256-.63.579-.864.953-.432.696-.621 1.58-.046 2.73.473.947.67 2.284-.278 3.232-.61.61-1.545.84-2.403.633a2.79 2.79 0 0 1-1.436-.874A3.198 3.198 0 0 0 3 10c0 2.53 2.164 4.5 4.998 4.5Z",
    "trophy": "M3.217 6.962A3.75 3.75 0 0 1 0 3.25v-.5C0 1.784.784 1 1.75 1h1.356c.228-.585.796-1 1.462-1h6.864c.647 0 1.227.397 1.462 1h1.356c.966 0 1.75.784 1.75 1.75v.5a3.75 3.750 0 0 1-3.217 3.712 5.014 5.014 0 0 1-2.771 3.117l.144 1.446c.005.05.03.12.114.204.086.087.217.17.373.227.283.103.618.274.89.568.285.31.467.723.467 1.226v.75h1.25a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1 0-1.5H4v-.75c0-.503.182-.916.468-1.226.27-.294.606-.465.889-.568.139-.048.266-.126.373-.227.084-.085.109-.153.114-.204l.144-1.446a5.015 5.015 0 0 1-2.770-3.117ZM4.5 1.568V5.5a3.5 3.5 0 1 0 7 0V1.568a.068.068 0 0 0-.068-.068H4.568a.068.068 0 0 0-.068.068Zm2.957 8.902-.12 1.204c-.093.925-.858 1.470-1.467 1.691a.766.766 0 0 0-.3.176c-.037.04-.07.093-.07.21v.75h5v-.75c0-.117-.033-.17-.07-.21a.766.766 0 0 0-.3-.176c-.609-.221-1.374-.766-1.466-1.690l-.12-1.204a5.064 5.064 0 0 1-1.087 0ZM13 2.5v2.872a2.25 2.25 0 0 0 1.5-2.122v-.5a.25.25 0 0 0-.25-.25H13Zm-10 0H1.75a.25.25 0 0 0-.25.25v.5c0 .98.626 1.813 1.5 2.122Z",
    "pulse": "M6 2c.306 0 .582.187.696.471L10 10.731l1.304-3.26A.751.751 0 0 1 12 7h3.25a.75.75 0 0 1 0 1.5h-2.742l-1.812 4.528a.751.751 0 0 1-1.392 0L6 4.77 4.696 8.030A.75.75 0 0 1 4 8.5H.75a.75.75 0 0 1 0-1.5h2.742l1.812-4.529A.751.751 0 0 1 6 2Z",
    "arrow-up": "M3.47 7.78a.75.75 0 0 1 0-1.06l4.25-4.25a.75.75 0 0 1 1.06 0l4.25 4.25a.751.751 0 0 1-.018 1.042.751.751 0 0 1-1.042.018L9 4.81v7.44a.75.75 0 0 1-1.5 0V4.81L4.53 7.78a.75.75 0 0 1-1.060 0Z",
    "graph": "M1.5 1.75V13.5h13.75a.75.75 0 0 1 0 1.5H.75a.75.75 0 0 1-.75-.75V1.75a.75.75 0 0 1 1.5 0Zm14.28 2.53-5.25 5.25a.75.75 0 0 1-1.06 0L7 7.06 4.28 9.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.250-3.25a.75.75 0 0 1 1.06 0L10 7.94l4.72-4.72a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042Z",
    "code": "m11.28 3.22 4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.749.749 0 0 1-1.275-.326.749.749 0 0 1 .215-.734L13.94 8l-3.72-3.72a.749.749 0 0 1 .326-1.275.749.749 0 0 1 .734.215Zm-6.56 0a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042L2.06 8l3.72 3.72a.749.749 0 0 1-.326 1.275.749.749 0 0 1-.734-.215L.47 8.53a.75.75 0 0 1 0-1.06Z",
}


# ---------- data ----------

def fetch(url, token=None, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "profile-card"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get("Link") or ""


def get(url, token):
    body, link = fetch(url, token)
    return json.loads(body), link


def contributions(query=""):
    """Daily counts from the public contributions page, oldest first."""
    page = fetch(f"https://github.com/users/{LOGIN}/contributions{query}", accept="text/html")[0]
    page = page.decode("utf-8")
    cells = {}
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        day = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        ident = re.search(r'id="(contribution-day-component-(\d+)-(\d+))"', tag)
        level = re.search(r'data-level="(\d)"', tag)
        if day and ident and level:
            cells[ident.group(1)] = [date.fromisoformat(day.group(1)), int(ident.group(3)), 0, int(level.group(1))]
    for ident, label in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        number = re.match(r"\s*([\d,]+) contribution", unescape(label))
        if ident in cells and number:
            cells[ident][2] = int(number.group(1).replace(",", ""))
    # (date, week column, count, GitHub colour level 0-4)
    if not cells:
        raise RuntimeError("contributions page format changed")
    return sorted((tuple(cell) for cell in cells.values()), key=lambda cell: cell[0])


def repositories(token):
    url = f"{API}/user/repos?affiliation=owner&visibility=all&per_page=100"
    while url:
        page, link = get(url, token)
        yield from page
        url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip(" <>")


def notebook_code(repo, token):
    """Bytes of source in the code cells of every notebook in a repository."""
    tree, _ = get(f"{API}/repos/{repo['full_name']}/git/trees/{repo['default_branch']}?recursive=1", token)
    size = 0
    for item in tree.get("tree", []):
        if item["type"] != "blob" or not item["path"].endswith(".ipynb"):
            continue
        blob, _ = get(item["url"], token)
        try:
            notebook = json.loads(base64.b64decode(blob["content"]))
        except (ValueError, KeyError):
            continue
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") == "code":
                source = cell.get("source", "")
                if isinstance(source, list):
                    source = "".join(source)
                size += len(source.encode("utf-8"))
    return size


def languages(token):
    counts = {}
    for repo in repositories(token):
        if repo["fork"] or repo["archived"]:
            continue
        found, _ = get(repo["languages_url"], token)
        for name, size in found.items():
            if name == NOTEBOOK:
                size = notebook_code(repo, token)
            if name not in EXCLUDE and size:
                counts[name] = counts.get(name, 0) + size
    if not counts:
        raise RuntimeError("no language data returned")
    total = sum(counts.values())
    ranked = sorted(counts.items(), key=lambda item: -item[1])
    rows = [(name, size / total * 100) for name, size in ranked[:TOP]]
    rest = sum(size for _, size in ranked[TOP:])
    if rest:
        rows.append(("Other", rest / total * 100))
    return rows


def history(token):
    """Daily counts for every year since the account was created."""
    joined = int(get(f"{API}/users/{LOGIN}", token)[0]["created_at"][:4])
    counts = {}
    for year in range(joined, date.today().year + 1):
        for day, _, count, _ in contributions(f"?from={year}-01-01&to={year}-12-31"):
            if day <= date.today():
                counts[day] = count
    return sorted(counts.items())


def streaks(days, past):
    best = run = 0
    best_year = None
    for day, count in past:
        run = run + 1 if count else 0
        if run > best:
            best, best_year = run, day.year
    counts = [count for _, _, count, _ in days]
    current = 0
    tail = counts[:-1] if counts and not counts[-1] else counts  # today may still come
    for count in reversed(tail):
        if not count:
            break
        current += 1
    total = sum(counts)
    return {
        "total": total,
        "current": current,
        "best": best,
        "best_year": best_year,
        "highest": max(counts),
        "average": total / len(counts),
    }


# ---------- drawing ----------

def shade(colour, factor):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(c * factor) for c in (r, g, b))


def icon(name, x, y, colour):
    return f'<path transform="translate({x} {y})" fill="{colour}" d="{ICONS[name]}"/>'


def line(name, x, y, text, theme, heading=False):
    colour = theme["title"] if heading else theme["text"]
    css = "h" if heading else "b"
    return icon(name, x, y - 12, colour) + f'<text x="{x + 24}" y="{y}" class="{css}">{escape(text)}</text>'


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def calendar(days, theme, top):
    """Isometric calendar of the last WEEKS weeks, cubes drawn back to front."""
    last = max(week for _, week, _, _ in days)
    cells = [(d, w - (last - WEEKS + 1), c, l) for d, w, c, l in days if w > last - WEEKS]
    peak = max((c for _, _, c, _ in cells), default=0) or 1
    a, b, tall = 6.6, 3.81, 38  # half-width and half-height of one tile, tallest cube
    ai, bi = a * 0.86, b * 0.86  # tiles are inset so a thin gap separates them
    x0, y0 = 7 * a + 6, top + tall + 6
    pts = lambda *p: " ".join(f"{px:.1f},{py:.1f}" for px, py in p)
    shapes = []
    for day, week, count, level in sorted(cells, key=lambda c: (c[1] + (c[0].isoweekday() % 7), c[1])):
        row = day.isoweekday() % 7  # Sunday first, as on GitHub
        cx, cy = x0 + (week - row) * a, y0 + (week + row) * b + b  # tile centre
        h = 3 + (tall - 3) * count / peak if count else 0
        top_colour = theme["levels"][level]
        if h:
            shapes.append(f'<polygon fill="{shade(top_colour, 0.82)}" points="{pts((cx - ai, cy - h), (cx, cy + bi - h), (cx, cy + bi), (cx - ai, cy))}"/>')
            shapes.append(f'<polygon fill="{shade(top_colour, 0.66)}" points="{pts((cx, cy + bi - h), (cx + ai, cy - h), (cx + ai, cy), (cx, cy + bi))}"/>')
        shapes.append(f'<polygon fill="{top_colour}" points="{pts((cx, cy - bi - h), (cx + ai, cy - h), (cx, cy + bi - h), (cx - ai, cy - h))}"/>')
    height = tall + 6 + (WEEKS + 7) * b + 4
    return "".join(shapes), height


def donut(rows, top):
    cx, cy, r, ring = 92, top + 14 + 24 * (len(rows) - 1) / 2, 54, 20
    gap = 0.6 if len(rows) > 1 else 0
    out, offset = [], 0.0
    for name, pct in rows:
        length = max(pct - gap, 0.05)
        out.append(
            f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}" pathLength="100" '
            f'stroke="{COLOURS.get(name, OTHER)}" stroke-width="{ring}" fill="none" '
            f'stroke-dasharray="{length:.2f} {100 - length:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy:.1f})"/>'
        )
        offset += pct
    return "".join(out)


def card(days, stats, rows, theme):
    parts = [line("calendar", 8, 22, "Contributions calendar", theme, heading=True)]

    cubes, cal_height = calendar(days, theme, 34)
    parts.append(cubes)

    x = 250
    parts += [
        line("commit", x, 52, f"{plural(stats['total'], 'contribution')} last year", theme),
        line("flame", x, 86, "Contribution streaks", theme, heading=True),
        line("flame", x, 108, f"Current streak {plural(stats['current'], 'day')}", theme),
        line("trophy", x, 128, f"Best streak {plural(stats['best'], 'day')} ({stats['best_year']})", theme),
        line("pulse", x, 162, "Contributions per day", theme, heading=True),
        line("arrow-up", x, 184, f"Highest in a day at {stats['highest']}", theme),
        line("graph", x, 204, f"Average per day at ~{stats['average']:.2f}", theme),
    ]

    top = 34 + max(cal_height, 190) + 18
    parts.append(line("code", 8, top, "Languages", theme, heading=True))
    parts.append(f'<text x="32" y="{top + 18}" class="s">Code in all my repositories, notebooks counted by their code cells</text>')
    legend_top = top + 48
    parts.append(donut(rows, legend_top))
    for i, (name, pct) in enumerate(rows):
        y = legend_top + i * 24
        parts.append(
            f'<circle cx="196" cy="{y - 4}" r="5" fill="{COLOURS.get(name, OTHER)}"/>'
            f'<text x="210" y="{y}" class="b">{escape(name)}</text>'
            f'<text x="{WIDTH - 20}" y="{y}" class="b" text-anchor="end">{pct:.1f}%</text>'
        )
    height = legend_top + 24 * len(rows) + 20

    summary = (
        f"{stats['total']} contributions in the last year, current streak {stats['current']} days, "
        f"best streak {stats['best']} days in {stats['best_year']}. Languages: "
        + ", ".join(f"{name} {pct:.1f}%" for name, pct in rows)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(summary)}">'
        f"<title>{escape(summary)}</title>"
        "<!-- Icons: Primer Octicons, MIT License, Copyright GitHub Inc. -->"
        "<style>"
        'text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}'
        f".h{{fill:{theme['title']};font-size:16px}}"
        f".b{{fill:{theme['text']};font-size:14px}}"
        f".s{{fill:{theme['text']};font-size:11px}}"
        "</style>"
        + "".join(parts)
        + "</svg>\n"
    )


def main():
    token = os.environ.get("LANG_TOKEN")
    if not token:
        sys.exit("LANG_TOKEN is not set")
    try:
        days = contributions()
        past = history(token)
        rows = languages(token)
    except (urllib.error.URLError, RuntimeError) as error:
        sys.exit(f"Keeping the old card: {error}")
    stats = streaks(days, past)
    for name, theme in THEMES.items():
        with open(f"card-{name}.svg", "w", encoding="utf-8") as handle:
            handle.write(card(days, stats, rows, theme))


if __name__ == "__main__":
    main()
