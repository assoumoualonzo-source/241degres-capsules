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
# Rendu 4K : la mise en page reste en coordonnées 1080x1920 ; les photos de fond sont traitées en 2160x3840
# et l'habillage est agrandi (Lanczos) puis composé dessus. RENDER_SCALE=1 pour un rendu 1080p rapide.
S = int(os.environ.get("RENDER_SCALE", "2"))
RW, RH = W * S, H * S
GREEN, YELLOW, BLUE, RED = (0, 158, 96), (252, 209, 22), (58, 117, 196), (230, 57, 70)
WHITE, BLACK = (255, 255, 255), (8, 10, 14)
INK_DARK = (14, 22, 36)
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


def download(url, dest, base=None):
    if dest.exists() and dest.stat().st_size > 1000:
        return
    if not url.startswith("http"):   # photo locale (ex. photo d'article téléchargée dans shots/)
        Image.open(Path(base or ".") / url).convert("RGB").save(dest, quality=95)
        return
    if "images.unsplash.com" in url:   # 4K : on demande une largeur suffisante
        import re
        url = re.sub(r"([?&])w=\d+", r"\1w=2400", url)
        url = re.sub(r"([?&])q=\d+", r"\1q=85", url)
    req = urllib.request.Request(url, headers={"User-Agent": "241degres/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())


def wrap(draw, text, fnt, maxw):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):   # espaces insécables gardés (« ? » collé au mot)
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


def cue_pauses(v, words, extra=0.35, thr_db=-40):
    """Ajoute une respiration (~0,5 s au total) après « Pourquoi ça compte ? » et « Concrètement, »."""
    hop = int(0.01 * SR)
    norm = lambda s: s.lower().strip(" ?,.:;!…")
    cues = []
    for k, w in enumerate(words):
        if (norm(w["w"]) == "compte" and k > 0 and norm(words[k - 1]["w"]) == "ça") or norm(w["w"]) == "concrètement":
            end = w["t"] + w["d"]
            # point d'insertion : premier passage silencieux juste après le mot (on ne coupe pas sa fin)
            s = int(end * SR)
            for j in range(s, min(len(v) - hop, s + int(0.35 * SR)), hop):
                if 20 * np.log10(np.sqrt(np.mean(v[j:j + hop] ** 2)) + 1e-12) < thr_db:
                    s = j
                    break
            cues.append((s / SR, s))
    if not cues:
        return v, words
    parts, last = [], 0
    for _, s in cues:
        parts += [v[last:s], np.zeros(int(extra * SR), v.dtype)]
        last = s
    parts.append(v[last:])
    shift = lambda t: t + extra * sum(1 for c, _ in cues if c <= t)
    return np.concatenate(parts), [dict(w, t=shift(w["t"])) for w in words]


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


def birds_bed(n, seed=241):
    """Ambiance forêt tropicale générée (libre de droits) : souffle d'air très doux + chants d'oiseaux épars.
    Remplace la musique : la piste musicale est ajoutée sur TikTok."""
    rng = np.random.default_rng(seed)
    out = np.zeros(n, np.float32)
    # souffle de forêt : bruit brun très bas, filtré
    air = np.cumsum(rng.standard_normal(n)).astype(np.float32)
    air -= np.convolve(air, np.ones(4410) / 4410, mode="same")
    out += 0.04 * air / (np.abs(air).max() + 1e-6)

    def tone(f0, f1, dur, vib=0.0, harm=0.15):
        k = int(dur * SR)
        tt = np.arange(k) / SR
        f = np.linspace(f0, f1, k) * (1 + vib * np.sin(2 * np.pi * 28 * tt))
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.sin(np.pi * np.minimum(1, tt / dur)) ** 1.5
        return (np.sin(ph) + harm * np.sin(2 * ph)) * env

    def whistle():   # sifflement qui glisse
        f = rng.uniform(1800, 3400)
        return tone(f, f * rng.uniform(0.7, 1.4), rng.uniform(0.18, 0.45), vib=0.01)

    def trill():     # trille rapide
        f, k = rng.uniform(3000, 5000), rng.integers(6, 14)
        gap = rng.uniform(0.045, 0.07)
        notes = [np.concatenate([tone(f * rng.uniform(0.95, 1.05), f * 1.1, 0.035), np.zeros(int(gap * SR))])
                 for _ in range(k)]
        x = np.concatenate(notes)
        return x * np.linspace(1, 0.6, len(x))

    def dove():      # « hou-hou » grave de tourterelle
        f = rng.uniform(480, 620)
        a = tone(f, f * 0.92, 0.32, harm=0.05)
        return np.concatenate([a, np.zeros(int(0.12 * SR)), tone(f * 1.06, f * 0.9, 0.45, harm=0.05)]) * 0.7

    def chip():      # petits cris secs
        f = rng.uniform(4000, 6500)
        return np.concatenate([np.concatenate([tone(f, f * 0.8, 0.025), np.zeros(int(rng.uniform(0.08, 0.2) * SR))])
                               for _ in range(rng.integers(2, 5))])

    kinds = [whistle, whistle, trill, dove, chip]
    t = rng.uniform(0.2, 1.0)
    while t < n / SR:
        call = kinds[rng.integers(len(kinds))]()
        dist = rng.uniform(0.25, 1.0)                     # oiseau proche ou lointain
        if dist < 0.6:                                    # lointain : plus doux et plus sourd
            call = np.convolve(call, np.ones(6) / 6, mode="same")
        reps = rng.integers(1, 3)
        for r in range(reps):
            s = int((t + r * (len(call) / SR + rng.uniform(0.15, 0.4))) * SR)
            e = min(n, s + len(call))
            if s < n:
                out[s:e] += 0.5 * dist * call[: e - s]
        t += rng.uniform(0.6, 2.2)
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
    s = max(RW * 1.12 / w, RH * 1.12 / h)
    img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)
    h, w = img.shape[:2]
    y0, x0 = (h - int(RH * 1.12)) // 2, (w - int(RW * 1.12)) // 2
    img = img[y0:y0 + int(RH * 1.12), x0:x0 + int(RW * 1.12)]
    img = brighten(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).astype(np.float32)
    # voile léger, plus marqué seulement dans la zone des titres (l'image reste lumineuse)
    yy = np.linspace(0, 1, img.shape[0])[:, None, None]
    shade = 0.92 - 0.26 * np.exp(-((yy - 0.40) ** 2) / 0.06)
    img = img * shade
    return np.clip(img, 0, 255).astype(np.uint8)


def brighten(rgb):
    """Photo plus lumineuse et plus vive : gamma 0,85, saturation +15 %, netteté légère."""
    lut = np.array([((i / 255) ** 0.85) * 255 for i in range(256)], np.uint8)
    rgb = cv2.LUT(rgb, lut)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.15, 0, 255)
    rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    blur = cv2.GaussianBlur(rgb, (0, 0), 2.0)
    return cv2.addWeighted(rgb, 1.25, blur, -0.25, 0)


def compose(base, overlay):
    """Compose l'habillage (RGBA 1080x1920) agrandi en 4K sur la photo de fond (RGB RWxRH)."""
    ov = np.asarray(overlay, dtype=np.float32)
    a = ov[..., 3:4] / 255.0
    prem = ov[..., :3] * a
    if S != 1:
        prem = cv2.resize(prem, (RW, RH), interpolation=cv2.INTER_LANCZOS4)
        a = np.clip(cv2.resize(a[..., 0], (RW, RH), interpolation=cv2.INTER_LANCZOS4), 0, 1)[..., None]
    out = base.astype(np.float32) * (1 - a) + prem
    return np.clip(out, 0, 255).astype(np.uint8)


def cover_base(path):
    """Photo de vignette recadrée en RWxRH, éclaircie."""
    src = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)
    h0, w0 = src.shape[:2]
    sc_ = max(RW / w0, RH / h0)
    src = cv2.resize(src, (int(w0 * sc_) + 1, int(h0 * sc_) + 1), interpolation=cv2.INTER_AREA if sc_ < 1 else cv2.INTER_LANCZOS4)
    y0, x0 = (src.shape[0] - RH) // 2, (src.shape[1] - RW) // 2
    return brighten(np.ascontiguousarray(src[y0:y0 + RH, x0:x0 + RW]))


def bg_frame(bg, t, direction):
    z = 1.0 + 0.07 * t
    bh, bw = bg.shape[:2]
    cx, cy = bw / 2 + direction * 30 * S * (t - 0.5), bh / 2
    M = np.float32([[z, 0, RW / 2 - z * cx], [0, z, RH / 2 - z * cy]])
    return cv2.warpAffine(bg, M, (RW, RH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


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
        size = {"hook": 170, "cta": 170, "civic": 130, "brief": 104, "screen": 100}.get(k, 122)
        self.head = text_layer(sc.get("headline", ""), ANTON(size), WHITE, maxw=960, spacing=0.86)
        self.head_lines = [text_layer(l, ANTON(size), WHITE, maxw=960, spacing=0.86) for l in sc.get("headline", "").split("\n")]
        if "stat" in sc:
            ss = 170
            while ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(sc["stat"], font=ANTON(ss)) > 900:
                ss -= 10
            self.stat = text_layer(sc["stat"], ANTON(ss), YELLOW, maxw=980)
            self.stat_lbl = text_layer(sc["stat_label"], MONT(40, "SemiBold"), WHITE, maxw=880)
        if k == "brief":
            self.p = card("POURQUOI ÇA COMPTE", sc["problem"], RED)
            self.c = card("CONCRÈTEMENT", sc["clear"], GREEN)
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
        if k == "screen":
            self.shot = shot_layer(ep_dir / sc["shot"], 940, 430)   # la source reste au-dessus des sous-titres (y 1390)
            self.src = pill("SOURCE : " + sc["source"].upper(), WHITE, BLACK, 40)
        if k == "cta":
            self.logo = logo_layer(400)
            self.btn = pill("  ABONNE-TOI  ", RED, WHITE, 64)
            self.sub = text_layer(sc.get("sub", ""), MONT(46, "Bold"), YELLOW, maxw=960, align="center")
        self.brand = logo_layer(124)
        self.date = text_layer(EP["date"], MONT(36, "Bold"), WHITE, maxw=500)
        # crédit photo à l'écran (photos d'articles : « PHOTO : MÉDIA »)
        self.credit = text_layer(sc["credit"], MONT(30, "Bold"), WHITE, maxw=900) if sc.get("credit") else None

    def frame(self, i):
        sc, k = self.sc, self.sc["kind"]
        t = i / FPS
        p = t / self.dur
        fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # habillage en 1080x1920, composé en 4K à la fin
        if self.credit is not None:
            paste(fr, self.credit, 36, H - 130)
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
        elif k == "screen":
            paste(fr, self.head, 60, top + 90 + 80 * (1 - ease_out((t - 0.1) / 0.4)), ease_out((t - 0.1) / 0.3))
            y = top + 130 + self.head.height
            ts = 0.35
            z = 0.92 + 0.08 * back_out((t - ts) / 0.45) + 0.02 * p   # pop puis léger zoom continu
            paste(fr, self.shot, (W - self.shot.width) / 2, y, ease_out((t - ts) / 0.3), z)
            paste(fr, self.src, (W - self.src.width) / 2, y + self.shot.height + 30, ease_out((t - ts - 0.4) / 0.3))
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
        return Image.fromarray(compose(bg_frame(self.bg, p, self.dir), fr))


def shot_layer(path, maxw, maxh):
    """Capture d'écran dans un cadre blanc arrondi avec ombre (scènes screen et vignette BUZZ)."""
    im = Image.open(path).convert("RGB")
    s_ = min(maxw / im.width, maxh / im.height)
    im = im.resize((int(im.width * s_), int(im.height * s_)), Image.LANCZOS).convert("RGBA")
    pad, r = 14, 26
    frame = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=r, fill=WHITE)
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r - 8, fill=255)
    im.putalpha(m)
    frame.alpha_composite(im, (pad, pad))
    out = Image.new("RGBA", (frame.width + 60, frame.height + 60), (0, 0, 0, 0))
    out.paste((0, 0, 0, 150), (30, 40), frame.split()[3])
    out = out.filter(ImageFilter.GaussianBlur(14))
    out.alpha_composite(frame, (30, 30))
    return out


def shot_background(shot, dest):
    """Fond flou tiré de la capture quand la scène screen n'a pas d'image Unsplash."""
    im = Image.open(shot).convert("RGB")
    s_ = max(W / im.width, H / im.height) * 1.2
    im = im.resize((int(im.width * s_) + 1, int(im.height * s_) + 1), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im.crop((x0, y0, x0 + W, y0 + H)).filter(ImageFilter.GaussianBlur(28)).save(dest, quality=90)


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


JOURS = ["LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE"]


def fit_font(text, maxw, start, mk):
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    size = start
    while size > 20 and tmp.textlength(text, font=mk(size)) > maxw:
        size -= 2
    return mk(size)


def make_cover(ep_dir, scenes):
    """Vignette TikTok 1080x1920, lumineuse : grand logo, date, titre, 5 infos illustrées sur cartes claires.
    Le contenu utile tient dans la zone centrale 3:4 (y 240-1680) visible dans la grille du profil."""
    import datetime
    base = cover_base(ep_dir / "img" / "01.jpg")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # habillage 1080x1920, composé en 4K sur la photo
    # voile léger : l'image reste lumineuse, juste assez assombrie sous le titre
    shade = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a_ = int(10 + 75 * min(1, max(0, y - 300) / 500))
        sd.line([(0, y), (W, y)], fill=(5, 20, 35, a_))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    for i, c in enumerate((GREEN, YELLOW, BLUE)):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 22), fill=c)
        d.rectangle((i * W / 3, H - 22, (i + 1) * W / 3, H), fill=c)
    # grand logo centré, sur une pastille claire pour ressortir
    logo = logo_layer(200)
    plate = Image.new("RGBA", (logo.width + 40, logo.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), radius=56, fill=(255, 255, 255, 235))
    plate.alpha_composite(logo, (20, 20))
    sh = Image.new("RGBA", (plate.width + 60, plate.height + 60), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), (30, 40), plate.split()[3])
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), ((W - plate.width) // 2 - 30, 250 - 30))
    img.alpha_composite(plate, ((W - plate.width) // 2, 250))
    try:
        dt = datetime.date.fromisoformat(ep_dir.name[:10])
        mois = ["JANV.", "FÉVR.", "MARS", "AVRIL", "MAI", "JUIN", "JUIL.", "AOÛT", "SEPT.", "OCT.", "NOV.", "DÉC."]
        date_txt = f"{JOURS[dt.weekday()]} {dt.day} {mois[dt.month - 1]} {dt.year}"
    except ValueError:
        date_txt = EP["date"]
    y = 250 + plate.height + 30
    dp = pill(date_txt, YELLOW, BLACK, 46)
    img.alpha_composite(dp, ((W - dp.width) // 2, y))
    y += dp.height + 18
    t = text_layer(EP.get("cover_title", "LES INFOS DU JOUR"), ANTON(124), WHITE, maxw=1040, spacing=0.86, align="center")
    img.alpha_composite(t, ((W - t.width) // 2, y))
    y += t.height + 10
    briefs = [s_ for s_ in scenes if s_["kind"] in ("brief", "story", "alert")][:5]
    ranks = sorted([s_ for s_ in scenes if s_["kind"] == "rank"], key=lambda s_: int(s_["rank"]))
    if ranks and not briefs:
        briefs = ranks[:5]
    row_h, card_h = 168, 150
    colors = [RED, GREEN, BLUE, YELLOW, GREEN]
    for n, sc in enumerate(briefs):
        idx = scenes.index(sc)
        th = Image.open(ep_dir / "img" / f"{idx:02d}.jpg").convert("RGB")
        side = min(th.size)
        th = th.crop(((th.width - side) // 2, (th.height - side) // 2, (th.width + side) // 2, (th.height + side) // 2))
        th = th.resize((card_h - 16, card_h - 16), Image.LANCZOS).convert("RGBA")
        m = Image.new("L", th.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, th.width - 1, th.height - 1), radius=22, fill=255)
        th.putalpha(m)
        ry = y + n * row_h
        d.rounded_rectangle((50, ry, W - 50, ry + card_h), radius=30, fill=(255, 255, 255, 240))
        d.rounded_rectangle((50, ry, 64, ry + card_h), radius=6, fill=colors[n])
        img.alpha_composite(th, (74, ry + 8))
        nb = pill(str(sc.get("rank", n + 1)), colors[n], BLACK if colors[n] == YELLOW else WHITE, 38)
        img.alpha_composite(nb, (40, ry - 14))
        label = sc.get("cover", sc.get("headline", "").replace("\n", " "))
        kick = sc.get("kicker", "").split("·")[-1].strip()
        tx = 74 + th.width + 22
        d.text((tx, ry + 18), kick, font=MONT(30, "Black"), fill=(0, 120, 72))
        maxw = W - 50 - tx - 25
        f = fit_font(label, maxw, 58, ANTON)
        d.text((tx, ry + 58), label, font=f, fill=INK_DARK)
    hd = text_layer("@241degres", MONT(50, "Black"), WHITE, maxw=900, align="center")
    img.alpha_composite(hd, ((W - hd.width) // 2, y + 5 * row_h + 5))
    Image.fromarray(compose(base, img)).save(ep_dir / "out" / "cover.jpg", quality=93)


def make_cover_buzz(ep_dir, scenes):
    """Vignette d'un short à sujet unique (BUZZ, CULTURE…) : logo, date, pastille, gros titre, capture ou photo créditée.
    La pastille vient de `cover_pill` (défaut « ÇA BUZZE ») ; le fond, de `cover_image_scene` (index) sinon de la scène screen."""
    import datetime
    scr = next((s_ for s_ in scenes if s_["kind"] == "screen"), None)
    bg_idx = EP.get("cover_image_scene", scenes.index(scr) if scr and scr.get("image") else 0)
    base = cover_base(ep_dir / "img" / f"{bg_idx:02d}.jpg")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(Image.new("RGBA", (W, H), (5, 12, 24, 70)))
    d = ImageDraw.Draw(img)
    for i, c in enumerate((GREEN, YELLOW, BLUE)):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 22), fill=c)
        d.rectangle((i * W / 3, H - 22, (i + 1) * W / 3, H), fill=c)
    logo = logo_layer(150)
    plate = Image.new("RGBA", (logo.width + 32, logo.height + 32), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), radius=44, fill=(255, 255, 255, 235))
    plate.alpha_composite(logo, (16, 16))
    img.alpha_composite(plate, ((W - plate.width) // 2, 250))
    y = 250 + plate.height + 26
    try:
        dt = datetime.date.fromisoformat(ep_dir.name[:10])
        mois = ["JANV.", "FÉVR.", "MARS", "AVRIL", "MAI", "JUIN", "JUIL.", "AOÛT", "SEPT.", "OCT.", "NOV.", "DÉC."]
        date_txt = f"{JOURS[dt.weekday()]} {dt.day} {mois[dt.month - 1]} {dt.year}"
    except ValueError:
        date_txt = EP["date"]
    pc = {"red": RED, "green": GREEN, "blue": BLUE}.get(EP.get("cover_pill_color", "red"), RED)
    row = [pill(EP.get("cover_pill", "ÇA BUZZE"), pc, WHITE, 46), pill(date_txt, YELLOW, BLACK, 46)]
    tw = sum(r.width for r in row) + 20
    x = (W - tw) // 2
    for r in row:
        img.alpha_composite(r, (x, y))
        x += r.width + 20
    y += row[0].height + 24
    t = text_layer(EP.get("cover_title", "ÇA BUZZE"), ANTON(150), WHITE, maxw=1000, spacing=0.86, align="center")
    img.alpha_composite(t, ((W - t.width) // 2, y))
    y += t.height + 30
    if scr:
        sh = shot_layer(ep_dir / scr["shot"], 900, min(560, 1560 - y)).rotate(-2, resample=Image.BICUBIC, expand=True)
        img.alpha_composite(sh, ((W - sh.width) // 2, y))
        y += sh.height + 6
        sp = pill("SOURCE : " + scr["source"].upper(), WHITE, BLACK, 38)
        img.alpha_composite(sp, ((W - sp.width) // 2, min(y, 1620)))
    hd = text_layer("@241degres", MONT(50, "Black"), WHITE, maxw=900, align="center")
    img.alpha_composite(hd, ((W - hd.width) // 2, 1720))
    Image.fromarray(compose(base, img)).save(ep_dir / "out" / "cover.jpg", quality=93)


LEAD, TAIL = 0.15, 0.30
COVER_DUR = 1.0
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
        if sc.get("image"):
            download(sc["image"], ep_dir / "img" / f"{i:02d}.jpg", ep_dir)
        else:   # scène screen sans photo : fond flou tiré de la capture
            shot_background(ep_dir / sc["shot"], ep_dir / "img" / f"{i:02d}.jpg")
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
    single = EP.get("type") == "buzz" or EP.get("cover_style") == "short"
    (make_cover_buzz if single else make_cover)(ep_dir, scenes)
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
        tmp = out.with_suffix(".tmp.mp4")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}",
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
    # vignette en ouverture (1 s, léger zoom avant) : c'est elle que TikTok montre en premier
    intro = ep_dir / "scenes" / "intro.mp4"
    tmp = intro.with_suffix(".tmp.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(ep_dir / "out" / "cover.jpg"),
                    "-vf", f"format=yuv420p,loop=-1:1,trim=duration={COVER_DUR},"
                           f"scale=iw*1.04:-1,zoompan=z='min(1+0.04*on/{int(COVER_DUR * FPS)},1.04)':d=1:"
                           f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={RW}x{RH}:fps={FPS},format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    str(tmp)], check=True)
    tmp.rename(intro)
    lst = ep_dir / "scenes" / "list.txt"
    lst.write_text(f"file '{intro.name}'\n" + "".join(f"file '{f.name}'\n" for f in files))
    silent = ep_dir / "scenes" / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    # 3. audio : voix + ambiance oiseaux très légère + whoosh (la musique est ajoutée sur TikTok)
    total += COVER_DUR
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)
    wh = whoosh()
    pos = COVER_DUR
    for i, v in enumerate(voices):
        s = int((pos + LEAD) * SR)
        voice[s:s + len(v)] += v
        if True:
            ws = max(0, int(pos * SR) - len(wh) // 2)
            sfx[ws:ws + len(wh)] += wh[: n - ws]
        pos += durs[i]
    env = np.convolve(np.abs(voice), np.ones(SR // 5) / (SR // 5), mode="same")
    duck = 1 - 0.65 * np.clip(env / (env.max() * 0.25 + 1e-6), 0, 1)
    mix = voice * 1.0 + birds_bed(n) * 0.04 + sfx * 0.35
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
