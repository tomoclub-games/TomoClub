/* "Book a 20-minute call" pop-up.
   Links with [data-book-call] open our own booking pop-up: pick a day and time, then name, email and the reason
   for the call. Open times come live from Calendly through /api/call (fetched quietly after the page loads, so the
   calendar is ready when the pop-up opens), and /api/call books the call in Calendly, which sends the invite and
   meeting link. If the times cannot load or the booking fails, the visitor can open the Calendly pop-up instead;
   a booking made there is still saved through /api/lead (type call_booked).
   A modifier-key click (new tab) behaves as a normal link. */
(function () {
  var CALENDLY_URL = 'https://calendly.com/avinashtomo/tomoclub-call';
  var TZ = (function () { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { return ''; } })();
  var MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  var S = { slots: null, minutes: 20, load: 'idle', fetchedAt: 0, step: 1, month: 0, date: null, slot: null,
    name: '', email: '', reason: '', guests: '', showGuests: false, hp: '', busy: false, error: '', started: false,
    done: false, sid: '' };
  var overlay = null, box = null, lastFocus = null, pending = null, isOpen = false;

  function track(name, params) { if (window.tomoTrack) window.tomoTrack(name, params || {}); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function newId() { return (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2); }
  function dayKey(d) { return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }
  function timeLabel(iso) { return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }); }
  function dateLabel(iso) { return new Date(iso).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }); }
  function tzShort(d) {
    try { var p = new Intl.DateTimeFormat('en-US', { timeZoneName: 'short' }).formatToParts(d || new Date()); for (var i = 0; i < p.length; i++) if (p[i].type === 'timeZoneName') return p[i].value; } catch (e) {}
    return '';
  }
  function tzText() { var s = tzShort(); return (TZ ? TZ.replace(/_/g, ' ') : 'your local time') + (s ? ' (' + s + ')' : ''); }
  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i.test(String(v || '').trim()); }
  function guestList() { return S.guests.split(/[\s,;]+/).map(function (g) { return g.trim(); }).filter(Boolean); }
  function detailsOk() { var g = guestList(); return !!(S.name.trim() && validEmail(S.email) && S.reason.trim() && g.length <= 10 && g.every(validEmail)); }

  /* ---------- open times ---------- */
  function fetchSlots(force) {
    if (pending) return pending;
    if (!force && S.slots && Date.now() - S.fetchedAt < 2 * 60 * 1000) return Promise.resolve();
    if (!S.slots) S.load = 'loading';
    pending = fetch('/api/call', { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (!j || !j.ok || !Array.isArray(j.slots)) throw new Error('bad response');
        S.slots = j.slots; S.minutes = j.minutes || 20; S.fetchedAt = Date.now(); S.load = 'ok';
        if (S.slot && S.slots.indexOf(S.slot) < 0) { S.slot = null; if (S.step === 2) S.step = 1; }
      })
      .catch(function () { S.load = S.slots ? 'ok' : 'error'; })
      .then(function () { pending = null; if (isOpen) { pickFirstDate(); render(); } });
    return pending;
  }
  function byDay() {
    var m = {};
    (S.slots || []).forEach(function (iso) { var k = dayKey(new Date(iso)); (m[k] = m[k] || []).push(iso); });
    return m;
  }
  function months() {
    var now = new Date(), first = new Date(now.getFullYear(), now.getMonth(), 1), out = [first];
    var last = S.slots && S.slots.length ? new Date(S.slots[S.slots.length - 1]) : now;
    var span = (last.getFullYear() - now.getFullYear()) * 12 + last.getMonth() - now.getMonth();
    for (var i = 1; i <= span; i++) out.push(new Date(now.getFullYear(), now.getMonth() + i, 1));
    return out;
  }
  function pickFirstDate() {
    if (S.date || !S.slots || !S.slots.length) return;
    var f = new Date(S.slots[0]), now = new Date();
    S.date = dayKey(f);
    S.month = (f.getFullYear() - now.getFullYear()) * 12 + f.getMonth() - now.getMonth();
  }

  /* ---------- pop-up ---------- */
  var CSS = '' +
    '.tcb-overlay{position:fixed;inset:0;z-index:4000;background:rgba(15,23,42,.6);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;transition:opacity .2s}' +
    '.tcb-overlay.on{opacity:1}' +
    '.tcb-box{position:relative;background:#fff;color:#0F172A;font-family:var(--font-family,Outfit,system-ui,sans-serif);width:100%;max-width:760px;max-height:calc(100vh - 32px);overflow-y:auto;border-radius:24px;box-shadow:0 30px 80px rgba(0,0,0,.3);padding:28px;text-align:left;transform:translateY(16px);transition:transform .25s cubic-bezier(.16,1,.3,1)}' +
    '.tcb-overlay.on .tcb-box{transform:none}' +
    '.tcb-box *{box-sizing:border-box}' +
    '.tcb-box h2,.tcb-box h3,.tcb-box strong,.tcb-box label{color:#0F172A;letter-spacing:normal}' +
    '.tcb-close{position:absolute;top:16px;right:16px;width:36px;height:36px;border-radius:50%;border:0;background:#F1F5F9;color:#475569;font-size:22px;line-height:1;cursor:pointer}' +
    '.tcb-close:hover{background:#E2E8F0}' +
    '.tcb-head{padding-right:44px;margin-bottom:20px}' +
    '.tcb-head h2{margin:0 0 4px;font-size:1.5rem;line-height:1.25;color:#0F172A}' +
    '.tcb-head p{margin:0;color:#64748B;font-size:.95rem}' +
    '.tcb-cols{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);gap:28px}' +
    '.tcb-mhead{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}' +
    '.tcb-mhead strong{font-size:1.05rem}' +
    '.tcb-nav{width:36px;height:36px;border-radius:50%;border:1px solid #CBD5E1;background:#fff;color:#0F172A;font-size:18px;cursor:pointer}' +
    '.tcb-nav:disabled{opacity:.35;cursor:default}' +
    '.tcb-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:4px;text-align:center}' +
    '.tcb-dow{font-size:.75rem;font-weight:600;color:#64748B;padding:4px 0}' +
    '.tcb-day{font:inherit;font-size:.95rem;aspect-ratio:1;max-height:44px;border-radius:50%;border:0;background:transparent;color:#94A3B8;cursor:default;padding:0}' +
    '.tcb-day.av{background:rgba(42,180,184,.12);color:#0E6E72;font-weight:700;cursor:pointer}' +
    '.tcb-day.av:hover{background:rgba(42,180,184,.25)}' +
    '.tcb-day.sel{background:#2AB4B8;color:#fff}' +
    '.tcb-times h3{margin:0 0 4px;font-size:1rem}' +
    '.tcb-tz{margin:0 0 12px;font-size:.82rem;color:#64748B}' +
    '.tcb-tlist{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px;max-height:300px;overflow-y:auto;padding:2px}' +
    '.tcb-time{font:inherit;font-weight:600;min-height:44px;border-radius:12px;border:1.5px solid #2AB4B8;background:#fff;color:#0E6E72;cursor:pointer}' +
    '.tcb-time:hover{background:rgba(42,180,184,.08)}' +
    '.tcb-time.sel{background:#2AB4B8;color:#fff}' +
    '.tcb-btn{font:inherit;font-weight:700;font-size:1rem;min-height:50px;padding:12px 24px;border-radius:999px;border:0;background:#2AB4B8;color:#fff;cursor:pointer;width:100%;box-shadow:0 10px 30px rgba(42,180,184,.3)}' +
    '.tcb-btn:disabled{opacity:.45;cursor:default;box-shadow:none}' +
    '.tcb-link{font:inherit;font-weight:600;background:none;border:0;padding:4px 0;color:#0E6E72;text-decoration:underline;cursor:pointer}' +
    '.tcb-msg{margin:0;color:#64748B;font-size:.95rem}' +
    '.tcb-err{margin:0 0 14px;background:rgba(179,65,88,.1);color:#8C2B40;border-radius:12px;padding:10px 14px;font-size:.92rem;font-weight:600}' +
    '.tcb-pick{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;background:#F1F5F9;border-radius:14px;padding:12px 16px;margin-bottom:18px}' +
    '.tcb-form{max-width:520px}' +
    '.tcb-f{display:block;margin-bottom:14px}' +
    '.tcb-f span{display:block;font-weight:600;font-size:.92rem;margin-bottom:6px}' +
    '.tcb-f input,.tcb-f textarea{width:100%;font:inherit;font-size:1rem;color:#0F172A;background:#fff;border:1px solid #CBD5E1;border-radius:12px;padding:12px 14px;outline:none}' +
    '.tcb-f textarea{min-height:90px;resize:vertical}' +
    '.tcb-f input:focus,.tcb-f textarea:focus{border-color:#2AB4B8;box-shadow:0 0 0 4px rgba(42,180,184,.12)}' +
    '.tcb-guest{display:inline-block;font:inherit;font-weight:600;font-size:.9rem;padding:8px 16px;border-radius:999px;border:1.5px solid #2AB4B8;background:#fff;color:#0E6E72;cursor:pointer;margin:0 0 14px}' +
    '.tcb-fine{margin:12px 0 0;font-size:.8rem;color:#64748B;text-align:center}' +
    '.tcb-fine a{color:inherit}' +
    '.tcb-done{text-align:center;padding:12px 0 4px}' +
    '.tcb-tick{width:64px;height:64px;border-radius:50%;background:rgba(42,180,184,.15);color:#2AB4B8;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:32px;font-weight:700}' +
    '.tcb-done h2{margin:0 0 8px}' +
    '.tcb-done p{margin:0 auto 10px;max-width:420px;color:#475569}' +
    '.tcb-when{display:inline-block;background:#F1F5F9;border-radius:12px;padding:10px 16px;font-weight:700;color:#0F172A!important}' +
    '.tcb-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}' +
    '@media (max-width:720px){.tcb-cols{grid-template-columns:1fr;gap:20px}.tcb-tlist{max-height:none}}' +
    '@media (max-width:600px){.tcb-overlay{align-items:flex-end;padding:0}.tcb-box{border-radius:20px 20px 0 0;max-height:92vh;padding:22px 16px}}';

  function build() {
    if (overlay) return;
    var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
    overlay = document.createElement('div');
    overlay.className = 'tcb-overlay';
    overlay.innerHTML = '<div class="tcb-box" role="dialog" aria-modal="true" aria-labelledby="tcb-title" tabindex="-1"></div>';
    box = overlay.firstChild;
    overlay.addEventListener('click', onClick);
    overlay.addEventListener('input', onInput);
    overlay.addEventListener('keydown', onKey);
  }

  function open(trigger) {
    build();
    lastFocus = trigger || document.activeElement;
    if (S.done) { S.done = false; S.step = 1; S.slot = null; S.date = null; S.reason = ''; S.guests = ''; S.showGuests = false; }
    if (!S.sid) S.sid = newId();
    S.error = '';
    S.step = 1; // always reopen on the calendar; the picked time and typed details are kept
    isOpen = true;
    pickFirstDate();
    render();
    document.body.appendChild(overlay);
    document.documentElement.style.overflow = 'hidden';
    requestAnimationFrame(function () { overlay.classList.add('on'); box.focus(); });
    track('form_view', { form_name: 'book_call' });
    fetchSlots(false);
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    overlay.classList.remove('on');
    document.documentElement.style.overflow = '';
    setTimeout(function () { if (!isOpen && overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 200);
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (e) {} }
  }

  function render() {
    var h = '<button type="button" class="tcb-close" data-x aria-label="Close">&times;</button>';
    if (S.done) {
      h += '<div class="tcb-done"><div class="tcb-tick" aria-hidden="true">&#10003;</div><h2 id="tcb-title">You are booked</h2>' +
        '<p class="tcb-when">' + esc(dateLabel(S.slot) + ', ' + timeLabel(S.slot) + ' ' + tzShort(new Date(S.slot))) + '</p>' +
        '<p>A calendar invite with the meeting link is on its way to ' + esc(S.email.trim()) + '.</p>' +
        '<p style="margin-bottom:20px">Need to change the time? Use the link in that email.</p>' +
        '<button type="button" class="tcb-btn" data-x style="max-width:240px">Done</button></div>';
      box.innerHTML = h;
      return;
    }
    h += '<div class="tcb-head"><h2 id="tcb-title">Book a ' + esc(S.minutes) + '-minute call</h2><p>Pick a time that suits you. You will get a calendar invite with the video link.</p></div>';
    if (S.step === 2 && S.slot) {
      h += '<div class="tcb-form"><div class="tcb-pick"><strong>' + esc(dateLabel(S.slot) + ', ' + timeLabel(S.slot) + ' ' + tzShort(new Date(S.slot))) + '</strong><button type="button" class="tcb-link" data-back>Change time</button></div>' +
        (S.error ? '<p class="tcb-err" role="alert">' + S.error + '</p>' : '') +
        '<label class="tcb-f"><span>Name *</span><input name="name" type="text" autocomplete="name" value="' + esc(S.name) + '" required></label>' +
        '<label class="tcb-f"><span>Email *</span><input name="email" type="email" autocomplete="email" value="' + esc(S.email) + '" required></label>' +
        (S.showGuests
          ? '<label class="tcb-f"><span>Guest emails</span><input name="guests" type="text" autocomplete="off" placeholder="Separate emails with commas (up to 10)" value="' + esc(S.guests) + '"></label>'
          : '<button type="button" class="tcb-guest" data-guests>Add guests</button>') +
        '<label class="tcb-f"><span>Reason for the meeting *</span><textarea name="reason" required>' + esc(S.reason) + '</textarea></label>' +
        '<div class="tcb-hp" aria-hidden="true"><label>Leave this empty<input name="hp" tabindex="-1" autocomplete="off" value=""></label></div>' +
        '<button type="button" class="tcb-btn" data-book' + (detailsOk() && !S.busy ? '' : ' disabled') + '>' + (S.busy ? 'Booking&hellip;' : 'Schedule the call') + '</button>' +
        '<p class="tcb-fine">By booking you agree to our <a href="/privacy-policy" target="_blank" rel="noopener">privacy policy</a>.</p></div>';
      box.innerHTML = h;
      return;
    }
    if (S.error) h += '<p class="tcb-err" role="alert">' + S.error + '</p>';
    if (S.load === 'loading' || S.load === 'idle') {
      h += '<p class="tcb-msg" role="status">Loading available times&hellip;</p>';
    } else if (S.load === 'error') {
      h += '<p class="tcb-msg" role="alert" style="margin-bottom:14px">We could not load the available times.</p>' +
        '<button type="button" class="tcb-btn" data-calendly style="max-width:320px">Open the booking page instead</button>' +
        '<p class="tcb-fine" style="text-align:left">Or <button type="button" class="tcb-link" data-retry>try again</button>.</p>';
    } else if (!S.slots.length) {
      h += '<p class="tcb-msg">There are no open times in the next four weeks. Email <a href="mailto:avinash@tomoclub.org">avinash@tomoclub.org</a> and we will find a time.</p>';
    } else {
      var days = byDay(), ms = months(), mi = Math.max(0, Math.min(ms.length - 1, S.month)), first = ms[mi];
      var dim = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate(), lead = (first.getDay() + 6) % 7;
      var cal = '<div class="tcb-mhead"><button type="button" class="tcb-nav" data-month="-1" aria-label="Previous month"' + (mi <= 0 ? ' disabled' : '') + '>&lsaquo;</button>' +
        '<strong>' + MON[first.getMonth()] + ' ' + first.getFullYear() + '</strong>' +
        '<button type="button" class="tcb-nav" data-month="1" aria-label="Next month"' + (mi >= ms.length - 1 ? ' disabled' : '') + '>&rsaquo;</button></div>' +
        '<div class="tcb-grid">' + ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(function (x) { return '<span class="tcb-dow">' + x + '</span>'; }).join('');
      for (var k = 0; k < lead; k++) cal += '<span></span>';
      for (var d = 1; d <= dim; d++) {
        var dt = new Date(first.getFullYear(), first.getMonth(), d), key = dayKey(dt), av = !!days[key], sel = av && S.date === key;
        var lbl = DOW[dt.getDay()] + ' ' + d + ' ' + MON[dt.getMonth()];
        cal += '<button type="button" class="tcb-day' + (av ? ' av' : '') + (sel ? ' sel' : '') + '"' + (av ? ' data-date="' + key + '"' : ' disabled') +
          ' aria-pressed="' + sel + '" aria-label="' + lbl + (av ? ', available' : ', no times') + '">' + d + '</button>';
      }
      cal += '</div>';
      var times = S.date ? (days[S.date] || []) : [];
      var right = times.length
        ? '<h3>' + esc(dateLabel(times[0])) + '</h3><p class="tcb-tz">Times in ' + esc(tzText()) + '</p><div class="tcb-tlist">' +
          times.map(function (iso) { return '<button type="button" class="tcb-time' + (S.slot === iso ? ' sel' : '') + '" data-slot="' + esc(iso) + '" aria-pressed="' + (S.slot === iso) + '">' + timeLabel(iso) + '</button>'; }).join('') +
          '</div><div style="margin-top:16px"><button type="button" class="tcb-btn" data-next' + (S.slot && times.indexOf(S.slot) >= 0 ? '' : ' disabled') + '>Next</button></div>'
        : '<p class="tcb-msg">Pick a highlighted day to see the times.</p>';
      h += '<div class="tcb-cols"><div>' + cal + '</div><div class="tcb-times">' + right + '</div></div>';
    }
    box.innerHTML = h;
  }

  function onInput(e) {
    var n = e.target.name;
    if (n === 'hp') { S.hp = e.target.value; return; }
    if (!(n in S)) return;
    S[n] = e.target.value;
    if (!S.started) { S.started = true; track('form_start', { form_name: 'book_call' }); }
    var b = box.querySelector('[data-book]'); if (b) b.disabled = !detailsOk() || S.busy;
  }

  function onKey(e) {
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key !== 'Tab') return;
    var f = box.querySelectorAll('button:not([disabled]), input:not([tabindex="-1"]), textarea, a[href]');
    if (!f.length) return;
    var a = f[0], z = f[f.length - 1];
    if (e.shiftKey && (document.activeElement === a || document.activeElement === box)) { e.preventDefault(); z.focus(); }
    else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
  }

  function focusSoon(sel) { setTimeout(function () { var el = box.querySelector(sel); if (el) el.focus(); }, 0); }

  function onClick(e) {
    if (e.target === overlay) { close(); return; }
    var t = e.target.closest('button'); if (!t || t.disabled) return;
    if (t.hasAttribute('data-x')) close();
    else if (t.hasAttribute('data-month')) { S.month = Math.max(0, S.month + Number(t.getAttribute('data-month'))); render(); focusSoon('.tcb-mhead'); }
    else if (t.hasAttribute('data-date')) { S.date = t.getAttribute('data-date'); S.slot = null; S.error = ''; render(); focusSoon('.tcb-time'); }
    else if (t.hasAttribute('data-slot')) { S.slot = t.getAttribute('data-slot'); S.error = ''; render(); focusSoon('[data-next]'); }
    else if (t.hasAttribute('data-next')) { S.step = 2; S.error = ''; track('book_call_time_selected', {}); render(); focusSoon('input[name=name]'); }
    else if (t.hasAttribute('data-back')) { S.step = 1; S.error = ''; render(); }
    else if (t.hasAttribute('data-guests')) { S.showGuests = true; render(); focusSoon('input[name=guests]'); }
    else if (t.hasAttribute('data-retry')) { fetchSlots(true); render(); }
    else if (t.hasAttribute('data-calendly')) { track('book_call_fallback', {}); close(); openCalendly(); }
    else if (t.hasAttribute('data-book')) book();
  }

  function book() {
    if (S.busy || !S.slot || !detailsOk()) return;
    S.busy = true; S.error = ''; render();
    var body = { start: S.slot, name: S.name.trim(), email: S.email.trim(), reason: S.reason.trim(), guests: guestList(), timezone: TZ || 'UTC',
      page: location.pathname, hp_company_website: S.hp, submission_id: S.sid };
    if (window.tomoAttribution) { var a = window.tomoAttribution(); for (var k in a) body[k] = a[k]; }
    fetch('/api/call', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { return r.json().catch(function () { return null; }); })
      .catch(function () { return null; })
      .then(function (j) {
        S.busy = false;
        if (j && j.ok) {
          S.done = true; S.sid = ''; S.started = false;
          S.slots = (S.slots || []).filter(function (x) { return x !== S.slot; });
          try { window.dispatchEvent(new CustomEvent('tomo:call-booked')); } catch (e) {}
        } else if (j && j.code === 'slot_taken') {
          track('book_call_failed', { reason: 'slot_taken' });
          S.slots = (S.slots || []).filter(function (x) { return x !== S.slot; });
          S.slot = null; S.step = 1; S.error = 'Sorry, that time was just taken. Please pick another.';
          fetchSlots(true);
        } else if (j && (j.code === 'invalid' || j.code === 'too_many')) {
          track('book_call_failed', { reason: j.code });
          S.error = esc(j.error || 'Please check your details.');
        } else {
          track('book_call_failed', { reason: 'error' });
          S.error = 'Sorry, we could not complete the booking. <button type="button" class="tcb-link" data-calendly>Book on the Calendly page instead</button> or email <a href="mailto:avinash@tomoclub.org">avinash@tomoclub.org</a>.';
        }
        render();
      });
  }

  /* ---------- fallback: the Calendly pop-up ---------- */
  var loading = null;
  function loadCalendly() {
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
  function openCalendly() {
    loadCalendly().then(function () { window.Calendly.initPopupWidget({ url: CALENDLY_URL }); })
      .catch(function () { window.open(CALENDLY_URL, '_blank', 'noopener'); });
  }
  window.addEventListener('message', function (ev) {
    if (ev.origin !== 'https://calendly.com' || !ev.data || ev.data.event !== 'calendly.event_scheduled') return;
    var uri = ev.data.payload && ev.data.payload.invitee && ev.data.payload.invitee.uri;
    if (!uri) return;
    var body = { type: 'call_booked', invitee_uri: uri, page: location.pathname };
    if (window.tomoAttribution) { var a = window.tomoAttribution(); for (var k in a) body[k] = a[k]; }
    fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).catch(function () {});
  });

  /* ---------- wiring ---------- */
  document.addEventListener('click', function (ev) {
    var el = ev.target.closest && ev.target.closest('[data-book-call]');
    if (!el || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.button > 0) return;
    ev.preventDefault();
    open(el);
  }, true);

  window.addEventListener('pagehide', function () {
    if (S.started && !S.done) { S.started = false; track('form_abandon', { form_name: 'book_call' }); }
  });

  // Fetch the open times quietly once the page has settled, so the calendar is ready when the pop-up opens.
  function prefetch() { if (document.querySelector('[data-book-call]')) fetchSlots(false); }
  function later() { (window.requestIdleCallback || function (f) { setTimeout(f, 1500); })(prefetch, { timeout: 4000 }); }
  if (document.readyState === 'complete') later(); else window.addEventListener('load', later);
  document.addEventListener('pointerover', function (ev) {
    if (ev.target.closest && ev.target.closest('[data-book-call]')) fetchSlots(false);
  }, { passive: true });
})();
