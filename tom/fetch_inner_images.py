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
            # The main content usually starts after a specific container.
            # Let's just find all images in the content.
            # Usually content is in a div with elementor-widget-theme-post-content
            start = html.find('elementor-widget-theme-post-content')
            if start == -1: start = 0
            # cut after footer
            end = html.find('elementor-location-footer')
            if end == -1: end = len(html)
            
            content_html = html[start:end]
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
            
            # Filter for actual content images
            content_imgs = []
            for img in imgs:
                if 'uploads' in img and 'logo' not in img.lower() and 'icon' not in img.lower():
                    if img not in content_imgs:
                        content_imgs.append(img)
            all_images[f'article_{i+1}'] = content_imgs
    except Exception as e:
        print(f"Error fetching {url}: {e}")

print(json.dumps(all_images, indent=2))
