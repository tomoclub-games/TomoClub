import re

def make_parents_changes():
    with open('parents.html', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    changes = []
    
    # =====================================================
    # 1. Hero Section: Add "Know More" secondary CTA
    # =====================================================
    old_hero_btns = '''<div class="hero-cta-buttons">
                <a href="#quiz" class="btn-parents-primary" onclick="scrollToQuiz(event)">Which program fits my child? &rarr;</a>
                <a href="#programs" class="btn-parents-ghost" onclick="scrollToPrograms(event)">Book free trial</a>
            </div>'''
    new_hero_btns = '''<div class="hero-cta-buttons">
                <a href="#quiz" class="btn-parents-primary" onclick="scrollToQuiz(event)">Which program fits my child? &rarr;</a>
                <a href="#programs" class="btn-parents-ghost" onclick="scrollToPrograms(event)">Book free trial</a>
                <a href="#programs" class="btn-parents-ghost" onclick="scrollToPrograms(event)">Know More</a>
            </div>'''
    
    if old_hero_btns in content:
        content = content.replace(old_hero_btns, new_hero_btns)
        changes.append("Added 'Know More' secondary CTA to hero section")
    
    # =====================================================
    # 2. Stat cards: "Fewer behaviour issues" -> "80% increase in student competency (Leadership, EI)"
    # =====================================================
    old_stat = '''<div class="label">Fewer behaviour issues</div>'''
    new_stat = '''<div class="label">Increase in student competency (Leadership, EI)</div>'''
    
    if old_stat in content:
        content = content.replace(old_stat, new_stat)
        changes.append("Updated stat card: behaviour issues -> student competency")

    # =====================================================
    # 3. Why Now stats: Update "80% of parents are worried..." to "are uncertain about what skills matter in the future"
    # =====================================================
    old_why_stat1 = 'are worried about safe classroom AI integration'
    new_why_stat1 = 'are uncertain about what skills matter in the future'
    
    if old_why_stat1 in content:
        content = content.replace(old_why_stat1, new_why_stat1)
        changes.append("Updated 80% of parents stat text")
    
    # =====================================================
    # 4. Why Now stats: Update "50% of schools" description
    # =====================================================
    old_why_stat2 = "teach no computer science or digital safety curricula"
    new_why_stat2 = "don't teach digital and cyber safety"
    
    if old_why_stat2 in content:
        content = content.replace(old_why_stat2, new_why_stat2)
        changes.append("Updated 50% of schools stat text")
    
    # =====================================================
    # 5. Why Now AI section heading: "AI is All around us"
    # =====================================================
    old_why_heading = '''<h3>AI is in your child's school. Are they ready to question it?</h3>'''
    new_why_heading = '''<h3>AI is All around us</h3>'''
    
    if old_why_heading in content:
        content = content.replace(old_why_heading, new_why_heading)
        changes.append("Updated Why Now AI heading to 'AI is All around us'")
    
    # =====================================================
    # 6. AI Lab session description: "Kids prompt real AI tools" -> "Children use Group activities, games and prompt real AI tools to understand how AI works"
    # =====================================================
    old_ai_desc = 'Kids prompt real AI tools, test limits, compare outputs. Hands-on.'
    new_ai_desc = 'Children use Group activities, games and prompt real AI tools to understand how AI works.'
    
    if old_ai_desc in content:
        content = content.replace(old_ai_desc, new_ai_desc)
        changes.append("Updated AI Lab description")
    
    # =====================================================
    # 7. Replace Kid/Kids with Child/Children throughout
    # =====================================================
    kid_replacements = [
        ("Quiet kids grow the fastest here.", "Quiet children grow the fastest here."),
        ("Same 8 kids every session", "Same 8 children every session"),
        ("One real dilemma. Kids argue, vote, defend. Coach facilitates.", "One real dilemma. Children argue, vote, defend. Coach facilitates."),
        ("Multiplayer team challenge. Kids reveal more in games than classrooms.", "Multiplayer team challenge. Children reveal more in games than classrooms."),
        ("Game &rarr; real life. Kids name their own patterns out loud.", "Game &rarr; real life. Children name their own patterns out loud."),
        ("We teach kids how to *question* and *direct* AI", "We teach children how to *question* and *direct* AI"),
        ("Research-backed insights on raising future-ready kids in an AI-first world.", "Research-backed insights on raising future-ready children in an AI-first world."),
        ("Raising Resilient Kids in an AI-Driven World", "Raising Resilient Children in an AI-Driven World"),
    ]
    
    for old_text, new_text in kid_replacements:
        if old_text in content:
            content = content.replace(old_text, new_text)
            changes.append(f"Replaced Kid/Kids: '{old_text[:50]}...'")
    
    # =====================================================
    # 8. Podcast episode links
    # =====================================================
    # AI in K12 podcast
    old_ai_k12 = 'AI in K&ndash;12: What Parents Need to Know'
    if old_ai_k12 in content:
        idx = content.find(old_ai_k12)
        a_start = content.rfind('<a href=', 0, idx)
        a_href_end = content.find('>', a_start) + 1
        new_a_tag = '<a href="https://www.youtube.com/watch?v=gUJKauNF7Kc" target="_blank" rel="noopener noreferrer" style="display:flex;gap:1rem;align-items:flex-start;padding:1.25rem;background:var(--surface);border:1px solid var(--border-color);border-radius:12px;text-decoration:none;transition:transform 0.2s ease,box-shadow 0.2s ease;" onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 8px 24px rgba(0,0,0,0.1)\';" onmouseout="this.style.transform=\'none\';this.style.boxShadow=\'none\';">'
        content = content[:a_start] + new_a_tag + content[a_href_end:]
        changes.append("Updated AI in K12 podcast link to specific YouTube video")
    
    # Game-Based Learning podcast
    old_gbl = 'Game-Based Learning: Why It Works for Every Child'
    if old_gbl in content:
        idx = content.find(old_gbl)
        a_start = content.rfind('<a href=', 0, idx)
        a_href_end = content.find('>', a_start) + 1
        new_a_tag = '<a href="https://www.youtube.com/watch?v=XW77-D37Jng" target="_blank" rel="noopener noreferrer" style="display:flex;gap:1rem;align-items:flex-start;padding:1.25rem;background:var(--surface);border:1px solid var(--border-color);border-radius:12px;text-decoration:none;transition:transform 0.2s ease,box-shadow 0.2s ease;" onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 8px 24px rgba(0,0,0,0.1)\';" onmouseout="this.style.transform=\'none\';this.style.boxShadow=\'none\';">'
        content = content[:a_start] + new_a_tag + content[a_href_end:]
        changes.append("Updated Game-Based Learning podcast link to specific YouTube video")
    
    # Raising Resilient Kids/Children podcast
    old_rrk_kids = 'Raising Resilient Children in an AI-Driven World'
    if old_rrk_kids in content:
        idx = content.find(old_rrk_kids)
        a_start = content.rfind('<a href=', 0, idx)
        a_href_end = content.find('>', a_start) + 1
        new_a_tag = '<a href="https://www.youtube.com/watch?v=TfHPHYLwehE" target="_blank" rel="noopener noreferrer" style="display:flex;gap:1rem;align-items:flex-start;padding:1.25rem;background:var(--surface);border:1px solid var(--border-color);border-radius:12px;text-decoration:none;transition:transform 0.2s ease,box-shadow 0.2s ease;" onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 8px 24px rgba(0,0,0,0.1)\';" onmouseout="this.style.transform=\'none\';this.style.boxShadow=\'none\';">'
        content = content[:a_start] + new_a_tag + content[a_href_end:]
        changes.append("Updated Raising Resilient Kids podcast link")
    
    # =====================================================
    # 9. Calendly links
    # =====================================================
    old_ai_trial_href = 'href="mailto:info@tomoclub.com?subject=Free%20trial%20%E2%80%94%20Tomo%20AI%20Lab'
    if old_ai_trial_href in content:
        idx = content.find(old_ai_trial_href)
        a_start = content.rfind('<a ', 0, idx)
        a_end = content.find('>', a_start) + 1
        old_a = content[a_start:a_end]
        new_a = re.sub(r'href="[^"]*"', 'href="https://calendly.com/tomoclubdemo/tomo-ai-lab-trial" target="_blank" rel="noopener noreferrer"', old_a)
        content = content[:a_start] + new_a + content[a_end:]
        changes.append("Updated AI Lab trial button to Calendly link")
    
    old_skills_trial_href = 'href="mailto:info@tomoclub.com?subject=Book%20a%20Free%20Trial%20%E2%80%94%20Tomo%20Life%20Skills'
    if old_skills_trial_href in content:
        idx = content.find(old_skills_trial_href)
        a_start = content.rfind('<a ', 0, idx)
        a_end = content.find('>', a_start) + 1
        old_a = content[a_start:a_end]
        new_a = re.sub(r'href="[^"]*"', 'href="https://calendly.com/tomoclubdemo/life-skills" target="_blank" rel="noopener noreferrer"', old_a)
        content = content[:a_start] + new_a + content[a_end:]
        changes.append("Updated Life Skills trial button to Calendly link")
    
    # =====================================================
    # 10. Footer X link
    # =====================================================
    old_social_links = '''<a href="https://www.linkedin.com/company/tomoclub/" target="_blank" rel="noopener noreferrer" title="LinkedIn"><i data-lucide="linkedin"></i></a>
                    </div>'''
    new_social_links = '''<a href="https://www.linkedin.com/company/tomoclub/" target="_blank" rel="noopener noreferrer" title="LinkedIn"><i data-lucide="linkedin"></i></a>
                        <a href="https://x.com/TomoClub_edu" target="_blank" rel="noopener noreferrer" title="X (Twitter)"><i data-lucide="twitter"></i></a>
                    </div>'''
    if old_social_links in content:
        content = content.replace(old_social_links, new_social_links)
        changes.append("Added X (Twitter) link to footer social links")
    
    # =====================================================
    # 11. Footer Banner
    # =====================================================
    old_contact_section = '''<div class="footer-links">
                    <h4>Contact Us</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; font-size: 0.9rem;">
                            <i data-lucide="phone" style="width: 18px; color: var(--teal); flex-shrink: 0;"></i>
                            <div>
                                <span style="display: block; font-weight: 700; color: var(--navy);">Call Us</span>
                                <a href="tel:+16505478082" style="color: var(--text-muted);">+1 650 547-8082</a>
                            </div>
                        </li>
                        <li style="display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; font-size: 0.9rem;">
                            <i data-lucide="mail" style="width: 18px; color: var(--teal); flex-shrink: 0;"></i>
                            <div>
                                <a href="mailto:info@tomoclub.org" style="color: var(--text-muted);">info@tomoclub.org</a>
                            </div>
                        </li>
                    </ul>
                </div>'''
    new_contact_section = '''<div class="footer-links">
                    <h4>Contact Us</h4>
                    <p style="font-size: 0.9rem; line-height: 1.6; margin-bottom: 1rem;">Have questions or need additional information?</p>
                    <p style="font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.75rem;">Send us an email at: <a href="mailto:info@tomoclub.org" style="color: var(--teal);">info@tomoclub.org</a>. Or DM us on our social channels.</p>
                    <a href="/contact-us.html" style="display: inline-flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; font-weight: 600; color: var(--teal); text-decoration: none; border: 1px solid var(--teal); border-radius: 100px; padding: 6px 16px; transition: all 0.2s ease;" onmouseover="this.style.background='var(--teal)';this.style.color='#fff';" onmouseout="this.style.background='transparent';this.style.color='var(--teal)';">Contact Us Form &rarr;</a>
                </div>'''
    if old_contact_section in content:
        content = content.replace(old_contact_section, new_contact_section)
        changes.append("Updated footer contact section to banner with email and contact form link")
        
    # =====================================================
    # 13. "Build a real project every term" -> "Build a Project within 8 weeks"
    # =====================================================
    old_build = 'Build a real project every term'
    new_build = 'Build a Project within 8 weeks'
    if old_build in content:
        content = content.replace(old_build, new_build)
        changes.append("Updated 'Build a real project every term' to 'Build a Project within 8 weeks'")
        
    # =====================================================
    # 14. "85% fewer behaviour referrals" -> "80% increase in student competency"
    # =====================================================
    old_proof_stat = '<span class="num">85%</span>\n                            <span class="label">Fewer behaviour referrals in schools running the program</span>'
    new_proof_stat = '<span class="num">80%</span>\n                            <span class="label">Increase in student competency (Leadership, EI)</span>'
    if old_proof_stat in content:
        content = content.replace(old_proof_stat, new_proof_stat)
        changes.append("Updated proof stat: 85% fewer behaviour -> 80% increase in student competency")

    # =====================================================
    # 15. Mobile Footer Alignment CSS
    # =====================================================
    old_mobile_footer = '''@media (max-width: 768px) {
            footer .footer-grid {
                grid-template-columns: 1fr 1fr !important;
            }'''
    if old_mobile_footer in content:
        new_mobile_footer = '''@media (max-width: 768px) {
            footer .footer-grid {
                grid-template-columns: 1fr !important;
                text-align: center !important;
            }
            footer .social-links {
                justify-content: center !important;
            }'''
        content = content.replace(old_mobile_footer, new_mobile_footer)
        changes.append("Updated mobile footer to center alignment")

    # =====================================================
    # 16. MAKE TRUST BAR INTO CARDS (New Change)
    # =====================================================
    old_trust_row = '''<div class="trust-stats-row">
                <div class="trust-stat-item">
                    <div class="num stat-count" data-target="10000" data-comma="true" data-suffix="+">0+</div>
                    <div class="label">students reached</div>
                </div>
                <div class="trust-stat-item">
                    <div class="num stat-count" data-target="97" data-suffix="%">0%</div>
                    <div class="label">engagement rate</div>
                </div>
                <div class="trust-stat-item">
                    <div class="num stat-count" data-target="92" data-suffix="%">0%</div>
                    <div class="label">AI confidence increase</div>
                </div>
                <div class="trust-stat-item">
                    <div class="num stat-count" data-target="100" data-suffix="%">0%</div>
                    <div class="label">skills applied in 3 months</div>
                </div>
            </div>'''
            
    new_trust_row = '''<div class="stat-cards-grid">
                <div class="parent-stat-card">
                    <div class="stat-card-stripe" style="background-color: var(--brand-cyan);"></div>
                    <div class="num stat-count" data-target="10000" data-comma="true" data-suffix="+">0+</div>
                    <div class="label">students reached</div>
                </div>
                <div class="parent-stat-card">
                    <div class="stat-card-stripe" style="background-color: var(--brand-yellow);"></div>
                    <div class="num stat-count" data-target="97" data-suffix="%">0%</div>
                    <div class="label">engagement rate</div>
                </div>
                <div class="parent-stat-card">
                    <div class="stat-card-stripe" style="background-color: var(--brand-rose);"></div>
                    <div class="num stat-count" data-target="92" data-suffix="%">0%</div>
                    <div class="label">AI confidence increase</div>
                </div>
                <div class="parent-stat-card">
                    <div class="stat-card-stripe" style="background-color: var(--brand-cyan-dark);"></div>
                    <div class="num stat-count" data-target="100" data-suffix="%">0%</div>
                    <div class="label">skills applied in 3 months</div>
                </div>
            </div>'''
            
    if old_trust_row in content:
        content = content.replace(old_trust_row, new_trust_row)
        changes.append("Transformed trust stats into cards (theme of Tomoclub)")
    else:
        changes.append("WARNING: Could not find trust stats row")

    with open('parents.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Applied {len(changes)} changes to parents.html")
    for change in changes:
        print(f" - {change}")

make_parents_changes()
