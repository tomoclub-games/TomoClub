import os
import re

link = 'https://91fabf1c.sibforms.com/v2/serve/MUIFAKeejaVgAe6G18ijnd1U-_b-q5wwqWzAAdp-46T-FSh3yStr_6qw8aeR19UjV40KMRWBGFQErR3NuMTCAmG_-KUhUOYxLU6-Nzza27KOqv33BSKj1pi2yF5sKpquz-KXLYHY8-nnSxH1lt1wkx9dy6n9Yag5Bllp8Grh6x6YnVdT-wVhFN1pgUpqf2R0tY7UuCdnEPrMWXJEiA=='

def process_file(filepath):
    print(f"Processing {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    def replace_link(match):
        tag = match.group(0)
        # Replace href
        tag = re.sub(r'href="[^"]+"', 'href="#"', tag)
        # Remove target="_blank"
        tag = re.sub(r'target="_blank"', '', tag)
        # Add class open-pilot-modal
        if 'class="' in tag:
            tag = re.sub(r'class="([^"]*)"', r'class="\1 open-pilot-modal"', tag)
        else:
            tag = tag.replace('<a ', '<a class="open-pilot-modal" ')
        return tag

    new_content = re.sub(rf'<a [^>]*href="{re.escape(link)}"[^>]*>', replace_link, content)

    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes for {filepath}")

process_file('index.html')
