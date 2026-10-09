#!/usr/bin/env python3
"""Turn the Substack draft (Markdown) into a page you can open, select all, copy and paste into the Substack editor.

    python3 substack/build_html.py
"""
import os

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "taicy-2026-wrap-up.md")
DST = os.path.join(HERE, "taicy-2026-wrap-up.html")

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TAICY 2026 wrap-up</title>
<style>
  :root {{ --ink: #0f172a; --muted: #475569; --accent: #2ab4b8; --rule: #e2e8f0; --bg: #ffffff; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
         font: 19px/1.6 Georgia, "Times New Roman", serif; }}
  main {{ max-width: 680px; margin: 0 auto; padding: 40px 16px 80px; }}
  h1 {{ font: 700 38px/1.15 -apple-system, "Segoe UI", sans-serif; margin: 0 0 12px; }}
  h1 + p em {{ color: var(--muted); font-size: 21px; }}
  h2 {{ font: 700 26px/1.25 -apple-system, "Segoe UI", sans-serif; margin: 44px 0 12px; }}
  img {{ width: 100%; height: auto; border-radius: 8px; margin: 12px 0 4px; }}
  blockquote {{ margin: 20px 0; padding: 4px 0 4px 18px; border-left: 4px solid var(--accent); font-style: italic; }}
  a {{ color: #0e7c80; }}
  li {{ margin: 4px 0; }}
</style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""

if __name__ == "__main__":
    body = markdown.markdown(open(SRC, encoding="utf-8").read(), extensions=["extra"])
    with open(DST, "w", encoding="utf-8") as f:
        f.write(PAGE.format(body=body))
    print(DST)
