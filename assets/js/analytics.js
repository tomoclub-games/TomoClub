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
 *   cta_click      { cta_text, cta_href }             for links/buttons inside data-track sections
 *   lead_submitted { form_id }                        when the Build With Us form is submitted
 *
 * Meta Pixel events (besides PageView on every page):
 *   Lead    { content_name }   Build With Us thank-you page, contact-page Tally form submit,
 *                              or a page calling window.tomoTrackLead(name) after its own form succeeds
 *   Contact { content_name }   click on any WhatsApp link
 */
(function () {
  var CONFIG = {
    GA4: 'G-FEGGQ2ZDMT',
    LINKEDIN_PARTNER_ID: '8364153',
    CLARITY_PROJECT_ID: 'yibamjl9lq',
    LEADSY_PID: 'Er26IyzOijeMy17O',
    META_PIXEL_ID: '1805331960518408'
  };

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
})();
