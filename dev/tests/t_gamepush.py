"""Адаптер GamePush на подставном SDK (mock_gp.js): готовность, облачное сохранение, покупка, реклама, рейтинг.
Запуск: python dev/tests/t_gamepush.py. Это проверка нашей логики, не работы на платформе."""
import json
from harness import Run

def gpc(pg): return pg.evaluate("__gp.calls.map(c=>c.join(' '))")

with Run("t_gamepush") as r:
    # 1. Старт: готовность, покупка из прошлого запуска, облако, рейтинг, рекорд в рейтинг
    pg = r.page(sdk=False, gp=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_function("__gp.calls.some(c=>c[0].startsWith('consume'))&&__gp.calls.some(c=>c[0]==='gameStart')", timeout=10000)
    c = gpc(pg)
    r.ok(pg.evaluate("YG.platform") == "gamepush", "игра выбрала адаптер GamePush")
    r.ok(c.index("set arc") < c.index("sync") < c.index("consume starter"), "покупка: сначала сохранение в облако, потом consume")
    cloud = json.loads(pg.evaluate("__gp.store.arc") or "{}")
    r.ok(cloud.get("stars", 0) >= 300 and any(t.startswith("starter@") for t in cloud.get("tok", [])), "набор новичка выдан и записан в облако")
    r.arc(pg, "bd:surv")
    pg.wait_for_function("(document.getElementById('arcBd')||{}).innerText?.includes('Тест')", timeout=5000)
    r.ok("fetch arcsurv" in gpc(pg), "рейтинг строится через gp.leaderboard.fetch")
    r.arc(pg, "m:cls")
    for _ in range(40):
        if pg.locator('[data-arc="fin"]').count(): pg.click('[data-arc="fin"]'); break
        if pg.locator("#arcLb").count(): break
        o = pg.locator('[data-arc^="o:"]:not(:disabled)')
        if o.count():
            try: o.first.click(timeout=3000)
            except Exception: pass
        pg.wait_for_timeout(1500)
    pg.wait_for_timeout(1000)
    r.ok(pg.evaluate("__gp.store.arccls|0") > 0 and "set arccls" in gpc(pg), "рекорд записан в поле arccls")
    # 2. Реклама с рекламой
    pg.evaluate("window.__d=0;ygAdv(()=>{window.__d=1})")
    pg.wait_for_function("window.__d===1", timeout=3000)
    r.ok("fullscreen" in gpc(pg), "полноэкранная реклама идёт через gp.ads")
    pg.evaluate("window.__ro=0;ygReward(()=>{window.__ro=1})")
    pg.wait_for_function("window.__ro===1", timeout=3000)
    r.ok("rewarded" in gpc(pg), "ролик за награду выдаёт награду")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

    # 3. Сбой sync: покупка не потребляется
    pg = r.page(sdk=False, gp=True, failsave=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_timeout(3000)
    c = gpc(pg)
    r.ok("sync" in c and not any(x.startswith("consume") for x in c), "сбой sync → consume не вызван")

    # 4. Блокировщик рекламы: игра не ломается, награда не выдаётся
    pg = r.page(sdk=False, gp=True, gpinit="window.__adblock=true")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_function("YG.sdk", timeout=5000)
    pg.evaluate("window.__d=0;window.__ro=0;ygAdv(()=>{window.__d=1});ygReward(()=>{window.__ro=1})")
    pg.wait_for_function("window.__d===1", timeout=3000)
    pg.wait_for_timeout(300)
    c = gpc(pg)
    r.ok(pg.evaluate("window.__ro") == 0 and "rewarded" not in c and "fullscreen" not in c, "с блокировщиком рекламы: без роликов и без награды, игра идёт")
    r.ok(not pg.errors, f"с блокировщиком нет ошибок консоли ({pg.errors[:3]})")

    # 5. Платежи недоступны на платформе: магазин без платных товаров
    pg = r.page(sdk=False, gp=True, gpinit="window.__gpPay=false")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_timeout(1500)
    r.arc(pg, "shop")
    pg.wait_for_timeout(500)
    r.ok(pg.locator('[data-arc^="pay:"]').count() == 0, "платежи недоступны → платных товаров нет")
