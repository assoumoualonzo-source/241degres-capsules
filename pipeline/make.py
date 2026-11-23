#!/usr/bin/env python3
"""241degres — génère une capsule TikTok verticale (1080x1920, 30 fps) à partir d'un episode.json.

Usage : python3 pipeline/make.py episodes/AAAA-MM-JJ-info
Sortie : <episode>/out/video.mp4, cover.jpg, post.txt
"""
import asyncio, json, math, os, subprocess, sys, urllib.request, wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
W, H, FPS, SR = 1080, 1920, 30, 44100
GREEN, YELLOW, BLUE, RED = (0, 158, 96), (252, 209, 22), (58, 117, 196), (230, 57, 70)
WHITE, BLACK = (255, 255, 255), (8, 10, 14)
CA = os.environ.get("CCR_CA", "/root/.ccr/ca-bundle.crt")


# ---------- utilitaires ----------
def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
    return f

ANTON = lambda s: font("Anton-Regular.ttf", s)
MONT = lambda s, w="ExtraBold": font("Montserrat[wght].ttf", s, w)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def back_out(t):
    t = max(0.0, min(1.0, t))
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def download(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "241degres/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())


def wrap(draw, text, fnt, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            test = (cur + " " + w).strip()
            if draw.textlength(test, font=fnt) <= maxw:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_layer(text, fnt, fill=WHITE, maxw=900, spacing=1.05, stroke=0, align="left", shadow=True):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = wrap(tmp, text, fnt, maxw)
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * spacing)
    width = int(max(tmp.textlength(l, font=fnt) for l in lines)) + 2 * stroke + 20
    height = lh * len(lines) + 2 * stroke + 20
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        x = 10 + stroke if align == "left" else (width - d.textlength(l, font=fnt)) / 2
        d.text((x, 10 + stroke + i * lh), l, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=BLACK)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh.paste((0, 0, 0, 170), mask=img.split()[3])
        sh = sh.filter(ImageFilter.GaussianBlur(8))
        out = Image.new("RGBA", (width + 8, height + 8), (0, 0, 0, 0))
        out.alpha_composite(sh, (8, 8))
        out.alpha_composite(img, (0, 0))
        return out
    return img


def pill(text, bg, fg=BLACK, size=46):
    f = MONT(size, "Black")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = tmp.textlength(text, font=f)
    asc, desc = f.getmetrics()
    w, h = int(tw + 56), int(asc + desc + 26)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=bg)
    d.text((28, 12), text, font=f, fill=fg)
    return img


def card(title, body, color, w=920):
    ft, fb = MONT(44, "Black"), MONT(48, "Bold")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = wrap(tmp, body, fb, w - 90)
    asc, desc = fb.getmetrics()
    lh = int((asc + desc) * 1.12)
    h = 120 + lh * len(lines) + 30
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=36, fill=(12, 16, 22, 225), outline=color, width=6)
    d.rounded_rectangle((0, 0, w - 1, 90), radius=36, fill=color)
    d.rectangle((0, 55, w - 1, 90), fill=color)
    d.text((45, 18), title, font=ft, fill=WHITE if color != YELLOW else BLACK)
    for i, l in enumerate(lines):
        d.text((45, 115 + i * lh), l, font=fb, fill=WHITE)
    return img


def paste(frame, layer, x, y, alpha=1.0, scale=1.0):
    if alpha <= 0.01:
        return
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BILINEAR)
        x -= (layer.width - layer.width / scale) / 2
        y -= (layer.height - layer.height / scale) / 2
    if alpha < 1:
        a = layer.split()[3].point(lambda v: int(v * alpha))
        layer = layer.copy()
        layer.putalpha(a)
    frame.alpha_composite(layer, (int(x), int(y)))


# ---------- voix ----------
async def _tts(text, voice, rate, mp3, words_json):
    import certifi
    if os.path.exists(CA):
        certifi.where = lambda: CA
    import edge_tts
    com = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"t": ch["offset"] / 1e7, "d": ch["duration"] / 1e7, "w": ch["text"]})
    json.dump(words, open(words_json, "w"), ensure_ascii=False)


# Chaîne « radio » : voix pleine et puissante, sèche et proche.
# 1) nettoyage et porte (coupe les queues de réverbération de la pièce)
# 2) égalisation : corps à 120 Hz, moins de son de boîte à 300 Hz, présence à 3 kHz, air à 10 kHz
# 3) dé-essage, double compression (contrôle puis densité), très légère ambiance, limiteur
RADIO = ("highpass=f=70,afftdn=nr=8:nf=-50,agate=threshold=0.01:ratio=3:attack=2:release=70:range=0.1,"
         "equalizer=f=120:t=q:w=1.0:g=3.5,equalizer=f=320:t=q:w=1.2:g=-3.5,"
         "equalizer=f=3000:t=q:w=1.3:g=3,highshelf=f=10000:g=2.5,deesser=i=0.4,"
         "acompressor=threshold=-24dB:ratio=4:attack=4:release=80:makeup=4,"
         "acompressor=threshold=-12dB:ratio=2:attack=15:release=150:makeup=1.5,"
         "aecho=0.9:0.5:11|19:0.05|0.03,alimiter=limit=0.92:attack=3:release=40")


def tighten(v, words, max_pause=0.22, thr_db=-40):
    """Raccourcit les pauses internes trop longues (débit plus vif) et recale les sous-titres."""
    hop = int(0.01 * SR)
    n = len(v) // hop
    if n == 0:
        return v, words
    rms = np.sqrt(np.mean(v[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    silent = 20 * np.log10(rms) < thr_db
    keep = np.ones(len(v), bool)
    cuts = []
    i = 0
    while i < n:
        if not silent[i]:
            i += 1
            continue
        j = i
        while j < n and silent[j]:
            j += 1
        dur = (j - i) * 0.01
        if i > 0 and j < n and dur > max_pause:
            start = i * 0.01 + max_pause / 2
            rm = dur - max_pause
            keep[int(start * SR):int((start + rm) * SR)] = False
            cuts.append((start, rm))
        i = j
    remap = lambda t: t - sum(r for c, r in cuts if c < t)
    return v[keep], [dict(w, t=remap(w["t"])) for w in words]


def decode(path, radio=False):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)] + (["-af", RADIO] if radio else [])
    raw = subprocess.run(cmd + ["-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


# ---------- musique & sfx (générés, libres de droits) ----------
def music_bed(n):
    t = np.arange(n) / SR
    bpm = 100
    beat = 60 / bpm
    out = np.zeros(n, np.float32)
    # kick
    kl = int(0.35 * SR)
    kt = np.arange(kl) / SR
    kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 9)
    for k in range(int(n / SR / beat) + 1):
        s = int(k * beat * SR)
        e = min(n, s + kl)
        out[s:e] += 0.55 * kick[: e - s]
    # hats
    rng = np.random.default_rng(241)
    hl = int(0.05 * SR)
    hat = rng.standard_normal(hl) * np.exp(-np.arange(hl) / SR * 80)
    hat = np.diff(hat, prepend=0)
    for k in range(int(n / SR / beat) + 1):
        s = int((k + 0.5) * beat * SR)
        e = min(n, s + hl)
        if s < n:
            out[s:e] += 0.12 * hat[: e - s]
    # basse + nappe : La m - Fa - Do - Sol
    roots = [55.0, 43.65, 65.41, 49.0]
    bar = beat * 4
    for i, r in enumerate(roots * (int(n / SR / bar / 4) + 2)):
        s = int(i * bar * SR)
        if s >= n:
            break
        e = min(n, int((i + 1) * bar * SR))
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt * 4) * np.minimum(1, (bar - tt) * 4)
        pad = sum(np.sin(2 * np.pi * r * m * 2 * tt) / (j + 1) for j, m in enumerate([1, 1.5, 2, 2.52]))
        out[s:e] += env * (0.22 * np.sin(2 * np.pi * r * tt) + 0.05 * pad)
    return out / (np.abs(out).max() + 1e-6)


def whoosh():
    n = int(0.45 * SR)
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n).astype(np.float32)
    env = np.sin(np.linspace(0, np.pi, n)) ** 2
    k = 40
    y = np.convolve(x, np.ones(k) / k, mode="same")
    return (y * env * 0.5).astype(np.float32)


# ---------- rendu ----------
def prep_bg(path):
    img = cv2.imread(str(path))
    h, w = img.shape[:2]
    s = max(W * 1.12 / w, H * 1.12 / h)
    img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    y0, x0 = (h - int(H * 1.12)) // 2, (w - int(W * 1.12)) // 2
    img = img[y0:y0 + int(H * 1.12), x0:x0 + int(W * 1.12)]
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    # assombrissement + dégradé haut/bas pour la lisibilité
    yy = np.linspace(0, 1, img.shape[0])[:, None, None]
    shade = 0.30 + 0.22 * np.exp(-((yy - 0.35) ** 2) / 0.05)
    img = img * shade
    return np.clip(img, 0, 255).astype(np.uint8)


def bg_frame(bg, t, direction):
    z = 1.0 + 0.07 * t
    bh, bw = bg.shape[:2]
    cx, cy = bw / 2 + direction * 30 * (t - 0.5), bh / 2
    M = np.float32([[z, 0, W / 2 - z * cx], [0, z, H / 2 - z * cy]])
    return cv2.warpAffine(bg, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def chunks(words, maxc=16):
    out, cur = [], []
    for w in words:
        if cur and (sum(len(x["w"]) + 1 for x in cur) + len(w["w"]) > maxc or cur[-1]["w"][-1:] in ".?!:,"):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def caption_layer(chunk, now):
    f = MONT(68, "Black")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    txt = [w["w"].upper() for w in chunk]
    widths = [tmp.textlength(x, font=f) for x in txt]
    sp = tmp.textlength(" ", font=f)
    tot = sum(widths) + sp * (len(txt) - 1)
    img = Image.new("RGBA", (int(tot) + 40, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 20
    for w, s, wd in zip(chunk, txt, widths):
        active = w["t"] <= now < w["t"] + w["d"] + 0.12
        d.text((x, 18), s, font=f, fill=YELLOW if active else WHITE, stroke_width=7, stroke_fill=BLACK)
        x += wd + sp
    return img


class Scene:
    def __init__(self, sc, idx, ep_dir, words, dur, offset, total):
        self.sc, self.idx, self.words, self.dur = sc, idx, words, dur
        self.offset, self.total = offset, total
        img = ep_dir / "img" / f"{idx:02d}.jpg"
        self.bg = prep_bg(img)
        self.dir = 1 if idx % 2 else -1
        self.chunks = chunks(words)
        k = sc["kind"]
        self.kicker = pill(sc["kicker"], RED if k == "alert" else (GREEN if k in ("civic", "cta") else YELLOW),
                           WHITE if k in ("alert", "civic", "cta") else BLACK)
        size = {"hook": 170, "cta": 170, "civic": 130, "brief": 104}.get(k, 122)
        self.head = text_layer(sc.get("headline", ""), ANTON(size), WHITE, maxw=960, spacing=0.86)
        self.head_lines = [text_layer(l, ANTON(size), WHITE, maxw=960, spacing=0.86) for l in sc.get("headline", "").split("\n")]
        if "stat" in sc:
            ss = 170
            while ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(sc["stat"], font=ANTON(ss)) > 900:
                ss -= 10
            self.stat = text_layer(sc["stat"], ANTON(ss), YELLOW, maxw=980)
            self.stat_lbl = text_layer(sc["stat_label"], MONT(40, "SemiBold"), WHITE, maxw=880)
        if k == "brief":
            self.p = card("LE PROBLÈME", sc["problem"], RED)
            self.c = card("EN CLAIR", sc["clear"], GREEN)
        if k == "rank":
            self.rank = text_layer(str(sc["rank"]), ANTON(280), YELLOW, maxw=900)
        if k == "split":
            cols = {"red": RED, "green": GREEN, "blue": BLUE, "yellow": YELLOW}
            self.c1 = card(sc["left_title"], sc["left"], cols[sc.get("left_color", "green")])
            self.c2 = card(sc["right_title"], sc["right"], cols[sc.get("right_color", "blue")])
        if k == "alert":
            self.bul = [bullet(b, j == len(sc["bullets"]) - 1) for j, b in enumerate(sc["bullets"])]
        if k == "civic":
            self.q = card("TA RÉPONSE EN COMMENTAIRE", sc["question"], YELLOW)
        if k == "cta":
            self.logo = logo_layer(400)
            self.btn = pill("  ABONNE-TOI  ", RED, WHITE, 64)
            self.sub = text_layer(sc.get("sub", ""), MONT(46, "Bold"), YELLOW, maxw=960, align="center")
        self.brand = logo_layer(124)
        self.date = text_layer(EP["date"], MONT(36, "Bold"), WHITE, maxw=500)

    def frame(self, i):
        sc, k = self.sc, self.sc["kind"]
        t = i / FPS
        p = t / self.dur
        fr = Image.fromarray(bg_frame(self.bg, p, self.dir)).convert("RGBA")
        # habillage permanent
        paste(fr, self.brand, 36, 50)
        paste(fr, self.date, W - self.date.width - 30, 95)
        d = ImageDraw.Draw(fr)
        prog = (self.offset + t) / self.total
        d.rectangle((0, 0, W, 14), fill=(255, 255, 255, 60))
        d.rectangle((0, 0, int(W * prog), 14), fill=YELLOW)
        a_in = ease_out(t / 0.35)
        # kicker
        kx = 70 - 300 * (1 - ease_out(t / 0.3))
        top = {"hook": 470, "split": 300, "alert": 330, "cta": 330}.get(k, 330)
        if k != "cta":
            paste(fr, self.kicker, kx, top, a_in)
        if k == "hook":
            s = 1.35 - 0.35 * back_out(max(0, t - 0.1) / 0.35)
            paste(fr, self.head, 60, top + 110, ease_out((t - 0.1) / 0.2), s)
        elif k == "brief":
            paste(fr, self.head, 60, top + 90 + 80 * (1 - ease_out((t - 0.1) / 0.4)), ease_out((t - 0.1) / 0.3))
            y = top + 140 + self.head.height
            tp, tc = self.dur * 0.28, self.dur * 0.58
            paste(fr, self.p, 80, y + 100 * (1 - ease_out((t - tp) / 0.4)), ease_out((t - tp) / 0.3))
            paste(fr, self.c, 80, y + self.p.height + 25 + 100 * (1 - ease_out((t - tc) / 0.4)), ease_out((t - tc) / 0.3))
        elif k == "rank":
            paste(fr, self.rank, 50, top + 60, ease_out(t / 0.2), 1.5 - 0.5 * back_out(t / 0.35))
            y = top + 60 + self.rank.height - 40
            paste(fr, self.head, 60, y + 60 * (1 - ease_out((t - 0.3) / 0.4)), ease_out((t - 0.3) / 0.3))
            if "stat" in sc:
                y += self.head.height
                paste(fr, self.stat, 60, y + 20, ease_out((t - 0.9) / 0.2), 0.6 + 0.4 * back_out((t - 0.9) / 0.4))
                paste(fr, self.stat_lbl, 70, y + 40 + self.stat.height, ease_out((t - 1.2) / 0.3))
        elif k in ("story", "alert"):
            paste(fr, self.head, 60, top + 100 + 80 * (1 - ease_out((t - 0.1) / 0.4)), ease_out((t - 0.1) / 0.3))
            y = top + 110 + self.head.height
            if k == "story":
                ts = 0.9
                sc_ = 0.6 + 0.4 * back_out((t - ts) / 0.4)
                paste(fr, self.stat, 60, y + 40, ease_out((t - ts) / 0.2), sc_)
                paste(fr, self.stat_lbl, 70, y + 60 + self.stat.height, ease_out((t - ts - 0.3) / 0.3))
            else:
                if int(t * 4) % 2 == 0 and t < 2.5:
                    d.rectangle((0, 0, W - 1, H - 1), outline=RED, width=18)
                for j, b in enumerate(self.bul):
                    tj = self.dur * (0.55 + 0.11 * j)
                    paste(fr, b, 70 - 200 * (1 - ease_out((t - tj) / 0.3)), y + 50 + j * 115, ease_out((t - tj) / 0.25))
        elif k == "split":
            paste(fr, self.c1, 80, 430 + 120 * (1 - ease_out((t - 0.2) / 0.4)), ease_out((t - 0.2) / 0.3))
            t2 = self.dur * 0.5
            paste(fr, self.c2, 80, 470 + self.c1.height + 120 * (1 - ease_out((t - t2) / 0.4)), ease_out((t - t2) / 0.3))
        elif k == "civic":
            y = top + 110
            for j, l in enumerate(self.head_lines):
                tj = 0.2 + 0.45 * j
                paste(fr, l, 60, y, ease_out((t - tj) / 0.25), 1.2 - 0.2 * back_out((t - tj) / 0.3))
                y += l.height - 20
            tq = self.dur * 0.55
            paste(fr, self.q, 80, y + 40 + 100 * (1 - ease_out((t - tq) / 0.4)), ease_out((t - tq) / 0.3))
        elif k == "cta":
            paste(fr, self.logo, (W - self.logo.width) / 2, 360, a_in, 0.5 + 0.5 * back_out(t / 0.5))
            paste(fr, self.head, (W - self.head.width) / 2, 940, ease_out((t - 0.3) / 0.3))
            paste(fr, self.sub, (W - self.sub.width) / 2, 1190, ease_out((t - 0.45) / 0.3))
            pulse = 1 + 0.05 * math.sin(t * 7)
            paste(fr, self.btn, (W - self.btn.width) / 2, 1290, ease_out((t - 0.6) / 0.3), pulse)
        # sous-titres mot à mot
        now = t - LEAD
        cur = None
        for c in self.chunks:
            if c[0]["t"] - 0.05 <= now:
                cur = c
        if cur and now < cur[-1]["t"] + cur[-1]["d"] + 0.6 and k != "cta":
            cl = caption_layer(cur, now)
            sc_ = min(1.0, 0.85 + (now - cur[0]["t"]) * 2)
            paste(fr, cl, (W - cl.width) / 2, 1390, 1.0, sc_)
        # flash de transition
        if t < 0.18 and self.idx > 0:
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - t / 0.18))))
            fr.alpha_composite(fl)
        return fr.convert("RGB")


def bullet(text, ok):
    t = text_layer(text, MONT(60, "Black"), WHITE, maxw=820)
    img = Image.new("RGBA", (t.width + 110, max(t.height, 96)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = GREEN if ok else RED
    d.ellipse((4, 8, 84, 88), fill=c)
    if ok:
        d.line([(24, 50), (40, 66), (66, 30)], fill=WHITE, width=10, joint="curve")
    else:
        d.line([(28, 32), (60, 64)], fill=WHITE, width=10)
        d.line([(60, 32), (28, 64)], fill=WHITE, width=10)
    img.alpha_composite(t, (100, (img.height - t.height) // 2))
    return img


def logo_layer(size):
    """Logo officiel (assets/logo) mis à la hauteur demandée."""
    big = size >= 250
    src = ROOT / "assets" / "logo" / ("logo_241degres_carre.png" if big else "logo_241degres_bandeau.png")
    img = Image.open(src).convert("RGBA")
    if big:
        m = Image.new("L", img.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=img.width // 6, fill=255)
        img.putalpha(m)
        h = int(size * 1.4)
    else:
        h = size
    return img.resize((int(img.width * h / img.height), h), Image.LANCZOS)


LEAD, TAIL = 0.15, 0.30
EP = {}


def main(ep_dir):
    global EP
    ep_dir = Path(ep_dir).resolve()
    EP = json.load(open(ep_dir / "episode.json"))
    for sub in ("img", "audio", "scenes", "out"):
        (ep_dir / sub).mkdir(exist_ok=True)
    scenes = EP["scenes"]
    # 1. images + voix
    durs, words_all, voices = [], [], []
    for i, sc in enumerate(scenes):
        download(sc["image"], ep_dir / "img" / f"{i:02d}.jpg")
        mp3, wj = ep_dir / "audio" / f"{i:02d}.mp3", ep_dir / "audio" / f"{i:02d}.json"
        if not mp3.exists() or mp3.stat().st_size < 1000:
            asyncio.run(_tts(sc["voice"], EP.get("voice", "fr-FR-HenriNeural"), EP.get("rate", "+0%"), mp3, wj))
        voices.append(mp3)
        words_all.append(json.load(open(wj)))
    # voix clonée : timbre de l'enregistrement de référence appliqué à la voix de synthèse (timings inchangés)
    ref = EP.get("voice_ref")
    if ref:
        cl = ep_dir / "audio" / "clone"
        if not (cl / f"{len(scenes) - 1:02d}.wav").exists():
            subprocess.run([sys.executable, str(ROOT / "pipeline" / "voice_clone.py"), str(ep_dir / "audio"), str(cl),
                            str(ROOT / ref)], check=True)
        voices = [cl / f"{i:02d}.wav" for i in range(len(scenes))]
    voices = [decode(v, radio=bool(ref)) for v in voices]
    for i, v in enumerate(voices):
        voices[i], words_all[i] = tighten(v, words_all[i])
    for v in voices:
        durs.append(round((LEAD + len(v) / SR + TAIL) * FPS) / FPS)
    total = sum(durs)
    print(f"Durée totale : {total:.1f} s")
    # 2. vidéo, une scène = un fichier
    offset, files = 0.0, []
    for i, sc in enumerate(scenes):
        out = ep_dir / "scenes" / f"{i:02d}.mp4"
        files.append(out)
        S = Scene(sc, i, ep_dir, words_all[i], durs[i], offset, total)
        if PREVIEW:
            for q in (0.15, 0.5, 0.85):
                S.frame(int(q * durs[i] * FPS)).save(ep_dir / "out" / f"prev_{i:02d}_{int(q*100)}.jpg", quality=80)
            offset += durs[i]
            continue
        if i == 0:
            S.frame(int(1.2 * FPS)).save(ep_dir / "out" / "cover.jpg", quality=92)
        tmp = out.with_suffix(".tmp.mp4")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                              "-pix_fmt", "yuv420p", str(tmp)], stdin=subprocess.PIPE)
        for f in range(int(round(durs[i] * FPS))):
            p.stdin.write(S.frame(f).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            sys.exit(f"échec rendu scène {i}")
        tmp.rename(out)
        offset += durs[i]
        print(f"scène {i} ok ({durs[i]:.1f} s)")
    if PREVIEW:
        return
    lst = ep_dir / "scenes" / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    silent = ep_dir / "scenes" / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    # 3. audio : voix + musique ducking + whoosh
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)
    wh = whoosh()
    pos = 0.0
    for i, v in enumerate(voices):
        s = int((pos + LEAD) * SR)
        voice[s:s + len(v)] += v
        if i > 0:
            ws = max(0, int(pos * SR) - len(wh) // 2)
            sfx[ws:ws + len(wh)] += wh[: n - ws]
        pos += durs[i]
    env = np.convolve(np.abs(voice), np.ones(SR // 5) / (SR // 5), mode="same")
    duck = 1 - 0.65 * np.clip(env / (env.max() * 0.25 + 1e-6), 0, 1)
    mix = voice * 1.0 + music_bed(n) * 0.13 * duck + sfx * 0.35
    fade = int(1.2 * SR)
    mix = mix[: int(total * SR)]
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    wav = ep_dir / "audio" / "mix.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    final = ep_dir / "out" / "video.mp4"
    tmp = final.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.rename(final)
    # 4. texte de publication
    post = f"{EP['title']}\n\n{EP.get('hashtags', '')}\n\nSources :\n" + "\n".join(EP.get("sources", [])) + f"\n\n{EP.get('credits', '')}\n"
    (ep_dir / "out" / "post.txt").write_text(post)
    print("OK", final)


PREVIEW = "--preview" in sys.argv

if __name__ == "__main__":
    main(sys.argv[1])
