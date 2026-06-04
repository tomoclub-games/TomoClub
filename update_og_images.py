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

    # Find the article cover image
    match = re.search(r'<img\s+src="([^"]+)"[^>]*class="article-cover"', content)
    if match:
        img_src = match.group(1)
        # img_src is something like "../../articles/images/article-7-amanda.png"
        # We want to convert it to "https://www.tomoclub.org/articles/images/article-7-amanda.png"
        
        # Extract the part starting with 'articles/images/'
        img_name = img_src.split("articles/images/")[-1]
        new_url = f"https://www.tomoclub.org/articles/images/{img_name}"

        # Replace og:image
        content = re.sub(
            r'<meta property="og:image" content="[^"]+">',
            f'<meta property="og:image" content="{new_url}">',
            content
        )

        # Replace twitter:image
        content = re.sub(
            r'<meta name="twitter:image" content="[^"]+">',
            f'<meta name="twitter:image" content="{new_url}">',
            content
        )

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {folder} to {new_url}")
    else:
        print(f"No cover image found for {folder}")
