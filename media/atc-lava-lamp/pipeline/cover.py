import sys
fmt = sys.argv[1]
sys.argv = ['render.py', fmt]
import render as R
from PIL import Image

W, H = R.W, R.H
clip = R.load_clip(1297.0, 0.1)
base = R.grade(clip[0], 'glow')
if fmt == 'h':
    bg = base.resize((W, H), Image.LANCZOS, box=(0, 90, 960, 630)).filter(R.ImageFilter.GaussianBlur(30))
    bg = Image.blend(bg, Image.new('RGB', (W, H), R.DKGREEN), 0.55)
    panel = base.resize((870, 1080), Image.LANCZOS, box=(160, 0, 740, 720))
    ramp = [min(255, int(i * 255 / 220)) for i in range(870)]
    mask = Image.new('L', (870, 1080))
    mask.putdata([ramp[x] for y in range(1080) for x in range(870)])
    bg.paste(panel, (W - 870 - 20, 0), mask)
    img = R.ImageChops.multiply(bg, R.VIG)
    card = R.logo_card(270)
    img.paste(card, (40, 20), card)
    t = R.stack([R.text_line('DIY', 130), R.text_line('*LAVA*', 230), R.text_line('*LAMP!* {🌋}', 230)], align='l', gap=-10)
    t = R.shadow(t, 10, 8, 0.7)
    img.paste(t, (30, 340), t)
    c = R.chip('EASY SCIENCE EXPERIMENT {🧪}', 44, 'teal')
    img.paste(c, (40, 940), c)
else:
    ch = 720; cw = ch * 9 / 16
    box = (450 - cw / 2, 0, 450 + cw / 2, ch)
    img = base.resize((W, H), Image.LANCZOS, box=box)
    img = R.ImageChops.multiply(img, R.VIG)
    card = R.logo_card(300)
    img.paste(card, ((W - card.width) // 2, 150), card)
    t = R.stack([R.text_line('DIY', 150), R.text_line('*LAVA LAMP!*', 175), R.text_line('{🌋}', 150)], gap=-6)
    t = R.fit(t, 1000)
    t = R.shadow(t, 10, 8, 0.7)
    img.paste(t, ((W - t.width) // 2, 560), t)
    c = R.chip('EASY SCIENCE EXPERIMENT {🧪}', 46, 'teal')
    img.paste(c, ((W - c.width) // 2, 1480), c)
img.save(f'cover_{fmt}.jpg', quality=92)
print('ok', fmt)
