/* TomoClub site analytics — one file, loaded on every page.
 *
 *   <script defer src="/analytics.js"></script>   (already added before </head> on every page)
 *
 * Fill in the two IDs below. Nothing else needs editing.
 *   GA4          : Google Analytics property already used on the site.
 *   LINKEDIN     : LinkedIn Campaign Manager → Analyze → Insight Tag → "I will use a tag manager"
 *                  → copy the Partner ID (a number like 1234567).
 *   CLARITY      : clarity.microsoft.com → New project → Settings → Setup → copy the Project ID
 *                  (a short code like "abc1def2gh").
 * Leave an ID as '' to skip that tool.
 *
 * Also sends GA4 events:
 *   section_view   { section_name, engagement_ms }   when a section leaves the screen or the page is closed,
 *                                                     for any element with a data-track="name" attribute
 *   cta_click      { cta_text, cta_href }             for links/buttons inside data-track sections
 *   lead_submitted { form_id }                        when the Build With Us form is submitted
 */
(function () {
  var CONFIG = {
    GA4: 'G-FEGGQ2ZDMT',
    LINKEDIN_PARTNER_ID: '',      // e.g. '1234567'
    CLARITY_PROJECT_ID: ''        // e.g. 'abc1def2gh'
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

  /* ── 4. Section engagement → GA4 events ─────────────────────────────── */
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
