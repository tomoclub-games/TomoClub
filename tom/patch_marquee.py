import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We want to find <div class="testimonial-track">...</div> and multiply its inner content
def replacer(match):
    inner = match.group(1)
    # The inner content currently has 2 sets of cards.
    # Let's double it to 4 sets, which makes the track twice as wide.
    # So 50% translation will be 2 sets instead of 1 set.
    return '<div class="testimonial-track">' + inner + inner + '</div>'

new_html = re.sub(r'<div class="testimonial-track">(.*?)</div>', replacer, html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Patched index.html')
