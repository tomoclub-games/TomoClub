import os

old_url = 'https://calendly.com/tomoclub/info-call?month=2026-04'
new_url = 'https://91fabf1c.sibforms.com/v2/serve/MUIFAKeejaVgAe6G18ijnd1U-_b-q5wwqWzAAdp-46T-FSh3yStr_6qw8aeR19UjV40KMRWBGFQErR3NuMTCAmG_-KUhUOYxLU6-Nzza27KOqv33BSKj1pi2yF5sKpquz-KXLYHY8-nnSxH1lt1wkx9dy6n9Yag5Bllp8Grh6x6YnVdT-wVhFN1pgUpqf2R0tY7UuCdnEPrMWXJEiA=='

files_to_check = ['index.html', 'privacy-policy.html', 'terms-and-conditions.html']

for filename in files_to_check:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_url in content:
            print(f'Replacing in {filename}...')
            new_content = content.replace(old_url, new_url)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            print(f'Old URL not found in {filename}')
