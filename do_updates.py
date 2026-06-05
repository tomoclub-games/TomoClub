import re
import glob

# Read index.html footer
with open("index.html", "r", encoding="utf-8") as f:
    index_html = f.read()

footer_match = re.search(r'(<footer>.*?</footer>)', index_html, re.DOTALL)
if footer_match:
    footer_content = footer_match.group(1)
else:
    print("Could not find footer in index.html")
    exit(1)

html_files = glob.glob("*.html") + glob.glob("tom/*.html")

for file in set(html_files):
    if file == "index.html":
        continue
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace footer
    content = re.sub(r'<footer>.*?</footer>', footer_content, content, flags=re.DOTALL)
    
    # If this is parents.html (or tom/parents.html), also do the other changes
    if "parents.html" in file:
        newsletter_banner = """
    <!-- NEWSLETTER & CONTACT SECTION -->
    <section style="padding: 6rem 0; background: var(--bg-main);">
        <div class="container">
            <div class="glass-card animate-on-scroll" style="padding: 5rem 3rem; background: var(--card-grad-slate); border-radius: 48px; border: 1px solid var(--border-color); display: flex; flex-direction: column; align-items: center; text-align: center; position: relative; overflow: hidden; box-shadow: var(--shadow-2xl);">
                <!-- Decorative background elements -->
                <div style="position: absolute; top: -100px; right: -100px; width: 300px; height: 300px; background: radial-gradient(circle, rgba(42, 180, 184, 0.15) 0%, transparent 70%); border-radius: 50%;"></div>
                <div style="position: absolute; bottom: -50px; left: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(179, 65, 88, 0.08) 0%, transparent 70%); border-radius: 50%;"></div>
                
                <div style="max-width: 700px; position: relative; z-index: 1;">
                    <span class="badge" style="margin-bottom: 1.5rem; background: rgba(42, 180, 184, 0.1); color: var(--teal);">Weekly Insights</span>
                    <h2 style="font-size: clamp(2.5rem, 5vw, 3.5rem); line-height: 1.1; margin-bottom: 1.5rem; color: var(--navy);">Stay ahead of the <span class="text-gradient">AI curve.</span></h2>
                    <p style="font-size: 1.25rem; color: var(--text-muted); margin-bottom: 3rem; line-height: 1.6;">Parenting tips, AI literacy updates, and classroom insights delivered every Sunday. Join 2,500+ parents and educators.</p>
                    
                    <form id="parents-newsletter-form-bottom" class="newsletter-form" onsubmit="handleParentsNewsletter(event)" style="display: flex; gap: 1rem; width: 100%; max-width: 550px; margin: 0 auto; flex-wrap: wrap; background: var(--surface); padding: 0.5rem; border-radius: 20px; border: 1px solid var(--border-color); box-shadow: var(--shadow-lg);">
                        <input type="email" name="email" placeholder="Enter your email address" required 
                            style="flex: 1; min-width: 250px; padding: 1rem 1.5rem; border-radius: 16px; border: none; background: transparent; color: var(--text-main); font-size: 1.1rem; outline: none;">
                        <button type="submit" class="btn btn-primary" style="padding: 1rem 2.5rem; border-radius: 16px; font-weight: 700; display: flex; align-items: center; gap: 0.75rem; box-shadow: var(--shadow-md);">
                            Subscribe <i data-lucide="send" style="width: 20px; height: 20px;"></i>
                        </button>
                    </form>
                    
                    <div id="parents-newsletter-success-bottom" style="display: none; margin-top: 2rem; padding: 2rem; background: rgba(42, 180, 184, 0.05); border-radius: 24px; border: 1px solid rgba(42, 180, 184, 0.2);">
                        <div style="width: 56px; height: 56px; background: var(--teal); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;">
                            <i data-lucide="check" style="width: 28px; height: 28px;"></i>
                        </div>
                        <h4 style="color: var(--navy); margin-bottom: 0.5rem; font-size: 1.5rem;">Welcome!</h4>
                        <p style="color: var(--text-muted);">Check your inbox for our latest edition.</p>
                    </div>

                    <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid rgba(0,0,0,0.1);">
                        <h4 style="color: var(--navy); margin-bottom: 0.5rem; font-size: 1.25rem;">Have questions or need additional information?</h4>
                        <p style="color: var(--text-muted); font-size: 1rem; margin-bottom: 1rem;">Send us an email at: <a href="mailto:info@tomoclub.org" style="color: var(--teal); text-decoration: none; font-weight: 600;">info@tomoclub.org</a>. Or DM us on our social channels.</p>
                        <a href="/contact-us.html" class="btn btn-secondary" style="border-radius: 100px; padding: 0.5rem 1.5rem;">Contact Us Form &rarr;</a>
                    </div>
                </div>
            </div>
        </div>
    </section>
"""
        
        # Replace the old cta-contact-row with the new banner
        # Specifically matching the exact block from parents.html
        contact_row_regex = r'<div class="cta-contact-row">.*?</div>'
        content = re.sub(contact_row_regex, newsletter_banner, content, flags=re.DOTALL)
        
        # We also want to remove the old newsletter section from parents.html so there's not 2 of them.
        old_newsletter_regex = r'<!-- NEWSLETTER SUBSCRIPTION SECTION -->\s*<section.*?<!-- READ BLOGS \+ PODCAST SECTION -->'
        content = re.sub(old_newsletter_regex, '<!-- READ BLOGS + PODCAST SECTION -->', content, flags=re.DOTALL)

    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Successfully applied changes.")
