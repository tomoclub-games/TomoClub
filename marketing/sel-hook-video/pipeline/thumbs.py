"""Thumbnails / covers for the SEL hook video."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.argv = ['x', 'v']
NAVY = (15, 23, 42); TEAL = (42, 180, 184); GOLD = (253, 198, 45); CRIMSON = (179, 65, 88); WHITE = (255, 255, 255)
F = lambda w, s: ImageFont.truetype(f'fonts/Outfit-{w}.ttf', s)
LOGO = Image.open('logo.png').convert('RGBA')

def glow_bg(W, H):
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.zeros((H, W, 3), np.float32) + np.array(NAVY, np.float32)
    for (cx, cy, rad, col, a) in [(W * 0.95, H * 0.02, max(W, H) * 0.6, TEAL, 0.35), (0, H, max(W, H) * 0.65, CRIMSON, 0.28)]:
        k = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad, 0, 1) ** 2 * a
        g = g * (1 - k[..., None]) + np.array(col, np.float32) * k[..., None]
    return Image.fromarray(g.clip(0, 255).astype(np.uint8)).convert('RGBA')

def logo_pill(width):
    lg = LOGO.resize((width, int(LOGO.height * width / LOGO.width)), Image.LANCZOS)
    px, py = int(width * .08), int(width * .05)
    bg = Image.new('RGBA', (lg.width + 2 * px, lg.height + 2 * py), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle((0, 0, bg.width - 1, bg.height - 1), bg.height // 2, fill=WHITE)
    bg.alpha_composite(lg, (px, py)); return bg

def card(img, w, h, r=36, border=12, angle=0):
    im = img.copy(); s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = (im.width - w) // 2; y = (im.height - h) // 2; im = im.crop((x, y, x + w, y + h))
    out = Image.new('RGBA', (w + 2 * border, h + 2 * border), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle((0, 0, out.width - 1, out.height - 1), r + border, fill=WHITE)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    out.paste(im, (border, border), m)
    if angle: out = out.rotate(angle, resample=Image.BICUBIC, expand=True)
    return out

def shadow(img, blur=30, off=(0, 24), alpha=170):
    a = img.split()[3].point(lambda p: int(p * alpha / 255))
    sh = Image.new('RGBA', (img.width + 4 * blur, img.height + 4 * blur), (0, 0, 0, 0))
    blk = Image.new('RGBA', img.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (2 * blur + off[0], 2 * blur + off[1]))
    return sh.filter(ImageFilter.GaussianBlur(blur))

def paste_with_shadow(base, img, x, y, blur=30):
    sh = shadow(img, blur); base.alpha_composite(sh, (x - 2 * blur, y - 2 * blur)); base.alpha_composite(img, (x, y))

def sticker(text1, text2, d):
    im = Image.new('RGBA', (d, d), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, d - 1, d - 1), fill=GOLD)
    dr.ellipse((10, 10, d - 11, d - 11), outline=NAVY, width=4)
    f1 = F(900, int(d * 0.25)); f2 = F(800, int(d * 0.13))
    for txt, f, yy in [(text1, f1, 0.30), (text2, f2, 0.60)]:
        tw = dr.textlength(txt, font=f); dr.text(((d - tw) / 2, d * yy - f.getmetrics()[0] * 0.55), txt, font=f, fill=NAVY)
    return im.rotate(12, resample=Image.BICUBIC, expand=True)

def lines(dr, x, y, rows, align='left', W=None):
    """rows: list of [(text, font, color)] per line."""
    for row in rows:
        widths = [dr.textlength(t, font=f) for t, f, c in row]
        tw = sum(widths); xx = x if align == 'left' else (W - tw) / 2
        h = max(f.getmetrics()[0] + f.getmetrics()[1] for t, f, c in row)
        for (t, f, c), wd in zip(row, widths):
            dr.text((xx, y), t, font=f, fill=c, stroke_width=3, stroke_fill=(8, 12, 26)); xx += wd
        y += int(h * 0.98)
    return y

VK = Image.open('thumbsrc/v2_167.5.png').convert('RGBA').crop((0, 0, 1280, 690))   # coach tile, name label cropped off
BOARD = Image.open('thumbsrc/board975.png').convert('RGBA').crop((400, 20, 1960, 1400))

def pill(text, font, bg, fg, dot=None, padx=26, pady=12):
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1))); tw = d.textlength(text, font=font); asc, desc = font.getmetrics()
    extra = asc * 0.55 + 14 if dot else 0
    im = Image.new('RGBA', (int(tw + 2 * padx + extra), asc + desc + 2 * pady), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=bg)
    x = padx
    if dot:
        r = asc * .28; cy = im.height / 2; dr.ellipse((x, cy - r, x + 2 * r, cy + r), fill=dot); x += 2 * r + 14
    dr.text((x, pady - 1), text, font=font, fill=fg); return im

# ------------------------------------------------ 9:16 reel cover (key content inside centre 4:5 zone y 285..1635)
def vertical():
    W, H = 1080, 1920; im = glow_bg(W, H)
    b = BOARD.resize((1150, int(1150 * BOARD.height / BOARD.width)), Image.LANCZOS).rotate(-8, resample=Image.BICUBIC, expand=True)
    b.putalpha(b.split()[3].point(lambda p: int(p * 0.55)))
    b.putalpha(b.split()[3].point(lambda p: int(p * 0.75)))
    im.alpha_composite(b, ((W - b.width) // 2 + 60, 1250))
    fade = Image.new('RGBA', (W, 420), (0, 0, 0, 0)); fd = ImageDraw.Draw(fade)
    for i in range(420): fd.line((0, i, W, i), fill=NAVY + (int(235 * (1 - i / 420) ** 1.3),))
    im.alpha_composite(fade, (0, 1330))
    lg = logo_pill(330); im.alpha_composite(lg, ((W - lg.width) // 2, 300))
    dr = ImageDraw.Draw(im)
    y = lines(dr, 0, 440, [[('What happens when', F(800, 80), WHITE)], [('kids get ', F(800, 80), WHITE)],
                            [('NO RULES?', F(900, 150), GOLD)]], align='center', W=W)
    c = card(VK, 860, 484, angle=-3)
    paste_with_shadow(im, c, (W - c.width) // 2, y + 40)
    tag = pill('Coach VK', F(600, 36), (15, 23, 42, 225), WHITE, dot=TEAL)
    im.alpha_composite(tag, ((W - c.width) // 2 + 60, y + 80))
    st = sticker('FREE', 'FIRST CLASS', 250); im.alpha_composite(st, (W - st.width - 40, y + 330))
    p = pill('LIVE CLASS  ·  REAL STUDENTS  ·  GRADES 3–12', F(600, 34), (15, 23, 42, 235), WHITE, dot=CRIMSON)
    im.alpha_composite(p, ((W - p.width) // 2, y + 40 + c.height + 36))
    im.convert('RGB').save('out/TomoClub_SEL_Reel_cover_9x16.jpg', quality=95)
    # 4:5 grid preview crop (what the profile grid shows)
    im.convert('RGB').crop((0, 285, 1080, 1635)).save('chk/cover_grid_preview.jpg', quality=90)

# ------------------------------------------------ 16:9 LinkedIn thumbnail
def horizontal():
    W, H = 1920, 1080; im = glow_bg(W, H)
    b = BOARD.resize((1000, int(1000 * BOARD.height / BOARD.width)), Image.LANCZOS).rotate(8, resample=Image.BICUBIC, expand=True)
    b.putalpha(b.split()[3].point(lambda p: int(p * 0.5)))
    im.alpha_composite(b, (W - b.width + 120, H - b.height + 160))
    lg = logo_pill(330); im.alpha_composite(lg, (100, 90))
    dr = ImageDraw.Draw(im)
    y = lines(dr, 100, 250, [[('What happens when', F(800, 86), WHITE)], [('kids get', F(800, 86), WHITE)],
                              [('NO RULES?', F(900, 160), GOLD)]])
    dr.text((104, y + 20), 'Inside a live TomoClub Life Skills class', font=F(600, 44), fill=(226, 232, 240))
    p = pill('LIVE CLASS  ·  REAL STUDENTS  ·  GRADES 3–12', F(600, 32), (255, 255, 255, 40), WHITE, dot=CRIMSON)
    im.alpha_composite(p, (100, y + 110))
    c = card(VK, 820, 461, angle=3)
    paste_with_shadow(im, c, 1010, 250)
    tag = pill('Coach VK', F(600, 34), (15, 23, 42, 225), WHITE, dot=TEAL)
    im.alpha_composite(tag, (1070, 300))
    st = sticker('FREE', 'FIRST CLASS', 250); im.alpha_composite(st, (1640, 640))
    im.convert('RGB').save('out/TomoClub_SEL_LinkedIn_thumbnail_16x9.jpg', quality=95)

vertical(); horizontal(); print('ok')
