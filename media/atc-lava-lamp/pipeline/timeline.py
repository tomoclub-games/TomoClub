"""Edit decision list for the ATC lava-lamp hype video (shared by render + audio).

Source coords are inside the 960x720 camera area of the Zoom recording (x offset 160).
Markup in text: *highlight*  {emoji}  ~subscript~
"""
BPM = 128
B = 60 / BPM
BAR = 4 * B
END = 62.5


def bt(bar, beat=0.0):
    return (bar - 1) * BAR + beat * B


# ------------------------------------------------------------------ shots
# grade: day | glow ; z = (zoom_start, zoom_end) ; f = focus (x, y) in source px
SHOTS = [
    # HOOK
    dict(t0=0.0, t1=bt(2), src=1293.0, grade='glow', f=(450, 300), z=(1.12, 1.3)),
    dict(t0=bt(2), t1=bt(3), src=1415.0, grade='glow', f=(470, 270), z=(1.25, 1.45)),
    # TITLE (background)
    dict(t0=bt(3), t1=bt(5), src=1455.0, grade='glow', f=(565, 280), z=(1.0, 1.12), dim=0.55, blur=9, tint=0.3),
    # YOU'LL NEED
    dict(t0=bt(5), t1=bt(6), src=923.0, grade='day', f=(420, 470), z=(1.0, 1.1)),
    dict(t0=bt(6), t1=bt(6, 2), src=825.6, grade='day', f=(480, 470), z=(1.35, 1.45)),
    dict(t0=bt(6, 2), t1=bt(7), src=840.0, grade='day', f=(470, 400), z=(1.3, 1.4)),
    dict(t0=bt(7), t1=bt(7, 2), src=970.3, grade='day', f=(520, 330), z=(1.3, 1.4)),
    dict(t0=bt(7, 2), t1=bt(8), src=1076.5, grade='day', f=(760, 260), z=(1.05, 1.15)),
    dict(t0=bt(8), t1=bt(8, 2), src=1121.0, grade='day', f=(430, 560), z=(1.2, 1.3)),
    dict(t0=bt(8, 2), t1=bt(9), src=1182.3, grade='day', f=(740, 380), z=(1.3, 1.4)),
    # STEPS
    dict(t0=bt(9), t1=bt(10), src=868.3, grade='day', f=(540, 470), z=(1.15, 1.25)),
    dict(t0=bt(10), t1=bt(11), src=987.0, grade='day', f=(480, 520), z=(1.15, 1.25), speed=1.35),
    dict(t0=bt(11), t1=bt(12), src=1046.8, grade='day', f=(560, 420), z=(1.15, 1.25), speed=1.3),
    dict(t0=bt(12), t1=bt(12, 2), src=1146.3, grade='day', f=(540, 300), z=(1.3, 1.38)),
    dict(t0=bt(12, 2), t1=bt(13), src=1153.4, grade='day', f=(470, 260), z=(1.2, 1.28)),
    dict(t0=bt(13), t1=bt(14), src=1196.8, grade='day', f=(380, 470), z=(1.2, 1.3), speed=1.25),
    dict(t0=bt(14), t1=bt(15), src=1212.5, grade='day', f=(420, 330), z=(1.0, 1.08), speed=1.1),
    # BUILD: countdown (synced voice)
    dict(t0=bt(15), t1=29.85, src=1174.35, grade='day', f=(470, 300), z=(1.05, 1.35)),
    dict(t0=29.85, t1=bt(17), black=True),
    # DROP
    dict(t0=bt(17), t1=bt(18), src=1231.2, grade='glow', f=(400, 330), z=(1.1, 1.2), punch=True),
    dict(t0=bt(18), t1=bt(19), src=1233.2, grade='glow', f=(420, 330), z=(1.2, 1.28), punch=True),
    dict(t0=bt(19), t1=bt(21), src=1294.0, grade='glow', f=(450, 300), z=(1.08, 1.3), punch=True),
    dict(t0=bt(21), t1=bt(22), src=1351.5, grade='glow', f=(330, 430), z=(1.1, 1.2), punch=True),
    dict(t0=bt(22), t1=bt(23), src=1389.5, grade='glow', f=(467, 270), z=(1.3, 1.4), punch=True),
    dict(t0=bt(23), t1=bt(24), src=1418.0, grade='glow', f=(475, 270), z=(1.3, 1.4), punch=True),
    dict(t0=bt(24), t1=bt(25), src=1462.0, grade='glow', f=(565, 270), z=(1.2, 1.38), punch=True),
    # SCIENCE
    dict(t0=bt(25), t1=bt(27), src=1300.0, grade='glow', f=(450, 430), z=(1.08, 1.15), dim=0.85),
    dict(t0=bt(27), t1=bt(29), src=1355.0, grade='glow', f=(330, 440), z=(1.05, 1.15), dim=0.85),
    dict(t0=bt(29), t1=bt(31), src=1470.0, grade='glow', f=(565, 270), z=(1.1, 1.3), dim=0.85),
    # OUTRO
    dict(t0=bt(31), t1=bt(32), src=806.0, grade='day', f=(430, 300), z=(1.1, 1.2)),
    dict(t0=bt(32), t1=END, endcard=True),
]

# flashes: (time, duration, strength)
FLASHES = [(bt(3), 0.25, 0.9), (bt(5), 0.12, 0.5), (bt(9), 0.12, 0.5), (bt(17), 0.35, 1.0), (bt(19), 0.12, 0.45),
           (bt(21), 0.15, 0.6), (bt(25), 0.2, 0.6), (bt(31), 0.2, 0.6), (bt(32), 0.25, 0.9)]
# camera shakes: (time, duration, amplitude in output px)
SHAKES = [(bt(3), 0.35, 18), (bt(17), 0.5, 26), (bt(21), 0.3, 14), (bt(31), 0.3, 14)]

# ------------------------------------------------------------------ text
# pos per format: (x, y, anchor)  anchor c=center, l=left
# size per format; lines: list of (markup, size_multiplier)
T = []


def add(**kw):
    T.append(kw)


# HOOK
add(kind='hype', t0=0.0, t1=bt(2), anim='settle',
    lines={'h': [('CAN YOU MAKE A', 0.42)], 'v': [('CAN YOU MAKE A', 0.46)]},
    size={'h': 170, 'v': 150}, pos={'h': (960, 350), 'v': (540, 560)}, maxw={'h': 1500, 'v': 980})
add(kind='hype', t0=0.0, t1=bt(2), anim='settle', delay=0.12,
    lines={'h': [('*LAVA LAMP* {🌋}', 1.0)], 'v': [('*LAVA LAMP*', 1.0), ('{🌋}', 0.9)]},
    size={'h': 190, 'v': 170}, pos={'h': (960, 500), 'v': (540, 790)}, maxw={'h': 1500, 'v': 1000})
add(kind='hype', t0=bt(2), t1=bt(3), anim='pop',
    lines={'h': [('WITH STUFF FROM', 0.42)], 'v': [('WITH STUFF FROM', 0.46)]},
    size={'h': 170, 'v': 150}, pos={'h': (960, 350), 'v': (540, 560)}, maxw={'h': 1500, 'v': 980})
add(kind='hype', t0=bt(2, 0.5), t1=bt(3), anim='slam',
    lines={'h': [('*YOUR KITCHEN?!* {🤯}', 1.0)], 'v': [('*YOUR*', 1.0), ('*KITCHEN?!* {🤯}', 1.0)]},
    size={'h': 170, 'v': 150}, pos={'h': (960, 500), 'v': (540, 790)}, maxw={'h': 1600, 'v': 1000})

# TITLE
add(kind='logocard', t0=bt(3), t1=bt(5), anim='pop', size={'h': 400, 'v': 600},
    pos={'h': (960, 330), 'v': (540, 700)})
add(kind='hype', t0=bt(3, 1), t1=bt(5), anim='slam',
    lines={'h': [('DIY *LAVA LAMP*', 1.0)], 'v': [('DIY', 0.7), ('*LAVA LAMP*', 1.0)]},
    size={'h': 150, 'v': 160}, pos={'h': (960, 690), 'v': (540, 1200)}, maxw={'h': 1600, 'v': 1000})
add(kind='chip', t0=bt(3, 2), t1=bt(5), anim='pop', text='SCIENCE EXPERIMENT {🧪}', color='teal',
    size={'h': 54, 'v': 54}, pos={'h': (960, 860), 'v': (540, 1450)}, sfx='pop')

# YOU'LL NEED
add(kind='hype', t0=bt(5), t1=bt(6), anim='slam',
    lines={'h': [("YOU'LL *NEED*", 1.0)], 'v': [("YOU'LL *NEED*", 1.0)]},
    size={'h': 140, 'v': 130}, pos={'h': (960, 190), 'v': (540, 420)}, maxw={'h': 1500, 'v': 980})
add(kind='chip', t0=bt(5, 1.5), t1=bt(6), anim='pop', text='Easy stuff from home! {🏠}', color='green',
    size={'h': 50, 'v': 48}, pos={'h': (960, 330), 'v': (540, 560)}, sfx='pop')
ITEMS = ['EMPTY GLASS', 'BAKING SODA', 'VEGETABLE OIL', 'VINEGAR', 'FOOD COLOUR', 'TORCH {🔦}']
for i, name in enumerate(ITEMS):
    t0 = bt(6) + i * 2 * B
    add(kind='item', t0=t0, t1=t0 + 2 * B, anim='pop', num=i + 1, text=name,
        size={'h': 66, 'v': 62}, pos={'h': (960, 170), 'v': (540, 440)}, sfx='pop')

# STEPS
STEPS = [
    (bt(9), bt(10), 'Add 1 spoon of *BAKING SODA*', ['Add 1 spoon of', '*BAKING SODA*']),
    (bt(10), bt(11), 'Pour in *VEGETABLE OIL*', ['Pour in', '*VEGETABLE OIL*']),
    (bt(11), bt(12), 'Pour *VINEGAR* into a cup', ['Pour *VINEGAR*', 'into a cup']),
    (bt(12), bt(13), 'Add drops of *FOOD COLOUR*', ['Add drops of', '*FOOD COLOUR*']),
    (bt(13), bt(14), 'Pour it into the *OIL!*', ['Pour it into', 'the *OIL!*']),
    (bt(14), bt(15), 'Place it on a *TORCH* {🔦}', ['Place it on', 'a *TORCH* {🔦}']),
]
for i, (t0, t1, lh, lv) in enumerate(STEPS):
    add(kind='step', t0=t0, t1=t1, anim='pop', num=i + 1, size={'h': 50, 'v': 50},
        pos={'h': (90, 120, 'l'), 'v': (540, 320)}, sfx='pop')
    add(kind='hype', t0=t0 + 0.1, t1=t1, anim='slide',
        lines={'h': [(lh, 1.0)], 'v': [(l, 1.0) for l in lv]},
        size={'h': 76, 'v': 84}, pos={'h': (90, 250, 'l'), 'v': (540, 520)}, maxw={'h': 1350, 'v': 1000},
        align={'h': 'l', 'v': 'c'})

# BUILD / COUNTDOWN
add(kind='hype', t0=26.3, t1=27.15, anim='pop', lines={'h': [('READY?', 1.0)], 'v': [('READY?', 1.0)]},
    size={'h': 150, 'v': 150}, pos={'h': (960, 560), 'v': (540, 900)}, maxw={'h': 1500, 'v': 980})
for n, (t0, t1) in zip('321', [(27.2, 27.55), (27.55, 28.0), (28.0, 28.85)]):
    add(kind='count', t0=t0, t1=t1, anim='slam', lines={'h': [(f'*{n}*', 1.0)], 'v': [(f'*{n}*', 1.0)]},
        size={'h': 420, 'v': 460}, pos={'h': (960, 560), 'v': (540, 900)}, maxw={'h': 1500, 'v': 980})
add(kind='hype', t0=28.9, t1=29.85, anim='slam',
    lines={'h': [('LIGHTS… *OFF!*', 1.0)], 'v': [('LIGHTS…', 1.0), ('*OFF!*', 1.2)]},
    size={'h': 170, 'v': 170}, pos={'h': (960, 560), 'v': (540, 900)}, maxw={'h': 1600, 'v': 1000})

# DROP
DROP_TXT = [
    (bt(17, 1), bt(18), [('WHOA!! {🤯}', 1.0)], [('WHOA!! {🤯}', 1.0)]),
    (bt(18), bt(19), [("IT'S *GLOWING!* {✨}", 1.0)], [("IT'S", 0.7), ('*GLOWING!* {✨}', 1.0)]),
    (bt(19, 1), bt(21), [('WATCH THE BLOBS *RISE* {⬆️}', 1.0)], [('WATCH THE', 0.7), ('BLOBS *RISE* {⬆️}', 1.0)]),
    (bt(21), bt(22), [("IT'S *FIZZING!* {🫧}", 1.0)], [("IT'S", 0.7), ('*FIZZING!* {🫧}', 1.0)]),
    (bt(24), bt(25), [('A REAL *DIY LAVA LAMP* {🌋}', 1.0)], [('A REAL', 0.7), ('*DIY LAVA LAMP*', 1.0), ('{🌋}', 0.9)]),
]
for t0, t1, lh, lv in DROP_TXT:
    add(kind='hype', italic=True, t0=t0, t1=t1, anim='slam', lines={'h': lh, 'v': lv},
        size={'h': 150, 'v': 140}, pos={'h': (930, 170), 'v': (540, 450)}, maxw={'h': 1450, 'v': 1000})

# SCIENCE
add(kind='chip', t0=bt(25), t1=bt(31), anim='pop', text='THE SCIENCE {🔬}', color='yellow',
    size={'h': 58, 'v': 58}, pos={'h': (70, 105, 'l'), 'v': (540, 330)}, sfx='pop')
SCI = [
    (bt(25, 0.5), bt(27), "OIL & VINEGAR *DON'T MIX*",
     'Vinegar is heavier than oil, so it sinks to the bottom.'),
    (bt(27), bt(29), 'VINEGAR + BAKING SODA = *CO~2~ GAS*',
     'They react and make tons of tiny carbon dioxide bubbles!'),
    (bt(29), bt(31), 'UP {⬆️} … AND DOWN {⬇️}',
     'Bubbles lift the coloured vinegar up. At the top they pop, and the blob sinks back down!'),
]
CARD_POS = [{'h': (960, 935), 'v': (540, 1500)}, {'h': (1340, 890), 'v': (540, 1500)}, {'h': (960, 935), 'v': (540, 1500)}]
CARD_W = [{'h': 1300, 'v': 960}, {'h': 1060, 'v': 960}, {'h': 1400, 'v': 960}]
for (t0, t1, title, body), cp, cw in zip(SCI, CARD_POS, CARD_W):
    add(kind='card', t0=t0, t1=t1, anim='slide', title=title, body=body,
        size={'h': 58, 'v': 56}, width=cw, pos=cp, sfx='pop')
# layer labels on the glass (source-anchored)
add(kind='label', t0=bt(25, 2), t1=bt(27), anim='pop', text='OIL', color='yellow', anchor_src=(450, 300),
    size={'h': 56, 'v': 56}, sfx='pop')
add(kind='label', t0=bt(25, 3), t1=bt(27), anim='pop', text='VINEGAR', color='pink', anchor_src=(450, 445),
    size={'h': 56, 'v': 56}, sfx='pop')
add(kind='co2', t0=bt(27, 1), t1=bt(29), region_src=(110, 120, 430, 430))

# OUTRO
add(kind='hype', t0=bt(31), t1=bt(32), anim='slam',
    lines={'h': [('TRY IT AT *HOME!* {🏠}', 1.0)], 'v': [('TRY IT AT', 0.75), ('*HOME!* {🏠}', 1.0)]},
    size={'h': 140, 'v': 140}, pos={'h': (960, 200), 'v': (540, 440)}, maxw={'h': 1600, 'v': 1000})
add(kind='chip', t0=bt(31, 1), t1=bt(32), anim='pop', text='Ask a grown-up & wear gloves {🧤}', color='teal',
    size={'h': 50, 'v': 44}, pos={'h': (960, 345), 'v': (540, 640)}, sfx='pop')

WATERMARK = (bt(5), bt(32))

# ------------------------------------------------------------------ audio
VOICE = dict(src0=1174.35, src1=1177.95, t=bt(15))  # "let's do it… 3, 2, 1… lights off!"
SFX = []
for tt in [bt(5), bt(9), bt(25), bt(32)]:
    SFX.append(dict(type='whoosh', t=tt, gain=0.8))
SFX.append(dict(type='whoosh_down', t=28.9 + 0.3, gain=0.7))
SFX += [dict(type='tom_lo', t=27.2, gain=0.9), dict(type='tom', t=27.55, gain=0.9), dict(type='tom_hi', t=28.0, gain=0.9)]
for e in T:
    if e.get('sfx') == 'pop':
        SFX.append(dict(type='pop', t=e['t0'] + e.get('delay', 0), gain=0.7))
SFX.append(dict(type='pop', t=bt(32, 2), gain=0.7))
