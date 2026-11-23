#!/usr/bin/env python3
"""Génère les déclinaisons du logo 241°DEGRÉS à partir de la silhouette du Gabon (src/gabon_mask.png)."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"
GREEN, YELLOW, BLUE = (0, 158, 96), (252, 209, 22), (58, 117, 196)
INK, WHITE = (11, 18, 32), (255, 255, 255)


def mont(size, weight):
    f = ImageFont.truetype(str(FONTS / "Montserrat[wght].ttf"), size)
    f.set_variation_by_name(weight)
    return f


def halftone_map(height, color=GREEN, step_ratio=0.032):
    """Carte du Gabon en trame de points : les points rétrécissent vers les bords."""
    png = HERE / "src" / "gabon_mask.png"
    if png.exists():
        m = cv2.imread(str(png), 0)
    else:  # silhouette vectorielle versionnée dans le dépôt
        import json
        j = json.load(open(HERE / "gabon_mask.json"))
        m = np.zeros((j["h"], j["w"]), np.uint8)
        cv2.fillPoly(m, [np.array(j["poly"], np.int32)], 255)
    s = height / m.shape[0]
    m = cv2.resize(m, (int(m.shape[1] * s), height), interpolation=cv2.INTER_AREA)
    dist = cv2.distanceTransform((m > 127).astype(np.uint8), cv2.DIST_L2, 5)
    step = max(6, int(height * step_ratio))
    img = Image.new("RGBA", (m.shape[1] + step, height + step), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(step // 2, height, step):
        for x in range(step // 2, m.shape[1], step):
            if m[y, x] < 128:
                continue
            k = min(1.0, dist[y, x] / (step * 2.2))
            r = step * (0.18 + 0.27 * k)
            d.ellipse((x - r, y - r, x + r, y + r), fill=color)
    return img


def text(d, xy, s, f, fill, anchor="mm", tracking=0):
    if not tracking:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    widths = [d.textlength(c, font=f) for c in s]
    tot = sum(widths) + tracking * (len(s) - 1)
    x = xy[0] - tot / 2
    for c, w in zip(s, widths):
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="lm")
        x += w + tracking


def flag_bar(d, x0, y0, w, h):
    t = w / 3
    for i, c in enumerate((GREEN, YELLOW, BLUE)):
        d.rectangle((x0 + i * t, y0, x0 + (i + 1) * t, y0 + h), fill=c)


def square(size=2048, bg=INK, fg=WHITE, accent=YELLOW, shadow=True):
    """Avatar carré (contenu centré dans le cercle de recadrage TikTok)."""
    img = Image.new("RGBA", (size, size), bg + (255,))
    mp = halftone_map(int(size * 0.62))
    img.alpha_composite(mp, ((size - mp.width) // 2 + int(size * 0.01), int(size * 0.10)))
    d = ImageDraw.Draw(img)
    f = mont(int(size * 0.27), "Black")
    cy = int(size * 0.44)
    # ombre douce sous le chiffre
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((size // 2 + 10, cy + 14), "241°", font=f, fill=(0, 0, 0, 170), anchor="mm")
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size // 120)))
    d.text((size // 2, cy), "241°", font=f, fill=fg, anchor="mm")
    text(d, (size // 2, int(size * 0.80)), "DEGRÉS", mont(int(size * 0.085), "Bold"), accent, tracking=int(size * 0.03))
    bw = int(size * 0.34)
    flag_bar(d, (size - bw) // 2, int(size * 0.865), bw, int(size * 0.014))
    return img


def horizontal(height=400, fg=WHITE, plate=True):
    """Bandeau horizontal pour l'habillage vidéo : icône carte + 241° + DEGRÉS."""
    mp = halftone_map(int(height * 0.86))
    f1, f2 = mont(int(height * 0.50), "Black"), mont(int(height * 0.17), "Bold")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength("241°", font=f1)
    w = int(mp.width + tw + height * 0.55)
    img = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if plate:
        d.rounded_rectangle((0, 0, w - 1, height - 1), radius=height // 5, fill=INK + (235,))
    img.alpha_composite(mp, (int(height * 0.12), int(height * 0.07)))
    tx = int(mp.width + height * 0.22)
    d.text((tx, int(height * 0.40)), "241°", font=f1, fill=fg, anchor="lm")
    gap = int(height * 0.045)
    x = tx + 4
    for c in "DEGRÉS":
        d.text((x, int(height * 0.78)), c, font=f2, fill=YELLOW, anchor="lm")
        x += tmp.textlength(c, font=f2) + gap
    flag_bar(d, tx + 4, int(height * 0.90), int(x - gap - tx - 4), int(height * 0.035))
    return img


if __name__ == "__main__":
    out = HERE
    sq = square()
    sq.convert("RGB").save(out / "logo_241degres_carre.png")
    sq.resize((1024, 1024), Image.LANCZOS).convert("RGB").save(out / "logo_241degres_tiktok_1024.png")
    sql = square(bg=(250, 248, 242), fg=INK, accent=INK, shadow=False)
    sql.convert("RGB").save(out / "logo_241degres_carre_clair.png")
    horizontal(400).save(out / "logo_241degres_bandeau.png")
    horizontal(400, plate=False).save(out / "logo_241degres_bandeau_transparent.png")
    halftone_map(800).save(out / "icone_carte_gabon.png")
    print("ok")
