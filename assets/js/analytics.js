/* TomoClub site analytics — one file, loaded on every page.
 *
 *   <script defer src="/assets/js/analytics.js"></script>   (already added before </head> on every page)
 *
 * Fill in the two IDs below. Nothing else needs editing.
 *   GA4          : Google Analytics property already used on the site.
 *   LINKEDIN     : LinkedIn Campaign Manager → Analyze → Insight Tag → "I will use a tag manager"
 *                  → copy the Partner ID (a number like 1234567).
 *   CLARITY      : clarity.microsoft.com → New project → Settings → Setup → copy the Project ID
 *                  (a short code like "abc1def2gh").
 *   LEADSY       : leadsy.ai tag → copy the data-pid value from the install snippet.
 *   META_PIXEL   : Meta Events Manager → Data sources → the pixel → copy the Pixel ID (15–16 digits).
 * Leave an ID as '' to skip that tool.
 *
 * Also sends GA4 events:
 *   section_view   { section_name, engagement_ms }   when a section leaves the screen or the page is closed,
 *                                                     for any element with a data-track="name" attribute
 *   cta_click      { cta_name, cta_text, cta_href }   for links/buttons inside data-track sections
 *   lead_submitted { form_id }                        when the Build With Us form is submitted
 *   ...plus the site events in section 7 (book_call_click, generate_lead, form steps, and so on).
 *
 * Meta Pixel events (besides PageView on every page):
 *   Lead     { content_name }  Build With Us thank-you page, contact-page Tally form submit,
 *                              or a page calling window.tomoTrackLead(name) after its own form succeeds
 *   Contact  { content_name }  click on any WhatsApp link
 *   Schedule                   a booking completed in the Calendly pop-up
 */
(function () {
  var CONFIG = {
    GA4: 'G-FEGGQ2ZDMT',
    LINKEDIN_PARTNER_ID: '8364153',
    CLARITY_PROJECT_ID: 'yibamjl9lq',
    LEADSY_PID: 'Er26IyzOijeMy17O',
    META_PIXEL_ID: '1805331960518408'
  };

  /* ── 0. Where the visitor came from ─────────────────────────────────────
     UTM tags, ad click IDs, referrer and landing page, saved for the browser session on the first page
     (first touch). Same storage key and shape as parents-site.js, so every form can attach them:
     window.tomoAttribution() returns { utm_source, ..., gclid, fbclid, referrer, landing_page }. */
  var ATTR = (function () {
    try { var saved = sessionStorage.getItem('tomo_attr'); if (saved) return JSON.parse(saved); } catch (e) {}
    var a = {};
    try {
      var q = new URLSearchParams(location.search);
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'].forEach(function (k) { if (q.get(k)) a[k] = q.get(k); });
    } catch (e) {}
    a.referrer = document.referrer || '';
    a.landing_page = location.pathname + location.search;
    try { sessionStorage.setItem('tomo_attr', JSON.stringify(a)); } catch (e) {}
    return a;
  })();
  window.tomoAttribution = function () { var o = {}; Object.keys(ATTR).forEach(function (k) { o[k] = ATTR[k]; }); return o; };

  function load(src, attrs) {
    var s = document.createElement('script');
    s.async = true; s.src = src;
    if (attrs) { for (var k in attrs) s.setAttribute(k, attrs[k]); }
    document.head.appendChild(s);
    return s;
  }

  /* ── 1. Google Analytics 4 (only if the page hasn't already loaded it) ── */
  window.dataLayer = window.dataLayer || [];
  if (typeof window.gtag !== 'function') {
    window.gtag = function () { window.dataLayer.push(arguments); };
  }
  if (CONFIG.GA4 && !document.querySelector('script[src*="googletagmanager.com/gtag/js"]')) {
    load('https://www.googletagmanager.com/gtag/js?id=' + CONFIG.GA4);
    gtag('js', new Date());
    gtag('config', CONFIG.GA4);
  }

  /* ── 2. LinkedIn Insight Tag ─────────────────────────────────────────── */
  if (CONFIG.LINKEDIN_PARTNER_ID) {
    window._linkedin_partner_id = CONFIG.LINKEDIN_PARTNER_ID;
    window._linkedin_data_partner_ids = window._linkedin_data_partner_ids || [];
    window._linkedin_data_partner_ids.push(CONFIG.LINKEDIN_PARTNER_ID);
    if (!window.lintrk) {
      window.lintrk = function (a, b) { window.lintrk.q.push([a, b]); };
      window.lintrk.q = [];
    }
    load('https://snap.licdn.com/li.lms-analytics/insight.min.js');
  }

  /* ── 3. Microsoft Clarity (heatmaps, recordings, per-section attention) ─ */
  if (CONFIG.CLARITY_PROJECT_ID) {
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', CONFIG.CLARITY_PROJECT_ID);
  }

  /* ── 4. Leadsy.ai visitor identification ────────────────────────────── */
  if (CONFIG.LEADSY_PID) {
    load('https://r2.leadsy.ai/tag.js', {
      id: 'vtag-ai-js',
      'data-pid': CONFIG.LEADSY_PID,
      'data-version': '062024'
    });
  }

  /* ── 5. Meta Pixel (Facebook/Instagram ads) ─────────────────────────── */
  function metaTrack(event, params) {
    if (window.fbq) window.fbq('track', event, params || {});
  }
  // Pages with their own fetch-based forms call this once the submission succeeds.
  window.tomoTrackLead = function (name) { metaTrack('Lead', { content_name: name || '' }); };

  if (CONFIG.META_PIXEL_ID) {
    (function (f, b, e, v, n, t, s) {
      if (f.fbq) return;
      n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
      if (!f._fbq) f._fbq = n;
      n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
      t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    })(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', CONFIG.META_PIXEL_ID);
    window.fbq('track', 'PageView');

    // Build With Us only redirects here after a successful send, so count the Lead on arrival
    // rather than on submit (which also fires when validation fails).
    if (/^\/build-with-us\/thank-you(\.html)?$/.test(location.pathname)) {
      metaTrack('Lead', { content_name: 'build-with-us' });
    }

    // WhatsApp clicks → Contact
    document.addEventListener('click', function (ev) {
      var a = ev.target.closest && ev.target.closest('a[href*="whatsapp.com"], a[href*="wa.me"]');
      if (a) metaTrack('Contact', { content_name: 'whatsapp' });
    });

    // Tally form on the contact page posts a message to this window when submitted.
    window.addEventListener('message', function (ev) {
      if (!/(^|\.)tally\.so$/.test((ev.origin || '').replace(/^https?:\/\//, ''))) return;
      var d = ev.data;
      if (typeof d === 'string') { try { d = JSON.parse(d); } catch (x) { return; } }
      if (d && d.event === 'Tally.FormSubmitted') metaTrack('Lead', { content_name: location.pathname === '/share-your-story' ? 'share-your-story' : 'contact-us' });
    });
  }

  /* ── 6. Section engagement → GA4 events ─────────────────────────────── */
  function onReady(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn); else fn();
  }

  onReady(function () {
    var sections = Array.prototype.slice.call(document.querySelectorAll('[data-track]'));
    if (!sections.length || !('IntersectionObserver' in window)) return;

    var open = {};   // section_name → timestamp it became visible
    var seen = {};   // section_name → true once reported at least once

    function report(name, ms) {
      if (ms < 500) return;             // ignore scroll-throughs
      seen[name] = true;
      gtag('event', 'section_view', { section_name: name, engagement_ms: Math.round(ms), page_path: location.pathname });
      if (window.clarity) window.clarity('set', 'section', name);
    }

    var io = new IntersectionObserver(function (entries) {
      var now = performance.now();
      entries.forEach(function (e) {
        var name = e.target.getAttribute('data-track');
        if (e.isIntersecting) { if (!open[name]) open[name] = now; }
        else if (open[name]) { report(name, now - open[name]); delete open[name]; }
      });
    }, { threshold: 0.4 });
    sections.forEach(function (s) { io.observe(s); });

    // Flush anything still on screen when the visitor leaves.
    function flush() {
      var now = performance.now();
      for (var name in open) { report(name, now - open[name]); delete open[name]; }
    }
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden') flush(); });
    window.addEventListener('pagehide', flush);

    // CTA clicks inside tracked sections.
    document.addEventListener('click', function (ev) {
      var a = ev.target.closest && ev.target.closest('a, button');
      if (!a) return;
      var sec = a.closest('[data-track]');
      if (!sec) return;
      gtag('event', 'cta_click', {
        section_name: sec.getAttribute('data-track'),
        cta_name: ctaName(a),
        cta_text: (a.textContent || '').trim().slice(0, 60),
        cta_href: a.getAttribute('href') || ''
      });
    });

    // Lead form submissions (Build With Us).
    var form = document.getElementById('project-form');
    if (form) {
      form.addEventListener('submit', function () {
        gtag('event', 'lead_submitted', { form_id: 'build-with-us' });
        if (window.lintrk) window.lintrk('track', { conversion_id: null });
        if (window.clarity) window.clarity('set', 'lead', 'submitted');
      });
    }
  });

  /* ── 7. Site events → GA4 and Clarity ───────────────────────────────────
     Every listener here only watches: nothing changes what a click or a form does.
     No personal data: event values are button names, form names, FAQ questions and page paths, and anything
     that looks like an email address or phone number is replaced before it is sent.

     Events (mark the starred ones as key events in GA4):
       cta_click            { section_name, cta_name, cta_text, cta_href }  buttons outside data-track sections
                            (inside them, section 6 sends cta_click, now with cta_name too)
       book_call_click      { cta_location }   any "Book a call" link: Calendly pop-up or new tab
       book_call_scheduled* {}                 a Calendly pop-up booking was completed
       faq_open             { question }
       contact_click        { method }         email, phone or WhatsApp link
       form_view            { form_name }      a form came on screen (or its pop-up opened)
       form_start           { form_name }      first typing in a form
       form_abandon         { form_name }      typed in a form, then left without sending it
       generate_lead*       { form_name }      home form saved (sent by home.js), Build With Us thank-you page
       resource_download*   { resource_name }  guide or ebook download started (sent by the page's own form code)
       story_step_view      { event_label }    home page story steps (sent by home.js)
     Pages send their own events with window.tomoTrack(name, params) or tomoTrack(name, label). */
  // Emails, and digit runs long enough to be a phone number (9+ digits, so years and date ranges survive).
  function scrub(v) {
    return String(v == null ? '' : v)
      .replace(/[^\s@<>"]+@[^\s@<>"]+\.[a-z]{2,}/gi, '[removed]')
      .replace(/\+?\d[\d\s().-]{7,}\d/g, function (m) { return m.replace(/\D/g, '').length >= 9 ? '[removed]' : m; })
      .replace(/\s+/g, ' ').trim().slice(0, 100);
  }

  function track(name, params) {
    var p = { page_path: location.pathname };
    for (var k in params) p[k] = typeof params[k] === 'string' ? scrub(params[k]) : params[k];
    gtag('event', name, p);
    if (window.clarity) window.clarity('event', name);
  }
  window.tomoTrack = function (name, params) {
    track(name, params && typeof params === 'object' ? params : (params ? { event_label: String(params) } : {}));
  };

  // Fixed names for the buttons that matter, so reports group them however the button text is worded.
  function ctaName(el) {
    var href = el.getAttribute('href') || '';
    if (el.hasAttribute('data-book-call') || /calendly\.com/.test(href)) return 'Book a call';
    if (/\/build-with-us/.test(href) || el.getAttribute('data-interest') === 'Build With Us') return 'Build With Us';
    if (/#start$/.test(href)) return 'Tell us your problem';
    if (/\/professional-development/.test(href)) return 'Explore AI PD';
    if (/\/ai-literacy/.test(href)) return 'Explore AI Literacy';
    if (/\/future-ready/.test(href)) return 'Explore Future-Ready Skills';
    if (/\/results/.test(href)) return 'See results';
    if (/\/case-studies\//.test(href)) return 'Case study';
    if (/\/guides/.test(href) || el.classList.contains('open-download-modal')) return 'Guides';
    if (/^(mailto|tel):/.test(href)) return 'Contact us';
    return scrub(el.textContent).slice(0, 60) || 'Button';
  }

  function isBookCall(el) {
    return el.hasAttribute('data-book-call') || /calendly\.com/.test(el.getAttribute('href') || '');
  }

  // Clicks. Capture phase, so the state read here (FAQ open or closed) is the state before this click.
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('a, button, summary, .faq-question');
    if (!el) return;
    var href = el.getAttribute('href') || '';
    var sec = el.closest('[data-track]');

    if (el.tagName === 'SUMMARY' || el.classList.contains('faq-question')) {
      var item = el.parentElement;
      var wasOpen = el.tagName === 'SUMMARY' ? item && item.open : item && item.classList.contains('active');
      if (!wasOpen) track('faq_open', { question: el.textContent });
      return;
    }
    if (isBookCall(el)) {
      track('book_call_click', { cta_location: el.getAttribute('data-event-label') || (sec && sec.getAttribute('data-track')) || 'page' });
    }
    if (/^mailto:/.test(href)) track('contact_click', { method: 'email' });
    else if (/^tel:/.test(href)) track('contact_click', { method: 'phone' });
    else if (/wa\.me|whatsapp\.com/.test(href)) track('contact_click', { method: 'whatsapp' });

    var cls = typeof el.className === 'string' ? el.className : '';
    if (!sec && /(^|\s)btn(\s|$)/.test(cls)) {
      track('cta_click', { section_name: 'page', cta_name: ctaName(el), cta_text: el.textContent, cta_href: href });
    }
  }, true);

  // A booking completed in the Calendly pop-up (assets/js/calendly.js saves it; this only counts it).
  window.addEventListener('message', function (ev) {
    if (ev.origin !== 'https://calendly.com' || !ev.data || ev.data.event !== 'calendly.event_scheduled') return;
    track('book_call_scheduled', {});
    metaTrack('Schedule');
  });

  // Build With Us redirects to its thank-you page only after a successful send. Counted once per browser
  // session, so a reload does not count the lead twice.
  if (/^\/build-with-us\/thank-you(\.html)?$/.test(location.pathname)) {
    var counted = false;
    try { counted = sessionStorage.getItem('tomo_bwu_lead') === '1'; sessionStorage.setItem('tomo_bwu_lead', '1'); } catch (e) {}
    if (!counted) track('generate_lead', { form_name: 'build_with_us' });
  }

  // Form steps. The forms' own code is untouched; these listeners only watch.
  var FORMS = {
    'b2b-lead-form': 'home_discovery_form',
    'toolkit-download-form': 'guide_download',
    'hero-form': 'ebook_hero',
    'mid-form': 'ebook_mid',
    'project-form': 'build_with_us'
  };
  onReady(function () {
    var started = {}, sent = {};
    Object.keys(FORMS).forEach(function (id) {
      var f = document.getElementById(id);
      if (!f || f.tagName !== 'FORM') return;
      var name = FORMS[id];
      var viewed = false;
      function view() { if (!viewed) { viewed = true; track('form_view', { form_name: name }); } }
      // A pop-up form sits in every page, hidden with CSS, so being "on screen" says nothing: count it when its pop-up opens.
      var modal = f.closest('.modal-overlay');
      if (modal && 'MutationObserver' in window) {
        new MutationObserver(function () { if (modal.classList.contains('active')) view(); })
          .observe(modal, { attributes: true, attributeFilter: ['class'] });
      } else if (!modal && 'IntersectionObserver' in window) {
        var seen = new IntersectionObserver(function (entries) {
          if (entries.some(function (e) { return e.isIntersecting; })) { view(); seen.disconnect(); }
        }, { threshold: 0.3 });
        seen.observe(f);
      }
      f.addEventListener('input', function (ev) {
        if (started[name] || (ev.target && ev.target.name === 'hp_company_website')) return;
        started[name] = true;
        track('form_start', { form_name: name });
      });
      f.addEventListener('submit', function () { sent[name] = true; });
    });
    window.addEventListener('pagehide', function () {
      for (var name in started) if (!sent[name]) { sent[name] = true; track('form_abandon', { form_name: name }); }
    });
  });
})();
