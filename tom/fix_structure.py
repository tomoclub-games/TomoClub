import os
import re

def fix_navbar(content):
    # Check if it already has nav-container
    if 'nav-container' in content:
        return content
    
    # Simple regex to find <nav>...</nav> and wrap its inner content
    # Note: This assumes <nav> has no attributes or simple attributes
    pattern = re.compile(r'(<nav[^>]*>)(.*?)(</nav>)', re.DOTALL)
    
    def replacer(match):
        nav_open = match.group(1)
        nav_inner = match.group(2).strip()
        nav_close = match.group(3)
        return f'{nav_open}\n        <div class="container nav-container">\n            {nav_inner}\n        </div>\n    {nav_close}'
    
    return pattern.sub(replacer, content)

def fix_view_more_button(content):
    # Fix the View More button to be consistent and premium
    # Change btn-view-more or similar to the standardized version
    old_btn = r'<a href="([^"]+)" class="btn btn-secondary btn-view-more">\s*<i data-lucide="arrow-left"></i> View More\s*</a>'
    new_btn = r'<a href="\1" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; color: var(--teal); font-weight: 600; border: none; background: transparent; box-shadow: none; padding: 0;">\n                <i data-lucide="arrow-left" style="width: 20px; height: 20px;"></i> Back\n            </a>'
    
    content = re.sub(old_btn, new_btn, content)
    return content

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    content = fix_navbar(content)
    # content = fix_view_more_button(content) # Maybe keep the buttons for now or fix them manually
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")
    else:
        print(f"No changes for {filepath}")

def main():
    base_dir = r'c:\Users\JANMEJAY\Desktop\tom'
    
    # List of directories to process
    dirs = [
        os.path.join(base_dir, 'articles'),
        os.path.join(base_dir, 'blog'),
    ]
    
    # Individual files
    files = [
        os.path.join(base_dir, 'podcast-player.html'),
        os.path.join(base_dir, 'privacy-policy.html'),
        os.path.join(base_dir, 'terms-and-conditions.html'),
        os.path.join(base_dir, 'leaders-of-tomorrow', 'index.html'),
    ]
    
    for d in dirs:
        for root, _, filenames in os.walk(d):
            for filename in filenames:
                if filename.endswith('.html'):
                    process_file(os.path.join(root, filename))
    
    for f in files:
        if os.path.exists(f):
            process_file(f)

if __name__ == "__main__":
    main()
