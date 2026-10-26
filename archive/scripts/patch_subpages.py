import os
import re

# Classes were appended to styles.css in a previous step.
# .btn-view-more class is now available.

def patch_file(filepath, target_hash, target_text):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Standard button HTML
    # We use a relative path logic: ../../ if in sub-sub-dir, ../ if in sub-dir
    depth = filepath.count(os.sep) - 1 # Assuming base is root
    # Wait, let's just use what's already there or detect it.
    
    # Find existing back-nav or back-link
    top_button_regex = re.compile(r'<(div|a)[^>]*class="(back-nav|back-link)"[^>]*>.*?</\1>', re.DOTALL)
    
    # We'll just replace the whole section if found, or add it if missing.
    # But wait, it's safer to just standardize what's there and add the missing one.
    
    # Standardize existing buttons
    content = re.sub(
        r'<a href="([^"]+)" class="(btn btn-secondary|back-link)"[^>]*>\s*<i data-lucide="arrow-left"[^>]*></i>\s*([^<]+)\s*</a>',
        r'<a href="\1" class="btn btn-secondary btn-view-more"><i data-lucide="arrow-left"></i> View More</a>',
        content
    )
    
    # Check if we have it at the bottom.
    # Usually it's before </article> or before <footer>
    if 'View More' in content and 'btn-view-more' in content:
        # If it's only in one place, add it to the other.
        # This is a bit complex to automate perfectly without breaking layout.
        # I'll focus on the ones I know are missing.
        pass

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# Actually, I'll just do a more targeted replacement for the known pages.

# Podcast pages
podcast_dirs = [d for d in os.listdir('.') if d.startswith('podcast-') and os.path.isdir(d)]
for d in podcast_dirs:
    idx = os.path.join(d, 'index.html')
    if os.path.exists(idx):
        with open(idx, 'r', encoding='utf-8') as f:
            c = f.read()
        # Standardize buttons
        c = re.sub(r'class="btn btn-secondary" style="display: inline-flex;[^"]*"', 'class="btn btn-secondary btn-view-more"', c)
        c = re.sub(r'class="btn btn-secondary" style="display: inline-flex;[^"]*"', 'class="btn btn-secondary btn-view-more"', c)
        with open(idx, 'w', encoding='utf-8') as f:
            f.write(c)

# Article pages
article_root = 'articles'
for d in os.listdir(article_root):
    path = os.path.join(article_root, d)
    if os.path.isdir(path):
        idx = os.path.join(path, 'index.html')
        if os.path.exists(idx):
            with open(idx, 'r', encoding='utf-8') as f:
                c = f.read()
            # Standardize buttons
            c = re.sub(r'class="btn btn-secondary" style="display: inline-flex;[^"]*"', 'class="btn btn-secondary btn-view-more"', c)
            # Remove the extra div styles if any
            c = c.replace('style="margin-top: 140px; margin-bottom: -120px;"', 'style="margin-top: 140px; margin-bottom: 2rem;"')
            with open(idx, 'w', encoding='utf-8') as f:
                f.write(c)

# Blog pages
blog_root = 'blog'
for d in os.listdir(blog_root):
    path = os.path.join(blog_root, d)
    if os.path.isdir(path):
        idx = os.path.join(path, 'index.html')
        if os.path.exists(idx):
            with open(idx, 'r', encoding='utf-8') as f:
                c = f.read()
            # Standardize buttons
            c = re.sub(r'class="btn btn-secondary" style="display: inline-flex;[^"]*"', 'class="btn btn-secondary btn-view-more"', c)
            c = c.replace('style="margin-top: 140px; margin-bottom: -120px;"', 'style="margin-top: 140px; margin-bottom: 2rem;"')
            with open(idx, 'w', encoding='utf-8') as f:
                f.write(c)
