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
    "article_14": {
        "title": "Preparing Students for 2057: The Leadership Playbook of Jan Olson",
        "date": "August 27, 2026",
        "category": "Leadership",
        "slug": "jan-olson-leadership-playbook",
        "cover": "C:\Users\rohit\AppData\Local\Temp\claude\c--Users-rohit-TomoClub-Projects-TomoClub\55d28847-f164-48eb-bad2-45167a11ba44\scratchpad\page6-img1.jpeg"
    },
    "article_13": {
        "title": "Serve First: How Dr. Ronnie Tarchichi Rebuilds School Districts",
        "date": "August 10, 2026",
        "category": "School Leadership",
        "slug": "serve-first-how-dr-ronnie-tarchichi-rebuilds-school-districts",
        "cover": "articles/images/serve-first-how-dr-ronnie-tarchichi-rebuilds-school-districts-cover.jpeg"
    },
    "article_12": {
        "title": "People Over Programs: Sharon Pepukayi on People-First School Leadership",
        "date": "July 16, 2026",
        "category": "Leadership",
        "slug": "people-over-programs-sharon-pepukayi-on-people-first-school-leadership",
        "cover": "articles/images/Sharon.png"
    },
    "article_11": {
        "title": "Ten Miles Deep: A Lesson in Rural School Leadership from Edison's Dave Eastin",
        "date": "July 9, 2026",
        "category": "Leadership",
        "slug": "dave-eastin-rural-leadership",
        "cover": "articles/images/Dave_Eastin.jpg"
    },
    "article_10": {
        "title": "What Wade Stanford Learned by Doing Every Job in a School District First",
        "date": "July 6, 2026",
        "category": "Leadership",
        "slug": "what-wade-stanford-learned-by-doing-every-job-in-a-school-district-first",
        "cover": "articles/images/Wade_Stanford.jpg"
    },
    "article_9": {
        "title": "What 36 Years in Education Taught One Rural Superintendent",
        "date": "July 2, 2026",
        "category": "School Leadership",
        "slug": "what-36-years-in-education-taught-one-rural-superintendent",
        "cover": "articles/images/Brad_Johnson.jpg"
    },
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
    },
    "article_7": {
        "title": "How Van Dyke's Superintendent Built Trust in a District That Couldn't Afford to Lose Any",
        "date": "June 4, 2026",
        "category": "Leadership",
        "slug": "piper-bognar-van-dyke-leadership",
        "cover": "piper-new.jpg"
    },
    "article_8": {
        "title": "What Chris Parker Learned About Leading Technology When the Budget Says No",
        "date": "June 8, 2026",
        "category": "Technology Leadership",
        "slug": "chris-parker-technology-leadership",
        "cover": "Chris.jpg"
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
            <div class="nav-item"><a href="/contact-us" class="btn btn-primary" style="padding: 0.6rem 1.2rem; border-radius: 999px; font-size: 0.85rem;">Contact Us</a></div>
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
    if meta['cover'] in ["piper-new.jpg", "Chris.jpg"]:
        cover_local_name = meta['cover']
    cover_local_path = f"articles/images/{cover_local_name}"
    download_image(meta['cover'], cover_local_path)
    
    # Localise images inside content
    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
    for i, img_url in enumerate(img_tags):
        ext = img_url.split('.')[-1]
        local_name = f"{slug}-img-{i+1}.{ext}"
        local_path = f"articles/images/{local_name}"
        if download_image(img_url, local_path):
            content_html = content_html.replace(img_url, f"../../articles/images/{local_name}")
    
    # Create the index.html for the article
    final_html = html_template.format(
        title=meta['title'],
        description=meta['title'],
        category=meta['category'],
        date=meta['date'],
        cover_local=f"../../articles/images/{cover_local_name}",
        cover_local_name=cover_local_name,
        slug=slug,
        content=content_html
    )
    
    with open(f"{article_dir}/index.html", 'w', encoding='utf-8') as f:
        f.write(final_html)

print("Article pages generated successfully!")
