import urllib.request
import re
import json
from datetime import datetime
import concurrent.futures

# Extract IDs from generate_html.py
ids = []
with open('generate_html.py', 'r', encoding='utf-8') as f:
    content = f.read()
    match = re.search(r'urls = """(.*?)"""', content, re.DOTALL)
    if match:
        urls_str = match.group(1).strip()
        for line in urls_str.split('\n'):
            line = line.strip()
            if not line: continue
            if 'youtu.be/' in line:
                vid = line.split('youtu.be/')[1].split('?')[0]
                if vid not in ids:
                    ids.append(vid)

print(f"Found {len(ids)} unique videos")

def get_video_info(vid):
    url = f'https://www.youtube.com/watch?v={vid}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        title_match = re.search(r'<title>(.*?)</title>', html)
        title = title_match.group(1).replace(' - YouTube', '').strip() if title_match else 'Unknown Title'
        
        date_match = re.search(r'"publishDate":"(.*?)"', html)
        date_str = date_match.group(1) if date_match else '1970-01-01T00:00:00-00:00'
        
        duration_match = re.search(r'"approxDurationMs":"(\d+)"', html)
        if duration_match:
            ms = int(duration_match.group(1))
            minutes = ms // 60000
            seconds = (ms % 60000) // 1000
            duration = f"{minutes}:{seconds:02d}"
        else:
            duration = '0:00'
            
        return {
            'id': vid,
            'title': title,
            'date_str': date_str,
            'duration': duration
        }
    except Exception as e:
        print(f"Error fetching {vid}: {e}")
        return {
            'id': vid,
            'title': 'Unknown Title',
            'date_str': '1970-01-01T00:00:00-00:00',
            'duration': '0:00'
        }

# Fetch concurrently
video_data = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(get_video_info, ids)
    for r in results:
        video_data.append(r)

# Sort by date descending
video_data.sort(key=lambda x: x['date_str'], reverse=True)

with open('podcast_data.json', 'w', encoding='utf-8') as f:
    json.dump(video_data, f, indent=2)

print("Done fetching metadata!")
