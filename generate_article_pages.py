import json
import os
import re
import urllib.request

# Load article data
with open('articles_data.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Extract JSON from JS
json_str = js_content.replace('const articlesData = ', '').rstrip().rstrip(';')
articles = json.loads(json_str)

# Article metadata (matching index.html)
article_metadata = {
    "article_1": {
        "title": "Why TomoClub Exists – And the Side of Education Innovation We Don’t See",
        "date": "February 11, 2026",
        "category": "Innovation",
        "slug": "why-tomoclub-exists",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/03/why-tomoclub-exists-and-the-side-of-education-innovation-we-dont-see_n1.jpg"
    },
    "article_2": {
        "title": "How Santa Rosa Schools Are Rethinking Education Today",
        "date": "February 11, 2026",
        "category": "School Leadership",
        "slug": "santa-rosa-schools-rethinking-education",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/02/how-santa-rosa-schools-are-rethinking-education-today_article_img_02.jpg"
    },
    "article_3": {
        "title": "How Brenda Ortiz McGrath Is Rewiring Student Support in Public Education",
        "date": "March 9, 2026",
        "category": "Student Support",
        "slug": "brenda-ortiz-mcgrath-student-support",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/03/how-brenda-ortiz-mcgrath-is-rewiring-student-support-in-public-education_img_02.jpg"
    },
    "article_4": {
        "title": "How Dr. Scott D. Ripley Expanded Access to AP Courses",
        "date": "March 17, 2026",
        "category": "Equity",
        "slug": "dr-scott-ripley-ap-access",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/03/how-dr-scott-d-ripley-expanded-access-to-ap-courses_n1.jpg"
    },
    "article_5": {
        "title": "How Dr. Jill Handley Is Fixing What’s Broken in School Leadership",
        "date": "March 30, 2026",
        "category": "Leadership",
        "slug": "dr-jill-handley-school-leadership",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/03/how-dr-jill-handley-is-fixing-whats-broken-in-school-leadership_pic01.jpg"
    },
    "article_6": {
        "title": "How Michael Mai held Great Meadows together when the money ran out",
        "date": "April 12, 2026",
        "category": "Resilience",
        "slug": "michael-mai-great-meadows-resilience",
        "cover": "https://www.tomoclub.org/wp-content/uploads/2026/04/Untitled-800-x-500-px.jpg"
    }
}

# Create base directories
os.makedirs('articles', exist_ok=True)
os.makedirs('articles/images', exist_ok=True)

import subprocess

def download_image(url, local_path):
    if not os.path.exists(local_path):
        try:
            print(f"Downloading {url}...")
            cmd = [
                'curl.exe', '-A', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                '-L', '-o', local_path, url
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    return True

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
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

        /* Dark Theme Support */
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
            <a href="../../#education-hall" class="back-link">
                <i data-lucide="arrow-left"></i> Back to Education Hall
            </a>
        </div>
    </article>

    <footer style="background: var(--surface); padding: 5rem 0; border-top: 1px solid var(--border-color);">
        <div class="container text-center">
            <div class="logo" style="margin-bottom: 2rem;">
                <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
            </div>
            <p style="color: var(--text-muted);">&copy; 2026 TomoClub. All rights reserved.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script>
        lucide.createIcons();
        
        // Simple Theme Check
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-theme');
        }}
    </script>
</body>
</html>
"""

for art_id, meta in article_metadata.items():
    content_html = articles[art_id]
    slug = meta['slug']
    
    # Create article directory
    article_dir = f"articles/{slug}"
    os.makedirs(article_dir, exist_ok=True)
    
    # Download and localise cover image
    cover_ext = meta['cover'].split('.')[-1]
    cover_local_name = f"{slug}-cover.{cover_ext}"
    cover_local_path = f"articles/images/{cover_local_name}"
    download_image(meta['cover'], cover_local_path)
    
    # Localise images inside content
    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
    for i, img_url in enumerate(img_tags):
        ext = img_url.split('.')[-1]
        local_name = f"{slug}-img-{i+1}.{ext}"
        local_path = f"articles/images/{local_name}"
        if download_image(img_url, local_path):
            content_html = content_html.replace(img_url, f"../images/{local_name}")
    
    # Create the index.html for the article
    final_html = html_template.format(
        title=meta['title'],
        description=meta['title'],
        category=meta['category'],
        date=meta['date'],
        cover_local=f"../images/{cover_local_name}",
        content=content_html
    )
    
    with open(f"{article_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)

print("Article pages generated successfully!")
