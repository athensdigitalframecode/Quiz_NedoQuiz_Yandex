"""§8.1: жалоба на вопрос — причина, комментарий ≤200, режим и платформа; отмена; лимит 10 в день.
Запуск: python dev/tests/t_disp.py"""
from harness import Run, GAME, start, answer_wrong

DISP = "[...__db.values()].filter(x=>x.col==='disputes').map(x=>x.data)"

with Run("t_disp") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&!!uid", timeout=15000)
    start(pg)
    answer_wrong(pg, 3)
    pg.click("#s-game [data-leave]")
    pg.wait_for_selector(".dlgbg", timeout=3000)
    pg.click("#ayYes")
    pg.wait_for_function(f"{GAME}.status==='end'", timeout=5000)
    pg.click('[data-act="review"]')
    pg.wait_for_selector('[data-act="disp"]', timeout=5000)

    # отмена — ничего не пишется
    pg.locator('[data-act="disp"]').nth(1).click()
    pg.wait_for_selector("#arNo", timeout=3000)
    labels = pg.locator(".dlg .rsn label").all_inner_texts()
    r.ok(len(labels) == 6 and not any("картинка" in t for t in labels), f"6 причин, без «картинки» у вопроса без картинки ({len(labels)})")
    pg.click("#arNo")
    pg.wait_for_timeout(300)
    r.ok(pg.evaluate(DISP) == [] and pg.locator('[data-act="disp"]').nth(1).inner_text() == "Оспорить", "«Отмена» — жалоба не отправлена")

    # причина + комментарий
    pg.locator('[data-act="disp"]').first.click()
    pg.wait_for_selector("#arYes", timeout=3000)
    pg.check('.dlg input[value="old"]')
    pg.fill("#arC", "  Сейчас   уже\nдругой ответ  ")
    pg.click("#arYes")
    pg.wait_for_function(f"{DISP}.length===1", timeout=5000)
    d = pg.evaluate(DISP)[0]
    r.ok(d["r"] == "old" and d["c"] == "Сейчас уже другой ответ", f"причина и комментарий ({d.get('r')}, {d.get('c')!r})")
    r.ok(d["m"] == "solo" and d["pl"] == "yandex" and d["by"] == pg.evaluate("uid"), f"режим, платформа, автор ({d['m']}, {d['pl']})")
    r.ok(pg.locator('[data-act="disp"]').first.inner_text() == "Оспорено", "кнопка — «Оспорено»")
    r.ok(pg.evaluate("document.querySelector('#arC')") is None, "окно закрыто")

    # жалоба из партии (кнопка после ответа) — тем же окном
    pg.evaluate("flagQ();0")
    pg.wait_for_selector("#arYes", timeout=3000)
    pg.click("#arYes")
    pg.wait_for_function(f"{DISP}.length===2", timeout=5000)
    f = [x for x in pg.evaluate(DISP) if x.get("f") == 1]
    r.ok(len(f) == 1 and f[0]["r"] == "wrong" and f[0]["c"] == "", "кнопка после ответа: причина по умолчанию — «Неправильный ответ»")

    # лимит в день
    pg.evaluate("localStorage.setItem('quiz_dispday',JSON.stringify({d:dayKey(),n:10}))")
    pg.locator('[data-act="disp"]:not([disabled])').first.click()
    pg.wait_for_selector("#arNo", timeout=3000)
    r.ok(pg.locator("#arYes").count() == 0 and "уже отправили 10" in pg.inner_text(".dlg"), "после 10 жалоб за день — только «Понятно»")
    pg.click("#arNo")
    r.ok(len(pg.evaluate(DISP)) == 2, "сверх лимита ничего не отправлено")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
