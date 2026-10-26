import re

with open('parents.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Look at the quiz section and what 'Build' content is shown in AI lab description
pos = content.find('Children use')
if pos != -1:
    print('Children use at pos:', pos)
    print(content[max(0,pos-200):pos+500])
else:
    print('Children use NOT FOUND')

# Look at the AI sessions section
pos2 = content.find('session-step')
while pos2 != -1:
    ctx = content[pos2:pos2+200]
    if 'AI' in ctx or 'ai' in ctx or 'prompt' in ctx or 'Kid' in ctx or 'real' in ctx:
        print(f'\n--- session-step at {pos2} ---')
        print(ctx)
    pos2 = content.find('session-step', pos2+1)
    if pos2 > 110000:
        break

# Look at CTA panels (trial buttons)
pos3 = content.find('cta-trial-panel')
while pos3 != -1:
    ctx = content[pos3:pos3+2000]
    if 'href' in ctx:
        print(f'\n--- cta-trial-panel at {pos3} ---')
        print(ctx[:2000])
        break
    pos3 = content.find('cta-trial-panel', pos3+1)
