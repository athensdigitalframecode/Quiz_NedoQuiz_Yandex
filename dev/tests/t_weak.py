"""§4.3: блок «Ваши знания» (сильные стороны, что подтянуть, прогресс по темам) и «Тренировка слабых тем».
Запуск: python dev/tests/t_weak.py"""
from harness import Run

ARC = "JSON.parse(localStorage.getItem('quiz_arc')||'{}')"
SET = "kp=>{const S=JSON.parse(localStorage.getItem('quiz_arc')||'{}');S.kp=kp;localStorage.setItem('quiz_arc',JSON.stringify(S));arcOpen();0}"

with Run("t_weak") as r:
    pg = r.page(sdk=True)
    pg.wait_for_function("document.body.dataset.scr==='s-home'&&!!ME", timeout=15000)

    pg.evaluate("nav('me')")
    pg.wait_for_timeout(300)
    r.ok("Сыграйте ещё немного" in pg.inner_text("#meKnow"), "без данных — приглашение сыграть, без выводов")

    # две темы с запасом вопросов: сильная и слабая; третья — мало ответов
    a, b, c = pg.evaluate("(()=>{const n={};BANK.forEach(x=>{if(!x.i&&!isKid(x.c)&&!HID.has(x.c)&&![24,25,26,30,31].includes(x.c))n[x.c]=(n[x.c]|0)+1});return Object.keys(n).filter(k=>n[k]>=30).map(Number).slice(0,3)})()")
    na, nb = pg.evaluate("([a,b])=>[TOPICS[a],TOPICS[b]]", [a, b])
    kp = {"e": "", "m": "1" * 10, "h": "", "t": {str(a): [10, 10], str(b): [10, 2], str(c): [3, 1]}, "lv": 0}
    pg.evaluate(SET, kp)
    pg.evaluate("nav('home');nav('me')")
    pg.wait_for_timeout(300)
    t = pg.inner_text("#meKnow")
    r.ok("сильные стороны" in t and na in t.split("Что стоит")[0], f"сильная тема: {na}")
    r.ok("Что стоит подтянуть" in t and nb in t.split("Что стоит подтянуть")[1], f"слабая тема: {nb}")
    r.ok("Ещё 1 тема" in t, "тема с 3 ответами — без выводов")
    r.ok(pg.locator('#meKnow [data-arc="m:weak"]').count() == 1, "рекомендована тренировка слабых тем")

    before = pg.evaluate(ARC)
    pg.click('#meKnow [data-arc="m:weak"]')
    topics, n = set(), 0
    while True:
        pg.wait_for_selector("#arcBody .opt, #arcBody .arc-big", timeout=5000)
        if pg.locator("#arcBody .arc-big").count(): break
        q = pg.inner_text("#arcBody .arc-q")
        x = pg.evaluate("q=>{const x=BANK.find(b=>b.q===q);return [x.c,x.a]}", q)
        topics.add(x[0]); n += 1
        i = pg.evaluate("a=>[...document.querySelectorAll('#arcBody .opt .pt')].map(e=>e.innerText).indexOf(a)", x[1])
        pg.click(f'[data-arc="o:{i}"]')
        pg.mouse.move(1, 1)
        pg.wait_for_timeout(700)
    r.ok(topics == {b} and n == 10, f"10 вопросов только из слабой темы ({topics}, {n})")
    after = pg.evaluate(ARC)
    r.ok(after["kp"]["t"][str(b)] == [20, 12], f"прогресс по теме учтён ({after['kp']['t'][str(b)]})")
    r.ok(after["kp"]["m"] == before["kp"]["m"] and after["kp"]["e"] == before["kp"]["e"], "уровень сложности тренировкой не меняется")
    r.ok(after["stars"] == before["stars"] and after["tot"] == before["tot"] and after["runs"] == before["runs"], "тренировка не даёт звёзд и очков")

    r.arc(pg, "hub")
    pg.wait_for_timeout(300)
    r.ok(pg.locator('[data-arc="m:weak"]').count() == 1, "в быстрых режимах — «Слабые темы»")
    r.arc(pg, "mast")
    pg.wait_for_timeout(300)
    r.ok("Ваши знания" in pg.inner_text("#arcBody"), "блок есть и в «Мастерстве тем» (для гостей)")

    r.ok(not pg.errors, f"нет ошибок консоли ({pg.errors[:3]})")
    r.ok(not pg.external, f"нет внешних запросов ({pg.external[:3]})")
