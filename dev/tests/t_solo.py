"""«Играть» (Сам с собой) на подставной базе: старт, ответы, выход через окно игры (R-01).
Запуск: python dev/tests/t_solo.py"""
from harness import Run, GAME, start, answer

with Run("t_solo") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)

    start(pg)
    r.ok(pg.evaluate(f"{GAME}.mode") == "solo", "партия «Играть» создана")
    r.ok(pg.evaluate(f"({GAME}.qs||[]).length") == 10, "в партии 10 вопросов")
    pg.click("#s-game [data-leave]")
    pg.wait_for_timeout(500)
    r.ok(pg.locator(".dlgbg").count() == 0, "выход на 0 ответах — без окна")
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=5000)
    r.ok(True, "выход на 0 ответах ведёт на главную")

    start(pg)
    answer(pg, 3)
    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    t = pg.inner_text(".dlgbg")
    r.ok("Завершить игру?" in t and "3 из 10" in t, f"окно игры с числом ответов ({t[:60]!r})")
    pg.click("#ayNo")
    pg.wait_for_timeout(600)
    r.ok(pg.locator(".dlgbg").count() == 0 and pg.evaluate(f"{GAME}.status") == "q", "«Продолжить» закрывает окно, партия идёт")

    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    r.ok(pg.locator(".dlgbg").count() == 0 and pg.evaluate(f"{GAME}.status") == "q", "Esc закрывает окно, партия идёт")

    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_function(f"{GAME}.status==='end'", timeout=5000)
    r.ok(pg.evaluate(f"{GAME}.stopAt") == 3, "«Завершить» сохраняет 3 ответа (stopAt)")
    pg.wait_for_function("document.body.dataset.scr!=='s-game'", timeout=8000)
    r.ok(True, f"после «Завершить» показан итог ({pg.evaluate('document.body.dataset.scr')})")
    pg.wait_for_timeout(1500)
    st = pg.evaluate("[...__db.keys()].filter(k=>k.startsWith('stats/'))")
    r.ok(len(st) > 0, f"после досрочного выхода записана статистика ({st})")
    r.ok(pg.evaluate("__confirms") == 0, "системные confirm/alert не вызывались")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
