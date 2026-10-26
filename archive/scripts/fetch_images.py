import urllib.request
import re

req = urllib.request.Request('https://www.tomoclub.org/education-hall/', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
        # Find all image tags
        imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        # Filter for article covers (usually in uploads folder and large)
        covers = [img for img in imgs if 'uploads' in img]
        # remove duplicates preserving order
        unique_covers = []
        for c in covers:
            if c not in unique_covers and 'logo' not in c.lower() and 'icon' not in c.lower():
                unique_covers.append(c)
        for i, c in enumerate(unique_covers[:15]):
            print(f'Image {i+1}: {c}')
except Exception as e:
    print('Error:', e)
