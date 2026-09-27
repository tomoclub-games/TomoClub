"""YouTube thumbnail, 1280x720 (16:9), under 2 MB.

usage: python thumbnail.py <out.jpg>
"""
import sys

from PIL import Image, ImageDraw

from gfx import C, PITCH, background, note_block, pill, rgba, rrect, shadowed, text_img, wordmark

TW, TH = 1280, 720


def main():
    out = sys.argv[1]
    img = background().resize((TW, TH), Image.LANCZOS).convert("RGBA")
    img.alpha_composite(wordmark(44), (56, 44))

    # Song Maker grid with the unknown next note
    cell, cols, rows, pad = 52, 8, 7, 18
    gw, gh = cols * cell + 2 * pad, rows * cell + 2 * pad
    grid = rrect(gw, gh, 22, fill=rgba(C["white"]))
    d = ImageDraw.Draw(grid)
    for c in range(cols + 1):
        d.line([(pad + c * cell, pad), (pad + c * cell, pad + rows * cell)], fill=(226, 230, 236), width=2)
    for r in range(rows + 1):
        d.line([(pad, pad + r * cell), (pad + cols * cell, pad + r * cell)], fill=(226, 230, 236), width=1)
    for k, r in enumerate([6, 4, 2, 6, 4, 2, 6]):
        grid.alpha_composite(note_block(cell - 8, cell - 8, PITCH[r + 1], r=8), (pad + k * cell + 4, pad + r * cell + 4))
    shade = Image.new("RGBA", (cell, rows * cell), rgba(C["gold"], 90))
    grid.alpha_composite(shade, (pad + 7 * cell, pad))
    q = text_img("?", 120, 800, color=C["gold"])
    sg, p = shadowed(grid, blur=24, alpha=0.6)
    gx, gy = TW - gw - 64, 150
    img.alpha_composite(sg, (gx - p, gy - p))
    img.alpha_composite(q, (gx + pad + 7 * cell + (cell - q.width) // 2, gy + pad + 70))

    img.alpha_composite(text_img("*5 AI MOVES*", 104, 800), (52, 150))
    img.alpha_composite(text_img("Think like\na musician", 76, 800, lh=1.02), (56, 290))
    tag = pill("Try the Flip Challenge", 34, 800, fg=C["navy"], bg=C["teal"], padx=26, pady=14)
    img.alpha_composite(tag, (56, 560))
    img.convert("RGB").save(out, quality=92)
    print("wrote", out)


if __name__ == "__main__":
    main()
