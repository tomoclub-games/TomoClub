with open('index.html', encoding='utf-8') as f:
    c = f.read()
import re

# Find all track classes
tracks = re.findall(r'<div class="testimonial-track[^"]*"', c)
print('Tracks:')
for t in tracks:
    print(' ', t)

# Count total testimonial-cards
total = c.count('class="testimonial-card"')
print(f'\nTotal testimonial-card elements: {total}')
