import os
import re

def remove_dates_from_html(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern for homepage cards: <span style="font-size: 0.85rem; color: ...; font-weight: 600; text-transform: uppercase;">May 11, 2026</span>
    # Pattern for article pages: <span class="article-date">May 11, 2026</span>
    
    # 1. Remove from homepage cards (more specific to avoid accidental matches)
    homepage_pattern = r'<span style="font-size: 0.85rem; color: [^;]+; font-weight: 600; text-transform: uppercase;">[^<]+</span>'
    content = re.sub(homepage_pattern, '', content)
    
    # 2. Remove from article pages
    article_pattern = r'<span class="article-date">[^<]+</span>'
    content = re.sub(article_pattern, '', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Removed dates from {filepath}")
    else:
        print(f"No dates found in {filepath}")

def main():
    base_dir = r'c:\Users\JANMEJAY\Desktop\tom'
    
    # Homepage
    remove_dates_from_html(os.path.join(base_dir, 'index.html'))
    
    # Blog posts
    blog_dir = os.path.join(base_dir, 'blog')
    for root, _, filenames in os.walk(blog_dir):
        for filename in filenames:
            if filename.endswith('.html'):
                remove_dates_from_html(os.path.join(root, filename))

if __name__ == "__main__":
    main()
