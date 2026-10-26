import re

simple_banner = """
    <!-- SIMPLE CONTACT BANNER -->
    <section class="simple-contact-banner" style="padding: 4rem 0; background: var(--bg-main);">
        <div class="container">
            <div class="glass-card" style="padding: 3rem 2rem; background: var(--surface); border-radius: 24px; border: 1px solid var(--border-color); text-align: center; box-shadow: var(--shadow-md); max-width: 800px; margin: 0 auto;">
                <h4 style="color: var(--navy); margin-bottom: 1rem; font-size: 1.5rem;">Have questions or need additional information?</h4>
                <p style="color: var(--text-muted); font-size: 1.1rem; margin-bottom: 2rem;">Send us an email at: <a href="mailto:info@tomoclub.org" style="color: var(--teal); text-decoration: none; font-weight: 600;">info@tomoclub.org</a>. Or DM us on our social channels.</p>
                <a href="/contact-us.html" class="btn btn-secondary" style="border-radius: 100px; padding: 0.75rem 2rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.5rem; border: 1px solid var(--teal); color: var(--teal); text-decoration: none; transition: all 0.2s ease;" onmouseover="this.style.background='var(--teal)';this.style.color='#fff';" onmouseout="this.style.background='transparent';this.style.color='var(--teal)';">Contact Us Form &rarr;</a>
            </div>
        </div>
    </section>
"""

# We want to replace the NEWSLETTER & CONTACT SECTION block that I previously added.
files_to_update = ['parents.html', 'tom/parents.html']

for file in files_to_update:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to match the entire section starting with <!-- NEWSLETTER & CONTACT SECTION --> up to the next <!--
        # The section is closed by </section>. Let's match from <!-- NEWSLETTER & CONTACT SECTION --> up to </section>
        pattern = re.compile(r'<!-- NEWSLETTER & CONTACT SECTION -->.*?</section>', re.DOTALL)
        
        if pattern.search(content):
            content = pattern.sub(simple_banner.strip(), content)
            
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Successfully replaced banner in {file}")
        else:
            print(f"Could not find NEWSLETTER & CONTACT SECTION in {file}")
            
    except Exception as e:
        print(f"Error processing {file}: {e}")
