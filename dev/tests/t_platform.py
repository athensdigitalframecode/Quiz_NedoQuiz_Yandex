"""Платформа: SDK Яндекса (подставной), покупки, лидерборды, режим без SDK и без базы.
Запуск: python dev/tests/t_platform.py"""
from harness import Run

with Run("t_platform") as r:
    # 1. С SDK: готовность, покупка при старте, рейтинг
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_function("__yg.calls.some(c=>c[0]==='consume')&&__yg.calls.some(c=>c[0]==='ready')", timeout=10000)
    c = r.calls(pg)
    r.ok("ready" in c, "LoadingAPI.ready вызван после главной")
    r.ok(c.index("setData true") < c.index("consume tok-1"), "покупка: сначала облачное сохранение, потом consume")
    cloud = pg.evaluate("__yg.cloud&&__yg.cloud.arc")
    r.ok(cloud and cloud["stars"] >= 300 and "tok-1" in cloud["tok"], "набор новичка выдан и сохранён в облаке")
    r.arc(pg, "bd:surv")
    pg.wait_for_function("(document.getElementById('arcBd')||{}).innerText?.includes('Тест')", timeout=5000)
    r.ok("getEntries arcsurv" in r.calls(pg), "экран рейтинга идёт через ysdk.leaderboards")
    # раунд «Классики» → рекорд в лидерборд
    r.arc(pg, "m:cls")
    for _ in range(40):
        if pg.locator('[data-arc="fin"]').count(): pg.click('[data-arc="fin"]'); break
        if pg.locator("#arcLb").count(): break
        o = pg.locator('[data-arc^="o:"]:not(:disabled)')
        if o.count():
            try: o.first.click(timeout=3000)  # экран раунда перерисовывается; следующий проход повторит
            except Exception: pass
        pg.wait_for_timeout(1500)
    pg.wait_for_timeout(1000)
    sent = [x for x in r.calls(pg) if x.startswith("setScore")]
    r.ok(all(int(x.split()[-1]) > 0 for x in sent), f"в лидерборд не уходит нулевой счёт ({sent})")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")

    # 2. Сбой облачного сохранения: покупка не потребляется
    pg = r.page(sdk=True, failsave=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_timeout(3000)
    c = r.calls(pg)
    r.ok("setData true" in c and not any(x.startswith("consume") for x in c), "сбой сохранения → consume не вызван")

    # 3. Без SDK (обычный браузер): рейтинг честно недоступен, магазин без платных товаров
    pg = r.page(sdk=False)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=20000)
    r.arc(pg, "bd:surv")
    pg.wait_for_timeout(500)
    r.ok("Яндекс Играх" in pg.inner_text("#arcBd"), "без SDK рейтинг пишет «доступен на Яндекс Играх»")
    r.arc(pg, "shop")
    pg.wait_for_timeout(500)
    r.ok(pg.locator('[data-arc^="pay:"]').count() == 0, "без SDK платных товаров в магазине нет")
    r.ok(not pg.errors, f"нет ошибок консоли без SDK ({pg.errors[:3]})")

    # 4. База недоступна: быстрые режимы, без регистрации
    pg = r.page(sdk=True, db="down")
    pg.wait_for_timeout(9000)
    scr = pg.evaluate("document.body.dataset.scr")
    r.ok(scr in ("s-arc", "s-home"), f"без базы открывается игра ({scr})")
    r.ok(not pg.locator("#s-auth").is_visible(), "без базы нет экрана регистрации")
    r.arc(pg, "m:cls")
    pg.wait_for_timeout(800)
    r.ok(pg.locator('[data-arc^="o:"]').count() > 0, "без базы быстрый режим играется")
    r.ok(pg.evaluate("__confirms") == 0, "нет системных окон confirm/alert")
