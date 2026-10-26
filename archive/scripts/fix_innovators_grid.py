import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find the MEET THE INNOVATORS section
innovators_section_start = html.find('<!-- MEET THE INNOVATORS -->')
advisory_section_start = html.find('<!-- ADVISORY TEAM -->')

if innovators_section_start != -1 and advisory_section_start != -1:
    section = html[innovators_section_start:advisory_section_start]
    
    # 1. Replace the first grid-2 (or grid-3 if already changed) with grid-centered-5
    # Account for potential style attributes
    section = re.sub(r'<div class=\"grid-(2|3)\"[^>]*>', '<div class=\"grid-centered-5\" style=\"margin-bottom: 2rem;\">', section, count=1)
    
    # 2. Remove intermediate closing and opening tags that split the innovators
    # We want one single container for all 4 innovators
    section = re.sub(r'</div>\s*</div>\s*<div class=\"grid-(2|3)\"[^>]*>', '', section)
    
    html = html[:innovators_section_start] + section + html[advisory_section_start:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated Innovators section in index.html to centered grid")
