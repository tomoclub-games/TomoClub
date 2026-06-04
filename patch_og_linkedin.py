import os
import re

articles_dir = r"c:\Users\JANMEJAY\Desktop\tom\articles"

for folder in os.listdir(articles_dir):
    folder_path = os.path.join(articles_dir, folder)
    if not os.path.isdir(folder_path) or folder == "images":
        continue
    
    index_path = os.path.join(folder_path, "index.html")
    if not os.path.exists(index_path):
        continue

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Append ?v=2 to bust cache
    content = re.sub(
        r'<meta property="og:image" content="([^"]+?)(?:\?v=\d+)?">',
        r'<meta property="og:image" content="\1?v=2">',
        content
    )

    content = re.sub(
        r'<meta name="twitter:image" content="([^"]+?)(?:\?v=\d+)?">',
        r'<meta name="twitter:image" content="\1?v=2">',
        content
    )

    # Add og:url if not exists
    url = f"https://www.tomoclub.org/articles/{folder}/"
    if 'property="og:url"' not in content:
        # Insert after og:type
        content = re.sub(
            r'(<meta property="og:type" content="article">)',
            f'\\1\n    <meta property="og:url" content="{url}">',
            content
        )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Patched {folder}")
