"""Ролик за 50/50 посреди вопроса: время ролика не списывается с таймера вопроса.
Запуск: python dev/tests/t_hint.py"""
from harness import Run, GAME, start, answer

with Run("t_hint") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    start(pg)
    pg.wait_for_function("typeof me==='function'&&!!me()&&game&&game.status==='q'", timeout=20000)
    r.ok(pg.locator("#hintRow").is_hidden(), "на 1-м вопросе подсказок нет")
    answer(pg, 2)  # подсказки появляются с 3-го вопроса одной кнопкой
    pg.wait_for_selector("#hintRow [data-hmore]", timeout=5000)
    r.ok(pg.locator("#hintRow .btn").count() == 1, "с 3-го вопроса — одна кнопка «Подсказки»")
    pg.click("#hintRow [data-hmore]")
    r.ok(pg.locator("#hintRow [data-hint]").count() == 1, "по нажатию раскрывается список, 50/50 в нём")
    pg.evaluate("window.__adMs=2500")
    q = pg.evaluate("game.qi|0")
    t0 = pg.evaluate(f"endAt[{q}]")
    left0 = t0 - pg.evaluate("Date.now()")
    btn = pg.locator("[data-ghv]")
    r.ok(btn.count() == 1, "кнопка «50/50 за просмотр видео» есть")
    btn.click()
    pg.wait_for_function("__yg.calls.some(c=>c[0]==='reward')", timeout=5000)
    pg.wait_for_function(f"endAt[{q}]>{t0}+2000", timeout=8000)
    shift = pg.evaluate(f"endAt[{q}]") - t0
    r.ok(2400 <= shift <= 3500, f"срок вопроса сдвинут на длительность ролика ({shift} мс)")
    left1 = pg.evaluate(f"endAt[{q}]-Date.now()")
    r.ok(left1 >= left0 - 1500, f"после ролика осталось почти столько же времени ({left0:.0f} → {left1:.0f} мс)")
    pg.wait_for_function(f"(g=>g&&g.status==='q')({GAME})", timeout=5000)
    r.ok(pg.evaluate("YG.paused") is False, "пауза снята после ролика")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
