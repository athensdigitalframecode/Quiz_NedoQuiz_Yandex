"""Скриншоты игры для витрины площадок: 720x1280 (вертикальные), в dist/promo/.
Снимаются локально на подставных базе и SDK, в рабочую базу ничего не пишется. Запуск: python dev/tests/promo_shots.py"""
import pathlib
from harness import Run, ROOT, start

OUT = ROOT / "dist" / "promo"; OUT.mkdir(parents=True, exist_ok=True)
GP = dict(sdk=False, gp=True, viewport=(360, 640), scale=2, gpinit="window.__gpBought=false")

def ready(pg):
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&!!YG.sdk", timeout=20000)
    pg.wait_for_timeout(1500)

def shot(pg, name):
    pg.add_style_tag(content="#updBtn{display:none!important}")  # плашка «Обновления» в кадр не нужна
    pg.wait_for_timeout(600); p = OUT / name; pg.screenshot(path=str(p)); print("снято", p.name)

with Run("promo") as r:
    pg = r.page(**GP); ready(pg)
    shot(pg, "1_home.png")
    start(pg)
    pg.wait_for_function("typeof me==='function'&&!!me()", timeout=20000)
    shot(pg, "2_question.png")
    pg.locator("#opts .opt:not(.gone)").first.click()
    pg.wait_for_function("(g=>g&&g.status==='reveal')(" + "(()=>{const g=[...__db.values()].filter(r=>r.col==='games').pop();return g?g.data:null})()" + ")", timeout=8000)
    shot(pg, "3_answer.png")

    pg = r.page(**GP); ready(pg)
    pg.click("#arcOpen"); pg.wait_for_function("document.body.dataset.scr==='s-arc'", timeout=5000)
    shot(pg, "4_quick_modes.png")
    r.arc(pg, "m:cls")
    pg.wait_for_selector('[data-arc^="o:"]', timeout=8000)
    shot(pg, "5_quick_round.png")

    pg = r.page(**GP); ready(pg)
    pg.click("#arcShop")
    pg.wait_for_function("document.querySelectorAll('[data-arc^=\"pay:\"]').length===3", timeout=8000)
    pg.locator('[data-arc^="pay:"]').first.scroll_into_view_if_needed()
    pg.evaluate("document.querySelector('[data-arc^=\\\"pay:\\\"]').closest('.card,div').scrollIntoView({block:'start'})")
    shot(pg, "6_shop.png")
