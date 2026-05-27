import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

updates = {
    'Avinash': 'https://x.com/avinash_dtu',
    'Rochit': 'https://x.com/Rochit_Dubey',
    'Shreyas': 'https://x.com/shreyaskoushik',
    'Rohith': 'https://x.com/rohithkodes',
    'Manik': 'https://x.com/29manik',
    'Melvin': 'https://x.com/SuptMJBrown'
}

for name, x_url in updates.items():
    # Find block starting with <h3>Name...</h3> and ending with <div class="team-social-links">...</div>
    pattern = re.compile(r'(<h3>' + name + r'[^<]*</h3>.*?<div class="team-social-links">)(.*?)</div>', re.DOTALL | re.IGNORECASE)
    
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
print("Updated index.html")
