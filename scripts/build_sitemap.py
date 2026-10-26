"""Write sitemap.xml from the HTML pages that Vercel deploys and search engines may index.

A page is listed when it is deployed (not matched by .vercelignore), has no robots noindex,
and is not the source of a redirect in vercel.json. URLs use https://www.tomoclub.org with
no trailing slash (vercel.json: cleanUrls true, trailingSlash false). lastmod is the date of
the last git commit that touched the file, or today for uncommitted changes.

Usage (from the repo root):
    py scripts/build_sitemap.py           # write sitemap.xml
    py scripts/build_sitemap.py --check   # exit 1 if sitemap.xml differs from a fresh build
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import PurePath

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (this file is in scripts/)
SITE = "https://www.tomoclub.org"
OUT = os.path.join(ROOT, "sitemap.xml")
# Listed first, in this order; everything else follows alphabetically.
MAIN = ["/", "/ai-literacy", "/future-ready", "/professional-development", "/parents", "/guides",
        "/education-hall", "/podcast", "/blog", "/results", "/about", "/faqs", "/contact-us",
        "/leaders-of-tomorrow"]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def ignore_patterns():
    patterns = []
    for line in read(os.path.join(ROOT, ".vercelignore")).splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def ignored(rel, patterns):
    parts = rel.split("/")
    for p in patterns:
        if p.endswith("/"):
            if p.rstrip("/") in parts[:-1]:
                return True
        elif "/" in p:
            if fnmatch.fnmatch(rel, p):
                return True
        elif any(fnmatch.fnmatch(part, p) for part in parts):
            return True
    return False


def redirect_sources():
    config = json.loads(read(os.path.join(ROOT, "vercel.json")))
    return {r["source"].rstrip("/") or "/" for r in config.get("redirects", []) if "has" not in r}


def url_path(rel):
    m = re.match(r"podcast/episodes/([\w-]+)/index\.html$", rel)
    if m:
        return "/podcast-" + m.group(1)  # served at /podcast-<id> by a vercel.json rewrite
    path = "/" + rel
    path = path[: -len("index.html")] if path.endswith("/index.html") else path[: -len(".html")]
    return path.rstrip("/") or "/"


def git_dates():
    """Last commit date (YYYY-MM-DD) for every file, newest commit first wins."""
    out = subprocess.run(["git", "log", "--format=@%cs", "--name-only", "--no-renames"],
                         cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    dates, current = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            current = line[1:]
        elif line and line not in dates:
            dates[line] = current
    dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    today = date.today().isoformat()
    for line in dirty.splitlines():
        dates[line[3:].strip().strip('"').split(" -> ")[-1]] = today
    return dates


def build():
    patterns = ignore_patterns()
    redirects = redirect_sources()
    dates = git_dates()
    entries = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
        for name in filenames:
            if not name.endswith(".html"):
                continue
            rel = PurePath(os.path.relpath(os.path.join(dirpath, name), ROOT)).as_posix()
            if ignored(rel, patterns):
                continue
            path = url_path(rel)
            if path in redirects or path == "/podcast-player":
                continue
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+noindex', read(os.path.join(ROOT, rel)), re.I):
                continue
            entries[path] = dates.get(rel, date.today().isoformat())

    order = {p: i for i, p in enumerate(MAIN)}
    paths = sorted(entries, key=lambda p: (order.get(p, len(MAIN)), p))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in paths:
        lines.append(f"  <url><loc>{SITE}{'' if p == '/' else p}{'/' if p == '/' else ''}</loc>"
                     f"<lastmod>{entries[p]}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n", len(paths)


def main():
    xml, count = build()
    if "--check" in sys.argv:
        current = read(OUT).replace("\r\n", "\n") if os.path.isfile(OUT) else ""
        if current != xml:
            print("sitemap.xml is out of date; run py scripts/build_sitemap.py", file=sys.stderr)
            sys.exit(1)
        print(f"sitemap.xml up to date ({count} URLs)")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(xml)
    print(f"Wrote sitemap.xml ({count} URLs)")


if __name__ == "__main__":
    main()
