import json
import re
from datetime import datetime

with open('podcast_data.json', 'r', encoding='utf-8') as f:
    podcasts = json.load(f)

# Build new HTML
html_str = '            <div class="grid-3" id="podcast-grid">\n'
for p in podcasts:
    vid = p['id']
    title = p['title'].replace('&amp;', '&').replace('"', '&quot;')
    date_str = p['date_str']
    duration = p['duration']
    
    # Parse date
    try:
        dt = datetime.fromisoformat(date_str)
        display_date = dt.strftime('%b %d, %Y')
        timestamp = int(dt.timestamp())
    except:
        display_date = 'Unknown Date'
        timestamp = 0
        
    html_str += f'''                <a href="podcast-player.html?id={vid}" class="glass-card podcast-card" data-timestamp="{timestamp}">
                    <div style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 12px; overflow: hidden; margin-bottom: 1rem;">
                        <img src="https://img.youtube.com/vi/{vid}/hqdefault.jpg" alt="{title}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;">
                        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center;">
                            <i data-lucide="play-circle" style="color: white; width: 48px; height: 48px; opacity: 0.8;"></i>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.75rem; color: var(--teal); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                        <span>{display_date}</span>
                        <span>•</span>
                        <span>{duration}</span>
                    </div>
                    <h3 style="font-size: 1.4rem; margin-bottom: 0.75rem;">{title}</h3>
                    <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">Explore deep insights into the future of education and AI literacy.</p>
                    <span class="btn btn-secondary" style="margin-top: auto; padding: 0.6rem 1.2rem; font-size: 0.9rem; align-self: flex-start;">Read More <i data-lucide="arrow-right" style="width: 16px; height: 16px;"></i></span>
                </a>\n'''

html_str += '            </div>'

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the grid
start_str = '<div class="grid-3" id="podcast-grid">'
end_str = '<!-- Call to Action -->'
start_idx = html.find(start_str)
end_idx = html.find(end_str, start_idx)

if start_idx != -1 and end_idx != -1:
    # Notice that the closing </div> of the grid might be just before <!-- Call to Action --> or before the <div class="podcast-load-more-container"> (which is dynamically added).
    # Wait, the podcast grid ends with </div>\n        </section>
    # Let's use regex to replace the whole <div class="grid-3" id="podcast-grid">...</div> block safely
    pass

new_html = re.sub(r'<div class="grid-3" id="podcast-grid">.*?</div>\s*</section>', html_str + '\n        </section>', html, flags=re.DOTALL)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print("Updated index.html")
