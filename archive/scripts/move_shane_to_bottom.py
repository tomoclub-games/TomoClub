import re

with open('c:/Users/JANMEJAY/Desktop/tom/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The grid starts here
grid_start_str = '<div class="grid-3 animate-on-scroll" id="articles-grid">'
grid_start = content.find(grid_start_str)

grid_end = content.find('</div>\n        </section>\n\n    </div>\n\n    <!-- PAGE: PODCAST -->', grid_start)
if grid_end == -1:
    # Try another way to find the end
    grid_end = content.find('</section>', grid_start)
    grid_end = content.rfind('</div>', grid_start, grid_end)

# We know the Shane Ogden card is the first child of the grid right now.
# Let's extract it.
shane_start = content.find('<a href="articles/shane-ogden-superintendent/"', grid_start)
shane_end = content.find('</a>', shane_start) + 4

shane_card = content[shane_start:shane_end]

# Remove the card from its current position
content = content[:shane_start] + content[shane_end:]

# Recalculate grid_end since we removed something
grid_end -= len(shane_card)

# Insert the card right before the closing </div> of the grid
content = content[:grid_end] + '\n                ' + shane_card + '\n            ' + content[grid_end:]

with open('c:/Users/JANMEJAY/Desktop/tom/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Moved Shane Ogden card to the end of articles-grid.")
