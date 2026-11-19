/* "Book a 20-minute call" pop-up.
   Links with [data-book-call] open the Calendly pop-up instead of leaving the page. When Calendly reports a
   booking, the page sends the invitee to /api/lead (type call_booked), which saves a row and alerts Slack.
   If Calendly cannot load, or a modifier key is held, the link behaves as a normal link. */
(function () {
  var CALENDLY_URL = 'https://calendly.com/avinashtomo/tomoclub-call';
  var loading = null;

  function load() {
    if (window.Calendly) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise(function (resolve, reject) {
      var css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = 'https://assets.calendly.com/assets/external/widget.css';
      document.head.appendChild(css);
      var s = document.createElement('script');
      s.src = 'https://assets.calendly.com/assets/external/widget.js'; s.async = true;
      s.onload = resolve; s.onerror = function () { loading = null; reject(); };
      document.head.appendChild(s);
    });
    return loading;
  }

  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('[data-book-call]');
    if (!el || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
    ev.preventDefault();
    var href = el.getAttribute('href');
    var url = href && /calendly\.com/.test(href) ? href : CALENDLY_URL;
    load().then(function () { window.Calendly.initPopupWidget({ url: url }); })
      .catch(function () { window.open(url, '_blank', 'noopener'); });
  }, true);

  window.addEventListener('message', function (ev) {
    if (ev.origin !== 'https://calendly.com' || !ev.data || ev.data.event !== 'calendly.event_scheduled') return;
    var uri = ev.data.payload && ev.data.payload.invitee && ev.data.payload.invitee.uri;
    if (!uri) return;
    var body = { type: 'call_booked', invitee_uri: uri, page: location.pathname };
    if (window.tomoAttribution) { var a = window.tomoAttribution(); for (var k in a) body[k] = a[k]; }
    fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(function () {});
  });
})();
