"""Render the TomoClub SEL hook video.  usage: python3 render.py v|h"""
import sys, json, subprocess, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FMT = sys.argv[1]
W, H = (1080, 1920) if FMT == 'v' else (1920, 1080)
FPS = 30
NAVY = (15, 23, 42); NAVY2 = (30, 41, 59); TEAL = (42, 180, 184); GOLD = (253, 198, 45)
CRIMSON = (179, 65, 88); WHITE = (255, 255, 255); CREAM = (255, 253, 240)
F = lambda w, s: ImageFont.truetype(f'fonts/Outfit-{w}.ttf', s)
LOGO = Image.open('logo.png').convert('RGBA')

# ---------------------------------------------------------------- timeline
HEAD_HOOK = [('What happens when kids get ', WHITE), ('NO rules?', GOLD)]
SEGS = [
    dict(v=[('hook', 0.30, 3.90, 'B')], a=('v2', 165.70, 169.30), head=HEAD_HOOK, tag=[(0, 'Coach VK')]),
    dict(v=[('tl_hex', 0, 2.72, 'game')], a=('v2', 178.45, 181.00), head=HEAD_HOOK, tag=[(0, 'Coach VK')]),
    dict(v=[('maze', 0.35, 5.90, 'game')], a=('v2', 1894.95, 1900.50),
         head=[('They plan. They ', WHITE), ('split roles.', TEAL)], tag=[(0, 'Student')]),
    dict(v=[('tl_ally', 0, 4.48, 'game')], a=('v1', 1880.55, 1884.25),
         head=[('Challenges are ', WHITE), ('hard on purpose.', GOLD)], tag=[(0, 'Coach VK')]),
    dict(v=[('win', 0.25, 1.55, 'B'), ('win', 1.55, 4.60, 'A')], a=('v1', 2105.85, 2110.20),
         head=[('They win by ', WHITE), ('working together.', TEAL)], tag=[(0, 'Coach VK'), (1.3, 'Student')]),
    dict(v=[('twoway', 0.15, 5.60, 'B')], a=('v2', 2320.55, 2326.00),
         head=[('A coach links every game ', WHITE), ('to real life.', GOLD)], tag=[(0, 'Coach VK')]),
    dict(v=[('testi', 0.35, 4.35, 'A'), ('maze', 5.90, 11.40, 'game')], a=('v2', 3696.75, 3706.55),
         head=[('In their ', WHITE), ('own words.', TEAL)], tag=[(0, 'Student')]),
    dict(v=[('rate', 0.30, 3.95, 'B'), ('rate', 3.95, 6.70, 'grid')], a=('v1', 4084.30, 4090.70),
         head=[('And how did they ', WHITE), ('rate it?', GOLD)], tag=[(0, 'Coach VK'), (3.65, 'Students')]),
]
CTA_DUR = 6.0
FIX = {'hot': 'hard', 'i': 'I', "i'm": "I'm", "i'll": "I'll", 'Actually,': 'Actually,'}

t = 0.0
for s in SEGS:
    s['t0'] = t; s['dur'] = s['a'][2] - s['a'][1]; t += s['dur']
CTA_T0 = t; TOTAL = t + CTA_DUR

def seg_at_time(t):
    for s in SEGS:
        if s['t0'] <= t < s['t0'] + s['dur']: return s
# words -> captions
WJ = {v: json.load(open(f'audio/{v}.json')) for v in ('v1', 'v2')}
def seg_words(s):
    v, a0, a1 = s['a']; out = []
    for seg in WJ[v]:
        for ws, we, w in seg['words']:
            if a0 - 0.05 <= ws < a1 - 0.05:
                w = w.strip(); w = FIX.get(w, w)
                if w.lower().strip('.,?!') in ('um', 'uh'): continue
                out.append([s['t0'] + ws - a0, s['t0'] + min(we, a1) - a0, w])
    return out
CHUNKS = []  # (start, end, [words])
for s in SEGS:
    ws = seg_words(s); cur = []
    MAXC = 22 if FMT == 'v' else 30
    brk = [s['t0'] + tt for tt, _ in s['tag'][1:]]
    for w in ws:
        spk = any(cur and cur[-1][0] < b <= w[0] for b in brk)
        if cur and (spk or len(' '.join(x[2] for x in cur + [w])) > MAXC):
            CHUNKS.append(cur); cur = []
        cur.append(w)
        if w[2][-1] in '.?!':
            CHUNKS.append(cur); cur = []
    if cur: CHUNKS.append(cur)
prev_end = ''
for s_ in SEGS: s_['_w0'] = None
for i, c in enumerate(CHUNKS):
    first_in_seg = i == 0 or seg_at_time(c[0][0]) is not seg_at_time(CHUNKS[i - 1][0][0])
    if first_in_seg or CHUNKS[i - 1][-1][2][-1] in '.?!':
        c[0][2] = c[0][2][0].upper() + c[0][2][1:]
# a chunk stays until the next one starts (but not across segments / max 0.6s after)
CAP = []
for i, c in enumerate(CHUNKS):
    st = c[0][0]; en = c[-1][1] + 0.5
    if i + 1 < len(CHUNKS): en = min(en, CHUNKS[i + 1][0][0])
    CAP.append((st, en, c))

# ---------------------------------------------------------------- helpers
def rounded_mask(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255); return m

def text_block(parts, font, maxw, fill_default=WHITE, lh=1.12, align='left', stroke=0):
    """parts: [(text,color)] -> RGBA image with word wrapping preserving colours."""
    words = []
    for txt, col in parts:
        for wd in txt.split(' '):
            if wd: words.append((wd, col))
    lines, cur = [], []
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    sp = d.textlength(' ', font=font)
    for wd in words:
        test = cur + [wd]
        wlen = sum(d.textlength(x[0], font=font) for x in test) + sp * (len(test) - 1)
        if wlen > maxw and cur: lines.append(cur); cur = [wd]
        else: cur = test
    if cur: lines.append(cur)
    asc, desc = font.getmetrics(); lhpx = int((asc + desc) * lh)
    img = Image.new('RGBA', (int(maxw) + 2 * stroke + 4, lhpx * len(lines) + 2 * stroke + 6), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        lw = sum(d.textlength(x[0], font=font) for x in ln) + sp * (len(ln) - 1)
        x = stroke + (0 if align == 'left' else (maxw - lw) / 2)
        for wd, col in ln:
            dr.text((x, stroke + li * lhpx), wd, font=font, fill=col, stroke_width=stroke, stroke_fill=(10, 14, 28))
            x += d.textlength(wd, font=font) + sp
    return img.crop(img.getbbox()) if img.getbbox() else img

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def pill(text, font, bg, fg, padx=22, pady=10, dot=None):
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    tw = d.textlength(text, font=font); asc, desc = font.getmetrics()
    extra = (asc * 0.55 + 12) if dot else 0
    w = int(tw + 2 * padx + extra); h = int(asc + desc + 2 * pady)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=bg)
    x = padx
    if dot:
        r = asc * 0.28; cy = h / 2
        dr.ellipse((x, cy - r, x + 2 * r, cy + r), fill=dot); x += 2 * r + 12
    dr.text((x, pady - 1), text, font=font, fill=fg)
    return im

def logo_img(width, on_dark=True):
    lg = LOGO.resize((width, int(LOGO.height * width / LOGO.width)), Image.LANCZOS)
    if not on_dark: return lg
    padx, pady = int(width * 0.08), int(width * 0.05)
    bg = Image.new('RGBA', (lg.width + 2 * padx, lg.height + 2 * pady), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle((0, 0, bg.width - 1, bg.height - 1), bg.height // 2, fill=WHITE)
    bg.alpha_composite(lg, (padx, pady)); return bg

# ---------------------------------------------------------------- video access
class Clip:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(f'proc/{name}.mp4'); self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.idx = -1; self.frame = None
    def get(self, i):
        i = max(0, min(self.n - 1, i))
        if i < self.idx or i > self.idx + 30:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i); self.idx = i - 1
        while self.idx < i:
            ok, f = self.cap.read()
            if not ok: break
            self.frame = f; self.idx += 1
        return Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
CLIPS = {}
def clip(n):
    if n not in CLIPS: CLIPS[n] = Clip(n)
    return CLIPS[n]

TILES = {'A': (0, 0, 960, 540), 'B': (960, 0, 1920, 540), 'C': (480, 540, 1440, 1080)}
GAME_BOX = (62, 34, 1730, 1034)  # game area inside processed 1920x1080 screen-share

def cover(img, w, h, zoom=1.0, focus=(0.5, 0.5)):
    iw, ih = img.size; s = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * s + 0.5), int(ih * s + 0.5)
    im = img.resize((nw, nh), Image.BILINEAR)
    x = int((nw - w) * focus[0]); y = int((nh - h) * focus[1])
    return im.crop((x, y, x + w, y + h))

def panel_content(src, mode, pw, ph, zoom):
    """Build the video panel (pw x ph) from a processed frame."""
    if mode == 'game':
        g = src.crop(GAME_BOX)
        return cover(g, pw, ph, zoom)
    if mode == 'grid':
        base = Image.new('RGB', (pw, ph), NAVY)
        if FMT == 'v':  # coach on top, two students below
            hb = int(ph * 0.56); base.paste(cover(src.crop(TILES['B']), pw, hb, zoom), (0, 0))
            hw = (pw - 12) // 2; hh = ph - hb - 12
            base.paste(cover(src.crop(TILES['A']), hw, hh, zoom), (0, hb + 12))
            base.paste(cover(src.crop(TILES['C']), hw, hh, zoom), (hw + 12, hb + 12))
        else:
            hw = (pw - 12) // 2; hh = (ph - 12) // 2
            base.paste(cover(src.crop(TILES['B']), hw, hh, zoom), (0, 0))
            base.paste(cover(src.crop(TILES['A']), hw, hh, zoom), (hw + 12, 0))
            base.paste(cover(src.crop(TILES['C']), hw, hh, zoom), ((pw - hw) // 2, hh + 12))
        return base
    # speaker tile big + the other two tiles as picture-in-picture
    main = cover(src.crop(TILES[mode]), pw, ph, zoom)
    others = [k for k in 'BAC' if k != mode]
    pipw = int(pw * (0.30 if FMT == 'v' else 0.24)); piph = int(pipw * 9 / 16)
    m = rounded_mask(pipw + 8, piph + 8, 18)
    for j, k in enumerate(others):
        tile = cover(src.crop(TILES[k]), pipw, piph)
        fr = Image.new('RGB', (pipw + 8, piph + 8), WHITE); fr.paste(tile, (4, 4))
        x = pw - (pipw + 8) - 18 - j * (pipw + 8 + 12); y = ph - piph - 8 - 18
        main.paste(fr, (x, y), m)
    return main

# ---------------------------------------------------------------- layout
if FMT == 'v':
    PX, PY, PW, PH = 40, 470, 1000, 900
    HEAD_BOX = (60, 190, 960)   # x, y, maxw
    HEAD_FONT = F(800, 72)
    CAP_Y = 1440; CAP_FONT = F(900, 84); CAP_W = 980
else:
    PX, PY, PW, PH = 48, 60, 1296, 729
    HEAD_BOX = (1396, 170, 476)
    HEAD_FONT = F(800, 62)
    CAP_Y = 868; CAP_FONT = F(900, 68); CAP_W = 1296
PANEL_MASK = rounded_mask(PW, PH, 36)

def background():
    bg = Image.new('RGB', (W, H), NAVY)
    g = np.zeros((H, W, 3), np.float32) + np.array(NAVY, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    # soft teal glow top-right and crimson glow bottom-left
    for (cx, cy, rad, col, a) in [(W * 0.95, H * 0.02, max(W, H) * 0.55, TEAL, 0.28), (W * 0.0, H * 1.0, max(W, H) * 0.6, CRIMSON, 0.22)]:
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad
        k = np.clip(1 - d, 0, 1) ** 2 * a
        g = g * (1 - k[..., None]) + np.array(col, np.float32) * k[..., None]
    return Image.fromarray(g.clip(0, 255).astype(np.uint8))
BG = background()

HEAD_CACHE = {}
def head_img(parts):
    key = str(parts)
    if key not in HEAD_CACHE: HEAD_CACHE[key] = text_block(parts, HEAD_FONT, HEAD_BOX[2], lh=1.08)
    return HEAD_CACHE[key]

CAP_CACHE = {}
def cap_img(ci, active):
    key = (ci, active)
    if key not in CAP_CACHE:
        words = CAP[ci][2]
        parts = [(w[2], GOLD if j == active else WHITE) for j, w in enumerate(words)]
        CAP_CACHE[key] = text_block(parts, CAP_FONT, CAP_W, align='center', stroke=7, lh=1.05)
    return CAP_CACHE[key]

TAG_FONT = F(600, 34 if FMT == 'v' else 28)
LBL_FONT = F(600, 30 if FMT == 'v' else 24)
LOGO_SMALL = logo_img(250 if FMT == 'v' else 220)
LABEL = pill('LIVE CLASS  ·  REAL STUDENTS', LBL_FONT, (255, 255, 255, 34), WHITE, dot=CRIMSON)

def seg_at(t):
    for s in SEGS:
        if s['t0'] <= t < s['t0'] + s['dur']: return s
    return None

def draw_frame(t):
    if t >= CTA_T0: return cta_frame(t - CTA_T0)
    s = seg_at(t); rt = t - s['t0']
    frame = BG.copy()
    # which sub-clip
    acc = 0; sub = None
    for (cn, a, b, mode) in s['v']:
        span = b - a
        if cn in ('tl_hex', 'tl_ally'): span = s['dur'] - acc if sub is None and (cn, a, b, mode) == s['v'][-1] else span
        if rt < acc + span or (cn, a, b, mode) == s['v'][-1]:
            sub = (cn, a, b, mode, rt - acc, span); break
        acc += span
    cn, a, b, mode, lt, span = sub
    if cn.startswith('tl_'):
        fi = int(lt / s['dur'] * clip(cn).n)           # timelapse: stretch/compress to fit segment
    else:
        fi = int(round((a + lt) * 25))
    src = clip(cn).get(fi)
    # gentle push-in, plus a small punch at each cut
    zoom = 1.0 + 0.05 * (lt / max(span, 0.1)) + 0.04 * (1 - ease(lt / 0.25))
    pan = panel_content(src, mode, PW, PH, zoom)
    # drop shadow
    sh = Image.new('RGBA', (PW + 60, PH + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 36, PW + 30, PH + 36), 40, fill=(0, 0, 0, 150))
    frame.paste(sh.filter(ImageFilter.GaussianBlur(18)), (PX - 30, PY - 30), sh.filter(ImageFilter.GaussianBlur(18)))
    frame.paste(pan, (PX, PY), PANEL_MASK)
    fr = frame.convert('RGBA')
    # speaker tag on panel (top-left inside)
    tag = [x for x in s['tag'] if x[0] <= rt][-1][1]
    tg = pill(tag, TAG_FONT, (15, 23, 42, 215), WHITE, dot=TEAL if tag.startswith('Coach') else GOLD)
    fr.alpha_composite(tg, (PX + 22, PY + 22))
    # headline (slide/fade in when it changes)
    hi = head_img(s['head'])
    prev = SEGS[SEGS.index(s) - 1] if SEGS.index(s) > 0 else None
    fresh = prev is None or prev['head'] != s['head']
    k = ease(rt / 0.35) if fresh else 1.0
    if k < 1:
        hi = hi.copy(); a_ = hi.split()[3].point(lambda p: int(p * k)); hi.putalpha(a_)
    if FMT == 'v':
        hx = (W - hi.width) // 2; hy = HEAD_BOX[1] + (250 - hi.height) // 2 + int((1 - k) * 30)
    else:
        hx = HEAD_BOX[0]; hy = HEAD_BOX[1] + int((1 - k) * 30)
    fr.alpha_composite(hi, (hx, hy))
    # brand + label
    if FMT == 'v':
        fr.alpha_composite(LOGO_SMALL, ((W - LOGO_SMALL.width) // 2, 70))
    else:
        fr.alpha_composite(LOGO_SMALL, (HEAD_BOX[0], PY))
        fr.alpha_composite(LABEL, (HEAD_BOX[0], PY + PH - 100))
        ff = F(600, 30); dr = ImageDraw.Draw(fr)
        dr.text((HEAD_BOX[0], PY + PH - 40), 'Tomo Life Skills  ·  Grades 3–12', font=ff, fill=(203, 213, 225))
    # captions
    for ci, (st, en, words) in enumerate(CAP):
        if st <= t < en:
            act = max([j for j, w in enumerate(words) if w[0] <= t] or [0])
            im = cap_img(ci, act)
            pop = 1 + 0.06 * (1 - ease((t - st) / 0.12))
            if pop > 1.001: im = im.resize((int(im.width * pop), int(im.height * pop)), Image.BILINEAR)
            cy = CAP_Y + (60 if FMT == 'v' else 30)
            fr.alpha_composite(im, ((W - im.width) // 2 if FMT == 'v' else PX + (PW - im.width) // 2, int(cy - im.height / 2)))
            break
    # progress bar
    dr = ImageDraw.Draw(fr)
    by = H - 10 if FMT == 'h' else 1850
    dr.rounded_rectangle((0, by, int(W * t / TOTAL), by + 8), 4, fill=GOLD)
    return fr.convert('RGB')

# ---------------------------------------------------------------- CTA end card
def cta_static():
    bgc = clip('tl_hex').get(clip('tl_hex').n - 8).crop(GAME_BOX)
    bgc = cover(bgc, W, H).filter(ImageFilter.GaussianBlur(28))
    dark = Image.new('RGB', (W, H), NAVY)
    return Image.blend(bgc, dark, 0.78)
CTA_BG = None
def cta_frame(ct):
    global CTA_BG
    if CTA_BG is None: CTA_BG = cta_static()
    fr = CTA_BG.convert('RGBA')
    def put(img, x, y, t_in, dy=40):
        k = ease((ct - t_in) / 0.45)
        if k <= 0: return
        im = img.copy(); im.putalpha(im.split()[3].point(lambda p: int(p * k)))
        fr.alpha_composite(im, (int(x), int(y + (1 - k) * dy)))
    v = FMT == 'v'
    lg = logo_img(560 if v else 460)
    t1 = text_block([('Tomo ', WHITE), ('Life Skills', GOLD)], F(900, 96 if v else 84), 1000 if v else 1400, align='center')
    t2 = text_block([('Live online team games that build confidence, teamwork and grit.', (226, 232, 240))], F(400, 46 if v else 40), 900 if v else 1200, align='center', lh=1.2)
    bl = ['Grades 3–12', 'Groups of up to 12', 'Live coach in every class']
    chips = [pill(b, F(600, 38 if v else 32), (255, 255, 255, 30), WHITE, padx=26, pady=12, dot=c) for b, c in zip(bl, (TEAL, GOLD, CRIMSON))]
    btn = pill('Book a FREE class', F(800, 64 if v else 56), GOLD, NAVY, padx=56, pady=24)
    link = text_block([('tally.so/r/ZjWzPv', WHITE)], F(600, 46 if v else 40), 900, align='center')
    sub = text_block([('Link in bio  ·  tomoclub.org/parents' if v else 'Link in the post  ·  tomoclub.org/parents', (148, 163, 184))], F(400, 36 if v else 32), 1000, align='center')
    if v:
        y = 330
        put(lg, (W - lg.width) / 2, y, 0.0); y += lg.height + 90
        put(t1, (W - t1.width) / 2, y, 0.15); y += t1.height + 36
        put(t2, (W - t2.width) / 2, y, 0.3); y += t2.height + 70
        for i, c in enumerate(chips):
            put(c, (W - c.width) / 2, y, 0.45 + 0.12 * i); y += c.height + 22
        y += 60
        pulse = 1 + 0.035 * math.sin(max(0, ct - 1.2) * 6)
        b2 = btn.resize((int(btn.width * pulse), int(btn.height * pulse)), Image.BILINEAR)
        put(b2, (W - b2.width) / 2, y - (b2.height - btn.height) / 2, 0.9); y += btn.height + 40
        put(link, (W - link.width) / 2, y, 1.05); y += link.height + 22
        put(sub, (W - sub.width) / 2, y, 1.15)
    else:
        y = 160
        put(lg, (W - lg.width) / 2, y, 0.0); y += lg.height + 60
        put(t1, (W - t1.width) / 2, y, 0.15); y += t1.height + 26
        put(t2, (W - t2.width) / 2, y, 0.3); y += t2.height + 50
        tw = sum(c.width for c in chips) + 24 * (len(chips) - 1); x = (W - tw) / 2
        for i, c in enumerate(chips):
            put(c, x, y, 0.45 + 0.12 * i); x += c.width + 24
        y += chips[0].height + 60
        pulse = 1 + 0.035 * math.sin(max(0, ct - 1.2) * 6)
        b2 = btn.resize((int(btn.width * pulse), int(btn.height * pulse)), Image.BILINEAR)
        put(b2, (W - b2.width) / 2, y - (b2.height - btn.height) / 2, 0.9); y += btn.height + 34
        put(link, (W - link.width) / 2, y, 1.05); y += link.height + 16
        put(sub, (W - sub.width) / 2, y, 1.15)
    # fade to black at the very end
    out = fr.convert('RGB')
    if ct > CTA_DUR - 0.4:
        out = Image.blend(out, Image.new('RGB', (W, H), (0, 0, 0)), (ct - (CTA_DUR - 0.4)) / 0.4 * 0.6)
    return out

# ---------------------------------------------------------------- audio
SR = 48000
def load(v, a0, a1):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(a0), '-t', str(a1 - a0), '-i', f'src/{v}.mp4', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(p, np.float32).copy()
def build_audio(path):
    n = int(TOTAL * SR); dia = np.zeros(n, np.float32); speech_mask = np.zeros(n, np.float32)
    for s in SEGS:
        x = load(*s['a'])
        # level-match each bite (RMS of voiced part)
        act = x[np.abs(x) > np.percentile(np.abs(x), 60)]
        x = x * (0.09 / max(1e-4, np.sqrt(np.mean(act ** 2))))
        f = int(0.015 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        i0 = int(s['t0'] * SR); x = x[:n - i0]
        dia[i0:i0 + len(x)] += x; speech_mask[i0:i0 + len(x)] = 1
    m = load_music()
    m = m[:n] if len(m) >= n else np.pad(m, (0, n - len(m)))
    k = int(0.25 * SR); cs = np.concatenate([[0], np.cumsum(speech_mask)]); idx = np.arange(n); lo = np.clip(idx - k // 2, 0, n); hi = np.clip(idx + k // 2, 0, n); sm = (cs[hi] - cs[lo]) / np.maximum(1, hi - lo)
    env = 0.55 - 0.40 * sm           # duck under speech
    env[int(CTA_T0 * SR):] = np.linspace(0.40, 0.62, n - int(CTA_T0 * SR))
    fo = int(1.2 * SR); env[-fo:] *= np.linspace(1, 0, fo)
    mix = dia + m * env * 0.55
    mix = np.tanh(mix * 1.6) / 1.6
    mix.astype(np.float32).tofile(path + '.raw')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', path + '.raw',
                    '-af', 'highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', str(SR), '-ac', '2', path], check=True)
    os.remove(path + '.raw')
def load_music():
    p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', '6.0', '-i', 'music/Upbeat_Forever.mp3', '-t', str(TOTAL + 1), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(p, np.float32).copy(); return x / max(1e-4, np.abs(x).max()) * 0.9

if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    name = 'TomoClub_SEL_Reel_9x16' if FMT == 'v' else 'TomoClub_SEL_LinkedIn_16x9'
    if '--still' in sys.argv:
        for tt in [float(x) for x in sys.argv[sys.argv.index('--still') + 1].split(',')]:
            draw_frame(tt).save(f'chk/still_{FMT}_{tt:.1f}.jpg', quality=90)
        sys.exit()
    wav = f'out/{name}.wav'; build_audio(wav)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
                            '-profile:v', 'high', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'out/{name}.mp4'], stdin=subprocess.PIPE)
    nf = int(TOTAL * FPS)
    for i in range(nf):
        enc.stdin.write(draw_frame(i / FPS).tobytes())
        if i % 150 == 0: print(f'{i}/{nf}', flush=True)
    enc.stdin.close(); enc.wait(); os.remove(wav)
    print('total', TOTAL)
