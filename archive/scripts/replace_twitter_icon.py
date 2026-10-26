import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# X logo SVG
x_svg = '<svg width=\"20\" height=\"20\" viewBox=\"0 0 24 24\" fill=\"currentColor\" style=\"display: inline-block; vertical-align: middle;\"><path d=\"M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.134l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z\"/></svg>'

# Find links to x.com and replace the following <i> with SVG
# Pattern: <a href=\"https://x.com/[^\"]*\" target=\"_blank\"><i data-lucide=\"twitter\"></i></a>
pattern = re.compile(r'(<a href=\"https://x.com/[^\"]*\" target=\"_blank\">)<i data-lucide=\"twitter\"></i>(</a>)')

html = pattern.sub(r'\1' + x_svg + r'\2', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Replaced Twitter icons with X symbol")
