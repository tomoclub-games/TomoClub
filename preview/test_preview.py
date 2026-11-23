"""Clicks through the preview in headless Chrome. window.claude is replaced by a
TEST stand-in (literal word-overlap 'model' and an in-memory store) because the
real Claude and database capabilities exist only on claude.ai."""
import os, sys, subprocess, time
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, 'dist')
FIX = os.path.join(HERE, '..', 'test', 'fixtures')
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/preview-shots'
os.makedirs(OUT, exist_ok=True)

STAND_IN = r"""
(() => {
  const STOP = new Set('a an and are as at be by can do does for from has have how i if in is it its me my of on or our should the their this to was we what when where which who why will with you your about school district child student students'.split(' '));
  const words = (s) => (s.toLowerCase().match(/[a-z0-9]+/g) || []).filter((w) => w.length > 2 && !STOP.has(w));
  const stem = (w) => w.replace(/(ing|ed|es|s)$/, '');
  window.__calls = [];
  const sample = async (input, opts) => {
    window.__calls.push({ input, opts });
    if (/search keywords/i.test(input)) return { text: JSON.stringify({ terms: words(input.split('Question:').pop()) }) };
    const question = input.split('QUESTION:').pop();
    const q = new Set(words(question).map(stem));
    const src = input.split('QUESTION:')[0].split('=====').pop();
    const blocks = src.split(/\n(?=\[S\d+\] )/).filter((b) => /^\[S\d+\]/.test(b));
    let best = { score: 0 };
    for (const b of blocks) {
      const id = b.match(/^\[S(\d+)\]/)[1];
      for (const s of b.split('\n').slice(2).join(' ').split(/(?<=[.!?])\s+/)) {
        const score = new Set(words(s).map(stem).filter((w) => q.has(w))).size;
        if (score > best.score) best = { score, id, s: s.trim() };
      }
    }
    return { text: best.score >= 2 ? JSON.stringify({ found: true, answer: best.s + ' [S' + best.id + ']' }) : JSON.stringify({ found: false, answer: '' }) };
  };
  const store = [];
  const db = {
    collection: (p) => ({
      add: async (data) => { store.push({ path: p, data }); return { id: String(store.length) }; },
      orderBy: () => ({ limit: () => ({ get: async () => ({ docs: store.slice().reverse().map((x) => ({ data: () => x.data })) }) }) }),
    }),
  };
  window.claude = { use: (name) => Promise.resolve(name === 'sample' ? sample : name === 'db' ? db : null) };
})();
"""

server = subprocess.Popen([sys.executable, '-m', 'http.server', '4950', '--bind', '127.0.0.1'], cwd=DIST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
fails = []
def check(name, cond):
    print(('PASS ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
try:
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        ctx = br.new_context(viewport={'width': 1360, 'height': 900})
        ctx.add_init_script(STAND_IN)
        pg = ctx.new_page()
        errors = []
        pg.on('pageerror', lambda e: errors.append(str(e)))
        pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        pg.goto('http://127.0.0.1:4950/index.html')
        pg.wait_for_timeout(800)
        pg.screenshot(path=f'{OUT}/p1-start.png')

        # Live URL -> clear preview limit message
        pg.fill('#district-url', 'www.fcps.edu')
        pg.click('#url-form button[type=submit]')
        pg.wait_for_selector('#url-error:not([hidden])', timeout=5000)
        check('other URL explains it needs deployment', 'deployed server' in pg.inner_text('#url-error'))

        # Saved district replay
        pg.click('[data-try="www.riverbend-usd.example"]')
        pg.wait_for_selector('#processing:not([hidden])', timeout=5000)
        pg.wait_for_timeout(2200)
        pg.screenshot(path=f'{OUT}/p2-processing.png')
        pg.wait_for_selector('#workspace:not([hidden])', timeout=20000)
        check('district name shown', pg.inner_text('#district-name') == 'Riverbend Unified School District')
        check('categories shown', pg.locator('#categories .chip').count() >= 5)
        check('read list has 7', 'Read (7)' in pg.inner_text('#tab-read'))
        check('not-read list has 6', 'Not read (6)' in pg.inner_text('#tab-notread'))

        def ask(q):
            n = pg.locator('.msg-bot, .msg-error').count()
            pg.fill('#question', q)
            pg.click('#ask-form button')
            pg.wait_for_function(f"document.querySelectorAll('.msg-bot, .msg-error').length > {n}", timeout=15000)
            return pg.locator('.msg-bot, .msg-error').last.inner_text()

        a = ask('What is the cell phone policy during class?')
        check('phone answer cites handbook page 3', 'page 3' in a and 'main office' in a)
        a = ask('When is winter break?')
        check('winter break answer from calendar', 'December 21, 2026' in a and 'District Calendar' in a)
        a = ask("What is the superintendent's salary?")
        check('not-found reply is exact', a.strip() == "I couldn't find this information in the available district resources.")
        pg.screenshot(path=f'{OUT}/p3-chat.png')

        # Source viewer for fictional links
        pg.locator('.msg-sources a').first.click()
        pg.wait_for_selector('#src-modal:not([hidden])', timeout=3000)
        check('source viewer shows saved text', 'main office' in pg.inner_text('#src-body') and 'page 3' in pg.inner_text('#src-meta'))
        pg.screenshot(path=f'{OUT}/p4-source.png')
        pg.click('#src-close')

        # Upload into this district
        pg.set_input_files('#upload-form input[type=file]', [os.path.join(FIX, 'upload-transport-guide.pdf'), os.path.join(FIX, 'riverbend/docs/immunization-requirements-scan.pdf')])
        pg.click('#upload-form button')
        pg.wait_for_function("document.querySelector('.upload-result').textContent.includes('pages read')", timeout=30000)
        res = pg.inner_text('.upload-result')
        check('text PDF read and scanned PDF flagged', '1 of 2 pages read' in res and 'scanned' in res)
        a = ask('Is breakfast and lunch free for every student?')
        check('answer from uploaded PDF with page', 'page 2' in a and 'uploaded' in a)

        # Upload-only district
        pg.click('#new-district')
        pg.click('#show-upload-only')
        pg.fill('#upload-only-form [name=name]', 'Hillcrest Schools')
        pg.set_input_files('#upload-only-form [name=files]', os.path.join(FIX, 'upload-transport-guide.pdf'))
        pg.click('#upload-only-form button[type=submit]')
        pg.wait_for_selector('#workspace:not([hidden])', timeout=30000)
        check('upload-only district opens', pg.inner_text('#district-name') == 'Hillcrest Schools')
        a = ask('Are school meals free for every Hillcrest student?')
        check('upload-only district answers', 'Community Eligibility' in a)
        a = ask('When is winter break?')
        check('no mixing with Riverbend', a.strip() == "I couldn't find this information in the available district resources.")

        # Lead form
        pg.locator('#request').scroll_into_view_if_needed()
        pg.fill('[name=fullName]', 'Test Person')
        pg.fill('[name=workEmail]', 'test@exampledistrict.org')
        pg.fill('[name=jobTitle]', 'Superintendent')
        pg.fill('[name=district]', 'Example District')
        pg.fill('[name=problem]', 'Families ask the same calendar questions every week.')
        pg.click('#lead-form button[type=submit]')
        pg.wait_for_selector('#lead-form .form-error:not([hidden])', timeout=5000)
        check('too-fast submit refused', 'moment' in pg.inner_text('#lead-form .form-error'))
        pg.wait_for_timeout(3200)
        pg.click('#lead-form button[type=submit]')
        pg.wait_for_selector('#lead-thanks:not([hidden])', timeout=5000)
        check('lead saved', True)
        pg.click('#load-leads')
        pg.wait_for_function("document.querySelector('#leads-status').textContent.includes('saved request')", timeout=5000)
        check('saved request listed', 'test@exampledistrict.org' in pg.inner_text('#leads-table'))
        pg.locator('#request').screenshot(path=f'{OUT}/p5-lead.png')
        pg.locator('#preview-leads').screenshot(path=f'{OUT}/p6-saved-leads.png')

        m = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2)
        m.add_init_script(STAND_IN)
        mp = m.new_page()
        mp.goto('http://127.0.0.1:4950/index.html')
        mp.wait_for_timeout(600)
        mp.screenshot(path=f'{OUT}/p7-mobile.png')
        check('no page errors', not errors)
        if errors: print(errors)
        br.close()
finally:
    server.terminate()
print(f"\n{'ALL PASS' if not fails else str(len(fails)) + ' FAILED'}")
