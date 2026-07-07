"""
Add a single new podcast episode to the TomoClub site.

Usage:
    python add_podcast_episode.py --url "https://youtu.be/VIDEO_ID?si=..." --speaker "Full Name" --date "Month DD, YYYY"

What it does (all steps are duplicate-safe / idempotent -- safe to re-run):
    1. Fetches the real title + duration for JUST this one video from YouTube
       (does NOT re-fetch the whole back-catalog -- avoids 429 rate limits).
    2. Adds the entry to podcasts_data.js (used by podcast-player.html).
    3. Adds/updates the entry in podcast_data.json (the metadata cache).
    4. Appends the URL to generate_html.py's `urls` list (historical record).
    5. Appends the tuple to update_js_metadata.py's `new_podcasts` list (historical record).
    6. Inserts a new card at the TOP of the #podcast-grid in index.html, using
       the exact same template as the live cards (not the generic placeholder
       template that generate_html.py produces).

It deliberately does NOT run fetch_podcasts.py or generate_html.py's grid
rebuild -- that pipeline re-fetches all ~100 videos (triggers YouTube rate
limiting) and its naive regex-based grid replacement has been observed to
duplicate the entire grid instead of cleanly replacing it. This script
does targeted, minimal-diff text surgery instead.
"""

import argparse
import datetime
import json
import re
import sys
import time
import urllib.request


def extract_video_id(url: str) -> str:
    m = re.search(r'youtu\.be/([^?&]+)|[?&]v=([^&]+)', url)
    if not m:
        raise ValueError(f"Could not extract a video ID from URL: {url}")
    return m.group(1) or m.group(2)


def fetch_video_metadata(vid: str, retries: int = 3) -> dict:
    url = f'https://www.youtube.com/watch?v={vid}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(retries):
        try:
            html = urllib.request.urlopen(req).read().decode('utf-8')
            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1).replace(' - YouTube', '').strip() if title_match else 'Unknown Title'
            # Normalize bare '&' to '&amp;' without double-escaping existing entities
            title = re.sub(r'&(?!amp;|#\d+;|[a-zA-Z]+;)', '&amp;', title)

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

            return {'id': vid, 'title': title, 'date_str': date_str, 'duration': duration}
        except Exception as e:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  Fetch attempt {attempt + 1} failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Warning: could not fetch metadata for {vid}: {e}")
                return {'id': vid, 'title': 'TomoClub Podcast', 'date_str': '1970-01-01T00:00:00-00:00', 'duration': 'TBD'}


def update_podcasts_data_js(vid, title, speaker, date_display, duration):
    path = 'podcasts_data.js'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if re.search(r'"' + re.escape(vid) + r'":\s*\{', content):
        print(f"  podcasts_data.js already has an entry for {vid}, skipping.")
        return

    entry = f'''  "{vid}": {{
    "title": "{title}",
    "speaker": "{speaker}",
    "date": "{date_display}",
    "duration": "{duration}",
    "thumbnail": "https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
    "description": "<p>In this episode of the TomoClub Podcast, host Shreya sits down with {speaker} to explore the realities of leading effectively.</p>"
  }},
'''
    marker = "const podcastsData = {\n"
    idx = content.index(marker) + len(marker)
    content = content[:idx] + entry + content[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Added {vid} to podcasts_data.js")


def update_podcast_data_json(vid, title, date_str, duration):
    path = 'podcast_data.json'
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    data = [d for d in data if d['id'] != vid]
    data.append({'id': vid, 'title': title, 'date_str': date_str, 'duration': duration})
    data.sort(key=lambda x: x['date_str'], reverse=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"  Updated podcast_data.json ({len(data)} total entries)")


def update_generate_html_py(url, vid):
    path = 'generate_html.py'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if vid in content:
        print(f"  generate_html.py already references {vid}, skipping.")
        return content_unchanged(path)

    marker = '"""'
    end_idx = content.rindex(marker)
    content = content[:end_idx] + url + '\n' + content[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Appended URL to generate_html.py")


def content_unchanged(path):
    return None


def update_js_metadata_py(vid, speaker, date_display):
    path = 'update_js_metadata.py'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'"{vid}"' in content:
        print(f"  update_js_metadata.py already references {vid}, skipping.")
        return

    marker = "new_podcasts = [\n"
    idx = content.index(marker) + len(marker)
    line = f'    ("{vid}", "{speaker}", "{date_display}"),\n'
    content = content[:idx] + line + content[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Appended tuple to update_js_metadata.py")


def update_index_html(vid, title, date_abbrev, duration, timestamp):
    path = 'index.html'
    with open(path, encoding='utf-8') as f:
        content = f.read()

    if f'id={vid}"' in content:
        print(f"  index.html already has a card for {vid}, skipping.")
        return

    card = f'''                <a href="podcast-player.html?id={vid}" class="glass-card podcast-card" data-timestamp="{timestamp}">
                    <div style="position: relative; width: 100%; padding-top: 56.25%; border-radius: 12px; overflow: hidden; margin-bottom: 1rem;">
                        <img src="https://img.youtube.com/vi/{vid}/hqdefault.jpg" alt="{title}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;">
                        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center;">
                            <i data-lucide="play-circle" style="color: white; width: 48px; height: 48px; opacity: 0.8;"></i>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.75rem; color: var(--teal); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">
                        <span>{date_abbrev}</span>
                        <span>•</span>
                        <span>{duration}</span>
                    </div>
                    <h3 style="font-size: 1.4rem; margin-bottom: 0.75rem;">{title}</h3>
                    <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">Explore deep insights into the future of education and AI literacy.</p>
                    <span class="btn btn-secondary" style="margin-top: auto; padding: 0.6rem 1.2rem; font-size: 0.9rem; align-self: flex-start;">Read More <i data-lucide="arrow-right" style="width: 16px; height: 16px;"></i></span>
                </a>
'''
    marker = '<div class="grid-3" id="podcast-grid">\n'
    idx = content.index(marker) + len(marker)
    content = content[:idx] + card + content[idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("  Inserted new card at top of index.html podcast grid")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--url', required=True, help='YouTube URL, e.g. https://youtu.be/VIDEO_ID?si=...')
    parser.add_argument('--speaker', required=True, help='Guest/speaker name')
    parser.add_argument('--date', required=True, help='Release date, e.g. "July 26, 2026"')
    args = parser.parse_args()

    vid = extract_video_id(args.url)
    print(f"Video ID: {vid}")

    try:
        release_dt = datetime.datetime.strptime(args.date, "%B %d, %Y")
    except ValueError:
        print(f"Could not parse --date '{args.date}'. Expected format: 'Month DD, YYYY' (e.g. 'July 26, 2026')")
        sys.exit(1)

    date_display_full = release_dt.strftime("%B %d, %Y")
    date_display_abbrev = release_dt.strftime("%b %d, %Y")
    timestamp = int(datetime.datetime(
        release_dt.year, release_dt.month, release_dt.day, 14, 30, 0,
        tzinfo=datetime.timezone.utc
    ).timestamp())

    print("Fetching video metadata from YouTube (single video only)...")
    meta = fetch_video_metadata(vid)
    title = meta['title']
    duration = meta['duration']
    print(f"  Title: {title}")
    print(f"  Duration: {duration}")

    print("\nUpdating files...")
    update_podcasts_data_js(vid, title, args.speaker, date_display_full, duration)
    update_podcast_data_json(vid, title, meta['date_str'], duration)
    update_generate_html_py(args.url, vid)
    update_js_metadata_py(vid, args.speaker, date_display_full)
    update_index_html(vid, title, date_display_abbrev, duration, timestamp)

    print("\nDone. Review with: git diff --stat")
    print("Then preview locally before committing.")


if __name__ == '__main__':
    main()
