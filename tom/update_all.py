import os
import re

# Run fetch_podcasts.py and generate_html.py
os.system('python fetch_podcasts.py')
os.system('python generate_html.py')

# Read podcast_html.txt
with open('podcast_html.txt', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Make sure it has the id="podcast-grid"
html_content = html_content.replace('<div class="grid-3">', '<div class="grid-3" id="podcast-grid">')

# Read index.html
with open('index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

# Replace the block
pattern = re.compile(r'<div class="grid-3" id="podcast-grid">.*?</div>', re.DOTALL)
new_index_content = pattern.sub(html_content.strip(), index_content, count=1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_index_content)

print("index.html updated successfully!")
