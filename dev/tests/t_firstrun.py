"""Первый запуск и разбор ответа в «Играть»: без окна обучения, цвета верного/неверного, время на пояснение.
Плюс аудит банка вопросов без структурных ошибок. Запуск: python dev/tests/t_firstrun.py"""
import pathlib, sys
from harness import Run, GAME, start, ROOT

sys.path.insert(0, str(ROOT / "dev"))
import audit_bank

with Run("t_firstrun") as r:
    bank, topics = audit_bank.load()
    errs = {k: v[:3] for k, v in audit_bank.audit(bank, topics).items() if k.startswith("E:")}
    r.ok(not errs, f"банк вопросов: нет структурных ошибок ({errs})")

    pg = r.page(sdk=True, skip_onb=False)  # настоящий новичок: флага «обучение пройдено» нет
    pg.wait_for_function("document.body.dataset.scr==='s-home'", timeout=15000)
    pg.wait_for_timeout(2500)
    r.ok(pg.locator("#onb").is_hidden(), "новичку окно обучения само не открывается")
    r.ok(pg.locator('[data-act="new"][data-mode="solo"]').first.is_visible(), "кнопка «Играть» видна сразу")
    r.ok(pg.evaluate("revealSec('solo')===3&&revealSec('solo','пояснение')===7&&revealSec('pvp','x')===4"),
         "пояснение даёт +4 с только в «Играть»; дуэль не меняется")

    start(pg)
    pg.wait_for_function("typeof me==='function'&&!!me()", timeout=20000)
    a = pg.evaluate(f"aOf({GAME},{GAME}.qi)")
    o = pg.locator("#opts .opt")
    for _ in range(10):  # клик до загрузки своего игрока игра игнорирует
        for i in range(o.count()):
            if o.nth(i).get_attribute("data-o") != a: o.nth(i).click(); break
        try: pg.wait_for_function(f"{GAME}.status==='reveal'", timeout=2500); break
        except Exception: pass
    pg.wait_for_selector("#opts .opt.wrongpick", timeout=5000)
    bg = pg.evaluate("[...document.querySelectorAll('#opts .opt.right,#opts .opt.wrongpick')].map(b=>b.className.split(' ')[1]+':'+getComputedStyle(b).backgroundColor)")
    r.ok(any(x.startswith("right:rgba(47, 227, 138") for x in bg), f"верный ответ подсвечен зелёным ({bg})")
    r.ok(any(x.startswith("wrongpick:rgba(255, 77, 99") for x in bg), "свой неверный выбор подсвечен красным")
    r.ok(pg.inner_text("#banner").startswith("Не угадали") and a in pg.inner_text("#anst"), "после ошибки — спокойное «Не угадали» и правильный ответ")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
