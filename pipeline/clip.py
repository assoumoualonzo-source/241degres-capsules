#!/usr/bin/env python3
"""241degres — short « extrait vidéo » : discours, entretien ou déclaration d'une personnalité publique.

Stéphane fournit la vidéo (fichier local, ou lien Google Drive partagé « tous les utilisateurs disposant du lien »).
Le short garde l'image et le son d'origine, et ajoute l'habillage 241degres : titre, nom et fonction de la personne,
sous-titres mot à mot, étiquette SOURCE permanente, vignette d'ouverture et carton de fin.

Usage :
  python3 pipeline/clip.py <dossier> --transcribe   # transcrit toute la vidéo -> out/transcript.txt (minutage)
  python3 pipeline/clip.py <dossier> --preview      # images de contrôle + vignette
  python3 pipeline/clip.py <dossier>                # vidéo finale out/video.mp4, cover.jpg, post.txt

<dossier>/clip.json : voir docs/episode-schema.md (section « Extrait vidéo »).
"""
import json, os, re, subprocess, sys, urllib.request, wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make as M  # noqa: E402  (polices, couleurs, pastilles, logo, sous-titres : même charte que les capsules)

W, H, FPS, SR = M.W, M.H, M.FPS, M.SR
END_DUR, COVER_DUR = 2.8, 1.0


# ---------- source ----------
def fetch_video(ep, d):
    """Renvoie le chemin de la vidéo source (télécharge un lien Drive public si besoin)."""
    src = d / ep.get("video", "src.mp4")
    if src.exists() and src.stat().st_size > 10000:
        return src
    url = ep.get("video_url", "")
    m = re.search(r"(?:/d/|id=)([\w-]{20,})", url)
    if not m:
        sys.exit(f"vidéo introuvable : {src} (et pas de video_url Google Drive exploitable)")
    fid = m.group(1)
    dl = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    print("téléchargement Drive", fid)
    req = urllib.request.Request(dl, headers={"User-Agent": "241degres/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(src, "wb") as f:
        ctype = r.headers.get("Content-Type", "")
        f.write(r.read())
    if "text/html" in ctype or src.stat().st_size < 10000:
        src.unlink(missing_ok=True)
        sys.exit("Drive a renvoyé une page et non la vidéo : le fichier doit être partagé "
                 "« Tous les utilisateurs disposant du lien » (lecteur).")
    return src


def probe(src):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:stream_side_data=rotation:format=duration", "-of", "json", str(src)],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    w, h = s["width"], s["height"]
    rot = 0
    for sd in s.get("side_data_list", []) or []:
        rot = int(sd.get("rotation", 0) or 0)
    if abs(rot) in (90, 270):
        w, h = h, w
    return w, h, float(j["format"]["duration"])


def ts(t):
    t = max(0, t)
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}" if t >= 3600 else f"{int(t // 60):02d}:{t % 60:05.2f}"


def parse_t(v):
    """Accepte 75.5, "1:15.5" ou "00:01:15"."""
    if isinstance(v, (int, float)):
        return float(v)
    parts = [float(x) for x in str(v).replace(",", ".").split(":")]
    t = 0.0
    for p in parts:
        t = t * 60 + p
    return t


def whisper(path, model_name=None):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name or os.environ.get("CLIP_MODEL", "small"), device="cpu", compute_type="int8")
    # audio décodé par ffmpeg (16 kHz mono) : évite la dépendance à la version de PyAV
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    segs, _ = model.transcribe(audio, language="fr", word_timestamps=True, vad_filter=True, beam_size=5)
    return list(segs)


# ---------- étape 1 : transcription complète pour choisir l'extrait ----------
def transcribe(d, ep):
    src = fetch_video(ep, d)
    (d / "out").mkdir(exist_ok=True)
    wav = d / "audio_full.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "16000", str(wav)], check=True)
    segs = whisper(wav, os.environ.get("CLIP_MODEL_FULL", "base"))
    lines = [f"[{ts(s.start)} → {ts(s.end)}] {s.text.strip()}" for s in segs]
    (d / "out" / "transcript.txt").write_text("\n".join(lines) + "\n")
    wav.unlink(missing_ok=True)
    print("\n".join(lines))
    print("\n->", d / "out" / "transcript.txt", "(choisir start et end dans clip.json)")


# ---------- habillage ----------
def static_layer(ep, vertical, fg_box):
    """Calque fixe : logo, date, étiquette, titre, nom/fonction, source."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # dégradés haut/bas pour la lisibilité (surtout en vidéo verticale plein cadre)
    for y in range(H):
        a = 0
        if y < 620:
            a = int((200 if vertical else 120) * (1 - y / 620))
        elif y > 1180:
            a = int((215 if vertical else 150) * min(1, (y - 1180) / 400))
        if a:
            d.line([(0, y), (W, y)], fill=(4, 8, 14, a))
    lay.alpha_composite(M.logo_layer(124), (36, 50))
    dt = M.text_layer(ep["date"], M.MONT(36, "Bold"), M.WHITE, maxw=500)
    lay.alpha_composite(dt, (W - dt.width - 30, 95))
    kick = M.pill(ep.get("kicker", "EXTRAIT"), M.RED, M.WHITE)
    lay.alpha_composite(kick, (60, 225))
    head = M.text_layer(ep["headline"], M.ANTON(86), M.WHITE, maxw=960, spacing=0.86)
    lay.alpha_composite(head, (54, 225 + kick.height + 10))
    # plaque nom + fonction, sous la vidéo (ou bas d'écran en vertical)
    y0 = fg_box[3] + 26 if not vertical else 1170
    name = M.text_layer(ep["speaker"].upper(), M.MONT(46, "Black"), M.BLACK, maxw=900, shadow=False)
    role = M.text_layer(ep.get("role", ""), M.MONT(32, "SemiBold"), M.WHITE, maxw=900, shadow=False) if ep.get("role") else None
    pw = max(name.width, role.width if role else 0) + 56
    d.rounded_rectangle((60, y0, 60 + pw, y0 + name.height + 22), radius=16, fill=M.YELLOW)
    lay.alpha_composite(name, (60 + 28, y0 + 8))
    if role:
        d.rounded_rectangle((60, y0 + name.height + 30, 60 + role.width + 56, y0 + name.height + 30 + role.height + 20),
                            radius=14, fill=(14, 22, 36, 235))
        lay.alpha_composite(role, (60 + 28, y0 + name.height + 38))
    src = M.pill("SOURCE : " + ep["source"].upper(), M.WHITE, M.BLACK, 38)
    lay.alpha_composite(src, ((W - src.width) // 2, 1660))
    return lay


def caption_y(vertical, fg_box):
    return 1440 if vertical else min(1520, fg_box[3] + 225)


def end_card(bg_rgb, ep):
    img = Image.fromarray(bg_rgb).convert("RGBA").filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(Image.new("RGBA", (W, H), (4, 10, 20, 170)))
    logo = M.logo_layer(360)
    img.alpha_composite(logo, ((W - logo.width) // 2, 330))
    q = M.text_layer(ep.get("question", "Et toi, tu en penses quoi ?"), M.ANTON(96), M.WHITE, maxw=960,
                     spacing=0.9, align="center")
    img.alpha_composite(q, ((W - q.width) // 2, 900))
    sub = M.text_layer("Dis-le en commentaire !", M.MONT(46, "Bold"), M.YELLOW, maxw=960, align="center")
    img.alpha_composite(sub, ((W - sub.width) // 2, 920 + q.height))
    btn = M.pill("  ABONNE-TOI @241degres  ", M.RED, M.WHITE, 56)
    img.alpha_composite(btn, ((W - btn.width) // 2, 1060 + q.height))
    return img.convert("RGB")


def make_cover(frame_rgb, ep, out):
    img = Image.fromarray(frame_rgb).convert("RGBA")
    shade = Image.new("RGBA", (W, H))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=(5, 12, 24, int(60 + 140 * min(1, abs(y - 900) / 800))))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    for i, c in enumerate((M.GREEN, M.YELLOW, M.BLUE)):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 22), fill=c)
        d.rectangle((i * W / 3, H - 22, (i + 1) * W / 3, H), fill=c)
    logo = M.logo_layer(140)
    plate = Image.new("RGBA", (logo.width + 30, logo.height + 30), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), radius=40, fill=(255, 255, 255, 235))
    plate.alpha_composite(logo, (15, 15))
    img.alpha_composite(plate, ((W - plate.width) // 2, 250))
    y = 250 + plate.height + 24
    row = [M.pill(ep.get("kicker", "EXTRAIT"), M.RED, M.WHITE, 46), M.pill(ep["date"], M.YELLOW, M.BLACK, 46)]
    x = (W - sum(r.width for r in row) - 20) // 2
    for r in row:
        img.alpha_composite(r, (x, y))
        x += r.width + 20
    y += row[0].height + 30
    t = M.text_layer(ep.get("cover_title", ep["headline"]), M.ANTON(140), M.WHITE, maxw=1000, spacing=0.88, align="center")
    img.alpha_composite(t, ((W - t.width) // 2, y))
    y += t.height + 40
    name = M.pill(ep["speaker"].upper(), M.YELLOW, M.BLACK, 50)
    img.alpha_composite(name, ((W - name.width) // 2, max(y, 1300)))
    src = M.pill("SOURCE : " + ep["source"].upper(), M.WHITE, M.BLACK, 38)
    img.alpha_composite(src, ((W - src.width) // 2, max(y, 1300) + name.height + 24))
    hd = M.text_layer("@241degres", M.MONT(50, "Black"), M.WHITE, maxw=900, align="center")
    img.alpha_composite(hd, ((W - hd.width) // 2, 1740))
    img.convert("RGB").save(out, quality=93)


# ---------- étape 2 : rendu ----------
def render(d, ep, preview):
    src = fetch_video(ep, d)
    vw, vh, dur = probe(src)
    t0, t1 = parse_t(ep["start"]), parse_t(ep["end"])
    t1 = min(t1, dur)
    if not 5 <= t1 - t0 <= 90:
        sys.exit(f"extrait de {t1 - t0:.1f} s : il doit durer entre 5 et 90 s (20 à 45 s conseillé)")
    n = int(round((t1 - t0) * FPS))
    for sub in ("work", "out"):
        (d / sub).mkdir(exist_ok=True)
    wk = d / "work"
    # audio de l'extrait + transcription mot à mot (sous-titres)
    wav = wk / "clip.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0}", "-to", f"{t1}", "-i", str(src), "-vn", "-ac", "1",
                    "-ar", str(SR), str(wav)], check=True)
    wj = wk / "words.json"
    if not wj.exists() or json.load(open(wj)).get("span") != [t0, t1]:
        segs = whisper(wav)
        words = [{"w": w.word.strip(), "t": float(w.start), "d": float(w.end - w.start)}
                 for s in segs for w in (s.words or []) if w.word.strip()]
        json.dump({"span": [t0, t1], "words": words}, open(wj, "w"), ensure_ascii=False)
    words = []
    for w in json.load(open(wj))["words"]:   # recolle les élisions coupées par Whisper (« c 'est » -> « c'est »)
        if words and (w["w"][:1] in "'’-" or words[-1]["w"][-1:] in "'’"):
            words[-1]["w"] += w["w"]
            words[-1]["d"] = w["t"] + w["d"] - words[-1]["t"]
        else:
            words.append(dict(w))
    for fx in ep.get("fix", {}).items():   # corrections de transcription : {"mot entendu": "mot juste"}
        for w in words:
            if w["w"].strip(".,!?;:").lower() == fx[0].lower():
                w["w"] = w["w"].lower().replace(fx[0].lower(), fx[1])
    chunks = M.chunks(words, maxc=18)
    (d / "out" / "subtitles.txt").write_text(" ".join(w["w"] for w in words) + "\n")

    vertical = vh > vw * 1.1
    if vertical:
        fw, fh = W, H
        s_ = max(W / vw, H / vh)
        sw, shh = int(vw * s_ / 2) * 2 + 2, int(vh * s_ / 2) * 2 + 2
        vf = f"scale={sw}:{shh},crop={W}:{H}"
        fg_box = (0, 0, W, H)
    else:
        z = float(ep.get("zoom", 1.15))   # recadrage : on gagne en taille sur les visages (côtés rognés)
        fw = W
        fh = int(W * vh / vw * z / 2) * 2
        vf = f"scale={int(W * z / 2) * 2}:{fh},crop={W}:{fh}"
        y = 600
        fg_box = (0, y, W, y + fh)
    lay = static_layer(ep, vertical, fg_box)
    cap_y = caption_y(vertical, fg_box)

    def compose(fr, t, bare=False):
        if vertical:
            base = fr
        else:
            sc = max(W / fw, H / fh)
            bg = cv2.resize(cv2.resize(fr, (fw // 10, fh // 10), interpolation=cv2.INTER_AREA),
                            (int(fw * sc) + 2, int(fh * sc) + 2), interpolation=cv2.INTER_LINEAR)
            yy, xx = (bg.shape[0] - H) // 2, (bg.shape[1] - W) // 2
            bg = cv2.GaussianBlur(bg[yy:yy + H, xx:xx + W], (0, 0), 12)
            base = (bg * 0.45).astype(np.uint8)
            base[fg_box[1]:fg_box[3], :] = fr
        img = Image.fromarray(base).convert("RGBA")
        if bare:   # image nue (fond de la vignette et du carton de fin)
            return img.convert("RGB")
        img.alpha_composite(lay)
        dr = ImageDraw.Draw(img)
        dr.rectangle((0, 0, W, 14), fill=(255, 255, 255, 60))
        dr.rectangle((0, 0, int(W * t / (t1 - t0)), 14), fill=M.YELLOW)
        cur = None
        for c in chunks:
            if c[0]["t"] - 0.05 <= t:
                cur = c
        if cur and t < cur[-1]["t"] + cur[-1]["d"] + 0.6:
            cl = M.caption_layer(cur, t)
            if cl.width > W - 40:
                cl = cl.resize((W - 40, int(cl.height * (W - 40) / cl.width)), Image.LANCZOS)
            sc_ = min(1.0, 0.85 + (t - cur[0]["t"]) * 2)
            M.paste(img, cl, (W - cl.width) / 2, cap_y, 1.0, sc_)
        return img.convert("RGB")

    def frames():
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0}", "-to", f"{t1}", "-i", str(src), "-vf",
                              f"{vf},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        size = fw * fh * 3
        i = 0
        while True:
            buf = p.stdout.read(size)
            if len(buf) < size:
                break
            yield i, np.frombuffer(buf, np.uint8).reshape(fh, fw, 3)
            i += 1
        p.wait()

    if preview:
        targets = {int(n * q) for q in (0.1, 0.5, 0.9)}
        cover_i = int(n * float(ep.get("cover_at", 0.35)))
        for i, fr in frames():
            if i in targets:
                compose(fr, i / FPS).save(d / "out" / f"prev_clip_{int(100 * i / n):02d}.jpg", quality=80)
            if i == cover_i:
                make_cover(np.array(compose(fr, 0, True)), ep, d / "out" / "cover.jpg")
                end_card(np.array(compose(fr, 0, True)), ep).save(d / "out" / "prev_end.jpg", quality=80)
        print("aperçu ->", d / "out")
        return

    # rendu de l'extrait habillé
    body = wk / "body.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                            "-pix_fmt", "yuv420p", str(body)], stdin=subprocess.PIPE)
    cover_i, last, cover_fr = int(n * float(ep.get("cover_at", 0.35))), None, None
    for i, fr in frames():
        img = compose(fr, i / FPS)
        enc.stdin.write(img.tobytes())
        if i == cover_i:
            cover_fr = np.array(compose(fr, 0, True))
        last = fr
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("échec du rendu de l'extrait")
    make_cover(cover_fr if cover_fr is not None else np.array(compose(last, 0, True)), ep, d / "out" / "cover.jpg")
    endimg = wk / "end.jpg"
    end_card(np.array(compose(last, 0, True)), ep).save(endimg, quality=92)
    parts = []
    for name, img, du in (("intro", d / "out" / "cover.jpg", COVER_DUR), ("end", endimg, END_DUR)):
        out = wk / f"{name}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(du), "-i", str(img),
                        "-vf", f"scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                        "-r", str(FPS), str(out)], check=True)
        parts.append(out)
    lst = wk / "list.txt"
    lst.write_text(f"file '{parts[0].name}'\nfile '{body.name}'\nfile '{parts[1].name}'\n")
    silent = wk / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)], check=True)
    # audio : silence (vignette) + son d'origine + carton de fin avec whoosh
    with wave.open(str(wav)) as w_:
        a = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype(np.float32) / 32768
    a = a[: n * SR // FPS]
    fade = int(0.25 * SR)
    a[-fade:] *= np.linspace(1, 0, fade)
    total = COVER_DUR + n / FPS + END_DUR
    mix = np.zeros(int(total * SR) + SR, np.float32)
    s = int(COVER_DUR * SR)
    mix[s:s + len(a)] += a
    wh = M.whoosh()
    for pos in (COVER_DUR, COVER_DUR + n / FPS):
        ws = max(0, int(pos * SR) - len(wh) // 2)
        mix[ws:ws + len(wh)] += wh * 0.35
    mix = mix[: int(total * SR)]
    mix = mix / max(1.0, np.abs(mix).max() / 0.95)
    mixw = wk / "mix.wav"
    with wave.open(str(mixw), "wb") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
        w_.writeframes((mix * 32767).astype(np.int16).tobytes())
    final = d / "out" / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(mixw), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    post = (f"{ep['title']}\n\n{ep.get('hashtags', '')}\n\n"
            f"Extrait : {ep['speaker']}{', ' + ep['role'] if ep.get('role') else ''} · {ep['source']}\n"
            f"Vidéo d'origine : {ep.get('source_url', '')}\n"
            + ("\n".join(ep.get("sources", [])) + "\n" if ep.get("sources") else "")
            + f"\n{ep.get('credits', '')}\n")
    (d / "out" / "post.txt").write_text(post)
    print(f"OK {final} ({total:.1f} s)")


def nbsp(t):
    """Colle ? ! : ; » au mot précédent et « au suivant (typographie française, pas de « ? » seul en fin de ligne)."""
    return re.sub(r" ([?!:;»])", "\u00a0\\1", t).replace("« ", "«\u00a0")


def main():
    d = Path(sys.argv[1]).resolve()
    ep = json.load(open(d / "clip.json"))
    for k in ("headline", "cover_title", "question"):
        if ep.get(k):
            ep[k] = nbsp(ep[k])
    M.EP = ep
    if "--transcribe" in sys.argv:
        transcribe(d, ep)
    else:
        render(d, ep, "--preview" in sys.argv)


if __name__ == "__main__":
    main()
