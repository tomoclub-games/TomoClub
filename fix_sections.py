content = open('index.html', encoding='utf-8').read()

# Fix IEM table - the colgroup is there but cells still lack padding on data cells
# Replace old data cells (td without padding) with padded ones
import re

# Fix th padding lines that are broken
content = content.replace(
    '<th style="padding: 0.75rem 1rem 0.75rem 0;">Competency</th>',
    '<th style="padding:0.75rem 1rem 0.75rem 0;font-weight:700;">Competency</th>'
)
content = content.replace(
    '<th style="padding: 0.75rem 1rem;">First Session</th>',
    '<th style="padding:0.75rem 1rem;font-weight:700;">First Session</th>'
)
content = content.replace(
    '<th style="padding: 0.75rem 1rem;">Last Session</th>',
    '<th style="padding:0.75rem 1rem;font-weight:700;">Last Session</th>'
)
content = content.replace(
    '<th style="padding: 0.75rem 0 0.75rem 1rem; color: var(--teal);">% Growth</th>',
    '<th style="padding:0.75rem 0 0.75rem 1rem;font-weight:700;color:var(--teal);">% Growth</th>'
)

# Fix the data cells - add explicit padding to td elements that are missing it
content = content.replace(
    '<td style="padding: 0.85rem 1rem 0.85rem 0; font-weight: 600;">Leadership</td>',
    '<td style="padding:0.85rem 1.5rem 0.85rem 0;font-weight:600;">Leadership</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">2.24 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">2.24 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">4.05 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">4.05 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 0 0.85rem 1rem; font-weight: 700; color: var(--teal);">+81%</td>\n                                </tr>\n                                <tr style="border-bottom: 1px solid var(--border-color);">',
    '<td style="padding:0.85rem 0 0.85rem 1.5rem;font-weight:700;color:var(--teal);">+81%</td>\n                                </tr>\n                                <tr style="border-bottom: 1px solid var(--border-color);">'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem 0.85rem 0; font-weight: 600;">Innovation</td>',
    '<td style="padding:0.85rem 1.5rem 0.85rem 0;font-weight:600;">Innovation</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">2.32 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">2.32 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">4.19 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">4.19 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 0 0.85rem 1rem; font-weight: 700; color: var(--teal);">+81%</td>\n                                </tr>\n                                <tr>',
    '<td style="padding:0.85rem 0 0.85rem 1.5rem;font-weight:700;color:var(--teal);">+81%</td>\n                                </tr>\n                                <tr>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem 0.85rem 0; font-weight: 600;">Emotional Intelligence</td>',
    '<td style="padding:0.85rem 1.5rem 0.85rem 0;font-weight:600;">Emotional Intelligence</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">2.34 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">2.34 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 1rem;">4.22 / 5</td>',
    '<td style="padding:0.85rem 1.5rem;">4.22 / 5</td>'
)
content = content.replace(
    '<td style="padding: 0.85rem 0 0.85rem 1rem; font-weight: 700; color: var(--teal);">+80%</td>',
    '<td style="padding:0.85rem 0 0.85rem 1.5rem;font-weight:700;color:var(--teal);">+80%</td>'
)

open('index.html', 'w', encoding='utf-8').write(content)
print("Done - table cells padded")
