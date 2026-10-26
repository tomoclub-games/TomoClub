import json
import os
import re
from datetime import datetime

with open('podcast_data.json', 'r', encoding='utf-8') as f:
    podcasts = json.load(f)

count = 0
for p in podcasts:
    vid = p['id']
    title = p['title'].replace('&amp;', '&')
    title_escaped = title.replace('"', '&quot;')
    date_str = p['date_str']
    duration = p['duration']
    
    try:
        dt = datetime.fromisoformat(date_str)
        display_date = dt.strftime('%B %d, %Y')
    except:
        display_date = 'Unknown Date'
        
    filepath = f"podcast-{vid}.html"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        content = re.sub(
            r'<i data-lucide="calendar"></i> <strong>Date:</strong> <span>.*?</span>',
            f'<i data-lucide="calendar"></i> <strong>Date:</strong> <span>{display_date}</span>',
            content
        )
        
        content = re.sub(
            r'<i data-lucide="clock"></i> <strong>Duration:</strong> <span>.*?</span>',
            f'<i data-lucide="clock"></i> <strong>Duration:</strong> <span>{duration}</span>',
            content
        )
        
        content = re.sub(
            r'<h1 class="episode-title">.*?</h1>',
            f'<h1 class="episode-title">{title_escaped}</h1>',
            content
        )
        
        content = re.sub(
            r'<title>.*?</title>',
            f'<title>{title_escaped} | TomoClub Podcast</title>',
            content
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        count += 1

print(f"Updated {count} podcast pages.")
