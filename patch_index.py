import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('podcast_html.txt', 'r', encoding='utf-8') as f:
    new_grid = f.read()

# Find the start and end of the grid-3 div inside the podcast section
podcast_start = html.find('id="podcast"')
if podcast_start != -1:
    grid_start = html.find('<div class="grid-3">', podcast_start)
    if grid_start != -1:
        # Find the closing tag of this grid-3 div
        # We assume the grid-3 ends before the next section or the footer
        section_end = html.find('</section>', grid_start)
        # Search backwards for the last </div> before the section ends
        grid_end = html.rfind('</div>', grid_start, section_end) + 6
        
        new_html = html[:grid_start] + new_grid + html[grid_end:]
        
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("Successfully patched index.html")
    else:
        print("Could not find grid-3 in podcast section")
else:
    print("Could not find podcast section")
