/* TomoClub B2B interaction events (Nov 2026). Loaded by assets/js/analytics.js on every page.
 *
 * What it does
 *  1. Names every meaningful interaction as one event and sends it to GA4, Clarity, LinkedIn and Meta
 *     (whichever analytics.js loaded), and in small batches to /api/event, which saves it to the
 *     "Website events" Sheet tab and, for known contacts, routes high-intent activity to Instantly.
 *  2. Opens "Book a 20-minute call" links ([data-book-call]) as a Calendly pop-up, and when Calendly reports
 *     a booking, tells /api/lead so the meeting lands in the Sheet and Instantly with the invitee's details.
 *  3. Adds spam protection fields (a hidden honeypot and a load time) to every form that posts to our APIs.
 *  4. Remembers a visitor who has given their email (signed token from /api/lead or /api/signup), so later
 *     activity in the same browser can be tied to them. Nothing is stored for anyone who has not submitted a form.
 *
 * Event names (GA4 custom events; mark the starred ones as key events in GA4):
 *   offer_view            visited an offer page (label: offer)
 *   build_with_us_view    visited /build-with-us
 *   results_view          visited /results
 *   story_step_view       reached a step of the home page story (label: step)
 *   cta_click             clicked a button or link styled as a button (label: text | href)
 *   book_call_click       clicked "Book a 20-minute call" (label: where)
 *   book_call_scheduled * completed a Calendly booking
 *   form_start            first typed into a form (label: form)
 *   form_abandon          started a form and left without sending it (label: form)
 *   lead_submitted      * sent the discovery form (label: form)
 *   resource_download   * downloaded a guide or the ebook (label: file)
 *   case_study_download   opened a case-study download (label: title)
 *   faq_open              opened an FAQ (label: question); faq_cost_open when the question is about cost
 *   contact_click         clicked an email or phone link
 *   video_play            opened a video
 *   scroll_depth          reached 50 / 90 percent of a page (label: percent)
 */
(function () {
  'use strict';

  var CONFIG = {
    CALENDLY_URL: 'https://calendly.com/avinashtomo/tomoclub-call',
    // LinkedIn Campaign Manager > Analyze > Conversion tracking > create conversions with "Insight Tag event",
    // then paste their IDs here. Empty = not sent.
    LINKEDIN_CONVERSIONS: { lead_submitted: '', book_call_scheduled: '', resource_download: '' },
    // Cloudflare Turnstile site key. Leave empty until TURNSTILE_SECRET_KEY is set in Vercel.
    TURNSTILE_SITE_KEY: ''
  };

  var OFFER_PAGES = {
    '/professional-development': 'ai_pd', '/ai-literacy': 'ai_literacy',
    '/future-ready': 'future_ready', '/build-with-us': 'build_with_us'
  };
  var path = location.pathname.replace(/\/(index\.html)?$/, '') || '/';
  var store = {
    get: function (k, s) { try { return JSON.parse((s || localStorage).getItem(k)); } catch (e) { return null; } },
    set: function (k, v, s) { try { (s || localStorage).setItem(k, JSON.stringify(v)); } catch (e) {} }
  };

  // Anonymous visitor id (random, first party) and the pages seen this session.
  var visitorId = store.get('tomo_vid');
  if (!visitorId) { visitorId = 'v' + Math.random().toString(36).slice(2, 12) + Date.now().toString(36); store.set('tomo_vid', visitorId); }
  var seenPages = store.get('tomo_pages', sessionStorage) || [];
  if (seenPages[seenPages.length - 1] !== path) { seenPages.push(path); store.set('tomo_pages', seenPages.slice(-15), sessionStorage); }

  function known() { return store.get('tomo_lead') || null; }
  function attr() { return window.tomoAttribution ? window.tomoAttribution() : {}; }

  /* ── Event fan-out ───────────────────────────────────────────────────── */
  var queue = [];
  function flush(useBeacon) {
    if (!queue.length) return;
    var a = attr(), k = known();
    var payload = JSON.stringify({
      visitor_id: visitorId, email: k && k.email, token: k && k.token, events: queue.splice(0, 25),
      utm_source: a.utm_source, utm_campaign: a.utm_campaign, landing_page: a.landing_page
    });
    try {
      if (useBeacon && navigator.sendBeacon) navigator.sendBeacon('/api/event', new Blob([payload], { type: 'application/json' }));
      else fetch('/api/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: payload, keepalive: true }).catch(function () {});
    } catch (e) {}
  }
  setInterval(function () { flush(false); }, 15000);
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') flush(true); });
  window.addEventListener('pagehide', function () { flush(true); });

  function track(name, label, opts) {
    opts = opts || {};
    label = String(label || '').slice(0, 160);
    if (opts.ga !== false && typeof window.gtag === 'function') window.gtag('event', name, { event_label: label, page_path: path });
    if (window.clarity) window.clarity('event', name);
    var li = CONFIG.LINKEDIN_CONVERSIONS[name];
    if (li && window.lintrk) window.lintrk('track', { conversion_id: li });
    if (window.fbq) {
      if (name === 'lead_submitted') window.fbq('track', 'Lead', { content_name: label });
      else if (name === 'book_call_scheduled') window.fbq('track', 'Schedule');
      else if (name === 'resource_download') window.fbq('track', 'Lead', { content_name: 'download: ' + label });
    }
    queue.push({ name: name, label: label, page: path, ts: new Date().toISOString() });
    if (opts.now) flush(true);
  }
  window.tomoTrack = track;

  // Page-level intent.
  if (OFFER_PAGES[path]) track('offer_view', OFFER_PAGES[path]);
  if (path === '/build-with-us') track('build_with_us_view', document.referrer ? document.referrer.replace(/^https?:\/\//, '').slice(0, 80) : 'direct');
  if (path === '/results') track('results_view', '');

  /* ── Remember people who submit a form (token from our own APIs) ─────── */
  if (window.fetch) {
    var origFetch = window.fetch;
    window.fetch = function (input, init) {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      var p = origFetch.apply(this, arguments);
      if (/\/api\/(lead|signup)$/.test(url)) {
        p.then(function (r) { return r.clone().json(); }).then(function (j) {
          if (!j || !j.email || !j.token) return;
          var prev = store.get('tomo_lead');
          // A "hot" token (they asked to talk) is never replaced by a later "nurture" one.
          if (prev && prev.scope === 'hot' && j.scope !== 'hot' && prev.email === j.email) return;
          store.set('tomo_lead', { email: j.email, token: j.token, scope: j.scope || 'nurture' });
        }).catch(function () {});
      }
      return p;
    };
  }

  /* ── Calendly pop-up and booking capture ─────────────────────────────── */
  var calendlyLoading = null;
  function loadCalendly() {
    if (window.Calendly) return Promise.resolve();
    if (calendlyLoading) return calendlyLoading;
    calendlyLoading = new Promise(function (resolve, reject) {
      var css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = 'https://assets.calendly.com/assets/external/widget.css';
      document.head.appendChild(css);
      var s = document.createElement('script');
      s.src = 'https://assets.calendly.com/assets/external/widget.js'; s.async = true;
      s.onload = function () { resolve(); }; s.onerror = reject;
      document.head.appendChild(s);
      setTimeout(reject, 6000);
    });
    return calendlyLoading;
  }

  function openCalendly(href, where) {
    var a = attr(), k = known();
    var url = href && /calendly\.com/.test(href) ? href : CONFIG.CALENDLY_URL;
    track('book_call_click', where, { now: true });
    return loadCalendly().then(function () {
      window.Calendly.initPopupWidget({
        url: url,
        prefill: k ? { email: k.email } : {},
        utm: { utmSource: a.utm_source || 'website', utmMedium: a.utm_medium || '', utmCampaign: a.utm_campaign || '', utmContent: where || '', utmTerm: path }
      });
      return true;
    }).catch(function () { return false; });
  }

  window.addEventListener('message', function (ev) {
    if (ev.origin !== 'https://calendly.com' || !ev.data || typeof ev.data.event !== 'string') return;
    if (ev.data.event === 'calendly.event_scheduled') {
      track('book_call_scheduled', path, { now: true });
      var uri = ev.data.payload && ev.data.payload.invitee && ev.data.payload.invitee.uri;
      if (uri) {
        var a = attr();
        var body = { type: 'call_booked', invitee_uri: uri, page: path, pages_viewed: seenPages.join(' > ') };
        for (var key in a) body[key] = a[key];
        fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(function () {});
      }
    }
  });

  /* ── Clicks ──────────────────────────────────────────────────────────── */
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('a, button, summary');
    if (!el) return;
    var text = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 70);
    var href = el.getAttribute('href') || '';

    if (el.hasAttribute('data-book-call')) {
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey) { track('book_call_click', el.getAttribute('data-event-label') || text); return; }
      ev.preventDefault();
      openCalendly(href, el.getAttribute('data-event-label') || text).then(function (ok) {
        if (!ok) window.open(href || CONFIG.CALENDLY_URL, '_blank', 'noopener');
      });
      return;
    }
    if (el.tagName === 'SUMMARY') {
      track(/cost|price|pay|fund|budget/i.test(text) ? 'faq_cost_open' : 'faq_open', text);
      return;
    }
    if (/^mailto:|^tel:/.test(href)) { track('contact_click', href.split(':')[0]); return; }
    if (el.hasAttribute('data-file') || /case stud/i.test(text)) { track('case_study_download', el.getAttribute('data-title') || text); }
    if (el.hasAttribute('data-video') || el.classList.contains('video-thumb')) track('video_play', el.getAttribute('data-video') || text);
    if (el.hasAttribute('data-event')) { track(el.getAttribute('data-event'), el.getAttribute('data-event-label') || text); return; }
    if (/\bbtn\b/.test(el.className || '')) track('cta_click', text + ' | ' + href, { ga: !el.closest('[data-track]') });
  }, true);

  /* ── Forms: spam fields, start, submit, abandon ──────────────────────── */
  function formName(f) { return f.getAttribute('data-form-name') || f.id || f.className || 'form'; }
  var started = {}, sent = {};

  function harden(f) {
    if (f.__tomo) return; f.__tomo = true;
    var hp = document.createElement('div');
    hp.setAttribute('aria-hidden', 'true');
    hp.style.cssText = 'position:absolute!important;left:-9999px!important;width:1px;height:1px;overflow:hidden;';
    hp.innerHTML = '<label>Leave this empty<input type="text" name="hp_company_website" tabindex="-1" autocomplete="off"></label>';
    f.appendChild(hp);
    var t = document.createElement('input');
    t.type = 'hidden'; t.name = 'form_loaded_at'; t.value = String(Date.now());
    f.appendChild(t);
    var pv = document.createElement('input');
    pv.type = 'hidden'; pv.name = 'pages_viewed'; pv.value = seenPages.join(' > ');
    f.appendChild(pv);
    if (CONFIG.TURNSTILE_SITE_KEY && f.hasAttribute('data-lead-form')) {
      var box = document.createElement('div');
      box.className = 'cf-turnstile'; box.setAttribute('data-sitekey', CONFIG.TURNSTILE_SITE_KEY);
      var submit = f.querySelector('[type=submit]');
      f.insertBefore(box, submit ? submit.parentNode === f ? submit : submit.parentNode : null);
      if (!document.getElementById('cf-turnstile-js')) {
        var s = document.createElement('script'); s.id = 'cf-turnstile-js'; s.async = true; s.defer = true;
        s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'; document.head.appendChild(s);
      }
    }
    f.addEventListener('input', function () {
      var n = formName(f);
      if (!started[n]) { started[n] = true; track('form_start', n); }
    }, { once: false });
    f.addEventListener('submit', function () {
      var n = formName(f); sent[n] = true;
      if (f.classList.contains('ebook-form')) track('resource_download', 'Leaders of Tomorrow ebook', { now: true });
      else if (f.id === 'toolkit-download-form') track('resource_download', (f.querySelector('[name=toolkitName]') || {}).value || 'guide', { now: true });
    });
  }
  window.addEventListener('pagehide', function () {
    for (var n in started) if (!sent[n]) { track('form_abandon', n); }
    flush(true);
  });

  /* ── Scroll depth ────────────────────────────────────────────────────── */
  var depths = { 50: false, 90: false };
  window.addEventListener('scroll', function () {
    var h = document.documentElement;
    var pct = (h.scrollTop + window.innerHeight) / Math.max(h.scrollHeight, 1) * 100;
    for (var d in depths) if (!depths[d] && pct >= +d) { depths[d] = true; track('scroll_depth', d + '%', { ga: false }); }
  }, { passive: true });

  function ready() {
    Array.prototype.forEach.call(document.querySelectorAll('form[data-lead-form], #toolkit-download-form, .ebook-form, #project-form'), harden);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();
})();
