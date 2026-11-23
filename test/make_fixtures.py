"""Builds two FICTIONAL district websites used by the automated tests.

Riverbend exercises every crawler path: HTML pages, a text PDF with page
numbers, a scanned (image-only) PDF, a robots.txt block, a JavaScript-only page,
a broken link, a Google Drive link and a sitemap. Lakeside is a second district
used to prove answers never mix districts.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), 'fixtures')


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(text)


def page(title, body, nav=True):
    navhtml = """
<header><nav>
  <a href="/">Home</a>
  <a href="/calendar/">District Calendar</a>
  <a href="/transportation/">Transportation</a>
  <a href="/enrollment/">Enrollment &amp; Registration</a>
  <a href="/attendance/">Attendance</a>
  <a href="/docs/student-handbook-2026-27.pdf">Student Handbook 2026-27 (PDF)</a>
  <a href="/board/private/policy-drafts/">Board Policy Drafts</a>
  <a href="/parent-portal-app/">Parent Portal FAQ</a>
  <a href="/nutrition/">Nutrition Services</a>
  <a href="https://drive.google.com/file/d/abc123/view">Bell Schedule (Google Drive)</a>
  <a href="/docs/immunization-requirements-scan.pdf">Immunization Requirements (PDF)</a>
  <a href="/news/fall-sports-recap/">News: Fall sports recap</a>
</nav></header>""" if nav else ''
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{title} | Riverbend Unified School District</title>
<meta property="og:site_name" content="Riverbend Unified School District"></head>
<body>{navhtml}<main><h1>{title}</h1>{body}</main>
<footer>Riverbend Unified School District, 100 River Road, Riverbend, CA. Phone (555) 010-2000.</footer></body></html>"""


# ---------------- Riverbend (fictional) ----------------
write('riverbend/index.html', page('Welcome to Riverbend Unified', """
<p>Riverbend Unified School District serves 9,400 students in 14 schools. Our mission is that every student graduates ready for college, career and community.</p>
<h2>Quick links for families</h2>
<p>Find the district calendar, bus routes, enrollment steps and the student handbook using the links above.</p>"""))

write('riverbend/calendar/index.html', page('2026-27 District Calendar', """
<p>The first day of school for students is Wednesday, August 12, 2026. The last day of school is Thursday, June 3, 2027.</p>
<h2>Breaks and holidays</h2>
<ul>
<li>Labor Day: Monday, September 7, 2026 (no school)</li>
<li>Thanksgiving break: Monday, November 23 through Friday, November 27, 2026</li>
<li>Winter break: Monday, December 21, 2026 through Friday, January 1, 2027. Classes resume Monday, January 4, 2027.</li>
<li>Spring break: Monday, March 29 through Friday, April 2, 2027</li>
</ul>
<h2>Early release days</h2>
<p>Every Wednesday is an early release day. Elementary schools dismiss at 1:15 pm and secondary schools dismiss at 1:45 pm.</p>"""))

write('riverbend/transportation/index.html', page('Transportation', """
<p>Riverbend Unified provides free bus transportation to students who live more than 1.5 miles from their assigned school.</p>
<h2>Finding your bus stop</h2>
<p>Families can look up their bus stop and pickup time with the Stop Finder app. Enter your home address and your student's grade to see the stop. Routes are posted on August 1 each year.</p>
<h2>Bus rider rules</h2>
<p>Students must be at the stop five minutes before the scheduled pickup time. The driver will not wait for late students.</p>
<p>Questions about routes can go to the Transportation Office at (555) 010-2045, open 6:30 am to 4:30 pm on school days.</p>"""))

write('riverbend/enrollment/index.html', page('Enrollment & Registration', """
<p>New students enroll online through the district registration portal. Registration for the 2026-27 school year opens on February 2, 2026.</p>
<h2>Documents you need</h2>
<ul>
<li>Proof of the child's age, such as a birth certificate or passport</li>
<li>Two proofs of residency in Riverbend, such as a utility bill and a lease or mortgage statement dated within 60 days</li>
<li>Immunization records</li>
<li>The most recent report card or transcript, if the student attended another school</li>
</ul>
<h2>Kindergarten</h2>
<p>Children must turn five on or before September 1 to enroll in kindergarten. Transitional kindergarten is open to children who turn four by September 1.</p>"""))

write('riverbend/attendance/index.html', page('Attendance', """
<p>Regular attendance matters. When your child is absent, a parent or guardian must call the school attendance line or use the parent app before 9:00 am on the day of the absence.</p>
<h2>Excused absences</h2>
<p>Absences are excused for illness, medical or dental appointments, a death in the immediate family, and religious observances. A note is required within three school days of the student's return.</p>
<h2>Chronic absence</h2>
<p>Students who miss 10 percent or more of school days are considered chronically absent. The school will contact the family to make a support plan after the fifth unexcused absence.</p>"""))

write('riverbend/news/fall-sports-recap/index.html', page('Fall sports recap', '<p>Our teams had a great season with three league titles.</p>'))

# Robots-blocked page (must never be read)
write('riverbend/board/private/policy-drafts/index.html', page('Policy drafts', '<p>SECRET DRAFT: this text must never appear in answers.</p>'))

# JavaScript-only page
write('riverbend/parent-portal-app/index.html', """<!doctype html><html><head><title>Parent Portal FAQ</title>
<script src="/a.js"></script><script src="/b.js"></script><script src="/c.js"></script><script src="/d.js"></script><script src="/e.js"></script></head>
<body><div id="root"></div></body></html>""")

write('riverbend/robots.txt', """User-agent: *
Disallow: /board/private/
Sitemap: /sitemap.xml
""")
write('riverbend/sitemap.xml', """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>__ORIGIN__/calendar/</loc></url>
<url><loc>__ORIGIN__/transportation/</loc></url>
<url><loc>__ORIGIN__/health/medication-at-school/</loc></url>
</urlset>""")
write('riverbend/health/medication-at-school/index.html', page('Medication at School', """
<p>All medication taken at school, including over-the-counter medicine, requires a Medication Authorization Form signed by a parent and a licensed health care provider.</p>
<p>Medicine must be brought to the school nurse by an adult in the original labeled container. Students may carry asthma inhalers and epinephrine auto-injectors with written permission.</p>"""))

# Text PDF handbook with known content on known pages
os.makedirs(os.path.join(ROOT, 'riverbend/docs'), exist_ok=True)
pages = [
    ('Riverbend Unified School District', ['Student and Family Handbook 2026-27', 'This handbook explains district rules for students and families.']),
    ('Table of Contents', ['1. Welcome', '2. Contact information', '3. Cell phones and personal devices', '4. Grading', '5. Dress code']),
    ('Cell Phones and Personal Devices', [
        'Students may bring cell phones to school.',
        'Phones must be turned off and stored in backpacks from the first bell to the last bell.',
        'Students may use phones during lunch only at high schools.',
        'A phone used during class will be held in the main office until the end of the day.',
        'After a second violation, a parent must pick up the phone.',
    ]),
    ('Grading', ['Report cards are issued at the end of each semester.', 'Progress reports are available in the parent portal every six weeks.']),
    ('Dress Code', [
        'Clothing must cover the torso from the shoulders to mid-thigh.',
        'Hats may be worn outdoors only.',
        'Clothing with images of drugs, alcohol, weapons or hate symbols is not allowed.',
    ]),
]
c = canvas.Canvas(os.path.join(ROOT, 'riverbend/docs/student-handbook-2026-27.pdf'), pagesize=letter)
c.setTitle('Student and Family Handbook 2026-27')
for heading, lines in pages:
    c.setFont('Helvetica-Bold', 16)
    c.drawString(72, 720, heading)
    c.setFont('Helvetica', 11)
    y = 690
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.showPage()
c.save()

# Scanned PDF: an image of text, no text layer
img = Image.new('RGB', (1275, 1650), 'white')
d = ImageDraw.Draw(img)
d.text((100, 100), 'Immunization Requirements: DTaP, Polio, MMR, Hepatitis B, Varicella', fill='black')
img.save(os.path.join(ROOT, 'riverbend/docs/immunization-requirements-scan.pdf'), 'PDF', resolution=150)

# ---------------- Lakeside (second fictional district) ----------------
write('lakeside/index.html', """<!doctype html><html><head><title>Lakeside School District | Home</title></head>
<body><nav><a href="/calendar/">Calendar</a></nav><main><h1>Lakeside School District</h1>
<p>Lakeside School District serves families on the north shore with five elementary schools and one high school.</p></main></body></html>""")
write('lakeside/calendar/index.html', """<!doctype html><html><head><title>Calendar | Lakeside School District</title></head>
<body><main><h1>School Calendar</h1>
<p>Winter recess for Lakeside runs from December 18, 2026 to January 4, 2027. The first day of school was August 24, 2026.</p>
<p>Lakeside does not have weekly early release days.</p></main></body></html>""")
write('lakeside/robots.txt', 'User-agent: *\nAllow: /\n')

# ---------------- Upload test file ----------------
c = canvas.Canvas(os.path.join(ROOT, 'upload-transport-guide.pdf'), pagesize=letter)
c.setFont('Helvetica', 12)
c.drawString(72, 720, 'Hillcrest Schools Family Guide')
c.showPage()
c.setFont('Helvetica-Bold', 14)
c.drawString(72, 720, 'School Meals')
c.setFont('Helvetica', 11)
c.drawString(72, 700, 'Breakfast and lunch are free for every Hillcrest student under the Community Eligibility Provision.')
c.drawString(72, 682, 'Menus are posted monthly on the Nutrition Services page.')
c.showPage()
c.save()
print('fixtures written to', ROOT)
