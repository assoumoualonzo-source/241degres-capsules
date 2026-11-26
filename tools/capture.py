#!/usr/bin/env python3
"""Capture d'écran d'une publication (article de média, communiqué officiel, post public) pour un short BUZZ.

Usage :
  python3 tools/capture.py URL episodes/AAAA-MM-JJ-buzz/shots/01.png [--above 200] [--height 560] [--selector CSS]

- Fenêtre de 820 px (rendu x1,6) par défaut, --width 430 pour une vue mobile (x2,5) : capture nette dans la vidéo.
- Ferme au mieux les bandeaux cookies et pop-ups, puis capture par défaut le bloc titre :
  du titre h1 (moins --above px pour garder le logo du média) sur --height px. --selector capture un élément précis.
- Toujours regarder la capture : si une pub ou un pop-up la gâche, ajuster --above/--height ou --selector.
- Les captures restent hors dépôt (episodes/*/shots/ est dans .gitignore).
Réservé aux publications de médias, d'institutions ou de comptes publics : jamais un particulier ni un mineur.
"""
import argparse, os, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

CLOSE = ["Accepter", "Tout accepter", "J'accepte", "Accept", "Accept all", "OK", "Continuer", "Fermer", "Close",
         "Autoriser", "Consentir", "×"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--selector", help="élément à capturer (ex. 'article', 'h1', '.post')")
    ap.add_argument("--height", type=int, default=560, help="hauteur capturée en px CSS si pas de sélecteur")
    ap.add_argument("--width", type=int, default=820,
                    help="largeur de la fenêtre en px CSS (820 = tablette, lisible ; 430 = mobile pour les sites adaptés)")
    ap.add_argument("--above", type=int, default=0,
                    help="marge gardée au-dessus du titre h1 (ex. 200 pour inclure le logo du média)")
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    with sync_playwright() as p:
        b = p.chromium.launch(proxy={"server": proxy} if proxy else None)
        mobile = a.width < 600
        ctx = b.new_context(viewport={"width": a.width, "height": 1400}, device_scale_factor=2.5 if mobile else 1.6,
                            locale="fr-FR", is_mobile=mobile, has_touch=mobile,
                            user_agent=("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/124.0 Mobile Safari/537.36") if mobile else None)
        pg = ctx.new_page()
        pg.goto(a.url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(2500)
        for label in CLOSE:   # bandeaux cookies / pop-ups
            try:
                btn = pg.get_by_role("button", name=label, exact=True)
                if btn.count():
                    btn.first.click(timeout=1500)
                    pg.wait_for_timeout(400)
            except Exception:
                pass
        # masque les éléments flottants restants (pubs collantes, barres de partage)
        pg.add_style_tag(content="[class*='cookie'],[id*='cookie'],[class*='consent'],[id*='consent'],"
                                 "[class*='popup'],[class*='modal'],[class*='sticky'],[class*='newsletter']"
                                 "{display:none!important}")
        pg.wait_for_timeout(500)
        if a.selector:
            el = pg.locator(a.selector).first
            el.scroll_into_view_if_needed(timeout=5000)
            el.screenshot(path=str(out))
        else:
            # par défaut : le bloc titre (logo du média au-dessus du h1, titre, chapô)
            top = 0
            try:
                box = pg.locator("h1").first.bounding_box(timeout=3000)
                if box:
                    top = max(0, box["y"] - a.above)
            except Exception:
                pass
            pg.screenshot(path=str(out), full_page=True,
                          clip={"x": 0, "y": top, "width": a.width, "height": a.height})
        b.close()
    print("OK", out)


if __name__ == "__main__":
    sys.exit(main())
