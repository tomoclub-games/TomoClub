content = open('articles_data.js', encoding='utf-8').read()
count = content.count('class="glass-card"')
print("Count in articles_data.js:", count)
