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

  /* Lead form (not wired up yet) */
  var form = document.getElementById('b2b-lead-form');
  if (form) {
    var offerSel = form.querySelector('[name=offer_interest]');
    // Offer buttons elsewhere on the page can preselect the interest.
    document.querySelectorAll('[data-interest]').forEach(function (a) {
      a.addEventListener('click', function () { if (offerSel) offerSel.value = a.getAttribute('data-interest'); });
    });
    // No submit action yet: stop Enter from reloading the page with the form data in the URL.
    form.addEventListener('submit', function (ev) { ev.preventDefault(); });
  }
})();
