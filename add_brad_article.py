import os
import shutil

source_img = r'c:\Users\JANMEJAY\Desktop\tom\Brad.jpg'
dest_img = r'c:\Users\JANMEJAY\Desktop\tom\articles\images\Brad.jpg'
if os.path.exists(source_img):
    os.makedirs(os.path.dirname(dest_img), exist_ok=True)
    shutil.copy2(source_img, dest_img)

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{description}">
    
    <!-- Open Graph Meta Tags -->
    <meta property="og:title" content="{title} | TomoClub Education Hall">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="https://www.tomoclub.org/articles/images/{cover_local_name}">
    <meta property="og:url" content="https://www.tomoclub.org/articles/{slug}/">
    <meta property="og:type" content="article">
    
    <!-- Twitter Card Meta Tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} | TomoClub Education Hall">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="https://www.tomoclub.org/articles/images/{cover_local_name}">

    <title>{title} | TomoClub Education Hall</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <link rel="stylesheet" href="../../styles.css?v=21">
    <style>
        body {{
            background: var(--bg-main);
            color: var(--text-main);
        }}

        .article-hero {{
            padding: 160px 0 80px;
            background: var(--hero-glow-teal);
            text-align: center;
        }}

        .article-meta {{
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            align-items: center;
            margin-bottom: 2rem;
            color: var(--text-muted);
            font-weight: 500;
        }}

        .article-category {{
            background: rgba(42, 180, 184, 0.1);
            color: var(--teal);
            padding: 0.4rem 1rem;
            border-radius: 999px;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .article-title {{
            font-size: clamp(2.5rem, 5vw, 4rem);
            line-height: 1.1;
            max-width: 1000px;
            margin: 0 auto 3rem;
            font-weight: 800;
        }}

        .article-cover {{
            width: 100%;
            max-width: 1100px;
            aspect-ratio: 16/9;
            object-fit: cover;
            border-radius: 32px;
            box-shadow: var(--shadow-xl);
            margin: 0 auto;
            display: block;
            border: 1px solid var(--border-color);
        }}

        .article-content {{
            max-width: 800px;
            margin: 5rem auto;
            padding: 0 1.5rem;
            line-height: 1.8;
            font-size: 1.15rem;
            color: var(--text-main);
        }}

        .article-content h3 {{
            font-size: 2rem;
            margin: 3rem 0 1.5rem;
            color: var(--text-main);
            font-weight: 700;
        }}

        .article-content p {{
            margin-bottom: 1.5rem;
        }}

        .article-content ul {{
            margin-bottom: 2rem;
            padding-left: 1.5rem;
        }}

        .article-content li {{
            margin-bottom: 0.75rem;
        }}

        .back-nav {{
            max-width: 800px;
            margin: 4rem auto;
            padding: 0 1.5rem;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--teal);
            font-weight: 600;
            text-decoration: none;
            transition: var(--transition);
        }}

        .back-link:hover {{
            transform: translateX(-5px);
        }}

        /* Navigation Style matching Main Site */
        nav {{
            position: fixed;
            top: 1.5rem;
            left: 50%;
            transform: translateX(-50%);
            width: calc(100% - 3rem);
            max-width: 1200px;
            z-index: 1000;
            padding: 0.75rem 1.5rem;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .nav-links {{
            display: flex;
            gap: 2rem;
            align-items: center;
        }}

        .nav-item a {{
            color: #94A3B8;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: var(--transition);
        }}

        .nav-item a:hover {{
            color: #fff;
        }}

        .logo {{
            font-weight: 800;
            font-size: 1.5rem;
            text-decoration: none;
        }}

        /* Dark Theme Support */
        body.dark-theme {{
            --bg-main: #020617;
            --text-main: #f1f5f9;
            --border-color: rgba(255,255,255,0.1);
        }}
    </style>
</head>
<body>
    <nav>
        <a href="../../#home" class="logo">
            <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
        </a>
        <div class="nav-links">
            <div class="nav-item"><a href="../../#education-hall">Education Hall</a></div>
            <div class="nav-item"><a href="../../#signup" class="btn btn-primary" style="padding: 0.6rem 1.2rem; border-radius: 999px; font-size: 0.85rem;">Request a Pilot</a></div>
        </div>
    </nav>

    <article>
        <div class="back-nav" style="margin-top: 140px; margin-bottom: -120px;">
            <a href="../../#education-hall" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; font-weight: 700; border-radius: 12px; text-decoration: none;">
                <i data-lucide="arrow-left"></i> View More
            </a>
        </div>
        <header class="article-hero">
            <div class="container">
                <div class="article-meta">
                    <span class="article-category">{category}</span>
                    <span class="article-date">{date}</span>
                </div>
                <h1 class="article-title">{title}</h1>
                <img src="{cover_local}" alt="{title}" class="article-cover">
            </div>
        </header>

        <div class="article-content">
            {content}
        </div>

        <div class="back-nav">
            <a href="../../#education-hall" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.8rem 1.5rem; font-weight: 700; border-radius: 12px; text-decoration: none;">
                <i data-lucide="arrow-left"></i> View More
            </a>
        </div>
    </article>

    <footer style="background: var(--surface); padding: 5rem 0; border-top: 1px solid var(--border-color);">
        <div class="container text-center">
            <div class="logo" style="margin-bottom: 2rem;">
                <span style="color: var(--teal);">To</span><span style="color: var(--gold);">mo</span><span style="color: var(--crimson);">Club</span>
            </div>
            <p style="color: var(--text-muted);">&copy; 2026 TomoClub. All rights reserved.</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script>
        lucide.createIcons();
        
        // Simple Theme Check
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-theme');
        }}
    </script>
</body>
</html>
"""

content = """<h3>LEADERSHIP IN PRACTICE | SUPERINTENDENT SPOTLIGHT</h3>
<p>An Ohio superintendent on how keeping "two ledger sheets" helps a district stay grounded in the long game, why honesty during a first-year pandemic built more trust than certainty ever could, and what student voice looks like when it actually changes something.</p>

<p>FEATURING Brad Winterod, Superintendent, Georgetown Exempted Village Schools</p>

<p>Brad Winterod has spent nearly three decades in education. Before any of the titles, he was a kid who needed someone to show up for him. That background still follows him into every room he walks into. Here's how it shapes the way he leads.</p>

<h3>Becoming the Support He Once Needed</h3>
<p>Brad Winterod grew up in poverty. He doesn't say it to be dramatic. He says it because it explains a lot about who he became as an educator.</p>
<p>When he started working with students and families in similar situations early in his career, something clicked.</p>
<p>"Their circumstances mirrored my own experiences growing up, which created a deep personal connection and motivation to do everything possible to help students overcome barriers and achieve success."</p>
<p>That connection never left. Today, as superintendent of Georgetown Exempted Village Schools, he carries it into every decision, from budget line items to hallway conversations.</p>
<p>Two early mentors also left their mark. Before he was ever in the principal's chair, Brad had the chance to learn under two experienced administrators who showed him what purposeful leadership actually looked like. Not the loud, directive kind. The kind that's grounded, clear, and genuinely invested in people.</p>
<p>The most important thing they modeled, something Brad still talks about, is that being a strong leader and being a kind person aren't the same thing. You don't have to choose.</p>
<p>"Throughout my career, I have worked to ensure that people knew I cared deeply about them while maintaining high expectations and a clear vision for success.”</p>
<p>That sounds simple. It's not. A lot of leaders pick one side or the other. Brad spent 30 years building both.</p>

<h3>The Two Things He Has to Run at the Same Time</h3>
<p>When Brad arrived at Georgetown in 2019, one of the first things he built was a strategic plan. Not a short-term list of goals, but a real roadmap that could hold up over the years. A way to align what the district does every day with what it's actually trying to become.</p>
<p>He describes leading a school district as managing two ledger sheets at the same time.</p>
<p>The first one is daily operations. The fires, the calls, the decisions that can't wait, the parent who needs a callback, the crisis that showed up at 7 a.m. That ledger is never empty. The second is the long-term vision: where the district is going, what students need five years from now, and what's being built brick by brick.</p>
<p>"Leaders cannot allow themselves to become consumed by the urgent at the expense of the important. Maintaining perspective is critical."</p>
<p>In practice, that philosophy drove three of his most significant moves at Georgetown. He started by building a sustainable strategic plan, not a document that would sit in a drawer, but a real roadmap aligning the district's resources and decisions with long-term goals that mattered to students, staff, and the community.</p>
<p>From there, he turned to the gifted education program, which wasn't identifying or serving students the way it should. He brought in a consultant, redesigned the delivery model, and expanded who got identified. Students who'd been overlooked started getting served.</p>
<p>He also moved to expand mental health support on campus. Today, the district employs a Student and Family Resource Coordinator, a licensed social worker who connects students and families with community resources, and a separate full-time licensed social worker based on campus who works directly with students and consistently carries a full caseload. Students can't learn when other things are falling apart at home or in their heads. Brad knew that, and he made it someone's actual job.</p>
<p>None of these produced instant results you could put on a chart. All three required patience and planning. But they were the right things to build, and they're still standing.</p>

<h3>The Year He Had No Playbook</h3>
<p>Brad had been superintendent for less than a year when COVID hit.</p>
<p>He was still learning the district, still earning trust, still figuring out who was who. And suddenly he was being asked to make decisions that nobody had made before, with information that changed by the day.</p>
<p>"There were very few clear answers. Nearly every day brought new questions, challenges, and shifting expectations."</p>
<p>What he decided was to be honest about it. He didn't pretend to have a plan when he didn't. He told staff and families that he didn't have all the answers on COVID but that he was committed to working through every question as carefully and quickly as possible.</p>
<p>That kind of transparency is riskier than it sounds. People want certainty from their leaders. Admitting you don't have all the answers feels like weakness. But Brad made a bet: that honesty would build more trust than false confidence ever could.</p>
<p>He was right. The community came through it together. And the experience reinforced something he already believed: that people follow leaders they trust, and trust gets built in the hard moments, not the easy ones.</p>

<h3>Planning For AI Before the Mandate</h3>
<p>Brad's take on technology has always been simple: use it when it genuinely helps students learn, and don't when it doesn't.</p>
<p>"Technology cannot replace effective teaching, but it can serve as a powerful tool to support and enrich instruction."</p>
<p>That same logic applies to AI. He doesn't see it as a threat or a silver bullet. He sees it as something that's going to keep growing whether districts plan for it or not, which means the only real choice is whether to get ahead of it or keep catching up.</p>
<p>Georgetown chose to get ahead of it.</p>
<p>Before the pressure to just do something got loud, Brad convened a committee of teachers and staff across the district. The goal was to build an AI strategic plan with broad input, not to hand down a policy from the top.</p>
<p>"By convening a diverse committee, we were able to craft a plan that reflects multiple perspectives and builds collective responsibility for implementation.”</p>
<p>The plan is posted publicly on the district website. It's designed to evolve as technology and needs change. And because the people who built it are the same people who have to live with it, there's actual buy-in rather than just compliance.</p>
<p>He also pushed himself to keep learning. Seeking out professional development on AI, not just for staff but for himself, is part of how he stays positioned to lead rather than react.</p>
<p>"The goal is not simply to adopt AI, but to integrate it in a thoughtful, ethical, and purposeful way that enhances teaching and learning while keeping student success at the center."</p>
<p>That's the same logic he applies to everything else. The technology changes. The principle doesn't.</p>

<h3>Presence Isn't a Soft Skill</h3>
<p>Georgetown Exempted Village Schools sits on one campus. All the schools, together. That means Brad sees students every day. Not in a scheduled way, but in the way where you actually know people.</p>
<p>He talks about a student in the FFA program who came to him with a practical concern: there was no running water near the area where FFA students care for farm animals. The student made a case for it. It made sense. Brad looked into it, and they got it installed.</p>
<p>That story sounds small. It isn't. Because that student brought it forward because he believed it would go somewhere. That belief doesn't exist in a vacuum. It gets built when students see that their ideas actually land, that the person in charge is reachable, and that showing up and saying something matters.</p>
<p>Brad measures success partly this way. Not just test scores, but the overall mood of the building. How does it feel on a Wednesday in February?</p>
<p>"After working in education long enough, you develop a sense of the daily and seasonal ebbs and flows.”</p>
<p>When people feel supported and valued, you can feel it.</p>
<p>He also talks about graduation. In a small district, he often knows the graduates personally. Their stories. What they've been through. Watching them walk across the stage isn't just a ceremony to him. It's evidence.</p>
<p>For aspiring leaders, he has the one-third rule. Roughly one-third of people may support you, one-third may disagree, and one-third may stay neutral. It's not scientific. But it's a useful reminder not to lead for approval.</p>
<p>"Lead with purpose and integrity.”</p>
<p>And his final word? The simplest thing he says: don't give up. This work wears people down. It takes everything. But the reason to stay is the same as the reason to start: the students.</p>
<p>"You can only truly impact the people you know and the people who know you."</p>
<p>So he shows up. Every day.</p>

<h3>Thirty Years In, He's Still Figuring It Out</h3>
<p>Nearly three decades in, Brad Winterod hasn't become a person who leads from behind a desk. He still walks the campus. Still knows students by name. Still picks up the parent email himself.</p>
<p>The two ledger sheets keep running. The daily one: the fires, the decisions, the operational weight of keeping a district going. And the long one, the one that asks what kind of place Georgetown is building for the next generation.</p>
<p>The trick, he'd tell you, isn't choosing between them. It's running both at the same time, without losing sight of either.</p>
<p>That's harder than it sounds. Most leaders drift toward one or the other, consumed by the daily or so focused on the horizon they stop seeing what's in front of them. Brad has spent 30 years figuring out how to hold both. And from the look of it, he's still working on it. Which is probably exactly the point.</p>

<h3>Why TomoClub Is Sharing This Story</h3>
<p>At TomoClub, we believe the future of education isn't shaped by the loudest voices in the room. It's shaped by the leaders who've been quietly doing the work for decades and still show up every morning as it matters.</p>
<p>Brad Winterod's work at Georgetown Exempted Village Schools reflects a kind of leadership that doesn't make the headlines. Steady. Grounded. Present. The kind that understands you can't improve a school from a distance. The trust, the culture, and the outcomes all get built one relationship at a time. And showing up isn't a strategy you implement. It's who you decide to be.</p>
<p>That's exactly the kind of leader education needs right now.</p>
"""

slug = "brad-winterod-superintendent"
title = "How 30 Years in Education Shaped the Way Brad Winterod Leads a District"

article_html = html_template.format(
    title=title,
    description=title,
    category="School Leadership",
    date="June 22, 2026",
    cover_local="../../articles/images/Brad.jpg",
    cover_local_name="Brad.jpg",
    slug=slug,
    content=content
)

os.makedirs(fr'c:\Users\JANMEJAY\Desktop\tom\articles\{slug}', exist_ok=True)
with open(fr'c:\Users\JANMEJAY\Desktop\tom\articles\{slug}\index.html', 'w', encoding='utf-8') as f:
    f.write(article_html)

# Read index.html
with open(r'c:\Users\JANMEJAY\Desktop\tom\index.html', 'r', encoding='utf-8') as f:
    index_content = f.read()

new_card = f'''
                <a href="articles/{slug}/" class="glass-card" style="text-decoration: none; color: inherit; display: block; transition: transform 0.3s ease; padding: 0; overflow: hidden;" target="_blank">
                    <div style="background: var(--card-grad-teal); height: 100%; display: flex; flex-direction: column;">
                        <img src="articles/images/Brad.jpg" alt="Brad Winterod" style="width: 100%; height: 220px; object-fit: cover; border-bottom: 1px solid var(--border-color);">
                        <div style="padding: 2rem; display: flex; flex-direction: column; flex-grow: 1;">
                            
                            <h3 style="margin: 1rem 0; font-size: 1.25rem; font-weight: 600;" class="article-title">{title}</h3>
                            <span class="btn btn-secondary btn-read-more">Read More <i data-lucide="arrow-right"></i></span>
                        </div>
                    </div>
                </a>
'''

target_string = '<div class="grid-3 animate-on-scroll" id="articles-grid">'
if target_string in index_content:
    index_content = index_content.replace(target_string, target_string + new_card)

with open(r'c:\Users\JANMEJAY\Desktop\tom\index.html', 'w', encoding='utf-8') as f:
    f.write(index_content)

print('Added article and updated index.html')
