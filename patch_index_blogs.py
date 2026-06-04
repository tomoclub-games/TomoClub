import os

html_path = r"c:\Users\JANMEJAY\Desktop\tom\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Define the HTML blocks for the 3 new blogs
blog_28_html = """
                    <a href="blog/ai-in-k-12-education-opportunities-and-challenges/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;">
                        <div style="background: var(--card-grad-teal); height: 100%; display: flex; flex-direction: column;">
                            <div style="padding: 3rem 2rem 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                                <span style="font-size: 0.85rem; color: var(--teal); font-weight: 600; text-transform: uppercase;">AI Literacy</span>
                                <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;">AI in K–12 Education: Opportunities and Challenges</h3>
                                <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">Artificial Intelligence is revolutionizing education. Discover the opportunities and challenges of implementing AI and SEL in K-12 education.</p>
                                <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                            </div>
                        </div>
                    </a>"""

blog_29_html = """
                    <a href="blog/what-is-social-emotional-learning-sel/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;">
                        <div style="background: var(--card-grad-slate); height: 100%; display: flex; flex-direction: column;">
                            <div style="padding: 3rem 2rem 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                                <span style="font-size: 0.85rem; color: var(--navy); font-weight: 600; text-transform: uppercase;">SEL</span>
                                <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;">What is Social Emotional Learning (SEL)</h3>
                                <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">Discover what Social Emotional Learning is, its benefits, and how it can be implemented practically in schools.</p>
                                <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                            </div>
                        </div>
                    </a>"""

blog_30_html = """
                    <a href="blog/effective-stress-management-techniques-for-educators/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;">
                        <div style="background: var(--card-grad-gold); height: 100%; display: flex; flex-direction: column;">
                            <div style="padding: 3rem 2rem 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                                <span style="font-size: 0.85rem; color: #D97706; font-weight: 600; text-transform: uppercase;">Well-being</span>
                                <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;">Effective Stress Management Techniques for Educators</h3>
                                <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">Discover effective stress management techniques for educators, including mindfulness, time management, and how SEL builds resilience.</p>
                                <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                            </div>
                        </div>
                    </a>"""

# We want to insert these inside the <div class="grid-3"> inside <div id="blog" class="page">
# Let's find: `<div id="blog" class="page">` then the first `<div class="grid-3">`

blog_section_index = content.find('<div id="blog" class="page">')
if blog_section_index == -1:
    print("Could not find blog section")
else:
    grid_index = content.find('<div class="grid-3">', blog_section_index)
    if grid_index == -1:
        print("Could not find grid-3 in blog section")
    else:
        # We want to insert after `<div class="grid-3">`
        insert_pos = grid_index + len('<div class="grid-3">')
        new_content = content[:insert_pos] + blog_30_html + blog_29_html + blog_28_html + content[insert_pos:]
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully updated index.html")
