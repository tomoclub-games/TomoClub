import os

blogs = [
    {
        "title": "Proven Strategies to Boost Academic Performance in Schools",
        "slug": "proven-strategies-to-boost-academic-performance-in-schools",
        "desc": "Academic performance in present-day competitive environments is the only measure of being successful in institutions of learning."
    },
    {
        "title": "How Integrating SEL into Behavior Management Programs Empowers Student Success",
        "slug": "how-integrating-sel-into-behavior-management-programs-empowers-student-success",
        "desc": "Schools today are no longer just places for math, science, and history but environments where the young minds and hearts develop."
    },
    {
        "title": "How SEL Strengthens Student Relationships",
        "slug": "how-sel-strengthens-student-relationships",
        "desc": "Social-Emotional Learning, or SEL, is much more than a buzzword in today’s education environment. Rather, it is an all-in-one, transformative approach to the growth of students and the school culture itself."
    },
    {
        "title": "Effective Strategies for Behavior Management",
        "slug": "effective-strategies-for-behavior-management",
        "desc": "Behavior management in schools is an extremely crucial component of the learning and personal development environment."
    }
]

html_to_insert = ""
for blog in blogs:
    html_to_insert += f"""
                    <a href="blog/{blog['slug']}/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;">
                        <div style="background: var(--card-grad-gold); height: 100%; display: flex; flex-direction: column;">
                            <div style="padding: 3rem 2rem 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                                <span style="font-size: 0.85rem; color: #D97706; font-weight: 600; text-transform: uppercase;">Education</span>
                                <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;">{blog['title']}</h3>
                                <p style="font-size: 0.95rem; color: var(--text-muted); margin-bottom: 1.5rem; line-height: 1.5;">{blog['desc']}</p>
                                <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                            </div>
                        </div>
                    </a>"""

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '<div class="grid-3">' in line and 'TomoClub Blog' in ''.join(lines[i-10:i]):
        lines.insert(i+1, html_to_insert + "\n")
        break

with open('index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print("Injected into index.html successfully.")
