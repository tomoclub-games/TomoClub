"""
Add a new post to the TomoClub Blog (distinct from the Education Hall --
see add_article.py for that).

Usage:
    python add_blog_post.py --title "Healthy Screen-Time Habits for Kids" \
        --slug "healthy-screen-time-habits-for-kids" \
        --category "Parenting" \
        --description "Meta description / lead paragraph text." \
        --cover path/to/hero.jpeg \
        --content-file path/to/content.html

Notes:
    - --slug is optional; derived from --title if omitted.
    - --cover can be a URL (downloaded) or a local file path (copied). It
      is used ONLY for the homepage card thumbnail and OG/Twitter meta
      tags -- no live blog post actually renders the cover image inside
      the article body (verified against every existing post as of
      2026-07; don't reintroduce it by analogy with articles).
    - Blog posts do NOT show a publish date (removed sitewide in commit
      e6ed3d6, "Remove dates from all blog posts and homepage cards").
      Don't add one back into the template or content.
    - --content-file should contain the raw HTML that goes inside
      <div class="article-content">...</div>: <h2>/<h3> headers, <p>
      paragraphs, <ul><li> lists, and centered image blocks like
      <div style="text-align: center; margin: 2rem 0;"><img src="..."
      style="max-width: 100%; border-radius: 8px;" /></div>.
      Alternatively pass the HTML directly with --content.
    - Any <img src="..."> in the content that is a bare local filename
      (e.g. src="the-5-cs-of-screen-time.jpeg") is assumed to already be
      sitting next to --content-file (e.g. extracted from a source PDF
      with extract_pdf_images() below) and gets copied as-is into
      blog/<slug>/. External URLs get downloaded and localized the same
      way. Paths already starting with "http" that fail to download are
      left untouched with a warning.

What it does (duplicate-safe / idempotent -- safe to re-run with the same slug):
    1. Creates blog/<slug>/ and renders its index.html using the same
       template structure as the most recently published post
       (blog/ai-implementation-in-k12-schools/index.html as of 2026-07).
    2. Saves the cover image as blog/<slug>/hero.<ext> -- co-located with
       the post, NOT a shared blog/images/ folder. (blog/images/ is a
       staging inbox for source assets the user drops before this script
       runs; it is not where published assets live -- see the "clean up
       staging files" note in the skill doc.)
    3. Localizes any content images into blog/<slug>/ alongside hero.
    4. Inserts a new card at the TOP of the #blog grid-3 in index.html.
       This is deliberate, not arbitrary: unlike the Education Hall grid,
       the blog grid has no JS sort/filter -- it's a static grid in DOM
       order, so the newest post must be FIRST in the DOM to display
       first. Don't move insertion to the end by analogy with
       add_article.py.
    5. There is no JS/JSON registry to update for blog posts (no
       blog_data.js equivalent) -- the homepage card IS the registration.
"""

import argparse
import os
import re
import subprocess
import sys

from pdf_image_utils import extract_pdf_images  # noqa: F401 -- re-exported for callers


def normalize_content(html: str) -> str:
    lines = [line.rstrip() for line in html.splitlines()]
    return "\n".join(lines).strip()


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
    <title>{title} | TomoClub Blog</title>
    <meta name="description" content="{description}">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <link rel="stylesheet" href="../../styles.css?v=21">

    <style>
        :root {{
            --article-max-width: 850px;
        }}

        body {{
            background-color: var(--bg-main);
            color: var(--text-main);
            line-height: 1.6;
        }}

        .article-hero {{
            padding: 160px 0 80px;
            background: var(--hero-glow-teal);
            text-align: center;
        }}

        .article-meta {{
            margin-bottom: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 1.5rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-muted);
        }}

        .article-category {{
            background: rgba(42, 180, 184, 0.1);
            color: var(--teal);
            padding: 0.4rem 1rem;
            border-radius: 999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .article-title {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            font-weight: 800;
            margin-bottom: 3rem;
            line-height: 1.1;
            max-width: 1000px;
            margin-left: auto;
            margin-right: auto;
            color: var(--navy);
        }}

        .article-content {{
            max-width: var(--article-max-width);
            margin: 5rem auto;
            padding: 0 1.5rem;
            font-size: 1.2rem;
            line-height: 1.8;
            color: var(--text-main);
        }}

        .article-content h2 {{
            font-size: 2.25rem;
            margin: 4rem 0 1.5rem;
            color: var(--navy);
            font-weight: 700;
        }}

        .article-content h3 {{
            font-size: 1.6rem;
            margin: 3rem 0 1.25rem;
            color: var(--navy);
            font-weight: 700;
        }}

        .article-content p {{
            margin-bottom: 1.75rem;
        }}

        .article-content ul, .article-content ol {{
            margin-bottom: 2.5rem;
            padding-left: 1.5rem;
        }}

        .article-content li {{
            margin-bottom: 1rem;
        }}

        .back-nav {{
            max-width: var(--article-max-width);
            margin: 4rem auto;
            padding: 0 1.5rem;
        }}

        .reflect-box {{
            background: rgba(42, 180, 184, 0.08);
            border-left: 4px solid var(--teal);
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin: 2.5rem 0;
            font-style: italic;
            color: var(--navy);
        }}

        /* Navigation Style matching Main Site */
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
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }}

        .logo {{
            font-weight: 800;
            font-size: 1.75rem;
            text-decoration: none;
            letter-spacing: -0.04em;
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

        @media (max-width: 768px) {{
            .article-title {{
                font-size: 2.5rem;
            }}
            nav {{
                width: calc(100% - 1rem);
                padding: 0.5rem 1rem;
            }}
            .nav-links {{
                display: none;
            }}
        }}
    </style>

    <!-- Open Graph / Social Media Meta Tags -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title} | TomoClub Blog">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="https://www.tomoclub.org/blog/{slug}/{cover_local_name}">
    <meta property="og:site_name" content="TomoClub">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} | TomoClub Blog">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="https://www.tomoclub.org/blog/{slug}/{cover_local_name}">
</head>
<body>
    <nav>
        <div class="container nav-container">
            <a href="../../" class="logo">
            <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
        </a>
        <div class="nav-links">
            <div class="nav-item"><a href="../../#blog">Blog</a></div>
            <div class="nav-item"><a href="../../#signup" class="btn btn-primary" style="padding: 0.6rem 1.2rem; border-radius: 999px; font-size: 0.85rem;">Request a Pilot</a></div>
        </div>
        </div>
    </nav>

    <article>
        <div class="back-nav" style="margin-top: 140px; margin-bottom: 2rem;">
            <a href="../../#blog" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; color: var(--teal); font-weight: 600; border: none; background: transparent; box-shadow: none; padding: 0;">
                <i data-lucide="arrow-left" style="width: 20px; height: 20px;"></i> Back to Blog
            </a>
        </div>

        <header class="article-hero">
            <div class="container">
                <div class="article-meta">
                    <span class="article-category">{category}</span>

                </div>
                <h1 class="article-title">{title}</h1>
            </div>
        </header>

        <div class="article-content">
{content}
        </div>

        <div class="back-nav">
            <a href="../../#blog" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; color: var(--teal); font-weight: 600; border: none; background: transparent; box-shadow: none; padding: 0;">
                <i data-lucide="arrow-left" style="width: 20px; height: 20px;"></i> Back to Blog
            </a>
        </div>
    </article>

    <footer style="background: var(--surface); padding: 6rem 0; border-top: 1px solid var(--border-color);">
        <div class="container">
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center; gap: 2rem;">
                <a href="../../" class="logo">
                    <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
                </a>
                <p style="color: var(--text-muted); max-width: 600px; margin: 0 auto;">The K–12 implementation partner for AI literacy and human skills. Building future-ready schools alongside you.</p>
                <div style="display: flex; gap: 2rem; margin-top: 1rem;">
                    <a href="../../#blog" style="color: var(--text-muted); font-weight: 600;">Blog</a>
                    <a href="../../#pd" style="color: var(--text-muted); font-weight: 600;">Professional Development</a>
                    <a href="../../#future-ready" style="color: var(--text-muted); font-weight: 600;">AI Literacy</a>
                </div>
                <p style="color: var(--text-light); font-size: 0.9rem; margin-top: 2rem;">&copy; 2026 TomoClub. All rights reserved.</p>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script>
        lucide.createIcons();

        // Theme Management
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-theme');
        }}
    </script>
</body>
</html>
"""

# (gradient, category-badge text color) -- derived from the dominant
# pairing actually used across the live #blog grid as of 2026-07 (34
# cards inspected: gold+#D97706 x13, teal+var(--teal) x11, slate+var(--navy)
# x8, plus 2 one-off crimson outliers not worth reproducing).
GRADIENTS = [
    ('gold', '#D97706'),
    ('teal', 'var(--teal)'),
    ('slate', 'var(--navy)'),
]


def update_index_html_card(slug, title, description, category, cover_local_name, gradient, color):
    path = 'index.html'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'href="blog/{slug}/"' in content:
        print(f"  index.html already has a card for {slug}, skipping.")
        return

    card = f'''                    <a href="blog/{slug}/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;" target="_blank">
                        <div style="background: var(--card-grad-{gradient}); height: 100%; display: flex; flex-direction: column;">
                            <img loading="lazy" src="blog/{slug}/{cover_local_name}" alt="{title}" style="width: 100%; height: 200px; object-fit: cover;">
                            <div style="padding: 2rem 2rem 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                                <span style="font-size: 0.85rem; color: {color}; font-weight: 600; text-transform: uppercase;">{category}</span>
                                <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;">{title}</h3>
                                <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">{description}</p>
                                <span class="btn btn-secondary btn-read-more" style="margin-top: auto;">Read More <i data-lucide="arrow-right"></i></span>
                            </div>
                        </div>
                    </a>
'''
    blog_section_start = content.index('id="blog"')
    marker = '<div class="grid-3">'
    grid_marker_idx = content.index(marker, blog_section_start)
    insert_at = grid_marker_idx + len(marker) + 1  # +1 for the trailing newline
    content = content[:insert_at] + card + content[insert_at:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Inserted new card at TOP of index.html #blog grid (displays first -- grid has no JS sort)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--title', required=True)
    parser.add_argument('--slug', help='Defaults to a slugified version of --title')
    parser.add_argument('--category', required=True)
    parser.add_argument('--description', required=True, help='Meta description + homepage card teaser + lead paragraph text')
    parser.add_argument('--cover', required=True, help='URL or local file path for the cover image (homepage card + OG/Twitter meta only -- not shown inline in the post body)')
    parser.add_argument('--content', help='Raw HTML for the article content')
    parser.add_argument('--content-file', help='Path to a file containing the raw HTML content')
    parser.add_argument('--gradient', choices=[g for g, _ in GRADIENTS], help='Homepage card gradient; auto-rotates if omitted')
    args = parser.parse_args()

    if not args.content and not args.content_file:
        print("Provide post content via --content or --content-file")
        sys.exit(1)

    content_html = args.content
    content_file_dir = None
    if args.content_file:
        with open(args.content_file, encoding='utf-8') as f:
            content_html = f.read()
        content_file_dir = os.path.dirname(os.path.abspath(args.content_file))
    content_html = normalize_content(content_html)

    slug = args.slug or slugify(args.title)

    post_dir = f"blog/{slug}"
    if os.path.exists(post_dir):
        print(f"blog/{slug}/ already exists. Choose a different --slug or remove it first.")
        sys.exit(1)

    os.makedirs(post_dir, exist_ok=True)

    cover_ext = args.cover.split('.')[-1].split('?')[0]
    cover_local_name = f"hero.{cover_ext}"
    cover_local_path = f"{post_dir}/{cover_local_name}"
    print(f"Cover image -> {cover_local_path}")
    if not download_image(args.cover, cover_local_path):
        print("Failed to obtain cover image; aborting.")
        sys.exit(1)

    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
    for i, img_src in enumerate(img_tags):
        if img_src.startswith('http://') or img_src.startswith('https://'):
            ext = img_src.split('.')[-1].split('?')[0]
            local_name = f"{slug}-img-{i + 1}.{ext}"
            if download_image(img_src, f"{post_dir}/{local_name}"):
                content_html = content_html.replace(img_src, local_name)
            else:
                print(f"  WARNING: could not download {img_src}; left as-is in content.")
        elif not os.path.isabs(img_src) and '/' not in img_src:
            # Bare filename -- expected to already sit next to --content-file
            # (e.g. images pulled out with extract_pdf_images()). Copy it in.
            src_candidates = [img_src]
            if content_file_dir:
                src_candidates.insert(0, os.path.join(content_file_dir, img_src))
            for candidate in src_candidates:
                if os.path.exists(candidate):
                    dst = f"{post_dir}/{img_src}"
                    if not os.path.exists(dst):
                        with open(candidate, 'rb') as s, open(dst, 'wb') as d:
                            d.write(s.read())
                    break
            else:
                print(f"  WARNING: content references local image '{img_src}' but it wasn't found next to --content-file.")

    final_html = HTML_TEMPLATE.format(
        title=args.title,
        description=args.description,
        category=args.category,
        slug=slug,
        cover_local_name=cover_local_name,
        content=content_html,
    )
    with open(f"{post_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"Rendered {post_dir}/index.html")

    with open('index.html', encoding='utf-8') as f:
        blog_content = f.read()
        blog_section = blog_content[blog_content.index('id="blog"'):]
        existing_cards = len(re.findall(r'href="blog/', blog_section))
    if args.gradient:
        gradient, color = next(g for g in GRADIENTS if g[0] == args.gradient)
    else:
        gradient, color = GRADIENTS[existing_cards % len(GRADIENTS)]
    update_index_html_card(slug, args.title, args.description, args.category, cover_local_name, gradient, color)

    print("\nDone. Review with: git diff --stat")
    print("Then preview locally before committing.")


if __name__ == '__main__':
    main()
