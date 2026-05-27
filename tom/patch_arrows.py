import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# The target is: <i data-lucide="chevron-down" style="position: absolute; bottom: -14px; left: -13px; color: var(--teal); width: 24px; height: 24px;"></i>
# We'll replace it with: <i data-lucide="chevron-down" class="timeline-arrow" style="position: absolute; bottom: -14px; left: -13px; color: var(--teal); width: 24px; height: 24px;"></i>

old_str = '<i data-lucide="chevron-down" style="position: absolute; bottom: -14px; left: -13px; color: var(--teal); width: 24px; height: 24px;"></i>'
new_str = '<i data-lucide="chevron-down" class="timeline-arrow" style="position: absolute; bottom: -14px; left: -13px; color: var(--teal); width: 24px; height: 24px;"></i>'

new_html = html.replace(old_str, new_str)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Replaced", html.count(old_str), "instances.")
