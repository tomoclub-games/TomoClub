import re

files_to_fix = ["parents.html", "tom/parents.html"]

for file in files_to_fix:
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        # I want to extract the NEWSLETTER & CONTACT SECTION and place it AFTER the cta-trials-section.
        newsletter_regex = r'(\s*<!-- NEWSLETTER & CONTACT SECTION -->.*?</section>)'
        newsletter_match = re.search(newsletter_regex, content, re.DOTALL)
        if newsletter_match:
            newsletter_html = newsletter_match.group(1)
            # Remove it from its current position
            content = content.replace(newsletter_html, "")
            
            # Place it right before SECTION 13: FOOTER
            content = content.replace("<!-- SECTION 13: FOOTER", newsletter_html + "\n\n    <!-- SECTION 13: FOOTER")
            
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed {file}")
    except FileNotFoundError:
        pass
