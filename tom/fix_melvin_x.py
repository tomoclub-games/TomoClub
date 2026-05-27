import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Targeted update for Dr. Melvin J. Brown
name_pattern = "Melvin"
x_url = "https://x.com/SuptMJBrown"

pattern = re.compile(r'(<h3>[^<]*' + name_pattern + r'[^<]*</h3>.*?<div class="team-social-links">)(.*?)</div>', re.DOTALL | re.IGNORECASE)

def replacer(match):
    pre = match.group(1)
    inner = match.group(2)
    if 'twitter' not in inner and 'x.com' not in inner:
        link = f'\n                                        <a href="{x_url}" target="_blank"><i data-lucide="twitter"></i></a>\n                                    '
        return pre + inner + link + '</div>'
    return match.group(0)

html = pattern.sub(replacer, html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated Melvin in index.html")
