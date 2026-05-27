import urllib.request
import re

url = 'https://www.youtube.com/watch?v=4WQ06l2wCnY'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    title_match = re.search(r'<title>(.*?)</title>', html)
    title = title_match.group(1).replace(' - YouTube', '') if title_match else 'Unknown Title'
    
    date_match = re.search(r'"publishDate":"(.*?)"', html)
    date = date_match.group(1) if date_match else 'Unknown Date'
    
    # Try to find duration
    duration_match = re.search(r'"approxDurationMs":"(\d+)"', html)
    if duration_match:
        ms = int(duration_match.group(1))
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        duration = f"{minutes}:{seconds:02d}"
    else:
        duration = 'Unknown Time'
        
    print(f"Title: {title}")
    print(f"Date: {date}")
    print(f"Duration: {duration}")
except Exception as e:
    print("Error:", e)
