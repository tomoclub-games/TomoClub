import os
import re

def process_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else "TomoClub"
    # Remove any tags inside title
    title = re.sub(r'<[^>]+>', '', title).strip()

    # Extract description
    desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>', content, re.IGNORECASE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else "TomoClub is the K–12 implementation partner for AI literacy and future-ready skills."

    # Determine type and image
    og_type = "website"
    image_url = "https://www.tomoclub.org/assets/og-image.jpg"
    filepath_norm = filepath.replace('\\', '/')

    if "podcast-" in filepath_norm:
        og_type = "video.episode"
        yt_match = re.search(r'youtube-nocookie\.com/embed/([^?"]+)', content)
        if yt_match:
            image_url = f"https://img.youtube.com/vi/{yt_match.group(1)}/maxresdefault.jpg"
    elif "blog" in filepath_norm or "articles" in filepath_norm:
        og_type = "article"
        img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if img_match:
            img_src = img_match.group(1)
            if not img_src.startswith('http'):
                # it's a relative path, but let's just use the default og-image for simplicity
                pass

    # remove existing og: and twitter: tags
    content = re.sub(r'<meta\s+property=["\']og:[^>]+>\n?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<meta\s+name=["\']twitter:[^>]+>\n?', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<meta\s+property=["\']twitter:[^>]+>\n?', '', content, flags=re.IGNORECASE)

    # find </head> and insert our tags right before it
    head_end_match = re.search(r'</head>', content, re.IGNORECASE)
    if not head_end_match:
        return # Skip if no head tag

    # generate meta tags
    meta_tags = f"""
    <!-- Open Graph / Social Media Meta Tags -->
    <meta property="og:type" content="{og_type}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:site_name" content="TomoClub">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">
"""
    # Insert tags
    new_content = content[:head_end_match.start()] + meta_tags + content[head_end_match.start():]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated: {filepath}")

for root, dirs, files in os.walk('.'):
    # skip scratch dir
    if 'scratch' in root or '.git' in root:
        continue
    for file in files:
        if file.endswith('.html'):
            process_html_file(os.path.join(root, file))
