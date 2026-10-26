import re

def search_file(filename, terms):
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        print(f"\n=== {filename} (size: {len(content)}) ===")
        for term in terms:
            matches = [(m.start(), content[max(0,m.start()-80):m.end()+80]) for m in re.finditer(re.escape(term), content, re.IGNORECASE)]
            if matches:
                print(f"\n  [{term}] - {len(matches)} occurrences:")
                for pos, ctx in matches[:3]:
                    print(f"    pos {pos}: ...{ctx}...")
            else:
                print(f"\n  [{term}] - NOT FOUND")
    except Exception as e:
        print(f"Error reading {filename}: {e}")

terms = [
    "Build a Project",
    "8 weeks",
    "Behavioural",
    "Behavioral",
    "AI is All around",
    "AI is all around",
    "80% of parents",
    "50% of schools",
    "Know More",
    "calendly",
    "contact info",
    "X on the footer",
    "x.com/TomoClub",
    "podcast",
    "AI in K12",
    "Game Based Learning",
    "Raising Resilient",
    "Children use Group",
    "Kids use Group",
]

search_file("parents.html", terms)
search_file("index.html", terms)
