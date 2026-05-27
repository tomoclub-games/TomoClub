import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('patch_steps.txt', 'r', encoding='utf-8') as f:
    replacement = f.read()

# We want to replace the block starting at <div style="display: flex; flex-direction: column; gap: 0; max-width: 800px; margin: 0 auto;">
# and ending at the closing </div> right before the <!-- End of step 5 --> or the Request a Pilot button.

# Let's find the Exact match block.
start_idx = html.find('<div style="display: flex; flex-direction: column; gap: 0; max-width: 800px; margin: 0 auto;">')
if start_idx != -1:
    end_str = '<div class="text-center" style="margin-top: 4rem;">'
    end_idx = html.find(end_str, start_idx)
    if end_idx != -1:
        new_html = html[:start_idx] + replacement + '\n                ' + html[end_idx:]
        with open('index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        print("Success")
    else:
        print("End string not found")
else:
    print("Start string not found")
