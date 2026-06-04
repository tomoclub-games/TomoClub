import json
import os

with open('articles_data.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

json_str = js_content.replace('const articlesData = ', '').rstrip().rstrip(';')
articles = json.loads(json_str)

html_content = """<p class="article-meta-info" style="color: var(--teal); font-weight: bold; text-transform: uppercase;">LEADERSHIP IN PRACTICE | SUPERINTENDENT SPOTLIGHT</p>
<p><strong>A Michigan superintendent on why leading a School of Choice district means you're always competing, why over-communicating isn't a weakness but a strategy, what a personal brand like "Opportunity, Regardless" looks like in practice, and how to build culture in a community that needs more than just academic results.</strong></p>
<p><em>FEATURING Piper Bognar, Superintendent, Van Dyke Public Schools</em></p>
<div style="text-align: center; margin: 2rem 0;"><img src="../images/piper-new.png" style="max-width: 100%; border-radius: 8px;" alt="Piper Bognar" /></div>
<p>When you're building toward the superintendency, you’re completely unaware that the job will ask you to hold budget spreadsheets in one hand and a student's future in the other, all at the same time, every day. Piper Bognar has been doing exactly that. And the way she does it says a lot about how she got here.</p>
<p>Bognar leads Van Dyke Public Schools in Michigan, a district dealing with real complexity: student mobility, School of Choice competition, over 100 state categorical grants, and classrooms where a single teacher might be working with students spanning seven grade levels. None of it is tidy. None of it fits neatly into a leadership framework you'd find in a textbook.</p>
<p>What she built instead is something more durable. A philosophy she calls "Opportunity, Regardless", and a way of leading that's less about managing the chaos and more about staying oriented inside it.</p>
<h3>Not Your Typical Superintendent's Resume</h3>
<p>Before she was a superintendent, a curriculum director, or a literacy specialist, Piper Bognar worked at a car wash. She supervised kitchen maintenance at a university cafeteria and waited tables. A lot of tables.</p>
<p>She doesn't tell these stories to be humble. She tells them because they taught her something most leadership development programs skip entirely: what it actually feels like to be the person being managed. To wonder if the person at the top has any idea what your job looks like. To notice when a decision was made without thinking about how it lands on the ground floor.</p>
<p>"All of these experiences lend themselves to how you treat others and knowing what goes into a big picture view. If you leave out a facet of who or what will be affected, the decision itself is likely to yield some failures."</p>
<p>That's not a theory. That's something she learned before she ever sat in a district office.</p>
<p>Throughout her career in literacy, school improvement, curriculum, and district leadership, Piper has learned to ask deeper questions before taking action. When evaluating a new curriculum resource, she considers its effectiveness and broader implications, including its impact on users, the rollout process, the necessary training, support for teachers, and storage needs. Her thorough approach comes from her experiences in environments where these important questions were often overlooked.</p>
<h3>The Overlooked Daily Trials of School Leadership</h3>
<p>Van Dyke is a School of Choice district, which means families can leave. Not because of a major failure, sometimes because of something small. A single unhappy interaction. A policy decision that rubbed someone the wrong way. And when a family goes, it doesn't just affect enrollment numbers. It ripples into staffing, building usage, and projections for the next school year.</p>
<p>"We often 'trade' students with nearby districts on the whim of a parent being unhappy with small or large decisions."</p>
<p>That pressure changes how you think about every decision you make publicly.</p>
<p>Then there's the mobility piece. Students arriving mid-year who haven't been in a classroom in months, or in some cases, ever. Teachers working with one age group that's actually functioning across seven different grade levels. The MTSS framework Van Dyke has built tries to address this by meeting students where they are, bringing them to where they need to be, and Bognar isn't pretending it's solved.</p>
<p>It's a real, ongoing challenge. She accepts directly.</p>
<p>Budgeting sits on all of this. Managing local funds, federal funds, and more than 100 categorical state grants isn't a one-person job. The COVID-era federal funds made things simultaneously harder and more possible. And through all of it, she's had to keep her Board of Education not just informed, but actually involved. That matters.</p>
<h3>Over-Communicating Is a Strategy, Not a Habit</h3>
<p>Some superintendents go quiet during difficult times, hoping rumors fade. They send one cautious email and think that counts as communication. Bognar does the opposite.</p>
<p>Her instinct when something difficult happens, such as a community incident, a budget cut, a policy change that's going to upset people, is to send more messages, not fewer. She sends a message to families, and a separate one for staff that includes what community members are receiving, so nobody finds out through the grapevine. A message to the Board. Then a Q&A round for all stakeholders.</p>
<p>"I believe in overcommunicating and tailoring messages to each group."</p>
<p>It sounds like a lot of work because it is. But the alternative of letting people fill the silence with speculation is much worse.</p>
<p>"If you can't be proactive, such as with rumors, you may as well squash them with truth."</p>
<p>She also promises something many leaders are afraid to: "I'll be as transparent as legally possible." Not all the way, just what’s legally possible.</p>
<p>That distinction matters, and people notice when you're honest about where the line is.</p>
<p>Follow through, she says, is what builds trust over time. Not speeches or vision documents. Just doing what you said you were going to do, consistently, for years.</p>
<h3>What Equity Looks Like When It's Not on a Poster</h3>
<p>When Bognar is asked about school culture, she starts with equity, but not the poster-on-the-wall version. Her definition is specific: everyone feeling a sense of belonging, every single day, in a space that's both brave and safe. Experiences and challenges are understood and factored into the work.</p>
<p>"Until all stakeholders are ready to live in this work, the culture will have some fractures. This begins with leadership and communication. It takes more than a message in an email to live and walk that talk."</p>
<p>The fractures, she means, are real. You don't fix them with a professional development day. You fix them by modeling something different, consistently over time, and being honest when you fall short.</p>
<p>On the instructional side, she'll tell you there's no silver bullet in literacy. Not one program, not one approach. What Van Dyke is building is a strong Tier I foundation. Every student, every classroom has targeted Tier II and Tier III support layered on top. The Science of Reading model is the frame, but the philosophy underneath it is about meeting each kid where they actually are.</p>
<p>Same with professional learning. Teachers need time to collaborate, to look at data together, talk about what's working, and be honest about what isn't. That collaboration, she says, is what turns an average classroom into a better one because teachers A and B start talking about what works and why, in a brave space, with trained facilitation. Results come from that.</p>
<h3>AI is Something Nobody Has Figured Out Yet</h3>
<p>When the topic turns to artificial intelligence, Bognar doesn't pretend to have a polished district strategy ready to present.</p>
<p>"This is such a loaded question.”</p>
<p>What she's sitting with is real: students surveyed, staff surveyed, everyone at different comfort levels, different ideas about how it should be used. The preschool room looks nothing like 12th grade. What AI means in one context is completely different in another.</p>
<p>But she's not spooked. "We have an opportunity to create our path, which is rare." And she believes students are graduating into an AI world, whether the district is ready or not. The question isn't whether to engage with it; it's how to be intentional about the path.</p>
<p>That's about where most honest superintendents are right now. The ones who tell you they have it sorted out are probably oversimplifying.</p>
<h3>The One Thing She Asks Every Senior Class</h3>
<p>Every year, Piper Bognar stands before the graduating seniors and asks them one simple thing.</p>
<p>She doesn't urge them to change the world grandly or to be ambitious or successful, as motivational posters often suggest. Instead, she asks them to wake up each morning and decide how they will make the world a better place that day. Even if their actions seem small or if they are the only ones who notice, it's the intention that matters.</p>
<p>"Be the pebble in the pond."</p>
<p>That's her close for the class. It's also quiet, as she describes her own approach to the work. Improving the district's reputation. Building relationships that last. Seeing a student smile. Watching a colleague succeed.</p>
<p>"Every student smile I've seen has made me proud. Each success story has made me proud, whether it's been of myself or of a trusted and loved colleague."</p>
<p>It's neither flashy nor the kind of quote that goes viral. But it's honest, and after two decades in education, in roles from classroom teacher to superintendent, Piper Bognar has earned the right to say simple things and mean them entirely.</p>
<h3>Why TomoClub Is Sharing This Story</h3>
<p>At TomoClub, we believe the future of education is shaped not by flashy reforms, but by leaders within schools who quietly build systems, strengthen trust, and respond to real challenges with intention.</p>
<p>Piper Bognar's work at Van Dyke Public Schools reflects a leadership that often goes unnoticed. Grounded, communicative, and stubbornly student-first, which understands that before you improve outcomes, you build trust. And that trust is built through follow-through, not announcements. That kind of leadership is exactly what education needs right now.</p>
<p>Follow TomoClub for stories from leaders doing the real work in real schools.</p>"""

html_content = html_content.replace('\n', '')

articles['article_7'] = html_content

with open('articles_data.js', 'w', encoding='utf-8') as f:
    f.write('const articlesData = ' + json.dumps(articles, indent=2, ensure_ascii=False) + ';')

print("Updated articles_data.js")
