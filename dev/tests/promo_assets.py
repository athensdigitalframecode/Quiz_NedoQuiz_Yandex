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

def album(a, b, h=640):
    imgs = "".join(f"<img class=ph src='/dist/promo/{n}' style='height:{h}px'>" for n in (a, b))
    return center(f"<div style='display:flex;gap:{h * 56 // 640}px;height:{h}px'>{imgs}</div>")

ASSETS = {
  "icon_1024x1024.png": (1024, 1024, center(logo(1024, True))),  # логотип без текста; на всю площадь
  "icon_4x3_512x384.png": (512, 384, center(logo(300))),
  "icon_2x3_800x1200.png": (800, 1200, center(logo(520))),
  "cover_1920x1080.png": (1920, 1080, center(logo(330) + title(150) + "<div class=s style='font-size:44px'>Квиз на любую тему · 10 вопросов · рейтинг</div>", 34)),
  "cover_portrait_1080x1920.png": (1080, 1920, center(logo(420) + title(130) + "<div class=s style='font-size:42px'>Квиз на любую тему<br>10 вопросов · рейтинг</div>", 50)),
  "background_1920x1080.png": (1920, 1080, ""),  # без текста
}
# иконки товаров 512x512 (теги как в PROD): рисованный SVG в цветах игры
import math
def star(cx, cy, r, f="#ffc93c"):
    pts = " ".join(f"{cx + (r if i % 2 == 0 else r * .45) * math.sin(i * math.pi / 5):.1f},{cy - (r if i % 2 == 0 else r * .45) * math.cos(i * math.pi / 5):.1f}" for i in range(10))
    return f"<polygon points='{pts}' fill='{f}' stroke='#b8860b' stroke-width='{r * .06:.1f}' stroke-linejoin='round'/>"
def svg(body): return center("<svg width=512 height=512 viewBox='0 0 512 512' style='filter:drop-shadow(0 10px 24px #0008)'>" + body.replace("/>", " />") + "</svg>")  # пробел: иначе HTML читает «10/» как значение и не закрывает тег
GLOW = "<circle cx=256 cy=256 r=200 fill='#ffc93c' opacity='.10'/>"
PRODUCTS = {
  "stars_s": GLOW + star(256, 290, 120) + star(140, 170, 56) + star(380, 160, 66),
  "stars_m": GLOW + star(190, 120, 46) + star(320, 104, 40) + star(256, 84, 34)
     + "<path d='M196 168h120l-18 40c70 22 112 82 112 152 0 66-60 100-154 100s-154-34-154-100c0-70 42-130 112-152z' fill='#8a5a2b' stroke='#5a3816' stroke-width=10 stroke-linejoin=round/>"
     + "<rect x=192 y=196 width=128 height=22 rx=11 fill='#c9a8ff'/>" + star(256, 340, 66),
  "stars_l": GLOW + star(256, 120, 60) + star(150, 150, 36) + star(362, 150, 40)
     + "<rect x=86 y=210 width=340 height=90 rx=30 fill='#9a5d2a' stroke='#5a3816' stroke-width=10/>"
     + "<rect x=86 y=290 width=340 height=150 rx=18 fill='#7a4520' stroke='#5a3816' stroke-width=10/>"
     + "<rect x=86 y=280 width=340 height=26 fill='#ffc93c'/><rect x=230 y=270 width=52 height=70 rx=10 fill='#ffc93c' stroke='#b8860b' stroke-width=6/>",
  "noads": "<rect x=96 y=136 width=320 height=240 rx=40 fill='#1c2744' stroke='#6ab0ff' stroke-width=14/>"
     + "<text x=256 y=304 text-anchor=middle font-family='Unbounded,sans-serif' font-weight=800 font-size=120 fill='#eef2fb'>AD</text>"
     + "<circle cx=256 cy=256 r=196 fill=none stroke='#ff4d63' stroke-width=30/><line x1=118 y1=394 x2=394 y2=118 stroke='#ff4d63' stroke-width=30 stroke-linecap=round/>",
  "founder": GLOW + "<circle cx=256 cy=290 r=150 fill='#1c2744' stroke='#ffc93c' stroke-width=22/><circle cx=256 cy=290 r=118 fill=none stroke='#c9a8ff' stroke-width=6 stroke-dasharray='14 12'/>"
     + "<path d='M146 120l50 50 60-80 60 80 50-50-20 110H166z' fill='#ffc93c' stroke='#b8860b' stroke-width=8 stroke-linejoin=round/>"
     + star(256, 300, 70),
}
for tag, body in PRODUCTS.items(): ASSETS[f"product_{tag}_512x512.png"] = (512, 512, svg(body))
PAIRS = [("1_home.png", "2_question.png"), ("3_answer.png", "4_quick_modes.png"), ("5_quick_round.png", "6_shop.png"), ("2_question.png", "5_quick_round.png")]
for i, (a, b) in enumerate(PAIRS, 1): ASSETS[f"screenshot_album_{i}_1280x720.png"] = (1280, 720, album(a, b))
# VK: большой сниппет 1120x630 и скриншоты 1200x600
ASSETS["vk_snippet_1120x630.png"] = (1120, 630, center(logo(200) + title(84) + "<div class=s style='font-size:26px'>Квиз на любую тему · 10 вопросов · рейтинг</div>", 20))
for i, (a, b) in enumerate(PAIRS, 1): ASSETS[f"vk_screenshot_{i}_1200x600.png"] = (1200, 600, album(a, b, 540))

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
