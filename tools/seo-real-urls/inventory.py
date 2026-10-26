"""Read-only inventory for the SEO Real URLs project.

Records the hash routes in index.html, every route-style '#' link in the repo,
and the gap between sitemap.xml and the real pages on disk.

Usage (from the repo root):
    py tools/seo-real-urls/inventory.py            # writes docs/seo-real-urls/baseline/inventory.md
    py tools/seo-real-urls/inventory.py --check    # prints link count, exits 1 if any route links remain (Phase E)
"""
import os
import re
import sys
from collections import defaultdict
from datetime import date

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "docs", "seo-real-urls", "baseline", "inventory.md")

ROUTES = ["home", "ai-literacy", "future-ready", "pd", "guides", "education-hall",
          "podcast", "results", "faqs", "ebook", "about", "blog"]
SCAN_EXT = {".html", ".js", ".py", ".md", ".json", ".xml", ".txt"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", os.path.join("docs", "seo-real-urls"),
             os.path.join("tools", "seo-real-urls")}
NOT_PAGES = {"archive", "scratch", "docs", "tools", ".claude", "api", "assets"}

R = "|".join(re.escape(r) for r in ROUTES)
END = r"(?=[\"'\s?&)<\]]|$)"
LINK_PATTERNS = [
    # href="#pd", href="../#pd", href="/#pd", href="index.html#pd", href="https://www.tomoclub.org/#pd"
    re.compile(r"href=[\"'](?:\.{1,2}/|/)*(?:https?://(?:www\.)?tomoclub\.org/?)?(?:index\.html)?#(" + R + ")" + END),
    # any absolute tomoclub.org/#route
    re.compile(r"tomoclub\.org/(?:index\.html)?#(" + R + ")" + END),
    # string literals in generators: '../#podcast', "/#blog", 'index.html#education-hall'
    re.compile(r"[\"'`](?:\.\./)+#(" + R + ")" + END),
    re.compile(r"[\"'`]/(?:index\.html)?#(" + R + ")" + END),
    re.compile(r"[\"'`]index\.html#(" + R + ")" + END),
    # preview URLs in skills: http://localhost:8000/index.html#blog
    re.compile(r"localhost(?::\d+)?/(?:index\.html)?#(" + R + ")" + END),
]
END_MD = r"(?=[`\"'\s?&)<\]]|$)"
LINK_PATTERNS = [re.compile(p.pattern.replace(END, END_MD)) for p in LINK_PATTERNS]


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def walk(exts):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        r = os.path.relpath(dirpath, ROOT)
        dirnames[:] = [d for d in dirnames if os.path.normpath(os.path.join(r, d)) not in SKIP_DIRS
                       and d not in {".git", "node_modules", "__pycache__"}]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in exts:
                yield os.path.join(dirpath, f)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def route_sizes():
    html = read(os.path.join(ROOT, "index.html"))
    starts = [(m.start(), m.group(1)) for m in
              re.finditer(r"<div id=\"([a-z-]+)\" class=\"page[\" ]", html)]
    rows = []
    for i, (pos, rid) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else html.find("</main>", pos)
        if end == -1:
            end = len(html)
        rows.append((rid, (end - pos) / 1024))
    return len(html.encode("utf-8")) / 1024, rows


def route_links():
    hits = defaultdict(list)  # file -> [(line, route, text)]
    for path in walk(SCAN_EXT):
        text = read(path)
        seen = set()
        for pat in LINK_PATTERNS:
            for m in pat.finditer(text):
                if m.start(1) in seen:
                    continue
                seen.add(m.start(1))
                line = text.count("\n", 0, m.start()) + 1
                hits[rel(path)].append((line, m.group(1), m.group(0)[:60]))
    return hits


def url_for(relpath):
    p = relpath[:-len("index.html")] if relpath.endswith("index.html") else relpath[:-len(".html")]
    return "/" + p.rstrip("/")


def norm(url):
    url = re.sub(r"^https?://(www\.)?tomoclub\.org", "", url)
    url = url.split("#")[0].rstrip("/")
    return re.sub(r"\.html$", "", url) or "/"


def pages_vs_sitemap():
    pages = {}
    for path in walk({".html"}):
        r = rel(path)
        top = r.split("/")[0]
        if top in NOT_PAGES or "/" not in r and r.startswith("google"):
            continue
        noindex = bool(re.search(r"<meta[^>]+noindex", read(path), re.I))
        pages[norm(url_for(r)) or "/"] = (r, noindex)
    locs = re.findall(r"<loc>([^<]+)</loc>", read(os.path.join(ROOT, "sitemap.xml")))
    return pages, locs


def group(r):
    if r.startswith(".claude/skills/"):
        return "Skills"
    ext = os.path.splitext(r)[1]
    return {".py": "Generator scripts (.py)", ".js": "JavaScript", ".html": "HTML pages"}.get(ext, "Other")


def main():
    hits = route_links()
    total = sum(len(v) for v in hits.values())
    if "--check" in sys.argv:
        print(f"route-style # links: {total} in {len(hits)} files")
        sys.exit(1 if total else 0)

    size_kb, sizes = route_sizes()
    pages, locs = pages_vs_sitemap()
    loc_norm = {norm(l) for l in locs}
    hash_locs = [l for l in locs if "#" in l]
    missing = sorted(u for u, (_, ni) in pages.items() if u not in loc_norm and not ni)
    dead = sorted(l for l in locs if "#" not in l and norm(l) not in pages)

    by_route = defaultdict(int)
    by_group = defaultdict(list)
    for f, rows in hits.items():
        for _, rid, _ in rows:
            by_route[rid] += 1
        by_group[group(f)].append(f)

    o = []
    o.append("# Inventory baseline\n")
    o.append(f"Generated {date.today()} by `tools/seo-real-urls/inventory.py`. Rerun it to refresh. "
             "`--check` gives the Phase E exit check.\n")
    o.append("## Summary\n")
    o.append("| Metric | Value |\n|---|---|")
    o.append(f"| `index.html` size | {size_kb:,.0f} KB |")
    o.append(f"| Hash routes (`.page` divs) in `index.html` | {len(sizes)} |")
    o.append(f"| Route-style `#` links | {total} in {len(hits)} files |")
    o.append(f"| Sitemap entries | {len(locs)} ({len(hash_locs)} with `#`) |")
    o.append(f"| Real indexable pages on disk | {sum(1 for _, ni in pages.values() if not ni)} |")
    o.append(f"| Pages missing from sitemap | {len(missing)} |")
    o.append(f"| Sitemap entries with no page on disk | {len(dead)} |\n")

    o.append("## Routes in `index.html`\n")
    o.append("Size is the HTML from the route's `<div>` to the next one (approximate).\n")
    o.append("| Route | Size | Route links to it |\n|---|---|---|")
    for rid, kb in sizes:
        o.append(f"| `#{rid}` | {kb:,.0f} KB | {by_route.get(rid, 0)} |")
    for rid in ROUTES:
        if rid not in dict(sizes):
            o.append(f"| `#{rid}` | (no div) | {by_route.get(rid, 0)} |")
    o.append("")

    o.append("## Route-style `#` links by file\n")
    o.append("Phase E must bring this list to zero. In-page anchors such as `#signup` are not counted.\n")
    for g in ["Generator scripts (.py)", "Skills", "JavaScript", "HTML pages", "Other"]:
        files = sorted(by_group.get(g, []))
        if not files:
            continue
        o.append(f"### {g} ({len(files)} files, {sum(len(hits[f]) for f in files)} links)\n")
        o.append("| File | Links | Routes |\n|---|---|---|")
        for f in files:
            rs = sorted({rid for _, rid, _ in hits[f]})
            o.append(f"| `{f}` | {len(hits[f])} | {', '.join(rs)} |")
        o.append("")

    o.append("## Sitemap\n")
    o.append("### Current entries\n")
    for l in locs:
        o.append(f"- `{l}`" + (" (hash URL)" if "#" in l else ""))
    o.append("")
    o.append(f"### Pages missing from the sitemap ({len(missing)})\n")
    o.append("Excludes pages with `noindex` and the folders " + ", ".join(f"`{d}/`" for d in sorted(NOT_PAGES)) + ".\n")
    for u in missing:
        o.append(f"- `{u}` (`{pages[u][0]}`)")
    o.append("")
    if dead:
        o.append(f"### Sitemap entries with no page on disk ({len(dead)})\n")
        for l in dead:
            o.append(f"- `{l}`")
        o.append("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(o))
    print(f"wrote {rel(OUT)}: {total} route links in {len(hits)} files, "
          f"{len(missing)} pages missing from sitemap")


if __name__ == "__main__":
    main()
