import os

articles_dir = r"c:\Users\JANMEJAY\Desktop\tom\articles"
for root, dirs, files in os.walk(articles_dir):
    for file in files:
        if file == "index.html":
            path = os.path.join(root, file)
            print(f"Processing {path}...")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace('../images/', '/articles/images/')
            
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {path}")
            else:
                print(f"No changes for {path}")
