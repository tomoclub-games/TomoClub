// All Things Classroom — 9:16 promo. Every cue is placed on a 120 BPM beat grid
// (1 beat = 0.5s) so picture and soundtrack stay locked. window.seek(t) renders
// any moment deterministically; window.EVENTS feeds the soundtrack generator.
(async function () {
  await Promise.all([
    '700 100px Unbounded', '800 100px Unbounded', '900 100px Unbounded',
    '500 40px "Space Grotesk"', '600 40px "Space Grotesk"', '700 40px "Space Grotesk"',
  ].map(f => document.fonts.load(f)));

  const W = 1080, H = 1920, BPM = 120, SPB = 60 / BPM;
  const b = n => n * SPB;
  const DURATION = b(52);

  const C = {
    ink: '#0F0C24', violet: '#6D4AFF', violetD: '#4326D1', coral: '#FF5A5F', yellow: '#FFD23F',
    mint: '#2DE1A5', sky: '#3BA3FF', pink: '#FF6FD8', orange: '#FF8A3D', lime: '#B8F34A',
    cream: '#FFF8EC', white: '#FFFFFF', red: '#FF2E4D',
  };

  const EV = [];
  const ev = (type, beat, o = {}) => EV.push(Object.assign({ type, t: +b(beat).toFixed(4) }, o));

  let seed = 1337;
  const R = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const rr = (a, c) => a + R() * (c - a);
  const shuffle = a => { const o = a.slice(); for (let i = o.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [o[i], o[j]] = [o[j], o[i]]; } return o; };

  const stage = document.getElementById('stage');
  const cam = document.getElementById('cam');
  const fx = document.getElementById('fx');

  function $(tag, cls, parent, css) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) Object.assign(e.style, css);
    (parent || stage).appendChild(e);
    return e;
  }
  const place = (e, x, y, extra) => gsap.set(e, Object.assign({ x, y, xPercent: -50, yPercent: -50 }, extra || {}));

  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16);
    let r = n >> 16, g = n >> 8 & 255, bl = n & 255;
    const tgt = amt > 0 ? 255 : 0, a = Math.abs(amt);
    r = Math.round(r + (tgt - r) * a); g = Math.round(g + (tgt - g) * a); bl = Math.round(bl + (tgt - bl) * a);
    return `rgb(${r},${g},${bl})`;
  }
  const rgba = (hex, a) => { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${n >> 8 & 255},${n & 255},${a})`; };
  const svg = (name, size, color, sw = 2.2) =>
    `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" style="display:block;overflow:visible">${ICONS[name]}</svg>`;
  const fgFor = c => [C.violet, C.coral, C.ink, C.violetD].includes(c) ? C.white : C.ink;

  function makeTile(parent, name, bgc, fg, size) {
    const outer = $('div', 'abs', parent);
    const inner = $('div', 'tile', outer, {
      position: 'relative', width: size + 'px', height: size + 'px', borderRadius: size * 0.28 + 'px',
      background: `linear-gradient(155deg, ${shade(bgc, .30)} 0%, ${bgc} 48%, ${shade(bgc, -.14)} 100%)`,
      boxShadow: `0 ${size * .1}px ${size * .24}px rgba(8,5,30,.42), inset 0 ${-size * .045}px 0 rgba(0,0,0,.14), inset 0 ${size * .03}px 0 rgba(255,255,255,.45)`,
    });
    inner.innerHTML = svg(name, size * 0.5, fg || fgFor(bgc), 2.1);
    return { outer, inner, size };
  }
  function fit(e, maxW, size) {
    e.style.fontSize = size + 'px';
    const w = e.offsetWidth;
    if (w > maxW) e.style.fontSize = (size * maxW / w) + 'px';
    return parseFloat(e.style.fontSize);
  }
  function txt(parent, html, o = {}) {
    const e = $('div', 'txt', parent, {
      fontFamily: o.font || 'Unbounded', fontWeight: o.weight || 900, fontSize: (o.size || 100) + 'px',
      color: o.color || C.white, letterSpacing: o.ls || '-0.02em',
    });
    e.innerHTML = html;
    if (o.maxW) fit(e, o.maxW, o.size || 100);
    return e;
  }
  // Per-character line inside an overflow mask, for slot-machine style reveals.
  function splitLine(parent, str, o = {}) {
    const wrap = $('div', 'txt mask', parent, {
      fontFamily: o.font || 'Unbounded', fontWeight: o.weight || 900, fontSize: (o.size || 100) + 'px',
      letterSpacing: o.ls || '-0.02em',
    });
    const chars = [];
    const parts = Array.isArray(str) ? str : [[str, o.color || C.white]];
    for (const [s, col] of parts) for (const c of s) {
      const sp = $('span', 'ch', wrap, { color: col });
      sp.innerHTML = c === ' ' ? '&nbsp;' : c;
      chars.push(sp);
    }
    if (o.maxW) fit(wrap, o.maxW, o.size || 100);
    gsap.set(chars, { yPercent: 125 });
    return { wrap, chars };
  }
  const sizeOf = l => parseFloat((l.wrap || l).style.fontSize);
  const setSize = (ls, s) => ls.forEach(l => (l.wrap || l).style.fontSize = s + 'px');

  const tl = gsap.timeline({ paused: true, defaults: { ease: 'expo.out' } });
  const frameFns = [];
  const onFrame = f => frameFns.push(f);
  const reveal = (l, beat, dur = 0.4, st = 0.018) => tl.to(l.chars, { yPercent: 0, duration: dur, stagger: st }, b(beat));

  function shake(beat, amp = 16) {
    tl.to(cam, {
      keyframes: { x: [amp, -amp * .8, amp * .5, -amp * .25, 0], y: [-amp * .6, amp * .5, -amp * .3, amp * .1, 0], easeEach: 'sine.inOut' },
      duration: 0.3, ease: 'none',
    }, b(beat));
  }

  const blobs = [];
  function scene(color, o = {}) {
    const el = $('div', 'scene', cam);
    $('div', 'layer', el, { background: o.gradient || color });
    (o.blobs || []).forEach(([col, x, y, s, op]) => {
      const d = $('div', 'blob', el, { width: s + 'px', height: s + 'px', color: col, opacity: op });
      blobs.push({ d, x, y, s, ph: rr(0, 6.28), sp: rr(.5, .9) });
    });
    if (o.grid) $('div', 'layer', el, {
      backgroundImage: 'linear-gradient(rgba(255,255,255,.055) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,.055) 2px, transparent 2px)',
      backgroundSize: '90px 90px', backgroundPosition: '44px 49px',
    });
    if (o.dots) $('div', 'layer', el, { backgroundImage: `radial-gradient(${o.dots} 2.6px, transparent 3.4px)`, backgroundSize: '54px 54px', opacity: .16 });
    const content = $('div', 'layer', el);
    return { el, content };
  }
  const show = (s, from, to) => { tl.set(s.el, { autoAlpha: 1 }, from); if (to != null) tl.set(s.el, { autoAlpha: 0 }, to); };
  onFrame(t => blobs.forEach(B => {
    B.d.style.transform = `translate(${B.x - B.s / 2 + Math.sin(t * B.sp + B.ph) * 90}px, ${B.y - B.s / 2 + Math.cos(t * B.sp * .8 + B.ph) * 90}px)`;
  }));

  function makeMark(parent, size) {
    const outer = $('div', 'abs', parent);
    const box = $('div', '', outer, {
      position: 'relative', width: size + 'px', height: size + 'px', borderRadius: size * .3 + 'px', background: C.cream,
      boxShadow: `0 ${size * .12}px ${size * .3}px rgba(10,5,40,.45), inset 0 ${-size * .045}px 0 rgba(0,0,0,.08)`,
    });
    const m = size * .17, g = size * .08, cell = (size - 2 * m - g) / 2;
    const shapes = [
      { bg: C.yellow, r: cell * .28 + 'px' },
      { bg: C.coral, r: '50%' },
      { bg: C.mint, r: `${cell * .5}px 6px ${cell * .5}px 6px` },
      { bg: C.sky, r: cell * .28 + 'px', rot: 45, sc: .78 },
    ];
    const cells = shapes.map((s, i) => {
      const c = $('div', '', box, {
        position: 'absolute', width: cell + 'px', height: cell + 'px', left: (m + (i % 2) * (cell + g)) + 'px',
        top: (m + Math.floor(i / 2) * (cell + g)) + 'px', borderRadius: s.r, background: s.bg,
      });
      gsap.set(c, { rotation: s.rot || 0, scale: s.sc || 1 });
      c.dataset.sc = s.sc || 1;
      return c;
    });
    return { outer, box, cells };
  }
  function wordmark(parent, y, maxW, size) {
    const l1 = splitLine(parent, 'ALL THINGS', { size, maxW });
    const l2 = splitLine(parent, 'CLASSROOM', { size, maxW, color: C.yellow });
    const s = Math.min(sizeOf(l1), sizeOf(l2));
    setSize([l1, l2], s);
    place(l1.wrap, 540, y); place(l2.wrap, 540, y + s * 1.08);
    return { l1, l2, s };
  }

  // ───────────── SCENE 1 · Hook: "Math app. Science app. …  Too many apps?!" (b0–b8)
  const s1 = scene(C.ink, { grid: true, blobs: [[C.violet, 540, 760, 1000, .35], [C.coral, 980, 1700, 700, .18]] });
  show(s1, 0, b(9));
  const heroes = [
    { icon: 'calculator', bg: C.yellow, word: 'Math' },
    { icon: 'flask-conical', bg: C.mint, word: 'Science' },
    { icon: 'code-xml', bg: C.sky, word: 'Coding' },
    { icon: 'languages', bg: C.coral, word: 'Language' },
  ];
  const HERO_Y = 700, LABEL_Y = 1080;
  const scatter = [[235, 430, -12], [850, 360, 11], [205, 1480, 9], [870, 1520, -8]];
  const heroTiles = heroes.map(h => { const t = makeTile(s1.content, h.icon, h.bg, null, 330); place(t.outer, 540, HERO_Y, { scale: 0 }); return t; });
  const labels = heroes.map(h => splitLine(s1.content, [[h.word, h.bg], [' app.', C.white]], { size: 130, maxW: 960 }));
  setSize(labels, Math.min(...labels.map(sizeOf)));
  labels.forEach(l => place(l.wrap, 540, LABEL_Y));
  heroes.forEach((h, i) => {
    const t = heroTiles[i], L = labels[i];
    tl.fromTo(t.outer, { scale: 0, rotation: -35 }, { scale: 1, rotation: rr(-7, 7), duration: 0.42, ease: 'back.out(2.2)' }, b(i));
    tl.to(L.chars, { yPercent: 0, duration: 0.3, stagger: 0.012 }, b(i));
    tl.to(L.chars, { yPercent: -125, duration: 0.28, stagger: 0.008 }, b(i + 1));
    const [sx, sy, sr] = scatter[i];
    tl.to(t.outer, { x: sx, y: sy, scale: 0.5, rotation: sr, duration: 0.5 }, b(i + 1));
    ev('stab', i, { chord: i }); ev('pop', i);
  });

  const extrasDef = [
    [110, 170, 150, 'pencil', C.orange], [400, 205, 130, 'brain', C.pink], [650, 150, 160, 'rocket', C.violet], [965, 200, 140, 'music', C.mint],
    [560, 470, 150, 'palette', C.pink], [95, 700, 130, 'book-open', C.sky], [420, 650, 140, 'globe', C.lime], [700, 640, 150, 'atom', C.yellow], [985, 690, 130, 'gamepad-2', C.coral],
    [-5, 990, 150, 'video', C.orange], [1085, 1000, 150, 'bot', C.sky],
    [470, 1340, 160, 'lightbulb', C.yellow], [730, 1350, 140, 'puzzle', C.violet], [100, 1270, 130, 'telescope', C.mint], [985, 1280, 130, 'dna', C.pink],
    [390, 1630, 150, 'trophy', C.orange], [650, 1690, 170, 'headphones', C.lime], [965, 1790, 140, 'notebook-pen', C.coral], [120, 1790, 140, 'microscope', C.sky], [520, 1900, 130, 'clapperboard', C.pink],
  ];
  const extras = extrasDef.map(([x, y, s, ic, col]) => { const t = makeTile(s1.content, ic, col, null, s); place(t.outer, x, y, { scale: 0, rotation: rr(-18, 18) }); return t; });
  shuffle(extras).forEach((t, k) => {
    tl.fromTo(t.outer, { scale: 0 }, { scale: 1, duration: 0.38, ease: 'back.out(2.6)' }, b(4) + k * 0.022);
    if (k % 3 === 0) ev('blip', 4 + k * 0.044, { k });
  });
  const badgeNums = ['3', '12', '99+', '7', '1', '24', '5', '9+', '2', '42', '8', '16', '4', '31', '6', '11', '99+', '13', '3', '20', '15', '9', '27', '5'];
  const allS1 = [...heroTiles, ...extras];
  const badges = allS1.map((t, i) => {
    const d = Math.max(56, t.size * .3);
    const bd = $('div', '', t.inner, {
      position: 'absolute', right: -d * .3 + 'px', top: -d * .3 + 'px', minWidth: d + 'px', height: d + 'px', padding: '0 ' + d * .18 + 'px',
      boxSizing: 'border-box', borderRadius: d + 'px', background: C.red, color: '#fff', fontFamily: 'Space Grotesk', fontWeight: 700,
      fontSize: d * .5 + 'px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 6px 14px rgba(0,0,0,.35)', border: '4px solid ' + C.ink,
    });
    bd.textContent = badgeNums[i % badgeNums.length];
    gsap.set(bd, { scale: 0 });
    return bd;
  });
  tl.to(shuffle(badges), { scale: 1, duration: 0.3, ease: 'back.out(3)', stagger: 0.03 }, b(4.5));
  ev('ding', 4.5); ev('ding', 5.25, { hi: 1 });

  const hush = $('div', 'layer', s1.content, { background: `radial-gradient(ellipse 52% 16% at 50% 52%, ${rgba(C.ink, .92)} 0%, ${rgba(C.ink, .7)} 55%, transparent 100%)`, opacity: 0 });
  s1.content.insertBefore(hush, labels[0].wrap);
  tl.to(hush, { opacity: 1, duration: 0.3 }, b(4));
  const tooMany = splitLine(s1.content, 'Too many', { size: 130, maxW: 900 });
  place(tooMany.wrap, 540, 895);
  const appsQ = txt(s1.content, 'apps?!', { size: 240, color: C.yellow, maxW: 920 });
  place(appsQ, 540, 1085, { autoAlpha: 0 });
  reveal(tooMany, 4, 0.35, 0.02);
  tl.fromTo(appsQ, { scale: 2.6, rotation: -10, autoAlpha: 0 }, { scale: 1, rotation: -4, autoAlpha: 1, duration: 0.3 }, b(5));
  shake(5, 24); ev('slam', 5);

  allS1.forEach(t => { t.ph = rr(0, 6.28); t.fr = rr(10, 16); });
  onFrame(t => {
    const a = t < b(4) || t > b(6.3) ? 0 : Math.min(1, (t - b(4)) / b(2));
    allS1.forEach(tt => {
      tt.inner.style.transform = a
        ? `translate(${Math.sin(t * tt.fr + tt.ph) * 8 * a}px, ${Math.cos(t * tt.fr * 1.3 + tt.ph) * 8 * a}px) rotate(${Math.sin(t * tt.fr * .8 + tt.ph) * 7 * a}deg)`
        : '';
    });
  });

  // Implode everything into the centre, then ask the question.
  shuffle(allS1).forEach((t, k) => tl.to(t.outer, { x: 540, y: 960, scale: 0, rotation: '+=' + rr(140, 260), duration: 0.5, ease: 'power3.in' }, b(6) + k * 0.01));
  tl.to([tooMany.wrap, appsQ], { scale: 0.3, autoAlpha: 0, duration: 0.25, ease: 'power2.in' }, b(6));
  ev('suck', 6);
  const q1 = splitLine(s1.content, 'What if', { size: 150, maxW: 940 });
  const q2 = splitLine(s1.content, 'it was all', { size: 150, maxW: 940 });
  const q3 = splitLine(s1.content, [['in ', C.white], ['ONE', C.yellow], [' place?', C.white]], { size: 150, maxW: 960 });
  place(q1.wrap, 540, 790); place(q2.wrap, 540, 950); place(q3.wrap, 540, 1100);
  reveal(q1, 6.05, 0.3, 0.014); reveal(q2, 6.45, 0.3, 0.014); reveal(q3, 6.85, 0.3, 0.012);
  ev('riser', 6, { end: b(8) });

  // ───────────── SCENE 2 · Brand reveal (b8–b16)
  const ring = $('div', 'layer', cam, { background: C.yellow, visibility: 'hidden' });
  const s2 = scene(C.violet, { grid: true, blobs: [[C.pink, 160, 280, 900, .55], [C.sky, 940, 1680, 1000, .5], [C.violetD, 540, 1000, 900, .6]] });
  tl.set(ring, { visibility: 'visible' }, b(8) - 0.1);
  tl.fromTo(ring, { clipPath: 'circle(0px at 540px 960px)' }, { clipPath: 'circle(1150px at 540px 960px)', duration: 0.5, ease: 'expo.out', immediateRender: false }, b(8) - 0.1);
  tl.set(ring, { visibility: 'hidden' }, b(9));
  show(s2, b(8), b(16));
  tl.fromTo(s2.el, { clipPath: 'circle(0px at 540px 960px)' }, { clipPath: 'circle(1150px at 540px 960px)', duration: 0.55, ease: 'expo.out', immediateRender: false }, b(8));
  shake(8, 26); ev('impact', 8);

  const mk2 = makeMark(s2.content, 300);
  place(mk2.outer, 540, 600, { scale: 0 });
  tl.fromTo(mk2.outer, { scale: 0, rotation: -150 }, { scale: 1, rotation: 0, duration: 1.1, ease: 'elastic.out(1, 0.55)' }, b(8.05));
  tl.from(mk2.cells, { scale: 0, duration: 0.45, stagger: 0.07, ease: 'back.out(3)', immediateRender: false }, b(8.35));
  const wm2 = wordmark(s2.content, 900, 930, 150);
  reveal(wm2.l1, 8.6, 0.5, 0.03); reveal(wm2.l2, 9.1, 0.5, 0.03);
  ev('whoosh', 8.6, { soft: 1 });
  [10, 12, 14].forEach(k => { tl.to(mk2.box, { rotation: '+=90', duration: 0.5, ease: 'back.out(2.2)' }, b(k)); ev('tick', k); });
  const tg2 = splitLine(s2.content, [['All your ', C.white], ['learning tools.', C.white]], { font: 'Space Grotesk', weight: 700, size: 66, ls: '-0.01em', maxW: 940 });
  place(tg2.wrap, 540, 1240);
  reveal(tg2, 11, 0.45, 0.012);
  const pill2 = $('div', 'abs', s2.content, {
    background: C.yellow, color: C.ink, borderRadius: '999px', padding: '26px 56px 30px', fontFamily: 'Unbounded', fontWeight: 900,
    fontSize: '64px', whiteSpace: 'nowrap', letterSpacing: '-0.02em', boxShadow: '0 20px 44px rgba(10,5,40,.4)',
  });
  pill2.textContent = 'One place.';
  place(pill2, 540, 1390, { scale: 0 });
  tl.fromTo(pill2, { scale: 0, rotation: -12 }, { scale: 1, rotation: -3, duration: 0.7, ease: 'back.out(2.4)' }, b(12));
  shake(12, 12); ev('pop', 12, { big: 1 });
  tl.to(s2.content, { scale: 1.35, autoAlpha: 0, duration: 0.25, ease: 'power2.in' }, b(15.75));
  ev('whoosh', 16);

  // ───────────── SCENE 3 · Rapid-fire subject cuts (b16–b24)
  const cutsDef = [
    [16, 'MATH', 'pi', C.yellow, C.ink],
    [17, 'SCIENCE', 'atom', C.mint, C.ink],
    [18, 'CODING', 'code-xml', C.sky, C.ink],
    [19, 'LANGUAGES', 'languages', C.coral, C.white],
    [20, 'READING', 'book-open', C.violet, C.white],
    [20.5, 'ART', 'palette', C.pink, C.ink],
    [21, 'MUSIC', 'music', C.orange, C.ink],
    [21.5, 'HISTORY', 'landmark', C.lime, C.ink],
    [22, 'EXAM PREP', 'graduation-cap', C.sky, C.ink],
    [22.5, 'ROBOTICS', 'bot', C.cream, C.violet],
    [23, '& WAY MORE', 'sparkles', C.ink, C.yellow],
  ];
  cutsDef.forEach(([beat, word, icon, bgc, fg], i) => {
    const next = i + 1 < cutsDef.length ? cutsDef[i + 1][0] : 24;
    const last = i === cutsDef.length - 1;
    const sc = scene(bgc, last ? { grid: true, blobs: [[C.violet, 540, 960, 1100, .5]] } : { dots: fg });
    show(sc, b(beat), b(next));
    const r0 = rr(-25, 25);
    const big = $('div', 'abs', sc.content, { opacity: last ? .08 : .1 });
    big.innerHTML = svg(icon, 1350, fg, 1.1);
    place(big, 540 + rr(-80, 80), 960 + rr(-80, 80));
    tl.fromTo(big, { rotation: r0, scale: 1.12 }, { rotation: r0 + 20, scale: 1, duration: b(next - beat), ease: 'none' }, b(beat));
    if (!last) {
      const cap = txt(sc.content, 'TOOLS FOR', { font: 'Space Grotesk', weight: 700, size: 54, color: fg, ls: '0.2em' });
      cap.style.opacity = .8;
      place(cap, 540, 690);
    }
    const ic = $('div', 'abs', sc.content);
    ic.innerHTML = svg(icon, 240, fg, 2.2);
    place(ic, 540, 890);
    const w = txt(sc.content, word, { size: 230, maxW: 960, color: fg });
    place(w, 540, 1150);
    tl.fromTo(w, { scale: 1.5 }, { scale: 1, duration: 0.24 }, b(beat));
    tl.fromTo(ic, { scale: 0.3, rotation: -45 }, { scale: 1, rotation: 0, duration: 0.32, ease: 'back.out(2.6)' }, b(beat));
    ev('cut', beat, { i, last: last ? 1 : 0 });
  });

  // ───────────── SCENE 4 · The hub: everything snaps into one grid (b24–b28)
  const s4 = scene(C.ink, { grid: true, blobs: [[C.violet, 540, 1000, 1200, .55], [C.coral, 80, 180, 600, .22], [C.sky, 1000, 1820, 800, .3]] });
  show(s4, b(24), b(28));
  const hub1 = splitLine(s4.content, 'One hub.', { size: 160, maxW: 940 });
  place(hub1.wrap, 540, 330);
  const hub2 = splitLine(s4.content, [['Endless ways to ', C.white], ['learn.', C.mint]], { font: 'Space Grotesk', weight: 700, size: 66, maxW: 940 });
  place(hub2.wrap, 540, 470);
  reveal(hub1, 24.2, 0.45, 0.03); reveal(hub2, 25, 0.45, 0.012);
  const icons16 = ['calculator', 'flask-conical', 'code-xml', 'languages', 'book-open', 'palette', 'music', 'landmark', 'graduation-cap', 'bot', 'globe', 'atom', 'rocket', 'brain', 'gamepad-2', 'video'];
  const cols16 = [C.yellow, C.mint, C.sky, C.coral, C.violet, C.pink, C.orange, C.lime, C.sky, C.cream, C.mint, C.yellow, C.coral, C.pink, C.orange, C.violet];
  const TS = 196, GAP = 30, x0 = 540 - (4 * TS + 3 * GAP) / 2 + TS / 2, y0 = 1010 - (4 * TS + 3 * GAP) / 2 + TS / 2;
  const hubTiles = icons16.map((ic, i) => {
    const t = makeTile(s4.content, ic, cols16[i], null, TS);
    const fx0 = x0 + (i % 4) * (TS + GAP), fy0 = y0 + Math.floor(i / 4) * (TS + GAP);
    const ang = rr(0, 6.28), dist = rr(1300, 1700);
    place(t.outer, 540 + Math.cos(ang) * dist, 960 + Math.sin(ang) * dist, { rotation: rr(-200, 200), scale: .5 });
    t.fx = fx0; t.fy = fy0;
    return t;
  });
  shuffle(hubTiles).forEach((t, k) => tl.to(t.outer, { x: t.fx, y: t.fy, rotation: 0, scale: 1, duration: 0.7, ease: 'expo.out' }, b(24) + k * 0.025));
  ev('whoosh', 24); ev('sparkle', 24.6);
  [26, 27].forEach(k => tl.to(hubTiles.map(t => t.inner), {
    keyframes: { scale: [1.14, 1], easeEach: 'power2.out' }, duration: 0.3,
    stagger: { grid: [4, 4], from: 'center', amount: 0.22 },
  }, b(k)));
  tl.to(hubTiles.map(t => t.outer), { scale: 0, rotation: 90, duration: 0.3, ease: 'power3.in', stagger: { grid: [4, 4], from: 'edges', amount: 0.15 } }, b(27.45));
  tl.to([hub1.wrap, hub2.wrap], { yPercent: -150, autoAlpha: 0, duration: 0.3, ease: 'power3.in' }, b(27.5));

  // ───────────── SCENE 5 · Search: find what works for YOU (b28–b36)
  const s5 = scene(C.ink, { grid: true, blobs: [[C.violet, 300, 620, 1000, .5], [C.sky, 900, 1500, 1000, .32]] });
  show(s5, b(28), b(36));
  const fw1 = splitLine(s5.content, 'Find what works', { size: 110, maxW: 940 });
  const fw2 = splitLine(s5.content, [['for ', C.white], ['YOU.', C.yellow]], { size: 170, maxW: 940 });
  place(fw1.wrap, 540, 420); place(fw2.wrap, 540, 570);
  reveal(fw1, 28, 0.4, 0.015); reveal(fw2, 28.5, 0.45, 0.04);
  const bar = $('div', 'abs', s5.content, {
    width: '940px', height: '150px', borderRadius: '75px', background: C.white, display: 'flex', alignItems: 'center',
    boxShadow: '0 30px 70px rgba(0,0,0,.45), 0 0 0 10px rgba(109,74,255,.35)', boxSizing: 'border-box', padding: '0 0 0 44px',
  });
  place(bar, 540, 810, { autoAlpha: 0 });
  const sIcon = $('div', '', bar); sIcon.innerHTML = svg('search', 60, C.violet, 2.6);
  const qText = $('div', '', bar, { marginLeft: '26px', fontFamily: 'Space Grotesk', fontWeight: 600, fontSize: '54px', color: C.ink, whiteSpace: 'nowrap', letterSpacing: '-0.01em' });
  const caret = $('div', '', bar, { width: '5px', height: '62px', background: C.violet, marginLeft: '4px', borderRadius: '3px' });
  const go = $('div', 'tile', bar, { position: 'absolute', right: '20px', top: '20px', width: '110px', height: '110px', borderRadius: '55px', background: C.violet });
  go.innerHTML = svg('arrow-right', 54, C.white, 2.8);
  tl.fromTo(bar, { scaleX: 0.16, scaleY: 0.6, autoAlpha: 0 }, { scaleX: 1, scaleY: 1, autoAlpha: 1, duration: 0.6 }, b(28.15));
  ev('whoosh', 28.2, { soft: 1 });
  const QUERY = 'help with fractions', T0 = b(29), T1 = b(31);
  for (let i = 0; i < QUERY.length; i++) ev('key', (T0 + (T1 - T0) * i / QUERY.length) / SPB, { i });
  onFrame(t => {
    const n = Math.max(0, Math.min(QUERY.length, Math.floor((t - T0) / ((T1 - T0) / QUERY.length)) + 1));
    if (t < T0) { qText.textContent = 'Search anything…'; qText.style.color = '#A9A4C4'; }
    else { qText.textContent = QUERY.slice(0, n); qText.style.color = C.ink; }
    const typing = t >= T0 && t < T1 + 0.1;
    caret.style.opacity = typing || Math.floor(t * 3) % 2 === 0 ? 1 : 0;
    if (t < T0) caret.style.order = -1; else caret.style.order = 0;
  });
  tl.to(go, { keyframes: { scale: [0.82, 1.08, 1], easeEach: 'power2.out' }, duration: 0.35 }, b(31.2));
  tl.to(bar, { keyframes: { scale: [0.97, 1], easeEach: 'power2.out' }, duration: 0.3 }, b(31.2));
  ev('enter', 31.2);

  const results = [
    ['gamepad-2', C.yellow, 'Fraction Games', ['Math', 'Play & learn']],
    ['clapperboard', C.coral, 'Video Lessons', ['Math', 'Watch & learn']],
    ['bot', C.mint, 'AI Study Buddy', ['Math', 'Practice']],
  ];
  const CARD_Y = 1050;
  const cards = results.map(([ic, col, title, tags], i) => {
    const card = $('div', 'abs', s5.content, {
      width: '940px', height: '196px', borderRadius: '50px', background: 'rgba(255,255,255,.08)', border: '3px solid rgba(255,255,255,.14)',
      boxSizing: 'border-box', display: 'flex', alignItems: 'center', padding: '0 36px 0 30px', gap: '30px',
    });
    const t = makeTile(card, ic, col, null, 132);
    t.outer.style.position = 'relative';
    const colm = $('div', '', card, { display: 'flex', flexDirection: 'column', gap: '16px' });
    const tt = $('div', '', colm, { fontFamily: 'Unbounded', fontWeight: 800, fontSize: '44px', color: C.white, whiteSpace: 'nowrap', letterSpacing: '-0.02em' });
    tt.textContent = title;
    const tagRow = $('div', '', colm, { display: 'flex', gap: '12px' });
    tags.forEach((tg, j) => {
      const chip = $('div', '', tagRow, {
        fontFamily: 'Space Grotesk', fontWeight: 700, fontSize: '28px', padding: '8px 22px', borderRadius: '999px',
        background: j === 0 ? rgba(col, .2) : 'rgba(255,255,255,.1)', color: j === 0 ? col : 'rgba(255,255,255,.85)',
      });
      chip.textContent = tg;
    });
    const arr = $('div', '', card, { marginLeft: 'auto', opacity: .6 }); arr.innerHTML = svg('arrow-right', 52, C.white, 2.6);
    const cy = CARD_Y + i * 222;
    place(card, 540, cy, { autoAlpha: 0 });
    tl.fromTo(card, { y: cy + 160, autoAlpha: 0 }, { y: cy, autoAlpha: 1, duration: 0.55 }, b(31.5) + i * 0.12);
    ev('card', 31.5 + i * 0.24, { i });
    return card;
  });
  const pointer = $('div', 'abs', s5.content, {
    width: '86px', height: '86px', borderRadius: '50%', background: 'rgba(255,255,255,.92)', border: '6px solid rgba(255,255,255,.35)',
    backgroundClip: 'padding-box', boxShadow: '0 14px 30px rgba(0,0,0,.4)',
  });
  place(pointer, 900, 1800, { autoAlpha: 0 });
  const ripple = $('div', 'abs', s5.content, { width: '120px', height: '120px', borderRadius: '50%', border: '6px solid ' + C.yellow, boxSizing: 'border-box' });
  place(ripple, 760, CARD_Y, { autoAlpha: 0 });
  tl.to(pointer, { autoAlpha: 1, duration: 0.15 }, b(32.9));
  tl.to(pointer, { x: 760, y: CARD_Y, duration: 0.55, ease: 'power3.inOut' }, b(32.9));
  tl.to(pointer, { keyframes: { scale: [0.75, 1], easeEach: 'power2.out' }, duration: 0.3 }, b(34));
  tl.fromTo(ripple, { scale: 0.3, autoAlpha: 1 }, { scale: 3, autoAlpha: 0, duration: 0.6, ease: 'power2.out', immediateRender: false }, b(34));
  tl.to(cards[0], { scale: 1.05, borderColor: C.yellow, backgroundColor: 'rgba(255,210,63,.14)', duration: 0.4, ease: 'back.out(2.5)' }, b(34));
  tl.to(cards.slice(1), { autoAlpha: 0.35, duration: 0.3, ease: 'power2.out' }, b(34));
  const sparks = [0, 1, 2, 3, 4, 5].map(k => { const s = $('div', 'abs', s5.content); s.innerHTML = svg('sparkles', 64, k % 2 ? C.yellow : C.white, 2.2); place(s, 540, CARD_Y, { scale: 0 }); return s; });
  sparks.forEach((s, k) => {
    const a = -Math.PI / 2 + (k - 2.5) * 0.55, d = 300 + (k % 2) * 90;
    tl.fromTo(s, { x: 540, y: CARD_Y, scale: 0, rotation: 0 }, { x: 540 + Math.cos(a) * d * 1.4, y: CARD_Y + Math.sin(a) * d * .9, scale: 1, rotation: 90, duration: 0.6, ease: 'expo.out' }, b(34.05));
    tl.to(s, { scale: 0, duration: 0.3, ease: 'power2.in' }, b(35.2));
  });
  ev('tap', 34); ev('sparkle', 34.05);
  ev('riser', 34, { end: b(36), soft: 1 });

  // ───────────── SCENE 6 · DISCOVER. EXPLORE. LEVEL UP. (b36–b40)
  const s6 = scene(C.yellow, { dots: C.ink });
  show(s6, b(36), b(40.1));
  const bw = [
    splitLine(s6.content, 'DISCOVER.', { size: 170, maxW: 960, color: C.ink }),
    splitLine(s6.content, 'EXPLORE.', { size: 170, maxW: 960, color: C.ink }),
    splitLine(s6.content, [['LEVEL ', C.violet], ['UP.', C.coral]], { size: 170, maxW: 960 }),
  ];
  const bs = Math.min(...bw.map(sizeOf));
  setSize(bw, bs);
  bw.forEach((l, i) => {
    gsap.set(l.chars, { yPercent: 0 });
    place(l.wrap, 540, 760 + i * bs * 1.25, { autoAlpha: 0 });
    tl.fromTo(l.wrap, { scale: 2.4, rotation: i === 2 ? -10 : rr(-6, 6), autoAlpha: 0 }, { scale: 1, rotation: i === 2 ? -3 : 0, autoAlpha: 1, duration: 0.28 }, b(36 + i));
    shake(36 + i, 20 + i * 6); ev('slam', 36 + i, { i });
  });
  const wrt = splitLine(s6.content, 'with the right tools.', { font: 'Space Grotesk', weight: 700, size: 64, maxW: 900, color: C.ink });
  place(wrt.wrap, 540, 760 + 2 * bs * 1.25 + 175);
  reveal(wrt, 38.6, 0.4, 0.012);
  const s6sparks = [[150, 520, C.violet, 90], [930, 560, C.coral, 110], [130, 1420, C.coral, 80], [950, 1380, C.violet, 100]].map(([x, y, c, s]) => {
    const e = $('div', 'abs', s6.content); e.innerHTML = svg('sparkles', s, c, 2.4); place(e, x, y, { scale: 0 }); return e;
  });
  tl.to(s6sparks, { scale: 1, rotation: 20, duration: 0.5, ease: 'back.out(3)', stagger: 0.05 }, b(38));

  // Colour-stripe wipe into the end card (b39.5–b40.4)
  const stripes = [C.violet, C.coral, C.sky, C.mint, C.pink].map((c, i) =>
    $('div', 'abs', fx, { width: '218px', height: '1920px', left: (i * 216) + 'px', background: c }));
  tl.fromTo(stripes, { yPercent: 102 }, { yPercent: 0, duration: 0.32, stagger: 0.035, ease: 'power3.in' }, b(39.45));
  tl.to(stripes, { yPercent: -102, duration: 0.5, stagger: 0.035, ease: 'power3.out' }, b(40));
  ev('whoosh', 40);

  // ───────────── SCENE 7 · End card + CTA (b40–b52)
  const s7 = scene(C.violet, {
    gradient: `linear-gradient(170deg, ${C.violet} 0%, #5635E8 55%, #3A1EBE 100%)`, grid: true,
    blobs: [[C.pink, 120, 360, 820, .45], [C.sky, 960, 1520, 950, .45], [C.yellow, 920, 260, 520, .16]],
  });
  show(s7, b(40), null);
  ev('impact', 40, { final: 1 });
  const mk7 = makeMark(s7.content, 230);
  place(mk7.outer, 540, 560, { scale: 0 });
  tl.fromTo(mk7.outer, { scale: 0, rotation: -150 }, { scale: 1, rotation: 0, duration: 1.1, ease: 'elastic.out(1, 0.55)' }, b(40.15));
  const wm7 = wordmark(s7.content, 800, 900, 150);
  reveal(wm7.l1, 40.45, 0.5, 0.028); reveal(wm7.l2, 40.85, 0.5, 0.028);
  const tg7 = splitLine(s7.content, [['Your ', C.white], ['learning toolbox.', C.white]], { font: 'Space Grotesk', weight: 700, size: 60, maxW: 900 });
  place(tg7.wrap, 540, 800 + wm7.s * 1.08 + 170);
  reveal(tg7, 41.6, 0.45, 0.012);
  const btn = $('div', 'abs', s7.content, {
    background: C.yellow, borderRadius: '999px', display: 'flex', alignItems: 'center', gap: '26px', padding: '0 22px 0 58px',
    height: '156px', boxShadow: '0 26px 60px rgba(10,5,40,.5), inset 0 -8px 0 rgba(0,0,0,.12)', overflow: 'hidden', boxSizing: 'border-box',
  });
  const url = $('div', '', btn, { fontFamily: 'Unbounded', fontWeight: 800, fontSize: '48px', color: C.ink, whiteSpace: 'nowrap', letterSpacing: '-0.02em' });
  url.textContent = 'allthingsclassroom.com';
  const arrow = $('div', 'tile', btn, { width: '112px', height: '112px', borderRadius: '56px', background: C.ink, flex: 'none' });
  arrow.innerHTML = svg('arrow-right', 56, C.yellow, 2.8);
  fit(url, 700, 48);
  const shine = $('div', 'abs', btn, { width: '140px', height: '300px', top: '-70px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,.75), transparent)' });
  gsap.set(shine, { x: -300, rotation: 20 });
  const BTN_Y = 800 + wm7.s * 1.08 + 350;
  place(btn, 540, BTN_Y, { scale: 0 });
  tl.fromTo(btn, { scale: 0, rotation: -8 }, { scale: 1, rotation: 0, duration: 0.8, ease: 'elastic.out(1, 0.6)' }, b(42));
  ev('pop', 42, { big: 1 });
  [44, 46, 48, 50].forEach(k => {
    tl.to(btn, { keyframes: { scale: [1.07, 1], easeEach: 'power2.out' }, duration: 0.45 }, b(k));
    tl.to(arrow, { keyframes: { x: [12, 0], easeEach: 'power2.out' }, duration: 0.45 }, b(k));
  });
  [44, 48].forEach(k => { tl.fromTo(shine, { x: -300 }, { x: 1100, duration: 0.8, ease: 'power2.inOut', immediateRender: false }, b(k)); ev('shine', k); });
  const hand = $('div', 'abs', s7.content); hand.innerHTML = svg('pointer', 110, C.white, 1.8);
  place(hand, 1000, BTN_Y + 360, { autoAlpha: 0 });
  tl.to(hand, { autoAlpha: 1, x: 948, y: BTN_Y + 84, duration: 0.6, ease: 'power3.out' }, b(43.2));
  tl.to(hand, { keyframes: { scale: [0.82, 1], easeEach: 'power2.out' }, duration: 0.3 }, b(44));
  const twinkles = [[250, 470, 70, C.yellow], [835, 640, 56, C.white], [880, 430, 44, C.mint]].map(([x, y, s, c], i) => {
    const e = $('div', 'abs', s7.content); e.innerHTML = svg('sparkles', s, c, 2.2); place(e, x, y, { scale: 0 }); e.ph = i * 1.7; return e;
  });
  onFrame(t => twinkles.forEach(e => {
    const a = t < b(41) ? 0 : Math.min(1, (t - b(41)) / 0.4);
    gsap.set(e, { scale: a * (0.75 + 0.35 * Math.sin(t * 4 + e.ph)), rotation: Math.sin(t * 1.5 + e.ph) * 15 });
  }));

  // ───────────── Confetti (deterministic ballistic + drag)
  const cv = document.getElementById('confetti'), ctx = cv.getContext('2d');
  const confCols = [C.yellow, C.coral, C.mint, C.sky, C.pink, C.violet, C.white, C.lime];
  const parts = [];
  function cannon(beat, x, y, angDeg, n) {
    for (let k = 0; k < n; k++) {
      const a = (angDeg + rr(-17, 17)) * Math.PI / 180, v = rr(2200, 4300);
      parts.push({
        t0: b(beat) + rr(0, 0.06), x, y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, w: rr(16, 30), h: rr(9, 16),
        rot: rr(0, 6.28), vr: rr(-10, 10), flip: rr(6, 14), col: confCols[Math.floor(R() * confCols.length)], round: R() < .28,
      });
    }
  }
  cannon(38, -20, 1960, -62, 80); cannon(38, 1100, 1960, -118, 80);
  cannon(40.2, -20, 1960, -64, 90); cannon(40.2, 1100, 1960, -116, 90);
  ev('confetti', 38); ev('confetti', 40.2);
  const K = 2.6, G = 1500;
  onFrame(t => {
    ctx.clearRect(0, 0, W, H);
    for (const p of parts) {
      const dt = t - p.t0;
      if (dt < 0 || dt > 5) continue;
      const e = Math.exp(-K * dt);
      const x = p.x + p.vx / K * (1 - e) + Math.sin(dt * 3 + p.rot) * 30 * (1 - e);
      const y = p.y + (p.vy - G / K) / K * (1 - e) + G / K * dt;
      if (y > H + 60) continue;
      ctx.save();
      ctx.globalAlpha = dt > 3.8 ? Math.max(0, 1 - (dt - 3.8) / 1.2) : 1;
      ctx.translate(x, y); ctx.rotate(p.rot + p.vr * dt); ctx.scale(1, Math.cos(dt * p.flip));
      ctx.fillStyle = p.col;
      if (p.round) { ctx.beginPath(); ctx.arc(0, 0, p.h * .7, 0, 6.283); ctx.fill(); }
      else ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
      ctx.restore();
    }
  });

  // ───────────── Film grain
  const grain = document.getElementById('grain');
  const gcv = document.createElement('canvas'); gcv.width = gcv.height = 256;
  const gctx = gcv.getContext('2d'), gid = gctx.createImageData(256, 256);
  for (let i = 0; i < 256 * 256; i++) { const v = R() * 255; gid.data[i * 4] = gid.data[i * 4 + 1] = gid.data[i * 4 + 2] = v; gid.data[i * 4 + 3] = 255; }
  gctx.putImageData(gid, 0, 0);
  grain.style.backgroundImage = `url(${gcv.toDataURL()})`;
  onFrame(t => { const f = Math.floor(t * 30); grain.style.backgroundPosition = `${(f * 97) % 256}px ${(f * 57) % 256}px`; });

  EV.sort((a, c) => a.t - c.t);
  window.DURATION = DURATION; window.EVENTS = EV; window.BPM = BPM;
  window.seek = t => { tl.seek(t, false); frameFns.forEach(f => f(t)); };
  window.seek(0);
  window.READY = true;

  if (/play/.test(location.search)) {
    const fitStage = () => { const s = Math.min(innerWidth / W, innerHeight / H); stage.style.transform = `scale(${s})`; stage.style.transformOrigin = '0 0'; };
    fitStage(); addEventListener('resize', fitStage);
    const start = performance.now();
    const loop = () => { window.seek(((performance.now() - start) / 1000) % DURATION); requestAnimationFrame(loop); };
    loop();
  }
})();
