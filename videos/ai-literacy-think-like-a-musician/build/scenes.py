"""Scene layouts. Each builder returns a list of animated elements for one scene."""
import math
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from gfx import (C, FPS, H, PITCH, SYM, W, Dyn, El, arc_ring, card, check_icon, circle, clamp01, ease,
                 lock_icon, note_block, paste, pill, rgba, rrect, shadowed, stamp, text_img, wordmark)

LX = 120            # left column x
RX = 1000           # right panel x
RW = 800            # right panel width
CLIP_W, CLIP_H = 1536, 864
CLIP_X, CLIP_Y = (W - CLIP_W) // 2, 150

# Student video tiles in the session recording (source pixels). They are already
# blurred in the source; we blur them again so no student can be recognised.
STUDENT_TILES = (1556, 222, 364, 858)


def _blur_filter(scale):
    x, y, w, h = STUDENT_TILES
    return (f"[0:v]fps={FPS},split[m][s];[s]crop={w}:{h}:{x}:{y},boxblur=24:3[b];"
            f"[m][b]overlay={x}:{y},scale={scale[0]}:{scale[1]}:flags=lanczos,format=rgb24")


def clip_frames(src, segs, size=(CLIP_W, CLIP_H)):
    fs = size[0] * size[1] * 3
    last = None
    for a, b in segs:
        n = round((b - a) * FPS)
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{a}", "-i", src, "-t", f"{b - a}",
                              "-filter_complex", _blur_filter(size), "-f", "rawvideo", "-"],
                             stdout=subprocess.PIPE)
        for _ in range(n):
            buf = p.stdout.read(fs)
            if len(buf) == fs:
                last = Image.frombuffer("RGB", size, buf)
            yield last
        p.stdout.close()
        p.wait()


def still(src, t, size):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", src, "-filter_complex", _blur_filter(size),
                          "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return Image.frombuffer("RGB", size, raw)


class ClipPlayer:
    def __init__(self, src, segs):
        self.gen = clip_frames(src, segs)
        self.idx, self.cur = -1, None

    def at(self, t):
        want = int(round(t * FPS))
        while self.idx < want:
            try:
                self.cur = next(self.gen)
            except StopIteration:
                pass
            self.idx += 1
        return self.cur


# ---------------------------------------------------------------- shared pieces

def move_header(n, title):
    return [
        El(pill(f"MOVE {n} OF 5", 26, 800, fg=C["navy"], bg=C["teal"]), LX, 108, 0.05),
        El(text_img(f"0{n}", 170, 800, color=C["gold"]), LX - 8, 150, 0.12),
        El(text_img(title, 84, 800, lh=1.04), LX, 370, 0.2),
    ]


def chrome(n):
    wm = wordmark(40)
    bars = Image.new("RGBA", (5 * 64 + 4 * 12, 10), (0, 0, 0, 0))
    for i in range(5):
        col = C["teal"] if i < n - 1 else C["gold"] if i == n - 1 else C["slate2"]
        bars.alpha_composite(rrect(64, 10, 5, fill=rgba(col)), (i * 76, 0))
    return [El(wm, W - 120 - wm.width, 108, 0.0, dy=0), El(bars, LX, 1012, 0.0, dy=0)]


def principle(markup, t0, t1=None, y=612):
    return El(text_img(markup, 40, 600, max_w=780), LX, y, t0, t1)


def try_it(markup, t0, label="TRY IT", t1=None, accent=C["gold"]):
    c = card(800, 168, fill=C["slate"], accent=accent)
    c.alpha_composite(pill(label, 22, 800, fg=C["navy"], bg=accent, padx=16, pady=6), (32, 26))
    c.alpha_composite(text_img(markup, 32, 600, max_w=730, accent=accent), (32, 78))
    return El(shadowed(c, blur=18, alpha=0.4), LX, 790, t0, t1)


def wipe(img, p, line_h):
    """Reveal a text sprite line by line, left to right (typing effect)."""
    p = clamp01(p)
    if p >= 1:
        return img
    lines = max(1, round(img.height / line_h))
    k = p * lines
    full = int(k)
    mask = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(mask)
    if full:
        d.rectangle([0, 0, img.width, full * line_h], fill=255)
    d.rectangle([0, full * line_h, int(img.width * (k - full)), (full + 1) * line_h], fill=255)
    out = img.copy()
    out.putalpha(Image.composite(img.getchannel("A"), mask, mask))
    return out


def chat_window(title, question, answer, answer_hl=None, w=390, h=470):
    """Returns (window sprite, [(sprite, dx, dy, kind)]) for the bubbles inside it."""
    win = card(w, h, fill=C["slate"], r=24)
    hd = ImageDraw.Draw(win)
    for i, col in enumerate((C["crimson"], C["gold"], C["teal"])):
        hd.ellipse([24 + i * 26, 26, 40 + i * 26, 42], fill=rgba(col))
    win.alpha_composite(text_img(title, 26, 700, color=C["muted"]), (112, 18))
    hd.line([(0, 66), (w, 66)], fill=rgba(C["line"], 160), width=2)
    q = text_img(question, 26, 600, color=C["navy"], max_w=w - 110)
    qb = rrect(q.width + 36, q.height + 28, 20, fill=rgba(C["teal"]))
    qb.alpha_composite(q, (18, 12))
    parts = [(qb, w - 20 - qb.width, 92, "q")]
    ay = 92 + qb.height + 22
    lab = text_img("AI", 22, 800, color=C["muted"])
    parts.append((lab, 24, ay, "label"))
    a = text_img(answer, 26, 500, color=C["text"], max_w=w - 100)
    ab = rrect(a.width + 36, a.height + 28, 20, fill=rgba(C["slate2"]))
    parts.append((ab, 20, ay + 34, "abg"))
    parts.append((a, 38, ay + 46, "a"))
    if answer_hl:
        parts.append((text_img(answer_hl, 26, 500, color=C["text"], accent=C["pink"], max_w=w - 100),
                      38, ay + 46, "ahl"))
    return win, parts


def chat_elements(x, y, title, question, answer, t0, answer_hl=None, t_hl=None, type_dur=2.2):
    win, parts = chat_window(title, question, answer, answer_hl)
    els = [El(shadowed(win, blur=18, alpha=0.45), x, y, t0)]
    for img, dx, dy, kind in parts:
        if kind == "q":
            els.append(El(img, x + dx, y + dy, t0 + 0.35, dy=16))
        elif kind == "label":
            els.append(El(img, x + dx, y + dy, t0 + 0.9, dy=0))
        elif kind == "abg":
            els.append(El(img, x + dx, y + dy, t0 + 0.9, dy=12))
        elif kind == "a":
            ta = t0 + 1.1

            def typed(frame, t, op, img=img, ta=ta, px=x + dx, py=y + dy):
                paste(frame, wipe(img, (t - ta) / type_dur, int(26 * 1.16)), px, py, op)

            els.append(Dyn(typed, ta, t_hl if answer_hl else None, fadein=0.01, fade=0.25))
        elif kind == "ahl":
            els.append(El(img, x + dx, y + dy, t_hl, dy=0, dur=0.3))
    return els


# ---------------------------------------------------------------- scenes

def hook(sc, q, ctx):
    t1, t2, t3, t4 = q("h1"), q("h2"), q("h3"), q("h4")
    els = [
        El(text_img("Listen...", 44, 600, color=C["muted"]), W / 2, 150, 0.1, t1 - 0.25, center=True),
        El(text_img("What note comes next?", 84, 800), W / 2, 128, t1, t2 - 0.4, center=True, fade=0.25),
        El(text_img("Your brain just made a *prediction.*", 84, 800), W / 2, 128, t2 + 0.05, t3 - 0.45,
           center=True, fade=0.25),
        El(text_img("AI doesn't know. It *predicts patterns.*", 84, 800), W / 2, 128, t3, t4 - 0.45,
           center=True, fade=0.25),
    ]
    cell, cols, rows, pad = 64, 12, 8, 24
    gw, gh = cols * cell + 2 * pad, rows * cell + 2 * pad
    gx, gy = (W - gw) // 2, 280
    grid = rrect(gw, gh, 26, fill=rgba(C["white"]))
    d = ImageDraw.Draw(grid)
    for c in range(cols + 1):
        col = (200, 206, 214) if c % 3 == 0 else (232, 235, 240)
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + rows * cell)], fill=col, width=2 if c % 3 == 0 else 1)
    for r in range(rows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(232, 235, 240), width=1)
    els.append(El(shadowed(grid), gx, gy, 0.0, t4 - 0.1, dy=20))
    ox, oy = gx + pad, gy + pad

    # playhead
    ph = Image.new("RGBA", (cell, rows * cell), rgba(C["teal"], 46))

    def playhead(frame, t, op):
        k = (t - 0.4) / 0.32
        if -0.5 <= k <= 11.5:
            paste(frame, ph, ox + k * cell, oy, op)

    els.append(Dyn(playhead, 0.2, 4.2, fadein=0.2))
    melody_rows = [7, 5, 3]
    for k in range(11):
        r = melody_rows[k % 3]
        els.append(El(note_block(cell - 8, cell - 8, PITCH[r]), ox + k * cell + 4, oy + r * cell + 4,
                      0.4 + k * 0.32, t4 - 0.1, dur=0.28, anim="pop"))
    # question column
    qcol = Image.new("RGBA", (cell, rows * cell), rgba(C["gold"], 70))
    qmark = text_img("?", 110, 800, color=C["gold"])

    def question(frame, t, op):
        pulse = 0.75 + 0.25 * abs(((t * 1.6) % 2) - 1)
        paste(frame, qcol, ox + 11 * cell, oy, op * pulse)
        paste(frame, qmark, ox + 11 * cell + (cell - qmark.width) / 2 + 2, oy + 0.4 * cell, op)

    t_q = 0.4 + 11 * 0.32
    els.append(Dyn(question, t_q - 0.1, t2 - 0.05, fadein=0.25, fade=0.2))
    g = note_block(cell - 8, cell - 8, PITCH[3])
    els.append(El(shadowed(g, blur=12, off=(0, 0), alpha=1.0, pad=24, color=C["gold"]), ox + 11 * cell + 4, oy + 3 * cell + 4, t2,
                  t4 - 0.1, dur=0.35, anim="pop"))
    lab = pill("Most likely next note", 28, 700, fg=C["navy"], bg=C["gold"])
    els.append(El(lab, gx + gw + 24, oy + 3 * cell + 2, t2 + 0.25, t4 - 0.1, dx=-20, dy=0))
    # words / images / sounds
    chips = [pill(s, 32, 700, fg=C["text"], bg=None, outline=C["teal"]) for s in ("Words", "Images", "Sounds")]
    total = sum(c.width for c in chips) + 2 * 24
    x = (W - total) / 2
    for i, (c, sub) in enumerate(zip(chips, ("words", "images", "sounds"))):
        els.append(El(c, x, gy + gh + 40, q("h2", sub), t4 - 0.1))
        x += c.width + 24
    # h4: five moves
    els.append(El(text_img("*5 moves* from musicians", 110, 800), W / 2, 330, t4 + 0.1, center=True))
    els.append(El(text_img("to use AI like a pro, not a passenger.", 52, 600, color=C["teal"]), W / 2, 500,
                  q("h4", "to help"), center=True))
    cols5 = [C["teal"], C["gold"], C["crimson"], C["violet"], (52, 152, 219)]
    for i in range(5):
        b = note_block(120, 120, cols5[i], r=18)
        num = text_img(str(i + 1), 64, 800, color=C["navy"])
        b.alpha_composite(num, ((120 - num.width) // 2, 14))
        els.append(El(b, W / 2 - 5 * 150 / 2 + i * 150 + 15, 660, t4 + 0.4 + i * 0.12, anim="pop"))
    return els


def title(sc, q, ctx):
    els = [
        El(wordmark(64), W / 2, 200, 0.05, center=True),
        El(text_img("Think Like a Musician", 128, 800), W / 2, 320, 0.15, center=True),
        El(text_img("5 AI Literacy Moves for Students", 58, 600, color=C["teal"]), W / 2, 490, 0.35, center=True),
        El(text_img("Narration: AI-generated voice", 26, 400, color=C["muted"]), W / 2, 1000, 0.6, center=True),
    ]
    contour = [7, 5, 3, 5, 4, 2, 0, 2, 3, 5, 6, 7]
    for i, r in enumerate(contour):
        els.append(El(note_block(64, 64, PITCH[r], r=10), W / 2 - 12 * 84 / 2 + i * 84 + 10, 640 + r * 22,
                      0.4 + i * 0.05, dur=0.3, anim="pop"))
    return els


def soundcheck(sc, q, ctx):
    ttl = text_img("Sound Check", 96, 800)
    els = [
        El(pill("BEFORE YOU START", 26, 800, fg=C["navy"], bg=C["gold"]), LX, 108, 0.1),
        El(ttl, LX, 160, 0.15),
    ]
    mx = LX + ttl.width + 40

    def meter(frame, t, op):
        d = ImageDraw.Draw(frame)
        for i in range(6):
            h = 20 + 70 * abs(math.sin(t * (2.1 + i * 0.7) + i))
            col = PITCH[(i * 2) % 8]
            c = tuple(int(C["navy"][k] + (col[k] - C["navy"][k]) * op) for k in range(3))
            d.rounded_rectangle([mx + i * 30, 290 - h, mx + i * 30 + 18, 290], 6, fill=c)

    els.append(Dyn(meter, 0.3))
    specs = [
        (q("s2"), C["teal"], "badge", "Students 13+", "This video is made for teens."),
        (q("s2", "Only use"), C["gold"], "check", "Approved tools only",
         "Approved by your school or a parent/guardian. Follow each tool's age rules."),
        (q("s3"), C["crimson"], "billboard", "The Billboard Test",
         "Wouldn't put it on a billboard outside your school? Don't type it."),
    ]
    cw, ch = 530, 420
    for i, (t0, col, icon, head, body) in enumerate(specs):
        c = card(cw, ch, fill=C["slate"], accent=col)
        if icon == "badge":
            b = circle(120, fill=rgba(col))
            tx = text_img("13+", 46, 800, color=C["navy"])
            b.alpha_composite(tx, ((120 - tx.width) // 2, (120 - tx.height) // 2 + 2))
        elif icon == "check":
            b = check_icon(120, col)
        else:
            b = Image.new("RGBA", (150, 120), (0, 0, 0, 0))
            bd = ImageDraw.Draw(b)
            bd.rounded_rectangle([0, 0, 149, 80], 10, fill=rgba(col))
            for k in range(3):
                bd.rounded_rectangle([18, 16 + k * 20, 130 - k * 30, 26 + k * 20], 4, fill=(255, 255, 255, 220))
            bd.rectangle([36, 80, 46, 119], fill=rgba(col))
            bd.rectangle([104, 80, 114, 119], fill=rgba(col))
        c.alpha_composite(b, (40, 50))
        c.alpha_composite(text_img(head, 42, 800), (40, 200))
        c.alpha_composite(text_img(body, 30, 500, color=C["muted"], max_w=450, lh=1.28), (40, 262))
        els.append(El(shadowed(c, alpha=0.45), LX + i * (cw + 45), 350, t0))
    subs = [("No full names", "No full names"), ("No addresses", "addresses"), ("No passwords", "passwords"),
            ("No photos of friends", "photos")]
    pills = [pill(s, 28, 700, fg=C["pink"], bg=None, outline=C["crimson"]) for s, _ in subs]
    x = LX
    for p_, (_, sub) in zip(pills, subs):
        els.append(El(p_, x, 820, q("s3", sub), anim="pop", dur=0.35))
        x += p_.width + 20
    return els


def m1_intro(sc, q, ctx):
    els = move_header(1, "Guess the\nNext Note") + chrome(1)
    els.append(principle("AI writes by predicting *what comes next.*", q("m1a") + 0.7))
    t = q("m1b")
    els.append(El(pill("Real TomoClub session", 26, 800, fg=C["navy"], bg=C["teal"]), RX, 200, t))
    img = ctx["still_a"].copy()
    mask = rrect(img.width, img.height, 22, fill=(255, 255, 255, 255))
    framed = Image.new("RGBA", img.size, (0, 0, 0, 0))
    framed.paste(img, (0, 0), mask)
    els.append(El(shadowed(framed), RX, 270, t + 0.15))
    play = circle(128, fill=(255, 255, 255, 235))
    pd = ImageDraw.Draw(play)
    pd.polygon([(50, 36), (50, 92), (98, 64)], fill=rgba(C["teal"]))
    px, py = RX + (img.width - 128) / 2, 270 + (img.height - 128) / 2

    def pulse(frame, t_, op):
        s = 1 + 0.06 * abs(((t_ * 1.2) % 2) - 1)
        n = int(128 * s)
        paste(frame, play.resize((n, n), Image.BILINEAR), px - (n - 128) / 2, py - (n - 128) / 2, op)

    els.append(Dyn(pulse, t + 0.5))
    els.append(El(text_img("Chrome Music Lab  ·  Song Maker", 34, 600, color=C["text"]), RX, 270 + img.height + 26,
                  t + 0.3))
    note = lock_icon(28, C["muted"])
    txt = text_img("Student faces & names blurred for privacy", 26, 500, color=C["muted"])
    row = Image.new("RGBA", (40 + txt.width, max(30, txt.height)), (0, 0, 0, 0))
    row.alpha_composite(note, (0, 0))
    row.alpha_composite(txt, (40, -2))
    els.append(El(row, RX, 270 + img.height + 80, t + 0.45))
    return els


def clip_scene(sc, q, ctx, segs, callouts):
    D = sc["dur"]
    player = ClipPlayer(ctx["src"], segs)
    mask = rrect(CLIP_W, CLIP_H, 22, fill=(255, 255, 255, 255)).getchannel("A")
    border = rrect(CLIP_W + 6, CLIP_H + 6, 25, outline=rgba(C["line"]), ow=3)

    def video(frame, t, op):
        f = player.at(t)
        if f is None:
            return
        m = mask if op >= 0.997 else mask.point(lambda v: int(v * op))
        frame.paste(f, (CLIP_X, CLIP_Y), m)
        paste(frame, border, CLIP_X - 3, CLIP_Y - 3, op)

    els = [Dyn(video, 0.0, D - 0.3, fadein=0.3, fade=0.3)]
    tag = pill("Real TomoClub session", 26, 800, fg=C["navy"], bg=C["teal"])
    els.append(El(tag, CLIP_X, 70, 0.0, dy=0))
    els.append(El(text_img("Chrome Music Lab  ·  Song Maker", 30, 600), CLIP_X + tag.width + 22, 76, 0.1, dy=0))
    txt = text_img("Student faces & names blurred for privacy", 24, 500, color=C["muted"])
    row = Image.new("RGBA", (38 + txt.width, 30), (0, 0, 0, 0))
    row.alpha_composite(lock_icon(26, C["muted"]), (0, 0))
    row.alpha_composite(txt, (38, -1))
    els.append(El(row, CLIP_X + CLIP_W - row.width, 80, 0.1, dy=0))
    for t0, t1, text in callouts:
        c = pill(text, 34, 800, fg=C["navy"], bg=C["gold"], padx=28, pady=14)
        els.append(El(shadowed(c, blur=14, alpha=0.5, pad=30), CLIP_X + 36, CLIP_Y + 36, t0, t1, dy=0, dx=-30))
    return els


def clipA(sc, q, ctx):
    return clip_scene(sc, q, ctx, ctx["clips"]["clipA"], [(9.7, 12.6, "Anticipate = predict what comes next")])


def clipB(sc, q, ctx):
    return clip_scene(sc, q, ctx, ctx["clips"]["clipB"], [
        (1.95, 6.35, "Experimenting is how you learn"),
        (11.95, 17.15, "Spotting patterns is an AI literacy skill"),
    ])


def m1_body(sc, q, ctx):
    tc, td, te = q("m1c"), q("m1d"), q("m1e")
    els = move_header(1, "Guess the\nNext Note") + chrome(1)
    els.append(principle("AI predicts the *most likely* next piece.", tc, te - 0.1))
    els.append(principle("AI plays it safe. *Surprise* is your job.", te + 0.15))
    els.append(try_it("Build 3 bars in Song Maker. Ask a friend to guess *bar 4.*", q("m1d", "Build")))

    # Phase 1: prediction bars
    els.append(El(pill("HOW AI WRITES: ONE PIECE AT A TIME", 24, 800, fg=C["navy"], bg=C["teal"]), RX, 200, tc,
                  td - 0.15))
    pc = card(RW, 520, fill=C["slate"])
    pc.alpha_composite(text_img("Twinkle, twinkle, little ___", 54, 700), (48, 44))
    rows = [("star", 1.0, C["teal"], "most likely"), ("light", 0.46, C["gold"], "possible"),
            ("pickle", 0.12, C["crimson"], "surprising")]
    for i, (w_, _, _, tag) in enumerate(rows):
        pc.alpha_composite(text_img(w_, 44, 700), (48, 170 + i * 110))
        pc.alpha_composite(text_img(tag, 24, 600, color=C["muted"]), (250, 226 + i * 110))
    els.append(El(shadowed(pc, alpha=0.45), RX, 270, tc + 0.1, td - 0.15))
    t_bars = q("m1c", "AI writes")

    def bars(frame, t, op):
        for i, (_, frac, col, _) in enumerate(rows):
            p = ease((t - t_bars - i * 0.35) / 0.9)
            if p <= 0:
                continue
            w = max(12, int(470 * frac * p))
            paste(frame, rrect(w, 40, 12, fill=rgba(col)), RX + 250, 270 + 180 + i * 110, op)

    els.append(Dyn(bars, t_bars, td - 0.15, fadein=0.01))

    # Phase 2: 4-bar Song Maker grid
    cell, cols, nrows, pad = 46, 16, 8, 24
    gw, gh = cols * cell + 2 * pad, nrows * cell + 2 * pad
    gx, gy = RX + (RW - gw) // 2, 290
    grid = rrect(gw, gh, 22, fill=rgba(C["white"]))
    d = ImageDraw.Draw(grid)
    for c in range(cols + 1):
        col = (190, 196, 206) if c % 4 == 0 else (232, 235, 240)
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + nrows * cell)], fill=col, width=2 if c % 4 == 0 else 1)
    for r in range(nrows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(232, 235, 240), width=1)
    t_grid = td + 0.1
    els.append(El(pill("TRY IT IN SONG MAKER", 24, 800, fg=C["navy"], bg=C["gold"]), RX, 200, t_grid))
    els.append(El(shadowed(grid), gx, gy, t_grid))
    ox, oy = gx + pad, gy + pad
    melody = [7, 5, 3, 5, 6, 4, 2, 4, 5, 3, 1, 3]
    for k, r in enumerate(melody):
        els.append(El(note_block(cell - 6, cell - 6, PITCH[r], r=6), ox + k * cell + 3, oy + r * cell + 3,
                      t_grid + 0.4 + k * 0.08, dur=0.25, anim="pop"))
    t_q = q("m1d", "ask a friend")
    t_safe = q("m1d", "Notice how often")
    t_sur = q("m1e", "choose the surprising")
    shade = Image.new("RGBA", (4 * cell, nrows * cell), rgba(C["gold"], 60))
    qm = text_img("?", 90, 800, color=C["gold"])
    els.append(El(shade, ox + 12 * cell, oy, t_q, t_sur, dy=0))
    els.append(El(qm, ox + 14 * cell - qm.width / 2, oy + (nrows * cell - qm.height) / 2, t_q, t_safe, dy=0))
    safe = [4, 2, 0, 2]
    ghost = rrect(cell - 6, cell - 6, 6, outline=(120, 130, 145, 255), ow=3)
    for k, r in enumerate(safe):
        els.append(El(ghost, ox + (12 + k) * cell + 3, oy + r * cell + 3, t_safe + k * 0.1, t_sur, dur=0.25,
                      anim="pop"))
    surprise = [0, 6, 1, 7]
    for k, r in enumerate(surprise):
        b = note_block(cell - 6, cell - 6, C["gold"], r=6)
        els.append(El(shadowed(b, blur=10, off=(0, 0), alpha=1.0, pad=20, color=C["white"]), ox + (12 + k) * cell + 3,
                      oy + r * cell + 3, t_sur + k * 0.12, dur=0.3, anim="pop"))
    ly = gy + gh + 30
    els.append(El(pill("Bar 4: your friend guesses", 28, 700, fg=C["text"], bg=None, outline=C["gold"]), RX, ly,
                  t_q, t_safe - 0.1))
    els.append(El(pill("The safe, expected guess", 28, 700, fg=C["text"], bg=None, outline=C["muted"]), RX, ly,
                  t_safe, t_sur - 0.1))
    els.append(El(pill("Your surprising choice", 28, 800, fg=C["navy"], bg=C["gold"]), RX, ly, t_sur + 0.2))
    return els


def m2(sc, q, ctx):
    els = move_header(2, "Play It\nTwice") + chrome(2)
    els.append(principle("Same question. *Brand-new chat.* Compare.", q("m2b")))
    els.append(try_it("Facts changed? Treat that part as a *rumor* until you check it.",
                      q("m2c", "Treat that part")))
    question = "When did our town's library first open?"
    t_hl = q("m2c", "If a name")
    els += chat_elements(RX, 190, "Chat 1", question, "Our town's library first opened in 1962.", q("m2b") + 0.3,
                         answer_hl="Our town's library first opened in *1962.*", t_hl=t_hl)
    els += chat_elements(RX + 410, 190, "New chat", question, "It opened its doors in 1958, after a local fundraiser.",
                         q("m2b", "Open a brand-new chat"),
                         answer_hl="It opened its doors in *1958,* after a local fundraiser.", t_hl=t_hl)
    els.append(El(pill("Same answer twice? Good sign.", 30, 700, fg=C["navy"], bg=C["teal"]), RX + 190, 720,
                  q("m2c"), t_hl - 0.1))
    els.append(El(stamp("FACTS CHANGED = IT WAS GUESSING", C["pink"], 40), RX + 40, 700, t_hl + 0.1, anim="pop",
                  dur=0.4))
    return els


def m3(sc, q, ctx):
    els = move_header(3, "Flip the\nKey") + chrome(3)
    tb, tcq, td = q("m3b"), q("m3c"), q("m3d")
    els.append(principle("The way you ask *changes* the answer.", q("m3b", "Questions work"), td - 0.1))
    els.append(principle("Agrees with both sides? It's *following your lead.*", td + 0.1))
    els.append(try_it("“What are the pros and cons of each?”", q("m3d", "So ask neutral"),
                      label="ASK NEUTRAL QUESTIONS", accent=C["teal"]))
    # phase 1: major vs minor
    pc = card(RW, 480, fill=C["slate"])
    for j, (name, mood, col, ys) in enumerate((("MAJOR", "bright", C["gold"], [110, 172, 234]),
                                               ("MINOR", "moody", C["violet"], [110, 194, 234]))):
        bx = 90 + j * 400
        pc.alpha_composite(text_img(name, 34, 800, color=col), (bx, 40))
        for y_ in ys:
            pc.alpha_composite(note_block(220, 40, col, r=10), (bx, y_))
        pc.alpha_composite(text_img(mood, 40, 700), (bx, 300))
    ad = ImageDraw.Draw(pc)
    ad.text((360, 150), "⇄", font=SYM(72), fill=rgba(C["text"]))
    pc.alpha_composite(text_img("One small flip, a whole new mood.", 32, 600, color=C["muted"]), (90, 400))
    els.append(El(pill("SAME NOTES, ONE FLIP", 24, 800, fg=C["navy"], bg=C["violet"]), RX, 200, tb, tcq - 0.15))
    els.append(El(shadowed(pc, alpha=0.45), RX, 270, tb + 0.1, tcq - 0.15))
    # phase 2: two leading questions
    els += chat_elements(RX, 190, "Chat 1", "Why is studying in the morning better?",
                         "Great question! Morning study is better because your mind is fresh and focused...",
                         tcq + 0.1)
    els += chat_elements(RX + 410, 190, "New chat", "Why is studying at night better?",
                         "Great question! Night study is better because it's quiet and calm...",
                         q("m3c", "Then, in a new chat"))
    els.append(El(stamp("IT AGREED BOTH TIMES", C["pink"], 44), RX + 150, 700, td + 0.3, anim="pop", dur=0.4))
    return els


def m4(sc, q, ctx):
    els = move_header(4, "Find the\nSheet Music") + chrome(4)
    els.append(principle("Before you repeat it, *find the receipt.*", q("m4b")))
    els.append(try_it("No receipt? *Don't repeat it.*", q("m4c", "No receipt"), label="THE RULE",
                      accent=C["crimson"]))
    rw, rh = 560, 680
    r = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
    rd = ImageDraw.Draw(r)
    zig = 18
    pts = [(0, 0), (rw, 0), (rw, rh - zig)]
    for i in range(rw // zig, -1, -1):
        pts.append((i * zig, rh - (zig if i % 2 == 0 else 0)))
    rd.polygon(pts, fill=rgba(C["paper"]))
    head = text_img("FACT  RECEIPT", 44, 800, color=C["ink"])
    r.alpha_composite(head, ((rw - head.width) // 2, 40))
    for x in range(40, rw - 40, 18):
        rd.line([(x, 118), (x + 9, 118)], fill=(160, 166, 176), width=2)
    r.alpha_composite(text_img("Before I repeat this fact, I...", 28, 600, color=(71, 85, 105)), (40, 140))
    items = ["Opened the source myself", "Checked it's a trustworthy source", "Found the exact line",
             "Clicked every link the AI gave me"]
    for i, it in enumerate(items):
        y = 212 + i * 88
        rd.rounded_rectangle([40, y, 84, y + 44], 8, outline=(120, 130, 145), width=3)
        r.alpha_composite(text_img(it, 28, 600, color=C["ink"], max_w=400), (104, y + 4))
    for x in range(40, rw - 40, 18):
        rd.line([(x, 572), (x + 9, 572)], fill=(160, 166, 176), width=2)
    r.alpha_composite(text_img("TOTAL:  1 CHECKED FACT", 30, 800, color=C["ink"]), (40, 594))
    ry, rx0 = 200, RX + 70
    els.append(El(shadowed(r, alpha=0.5), rx0, ry, q("m4b") + 0.2))
    cues = [q("m4b", "Open a real source"), q("m4b", "like a textbook"), q("m4b", "find the exact line"),
            q("m4c", "clicked it")]
    for i, t0 in enumerate(cues):
        els.append(El(check_icon(52, C["teal"], C["white"]), rx0 + 36, ry + 208 + i * 88, t0, anim="pop",
                      dur=0.35))
    els.append(El(stamp("VERIFIED", C["teal"], 54, angle=-10), rx0 + 400, ry + 610, q("m4c", "No receipt") - 0.4,
                  anim="pop", dur=0.4))
    return els


def m5(sc, q, ctx):
    els = move_header(5, "Play It\nBy Ear") + chrome(5)
    tb, tc, td = q("m5b"), q("m5c"), q("m5d")
    els.append(principle("Can you play it *without the sheet?*", tb, td - 0.1))
    els.append(principle("AI should *train* your brain, not replace it.", td + 0.1))
    els.append(try_it("Close the tab. Explain it out loud in *30 seconds.*", q("m5c", "close the tab")))
    # phase 1: sheet music
    sh = rrect(720, 400, 22, fill=rgba(C["paper"]))
    sd = ImageDraw.Draw(sh)
    for i in range(5):
        sd.line([(50, 120 + i * 30), (670, 120 + i * 30)], fill=(90, 100, 115), width=3)
    notes = [(110, 4), (190, 3), (270, 2), (350, 3), (430, 1), (510, 2), (590, 0)]
    for x, k in notes:
        y = 120 + k * 30 + 15
        sd.ellipse([x - 20, y - 14, x + 20, y + 14], fill=C["ink"])
        sd.line([(x + 18, y), (x + 18, y - 95)], fill=C["ink"], width=5)
    sh.alpha_composite(text_img("Reading along isn't the same as knowing it.", 30, 600, color=(71, 85, 105)),
                       (50, 320))
    els.append(El(shadowed(sh, alpha=0.45), RX + 40, 300, tb + 0.1, tc - 0.15))
    # phase 2: 30 second timer
    ring = 400
    rx, ry = RX + (RW - ring) // 2, 170
    t_run0, t_run1 = q("m5c", "explain it out loud"), td + 1.2

    def timer(frame, t, op):
        p = clamp01((t - t_run0) / (t_run1 - t_run0))
        col = C["gold"] if t >= td else C["teal"]
        paste(frame, arc_ring(ring, 1 - p, col), rx, ry, op)
        secs = int(round(30 * (1 - p)))
        txt = text_img(f"0:{secs:02d}", 96, 800)
        paste(frame, txt, rx + (ring - txt.width) / 2, ry + (ring - txt.height) / 2 - 6, op)

    els.append(Dyn(timer, tc, fadein=0.4))
    lab = text_img("Explain it out loud", 44, 800)
    els.append(El(lab, RX + (RW - lab.width) / 2, 610, q("m5c", "explain it out loud")))
    who = [("a friend", "to a friend"), ("family", "a family member"), ("your dog", "your dog")]
    pills = [pill(a, 30, 700, fg=C["text"], bg=None, outline=C["teal"]) for a, _ in who]
    total = sum(p_.width for p_ in pills) + 40
    x = RX + (RW - total) / 2
    for p_, (_, sub) in zip(pills, who):
        els.append(El(p_, x, 700, q("m5c", sub), anim="pop", dur=0.35))
        x += p_.width + 20
    st = pill("Stuck? That's what to learn next.", 32, 800, fg=C["navy"], bg=C["gold"])
    els.append(El(st, RX + (RW - st.width) / 2, 800, td + 0.1))
    return els


def exp_intro(sc, q, ctx):
    els = [El(text_img("They didn't aim for perfect.", 76, 700), W / 2, 380, q("e1"), center=True),
           El(text_img("They *experimented.*", 120, 800), W / 2, 500, q("e1", "They experimented"), center=True)]
    return els


def exp_outro(sc, q, ctx):
    els = [El(text_img("Treat AI like an instrument you're *learning.*", 66, 800), W / 2, 250, q("e2", "Treat"),
              center=True)]
    specs = [("Test it.", C["teal"], C["navy"], "Test it"), ("Question it.", C["gold"], C["navy"], "question it"),
             ("Listen for\nits patterns.", C["crimson"], C["white"], "listen for")]
    cw, ch = 480, 240
    x0 = (W - (3 * cw + 2 * 60)) / 2
    for i, (txt, bg, fg, sub) in enumerate(specs):
        c = rrect(cw, ch, 28, fill=rgba(bg))
        t = text_img(txt, 56, 800, color=fg, align="center")
        c.alpha_composite(t, ((cw - t.width) // 2, (ch - t.height) // 2))
        els.append(El(shadowed(c, alpha=0.45), x0 + i * (cw + 60), 460, q("e2", sub), anim="pop", dur=0.4))
    return els


def challenge(sc, q, ctx):
    els = [
        El(pill("YOUR TURN", 28, 800, fg=C["navy"], bg=C["gold"]), LX, 100, max(0.05, q("c1") - 0.3)),
        El(text_img("The Flip Challenge", 96, 800), LX, 150, q("c1") + 0.2),
        El(text_img("Can you make an AI *flip?*", 50, 600, color=C["teal"], accent=C["gold"]), LX, 275,
           q("c1", "can you make")),
    ]

    def step(n, head, h, extra=None):
        c = card(900, h, fill=C["slate"])
        b = circle(64, fill=rgba(C["gold"]))
        num = text_img(str(n), 38, 800, color=C["navy"])
        b.alpha_composite(num, ((64 - num.width) // 2, (64 - num.height) // 2 + 1))
        c.alpha_composite(b, (28, 26))
        c.alpha_composite(text_img(head, 36, 700, max_w=760), (116, 34))
        if extra:
            x = 116
            for e in extra:
                c.alpha_composite(e, (x, 100))
                x += e.width + 14
        return shadowed(c, blur=16, alpha=0.4)

    ex = [pill(s, 24, 700, fg=C["text"], bg=None, outline=C["teal"], padx=16, pady=6)
          for s in ("cats or dogs", "summer or winter", "morning or night study")]
    els.append(El(step(1, "Pick a this-or-that question", 170, ex), LX, 380, q("c2")))
    els.append(El(step(2, "Chat 1: “Why is the first one better?”", 116), LX, 572, q("c3")))
    els.append(El(step(3, "New chat: “Why is the second one better?”", 116), LX, 710,
                  q("c3", "Then open")))
    cx = 1110
    els.append(El(text_img("Did it flip or hold?", 44, 800), cx, 380, q("c4")))
    fl = pill("FLIPPED", 44, 800, fg=C["white"], bg=C["crimson"], padx=34, pady=16)
    hd = pill("HELD", 44, 800, fg=C["navy"], bg=C["teal"], padx=34, pady=16)
    els.append(El(fl, cx, 455, q("c4", "flip to agree"), anim="pop", dur=0.35))
    els.append(El(hd, cx + fl.width + 24, 455, q("c4", "hold its ground"), anim="pop", dur=0.35))
    cm = rrect(690, 250, 22, fill=rgba(C["white"]))
    cm.alpha_composite(text_img("Your comment", 26, 600, color=(100, 116, 139)), (32, 26))
    ImageDraw.Draw(cm).line([(32, 72), (658, 72)], fill=(226, 232, 240), width=2)
    cm.alpha_composite(pill("Comment", 26, 700, fg=C["navy"], bg=C["teal"], padx=20, pady=8), (520, 180))
    t_cm = q("c4", "Comment")
    els.append(El(shadowed(cm, alpha=0.5), cx, 580, t_cm - 0.3))
    typed_txt = text_img("HELD  ·  cats or dogs", 44, 800, color=C["ink"])

    def typing(frame, t, op):
        paste(frame, wipe(typed_txt, (t - t_cm) / 1.6, typed_txt.height), cx + 32, 580 + 96, op)

    els.append(Dyn(typing, t_cm, fadein=0.01))
    banner = rrect(1680, 92, 22, fill=rgba(C["slate"]), outline=rgba(C["crimson"]), ow=3)
    banner.alpha_composite(lock_icon(40, C["pink"]), (34, 24))
    banner.alpha_composite(text_img("Keep it anonymous: no names, schools, or personal details.", 34, 700), (96, 22))
    els.append(El(banner, LX, 918, q("c5")))
    return els


def recap(sc, q, ctx):
    els = [El(text_img("Quick Recap", 88, 800), W / 2, 90, q("r0"), center=True)]
    names = ["Guess the next note", "Play it twice", "Flip the key", "Find the sheet music", "Play it by ear"]
    cols5 = [C["teal"], C["gold"], C["crimson"], C["violet"], (52, 152, 219)]
    x0 = 560
    for i, n in enumerate(names):
        b = note_block(100, 100, cols5[i], r=16)
        num = text_img(str(i + 1), 56, 800, color=C["navy"])
        b.alpha_composite(num, ((100 - num.width) // 2, 12))
        y = 250 + i * 142
        t0 = q(f"r{i + 1}")
        els.append(El(b, x0, y, t0, anim="pop", dur=0.3))
        els.append(El(text_img(n, 62, 800), x0 + 140, y + 8, t0 + 0.05, dx=-30, dy=0))
    return els


def outro(sc, q, ctx):
    D = sc["dur"]
    t2 = q("o2")
    els = [
        El(pill("ONE MORE THING", 28, 800, fg=C["navy"], bg=C["gold"]), W / 2, 220, q("o1"), t2 - 0.3, center=True),
        El(text_img("This narration was generated by *AI.*", 80, 800), W / 2, 320, q("o1", "The voice"), t2 - 0.3,
           center=True),
        El(text_img("Now you know how to question it.", 50, 600, color=C["teal"]), W / 2, 460,
           q("o1", "Now you know"), t2 - 0.3, center=True),
        El(wordmark(150), W / 2, 270, t2, D - 0.8, center=True, fade=0.8),
        El(text_img("Stay curious.", 76, 800), W / 2, 500, t2 + 0.2, D - 0.8, center=True, fade=0.8),
        El(text_img("tomoclub.org", 40, 600, color=C["muted"]), W / 2, 620, t2 + 0.5, D - 0.8, center=True,
           fade=0.8),
    ]
    return els


BUILDERS = {f.__name__: f for f in (hook, title, soundcheck, m1_intro, clipA, m1_body, m2, m3, m4, m5, exp_intro,
                                    clipB, exp_outro, challenge, recap, outro)}
