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
                <a href="blog/{blog['slug']}/" class="glass-card fade-in" style="text-decoration: none; display: flex; flex-direction: column; color: inherit;">
                    <div style="flex: 1;">
                        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                            <span style="background: rgba(42, 180, 184, 0.1); color: var(--teal); padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;">Education</span>
                        </div>
                        <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem; color: var(--navy); line-height: 1.4;">{blog['title']}</h3>
                        <p style="color: var(--text-muted); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">{blog['desc']}</p>
                    </div>
                    <div style="display: flex; align-items: center; color: var(--teal); font-weight: 600; font-size: 0.9rem; margin-top: auto;">
                        Read Article <i data-lucide="arrow-right" style="width: 16px; height: 16px; margin-left: 0.5rem;"></i>
                    </div>
                </a>"""

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

marker = '<div class="grid-3" style="gap: 2rem;">'
insert_pos = content.find(marker)
if insert_pos != -1:
    insert_pos += len(marker)
    new_content = content[:insert_pos] + html_to_insert + content[insert_pos:]
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Injected into index.html successfully.")
else:
    print("Marker not found in index.html")
