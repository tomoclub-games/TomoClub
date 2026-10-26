"""Build site pages from pages/*.html and the shared layout in _partials/.

Each page file starts with a front-matter comment (key: value lines, `output` required),
then optional named blocks, then the body. See docs/seo-real-urls/02-layout-spec.md.

Usage (from the repo root):
    py build_pages.py           # write every output file
    py build_pages.py --check   # exit 1 if any committed output differs from a fresh build
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PARTIALS = os.path.join(ROOT, "_partials")
PAGES = os.path.join(ROOT, "pages")

TAG = re.compile(r"\{\{(> *[\w-]+|block:[\w-]+|[\w-]+)\}\}")
BLOCK_START = re.compile(r"<!-- block:([\w-]+) -->\n")
BLOCK_END = "<!-- endblock -->\n"


class BuildError(Exception):
    pass


def read(path):
    # Git on Windows may check files out with CRLF; build on LF and write LF.
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read().replace("\r\n", "\n")


def parse_page(path):
    name = os.path.relpath(path, ROOT)
    text = read(path)
    if not text.startswith("<!--\n"):
        raise BuildError(f"{name}: must start with a front-matter comment")
    end = text.find("\n-->\n")
    if end == -1:
        raise BuildError(f"{name}: front-matter comment is not closed")
    values = {}
    for n, line in enumerate(text[5:end].split("\n"), start=2):
        key, sep, value = line.partition(": ")
        if not sep or not re.fullmatch(r"[\w-]+", key):
            raise BuildError(f"{name}:{n}: expected 'key: value', got {line!r}")
        values[key] = value
    if "output" not in values:
        raise BuildError(f"{name}: front matter has no 'output'")

    rest = text[end + 5:]
    blocks = {}
    while True:
        m = BLOCK_START.match(rest)
        if not m:
            break
        close = rest.find(BLOCK_END, m.end())
        if close == -1:
            raise BuildError(f"{name}: block '{m.group(1)}' has no <!-- endblock -->")
        blocks[m.group(1)] = rest[m.end():close]
        rest = rest[close + len(BLOCK_END):]
    return values, blocks, rest


def render(template_name, page, values, blocks, body, stack=()):
    if template_name in stack:
        raise BuildError(f"{page}: partial '{template_name}' includes itself ({' > '.join(stack + (template_name,))})")
    path = os.path.join(PARTIALS, template_name + ".html")
    if not os.path.isfile(path):
        where = f" (included from _partials/{stack[-1]}.html)" if stack else ""
        raise BuildError(f"{page}: partial '{template_name}' not found{where}")
    stack = stack + (template_name,)

    def resolve(tag, lineno):
        where = f"{page}: _partials/{template_name}.html:{lineno}"
        if tag.startswith(">"):
            return render(tag[1:].strip(), page, values, blocks, body, stack)
        if tag.startswith("block:"):
            if tag[6:] not in blocks:
                raise BuildError(f"{where}: page has no block '{tag[6:]}'")
            return blocks[tag[6:]]
        if tag == "content":
            return body
        if tag not in values:
            raise BuildError(f"{where}: page has no value '{tag}'")
        return values[tag]

    out = []
    for lineno, line in enumerate(read(path).splitlines(keepends=True), start=1):
        # A line holding only one tag is replaced whole; inserted text brings its own newline.
        m = TAG.fullmatch(line.rstrip("\n"))
        if m and m.group(1) != "output":
            out.append(resolve(m.group(1), lineno))
        else:
            out.append(TAG.sub(lambda t: resolve(t.group(1), lineno), line))
    return "".join(out)


def build():
    results = []
    for fname in sorted(os.listdir(PAGES)):
        if not fname.endswith(".html"):
            continue
        page = f"pages/{fname}"
        values, blocks, body = parse_page(os.path.join(PAGES, fname))
        values.setdefault("source", page)
        html = render("layout", page, values, blocks, body)
        results.append((page, values["output"], html))
    return results


def main():
    check = "--check" in sys.argv
    try:
        results = build()
    except BuildError as e:
        print(f"build_pages: {e}", file=sys.stderr)
        sys.exit(2)

    stale = []
    for page, output, html in results:
        target = os.path.join(ROOT, output)
        if check:
            current = read(target) if os.path.isfile(target) else None
            if current != html:
                stale.append(output)
            continue
        os.makedirs(os.path.dirname(target) or ROOT, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(html)
        print(f"{page} -> {output}")

    if check:
        if stale:
            print("Out of date (edit pages/ or _partials/, then run py build_pages.py):", file=sys.stderr)
            for output in stale:
                print(f"  {output}", file=sys.stderr)
            sys.exit(1)
        print(f"{len(results)} page(s) up to date")


if __name__ == "__main__":
    main()
