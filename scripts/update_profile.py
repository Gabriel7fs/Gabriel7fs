#!/usr/bin/env python3
"""Generate a GitHub profile card using public GitHub data and profile.json."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from string import Template
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com"
START = "<!-- PROFILE-CONTENT:START -->"
END = "<!-- PROFILE-CONTENT:END -->"


def github_get(path: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "Gabriel7fs-profile-card",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    for attempt in range(3):
        try:
            with urlopen(Request(API + path, headers=headers), timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(
                f"GitHub API returned HTTP {error.code} for {path}. "
                "No new card was saved. Check authentication and API limits."
            ) from None
        except (URLError, TimeoutError) as error:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError("Could not reach the GitHub API. No new card was saved.") from error


def collect_data(config: dict) -> dict:
    username = config["username"]
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        raise ValueError("Invalid GitHub username in profile.json")
    user = github_get("/users/" + quote(username, safe=""))
    repositories = []
    page = 1
    while True:
        query = urlencode({"type": "owner", "per_page": 100, "page": page})
        batch = github_get(f"/users/{quote(username, safe='')}/repos?{query}")
        repositories.extend(
            repo for repo in batch
            if not repo.get("private")
            and repo["owner"]["login"].casefold() == username.casefold()
        )
        if len(batch) < 100:
            break
        page += 1

    original_repositories = [repo for repo in repositories if not repo["fork"]]
    excluded = {name.casefold() for name in config.get("language_excluded_repositories", [])}
    language_repositories = [
        repo for repo in original_repositories if repo["name"].casefold() not in excluded
    ]

    def languages(repo: dict) -> dict:
        path = "/repos/" + quote(username, safe="") + "/" + quote(repo["name"], safe="") + "/languages"
        return github_get(path)

    language_bytes = Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(languages, language_repositories):
            language_bytes.update({name: int(size) for name, size in result.items()})

    return {
        "username": user["login"],
        "public_repos": int(user["public_repos"]),
        "stars": sum(int(repo["stargazers_count"]) for repo in original_repositories),
        "followers": int(user["followers"]),
        "language_bytes": dict(sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))),
        "language_repositories": len(language_repositories),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def language_svg(data: dict) -> str:
    languages = sorted(
        ((name, int(size)) for name, size in data["language_bytes"].items() if int(size) > 0),
        key=lambda item: (-item[1], item[0]),
    )
    total = sum(size for _, size in languages)
    if not total:
        return '<text x="66" y="505" fill="#A9BCD0" font-size="18">No language data in public original repositories yet.</text>'
    entries = languages[:3]
    remaining = sum(size for _, size in languages[3:])
    if remaining:
        entries.append(("Other", remaining))
    colors = ["#8BC8F6", "#5D9FD3", "#4275A5", "#52667D"]
    fragments = []
    x = 66.0
    for index, (name, size) in enumerate(entries):
        width = 1148 * size / total
        fragments.append(
            f'<rect x="{x:.3f}" y="482" width="{width:.3f}" height="8" fill="{colors[index]}"/>'
        )
        label_x = 66 + index * 287
        fragments.append(
            f'<circle cx="{label_x + 4}" cy="516" r="4" fill="{colors[index]}"/>'
            f'<text x="{label_x + 18}" y="522" fill="#C5D5E5" font-size="18">'
            f'{escape(name)} <tspan fill="#8AA2B9">{100 * size / total:.1f}%</tspan></text>'
        )
        x += width
    return "\n".join(fragments)


def render_card(config: dict, data: dict) -> str:
    if data["username"].casefold() != config["username"].casefold():
        raise ValueError("The data snapshot belongs to a different GitHub account")
    updated = datetime.fromisoformat(data["updated_at"]).astimezone(ZoneInfo("America/Sao_Paulo"))
    values = {key: escape(str(config[key])) for key in (
        "display_name", "headline", "summary", "detail", "featured_stack", "featured_learning", "username"
    )}
    values.update({key: f"{int(data[key]):,}" for key in ("public_repos", "stars", "followers")})
    values["updated"] = updated.strftime("%d %b %Y, %H:%M BRT")
    values["languages"] = language_svg(data)
    return Template((ROOT / "templates/profile-card.svg").read_text()).substitute(values)


def badge(label: str) -> str:
    # A shared dark/blue palette keeps all groups visually consistent.
    logos = {
        "HTML5": "html5", "TypeScript": "typescript", "C": "c", "Angular": "angular",
        "Ionic": "ionic", "Git": "git", "GitHub": "github", "MySQL": "mysql",
        "PostgreSQL": "postgresql", "Spring Boot": "springboot", "Dart": "dart",
        "Flutter": "flutter", "Arduino IDE": "arduino",
    }
    query = {"style": "for-the-badge", "logoColor": "8BC8F6"}
    if label in logos:
        query["logo"] = logos[label]
    url = "https://img.shields.io/badge/" + quote(label.replace("-", "--"), safe="") + "-172638?" + urlencode(query)
    return f"![{label}]({url})"


def render_content(config: dict, data: dict) -> str:
    rows = ["## Skills & experience", "", "| Area | Technologies |", "| --- | --- |"]
    for item in config["experience"]:
        area = str(item["area"]).replace("|", "\\|").replace("\n", " ")
        technologies = str(item["technologies"]).replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {area} | {technologies} |")
    for title, key in (
        ("Technology stack", "technologies"), ("Tools", "tools"), ("Databases", "databases"),
        ("Development environments", "environments"), ("Currently learning", "learning"),
    ):
        rows.extend(["", "## " + title, "", "\n".join(badge(label) for label in config[key])])
    rows.extend([
        "", "## GitHub activity", "",
        f"**{int(data['public_repos'])} public repositories** · "
        f"**{int(data['stars'])} stars on original public repositories** · "
        f"**{int(data['followers'])} followers**", "",
        "Language percentages represent code bytes in original public repositories. "
        "Forks and the profile repository are excluded from the language chart.",
    ])
    return "\n".join(rows)


def build_readme(config: dict, data: dict) -> str:
    current = (ROOT / "README.md").read_text()
    if current.count(START) != 1 or current.count(END) != 1:
        raise ValueError("README.md must contain exactly one pair of PROFILE-CONTENT markers")
    before, rest = current.split(START, 1)
    _, after = rest.split(END, 1)
    return before + START + "\n\n" + render_content(config, data) + "\n\n" + END + after


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-snapshot", type=Path, help="Render a saved public-data snapshot without network access")
    args = parser.parse_args()
    try:
        config = json.loads((ROOT / "profile.json").read_text())
        data = json.loads(args.from_snapshot.read_text()) if args.from_snapshot else collect_data(config)
        card = render_card(config, data)
        readme = build_readme(config, data)
        atomic_write(ROOT / "assets/profile-card.svg", card)
        atomic_write(ROOT / "assets/github-data.json", json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        atomic_write(ROOT / "README.md", readme)
        print(f"Updated {config['username']}: {data['public_repos']} public repositories, "
              f"{data['stars']} stars, {data['followers']} followers.")
        return 0
    except (RuntimeError, ValueError, KeyError, OSError) as error:
        print(f"Profile update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
