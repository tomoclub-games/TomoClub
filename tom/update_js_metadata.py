import json

new_podcasts = [
    ("4DXGEIsQjFI", "Priya Darbari", "April 24, 2026"),
    ("Y2CXz0cO7Ew", "Dr. Libby Bonesteel", "April 27, 2026"),
    ("DKYbEM1Hmqw", "Chris Mason", "April 28, 2026"),
    ("-amEwzzrmf8", "Christopher Kinney", "April 29, 2026"),
    ("BQTZxLWm8pE", "David A. Garringer", "April 30, 2026"),
    ("SICAlWePP1I", "Derrick Davis", "May 1, 2026"),
    ("T3kkXiTYeFM", "Allwyn Fitzpatrick", "May 4, 2026"),
    ("UmOrxumbVjE", "Aaron Sitze", "May 5, 2026"),
    ("WlqUlrw0sZA", "Dr. Rose Ann Bomentre", "May 6, 2026"),
    ("lslJPs8hxBQ", "Phillip Nowlin", "May 7, 2026"),
    ("4kiwEPBLyeY", "Dr. Michael A. Cardona", "May 8, 2026"),
    ("pDcK0JcHLKs", "Dr. Laura Spencer", "May 10, 2026"),
    ("ZGAGd-nUbxk", "Dr. Jason Hasty", "May 11, 2026"),
    ("OXQvNbMklkU", "Dr. Mark Shanoff", "May 12, 2026"),
    ("Oyu7DcaKCVM", "Rick Johnson", "May 13, 2026"),
    ("pUUxNLOPrK8", "Robert L. Butts", "May 14, 2026"),
    ("V-nR2T6iBTc", "Dr. Marnie Hazelton", "May 15, 2026"),
    ("u0AJJQ5iXSc", "Sam Podbelski", "May 18, 2026"),
    ("2aZPyQnE0e8", "Khushboo Vaidya", "May 19, 2026"),
    ("JNQ6ME7RSnw", "Dr. Meera Viswanathan", "May 20, 2026"),
    ("cur8l7SnLbA", "Michael Berry", "May 21, 2026"),
]

with open('podcast_data.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

json_dict = {item['id']: item for item in json_data}

with open('podcasts_data.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We need to insert before the last `};`
insert_idx = content.rfind('}')

additions = ""
for vid, speaker, date in new_podcasts:
    info = json_dict.get(vid, {})
    title = info.get('title', 'TomoClub Podcast').replace('"', '\\"').replace('\n', ' ')
    duration = info.get('duration', 'TBD')
    additions += f""",
  "{vid}": {{
    "title": "{title}",
    "speaker": "{speaker}",
    "date": "{date}",
    "duration": "{duration}",
    "thumbnail": "https://img.youtube.com/vi/{vid}/maxresdefault.jpg",
    "description": "<p>In this episode of the TomoClub Podcast, host Shreya sits down with {speaker} to explore the realities of leading effectively.</p>"
  }}"""

new_content = content[:insert_idx] + additions + '\n' + content[insert_idx:]

with open('podcasts_data.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated podcasts_data.js!")
