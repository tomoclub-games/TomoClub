import re
content = open('index.html', encoding='utf-8').read()
urls = re.findall(r'<a href="blog/([^"]+)/"', content)
for i, url in enumerate(urls, 1):
    print(f"{i}. {url}")
