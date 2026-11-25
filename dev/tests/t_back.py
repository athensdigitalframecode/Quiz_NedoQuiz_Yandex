"""§10.2: системная кнопка «Назад» (popstate) — окно, партия, быстрые режимы, обычные экраны.
Запуск: python dev/tests/t_back.py"""
from harness import Run, GAME, start, answer

SCR = "document.body.dataset.scr"

with Run("t_back") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function(f"{SCR}==='s-home'", timeout=15000)
    r.ok(not pg.evaluate("bkOn"), "на главной «Назад» не перехватывается")

    # обычный экран → «Назад» → главная
    pg.evaluate("nav('faq')")
    r.ok(pg.evaluate("bkOn"), "на другом экране — запись-страховка в истории")
    pg.go_back()
    pg.wait_for_function(f"{SCR}==='s-home'", timeout=3000)
    r.ok(True, "с экрана вопросов-ответов «Назад» ведёт на главную")

    # партия «Играть»: «Назад» спрашивает, второе «Назад» закрывает окно, партия идёт
    start(pg)
    answer(pg, 1)
    pg.go_back()
    pg.wait_for_selector(".dlgbg", timeout=3000)
    r.ok("Завершить игру?" in pg.inner_text(".dlgbg"), "посреди партии «Назад» показывает «Завершить игру?»")
    pg.go_back()
    pg.wait_for_timeout(400)
    r.ok(pg.locator(".dlgbg").count() == 0 and pg.evaluate(f"{GAME}.status") in ("q", "reveal") and pg.evaluate(SCR) == "s-game",
         "второе «Назад» закрывает окно, партия продолжается")
    pg.go_back()
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_function(f"{GAME}.status==='end'", timeout=5000)
    pg.wait_for_timeout(300)
    pg.go_back()
    pg.wait_for_function(f"{SCR}==='s-home'", timeout=3000)
    r.ok(True, "с итогов партии «Назад» ведёт на главную")

    # быстрые режимы: посреди раунда — вопрос, «Играть дальше» — раунд идёт, «Выйти» — список режимов
    r.arc(pg, "hub")
    pg.wait_for_selector('[data-arc="m:surv"]', timeout=5000)
    pg.click('[data-arc="m:surv"]')
    pg.wait_for_selector("#arcBody .arc-q", timeout=5000)
    pg.go_back()
    pg.wait_for_selector(".dlgbg", timeout=3000)
    r.ok("Выйти из раунда?" in pg.inner_text(".dlgbg"), "посреди раунда «Назад» спрашивает о выходе")
    pg.click("#ayNo")
    pg.wait_for_timeout(300)
    r.ok(pg.locator("#arcBody .arc-q").count() == 1 and pg.locator(".dlgbg").count() == 0, "«Играть дальше» — раунд продолжается")
    pg.go_back()
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_selector('[data-arc="m:surv"]', timeout=3000)
    r.ok(pg.evaluate(SCR) == "s-arc", "«Выйти» — к списку быстрых режимов")
    pg.go_back()
    pg.wait_for_timeout(400)
    online = pg.evaluate("!!(uid&&ME)")
    r.ok(pg.evaluate(SCR) == ("s-home" if online else "s-arc"), f"со списка режимов «Назад» — на главную (вошёл: {online})")

    r.ok(pg.url.endswith("/index.html"), f"страница игры не покинута ({pg.url})")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
