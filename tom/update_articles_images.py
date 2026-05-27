import urllib.request
import re
import json

urls = [
    'https://www.tomoclub.org/innovation-in-education/why-tomoclub-exists-and-the-side-of-education-innovation-we-dont-see/',
    'https://www.tomoclub.org/innovation-in-education/how-santa-rosa-schools-are-rethinking-education-today/',
    'https://www.tomoclub.org/innovation-in-education/how-brenda-ortiz-mcgrath-is-rewiring-student-support-in-public-education/',
    'https://www.tomoclub.org/innovation-in-education/how-dr-scott-d-ripley-expanded-access-to-ap-courses/',
    'https://www.tomoclub.org/innovation-in-education/how-dr-jill-handley-is-fixing-whats-broken-in-school-leadership/',
    'https://www.tomoclub.org/innovation-in-education/how-michael-mai-held-great-meadows-together-when-the-money-ran-out/'
]

all_images = {}

for i, url in enumerate(urls):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            start = html.find('elementor-widget-theme-post-content')
            if start == -1: start = 0
            end = html.find('elementor-location-footer')
            if end == -1: end = len(html)
            
            content_html = html[start:end]
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
            
            content_imgs = []
            for img in imgs:
                if 'uploads' in img and 'logo' not in img.lower() and 'icon' not in img.lower():
                    if img not in content_imgs:
                        content_imgs.append(img)
            all_images[f'article_{i+1}'] = content_imgs
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# Read existing articles_data.js
with open('articles_data.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Parse the JSON from the JS string
json_str = js_content.replace('const articlesData = ', '').rstrip().rstrip(';')
articles = json.loads(json_str)

# Embed images into articles
for art_id, img_list in all_images.items():
    if art_id in articles and len(img_list) > 1:
        # The first image is the cover, so we skip it.
        # We'll embed the remaining images nicely spaced.
        remaining_imgs = img_list[1:]
        
        # We split the html into paragraphs
        html_body = articles[art_id]
        parts = html_body.split('</p>')
        
        # Insert an image roughly every (len(parts) / (len(remaining_imgs) + 1)) paragraphs
        if len(parts) > 2 and len(remaining_imgs) > 0:
            step = max(1, len(parts) // (len(remaining_imgs) + 1))
            new_parts = []
            img_index = 0
            for j, p in enumerate(parts):
                new_parts.append(p)
                if p.strip() != '' and (j + 1) % step == 0 and img_index < len(remaining_imgs):
                    img_src = remaining_imgs[img_index]
                    new_parts.append(f'</p><div style="text-align: center; margin: 2rem 0;"><img src="{img_src}" style="max-width: 100%; border-radius: 8px;" /></div><p>')
                    img_index += 1
            
            articles[art_id] = '</p>'.join(new_parts)

# Write it back out
with open('articles_data.js', 'w', encoding='utf-8') as f:
    f.write('const articlesData = ' + json.dumps(articles, indent=2) + ';\n')

print("articles_data.js updated with inner images successfully.")
