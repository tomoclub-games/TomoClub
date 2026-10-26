"""Rewrite route-style '#' links (/#pd, ../#podcast, tomoclub.org/#blog, ...) to real URLs.

Dry run by default: prints what would change per file. --apply writes the files.
Generated pages are skipped (edit pages/ and run build_pages.py instead).

Usage (from the repo root):
    py tools/seo-real-urls/rewrite_links.py            # dry run
    py tools/seo-real-urls/rewrite_links.py --apply
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inventory  # noqa: E402  (shares ROUTES, file walking and the skip list)

ROOT = inventory.ROOT
SITE = "https://www.tomoclub.org"
TARGET = {r: "/" + r for r in inventory.ROUTES}
TARGET.update({"home": "/", "pd": "/professional-development", "ebook": "/leaders-of-tomorrow"})

R = inventory.R
END = r"(?=[\"'`\s?&)<\]]|$)"
ABSOLUTE = re.compile(r"(?:https?://)?(?:www\.)?tomoclub\.org/?(?:index\.html)?#(" + R + ")" + END)
LOCALHOST = re.compile(r"(https?://localhost(?::\d+)?)/(?:index\.html)?#(" + R + ")" + END)
# A quote (attribute value or string literal), then a relative prefix, then #route.
QUOTED = re.compile(r"([\"'`])((?:\.{1,2}/)+|/|(?:\.{1,2}/)*index\.html)#(" + R + ")" + END)
# A bare href="#route". Only inside href, so JS maps such as the hash shim's {'#pd': ...} are left alone.
BARE_HREF = re.compile(r"\bhref=([\"'])#(" + R + ")" + END)


def generated_outputs():
    outs = set()
    for fname in os.listdir(os.path.join(ROOT, "pages")):
        if fname.endswith(".html"):
            text = open(os.path.join(ROOT, "pages", fname), encoding="utf-8").read()
            m = re.search(r"^output: (.+)$", text, re.M)
            if m:
                outs.add(m.group(1).strip())
    return outs


def rewrite(text):
    flagged = []

    text, n_abs = ABSOLUTE.subn(lambda m: SITE + TARGET[m.group(1)], text)
    text, n_loc = LOCALHOST.subn(lambda m: m.group(1) + TARGET[m.group(2)], text)

    ids = set(re.findall(r"\bid=[\"']([\w-]+)[\"']", text))

    def bare(m):
        quote, route = m.groups()
        if route in ids:
            # A matching id="x" in this file means it may be an in-page anchor.
            flagged.append(route)
            return m.group(0)
        return f"href={quote}{TARGET[route]}"

    text, n_rel = QUOTED.subn(lambda m: m.group(1) + TARGET[m.group(3)], text)
    text, n_bare = BARE_HREF.subn(bare, text)
    return text, n_abs + n_loc + n_rel + n_bare - len(flagged), flagged


def main():
    apply = "--apply" in sys.argv
    skip = generated_outputs() | {"sitemap.xml"}
    total = files = 0
    review = []
    for path in inventory.walk(inventory.SCAN_EXT):
        rel = inventory.rel(path)
        if rel in skip or rel.startswith("archive/"):
            continue
        if rel.endswith(".md") and not rel.startswith(".claude/skills/"):
            continue  # notes and reports record history; only skills generate pages
        try:
            raw = open(path, encoding="utf-8", newline="").read()
        except UnicodeDecodeError:
            print(f"skip  {rel} (not UTF-8)")
            continue
        crlf = "\r\n" in raw
        new, n, flagged = rewrite(raw.replace("\r\n", "\n"))
        if flagged:
            review.append((rel, sorted(set(flagged))))
        if not n:
            continue
        files += 1
        total += n
        print(f"{n:4}  {rel}")
        if apply:
            with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as fh:
                fh.write(new)
    print(f"{'Rewrote' if apply else 'Would rewrite'} {total} links in {files} files.")
    if review:
        print("Not changed, review by hand (bare #x where the file also has id=\"x\"):")
        for rel, routes in review:
            print(f"      {rel}: {', '.join('#' + r for r in routes)}")


if __name__ == "__main__":
    main()
