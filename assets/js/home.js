/* B2B home page behaviour: reveal on scroll, hero parallax, the pinned "one request" story, the lead form.
 * Plain JS, no libraries. Respects prefers-reduced-motion and falls back to a stacked layout on small screens. */
(function () {
  'use strict';
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Reveal on scroll */
  var reveals = document.querySelectorAll('.h-reveal, .h-section-head, .h-cred-title, .h-start h2');
  if ('IntersectionObserver' in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
    }, { threshold: 0.18 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* Hero parallax: the three cards drift at different speeds */
  var cards = document.querySelectorAll('.h-hero-art .h-card');
  var speeds = [-0.06, 0.05, -0.12];

  /* Story */
  var story = document.querySelector('.h-story');
  var frame = story && story.querySelector('.h-story-frame');
  var intro = story && story.querySelector('.h-story-intro');
  var grid = story && story.querySelector('.h-story-grid');
  var steps = story ? story.querySelectorAll('.h-step') : [];
  var scenes = story ? story.querySelectorAll('.h-scene') : [];
  var fill = story && story.querySelector('.h-steps-fill');
  var current = -1;
  var isStatic = false;

  function setStatic() {
    var want = reduce || window.innerWidth < 900 || window.innerHeight < 560;
    if (!story || want === isStatic) return;
    isStatic = want;
    story.classList.toggle('is-static', isStatic);
    if (isStatic) {
      frame.style.transform = ''; frame.style.borderRadius = '';
      intro.style.opacity = ''; grid.style.opacity = '';
      scenes.forEach(function (s) { s.classList.add('on'); });
    } else { current = -1; }
  }

  function show(i) {
    if (i === current) return;
    current = i;
    steps.forEach(function (s, k) { s.classList.toggle('on', k <= i); });
    scenes.forEach(function (s, k) { s.classList.toggle('on', k === i); });
    if (fill && steps.length) {
      var last = steps[Math.max(i, 0)];
      fill.style.height = i < 0 ? '0px' : (last.offsetTop + 20) + 'px';
    }
    if (i >= 0 && window.tomoTrack) {
      var label = steps[i].getAttribute('data-step') || String(i + 1);
      if (!show.sent) show.sent = {};
      if (!show.sent[label]) { show.sent[label] = true; window.tomoTrack('story_step_view', label, { ga: true }); }
    }
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var y = window.scrollY;
      if (!reduce) cards.forEach(function (c, i) { c.style.transform = 'translate3d(0,' + (y * speeds[i]).toFixed(1) + 'px,0)'; });
      if (!story || isStatic) return;
      var r = story.getBoundingClientRect();
      var total = story.offsetHeight - window.innerHeight;
      var p = Math.min(1, Math.max(0, -r.top / total));
      // Phase 1 (0 to 0.16): the frame zooms from a card to the full screen, like a camera moving in.
      var z = Math.min(1, p / 0.16);
      var ease = 1 - Math.pow(1 - z, 3);
      var scale = 0.62 + 0.38 * ease;
      frame.style.transform = 'scale(' + scale.toFixed(4) + ')';
      frame.style.borderRadius = (36 * (1 - ease)).toFixed(1) + 'px';
      intro.style.opacity = String(Math.max(0, 1 - z * 1.6));
      grid.style.opacity = String(Math.min(1, Math.max(0, (z - 0.55) / 0.45)));
      // Phase 2 (0.16 to 1): four steps.
      var q = (p - 0.16) / 0.84;
      show(q < 0 ? -1 : Math.min(steps.length - 1, Math.floor(q * steps.length)));
    });
  }

  setStatic();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { setStatic(); onScroll(); });
  onScroll();

  /* Lead form -> /api/lead (Sheet row + Slack alert) */
  var form = document.getElementById('b2b-lead-form');
  if (form) {
    var status = form.querySelector('.h-form-status');
    var offerSel = form.querySelector('[name=offer_interest]');
    var loadedAt = Date.now();
    var submissionId = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);
    // Offer buttons elsewhere on the page can preselect the interest.
    document.querySelectorAll('[data-interest]').forEach(function (a) {
      a.addEventListener('click', function () { if (offerSel) offerSel.value = a.getAttribute('data-interest'); });
    });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!form.reportValidity()) return;
      var btn = form.querySelector('button[type=submit]');
      var original = btn.innerHTML;
      btn.disabled = true; btn.textContent = 'Sending...';
      status.className = 'h-form-status'; status.textContent = '';
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      data.type = 'discovery_request';
      data.page = location.pathname;
      data.form_loaded_at = loadedAt;
      data.submission_id = submissionId;
      if (window.tomoAttribution) { var a = window.tomoAttribution(); for (var k in a) data[k] = a[k]; }
      fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok && j && j.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error((res.j && res.j.error) || 'Something went wrong');
          if (window.tomoTrack) window.tomoTrack('generate_lead', { form_name: 'home_discovery_form' });
          if (window.tomoTrackLead) window.tomoTrackLead('home');
          form.querySelectorAll('.h-field, .row, button[type=submit], .fine').forEach(function (el) { el.style.display = 'none'; });
          status.className = 'h-form-status ok';
          status.innerHTML = '<strong>Thank you' + (res.j.name ? ', ' + String(res.j.name).replace(/[<>&"]/g, '') : '') + '.</strong> A co-founder will read this and reply within 24 hours. ' +
            'If a call is easier, <a href="https://calendly.com/avinashtomo/tomoclub-call" data-book-call>pick a 20-minute slot</a>.';
        })
        .catch(function (e) {
          btn.disabled = false; btn.innerHTML = original;
          status.className = 'h-form-status err';
          status.innerHTML = 'That did not go through (' + String(e.message).replace(/[<>&"]/g, '') + '). Please try again, or email <a href="mailto:avinash@tomoclub.org">avinash@tomoclub.org</a>.';
        });
    });
  }
})();
