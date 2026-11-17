/* Spam protection for website forms. Add data-guard to a <form> and load this script.
   It adds a hidden honeypot field ("website") and the time the form appeared ("t0"), and, when the site
   has a Cloudflare Turnstile key configured (/api/form-config), shows the Turnstile check.
   window.tomoGuard(form) returns the extra fields to send with the form data:
     { website, t0, turnstileToken }
   The server checks all of them (api/_lib/guard.js). */
(function () {
  var shownAt = Date.now();
  var siteKey = '';
  var configLoaded = fetch('/api/form-config', { headers: { Accept: 'application/json' } })
    .then(function (r) { return r.json(); })
    .then(function (j) { siteKey = (j && j.turnstileSiteKey) || ''; })
    .catch(function () {});

  function addHoneypot(form) {
    if (form.querySelector('input[name="website"]')) return;
    var wrap = document.createElement('div');
    wrap.setAttribute('aria-hidden', 'true');
    wrap.style.cssText = 'position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden;';
    wrap.innerHTML = '<label>Leave this empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label>';
    form.appendChild(wrap);
  }

  function addTurnstile(form) {
    if (!siteKey || form.querySelector('.cf-turnstile')) return;
    var box = document.createElement('div');
    box.className = 'cf-turnstile';
    box.setAttribute('data-sitekey', siteKey);
    box.style.margin = '0.75rem 0';
    var submit = form.querySelector('[type="submit"]');
    (submit && submit.parentNode ? submit.parentNode : form).insertBefore(box, submit || null);
    if (!document.querySelector('script[src*="challenges.cloudflare.com/turnstile"]')) {
      var s = document.createElement('script');
      s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
      s.async = true; s.defer = true;
      document.head.appendChild(s);
    } else if (window.turnstile) {
      window.turnstile.render(box);
    }
  }

  function init() {
    var forms = document.querySelectorAll('form[data-guard]');
    forms.forEach(addHoneypot);
    configLoaded.then(function () { forms.forEach(addTurnstile); });
  }

  window.tomoGuard = function (form) {
    var hp = form.querySelector('input[name="website"]');
    var ts = form.querySelector('input[name="cf-turnstile-response"]');
    return { website: hp ? hp.value : '', t0: shownAt, turnstileToken: ts ? ts.value : '' };
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
