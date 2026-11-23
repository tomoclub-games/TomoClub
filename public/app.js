// District Assistant front end (no framework). Talks only to this app's /api.
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const state = { district: null, history: [], tab: 'read', poll: null, leadStarted: Date.now() };

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      ...opts,
      headers: opts.body instanceof FormData ? {} : { 'content-type': 'application/json' },
    });
    let data = {};
    try {
      data = await res.json();
    } catch {
      /* non-JSON */
    }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status}).`);
    return data;
  }

  function show(id) {
    for (const s of ['start', 'processing', 'workspace']) $(`#${s}`).hidden = s !== id;
  }
  function setError(el, msg) {
    el.textContent = msg || '';
    el.hidden = !msg;
  }
  function setUrlParam(id) {
    const u = new URL(location.href);
    if (id) u.searchParams.set('d', id);
    else u.searchParams.delete('d');
    history.replaceState(null, '', u);
  }

  // ---------- start ----------
  $('#url-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.submitter || $('#url-form button');
    const url = $('#district-url').value.trim();
    setError($('#url-error'), '');
    if (!url) return setError($('#url-error'), 'Please enter a district website address.');
    btn.disabled = true;
    try {
      const { district } = await api('/api/districts', { method: 'POST', body: JSON.stringify({ url }) });
      openDistrict(district);
    } catch (err) {
      setError($('#url-error'), err.message);
    } finally {
      btn.disabled = false;
    }
  });

  $('#show-upload-only').addEventListener('click', () => {
    const f = $('#upload-only-form');
    f.hidden = !f.hidden;
    if (!f.hidden) f.querySelector('input').focus();
  });

  $('#upload-only-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const err = form.querySelector('.form-error');
    const btn = form.querySelector('button');
    setError(err, '');
    const name = form.elements.namedItem('name').value.trim();
    const files = form.elements.namedItem('files').files;
    if (!name || !files.length) return setError(err, 'Please enter the district name and choose at least one PDF.');
    btn.disabled = true;
    btn.textContent = 'Reading PDFs...';
    try {
      const { district } = await api('/api/districts/upload-only', { method: 'POST', body: JSON.stringify({ name }) });
      const fd = new FormData();
      for (const f of files) fd.append('files', f);
      const out = await api(`/api/districts/${district.id}/documents`, { method: 'POST', body: fd });
      const failed = out.results.filter((r) => r.status === 'failed');
      if (failed.length === out.results.length) {
        setError(err, failed.map((r) => r.message).join(' '));
      } else {
        openDistrict(out.district);
      }
    } catch (ex) {
      setError(err, ex.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Upload and build';
    }
  });

  // ---------- processing ----------
  function openDistrict(d) {
    state.district = d;
    state.history = [];
    $('#chat-log').innerHTML = '';
    setUrlParam(d.id);
    if (d.status === 'ready') return renderWorkspace(d);
    if (d.status === 'failed') return renderFailed(d);
    renderProcessing(d);
    clearInterval(state.poll);
    state.poll = setInterval(async () => {
      try {
        const { district } = await api(`/api/districts/${d.id}`);
        state.district = district;
        if (district.status === 'ready') {
          clearInterval(state.poll);
          renderWorkspace(district);
        } else if (district.status === 'failed') {
          clearInterval(state.poll);
          renderFailed(district);
        } else {
          renderProcessing(district);
        }
      } catch {
        /* keep polling */
      }
    }, 1500);
  }

  function renderProcessing(d) {
    show('processing');
    $('#proc-title').textContent = `Reading ${d.name || 'the district website'}`;
    $('#proc-message').textContent = d.message || 'Working';
    $('#proc-url').textContent = d.currentUrl ? `Now reading: ${d.currentUrl}` : '';
    $('#proc-pages').textContent = d.counts.pages;
    $('#proc-pdfs').textContent = d.counts.pdfs;
    $('#proc-failed').textContent = d.counts.notRead;
  }

  function renderFailed(d) {
    show('start');
    setUrlParam(null);
    setError($('#url-error'), d.message || 'This website could not be read.');
    if (d.sources?.length) {
      const reasons = d.sources.filter((s) => s.reason).slice(0, 3).map((s) => `${s.title || s.url}: ${s.reason}`);
      if (reasons.length) $('#url-error').textContent += ` Details: ${reasons.join(' | ')}`;
    }
  }

  // ---------- workspace ----------
  function renderWorkspace(d) {
    show('workspace');
    $('#district-name').textContent = d.name;
    const site = d.website ? `<a href="${esc(d.website)}" target="_blank" rel="noopener">${esc(new URL(d.website).hostname)}</a>` : 'Uploaded documents only';
    const read = new Date(d.updatedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
    $('#district-meta').innerHTML = `${site} &middot; ${plural(d.counts.pages, 'page')} and ${plural(d.counts.pdfs, 'document')} read on ${esc(read)}`;

    $('#categories').innerHTML = d.categories.length
      ? d.categories.map((c) => `<span class="chip">${esc(c.label)} <b>${c.count}</b></span>`).join('')
      : '<span class="chip">No common categories detected yet</span>';

    renderSuggestions(d.suggestedQuestions);
    renderSources();
    if (!$('#chat-log').children.length) {
      addBot(`<p>Ask a question about ${esc(d.name)}. Every answer links to the page or document it came from.</p>`);
    }
  }

  function renderSuggestions(list) {
    const box = $('#suggestions');
    box.innerHTML = '';
    for (const q of list || []) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = q;
      b.addEventListener('click', () => ask(q));
      box.append(b);
    }
  }

  function renderSources() {
    const d = state.district;
    const good = d.sources.filter((s) => ['ok', 'partial'].includes(s.status));
    const bad = d.sources.filter((s) => ['failed', 'skipped'].includes(s.status));
    $('#tab-read').textContent = `Read (${good.length})`;
    $('#tab-notread').textContent = `Not read (${bad.length})`;
    for (const b of document.querySelectorAll('.tabs button')) b.setAttribute('aria-selected', String(b.dataset.tab === state.tab));
    const list = state.tab === 'read' ? good : bad;
    $('#source-list').innerHTML =
      list
        .map((s) => {
          const kind = s.kind === 'page' ? 'Web page' : s.kind === 'pdf' ? `PDF${s.pages ? `, ${s.pages} pages` : ''}` : `Uploaded PDF${s.pages ? `, ${s.pages} pages` : ''}`;
          const name = s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.url)}</a>` : esc(s.title);
          const cls = s.status === 'partial' ? 'partial' : ['failed', 'skipped'].includes(s.status) ? 'bad' : '';
          return `<li class="${cls}">${name}<span class="meta">${kind}${s.reason ? ` &middot; ${esc(s.reason)}` : ''}</span></li>`;
        })
        .join('') || `<li class="meta">${state.tab === 'read' ? 'Nothing read yet.' : 'Everything that was tried could be read.'}</li>`;
  }

  for (const b of document.querySelectorAll('.tabs button')) {
    b.addEventListener('click', () => {
      state.tab = b.dataset.tab;
      renderSources();
    });
  }

  $('#new-district').addEventListener('click', () => {
    clearInterval(state.poll);
    state.district = null;
    setUrlParam(null);
    $('#district-url').value = '';
    show('start');
    $('#district-url').focus();
  });

  $('#upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const out = form.querySelector('.upload-result');
    const files = form.elements.namedItem('files').files;
    if (!files.length) {
      out.textContent = 'Choose one or more PDF files first.';
      return;
    }
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    const btn = form.querySelector('button');
    btn.disabled = true;
    out.textContent = 'Reading...';
    try {
      const r = await api(`/api/districts/${state.district.id}/documents`, { method: 'POST', body: fd });
      out.textContent = r.results.map((x) => x.message).join(' ');
      state.district = r.district;
      renderWorkspace(r.district);
      form.reset();
    } catch (ex) {
      out.textContent = ex.message;
    } finally {
      btn.disabled = false;
    }
  });

  // ---------- chat ----------
  function addMsg(cls, html) {
    const div = document.createElement('div');
    div.className = `msg ${cls}`;
    div.innerHTML = html;
    $('#chat-log').append(div);
    $('#chat-log').scrollTop = $('#chat-log').scrollHeight;
    return div;
  }
  const addBot = (html) => addMsg('msg-bot', html);

  function formatAnswer(text, citations) {
    const byN = new Map(citations.map((c) => [c.n, c]));
    const inline = (line) =>
      esc(line).replace(/\[(\d+)\]/g, (m, n) => {
        const c = byN.get(Number(n));
        if (!c) return '';
        return c.url
          ? `<a class="cite" href="${esc(c.url)}" target="_blank" rel="noopener" title="${esc(c.title)}">[${n}]</a>`
          : `<span class="cite" title="${esc(c.title)}">[${n}]</span>`;
      });
    const lines = text.split(/\n+/).map((l) => l.trim()).filter(Boolean);
    let html = '';
    let inList = false;
    for (const l of lines) {
      const item = l.match(/^([-*•]|\d+[.)])\s+(.*)$/);
      if (item) {
        if (!inList) html += '<ul>';
        inList = true;
        html += `<li>${inline(item[2])}</li>`;
      } else {
        if (inList) html += '</ul>';
        inList = false;
        html += `<p>${inline(l)}</p>`;
      }
    }
    if (inList) html += '</ul>';
    return html;
  }

  function sourcesHtml(citations) {
    if (!citations.length) return '';
    return `<div class="msg-sources"><strong>Sources</strong><ol>${citations
      .map((c) => {
        const label = `${esc(c.title)}${c.page ? `, page ${c.page}` : ''}`;
        return `<li>${c.url ? `<a href="${esc(c.url)}" target="_blank" rel="noopener">${label}</a>` : `${label} (uploaded)`}</li>`;
      })
      .join('')}</ol></div>`;
  }

  async function ask(question) {
    const q = String(question || '').trim();
    if (!q || !state.district) return;
    addMsg('msg-user', `<p>${esc(q)}</p>`);
    $('#question').value = '';
    const thinking = addMsg('msg-thinking', '<p>Searching the district’s documents...</p>');
    const btn = $('#ask-form button');
    btn.disabled = true;
    try {
      const r = await api(`/api/districts/${state.district.id}/ask`, {
        method: 'POST',
        body: JSON.stringify({ question: q, history: state.history }),
      });
      thinking.remove();
      addBot(formatAnswer(r.answer, r.citations) + sourcesHtml(r.citations));
      state.history = [...state.history, { question: q, answer: r.answer }].slice(-2);
    } catch (err) {
      thinking.remove();
      addMsg('msg-error', `<p>${esc(err.message)}</p>`);
    } finally {
      btn.disabled = false;
    }
  }

  $('#ask-form').addEventListener('submit', (e) => {
    e.preventDefault();
    ask($('#question').value);
  });
  $('#question').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask($('#question').value);
    }
  });

  // ---------- lead form ----------
  $('#lead-form').addEventListener('focusin', () => {
    if (!state.leadTouched) {
      state.leadTouched = true;
      state.leadStarted = Date.now();
    }
  });
  $('#lead-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const err = form.querySelector('.form-error');
    setError(err, '');
    const data = Object.fromEntries(new FormData(form).entries());
    for (const k of ['fullName', 'workEmail', 'jobTitle', 'district', 'problem']) {
      if (!String(data[k] || '').trim()) return setError(err, 'Please fill in every field.');
    }
    data.started_at = state.leadStarted;
    data.demoDistrict = state.district?.name || '';
    const btn = form.querySelector('button[type=submit]');
    btn.disabled = true;
    try {
      await api('/api/leads', { method: 'POST', body: JSON.stringify(data) });
      form.hidden = true;
      $('#lead-thanks').hidden = false;
    } catch (ex) {
      setError(err, ex.message);
    } finally {
      btn.disabled = false;
    }
  });

  // ---------- reopen a shared link ----------
  const initial = new URL(location.href).searchParams.get('d');
  if (initial) {
    api(`/api/districts/${encodeURIComponent(initial)}`)
      .then(({ district }) => openDistrict(district))
      .catch(() => setUrlParam(null));
  }
  api('/api/health')
    .then((h) => {
      if (!h.ai) {
        const p = document.createElement('p');
        p.className = 'form-error';
        p.textContent = 'Setup note: the AI service is not configured on this server yet, so questions cannot be answered.';
        $('#start .wrap').append(p);
      }
    })
    .catch(() => {});
})();
