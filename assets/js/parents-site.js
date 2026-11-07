/* TomoClub site settings.
   sheetEndpoint: paste the Web app URL of your Google Apps Script collector (set up with data-capture/Code.gs).
   Leave it empty and the site still works; data just isn't saved to the sheet.
   logClicksToSheet: also write every click/event to the "Events" tab (set false to send only form data). */
window.TOMO_CONFIG = {
  sheetEndpoint: '',
  logClicksToSheet: true
};

/* TomoClub parents site: shared behaviour (tracking, booking, enrolment, picker, FAQ). No dependencies. */
(function () {
  'use strict';
  var INK = '#0B1230', MUTED = '#4A5372', TEAL = '#0E8A8E';
  var PAGE = document.body.getAttribute('data-page') || 'home';
  var DEBUG = /[?&]debug=1/.test(location.search);
  var logBox = null;

  function esc(v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  /* ---------- config, visitor and session context ---------- */
  var CONFIG = Object.assign({ sheetEndpoint: '', logClicksToSheet: true }, window.TOMO_CONFIG || {});
  function store(kind, key, val) { try { var st = kind === 'local' ? localStorage : sessionStorage; if (val === undefined) return st.getItem(key); st.setItem(key, val); } catch (e) { return null; } }
  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 8); }
  var VISITOR = store('local', 'tomo_vid') || (function () { var v = uid(); store('local', 'tomo_vid', v); return v; })();
  var SESSION = store('session', 'tomo_sid') || (function () { var v = uid(); store('session', 'tomo_sid', v); return v; })();
  var ATTR = (function () {
    var saved = store('session', 'tomo_attr');
    if (saved) { try { return JSON.parse(saved); } catch (e) {} }
    var q = new URLSearchParams(location.search), a = {};
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'].forEach(function (k) { if (q.get(k)) a[k] = q.get(k); });
    a.referrer = document.referrer || ''; a.landing_page = location.pathname + location.search;
    store('session', 'tomo_attr', JSON.stringify(a));
    return a;
  })();
  function ctx() { return Object.assign({ timestamp: new Date().toISOString(), session_id: SESSION, visitor_id: VISITOR }, ATTR); }

  /* ---------- sending rows to the sheet collector ---------- */
  var queue = [];
  function post(rows, beacon) {
    if (!CONFIG.sheetEndpoint || !rows.length) return;
    var body = JSON.stringify({ rows: rows });
    if (beacon && navigator.sendBeacon) { navigator.sendBeacon(CONFIG.sheetEndpoint, new Blob([body], { type: 'text/plain;charset=utf-8' })); return; }
    try { fetch(CONFIG.sheetEndpoint, { method: 'POST', mode: 'no-cors', keepalive: true, headers: { 'Content-Type': 'text/plain;charset=utf-8' }, body: body }); } catch (e) {}
  }
  function flush(beacon) { if (queue.length) { post(queue.splice(0, queue.length), beacon); } }
  setInterval(function () { flush(false); }, 4000);
  window.addEventListener('pagehide', function () { flush(true); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') flush(true); });
  /* a submitted form: saved straight away as one row in the named sheet */
  function saveRecord(sheet, data) {
    var row = Object.assign(ctx(), { page: PAGE }, data);
    post([{ sheet: sheet, data: row }], false);
    if (DEBUG) showLog({ event: 'saved to sheet: ' + sheet });
  }
  window.tomoSaveRecord = saveRecord;

  /* ---------- tracking ---------- */
  var KNOWN = ['event', 'page', 'cta_location', 'label', 'program', 'grade'];
  function track(name, params) {
    params = params || {};
    var payload = { event: name, page: PAGE, session_id: SESSION, visitor_id: VISITOR };
    Object.keys(ATTR).forEach(function (k) { if (k.indexOf('utm_') === 0 && ATTR[k]) payload[k] = ATTR[k]; });
    Object.keys(params).forEach(function (k) { if (params[k] !== undefined && params[k] !== null && params[k] !== '') payload[k] = params[k]; });
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(payload);
    if (DEBUG) showLog(payload);
    if (CONFIG.logClicksToSheet) {
      var details = {};
      Object.keys(params).forEach(function (k) { if (KNOWN.indexOf(k) < 0 && k !== 'ecommerce' && params[k] !== undefined && params[k] !== '') details[k] = params[k]; });
      if (params.ecommerce) details.value = params.ecommerce.value;
      queue.push({ sheet: 'Events', data: Object.assign(ctx(), { event: name, page: PAGE, cta_location: params.cta_location || '', label: params.label || '', program: params.program || '', grade: params.grade || '', details: Object.keys(details).length ? JSON.stringify(details) : '', path: location.pathname }) });
      if (queue.length >= 10) flush(false);
    }
  }
  window.tomoTrack = track;
  function showLog(p) {
    if (!logBox) {
      logBox = document.createElement('div');
      logBox.setAttribute('aria-hidden', 'true');
      logBox.style.cssText = 'position:fixed;left:16px;bottom:16px;z-index:99;width:360px;max-height:50vh;overflow:auto;background:#070C22;color:#8EE3E5;border-radius:14px;padding:12px 14px;font:12px/1.5 ui-monospace,Menlo,monospace;box-shadow:0 10px 30px rgba(0,0,0,.35)';
      document.body.appendChild(logBox);
    }
    var line = document.createElement('div');
    line.textContent = Object.keys(p).filter(function (k) { return ['ecommerce', 'session_id', 'visitor_id', 'page'].indexOf(k) < 0 && k.indexOf('utm_') !== 0; }).map(function (k) { return k === 'event' ? p[k] : k + '=' + p[k]; }).join(' ');
    logBox.insertBefore(line, logBox.firstChild);
    while (logBox.children.length > 10) logBox.removeChild(logBox.lastChild);
  }
  function labelOf(el) { return (el.getAttribute('aria-label') || el.textContent || el.getAttribute('title') || '').replace(/\s+/g, ' ').trim().slice(0, 80); }
  function sectionOf(el) {
    var s = el.closest('section, header, footer, nav, [role=dialog]');
    if (!s) return 'page';
    var lb = s.getAttribute('aria-labelledby');
    return (lb ? lb.replace(/-title$/, '') : '') || s.id || (s.getAttribute('aria-label') || '').toLowerCase().replace(/\s+/g, '_') || s.tagName.toLowerCase();
  }

  /* every link and button click is captured. Elements with data-event use that name; the rest are
     recorded as link_click / button_click with their text and section. Booking, enrolment, picker and
     newsletter components send their own specific events (marked data-self-tracked). */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('a, button, [role=button]');
    if (el && !el.closest('[data-self-tracked]') && !el.hasAttribute('data-faq-tab')) {
      var href = el.getAttribute('href') || '';
      var base = { cta_location: el.getAttribute('data-location') || sectionOf(el), program: el.getAttribute('data-program') || '', label: labelOf(el), href: href || undefined };
      if (href && /^https?:/i.test(href) && href.indexOf(location.host) < 0) base.outbound = true;
      if (/^tel:/.test(href)) base.contact = 'phone';
      if (/^mailto:/.test(href)) base.contact = 'email';
      var name = el.getAttribute('data-event') || (el.tagName === 'A' ? 'link_click' : 'button_click');
      track(name, base);
    }
    var sc = e.target.closest('[data-scroll-to]');
    if (sc) {
      var target = document.getElementById(sc.getAttribute('data-scroll-to'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    }
  }, true); /* capture phase: runs before components re-render, so self-tracked buttons are recognised */
  document.addEventListener('toggle', function (e) {
    var d = e.target;
    if (d && d.tagName === 'DETAILS' && d.open && d.getAttribute('data-question')) track('faq_open', { cta_location: sectionOf(d), question: d.getAttribute('data-question'), label: d.getAttribute('data-question') });
  }, true);
  /* first interaction with any form */
  var started = {};
  document.addEventListener('focusin', function (e) {
    var f = e.target.closest('[data-booking], [data-enrol], [data-newsletter]');
    if (!f || !/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
    var k = f.hasAttribute('data-booking') ? 'trial_booking' : (f.hasAttribute('data-enrol') ? 'enrolment' : 'newsletter');
    if (!started[k]) { started[k] = true; track('form_start', { cta_location: k, form: k }); }
  });
  /* scroll depth and section views */
  var depths = [25, 50, 75, 100], hit = {};
  window.addEventListener('scroll', function () {
    var h = document.documentElement, pct = Math.round((h.scrollTop + window.innerHeight) / h.scrollHeight * 100);
    depths.forEach(function (d) { if (pct >= d && !hit[d]) { hit[d] = true; track('scroll_depth', { percent: d }); } });
  }, { passive: true });
  function initSectionViews() {
    if (!('IntersectionObserver' in window)) return;
    var seen = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var id = sectionOf(en.target);
        if (!seen[id]) { seen[id] = true; track('section_view', { cta_location: id }); }
      });
    }, { threshold: 0.4 });
    document.querySelectorAll('main section').forEach(function (s) { io.observe(s); });
  }

  /* ---------- modal helper ---------- */
  function modal(html, z) {
    var wrap = document.createElement('div');
    wrap.setAttribute('data-self-tracked', '');
    wrap.style.cssText = 'position:fixed;inset:0;z-index:' + (z || 60) + ';background:rgba(11,18,48,.6);display:flex;align-items:center;justify-content:center;padding:20px';
    wrap.innerHTML = html;
    document.body.appendChild(wrap);
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    function onKey(e) { if (e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);
    function close() { document.removeEventListener('keydown', onKey); if (wrap.parentNode) wrap.parentNode.removeChild(wrap); }
    var first = wrap.querySelector('button, a, input'); if (first) first.focus();
    return { el: wrap, close: close };
  }

  var pillOn = 'background:#0B1230;color:#FFFFFF;border:2px solid #0B1230';
  var pillOff = 'background:#FFFFFF;color:#0B1230;border:2px solid #CDD3E1';

  /* ---------- homepage: booking picker (grade first, then eligible programs) ---------- */
  function initPicker() {
    var triggers = document.querySelectorAll('[data-open-picker]');
    if (!triggers.length) return;
    var PROGS = {
      life_skills: { name: 'Tomo Life Skills', line: 'Confidence, speaking up and teamwork', color: '#FF6F4F', href: '/life-skills' },
      ai_lab: { name: 'Tomo AI Lab', line: 'Smart, safe and creative with AI', color: '#7B6CF6', href: '/ai-lab' },
      bundle: { name: 'Both programs', line: 'Life Skills and AI Lab, 8 classes a month', color: '#FFC83D', href: '/both-programs' }
    };
    function open(intent) {
      var m = modal('<div role="dialog" aria-modal="true" aria-labelledby="picker-title" style="width:min(500px,100%);background:#FFFFFF;border-radius:28px;padding:28px;box-sizing:border-box;display:flex;flex-direction:column;gap:18px;box-shadow:0 30px 80px rgba(0,0,0,.35);font-family:Outfit,system-ui,sans-serif;color:#0B1230" data-picker></div>', 50);
      var box = m.el.querySelector('[data-picker]');
      function head(step, title) {
        return '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px"><div style="display:flex;flex-direction:column;gap:4px"><span style="font-size:13px;font-weight:600;color:' + MUTED + '">' + step + '</span><h2 id="picker-title" style="margin:0;font-weight:700;font-size:25px;line-height:1.2">' + title + '</h2></div><button type="button" aria-label="Close" data-close style="flex-shrink:0;width:44px;height:44px;border-radius:50%;border:0;background:#F1F3F9;font-size:22px;cursor:pointer;color:#0B1230">&times;</button></div>';
      }
      function gradeStep() {
        box.innerHTML = head('Step 1 of 2', 'What grade is your child in?') + '<div style="display:flex;flex-direction:column;gap:10px">' +
          [['3-5', 'Grades 3 to 5'], ['6-8', 'Grades 6 to 8'], ['9-12', 'Grades 9 to 12']].map(function (g) {
            return '<button type="button" data-grade="' + g[0] + '" style="font:inherit;font-weight:600;font-size:18px;text-align:left;padding:16px 20px;min-height:56px;border-radius:16px;border:2px solid #E3E6EF;background:#FFFFFF;color:#0B1230;cursor:pointer">' + g[1] + '</button>';
          }).join('') + '</div>';
      }
      function programStep(g) {
        var opts = g === '3-5' ? ['life_skills'] : ['life_skills', 'ai_lab'];
        if (intent && opts.indexOf(intent) > -1) opts = [intent].concat(opts.filter(function (o) { return o !== intent; }));
        box.innerHTML = head('Step 2 of 2', 'Which class should your child try?') + '<div style="display:flex;flex-direction:column;gap:10px">' +
          opts.map(function (k) {
            var p = PROGS[k];
            return '<a href="' + p.href + '?grade=' + g + '" data-program-link="' + k + '" style="display:flex;align-items:center;gap:14px;padding:16px 18px;border:2px solid #E3E6EF;border-radius:18px;text-decoration:none;color:#0B1230;background:#FFFFFF"><span aria-hidden="true" style="flex-shrink:0;width:14px;align-self:stretch;border-radius:8px;background:' + p.color + '"></span><span style="flex-grow:1"><strong style="font-size:19px">' + p.name + '</strong><br><span style="color:' + MUTED + ';font-size:15px">' + p.line + '</span></span><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="#0B1230" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></a>';
          }).join('') +
          (g === '3-5' ? '<p style="margin:0;font-size:14px;color:' + MUTED + '">Tomo AI Lab starts at Grade 6.</p>' : '') +
          '<button type="button" data-back style="align-self:flex-start;font:inherit;font-weight:600;font-size:15px;background:none;border:0;padding:8px 0;color:' + TEAL + ';cursor:pointer;text-decoration:underline">Change grade</button></div>';
      }
      box.addEventListener('click', function (e) {
        var t = e.target.closest('[data-grade],[data-back],[data-close],[data-program-link]');
        if (!t) return;
        if (t.hasAttribute('data-close')) { track('picker_close', { cta_location: 'picker' }); m.close(); }
        else if (t.hasAttribute('data-back')) { track('grade_change', { cta_location: 'picker' }); gradeStep(); }
        else if (t.hasAttribute('data-grade')) { var g = t.getAttribute('data-grade'); track('grade_select', { cta_location: 'picker', grade: g }); programStep(g); }
        else if (t.hasAttribute('data-program-link')) { track('program_select', { cta_location: 'picker', program: t.getAttribute('data-program-link') }); }
      });
      gradeStep();
    }
    triggers.forEach(function (b) { b.addEventListener('click', function () { open(b.getAttribute('data-program')); }); });
  }

  /* ---------- FAQ topic tabs ---------- */
  function initFaqTabs() {
    var tabs = document.querySelectorAll('[data-faq-tab]');
    if (!tabs.length) return;
    function select(k) {
      tabs.forEach(function (t) {
        var on = t.getAttribute('data-faq-tab') === k;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.style.background = on ? INK : '#FFFFFF'; t.style.color = on ? '#FFFFFF' : INK; t.style.borderColor = on ? INK : '#D5DAE6';
      });
      document.querySelectorAll('[data-faq-panel]').forEach(function (p) { p.style.display = p.getAttribute('data-faq-panel') === k ? 'block' : 'none'; });
    }
    tabs.forEach(function (t) { t.addEventListener('click', function () { track('faq_tab', { cta_location: 'faq', tab: t.getAttribute('data-faq-tab') }); select(t.getAttribute('data-faq-tab')); }); });
  }

  /* ---------- newsletter (footer) ---------- */
  function initNewsletter() {
    var f = document.querySelector('[data-newsletter]');
    if (!f) return;
    var email = f.querySelector('[name=email]'), nl = f.querySelector('[name=nl]'), wa = f.querySelector('[name=wa]'), phone = f.querySelector('[name=phone]'), btn = f.querySelector('button'), msg = f.querySelector('[data-sent]');
    function valid() {
      var okEmail = /\S+@\S+\.\S+/.test(email.value), okPhone = phone.value.replace(/\D/g, '').length >= 8;
      phone.style.display = wa.checked ? 'block' : 'none';
      btn.disabled = !(okEmail && nl.checked && (!wa.checked || okPhone));
    }
    f.addEventListener('input', valid); f.addEventListener('change', function (e) { valid(); if (e.target.type === 'checkbox') track('consent_toggle', { cta_location: 'footer', consent: e.target.name === 'nl' ? 'email' : 'whatsapp', checked: e.target.checked }); }); valid();
    f.addEventListener('submit', function (e) {
      e.preventDefault(); if (btn.disabled) return;
      track('newsletter_signup', { cta_location: 'footer', channel: wa.checked ? 'email+whatsapp' : 'email' });
      saveRecord('Newsletter', { email: email.value.trim(), email_consent: nl.checked ? 'yes' : 'no', whatsapp: wa.checked ? phone.value.trim() : '', whatsapp_consent: wa.checked ? 'yes' : 'no' });
      msg.style.display = 'block';
    });
  }

  /* ---------- shared form bits ---------- */
  var COUNTRIES = ['India', 'United States', 'United Arab Emirates', 'United Kingdom', 'Canada', 'Singapore', 'Australia', 'Other'];
  function field(label, html) { return '<label style="display:flex;flex-direction:column;gap:6px"><span class="lbl">' + label + '</span>' + html + '</label>'; }
  function input(name, type, ac, ph, val) { return '<input class="field" name="' + name + '" type="' + type + '" autocomplete="' + ac + '" placeholder="' + esc(ph) + '" value="' + esc(val) + '">'; }
  function select(name, first, opts, val) { return '<select class="field" name="' + name + '"><option value="">' + first + '</option>' + opts.map(function (o) { var v = Array.isArray(o) ? o[0] : o, l = Array.isArray(o) ? o[1] : o; return '<option value="' + esc(v) + '"' + (String(val) === String(v) ? ' selected' : '') + '>' + esc(l) + '</option>'; }).join('') + '</select>'; }
  function dots(step, labels) {
    return '<div style="display:flex;align-items:center;gap:8px">' + labels.map(function (l, i) {
      var n = i + 1, on = step >= n, c = on ? INK : '#A3ABC2';
      return (i ? '<span aria-hidden="true" style="flex:1;height:2px;background:' + (on ? INK : '#E3E6EF') + ';border-radius:2px"></span>' : '') +
        '<span style="display:inline-flex;align-items:center;gap:8px;font-size:14px;font-weight:600;color:' + (on ? INK : '#7A839C') + '"><span style="width:26px;height:26px;border-radius:50%;background:' + c + ';color:#FFFFFF;font-size:13px;display:inline-flex;align-items:center;justify-content:center">' + n + '</span>' + l + '</span>';
    }).join('') + '</div>';
  }
  var BTN_MAIN = 'font:inherit;font-weight:700;font-size:18px;background:#FFC83D;color:#0B1230;border:0;border-radius:999px;min-height:56px;padding:14px 24px;cursor:pointer;box-shadow:0 0 0 6px rgba(255,200,61,.25)';
  var BTN_BACK = 'font:inherit;font-weight:700;background:#FFFFFF;color:#0B1230;border:2px solid #CDD3E1;border-radius:999px;min-height:56px;padding:12px 20px;cursor:pointer';
  function validEmail(v) { return /\S+@\S+\.\S+/.test(v || ''); }
  function tzLabel(country) { return !country || country === 'India' ? 'IST' : 'your local time'; }
  var MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  /* ---------- program pages: free trial booking (details, then calendar) ---------- */
  function initBooking(card) {
    var urlGrade = (location.search.match(/grade=([0-9-]+)/) || [])[1];
    var S = { step: 1, name: '', email: '', phone: '', country: '', city: '', grade: '', program: card.getAttribute('data-default-program') || 'life_skills', month: 0, date: null, dateLabel: '', wd: null, slot: null, waOk: false };
    if (urlGrade) { var gmin = parseInt(urlGrade, 10); if (gmin >= 3 && gmin <= 12) S.grade = String(gmin); }
    function eff() { var g = Number(S.grade || 0); return S.program === 'ai_lab' && g && g < 6 ? 'life_skills' : S.program; }
    function detailsOk() { return !!(S.name.trim() && validEmail(S.email) && S.grade && S.country && S.city.trim()); }
    function render() {
      var step2 = S.step === 2 && detailsOk();
      var h = '<div style="display:flex;flex-direction:column;gap:10px"><h2 style="margin:0;font-weight:700;font-size:24px;letter-spacing:-0.01em">Book a free trial class</h2>' + dots(step2 ? 2 : 1, ['Your details', 'Date and time']) + '</div>';
      if (!step2) {
        var g = Number(S.grade || 0), p = eff(), aiOff = g && g < 6;
        var pb = function (k, label) { return '<button type="button" data-prog="' + k + '" aria-pressed="' + (p === k) + '"' + (k === 'ai_lab' && aiOff ? ' disabled' : '') + ' style="font:inherit;font-weight:600;min-height:48px;padding:10px 14px;border-radius:14px;cursor:pointer;' + (p === k ? pillOn : pillOff) + '">' + label + '</button>'; };
        h += '<div style="display:flex;flex-direction:column;gap:14px"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(200px,100%),1fr));gap:12px 14px">' +
          field('Parent&#39;s name', input('name', 'text', 'name', 'Your full name', S.name)) +
          field('Child&#39;s grade', select('grade', 'Select grade', [3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(function (x) { return [x, 'Grade ' + x]; }), S.grade)) +
          field('Email', input('email', 'email', 'email', 'For the class link', S.email)) +
          field('WhatsApp number', input('phone', 'tel', 'tel', 'With country code', S.phone)) +
          field('Country', select('country', 'Select country', COUNTRIES, S.country)) +
          field('City', input('city', 'text', 'address-level2', 'e.g. Bengaluru', S.city)) +
          '</div><fieldset style="border:0;margin:0;padding:0;display:flex;flex-direction:column;gap:8px"><legend class="lbl" style="padding:0;margin-bottom:8px">Program for the trial</legend><div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">' + pb('life_skills', 'Tomo Life Skills') + pb('ai_lab', 'Tomo AI Lab') + '</div>' +
          (aiOff ? '<p style="margin:0;font-size:14px;color:' + MUTED + '">Tomo AI Lab starts at Grade 6' + (card.getAttribute('data-default-program') === 'ai_lab' ? ', so we&#39;ve picked Tomo Life Skills for Grades 3 to 5' : '') + '.</p>' : '') +
          '</fieldset><button type="button" data-next' + (detailsOk() ? '' : ' disabled') + ' style="' + BTN_MAIN + '">Next: pick a date and time</button><p style="margin:0;font-size:13px;color:' + MUTED + ';text-align:center">Free, with no obligation to continue. <a href="https://www.tomoclub.org/privacy-policy">Privacy policy</a></p></div>';
      } else {
        var today = new Date(); today.setHours(0, 0, 0, 0);
        var first = new Date(today.getFullYear(), today.getMonth() + S.month, 1);
        var last = new Date(today.getTime() + 30 * 86400000);
        var days = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate(), lead = (first.getDay() + 6) % 7;
        var cells = '';
        for (var k = 0; k < lead; k++) cells += '<span></span>';
        for (var d = 1; d <= days; d++) {
          var dt = new Date(first.getFullYear(), first.getMonth(), d), key = dt.getFullYear() + '-' + (dt.getMonth() + 1) + '-' + d;
          var avail = dt > today && dt <= last && dt.getDay() !== 0, sel = S.date === key;
          var st = sel ? 'background:#0B1230;color:#FFFFFF;border:1.5px solid #0B1230;font-weight:700' : (avail ? 'background:#FFF1EC;color:#B23A20;border:1.5px solid #FFD4C7;font-weight:700' : 'background:#FFFFFF;color:#A3ABC2;border:1.5px solid #FFFFFF');
          var lbl = DOW[dt.getDay()] + ' ' + d + ' ' + MON[dt.getMonth()].slice(0, 3);
          cells += '<button type="button" data-date="' + key + '" data-label="' + lbl + '" data-wd="' + dt.getDay() + '" aria-pressed="' + sel + '" aria-label="' + lbl + (avail ? ', available' : ', unavailable') + '"' + (avail ? '' : ' disabled') + ' style="font:inherit;font-size:15px;height:40px;border-radius:12px;cursor:pointer;' + st + '">' + d + '</button>';
        }
        var times = S.date ? (S.wd === 6 ? ['10:00 AM', '11:30 AM', '4:00 PM', '5:30 PM'] : ['5:00 PM', '6:00 PM', '7:00 PM']) : [];
        var navBtn = function (dir, dis, sym, lab) { return '<button type="button" data-month="' + dir + '" aria-label="' + lab + '"' + (dis ? ' disabled' : '') + ' style="font:inherit;width:40px;height:40px;border-radius:50%;border:1.5px solid #CDD3E1;background:#FFFFFF;cursor:pointer;font-size:18px;color:#0B1230">' + sym + '</button>'; };
        h += '<div style="display:flex;flex-direction:column;gap:14px"><div style="display:flex;align-items:center;justify-content:space-between;gap:10px">' + navBtn(-1, S.month <= 0, '&lsaquo;', 'Previous month') + '<strong style="font-size:18px">' + MON[first.getMonth()] + ' ' + first.getFullYear() + '</strong>' + navBtn(1, S.month >= 1, '&rsaquo;', 'Next month') + '</div>' +
          '<div role="grid" aria-label="Calendar" style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px;text-align:center">' + ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(function (x) { return '<span style="font-size:12px;font-weight:600;color:' + MUTED + '">' + x + '</span>'; }).join('') + cells + '</div>' +
          (S.date ? '<div style="display:flex;flex-direction:column;gap:8px"><span style="font-size:14px;color:' + MUTED + '">Times on ' + esc(S.dateLabel) + ' (' + tzLabel(S.country) + ')</span><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px">' + times.map(function (t) { return '<button type="button" data-slot="' + t + '" aria-pressed="' + (S.slot === t) + '" style="font:inherit;font-weight:600;min-height:44px;border-radius:12px;cursor:pointer;' + (S.slot === t ? pillOn : pillOff) + '">' + t + '</button>'; }).join('') + '</div></div>' : '<p style="margin:0;font-size:14px;color:' + MUTED + '">Pick a highlighted date to see available times.</p>') +
          '<label style="display:flex;gap:10px;align-items:flex-start;font-size:14px;cursor:pointer"><input type="checkbox" name="waOk"' + (S.waOk ? ' checked' : '') + ' style="width:18px;height:18px;margin:2px 0 0;accent-color:' + TEAL + ';flex-shrink:0"><span>Send class reminders to my WhatsApp.</span></label>' +
          '<div style="display:flex;gap:10px"><button type="button" data-back style="' + BTN_BACK + '">Back</button><button type="button" data-book' + (S.date && S.slot ? '' : ' disabled') + ' style="flex:1;' + BTN_MAIN + ';font-size:18px">Book free trial class now</button></div>' +
          '<p style="margin:0;font-size:12px;color:' + MUTED + ';text-align:center">Live availability via Calendly. Your details are filled in for you.</p></div>';
      }
      card.innerHTML = h;
    }
    card.addEventListener('input', function (e) {
      var n = e.target.name; if (!n || n === 'waOk') return;
      S[n] = e.target.value;
      var nb = card.querySelector('[data-next]'); if (nb) nb.disabled = !detailsOk();
    });
    card.addEventListener('change', function (e) {
      var n = e.target.name;
      if (n === 'grade') { S.grade = e.target.value; track('grade_select', { cta_location: 'booking', grade: S.grade }); render(); }
      else if (n === 'country') { S.country = e.target.value; track('country_select', { cta_location: 'booking', country: S.country }); var nb = card.querySelector('[data-next]'); if (nb) nb.disabled = !detailsOk(); }
      else if (n === 'waOk') { S.waOk = e.target.checked; track('whatsapp_reminder_toggle', { cta_location: 'booking', checked: S.waOk }); }
    });
    card.addEventListener('click', function (e) {
      var t = e.target.closest('button'); if (!t || t.disabled) return;
      if (t.hasAttribute('data-prog')) { S.program = t.getAttribute('data-prog'); track('program_change', { cta_location: 'booking', program: S.program }); render(); }
      else if (t.hasAttribute('data-next')) { track('lead_submitted', { cta_location: 'booking', program: eff(), grade: S.grade, country: S.country, city: S.city.trim() }); saveRecord('Leads', { program: eff(), parent_name: S.name.trim(), email: S.email.trim(), whatsapp: S.phone.trim(), country: S.country, city: S.city.trim(), grade: S.grade }); S.step = 2; render(); }
      else if (t.hasAttribute('data-back')) { track('booking_back', { cta_location: 'booking' }); S.step = 1; render(); }
      else if (t.hasAttribute('data-month')) { S.month = Math.max(0, Math.min(1, S.month + Number(t.getAttribute('data-month')))); track('month_change', { cta_location: 'booking' }); render(); }
      else if (t.hasAttribute('data-date')) { S.date = t.getAttribute('data-date'); S.dateLabel = t.getAttribute('data-label'); S.wd = Number(t.getAttribute('data-wd')); S.slot = null; track('date_select', { cta_location: 'booking', date: S.dateLabel }); render(); }
      else if (t.hasAttribute('data-slot')) { S.slot = t.getAttribute('data-slot'); track('slot_select', { cta_location: 'booking', date: S.dateLabel, time: S.slot }); render(); }
      else if (t.hasAttribute('data-book')) {
        var p = eff();
        track('booking_submit', { cta_location: 'booking', program: p, grade: S.grade, date: S.dateLabel, time: S.slot, whatsapp_optin: S.waOk });
        /* TODO (developer): create the booking via your Calendly/booking API here, passing name, email, phone, grade, country, city and program. */
        saveRecord('Trial bookings', { program: p, parent_name: S.name.trim(), email: S.email.trim(), whatsapp: S.phone.trim(), country: S.country, city: S.city.trim(), grade: S.grade, class_date: S.dateLabel, class_time: S.slot, time_zone: tzLabel(S.country), whatsapp_reminders: S.waOk ? 'yes' : 'no' });
        track('booking_confirmed', { program: p, grade: S.grade, date: S.dateLabel, time: S.slot });
        confirmBooking(p);
      }
    });
    function confirmBooking(p) {
      var pname = p === 'ai_lab' ? 'Tomo AI Lab' : 'Tomo Life Skills', first = S.name.trim().split(' ')[0];
      var m = modal('<div role="dialog" aria-modal="true" aria-labelledby="done-title" style="width:min(480px,100%);background:#FFFFFF;border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.35);font-family:Outfit,system-ui,sans-serif;color:#0B1230">' +
        '<div style="background:#FFF4F0;padding:28px 24px 10px;display:flex;justify-content:center">' + CELEBRATE + '</div>' +
        '<div style="padding:22px 28px 28px;display:flex;flex-direction:column;gap:12px;text-align:center"><h2 id="done-title" style="margin:0;font-weight:700;font-size:28px">Your booking is confirmed!</h2>' +
        '<p style="margin:0;color:' + MUTED + '">' + esc(first ? first + ', your' : 'Your') + ' child&#39;s free ' + pname + ' class is booked.</p>' +
        '<p style="margin:0;background:#F6F7FB;border-radius:14px;padding:12px 16px;font-weight:600">' + esc(S.dateLabel + ', ' + S.slot + ' ' + tzLabel(S.country)) + '</p>' +
        '<p style="margin:0;font-size:15px;color:' + MUTED + '">We&#39;ve sent the class link to ' + esc(S.email) + '. Our team will also confirm on WhatsApp.</p>' +
        '<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin-top:6px"><button type="button" data-cal style="font:inherit;font-weight:700;background:#FFFFFF;color:#0B1230;border:2px solid #0B1230;border-radius:999px;padding:12px 20px;min-height:48px;cursor:pointer">Add to calendar</button><button type="button" data-done style="font:inherit;font-weight:700;background:#FFC83D;color:#0B1230;border:0;border-radius:999px;padding:12px 24px;min-height:48px;cursor:pointer">Done</button></div></div></div>', 70);
      m.el.addEventListener('click', function (e) {
        if (e.target.closest('[data-cal]')) track('add_to_calendar', { cta_location: 'confirmation' });
        if (e.target.closest('[data-done]')) { track('confirmation_close', { cta_location: 'confirmation' }); m.close(); S.step = 1; S.date = null; S.slot = null; render(); }
      });
    }
    render();
  }

  /* ---------- both programs: enrolment and payment ---------- */
  function initEnrol(card) {
    var urlGrade = (location.search.match(/grade=([0-9-]+)/) || [])[1];
    var S = { step: 1, name: '', email: '', phone: '', country: '', city: '', grade: '', ls: null, ai: null, method: null, terms: false, waOk: false };
    if (urlGrade) { var gm = parseInt(urlGrade, 10); if (gm >= 6 && gm <= 12) S.grade = String(gm); }
    var LS = ['Mon 5:00 PM', 'Wed 6:00 PM', 'Sat 11:30 AM'], AI = ['Tue 6:00 PM', 'Thu 5:00 PM', 'Sat 4:00 PM'];
    var ECOM = { currency: 'INR', value: 4999, items: [{ item_id: 'bundle', item_name: 'Tomo Life Skills + Tomo AI Lab', price: 4999, quantity: 1 }] };
    function ok1() { return !!(S.name.trim() && validEmail(S.email) && S.grade && S.country && S.city.trim()); }
    function ok2() { return !!(S.ls && S.ai); }
    function canPay() { return ok1() && ok2() && S.method && S.terms; }
    function startLabel() { var d = new Date(), add = (8 - d.getDay()) % 7 || 7, s = new Date(d.getFullYear(), d.getMonth(), d.getDate() + add); return s.getDate() + ' ' + MON[s.getMonth()].slice(0, 3); }
    function chips(list, key) { return list.map(function (t) { return '<button type="button" data-pick="' + key + '" data-val="' + t + '" aria-pressed="' + (S[key] === t) + '" style="font:inherit;font-weight:600;font-size:15px;min-height:44px;padding:8px 14px;border-radius:12px;cursor:pointer;' + (S[key] === t ? pillOn : pillOff) + '">' + t + '</button>'; }).join(''); }
    function render() {
      var step = S.step === 3 && ok1() && ok2() ? 3 : (S.step >= 2 && ok1() ? 2 : 1);
      var h = '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px"><div><h2 style="margin:0;font-weight:700;font-size:24px">Enrol in both programs</h2><p style="margin:2px 0 0;color:' + MUTED + ';font-size:15px"><strong style="color:#0B1230;font-size:18px">&#8377;4,999</strong> per month, taxes included</p></div><span style="background:#E3F6F6;color:' + TEAL + ';font-weight:700;font-size:13px;padding:5px 10px;border-radius:999px;white-space:nowrap">Cancel any time</span></div>' + dots(step, ['Details', 'Class times', 'Pay']);
      if (step === 1) {
        h += '<div style="display:flex;flex-direction:column;gap:12px"><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(min(200px,100%),1fr));gap:10px 14px">' +
          field('Parent&#39;s name', input('name', 'text', 'name', 'Your full name', S.name)) +
          field('Child&#39;s grade', select('grade', 'Select grade', [6, 7, 8, 9, 10, 11, 12].map(function (x) { return [x, 'Grade ' + x]; }), S.grade)) +
          field('Email', input('email', 'email', 'email', 'For your receipt and schedule', S.email)) +
          field('WhatsApp number', input('phone', 'tel', 'tel', 'With country code', S.phone)) +
          field('Country', select('country', 'Select country', COUNTRIES, S.country)) +
          field('City', input('city', 'text', 'address-level2', 'e.g. Pune', S.city)) +
          '</div><p style="margin:0;font-size:13px;color:' + MUTED + '">Both programs are for Grades 6 to 12. For Grades 3 to 5, see <a href="/life-skills">Tomo Life Skills</a>.</p><button type="button" data-next1' + (ok1() ? '' : ' disabled') + ' style="' + BTN_MAIN + '">Next: choose class times</button></div>';
      } else if (step === 2) {
        h += '<div style="display:flex;flex-direction:column;gap:16px">' +
          '<div style="display:flex;flex-direction:column;gap:8px"><span class="lbl" style="display:flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:#FF6F4F"></span>Tomo Life Skills, weekly class (' + tzLabel(S.country) + ')</span><div style="display:flex;flex-wrap:wrap;gap:8px">' + chips(LS, 'ls') + '</div></div>' +
          '<div style="display:flex;flex-direction:column;gap:8px"><span class="lbl" style="display:flex;align-items:center;gap:8px"><span style="width:10px;height:10px;border-radius:50%;background:#7B6CF6"></span>Tomo AI Lab, weekly class (' + tzLabel(S.country) + ')</span><div style="display:flex;flex-wrap:wrap;gap:8px">' + chips(AI, 'ai') + '</div></div>' +
          '<p style="margin:0;font-size:14px;color:' + MUTED + '">Classes start the week of ' + startLabel() + '. Each batch has up to 12 children.</p>' +
          '<div style="display:flex;gap:10px"><button type="button" data-to="1" style="' + BTN_BACK + '">Back</button><button type="button" data-next2' + (ok2() ? '' : ' disabled') + ' style="flex:1;' + BTN_MAIN + '">Next: review and pay</button></div></div>';
      } else {
        h += '<div style="display:flex;flex-direction:column;gap:14px"><div style="background:#F6F7FB;border-radius:16px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;font-size:15px">' +
          '<div style="display:flex;justify-content:space-between;gap:12px"><span>Tomo Life Skills, ' + esc(S.ls) + '</span><span style="color:' + MUTED + '">4 classes</span></div>' +
          '<div style="display:flex;justify-content:space-between;gap:12px"><span>Tomo AI Lab, ' + esc(S.ai) + '</span><span style="color:' + MUTED + '">4 classes</span></div>' +
          '<div style="display:flex;justify-content:space-between;gap:12px;border-top:1px solid #E3E6EF;padding-top:8px;margin-top:2px"><strong>Total per month</strong><strong>&#8377;4,999</strong></div>' +
          '<span style="font-size:13px;color:' + MUTED + '">Taxes included. Billed monthly. Cancel any time; your plan runs to the end of the paid month.</span></div>' +
          '<div style="display:flex;flex-direction:column;gap:8px"><span class="lbl">Pay with</span><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">' + chips(['UPI', 'Card', 'Net banking'], 'method') + '</div></div>' +
          '<label style="display:flex;gap:10px;align-items:flex-start;font-size:14px;cursor:pointer"><input type="checkbox" name="terms"' + (S.terms ? ' checked' : '') + ' style="width:18px;height:18px;margin:2px 0 0;accent-color:' + TEAL + ';flex-shrink:0"><span>I agree to the <a href="https://www.tomoclub.org/terms-and-conditions">terms</a> and a monthly subscription of &#8377;4,999 that I can cancel any time.</span></label>' +
          '<label style="display:flex;gap:10px;align-items:flex-start;font-size:14px;cursor:pointer"><input type="checkbox" name="waOk"' + (S.waOk ? ' checked' : '') + ' style="width:18px;height:18px;margin:2px 0 0;accent-color:' + TEAL + ';flex-shrink:0"><span>Send class reminders to my WhatsApp.</span></label>' +
          '<div style="display:flex;gap:10px"><button type="button" data-to="2" style="' + BTN_BACK + '">Back</button><button type="button" data-pay' + (canPay() ? '' : ' disabled') + ' style="flex:1;' + BTN_MAIN + '">Pay &#8377;4,999 and enrol</button></div>' +
          '<p style="margin:0;display:flex;align-items:center;justify-content:center;gap:6px;font-size:13px;color:' + MUTED + '">Secure payment. Your card details never touch our servers.</p></div>';
      }
      card.innerHTML = h;
    }
    function refresh() { var b1 = card.querySelector('[data-next1]'); if (b1) b1.disabled = !ok1(); var bp = card.querySelector('[data-pay]'); if (bp) bp.disabled = !canPay(); }
    card.addEventListener('input', function (e) { var n = e.target.name; if (!n || n === 'terms' || n === 'waOk') return; S[n] = e.target.value; refresh(); });
    card.addEventListener('change', function (e) {
      var n = e.target.name;
      if (n === 'grade') { S.grade = e.target.value; track('grade_select', { cta_location: 'enrol', grade: S.grade }); }
      if (n === 'country') { S.country = e.target.value; track('country_select', { cta_location: 'enrol', country: S.country }); }
      if (n === 'terms') { S.terms = e.target.checked; track('terms_toggle', { cta_location: 'enrol', checked: S.terms }); }
      if (n === 'waOk') { S.waOk = e.target.checked; track('whatsapp_reminder_toggle', { cta_location: 'enrol', checked: S.waOk }); }
      refresh();
    });
    card.addEventListener('click', function (e) {
      var t = e.target.closest('button'); if (!t || t.disabled) return;
      if (t.hasAttribute('data-next1')) { track('lead_submitted', { cta_location: 'enrol', program: 'bundle', grade: S.grade, country: S.country, city: S.city.trim() }); saveRecord('Leads', { program: 'bundle', parent_name: S.name.trim(), email: S.email.trim(), whatsapp: S.phone.trim(), country: S.country, city: S.city.trim(), grade: S.grade }); S.step = 2; render(); }
      else if (t.hasAttribute('data-next2')) { track('begin_checkout', { cta_location: 'enrol', program: 'bundle', ecommerce: ECOM }); S.step = 3; render(); }
      else if (t.hasAttribute('data-to')) { track('enrol_back', { cta_location: 'enrol' }); S.step = Number(t.getAttribute('data-to')); render(); }
      else if (t.hasAttribute('data-pick')) {
        var k = t.getAttribute('data-pick'); S[k] = t.getAttribute('data-val');
        if (k === 'method') track('payment_method_select', { cta_location: 'enrol', method: S.method });
        else track('batch_select', { cta_location: 'enrol', program: k === 'ls' ? 'life_skills' : 'ai_lab', batch: S[k] });
        render();
      }
      else if (t.hasAttribute('data-pay')) { track('add_payment_info', { cta_location: 'enrol', payment_type: S.method, ecommerce: ECOM }); track('payment_started', { cta_location: 'enrol', method: S.method, value: 4999 }); pay(); }
    });
    function pay() {
      /* TODO (developer): replace this demo window with your payment gateway (for example a Razorpay subscription checkout).
         On the gateway's success callback, call done(paymentId). */
      var m = modal('<div role="dialog" aria-modal="true" aria-labelledby="pay-title" style="width:min(420px,100%);background:#FFFFFF;border-radius:24px;padding:26px;display:flex;flex-direction:column;gap:14px;box-shadow:0 30px 80px rgba(0,0,0,.35);font-family:Outfit,system-ui,sans-serif;color:#0B1230">' +
        '<div style="display:flex;justify-content:space-between;align-items:center"><strong id="pay-title" style="font-size:20px">Complete payment</strong><span style="font-size:13px;color:' + MUTED + '">Demo checkout</span></div>' +
        '<div style="background:#F6F7FB;border-radius:14px;padding:14px;display:flex;justify-content:space-between"><span>Both programs, monthly</span><strong>&#8377;4,999</strong></div>' +
        '<p style="margin:0;color:' + MUTED + ';font-size:15px">Paying with ' + esc(S.method) + '. On the live site this is your payment provider&#39;s secure checkout.</p>' +
        '<button type="button" data-paid style="font:inherit;font-weight:700;font-size:18px;background:#20B2B6;color:#FFFFFF;border:0;border-radius:999px;min-height:52px;cursor:pointer">Pay &#8377;4,999</button>' +
        '<button type="button" data-cancel style="font:inherit;font-weight:600;background:none;border:0;color:' + MUTED + ';cursor:pointer;text-decoration:underline">Cancel</button></div>', 60);
      m.el.addEventListener('click', function (e) {
        if (e.target.closest('[data-cancel]')) { track('payment_cancelled', { cta_location: 'checkout' }); saveRecord('Enrolments', Object.assign({ status: 'payment_cancelled', transaction_id: '' }, { parent_name: S.name.trim(), email: S.email.trim(), whatsapp: S.phone.trim(), country: S.country, city: S.city.trim(), grade: S.grade, life_skills_batch: S.ls, ai_lab_batch: S.ai, payment_method: S.method, amount_inr: 4999, whatsapp_reminders: S.waOk ? 'yes' : 'no' })); m.close(); }
        if (e.target.closest('[data-paid]')) { m.close(); done('demo-' + Date.now()); }
      });
    }
    function done(txn) {
      track('purchase', { transaction_id: txn, grade: S.grade, country: S.country, ecommerce: ECOM });
      saveRecord('Enrolments', Object.assign({ status: 'paid', transaction_id: txn }, { parent_name: S.name.trim(), email: S.email.trim(), whatsapp: S.phone.trim(), country: S.country, city: S.city.trim(), grade: S.grade, life_skills_batch: S.ls, ai_lab_batch: S.ai, payment_method: S.method, amount_inr: 4999, whatsapp_reminders: S.waOk ? 'yes' : 'no' }));
      track('payment_completed', { value: 4999, method: S.method });
      var first = S.name.trim().split(' ')[0];
      var m = modal('<div role="dialog" aria-modal="true" aria-labelledby="done-title" style="width:min(480px,100%);background:#FFFFFF;border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.35);font-family:Outfit,system-ui,sans-serif;color:#0B1230">' +
        '<div style="background:#F3F1FF;padding:26px 24px 8px;display:flex;justify-content:center">' + BADGE + '</div>' +
        '<div style="padding:20px 28px 28px;display:flex;flex-direction:column;gap:12px;text-align:center"><h2 id="done-title" style="margin:0;font-weight:700;font-size:28px">You&#39;re enrolled!</h2>' +
        '<p style="margin:0;color:' + MUTED + '">' + esc(first ? first + ', your' : 'Your') + ' child is enrolled in Tomo Life Skills and Tomo AI Lab.</p>' +
        '<div style="background:#F6F7FB;border-radius:14px;padding:12px 16px;display:flex;flex-direction:column;gap:4px;font-weight:600"><span>Life Skills: ' + esc(S.ls) + '</span><span>AI Lab: ' + esc(S.ai) + '</span></div>' +
        '<p style="margin:0;font-size:15px;color:' + MUTED + '">Your receipt and class links are on their way to ' + esc(S.email) + '.</p>' +
        '<button type="button" data-done style="font:inherit;font-weight:700;background:#FFC83D;color:#0B1230;border:0;border-radius:999px;padding:12px 24px;min-height:48px;cursor:pointer">Done</button></div></div>', 70);
      m.el.addEventListener('click', function (e) { if (e.target.closest('[data-done]')) { track('confirmation_close', { cta_location: 'confirmation' }); m.close(); } });
    }
    render();
  }

  var CELEBRATE = '<svg width="220" height="150" viewBox="0 0 220 150" role="img" aria-label="Celebration: a calendar with a check mark and confetti"><circle cx="110" cy="80" r="62" fill="#FFE1D8"/><rect x="66" y="40" width="88" height="80" rx="12" fill="#FFFFFF" stroke="#0B1230" stroke-width="3"/><rect x="66" y="40" width="88" height="22" rx="10" fill="#FF6F4F" stroke="#0B1230" stroke-width="3"/><path d="M86 32v16M134 32v16" stroke="#0B1230" stroke-width="3.5" stroke-linecap="round"/><circle cx="110" cy="92" r="20" fill="#20B2B6"/><path d="M100 92l7 7 13-14" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><rect x="26" y="34" width="10" height="10" rx="2" fill="#FFC83D" transform="rotate(20 31 39)"/><rect x="182" y="46" width="10" height="10" rx="2" fill="#7B6CF6" transform="rotate(-15 187 51)"/><circle cx="44" cy="100" r="5" fill="#7B6CF6"/><circle cx="178" cy="104" r="5" fill="#FFC83D"/><circle cx="170" cy="22" r="4" fill="#20B2B6"/><circle cx="52" cy="18" r="4" fill="#FF6F4F"/></svg>';
  var BADGE = '<svg width="220" height="150" viewBox="0 0 220 150" role="img" aria-label="Celebration: a badge with a check mark and confetti"><circle cx="110" cy="78" r="62" fill="#E2DEFF"/><path d="M110 22l12 9 15-1 5 14 13 7-3 15 7 13-11 10-2 15-15 3-9 12-12-7-12 7-9-12-15-3-2-15-11-10 7-13-3-15 13-7 5-14 15 1z" fill="#FFC83D" stroke="#0B1230" stroke-width="3" stroke-linejoin="round"/><circle cx="110" cy="78" r="30" fill="#FFFFFF" stroke="#0B1230" stroke-width="3"/><path d="M96 78l9 9 18-19" fill="none" stroke="#20B2B6" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="44" cy="104" r="5" fill="#7B6CF6"/><circle cx="180" cy="110" r="5" fill="#FF6F4F"/><circle cx="170" cy="20" r="4" fill="#20B2B6"/></svg>';

  /* ---------- navbar: menu button on narrow screens ---------- */
  function initNav() {
    var t = document.querySelector('.navtoggle'), n = document.getElementById('main-nav');
    if (!t || !n) return;
    function set(open) {
      n.classList.toggle('open', open);
      t.setAttribute('aria-expanded', open ? 'true' : 'false');
      t.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    }
    t.addEventListener('click', function () { set(!n.classList.contains('open')); });
    n.addEventListener('click', function (e) { if (e.target.closest('a')) set(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') set(false); });
  }

  document.addEventListener('DOMContentLoaded', function () {
    track('tomo_page_view', { cta_location: 'page', title: document.title });
    initSectionViews();
    initPicker(); initFaqTabs(); initNewsletter(); initNav();
    var b = document.querySelector('[data-booking]'); if (b) initBooking(b);
    var en = document.querySelector('[data-enrol]'); if (en) initEnrol(en);
  });
})();
