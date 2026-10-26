import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the blog section
blog_start = content.find('id="blog"')
if blog_start == -1:
    print('Blog section not found')
    exit(1)

blog_end = content.find('</section>', blog_start)
blog_content = content[blog_start:blog_end]

# Find all cards
# Card structure starts with <a href="blog/
# and has <div style="background: ...;">
# We want to replace the <div style="padding: 3rem 2rem 2rem; ..."> with an image + div

pattern = r'(<a href="blog/[^"]+"[^>]*>\s*<div style="[^"]*background:[^"]+">\s*)(<div style="padding: [^"]+">)'

cards = list(re.finditer(pattern, blog_content))

new_blog_content = blog_content
offset = 0
for i, match in enumerate(cards):
    if i >= 15:
        break
    
    img_name = f'blog post {i+1}.png'
    # encode space as %20
    img_src = img_name.replace(' ', '%20')
    img_tag = f'<img src="./{img_src}" alt="Blog Post {i+1}" style="width: 100%; height: 200px; object-fit: cover;">\n                            '
    
    # replace padding 3rem with 2rem so it looks balanced with image above
    inner_div = match.group(2)
    inner_div = inner_div.replace('padding: 3rem', 'padding: 2rem')
    
    replacement = match.group(1) + img_tag + inner_div
    
    # replace in new_blog_content
    start_idx = match.start() + offset
    end_idx = match.end() + offset
    new_blog_content = new_blog_content[:start_idx] + replacement + new_blog_content[end_idx:]
    
    offset += len(replacement) - (match.end() - match.start())

content = content[:blog_start] + new_blog_content + content[blog_end:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated index.html')
