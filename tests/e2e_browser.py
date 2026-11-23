"""End-to-end browser test for TomoClub tracking, consented partial leads, notifications and the /admin dashboard.
Needs: python playwright, Chrome, and `node tests/e2e-server.mjs 8100` running. Run: python3 tests/e2e_browser.py
External services (GA, Calendly, fonts) are stubbed; gtag calls are captured from window.dataLayer and checked
for personal data."""
import asyncio, json, re, sys, os, urllib.request
from playwright.async_api import async_playwright

BASE = 'http://localhost:8100'
NODE = os.environ.get('NODE_MODULES', '/home/claude/audit/node_modules/')
OUT = os.environ.get('SHOTS', '/home/claude/tctest/')
results, ga_calls = [], []

def state(): return json.load(urllib.request.urlopen(BASE + '/__test/state'))
def call(p): return json.load(urllib.request.urlopen(BASE + p))
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail)); print(('PASS ' if cond else 'FAIL ') + name + ('' if cond else '  ' + str(detail)))
def rows(tab):
    t = state()['tabs'].get(tab) or []
    if not t: return []
    head = t[0]; return [dict(zip(head, r)) for r in t[1:]]

async def route(r):
    u = r.request.url
    if 'lucide' in u: return await r.fulfill(path=NODE + 'lucide/dist/umd/lucide.min.js', content_type='text/javascript')
    if 'purify' in u: return await r.fulfill(path=NODE + 'dompurify/dist/purify.min.js', content_type='text/javascript')
    if 'googletagmanager.com/gtag' in u: return await r.fulfill(body='/* gtag stub */', content_type='text/javascript')
    if u.startswith(BASE): return await r.continue_()
    return await r.abort()

async def grab_ga(pg):
    try:
        dl = await pg.evaluate("JSON.stringify((window.dataLayer||[]).map(a=>Array.from(a)))")
        ga_calls.extend(json.loads(dl))
    except Exception: pass

async def new_page(ctx):
    # Only outside requests are intercepted; the site's own requests (including unload beacons) go straight through.
    pg = await ctx.new_page(); await pg.route(lambda url: not url.startswith(BASE), route); return pg

async def main():
    urllib.request.urlopen(BASE + '/__test/reset').read()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'])
        ctx = await b.new_context(viewport={'width': 1366, 'height': 900}, accept_downloads=True, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
        errors = []
        ctx.on('weberror', lambda e: errors.append(str(e.error)))

        # 1. Page view + traffic source + device
        pg = await new_page(ctx)
        await pg.goto(BASE + '/?utm_source=linkedin&utm_medium=social&email=leak@example.org', wait_until='networkidle')
        await pg.wait_for_timeout(800)
        consent = await pg.evaluate("[...document.querySelectorAll('#b2b-lead-form .tc-consent input')].map(i=>i.name+':'+i.checked)")
        check('consent boxes added to the home form, unticked', consent == ['save_progress_consent:false', 'marketing_consent:false'], consent)
        await pg.screenshot(path=OUT + 'home-form.png', clip=await pg.evaluate("(()=>{const r=document.querySelector('#b2b-lead-form').getBoundingClientRect();return {x:r.x,y:r.y+scrollY,width:r.width,height:r.height}})()"), full_page=True)

        # 2. Button clicks: hero Book a call (Calendly blocked -> falls back to a new tab) and an offer link
        async with ctx.expect_page() as popup:
            await pg.click('.h-hero a[data-book-call]')
        await (await popup.value).close()
        await pg.click('a[href="#proof"]')
        await pg.wait_for_timeout(300)

        # 3. Partial lead WITHOUT consent: typed, left -> nothing saved
        await pg.fill('#lf-name', 'Nora Noconsent'); await pg.fill('#lf-email', 'nora@district.org'); await pg.fill('#lf-org', 'Nope USD')
        await pg.wait_for_timeout(4600)
        await grab_ga(pg)
        await pg.goto(BASE + '/about', wait_until='networkidle'); await pg.wait_for_timeout(500)
        check('no partial lead saved without consent', not any(r['Email'] == 'nora@district.org' for r in rows('Partial leads')))
        ev = rows('Website events')
        check('page_view recorded with source linkedin and device', any(e['Event'] == 'page_view' and e['Source'] == 'linkedin' and e['Device'] == 'desktop' for e in ev))
        check('book_call_click recorded', any(e['Event'] == 'book_call_click' for e in ev))
        check('form_start and form_abandon recorded for home form', {'form_start', 'form_abandon'} <= {e['Event'] for e in ev if e['Form'] == 'home_discovery'})
        check('form_view recorded', any(e['Event'] == 'form_view' and e['Form'] == 'home_discovery' for e in ev))
        check('no email in any event row', not any('@' in json.dumps(list(e.values())) for e in ev), [e for e in ev if '@' in json.dumps(list(e.values()))][:2])

        # 4. Partial lead WITH consent, then leave -> saved; team alerted once after the wait
        await pg.goto(BASE + '/', wait_until='networkidle'); await pg.wait_for_timeout(500)
        await pg.fill('#lf-name', 'Pat Partial'); await pg.fill('#lf-email', 'pat@district.org'); await pg.fill('#lf-org', 'Partial Valley SD')
        await pg.check('#b2b-lead-form [name=save_progress_consent]')
        await pg.wait_for_timeout(1200)
        await grab_ga(pg)
        await pg.goto(BASE + '/results', wait_until='networkidle'); await pg.wait_for_timeout(600)
        pr = [r for r in rows('Partial leads') if r['Email'] == 'pat@district.org']
        check('consented partial lead saved with name, email, district', len(pr) == 1 and pr[0]['Name'] == 'Pat Partial' and pr[0]['School or district'] == 'Partial Valley SD', pr)
        check('partial lead stores the consent text', pr and "Save my details" in pr[0]['Consent shown'])
        before = len(state()['mail'])
        call('/__test/run-partial-check'); call('/__test/run-partial-check')
        st = state()
        check('partial lead alert sent exactly once (email + Slack)', len(st['mail']) == before + 1 and sum('Unfinished form' in s for s in st['slack']) == 1, (len(st['mail']), before))

        # 5. Withdraw: tick, save, untick -> erased
        await pg.goto(BASE + '/', wait_until='networkidle'); await pg.wait_for_timeout(400)
        await pg.fill('#lf-name', 'Wendy Withdraw'); await pg.fill('#lf-email', 'wendy@district.org')
        await pg.check('#b2b-lead-form [name=save_progress_consent]'); await pg.wait_for_timeout(800)
        saved = any(r['Email'] == 'wendy@district.org' for r in rows('Partial leads'))
        await pg.uncheck('#b2b-lead-form [name=save_progress_consent]'); await pg.wait_for_timeout(800)
        wr = [r for r in rows('Partial leads') if r['Status (partial / converted / withdrawn)'] == 'withdrawn']
        check('unticking erases a saved partial lead', saved and len(wr) == 1 and wr[0]['Email'] == '' and wr[0]['Name'] == '', wr)

        # 6. Complete the home form with marketing consent (partial first, then send) -> converted, one alert, Instantly
        await pg.goto(BASE + '/', wait_until='networkidle'); await pg.wait_for_timeout(400)
        await pg.fill('#lf-name', 'Jane Complete'); await pg.fill('#lf-email', 'jane@district.org'); await pg.fill('#lf-org', 'Complete Unified SD')
        await pg.select_option('#lf-role', 'Superintendent'); await pg.fill('#lf-goal', 'We need an AI policy our board can follow.')
        await pg.check('#b2b-lead-form [name=save_progress_consent]'); await pg.check('#b2b-lead-form [name=marketing_consent]')
        await pg.wait_for_timeout(3300)
        mails_before = len(state()['mail'])
        await pg.click('#b2b-lead-form button[type=submit]')
        await pg.wait_for_selector('.h-form-status.ok', timeout=8000)
        await grab_ga(pg)
        sl = [r for r in rows('School leads') if r['Email'] == 'jane@district.org']
        check('completed lead saved once with consent flag', len(sl) == 1 and sl[0]['Agreed to marketing emails'] == 'yes' and sl[0]['Form'] == 'home_discovery', sl)
        check('Instantly received the consented lead', any(l['leads'][0]['email'] == 'jane@district.org' for l in state()['instantly']))
        check('its partial lead was marked converted', any(r['Email'] == 'jane@district.org' and r['Status (partial / converted / withdrawn)'] == 'converted' for r in rows('Partial leads')))
        check('one alert for the completed lead', len(state()['mail']) == mails_before + 1)
        call('/__test/run-partial-check')
        check('converted partial lead is never alerted', len(state()['mail']) == mails_before + 1)
        # duplicate submit with the same submission id (a retry) -> no new row, no new alert
        body = await pg.evaluate("""async () => { const r = await fetch('/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'discovery_request',name:'Jane Complete',email:'jane@district.org',district:'Complete Unified SD',goal:'x',submission_id:document.querySelector('#b2b-lead-form [name=submission_id]').value,form_loaded_at:Date.now()-9000})}); return r.status; }""")
        await pg.wait_for_timeout(300)
        n_jane = len([r for r in rows('School leads') if r['Email'] == 'jane@district.org'])
        check('new submission id after success (so a second, real message is not dropped)', n_jane == 2 and len(state()['mail']) == mails_before + 2, (n_jane, len(state()['mail'])))
        # same exact submission id twice
        await pg.evaluate("""async () => { const b={type:'discovery_request',name:'Retry Rae',email:'rae@district.org',district:'R',goal:'x',submission_id:'subRETRY12345',form_loaded_at:Date.now()-9000}; for (let i=0;i<2;i++) await fetch('/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}); }""")
        check('retried submission saved once and alerted once', len([r for r in rows('School leads') if r['Email'] == 'rae@district.org']) == 1 and sum('rae@district.org' in m['body'] for m in state()['mail']) == 1)

        # 7. Spam: honeypot filled -> silently dropped
        await pg.evaluate("""async () => { await fetch('/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'discovery_request',name:'Bot',email:'bot@spam.biz',district:'x',goal:'x',hp_company_website:'http://spam',form_loaded_at:Date.now()-9000})}); }""")
        check('honeypot submission dropped', not any(r['Email'] == 'bot@spam.biz' for r in rows('School leads')))

        # 8. Calendly booking confirmed
        await pg.evaluate("""window.dispatchEvent(new MessageEvent('message',{origin:'https://calendly.com',data:{event:'calendly.event_scheduled',payload:{invitee:{uri:'https://api.calendly.com/scheduled_events/EV1/invitees/IN1'}}}}))""")
        await pg.wait_for_timeout(1200)
        await grab_ga(pg)
        cb = [r for r in rows('School leads') if r['Type'] == 'call_booked']
        check('confirmed Calendly booking saved as a lead with meeting time', len(cb) == 1 and cb[0]['Email'] == 'casey@district.k12.us' and cb[0]['Meeting start (UTC)'].startswith('2026-11-25'), cb)
        check('booking not sent to Instantly (no marketing consent)', not any(l['leads'][0]['email'] == 'casey@district.k12.us' for l in state()['instantly']))

        # 9. Build With Us form
        await pg.goto(BASE + '/build-with-us', wait_until='networkidle'); await pg.wait_for_timeout(3200)
        await pg.fill('#f-name', 'Ben Builder'); await pg.fill('#f-org', 'Builder County Schools'); await pg.fill('#f-email', 'ben@builder.k12.us'); await pg.fill('#f-goal', 'Special ed life-skills games')
        await pg.screenshot(path=OUT + 'bwu-form.png', clip=await pg.evaluate("(()=>{const r=document.querySelector('#project-form').getBoundingClientRect();return {x:r.x,y:r.y+scrollY,width:r.width,height:r.height}})()"), full_page=True)
        await grab_ga(pg)
        await pg.click('#project-form button[type=submit]')
        await pg.wait_for_url('**/build-with-us/thank-you', timeout=8000)
        bw = [r for r in rows('School leads') if r['Email'] == 'ben@builder.k12.us']
        check('Build With Us form saved via the lead API', len(bw) == 1 and bw[0]['Type'] == 'build_with_us', bw)
        check('Build With Us lead not sent to Instantly without consent', bw and bw[0]['Instantly'].startswith('not sent'))

        # 10. Guide download (modal on /guides)
        await pg.goto(BASE + '/guides', wait_until='networkidle'); await pg.wait_for_timeout(500)
        await pg.click('[data-file]')
        await pg.wait_for_timeout(3200)
        await pg.fill('#toolkit-download-form [name=firstName]', 'Gia Guide'); await pg.fill('#toolkit-download-form [name=email]', 'gia@school.org')
        await pg.check('#toolkit-download-form [name=marketing_consent]')
        async with pg.expect_download() as dlinfo:
            await pg.click('#toolkit-download-form button[type=submit]')
        await pg.wait_for_timeout(800)
        await grab_ga(pg)
        td = [r for r in rows('Toolkit downloads') if r['Email'] == 'gia@school.org']
        check('guide download saved with marketing consent and sent to Instantly', len(td) == 1 and td[0]['Agreed to marketing emails'] == 'yes' and any(l['leads'][0]['email'] == 'gia@school.org' for l in state()['instantly']), td)

        # 11. Ebook
        await pg.goto(BASE + '/leaders-of-tomorrow', wait_until='networkidle'); await pg.wait_for_timeout(3200)
        await pg.fill('#hero-form [name=firstName]', 'Eli Ebook'); await pg.fill('#hero-form [name=email]', 'eli@school.org')
        await pg.click('#hero-form button[type=submit]'); await pg.wait_for_timeout(1200)
        await grab_ga(pg)
        er = [r for r in rows('E-book requests') if r['Email'] == 'eli@school.org']
        check('ebook request saved, no Instantly without consent', len(er) == 1 and not any(l['leads'][0]['email'] == 'eli@school.org' for l in state()['instantly']))
        await pg.goto(BASE + '/about', wait_until='networkidle'); await pg.wait_for_timeout(600)

        # 12. Events summary
        ev = rows('Website events'); names = {e['Event'] for e in ev}
        need = {'page_view', 'cta_click', 'book_call_click', 'form_view', 'form_start', 'form_submit', 'form_success', 'form_abandon', 'partial_saved', 'resource_download', 'book_call_scheduled'}
        check('all event types recorded', need <= names, need - names)
        check('still no email or phone in any event row', not any(re.search(r'@|\d{3}[\s.-]\d{3}[\s.-]\d{4}', json.dumps(list(e.values()))) for e in ev))

        # 13. GA4 payloads: events present, no personal data
        ga_events = [c for c in ga_calls if c and c[0] == 'event']
        ga_names = {c[1] for c in ga_events}
        check('GA4 got generate_lead, book_call_scheduled, resource_download, cta and form events', {'generate_lead', 'book_call_scheduled', 'resource_download', 'book_call_click', 'cta_click', 'form_start', 'form_view'} <= ga_names, ga_names)
        blob = json.dumps(ga_calls)
        pii = [s for s in ['@district.org', '@school.org', 'leak@example.org', 'Jane Complete', 'Pat Partial', 'Partial Valley', 'Complete Unified', 'gia@', 'Ben Builder'] if s in blob]
        check('GA4 received no names, emails or school names', not pii, pii)
        cfg = [c for c in ga_calls if c and c[0] == 'config']
        check('GA4 page_location has personal query values redacted', cfg and all('leak%40' not in json.dumps(c) and 'leak@' not in json.dumps(c) for c in cfg), cfg[:1])

        # 14. Dashboard
        ad = await new_page(ctx)
        await ad.goto(BASE + '/admin', wait_until='networkidle')
        await ad.fill('#pw', 'wrong password!!'); await ad.click('#login button'); await ad.wait_for_timeout(500)
        check('wrong password refused', 'Wrong password' in await ad.inner_text('#login-err'))
        await ad.fill('#pw', 'correct horse battery'); await ad.click('#login button')
        await ad.wait_for_selector('.kpi', timeout=8000); await ad.wait_for_timeout(500)
        kp = await ad.evaluate("Object.fromEntries([...document.querySelectorAll('.kpi')].map(k=>[k.querySelector('.l').textContent,k.querySelector('.n').textContent]))")
        check('dashboard shows visitors, leads and incomplete leads', int(kp['Visitors']) >= 1 and int(kp['Completed leads']) >= 6 and int(kp['Incomplete leads (consented)']) >= 1, kp)
        srcs = await ad.inner_text('#sources'); check('traffic sources include linkedin', 'linkedin' in srcs)
        ctas = await ad.inner_text('#ctas'); check('buttons clicked include Book a call', 'Book a call' in ctas, ctas)
        forms = await ad.inner_text('#forms'); check('forms table lists the home form and Build With Us', 'Home page' in forms and 'Build With Us' in forms)
        await ad.screenshot(path=OUT + 'dashboard-top.png', full_page=False)
        n_completed = await ad.locator('#lead-table tbody tr[data-id]').count()
        check('completed leads listed', n_completed >= 6, n_completed)
        # status change
        first = ad.locator('#lead-table tbody tr[data-id]').first
        lid = await first.get_attribute('data-id')
        await ad.fill('#me', 'Avinash'); await ad.dispatch_event('#me', 'change')
        await first.locator('select').select_option('Contacted'); await ad.wait_for_timeout(700)
        ls = rows('Lead status')
        check('follow-up status saved to the Sheet', any(r['Lead ID'] == lid and r['Status'] == 'Contacted' and r['Updated by'] == 'Avinash' for r in ls), ls[-1:] )
        # CSV
        async with ad.expect_download() as d1:
            await ad.click('#csv')
        csv = open(await (await d1.value).path(), encoding='utf-8-sig').read()
        check('CSV export of completed leads', csv.startswith('lead_id,kind,name,email') and 'jane@district.org' in csv, csv[:120])
        await ad.click('#tab-p'); await ad.wait_for_timeout(300)
        ptxt = await ad.inner_text('#lead-table')
        check('incomplete tab shows the consented partial lead only', 'pat@district.org' in ptxt and 'jane@district.org' not in ptxt and 'nora@' not in ptxt, ptxt[:200])
        async with ad.expect_download() as d2:
            await ad.click('#csv')
        csv2 = open(await (await d2.value).path(), encoding='utf-8-sig').read()
        check('CSV export of incomplete leads', 'pat@district.org' in csv2 and 'notified_at' in csv2)
        await ad.screenshot(path=OUT + 'dashboard-leads.png', full_page=True)
        # reload keeps status
        await ad.reload(wait_until='networkidle'); await ad.wait_for_selector('#lead-table tr[data-id]')
        sel = await ad.locator(f'#lead-table tr[data-id="{lid}"] select').input_value()
        check('status persists after reload', sel == 'Contacted', sel)
        # mobile
        mob = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1')
        cookies = await ctx.cookies(); await mob.add_cookies(cookies)
        mp = await mob.new_page(); await mp.route(lambda url: not url.startswith(BASE), route)
        await mp.goto(BASE + '/admin', wait_until='networkidle'); await mp.wait_for_selector('.kpi'); await mp.wait_for_timeout(500)
        wide = await mp.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        check('dashboard fits a phone screen (no sideways scroll)', wide)
        await mp.screenshot(path=OUT + 'dashboard-mobile.png', full_page=True)
        # signed-out access refused
        anon = await b.new_context(); ap = await anon.new_page()
        r = await ap.request.get(BASE + '/api/admin?action=data')
        check('dashboard data refused without sign-in', r.status == 401)
        bot = urllib.request.Request(BASE + '/api/beat', data=json.dumps({'visitor_id': 'vbot12345678', 'events': [{'name': 'page_view', 'page': '/bot'}]}).encode(), headers={'Origin': BASE, 'User-Agent': 'Googlebot/2.1', 'Content-Type': 'text/plain'})
        urllib.request.urlopen(bot).read()
        check('bot traffic is not counted', not any(e['Page'] == '/bot' for e in rows('Website events')))
        check('no page script errors', not errors, errors[:3])
        await b.close()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)

asyncio.run(main())
