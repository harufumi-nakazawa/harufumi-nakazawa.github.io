#!/usr/bin/env python3
"""Generate movies/index.html from Obsidian movies.md."""

from __future__ import annotations

import argparse
import html
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_SOURCE = Path.home() / "Dropbox (Personal)/obsidian/15_media/movies.md"
REPO_ROOT = Path(__file__).resolve().parent
OUTPUT = REPO_ROOT / "movies/index.html"

YEAR_RE = re.compile(r"[\(（](\d{4})[\)）]")


def parse_watched_entries(text: str) -> list[str]:
    stop = text.find("# To Watch")
    if stop >= 0:
        text = text[:stop]

    entries: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            entries.append(line[2:].strip())
    return entries


def extract_year(entry: str) -> int | None:
    match = YEAR_RE.search(entry)
    return int(match.group(1)) if match else None


def normalize_title(entry: str) -> str:
    title = YEAR_RE.sub("", entry).lower()
    return re.sub(r"[^a-z0-9\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]", "", title)


def bracket_titles(entry: str) -> set[str]:
    title = YEAR_RE.sub("", entry)
    return {match.strip() for match in re.findall(r"「([^」]+)」", title) if match.strip()}


def primary_title(entry: str) -> str:
    title = YEAR_RE.sub("", entry).strip()
    return re.sub(r"[^一-龯ぁ-んァ-ン]", "", title)


def is_japanese_primary(entry: str) -> bool:
    title = YEAR_RE.sub("", entry)
    return len(re.findall(r"[A-Za-z]", title)) < 3


def core_titles(entry: str) -> set[str]:
    titles = bracket_titles(entry)
    if is_japanese_primary(entry):
        primary = primary_title(entry)
        if primary:
            titles.add(primary)
    return titles


def choose_preferred(existing: str, candidate: str) -> str:
    """Keep the richer display title when the same film appears twice."""
    if len(candidate) > len(existing):
        return candidate
    if len(candidate) == len(existing):
        return candidate if candidate < existing else existing
    return existing


def same_film(a: str, b: str) -> bool:
    year_a = extract_year(a)
    year_b = extract_year(b)
    if year_a is None or year_b is None or year_a != year_b:
        return False
    if a == b or normalize_title(a) == normalize_title(b):
        return True
    return bool(core_titles(a) & core_titles(b))


def dedupe_entries(entries: list[str]) -> list[str]:
    deduped: list[str] = []
    no_year: list[str] = []

    for entry in entries:
        year = extract_year(entry)
        if year is None:
            no_year.append(entry)
            continue

        matched = False
        for index, existing in enumerate(deduped):
            if same_film(entry, existing):
                deduped[index] = choose_preferred(existing, entry)
                matched = True
                break
        if not matched:
            deduped.append(entry)

    deduped.extend(no_year)
    deduped.sort(key=lambda item: (extract_year(item) or 9999, item.lower()))
    return deduped


def decade_label(year: int) -> str:
    decade = (year // 10) * 10
    return f"{decade}s"


def group_by_decade(entries: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        year = extract_year(entry)
        if year is None:
            continue
        groups[decade_label(year)].append(entry)

    for decade in groups:
        groups[decade].sort(key=lambda item: (extract_year(item), item.lower()))
    return dict(groups)


def render_sections(groups: dict[str, list[str]]) -> str:
    decade_order = [f"{d}s" for d in range(1930, 2030, 10)]
    sections: list[str] = []

    for decade in decade_order:
        movies = groups.get(decade, [])
        if not movies:
            continue

        items = "\n".join(
            f'                <li class="list-group-item">{html.escape(movie)}</li>'
            for movie in movies
        )
        sections.append(
            f"""        <section class="mb-5">
            <h3>{decade}</h3>
            <ul class="list-group list-group-flush">
{items}
            </ul>
        </section>"""
        )

    return "\n\n".join(sections)


def render_page(sections_html: str, total: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movies - Harufumi Nakazawa</title>
    <meta name="description" content="A personal list of films by Harufumi Nakazawa.">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://harufumi-nakazawa.github.io/movies/">
    <meta property="og:type" content="article">
    <meta property="og:title" content="Movies - Harufumi Nakazawa">
    <meta property="og:description" content="A personal list of films.">
    <meta property="og:url" content="https://harufumi-nakazawa.github.io/movies/">
    <meta property="og:image" content="https://harufumi-nakazawa.github.io/images/lombok.jpg">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="Movies - Harufumi Nakazawa">
    <meta name="twitter:description" content="A personal list of films.">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;1,400;1,600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,700;1,400;1,700&display=swap" rel="stylesheet">
    <link rel="icon" href="../images/favicon.png" type="image/png">
    <link rel="stylesheet" href="../style.css">
</head>

<body>
    <!-- Main Content -->
    <div class="container mt-5">
        <div class="row">
            <div class="col-md-4">
                <div class="card mb-4 sidebar-sticky">
                    <img src="../images/lombok.jpg" class="card-img-top" alt="Your Photo">
                    <div class="card-body">
                        <h3>Harufumi Nakazawa</h3>
                        <div class="sidebar-contact-inline">
                            <a href="mailto:hnakazawa@povertyactionlab.org"><i class="fas fa-envelope"></i> Email</a>
                            <a href="https://github.com/harufumi-nakazawa" target="_blank"><i class="fab fa-github"></i> GitHub</a>
                            <a href="https://linkedin.com/in/harufumi-nakazawa" target="_blank"><i class="fab fa-linkedin"></i> LinkedIn</a>
                        </div>
                        <div class="sidebar-page-links">
                            <a href="../">Home</a>
                            <a href="../research/">Research</a>
                            <a href="../data/">Data</a>
                            <a href="../photography/">Photography</a>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-8">
        <h2>Movies</h2>
        <p>{total} films watched, grouped by release decade.</p>

{sections_html}

            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="py-3 mt-5">
        <div class="container text-center">
            <p>&copy; 2026 Harufumi Nakazawa </p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.min.js"></script>
</body>
</html>
"""


def build(source: Path, output: Path) -> int:
    text = source.read_text(encoding="utf-8")
    entries = parse_watched_entries(text)
    deduped = dedupe_entries(entries)
    groups = group_by_decade(deduped)
    sections_html = render_sections(groups)
    output.write_text(render_page(sections_html, len(deduped)), encoding="utf-8")
    return len(deduped)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"Source file not found: {args.source}")

    count = build(args.source, args.output)
    print(f"Wrote {args.output} ({count} movies)")


if __name__ == "__main__":
    main()
