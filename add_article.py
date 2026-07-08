"""
Add a new Education Hall article to the TomoClub site.

Usage:
    python add_article.py --title "How X Did Y" --slug "custom-slug-name" \
        --date "July 6, 2026" --category "Leadership" \
        --cover "https://example.com/cover.jpg" \
        --content-file path/to/content.html \
        --alt "Speaker Name"

Notes:
    - --slug is optional; derived from --title if omitted.
    - --cover can be a URL (downloaded) or a local file path (copied).
    - --content-file should contain the raw HTML that goes inside
      <div class="article-content">...</div> (the same format used in
      articles_data.js: <h3>, <p>, <ul><li>, and centered <img> blocks).
      Alternatively pass the HTML directly with --content.
    - --alt sets the homepage card image alt text and og/twitter description;
      defaults to --title.

What it does (duplicate-safe / idempotent -- safe to re-run with the same slug):
    1. Creates articles/<slug>/ and renders its index.html using the same
       master template as generate_article_pages.py.
    2. Downloads the cover image (and any external images referenced in the
       content) into articles/images/, localizing paths in the content.
    3. Adds an entry to articlesData in articles_data.js.
    4. Adds an entry to article_metadata in generate_article_pages.py
       (kept as a historical record; this script does not invoke that
       script's full-batch regeneration, which would touch every article
       folder at once).
    5. Appends a new card at the END of #articles-grid in index.html.
       This is deliberate, not arbitrary: script.js sorts the Education
       Hall grid by DOM position (data-timestamp = index in the DOM), and
       "Newest First" is the default sort -- so the newest article must be
       the LAST card in the DOM to display first on page load.
"""

import argparse
import json
import os
import re
import subprocess
import sys

from pdf_image_utils import extract_pdf_images  # noqa: F401 -- re-exported for callers


def normalize_content(html: str) -> str:
    """Collapse a multi-line content file into the single-line style used
    throughout articles_data.js (whitespace between HTML tags is not
    significant, so this is purely cosmetic/consistency)."""
    lines = [line.strip() for line in html.splitlines()]
    return " ".join(line for line in lines if line)


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def download_image(url_or_path: str, local_path: str) -> bool:
    if os.path.exists(local_path):
        return True
    if os.path.exists(url_or_path):
        with open(url_or_path, 'rb') as src, open(local_path, 'wb') as dst:
            dst.write(src.read())
        return True
    try:
        print(f"  Downloading {url_or_path}...")
        cmd = [
            'curl.exe', '-A',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            '-L', '-o', local_path, url_or_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  Error downloading {url_or_path}: {e}")
        return False


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">

    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{title} | TomoClub Education Hall">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="https://www.tomoclub.org/articles/images/{cover_local_name}">
    <meta property="og:url" content="https://www.tomoclub.org/articles/{slug}/">
    <meta property="og:type" content="article">

    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} | TomoClub Education Hall">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="https://www.tomoclub.org/articles/images/{cover_local_name}">

    <title>{title} | TomoClub Education Hall</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="../../styles.css?v=21">
    <style>
        body {{
            background: var(--bg-main);
            color: var(--text-main);
        }}

        .article-hero {{
            padding: 160px 0 80px;
            background: var(--hero-glow-teal);
            text-align: center;
        }}

        .article-meta {{
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            align-items: center;
            margin-bottom: 2rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .article-category {{
            background: rgba(42, 180, 184, 0.1);
            color: var(--teal);
            padding: 0.4rem 1rem;
            border-radius: 999px;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .article-title {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            line-height: 1.1;
            max-width: 1000px;
            margin: 0 auto 3rem;
            font-weight: 800;
        }}

        .article-cover {{
            width: 100%;
            max-width: 1100px;
            aspect-ratio: 16/9;
            object-fit: cover;
            border-radius: 32px;
            box-shadow: var(--shadow-xl);
            margin: 0 auto;
            display: block;
            border: 1px solid var(--border-color);
        }}

        .article-content {{
            max-width: 800px;
            margin: 5rem auto;
            padding: 0 1.5rem;
            line-height: 1.8;
            font-size: 1.15rem;
            color: var(--text-main);
        }}

        .article-content h3 {{
            font-size: 2rem;
            margin: 3rem 0 1.5rem;
            color: var(--text-main);
            font-weight: 700;
        }}

        .article-content p {{
            margin-bottom: 1.5rem;
        }}

        .article-content ul {{
            margin-bottom: 2rem;
            padding-left: 1.5rem;
        }}

        .article-content li {{
            margin-bottom: 0.75rem;
        }}

        .back-nav {{
            max-width: 800px;
            margin: 4rem auto;
            padding: 0 1.5rem;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--teal);
            font-weight: 600;
            text-decoration: none;
            transition: var(--transition);
        }}

        .back-link:hover {{
            transform: translateX(-5px);
        }}

        nav {{
            position: fixed;
            top: 1.5rem;
            left: 50%;
            transform: translateX(-50%);
            width: calc(100% - 3rem);
            max-width: 1200px;
            z-index: 1000;
            padding: 0.75rem 1.5rem;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}

        .nav-item a {{
            color: #94A3B8;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: var(--transition);
        }}

        .nav-item a:hover {{
            color: #fff;
        }}

        .logo {{
            font-weight: 800;
            font-size: 1.5rem;
            text-decoration: none;
        }}

        body.dark-theme {{
            --bg-main: #020617;
            --text-main: #f1f5f9;
            --border-color: rgba(255,255,255,0.1);
        }}
    </style>
</head>
<body>
    <nav>
        <a href="../../#home" class="logo">
            <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
        </a>
        <div class="nav-links">
            <div class="nav-item"><a href="../../#education-hall">Education Hall</a></div>
            <div class="nav-item"><a href="../../#signup" class="btn btn-primary" style="padding: 0.6rem 1.2rem; border-radius: 999px; font-size: 0.85rem;">Request a Pilot</a></div>
        </div>
    </nav>

    <article>
        <div class="back-nav" style="margin-top: 140px; margin-bottom: -120px;">
            <a href="../../#education-hall" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; font-weight: 700; border-radius: 12px; text-decoration: none;">
                <i data-lucide="arrow-left"></i> View More
            </a>
        </div>
        <header class="article-hero">
            <div class="container">
                <div class="article-meta">
                    <span class="article-category">{category}</span>
                    <span class="article-date">{date}</span>
                </div>
                <h1 class="article-title">{title}</h1>
                <img src="{cover_local}" alt="{title}" class="article-cover">
            </div>
        </header>

        <div class="article-content">
            {content}
        </div>

        <div class="back-nav">
            <a href="../../#education-hall" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; font-weight: 700; border-radius: 12px; text-decoration: none;">
                <i data-lucide="arrow-left"></i> View More
            </a>
        </div>
    </article>

    <!-- Substack Newsletter Section -->
    <section class="newsletter-section" style="padding: 4rem 0; background: var(--bg-main); border-top: 1px solid var(--border-color); text-align: center;">
        <div class="container">
            <div class="glass-card" style="padding: 3rem 2rem; background: var(--card-grad-slate); border-radius: 24px; border: 1px solid var(--border-color); max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: var(--shadow-md);">
                <span class="badge" style="margin-bottom: 1rem; background: rgba(42, 180, 184, 0.1); color: var(--teal); border: 1px solid rgba(42, 180, 184, 0.2);">Weekly Insights</span>
                <h3 style="color: var(--navy); margin-bottom: 0.5rem; font-size: 1.5rem;">Join the TomoClub Newsletter</h3>
                <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 2rem; max-width: 480px;">Insights on K-12 education, AI literacy, and future-ready skills.</p>
                <div style="width: 100%; max-width: 480px; display: flex; justify-content: center; overflow: hidden; border-radius: 12px;">
                    <iframe src="https://tomoclub.substack.com/embed" width="480" height="320" style="border: 1px solid var(--border-color); background: white; border-radius: 12px;" frameborder="0" scrolling="no"></iframe>
                </div>
            </div>
        </div>
    </section>

    <footer style="background: var(--surface); padding: 5rem 0; border-top: 1px solid var(--border-color);">
        <div class="container text-center">
            <div class="logo" style="margin-bottom: 2rem;">
                <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
            </div>
            <div style="display: flex; gap: 2rem; margin-bottom: 2rem; justify-content: center; align-items: center;">
                <a href="https://x.com/TomoClub_edu" target="_blank" rel="noopener noreferrer" style="color: var(--text-muted); display: inline-flex; align-items: center; justify-content: center; text-decoration: none;"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" style="display: inline-block; vertical-align: middle;"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.134l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
            </div>
            <p style="color: var(--text-muted);">&copy; 2026 TomoClub. All rights reserved.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script>
        lucide.createIcons();
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-theme');
        }}
    </script>
</body>
</html>
"""

GRADIENTS = ['teal', 'gold', 'crimson', 'slate']


def next_article_key(articles_data_js: str) -> str:
    nums = [int(m) for m in re.findall(r'"article_(\d+)":', articles_data_js)]
    return f"article_{(max(nums) + 1) if nums else 1}"


def update_articles_data_js(art_key, content_html):
    path = 'articles_data.js'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'"{art_key}"' in content:
        print(f"  articles_data.js already has {art_key}, skipping.")
        return

    # json.dumps produces a properly escaped, quoted string that is also
    # valid as a JS string literal (handles embedded quotes/newlines/unicode).
    escaped = json.dumps(content_html)
    marker = "const articlesData = {\n"
    idx = content.index(marker) + len(marker)
    line = f'  "{art_key}": {escaped},\n'
    content = content[:idx] + line + content[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Added {art_key} to articles_data.js")


def update_generate_article_pages_py(art_key, title, date, category, slug, cover):
    path = 'generate_article_pages.py'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'"{art_key}"' in content:
        print(f"  generate_article_pages.py already has {art_key}, skipping.")
        return

    title_escaped = title.replace('"', '\\"')
    block = f'''    "{art_key}": {{
        "title": "{title_escaped}",
        "date": "{date}",
        "category": "{category}",
        "slug": "{slug}",
        "cover": "{cover}"
    }},
'''
    marker = "article_metadata = {\n"
    idx = content.index(marker) + len(marker)
    content = content[:idx] + block + content[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Added {art_key} metadata to generate_article_pages.py")


def update_index_html_card(slug, title, alt, cover_local_name, gradient):
    path = 'index.html'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'href="articles/{slug}/"' in content:
        print(f"  index.html already has a card for {slug}, skipping.")
        return

    card = f'''                <a href="articles/{slug}/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;" target="_blank">
                    <div style="background: var(--card-grad-{gradient}); height: 100%; display: flex; flex-direction: column;">
                        <img src="articles/images/{cover_local_name}" alt="{alt}" style="width: 100%; height: 220px; object-fit: cover; border-bottom: 1px solid var(--border-color);">
                        <div style="padding: 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                            <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;" class="article-title">{title}</h3>
                            <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                        </div>
                    </div>
                </a>

'''
    marker = '<div class="grid-3 animate-on-scroll" id="articles-grid">'
    grid_start = content.index(marker) + len(marker)
    grid_end = content.index('</div>\n        </section>', grid_start)
    content = content[:grid_end] + card + content[grid_end:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Appended new card at end of index.html #articles-grid (displays first under 'Newest First')")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--title', required=True)
    parser.add_argument('--slug', help='Defaults to a slugified version of --title')
    parser.add_argument('--date', required=True, help='e.g. "July 6, 2026"')
    parser.add_argument('--category', required=True)
    parser.add_argument('--cover', required=True, help='URL or local file path for the cover image')
    parser.add_argument('--content', help='Raw HTML for the article content')
    parser.add_argument('--content-file', help='Path to a file containing the raw HTML content')
    parser.add_argument('--alt', help='Image alt text / description; defaults to --title')
    parser.add_argument('--gradient', choices=GRADIENTS, help='Homepage card gradient; auto-rotates if omitted')
    args = parser.parse_args()

    if not args.content and not args.content_file:
        print("Provide article content via --content or --content-file")
        sys.exit(1)

    content_html = args.content
    content_file_dir = None
    if args.content_file:
        with open(args.content_file, encoding='utf-8') as f:
            content_html = f.read()
        content_file_dir = os.path.dirname(os.path.abspath(args.content_file))
    content_html = normalize_content(content_html)

    slug = args.slug or slugify(args.title)
    alt = args.alt or args.title

    article_dir = f"articles/{slug}"
    if os.path.exists(article_dir):
        print(f"articles/{slug}/ already exists. Choose a different --slug or remove it first.")
        sys.exit(1)

    os.makedirs(article_dir, exist_ok=True)
    os.makedirs('articles/images', exist_ok=True)

    cover_ext = args.cover.split('.')[-1].split('?')[0]
    cover_local_name = f"{slug}-cover.{cover_ext}"
    cover_local_path = f"articles/images/{cover_local_name}"
    print(f"Cover image -> {cover_local_path}")
    if not download_image(args.cover, cover_local_path):
        print("Failed to obtain cover image; aborting.")
        sys.exit(1)

    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
    for i, img_url in enumerate(img_tags):
        if img_url.startswith('../../') or img_url.startswith('articles/'):
            continue
        ext = img_url.split('.')[-1].split('?')[0]
        local_name = f"{slug}-img-{i + 1}.{ext}"
        local_path = f"articles/images/{local_name}"
        # Bare filenames (no scheme, no slash) are treated as sitting next
        # to --content-file -- e.g. images pulled out of a source PDF with
        # pdf_image_utils.extract_pdf_images(). Resolve against that
        # directory before falling back to download_image's cwd-relative
        # and URL handling.
        source = img_url
        if (content_file_dir and not img_url.startswith(('http://', 'https://'))
                and '/' not in img_url):
            candidate = os.path.join(content_file_dir, img_url)
            if os.path.exists(candidate):
                source = candidate
        if download_image(source, local_path):
            content_html = content_html.replace(img_url, f"../../articles/images/{local_name}")

    final_html = HTML_TEMPLATE.format(
        title=args.title,
        description=alt,
        category=args.category,
        date=args.date,
        cover_local=f"../../articles/images/{cover_local_name}",
        cover_local_name=cover_local_name,
        slug=slug,
        content=content_html,
    )
    with open(f"{article_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Rendered {article_dir}/index.html")

    with open('articles_data.js', encoding='utf-8') as f:
        art_key = next_article_key(f.read())
    print(f"Article key: {art_key}")

    update_articles_data_js(art_key, content_html)
    update_generate_article_pages_py(art_key, args.title, args.date, args.category, slug, args.cover)

    with open('index.html', encoding='utf-8') as f:
        existing_cards = len(re.findall(r'href="articles/', f.read()))
    gradient = args.gradient or GRADIENTS[existing_cards % len(GRADIENTS)]
    update_index_html_card(slug, args.title, alt, cover_local_name, gradient)

    print("\nDone. Review with: git diff --stat")
    print("Then preview locally before committing.")


if __name__ == '__main__':
    main()
