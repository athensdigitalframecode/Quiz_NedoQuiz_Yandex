"""Магазин: пакеты звёзд, «Основатель» с отключением рекламы, эффекты ответа и темы за звёзды.
Подставной SDK — проверяется наша логика, а не настоящая оплата. Запуск: python dev/tests/t_shop.py"""
from harness import Run

with Run("t_shop") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_function("__yg.calls.some(c=>c[0]==='consume')", timeout=10000)
    r.arc(pg, "shop")
    pg.wait_for_function("document.querySelectorAll('[data-arc^=\"pay:\"]').length===5", timeout=8000)
    ids = pg.evaluate("[...document.querySelectorAll('[data-arc^=\"pay:\"]')].map(b=>b.dataset.arc)")
    r.ok(ids == ["pay:stars_s", "pay:stars_m", "pay:stars_l", "pay:noads", "pay:founder"], f"платные товары: пакеты звёзд, noads, founder ({ids})")

    # пакет звёзд: +1000, затем consume
    SV = "JSON.parse(localStorage.getItem('quiz_arc'))"
    def setsv(js):  # правка сохранения быстрых режимов; магазин перечитывает его при открытии
        pg.evaluate("(()=>{const S=" + SV + ";" + js + ";localStorage.setItem('quiz_arc',JSON.stringify(S))})()")
        r.arc(pg, "shop")
    sv = lambda js: pg.evaluate("(S=>" + js + ")(" + SV + ")")
    s0 = sv("S.stars|0")
    r.arc(pg, "pay:stars_m")
    pg.wait_for_function(f"(JSON.parse(localStorage.getItem('quiz_arc')).stars|0)>={s0 + 1000}", timeout=5000)
    pg.wait_for_function("__yg.calls.filter(c=>c[0]==='consume').length>=2", timeout=5000)
    r.ok(True, "пакет звёзд: +1000⭐ и покупка потреблена")

    # «Основатель» отключает рекламу и закрывает «Без рекламы»
    pg.evaluate("YG.noads=false")
    r.arc(pg, "pay:founder")
    pg.wait_for_function("JSON.parse(localStorage.getItem('quiz_arc')).own.founder===1", timeout=5000)
    r.ok(pg.evaluate("YG.noads===true"), "«Основатель» отключает полноэкранную рекламу")
    pg.wait_for_timeout(300)
    r.ok("Входит в «Основателя»" in pg.inner_text("#arcBody"), "«Без рекламы» помечен как входящий в «Основателя»")
    # у кого «Основатель» был куплен раньше — реклама отключается при загрузке
    pg.evaluate("YG.noads=false"); setsv("S.own.noads=0")
    r.ok(pg.evaluate("YG.noads===true"), "старым «Основателям» реклама отключается при загрузке")

    # эффект ответа за звёзды
    setsv("S.stars=3000")
    r.arc(pg, "buy:x:confetti")
    r.ok(sv("S.own['x:confetti']===1&&S.eq.fx==='x:confetti'&&S.stars===2500"), "эффект «Конфетти» куплен за 500⭐ и надет")
    r.arc(pg, "eq:x:confetti")
    r.ok(sv("S.eq.fx===''"), "эффект снимается")
    r.arc(pg, "eq:x:confetti")
    r.ok(pg.evaluate("typeof window.fxOk==='function'&&(fxOk(),true)"), "fxOk работает без ошибок")

    # тема за звёзды
    r.ok(pg.locator('#thPick [data-th="cosmos"]').count() == 0, "не купленная тема не видна в выборе тем")
    r.arc(pg, "buy:t:cosmos")
    r.ok(pg.evaluate("document.documentElement.dataset.theme==='cosmos'") and sv("S.stars===2000"), "тема «Космос» куплена и включена")
    r.ok(pg.locator('#thPick [data-th="cosmos"]').count() == 1, "купленная тема появилась в выборе тем")
    r.arc(pg, "eq:t:cosmos")
    r.ok(pg.evaluate("document.documentElement.dataset.theme==='dark'"), "снять тему → «Золотая ночь»")

    # без денег: чужое не надевается, звёзд не хватает — сообщение
    setsv("S.stars=0")
    r.arc(pg, "buy:x:fire")
    r.ok(sv("!S.own['x:fire']") and "Не хватает" in pg.inner_text("#shMsg"), "без звёзд эффект не покупается")
    r.arc(pg, "eq:t:cherry")
    r.ok(pg.evaluate("document.documentElement.dataset.theme==='dark'"), "некупленную тему надеть нельзя")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
