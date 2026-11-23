/* TomoClub lead tracking (Nov 2026). Loaded on every page next to analytics.js.
 *
 * 1. Events. Page views, important button clicks, form steps, downloads and Calendly bookings go to
 *    - Google Analytics 4 (gtag, already loaded by the page or analytics.js), and
 *    - /api/beat, which keeps a first-party copy in the "Website events" Sheet tab for the /admin dashboard.
 *    Neither ever receives a name, email, phone number or anything typed into a form. Button labels are scrubbed of
 *    anything that looks like an email or phone number, and URLs lose query parameters that could carry them.
 *
 * 2. Consent. Each lead form gets two unticked boxes:
 *    - "Save my details if I don't finish ..."  allows /api/partial to keep name, email, school or district,
 *      phone and role when the visitor leaves without sending. Unticking it erases what was saved.
 *    - "Send me occasional emails ..."          the only thing that allows Instantly follow-up.
 *
 * 3. Each form also gets hidden fields the APIs use: form_name, submission_id (so a retry is saved once),
 *    draft_id (links a partial lead to the finished one), visitor_id, form_loaded_at and a honeypot (spam).
 *
 * GA4 key events to mark in GA4 > Admin > Events: generate_lead, book_call_scheduled, resource_download.
 */
(function () {
  'use strict';
  if (window.__tcForms) return;
  window.__tcForms = true;

  /* ── Identity: random, first-party, no personal data ─────────────────── */
  function rid(p) {
    var a = new Uint8Array(12);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return p + Array.prototype.map.call(a, function (x) { return ('0' + x.toString(16)).slice(-2); }).join('');
  }
  function store(k, v, s) {
    try { var st = s || localStorage; if (v === undefined) return st.getItem(k); st.setItem(k, v); } catch (e) { return null; }
    return v;
  }
  var visitorId = store('tc_vid') || store('tc_vid', rid('v'));
  var now = Date.now();
  var last = Number(store('tc_slast', undefined, sessionStorage) || 0);
  var sessionId = store('tc_sid', undefined, sessionStorage);
  if (!sessionId || now - last > 30 * 60000) sessionId = store('tc_sid', rid('s'), sessionStorage);
  store('tc_slast', String(now), sessionStorage);

  var path = location.pathname.replace(/\/index\.html$/, '/').replace(/(.)\/$/, '$1') || '/';
  var ua = navigator.userAgent || '';
  var device = /iPad|Tablet|PlayBook|Silk|(Android(?!.*Mobile))/i.test(ua) ? 'tablet' : /Mobi|iPhone|Android/i.test(ua) ? 'mobile' : 'desktop';

  function attr() { return window.tomoAttribution ? window.tomoAttribution() : { referrer: document.referrer, landing_page: path }; }
  function sourceOf(utm, ref) {
    if (utm) return String(utm).toLowerCase().slice(0, 60);
    var h = '';
    try { h = new URL(ref).hostname.replace(/^www\./, ''); } catch (e) { return 'direct'; }
    if (!h || /(^|\.)tomoclub\.org$/.test(h) || /vercel\.app$/.test(h)) return 'direct';
    var map = [[/(^|\.)google\./, 'google'], [/bing\.com$/, 'bing'], [/duckduckgo\.com$/, 'duckduckgo'], [/linkedin\.com$|lnkd\.in$/, 'linkedin'],
      [/facebook\.com$|fb\.me$/, 'facebook'], [/instagram\.com$/, 'instagram'], [/(^|\.)t\.co$|twitter\.com$|x\.com$/, 'x'], [/youtube\.com$|youtu\.be$/, 'youtube'],
      [/chatgpt\.com$|openai\.com$|perplexity\.ai$|claude\.ai$|gemini\.google/, 'ai assistant']];
    for (var i = 0; i < map.length; i++) if (map[i][0].test(h)) return map[i][1];
    return h.slice(0, 60);
  }
  var A = attr();
  var traffic = { source: sourceOf(A.utm_source, A.referrer), medium: (A.utm_medium || '').slice(0, 60), campaign: (A.utm_campaign || '').slice(0, 80) };

  function scrub(t) {
    return String(t || '').replace(/\s+/g, ' ').trim()
      .replace(/[^\s@<>()]+@[^\s@<>()]+\.[a-z]{2,}/gi, '[email]')
      .replace(/\+?\d[\d\s().-]{7,}\d/g, '[number]').slice(0, 80);
  }
  function safeHref(h) {
    if (!h) return '';
    if (/^(mailto|tel):/i.test(h)) return h.split(':')[0];
    try { var u = new URL(h, location.href); return (u.origin === location.origin ? '' : u.hostname) + u.pathname; } catch (e) { return ''; }
  }

  /* ── Event fan-out ──────────────────────────────────────────────────── */
  var queue = [];
  function flush(beacon) {
    if (!queue.length) return;
    var payload = JSON.stringify({ visitor_id: visitorId, session_id: sessionId, device: device, source: traffic.source, medium: traffic.medium, campaign: traffic.campaign, events: queue.splice(0, 30) });
    try {
      if (beacon && navigator.sendBeacon && navigator.sendBeacon('/api/beat', new Blob([payload], { type: 'text/plain' }))) return;
      fetch('/api/beat', { method: 'POST', headers: { 'Content-Type': 'text/plain' }, body: payload, keepalive: true }).catch(function () {});
    } catch (e) {}
  }
  setInterval(function () { flush(false); }, 10000);
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') flush(true); });
  window.addEventListener('pagehide', function () { flush(true); });

  // name: event name; p: { label, form, ga (false = skip GA), now (send at once), gaName, gaParams }
  function track(name, p) {
    p = p || {};
    var label = scrub(p.label);
    if (p.ga !== false && typeof window.gtag === 'function') {
      var params = { page_path: path };
      if (label) params.event_label = label;
      if (p.form) params.form_name = p.form;
      if (p.gaParams) for (var k in p.gaParams) params[k] = p.gaParams[k];
      window.gtag('event', p.gaName || name, params);
    }
    if (window.clarity) try { window.clarity('event', name); } catch (e) {}
    queue.push({ name: name, label: label, form: p.form || '', page: path, ts: new Date().toISOString() });
    if (p.now) flush(true);
  }
  // Older callers (home.js story steps) use tomoTrack(name, label, opts).
  window.tomoTrack = function (name, label, opts) { opts = opts || {}; track(name, { label: label, ga: opts.ga, now: opts.now }); };
  window.tcTrack = track;

  track('page_view', { ga: false, label: document.title.slice(0, 80) });

  /* ── Forms ──────────────────────────────────────────────────────────── */
  // name, how to find it, and whether it collects contact details for follow-up (save-progress consent)
  var FORMS = [
    { sel: '#b2b-lead-form', name: 'home_discovery', contact: true, marketing: true },
    { sel: '#project-form', name: 'build_with_us', contact: true, marketing: true },
    { sel: '#hero-form', name: 'ebook_hero', contact: true, marketing: true },
    { sel: '#mid-form', name: 'ebook_mid', contact: true, marketing: true },
    { sel: '#toolkit-download-form', name: 'guide_download', contact: true, marketing: true, modal: true }
  ];
  var SAVE_TEXT = "Save my details if I don't finish, so TomoClub can follow up.";
  var MKT_TEXT = 'Send me occasional emails from TomoClub. Unsubscribe any time.';
  var state = {}; // per form name

  function hidden(form, name, value) {
    var el = form.querySelector('input[type=hidden][name="' + name + '"]');
    if (!el) { el = document.createElement('input'); el.type = 'hidden'; el.name = name; form.appendChild(el); }
    el.value = value;
    return el;
  }
  function field(form, names) {
    for (var i = 0; i < names.length; i++) { var el = form.querySelector('[name="' + names[i] + '"]'); if (el && el.value) return el.value.trim(); }
    return '';
  }
  function contact(form) {
    return {
      name: field(form, ['name', 'firstName', 'full_name']),
      email: field(form, ['email']),
      district: field(form, ['district', 'organization', 'school']),
      phone: field(form, ['phone', 'tel', 'whatsapp']),
      role: field(form, ['role'])
    };
  }
  function hasContact(c) { return /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(c.email) || (c.phone.match(/\d/g) || []).length >= 7; }

  function consentBlock(cfg) {
    var box = document.createElement('div');
    box.className = 'tc-consent';
    box.style.cssText = 'display:flex;flex-direction:column;gap:.45rem;margin:.6rem 0 .9rem;font-size:.82rem;line-height:1.4;text-align:left;';
    var html = '';
    var row = function (n, t) {
      return '<label style="display:flex;gap:.55rem;align-items:flex-start;cursor:pointer;font-weight:400;opacity:.9;color:inherit;text-transform:none;letter-spacing:normal;margin:0">' +
        '<input type="checkbox" name="' + n + '" value="yes" style="width:17px;height:17px;min-width:17px;margin:.1rem 0 0;accent-color:#2AB4B8;flex:none">' +
        '<span>' + t + '</span></label>';
    };
    if (cfg.contact) html += row('save_progress_consent', SAVE_TEXT);
    if (cfg.marketing) html += row('marketing_consent', MKT_TEXT);
    box.innerHTML = html;
    return box;
  }

  function sendPartial(form, cfg, opts) {
    var st = state[cfg.name];
    if (!st || st.done) return;
    var save = form.querySelector('[name=save_progress_consent]');
    if (!save || !save.checked) return;
    var c = contact(form);
    if (!hasContact(c)) return;
    var sig = [c.name, c.email, c.district, c.phone, c.role, (form.querySelector('[name=marketing_consent]') || {}).checked].join('|');
    if (sig === st.lastSaved) return;
    st.lastSaved = sig;
    var a = attr();
    var body = { draft_id: st.draft, consent: 'yes', form_name: cfg.name, page: path, name: c.name, email: c.email, district: c.district, phone: c.phone, role: c.role,
      marketing_consent: (form.querySelector('[name=marketing_consent]') || {}).checked ? 'yes' : 'no', visitor_id: visitorId };
    for (var k in a) body[k] = a[k];
    var json = JSON.stringify(body);
    if (opts && opts.beacon && navigator.sendBeacon) navigator.sendBeacon('/api/partial', new Blob([json], { type: 'text/plain' }));
    else fetch('/api/partial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: json, keepalive: true }).catch(function () {});
    if (!st.partialTracked) { st.partialTracked = true; track('partial_saved', { form: cfg.name, ga: false }); }
  }
  function withdrawPartial(cfg) {
    var st = state[cfg.name];
    if (!st || !st.lastSaved) return;
    st.lastSaved = '';
    fetch('/api/partial', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ draft_id: st.draft, withdraw: true }), keepalive: true }).catch(function () {});
  }

  function setup(form, cfg) {
    if (form.__tc) return;
    form.__tc = true;
    var st = state[cfg.name] = { draft: rid('d'), started: false, done: false, viewed: false, lastSaved: '' };
    hidden(form, 'form_name', cfg.name);
    hidden(form, 'submission_id', rid('sub'));
    hidden(form, 'draft_id', st.draft);
    hidden(form, 'visitor_id', visitorId);
    if (!form.querySelector('[name=form_loaded_at]')) hidden(form, 'form_loaded_at', String(Date.now()));
    if (!form.querySelector('[name=hp_company_website]')) {
      var hp = document.createElement('div');
      hp.setAttribute('aria-hidden', 'true');
      hp.style.cssText = 'position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden';
      hp.innerHTML = '<input type="text" name="hp_company_website" tabindex="-1" autocomplete="off">';
      form.appendChild(hp);
    }
    // Consent boxes go just above the submit button.
    var submit = form.querySelector('button[type=submit], input[type=submit], button:not([type])');
    var block = consentBlock(cfg);
    var anchor = submit;
    while (anchor && anchor.parentNode && anchor.parentNode !== form) anchor = anchor.parentNode;
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(block, anchor); else form.appendChild(block);

    // form_view: when at least half the form is on screen (or the modal opens).
    // A form inside a pop-up counts as viewed when the pop-up opens (see the [data-file] click handler), not here.
    if ('IntersectionObserver' in window && !cfg.modal) {
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting && !st.viewed) { st.viewed = true; track('form_view', { form: cfg.name }); io.disconnect(); } });
      }, { threshold: 0.4 });
      io.observe(form);
    }
    form.addEventListener('input', function (ev) {
      if (ev.target && /consent|hp_company/.test(ev.target.name || '')) return;
      if (!st.started) { st.started = true; track('form_start', { form: cfg.name }); }
      clearTimeout(st.timer);
      st.timer = setTimeout(function () { sendPartial(form, cfg); }, 4000);
    });
    form.addEventListener('change', function (ev) {
      if (!ev.target) return;
      if (ev.target.name === 'save_progress_consent') {
        if (ev.target.checked) sendPartial(form, cfg); else withdrawPartial(cfg);
      } else if (ev.target.name === 'marketing_consent') {
        st.lastSaved = st.lastSaved ? 'x' : ''; sendPartial(form, cfg);
      }
    });
    form.addEventListener('submit', function () {
      track('form_submit', { form: cfg.name, ga: false });
    });
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') sendPartial(form, cfg, { beacon: true }); });
    window.addEventListener('pagehide', function () {
      sendPartial(form, cfg, { beacon: true });
      if (st.started && !st.done && !st.abandoned) { st.abandoned = true; track('form_abandon', { form: cfg.name, ga: true }); }
      flush(true);
    });
  }

  function markDone(formName, ok) {
    var st = state[formName];
    if (!st || st.done) return;
    if (!ok) { track('form_error', { form: formName, ga: false }); return; }
    st.done = true;
    var dl = /^guide_download$|^ebook_/.test(formName);
    // One form_success per sent form; GA4 gets generate_lead (and resource_download for downloads).
    track('form_success', { form: formName, now: !dl, gaName: 'generate_lead', gaParams: { form_name: formName, lead_type: dl ? 'download' : 'contact' } });
    if (dl) track('resource_download', { form: formName, now: true, gaParams: { form_name: formName } });
    var form = null;
    FORMS.forEach(function (f) { if (f.name === formName) form = document.querySelector(f.sel); });
    if (form) {
      hidden(form, 'submission_id', rid('sub'));
      var c = form.querySelector('.tc-consent');
      if (formName === 'home_discovery' && c) c.style.display = 'none';
    }
  }

  // Success is read from the site's own API answers, so a form counts as sent only when the server saved it.
  if (window.fetch) {
    var origFetch = window.fetch;
    window.fetch = function (input, init) {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      var p = origFetch.apply(this, arguments);
      if (/\/api\/(lead|signup)(\?|$)/.test(url) && init && typeof init.body === 'string') {
        var formName = '';
        try { var b = JSON.parse(init.body); formName = b.form_name || ''; if (b.type === 'call_booked') formName = ''; } catch (e) {}
        if (formName) p.then(function (r) { return r.clone().json().then(function (j) { markDone(formName, r.ok && j && (j.ok || j.success)); }); }).catch(function () { markDone(formName, false); });
      }
      return p;
    };
  }

  function scan() { FORMS.forEach(function (cfg) { var f = document.querySelector(cfg.sel); if (f) setup(f, cfg); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan); else scan();
  // The guide download form sits in a modal: count opening it as a form view.
  document.addEventListener('click', function (ev) {
    var dl = ev.target.closest && ev.target.closest('[data-file]');
    if (dl && state.guide_download && !state.guide_download.viewed) { state.guide_download.viewed = true; track('form_view', { form: 'guide_download' }); }
  }, true);

  /* ── Clicks ─────────────────────────────────────────────────────────── */
  function ctaName(text, href, el) {
    var t = text.toLowerCase(), h = (href || '').toLowerCase();
    if (el.hasAttribute('data-book-call') || /calendly\.com/.test(h) || /book (a )?20|book 20|book a call|pick a .*slot/.test(t)) return 'Book a call';
    if (/tell us (your|what|about)|share your school/.test(t)) return 'Tell us your problem';
    if (/build-with-us/.test(h) || /build with us|real requests/.test(t)) return 'Build With Us';
    if (/contact|write to us|talk to us/.test(t) || /\/contact|#start/.test(h)) return 'Contact us';
    if (/professional-development/.test(h)) return 'Explore AI PD';
    if (/ai-literacy/.test(h)) return 'Explore AI Literacy';
    if (/future-ready/.test(h)) return 'Explore Future-Ready Skills';
    if (/results|#proof|case stud/.test(h + ' ' + t)) return 'See results';
    return '';
  }
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('a, button, summary');
    if (!el || el.closest('.tc-consent')) return;
    var text = (el.getAttribute('aria-label') || el.textContent || '').replace(/\s+/g, ' ').trim();
    var href = el.getAttribute('href') || '';
    if (el.tagName === 'SUMMARY') { track('faq_open', { label: text, ga: true }); return; }
    if (/^(mailto|tel):/i.test(href)) { track('contact_click', { label: href.split(':')[0] }); return; }
    if (/\.pdf(\?|#|$)/i.test(href)) {
      track('file_download', { label: href.split('/').pop().split('?')[0], gaName: 'file_download', gaParams: { file_name: href.split('/').pop().split('?')[0] } });
      return;
    }
    var named = ctaName(text, href, el);
    var isButton = /\b(btn|more)\b/.test(String(el.className || '')) || el.tagName === 'BUTTON' || el.hasAttribute('data-book-call') || el.hasAttribute('data-cta');
    if (el.matches('button[type=submit]') || el.closest('.nav-actions button, #mobile-menu-toggle, .theme-toggle-btn, .modal-close')) return;
    if (named || isButton) {
      var dest = safeHref(href);
      var label = (named || scrub(text).slice(0, 50) || 'button') + (dest ? ' | ' + dest : '');
      if (named === 'Book a call') track('book_call_click', { label: label, gaParams: { cta_name: named, link_url: safeHref(href) } });
      else track('cta_click', { label: label, gaParams: { cta_name: named || scrub(text).slice(0, 50), link_url: safeHref(href) } });
      return;
    }
    if (el.tagName === 'A' && href && !/^#/.test(href)) {
      try { var u = new URL(href, location.href); if (u.origin !== location.origin) track('outbound_click', { label: u.hostname, ga: false }); } catch (e) {}
    }
  }, true);

  /* ── Calendly ───────────────────────────────────────────────────────── */
  window.addEventListener('message', function (ev) {
    if (ev.origin !== 'https://calendly.com' || !ev.data || typeof ev.data.event !== 'string') return;
    if (ev.data.event === 'calendly.event_type_viewed') track('book_call_open', { ga: false });
    if (ev.data.event === 'calendly.event_scheduled') track('book_call_scheduled', { now: true, gaParams: { method: 'calendly' } });
  });

  /* ── Scroll depth (first-party only) ────────────────────────────────── */
  var depth = { 50: false, 90: false };
  window.addEventListener('scroll', function () {
    var h = document.documentElement, pct = (h.scrollTop + innerHeight) / Math.max(h.scrollHeight, 1) * 100;
    for (var d in depth) if (!depth[d] && pct >= +d) { depth[d] = true; track('scroll_depth', { label: d + '%', ga: false }); }
  }, { passive: true });
})();
