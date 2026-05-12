import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Education Hall Read More buttons
content = re.sub(
    r'<span class="btn btn-secondary" style="margin-top: auto; padding: 0.6rem 1.2rem; font-size: 0.9rem; align-self: flex-start;[^"]*">Read More <i data-lucide="arrow-right"[^>]*></i></span>',
    '<span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>',
    content
)

# Also handle those without extra styles
content = re.sub(
    r'<span class="btn btn-secondary" style="margin-top: auto; padding: 0.6rem 1.2rem; font-size: 0.9rem; align-self: flex-start;">Read More <i data-lucide="arrow-right"[^>]*></i></span>',
    '<span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>',
    content
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
