import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find the MEET THE INNOVATORS section
start_marker = '<!-- MEET THE INNOVATORS -->'
end_marker = '<!-- ADVISORY TEAM -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    section = html[start_idx:end_idx]
    
    # Extract all team-container blocks
    # Each starts with <div class="team-container"> and should end with 3 closing </div> tags
    # (one for team-container, one for team-card, one for team-card-back or overlay?)
    # Actually, team-card has front and back.
    # Structure:
    # <div class="team-container">
    #   <div class="team-card">
    #     <div class="team-card-front">...</div>
    #     <div class="team-card-back">...</div>
    #   </div>
    # </div>
    
    containers = re.findall(r'<div class=\"team-container\">.*?</div>\s*</div>\s*</div>', section, re.DOTALL)
    
    new_section = f'''{start_marker}
                <div style="margin-bottom: 6rem;">
                    <h3 style="margin-bottom: 3rem; color: var(--navy); border-left: 4px solid var(--gold); padding-left: 1.5rem; font-size: 1.75rem;">Meet the Innovators</h3>
                    <div class="grid-centered-5" style="margin-bottom: 2rem;">
                        {"".join(containers)}
                    </div>
                </div>
                
                '''
    
    html = html[:start_idx] + new_section + html[end_idx:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Rewrote Innovators section correctly")
