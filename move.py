import re
import os

with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

match = re.search(r'(<a href="articles/piper-bognar-van-dyke-leadership/".*?</a>)', c, re.DOTALL)
if match:
    chunk = match.group(1)
    
    # Remove from original position
    # The chunk might have leading/trailing whitespaces, so we replace carefully.
    c = c.replace(chunk, '')
    
    # We want to put it right before the closing div and section
    target = '            </div>\n        </section>\n    </div>\n\n    <!-- PAGE: PODCAST -->'
    c = c.replace(target, chunk + '\n' + target)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(c)
    print("Successfully moved article to the bottom.")
else:
    print("Could not find article chunk.")
