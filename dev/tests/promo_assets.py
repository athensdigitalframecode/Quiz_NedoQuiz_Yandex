"""Материалы для раздела Promo Materials GamePush (размеры из панели) в dist/promo_gp/.
Логотип и цвета берутся из игры (icon-512.png, шрифты fonts/). Сначала нужны скриншоты: python dev/tests/promo_shots.py.
Запуск: python dev/tests/promo_assets.py"""
from harness import Run, ROOT

SHOTS = ROOT / "dist" / "promo"
OUT = ROOT / "dist" / "promo_gp"; OUT.mkdir(parents=True, exist_ok=True)
TMP = ROOT / "dist" / "promo_tmp.html"
BG = "radial-gradient(120% 90% at 20% 10%,#27386f 0%,#121b43 45%,#070b1f 100%)"

CSS = """<link rel="stylesheet" href="/fonts/fonts.css"><style>
*{box-sizing:border-box;margin:0}html,body{width:100%;height:100%;overflow:hidden}
body{background:__BG__;position:relative;font-family:Inter,sans-serif;color:#fff}
.t{font-family:'Playfair Display',serif;font-weight:700;line-height:1.02;text-align:center}
.t i{color:#c9a8ff;font-weight:400}
.s{color:#aab4d8;text-align:center}
.c{position:absolute;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:var(--g)}
.ph{height:100%;border-radius:36px;box-shadow:0 20px 60px #000a;border:3px solid #ffffff22}
</style>""".replace("__BG__", BG)

def page(w, h, inner): return f"<!doctype html><meta charset=utf-8>{CSS}<body style='width:{w}px;height:{h}px'>{inner}</body>"
def logo(px, full=False):
    # full: квадрат на всю площадь без скруглений (иконка); иначе края логотипа плавно растворяются в фоне обложки
    m = "" if full else "mix-blend-mode:lighten;-webkit-mask-image:radial-gradient(closest-side,#000 62%,transparent 100%);mask-image:radial-gradient(closest-side,#000 62%,transparent 100%);"
    return f"<img src='/icon-512.png' style='width:{px}px;height:{px}px;object-fit:cover;{m}'>"
def title(px): return f"<div class=t style='font-size:{px}px'>Квиз <i>или</i><br>Недоквиз</div>"
def center(inner, gap=0): return f"<div class=c style='inset:0;--g:{gap}px'>{inner}</div>"

def album(a, b):
    imgs = "".join(f"<img class=ph src='/dist/promo/{n}' style='height:640px'>" for n in (a, b))
    return center(f"<div style='display:flex;gap:56px;height:640px'>{imgs}</div>")

ASSETS = {
  "icon_1024x1024.png": (1024, 1024, center(logo(1024, True))),  # логотип без текста; на всю площадь
  "icon_4x3_512x384.png": (512, 384, center(logo(300))),
  "icon_2x3_800x1200.png": (800, 1200, center(logo(520))),
  "cover_1920x1080.png": (1920, 1080, center(logo(330) + title(150) + "<div class=s style='font-size:44px'>Квиз на любую тему · 10 вопросов · рейтинг</div>", 34)),
  "cover_portrait_1080x1920.png": (1080, 1920, center(logo(420) + title(130) + "<div class=s style='font-size:42px'>Квиз на любую тему<br>10 вопросов · рейтинг</div>", 50)),
  "background_1920x1080.png": (1920, 1080, ""),  # без текста
}
PAIRS = [("1_home.png", "2_question.png"), ("3_answer.png", "4_quick_modes.png"), ("5_quick_round.png", "6_shop.png"), ("2_question.png", "5_quick_round.png")]
for i, (a, b) in enumerate(PAIRS, 1): ASSETS[f"screenshot_album_{i}_1280x720.png"] = (1280, 720, album(a, b))

with Run("promo_assets") as r:
    ctx = r.br.new_context(viewport={"width": 1920, "height": 1920}, device_scale_factor=1)
    pg = ctx.new_page()
    for name, (w, h, inner) in ASSETS.items():
        TMP.write_text(page(w, h, inner), encoding="utf-8")
        pg.set_viewport_size({"width": w, "height": h})
        pg.goto(r.base + "/dist/promo_tmp.html"); pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / name), clip={"x": 0, "y": 0, "width": w, "height": h}); print("готово", name)
    # портретные скриншоты 720x1280 уже есть в dist/promo/, копируем под понятными именами
    import shutil
    for i, n in enumerate(sorted(p.name for p in SHOTS.glob("?_*.png")), 1):
        shutil.copy(SHOTS / n, OUT / f"screenshot_portrait_{n}")
    TMP.unlink(missing_ok=True)
