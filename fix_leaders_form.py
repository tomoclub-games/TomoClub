import os

file_path = 'leaders-of-tomorrow/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                        // 1. Submit to Google Sheets (Backup)
                        await fetch(GOOGLE_SHEET_WEBHOOK, {
                            method: 'POST',
                            mode: 'no-cors',
                            body: formData
                        });"""

replacement = """                        // 1. Submit to Centralized API Proxy
                        const data = Object.fromEntries(formData.entries());
                        data.type = (formId === 'bottom-form') ? 'newsletter' : 'ebook_request';
                        
                        await fetch('/api/signup', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(data)
                        });"""

# Try both CRLF and LF
if target in content:
    new_content = content.replace(target, replacement)
elif target.replace('\n', '\r\n') in content:
    new_content = content.replace(target.replace('\n', '\r\n'), replacement.replace('\n', '\r\n'))
else:
    # Fallback to a more flexible regex or partial match if needed
    print("Exact target not found, trying fuzzy match...")
    import re
    # Match the fetch block regardless of exact spacing
    pattern = r'// 1\. Submit to Google Sheets \(Backup\)\s+await fetch\(GOOGLE_SHEET_WEBHOOK, \{\s+method: \'POST\',\s+mode: \'no-cors\',\s+body: formData\s+\}\);'
    new_content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done")
