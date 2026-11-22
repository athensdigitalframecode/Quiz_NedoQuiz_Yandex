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
    r.ok(pg.locator("#homeBlitz").is_visible(), "«Блиц» виден на главной рядом с «Играть»")
    r.ok(pg.evaluate("revealSec('solo')===2&&revealSec('solo','пояснение')===7&&revealSec('pvp','x')===4"),
         "разбор в «Играть»: 2 с, с пояснением 7 с; дуэль не меняется")

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
    pg.wait_for_timeout(500)  # фон меняется плавно (transition .25s) — замеряем после перехода
    pg.locator("#opts .opt.right").hover(); pg.wait_for_timeout(400)  # наведение/«залипшее» касание не должно перебивать цвет
    bg = pg.evaluate("[...document.querySelectorAll('#opts .opt.right,#opts .opt.wrongpick')].map(b=>b.className.split(' ')[1]+':'+getComputedStyle(b).backgroundColor)")
    r.ok(any(x.startswith("right:rgba(47, 227, 138") for x in bg), f"верный ответ подсвечен зелёным ({bg})")
    r.ok(any(x.startswith("wrongpick:rgba(255, 77, 99") for x in bg), "свой неверный выбор подсвечен красным")
    bn = pg.inner_text("#banner")
    r.ok(pg.evaluate(f"NQ_NO.some(x=>{bn!r}.startsWith(x))") and "red" in pg.get_attribute("#banner", "class"), f"после ошибки — добрая реплика Недоквиза ({bn!r})")
    r.ok(pg.locator("#ans .noans, #ans.noans").count() == 1 and not pg.locator("#anst").is_visible(), "верный ответ не дублируется карточкой — он подсвечен в вариантах")
    r.ok(pg.evaluate("document.getElementById('tnum').textContent") == "✗", "вместо «0» на таймере — ✗")
    r.ok(pg.locator("#hintRow").is_hidden(), "на первом вопросе подсказок нет")
    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
